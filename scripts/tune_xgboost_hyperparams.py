"""Random search for XGBoost hyperparameters on the corrected baseline.

Search strategy:
- Hold-out test (20%); group-aware split by mouse_idx when --independent,
  random stratified split otherwise. Identical to train_classifier.py.
- 5-fold CV on the remaining 80% to score each sampled config.
  StratifiedGroupKFold(by mouse_idx) for --independent, StratifiedKFold otherwise.
- Each fold trains with `early_stopping_rounds=25` against the fold's validation
  set so n_estimators is chosen per-config rather than fixed.
- Class balance: scale_pos_weight = n_WT/n_HT on the fitting fold (corrected,
  single-weighting). sample_weight=balanced is NOT applied.

Selection:
- Primary objective: mean CV balanced accuracy.
- Top-K configs are then refit on the full 80% and scored on the held-out test.
- All trials and the top-K test metrics are saved to
  outputs/reports/xgboost_tuning/.

Usage:
    python scripts/tune_xgboost_hyperparams.py --dependent --n-trials 120
    python scripts/tune_xgboost_hyperparams.py --independent --n-trials 120
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    precision_score,
    recall_score,
)
from sklearn.model_selection import (
    StratifiedGroupKFold,
    StratifiedKFold,
    train_test_split,
)
from xgboost import XGBClassifier

REPO_ROOT = Path(__file__).resolve().parent.parent
BASELINE_CSV = REPO_ROOT / "outputs" / "external" / "aggregated" / "all_data_external_baseline.csv"
REPORTS_DIR = REPO_ROOT / "outputs" / "reports" / "xgboost_tuning"

COL_NAMES = [
    'syll1_s_freq', 'syll2_s_freq', 'syll3_s_freq', 'syll4_s_freq', 'syll5_s_freq',
    'syll6_s_freq', 'syll7_s_freq', 'syll8_s_freq', 'syll9_s_freq', 'syll10_s_freq',
    'syll1_e_freq', 'syll2_e_freq', 'syll3_e_freq', 'syll4_e_freq', 'syll5_e_freq',
    'syll6_e_freq', 'syll7_e_freq', 'syll8_e_freq', 'syll9_e_freq', 'syll10_e_freq',
    'syll1_dist', 'syll2_dist', 'syll3_dist', 'syll4_dist', 'syll5_dist',
    'syll6_dist', 'syll7_dist', 'syll8_dist', 'syll9_dist', 'syll10_dist',
    'syll1_dur', 'syll2_dur', 'syll3_dur', 'syll4_dur', 'syll5_dur',
    'syll6_dur', 'syll7_dur', 'syll8_dur', 'syll9_dur', 'syll10_dur',
    'mother_gen', 'pup_sex', 'avg_ISI_time', 'pup_age', 'session', 'pup_strain',
    'pup_gen', 'mouse_idx',
]

# Bounded ranges; sampled per-trial. Includes the current production point
# (max_depth=5, min_child_weight=0.1, lr=0.1, reg_lambda=1.5, reg_alpha=0.05,
# colsample_bytree=0.6) so it will be touched if drawn.
SEARCH_SPACE: Dict[str, List[Any]] = {
    'max_depth':        [3, 4, 5, 6, 7, 8],
    'min_child_weight': [1, 2, 3, 5, 8, 12, 20],
    'learning_rate':    [0.02, 0.03, 0.05, 0.08, 0.1, 0.15],
    'reg_lambda':       [0.5, 1.0, 1.5, 3.0, 6.0, 10.0],
    'reg_alpha':        [0.0, 0.05, 0.2, 0.5, 1.0, 2.0],
    'gamma':            [0.0, 0.1, 0.5, 1.0, 2.0, 4.0],
    'subsample':        [0.6, 0.7, 0.8, 0.9, 1.0],
    'colsample_bytree': [0.5, 0.6, 0.7, 0.8, 1.0],
}

N_EST_CEILING = 500
EARLY_STOP = 25
SEED = 100


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dependent', action='store_true',
                      help='Subject-dependent: random 80/20 holdout + StratifiedKFold CV.')
    mode.add_argument('--independent', action='store_true',
                      help='Subject-independent: group-aware 80/20 holdout + StratifiedGroupKFold CV.')
    p.add_argument('--n-trials', type=int, default=120,
                   help='Number of random configs to sample (default: 120).')
    p.add_argument('--top-k', type=int, default=5,
                   help='Refit the top-K configs on full trainval and score on test (default: 5).')
    p.add_argument('--n-folds', type=int, default=5,
                   help='CV folds (default: 5).')
    p.add_argument('--data-csv', type=str, default=str(BASELINE_CSV),
                   help=f'Training CSV (default: {BASELINE_CSV}).')
    p.add_argument('--random-state', type=int, default=42,
                   help='RNG seed for the random search (default: 42).')
    return p.parse_args()


def sample_config(rng: np.random.RandomState) -> Dict[str, Any]:
    return {k: _coerce(rng.choice(v)) for k, v in SEARCH_SPACE.items()}


def _coerce(v: Any) -> Any:
    # numpy scalars -> python scalars (so JSON serialization is clean)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.floating):
        return float(v)
    return v


def hold_out_split(X, y, groups, independent: bool):
    if independent:
        labels_per_mouse = (
            pd.DataFrame({'mouse_idx': groups.values, 'label': y.values})
            .groupby('mouse_idx')['label']
            .first()
        )
        mice = labels_per_mouse.index.values
        lbls = labels_per_mouse.values
        mice_trainval, mice_test = train_test_split(
            mice, test_size=0.2, random_state=SEED, stratify=lbls,
        )
        mask = groups.isin(mice_trainval)
        X_tv, X_te = X[mask], X[~mask]
        y_tv, y_te = y[mask], y[~mask]
        groups_tv = groups[mask]
        return X_tv, X_te, y_tv, y_te, groups_tv
    # Subject-dependent: row-level stratified
    X_tv, X_te, y_tv, y_te, idx_tv, _ = train_test_split(
        X, y, np.arange(len(X)), test_size=0.2, random_state=SEED, stratify=y,
    )
    groups_tv = groups.iloc[idx_tv]
    return X_tv, X_te, y_tv, y_te, groups_tv


def make_cv(independent: bool, n_folds: int):
    if independent:
        return StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=SEED)
    return StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=SEED)


def build_model(params: Dict[str, Any], scale_pos_weight: float, n_estimators: int,
                early_stopping: bool):
    return XGBClassifier(
        n_estimators=n_estimators,
        objective='binary:logistic',
        booster='gbtree',
        eval_metric='auc',
        scale_pos_weight=scale_pos_weight,
        random_state=SEED,
        n_jobs=1,
        verbosity=0,
        early_stopping_rounds=EARLY_STOP if early_stopping else None,
        **params,
    )


def fold_score(X_tr, y_tr, X_va, y_va, params: Dict[str, Any]) -> Dict[str, float]:
    n_wt = int((y_tr == 0).sum())
    n_ht = int((y_tr == 1).sum())
    spw = n_wt / max(n_ht, 1)
    model = build_model(params, spw, N_EST_CEILING, early_stopping=True)
    model.fit(X_tr, y_tr, eval_set=[(X_va, y_va)], verbose=False)
    pred = model.predict(X_va)
    return {
        'balanced_acc': float(balanced_accuracy_score(y_va, pred)),
        'acc': float(accuracy_score(y_va, pred)),
        'ht_recall': float(recall_score(y_va, pred, pos_label=1, zero_division=0)),
        'wt_recall': float(recall_score(y_va, pred, pos_label=0, zero_division=0)),
        'ht_precision': float(precision_score(y_va, pred, pos_label=1, zero_division=0)),
        'wt_precision': float(precision_score(y_va, pred, pos_label=0, zero_division=0)),
        'best_iter': int(getattr(model, 'best_iteration', N_EST_CEILING - 1)),
    }


def evaluate_on_test(params: Dict[str, Any], n_estimators: int,
                     X_tv, y_tv, X_te, y_te) -> Dict[str, float]:
    n_wt = int((y_tv == 0).sum())
    n_ht = int((y_tv == 1).sum())
    spw = n_wt / max(n_ht, 1)
    model = build_model(params, spw, n_estimators, early_stopping=False)
    model.fit(X_tv, y_tv, verbose=False)
    pred = model.predict(X_te)
    cm = confusion_matrix(y_te, pred, labels=[0, 1])
    return {
        'test_acc': float(accuracy_score(y_te, pred)),
        'test_balanced_acc': float(balanced_accuracy_score(y_te, pred)),
        'test_ht_recall': float(recall_score(y_te, pred, pos_label=1, zero_division=0)),
        'test_wt_recall': float(recall_score(y_te, pred, pos_label=0, zero_division=0)),
        'test_ht_precision': float(precision_score(y_te, pred, pos_label=1, zero_division=0)),
        'test_wt_precision': float(precision_score(y_te, pred, pos_label=0, zero_division=0)),
        'cm_tn': int(cm[0, 0]), 'cm_fp': int(cm[0, 1]),
        'cm_fn': int(cm[1, 0]), 'cm_tp': int(cm[1, 1]),
    }


def main() -> int:
    args = parse_args()
    independent = bool(args.independent)
    suffix = 'independent' if independent else 'dependent'

    csv_path = Path(args.data_csv)
    if not csv_path.is_file():
        print(f'ERROR: CSV not found: {csv_path}', file=sys.stderr)
        return 1

    print(f'== XGBoost hyperparameter search ({suffix}) ==')
    print(f'CSV:        {csv_path}')
    print(f'Trials:     {args.n_trials}')
    print(f'CV folds:   {args.n_folds}')
    print(f'Top-K test: {args.top_k}')
    print(f'Seed:       {args.random_state}')
    print()

    df = pd.read_csv(csv_path, header=None, names=COL_NAMES)
    feature_cols = [c for c in COL_NAMES if c not in {'pup_gen', 'mouse_idx'}]
    X = df[feature_cols]
    y = df['pup_gen']
    groups = df['mouse_idx']

    X_tv, X_te, y_tv, y_te, groups_tv = hold_out_split(X, y, groups, independent)
    print(f'Holdout split: trainval={len(X_tv)}, test={len(X_te)}')
    print(f'  trainval labels: WT={(y_tv==0).sum()} HT={(y_tv==1).sum()}')
    print(f'  test     labels: WT={(y_te==0).sum()} HT={(y_te==1).sum()}')
    print()

    cv = make_cv(independent, args.n_folds)
    cv_split_groups = groups_tv.values if independent else None

    rng = np.random.RandomState(args.random_state)
    trials: List[Dict[str, Any]] = []

    t0 = time.time()
    for trial_idx in range(args.n_trials):
        params = sample_config(rng)
        fold_metrics: List[Dict[str, float]] = []
        for tr_idx, va_idx in cv.split(X_tv, y_tv, groups=cv_split_groups):
            fold_metrics.append(fold_score(
                X_tv.iloc[tr_idx], y_tv.iloc[tr_idx],
                X_tv.iloc[va_idx], y_tv.iloc[va_idx],
                params,
            ))
        mean = lambda k: float(np.mean([m[k] for m in fold_metrics]))
        row = {
            'trial': trial_idx,
            **params,
            'cv_balanced_acc': mean('balanced_acc'),
            'cv_acc': mean('acc'),
            'cv_ht_recall': mean('ht_recall'),
            'cv_wt_recall': mean('wt_recall'),
            'cv_ht_precision': mean('ht_precision'),
            'cv_wt_precision': mean('wt_precision'),
            'cv_best_iter': mean('best_iter'),
        }
        trials.append(row)
        elapsed = time.time() - t0
        if (trial_idx + 1) % 10 == 0 or trial_idx == args.n_trials - 1:
            top = max(t['cv_balanced_acc'] for t in trials)
            print(f'  [{trial_idx+1:>3}/{args.n_trials}] elapsed={elapsed:6.1f}s  '
                  f'best CV bal_acc so far={top:.4f}')

    trials.sort(key=lambda r: r['cv_balanced_acc'], reverse=True)

    print()
    print('Refitting top-K configs on full trainval and scoring on test...')
    top_configs: List[Dict[str, Any]] = []
    for rank, r in enumerate(trials[:args.top_k], 1):
        params = {k: r[k] for k in SEARCH_SPACE.keys()}
        # 10% margin on top of mean best_iter; clamp to ceiling
        n_est = max(20, min(int(np.ceil(r['cv_best_iter'] * 1.1)), N_EST_CEILING))
        test_metrics = evaluate_on_test(params, n_est, X_tv, y_tv, X_te, y_te)
        top_configs.append({
            'rank': rank,
            **params,
            'n_estimators': n_est,
            'cv_balanced_acc': r['cv_balanced_acc'],
            'cv_ht_recall': r['cv_ht_recall'],
            'cv_wt_recall': r['cv_wt_recall'],
            **test_metrics,
        })
        print(f'  rank {rank}: CV bal_acc={r["cv_balanced_acc"]:.4f} '
              f'-> test acc={test_metrics["test_acc"]:.4f} '
              f'HT_recall={test_metrics["test_ht_recall"]:.4f} '
              f'WT_recall={test_metrics["test_wt_recall"]:.4f}')

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    trials_csv = REPORTS_DIR / f'trials_{suffix}.csv'
    top_json = REPORTS_DIR / f'top_configs_{suffix}.json'
    with trials_csv.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(trials[0].keys()))
        w.writeheader()
        w.writerows(trials)
    with top_json.open('w', encoding='utf-8') as f:
        json.dump(top_configs, f, indent=2)
    print()
    print(f'Saved {len(trials)} trials -> {trials_csv}')
    print(f'Saved top-{args.top_k} test-evaluated configs -> {top_json}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
