import argparse
import itertools
import os
import pickle
import re
import sys
from typing import Optional

# Load .env from repo root so TABPFN_TOKEN is available before any tabpfn import.
_ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
if os.path.isfile(_ENV_PATH):
    with open(_ENV_PATH) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip())

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_sample_weight

from models import (
    MODEL_REGISTRY,
    XGBOOST_FAMILY,
    extra_fit_kwargs,
    has_feature_importance,
    has_training_curves,
    merges_val_into_train,
    supports_eval_set,
    supports_sample_weight,
)
from report import generate_comparison

ALL_DATA_CSV = os.path.join("outputs", "legacy", "aggregated", "all_data.csv")
ALL_DATA_EXTERNAL_CSV = os.path.join(
    "outputs", "external", "aggregated", "tabular", "all_data_external_main.csv"
)
ALL_DATA_EXTERNAL_BASELINE_CSV = os.path.join(
    "outputs", "external", "aggregated", "tabular", "all_data_external_baseline.csv"
)

# Binary genotype in training CSV: WT=0, HT/HET=1 (positive = ASD model)
CLASS_NAMES = ["WT", "HT"]
GENOTYPE_NUM_TO_LABEL = {0: "WT", 1: "HT"}


def resolve_training_csv_path(args: argparse.Namespace) -> str:
    """Return absolute path to the tabular CSV; ``--data-csv`` wins over defaults."""
    if getattr(args, "data_csv", None):
        return os.path.abspath(args.data_csv)
    if getattr(args, "baseline", False):
        return os.path.abspath(ALL_DATA_EXTERNAL_BASELINE_CSV)
    if args.external:
        return os.path.abspath(ALL_DATA_EXTERNAL_CSV)
    return os.path.abspath(ALL_DATA_CSV)


def default_results_subdir(
    model_name: str,
    group_split: bool,
    data_csv_abspath: str,
    strain: Optional[int] = None,
    legacy: bool = False,
) -> str:
    """Build ``results/tabular_models/<subdir>`` name from data source."""
    base = f"{model_name}_legacy" if legacy else model_name
    prefix = f"{base}_strain{strain}" if strain else base
    subdir = prefix + (
        "_subject_eval_independent" if group_split else "_subject_eval_dependent"
    )
    ext_abs = os.path.abspath(ALL_DATA_EXTERNAL_CSV)
    baseline_abs = os.path.abspath(ALL_DATA_EXTERNAL_BASELINE_CSV)
    int_abs = os.path.abspath(ALL_DATA_CSV)
    if data_csv_abspath == baseline_abs:
        subdir += "_baseline"
    elif data_csv_abspath == ext_abs:
        subdir += "_external"
    elif data_csv_abspath == int_abs:
        pass
    else:
        stem = os.path.splitext(os.path.basename(data_csv_abspath))[0]
        safe = re.sub(r"[^0-9a-zA-Z_-]+", "_", stem).strip("_")[:48] or "custom"
        subdir += "_data_" + safe
    if strain:
        return os.path.join("strain", subdir)
    return subdir


COL_NAMES = [
    'syll1_s_freq', 'syll2_s_freq', 'syll3_s_freq', 'syll4_s_freq', 'syll5_s_freq',
    'syll6_s_freq', 'syll7_s_freq', 'syll8_s_freq', 'syll9_s_freq', 'syll10_s_freq',
    'syll1_e_freq', 'syll2_e_freq', 'syll3_e_freq', 'syll4_e_freq', 'syll5_e_freq',
    'syll6_e_freq', 'syll7_e_freq', 'syll8_e_freq', 'syll9_e_freq', 'syll10_e_freq',
    'syll1_dist', 'syll2_dist', 'syll3_dist', 'syll4_dist', 'syll5_dist',
    'syll6_dist', 'syll7_dist', 'syll8_dist', 'syll9_dist', 'syll10_dist',
    'syll1_dur', 'syll2_dur', 'syll3_dur', 'syll4_dur', 'syll5_dur',
    'syll6_dur', 'syll7_dur', 'syll8_dur', 'syll9_dur', 'syll10_dur',
    'mother_gen',
    'pup_sex',
    'avg_ISI_time', 'pup_age', 'session', 'pup_strain',
    'pup_gen',
    'mouse_idx',
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train classifier for Mouse USV ASD detection",
    )
    parser.add_argument(
        '--model',
        type=str,
        default='xgboost',
        choices=sorted(MODEL_REGISTRY),
        help='Model to train (default: xgboost).',
    )
    parser.add_argument(
        '--group-split', '--independent',
        action='store_true',
        help='Subject-independent evaluation: group-aware train/val/test split by subject '
             '(mouse) so no subject appears in more than one set (alias: --independent). '
             'Without this flag, evaluation is subject-dependent (random split; overlap '
             'across sets is allowed).',
    )
    parser.add_argument(
        '--external',
        action='store_true',
        help='RECOMMENDED. Use the externally-validated dataset with correct individual '
             'genotyping (all_data_external_main.csv). This is the preferred data source. '
             'Ignored for choosing the CSV path when --data-csv is set.',
    )
    parser.add_argument(
        '--data-csv',
        type=str,
        default=None,
        metavar='PATH',
        help='Path to the tabular training CSV (48 columns, no header). '
             'Use this to train on a specific aggregate (e.g. a filtered variant). '
             'When set, overrides the path implied by --external / internal default.',
    )
    parser.add_argument(
        '--strain',
        type=int,
        choices=[1, 2],
        default=None,
        help='Keep only rows where pup_strain equals this value (1 or 2). '
             'Applied after loading CSV and before train/val/test split. '
             'Default output goes under results/tabular_models/strain/.',
    )
    parser.add_argument(
        '--baseline',
        action='store_true',
        help='Use the official baseline dataset (all_data_external_baseline.csv) — '
             'external data with invalid_sex and supplement_offspring removed '
             '(Noise==1 syllables retained) on top of the genotype binary filter. '
             'Required data source for all training-matrix runs (Issue #42). '
             'Takes precedence over --external when both are set; ignored when --data-csv is set.',
    )
    parser.add_argument(
        '--legacy',
        action='store_true',
        help='XGBoost only. Reproduce the pre-fix class-balance recipe: '
             'sample_weight=balanced PLUS scale_pos_weight=n_WT/n_HT (double-weighting). '
             'Default (without --legacy) applies only scale_pos_weight, which is the '
             'corrected behavior. Output goes under results/tabular_models/xgboost_legacy_*.',
    )
    parser.add_argument(
        '--results-dir',
        type=str,
        default=None,
        help='Directory for results. Defaults under results/tabular_models/ with '
             '_subject_eval_dependent or _subject_eval_independent (+ _external). '
             'Example: results/tabular_models/tabpfn_subject_eval_independent_external.',
    )
    return parser.parse_args()


def plot_confusion_matrix(cnf_matrix, plots_dir, numbers_type='normalized',
                          class_names=None, title='Confusion matrix',
                          cmap=plt.cm.Blues, file_name='confusionmatrix.png'):
    """Plot and save a confusion matrix figure.
    Normalization can be applied by setting `normalize=True`.
    """
    if class_names is None:
        class_names = CLASS_NAMES
    cnf_matrix_normalized = cnf_matrix.astype('float') / cnf_matrix.sum(axis=1)[:, np.newaxis]
    if numbers_type == 'normalized':
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    plt.figure()
    plt.figure(figsize=(5, 5))
    plt.imshow(cnf_matrix, interpolation='nearest', cmap=cmap)
    plt.title(title, fontsize=18)
    plt.colorbar(plt.imshow(cnf_matrix, interpolation='nearest', cmap=cmap), shrink=0.80)
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45)
    plt.yticks(tick_marks, class_names)

    thresh = 0.8 * cnf_matrix.max() / 1.
    for i, j in itertools.product(range(cnf_matrix.shape[0]), range(cnf_matrix.shape[1])):
        if numbers_type == 'numbers_and_percentage':
            st1 = '{:.2f}%'.format(100 * cnf_matrix_normalized[i, j])
            st2 = '({:2d})'.format(cnf_matrix[i, j])
            plt.text(j, i, st1 + st2,
                     horizontalalignment="center", verticalalignment='bottom',
                     color="white" if cnf_matrix[i, j] > thresh else "black", fontsize=18)
        elif numbers_type == 'percentage':
            plt.text(j, i, format(cnf_matrix_normalized[i, j], '.2f'),
                     horizontalalignment="center", verticalalignment='bottom',
                     color="white" if cnf_matrix[i, j] > thresh else "black", fontsize=18)
        else:
            plt.text(j, i, format(cnf_matrix[i, j], 'd'),
                     horizontalalignment="center", verticalalignment='bottom',
                     color="white" if cnf_matrix[i, j] > thresh else "black", fontsize=18)

    plt.tight_layout()
    plt.ylabel('True label', fontsize=18)
    plt.xlabel('Predicted label', fontsize=18)
    plt.savefig(os.path.join(plots_dir, file_name))


def random_split(X, y, seed):
    """Default random row-level split (baseline behavior)."""
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed, shuffle=True,
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.25, random_state=seed, shuffle=True,
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def group_aware_split(X, y, groups, seed):
    """Split by mouse identity so no mouse appears in more than one set.

    Splits at the mouse level with stratification on pup_gen, then maps
    back to rows.  Asserts that the three sets are fully disjoint.
    """
    mouse_labels = (
        pd.DataFrame({'mouse_idx': groups.values, 'label': y.values})
        .groupby('mouse_idx')['label']
        .first()
    )
    mice = mouse_labels.index.values
    labels = mouse_labels.values

    mice_trainval, mice_test = train_test_split(
        mice, test_size=0.2, random_state=seed, stratify=labels,
    )
    mice_trainval_labels = mouse_labels.loc[mice_trainval].values
    mice_train, mice_val = train_test_split(
        mice_trainval, test_size=0.25, random_state=seed, stratify=mice_trainval_labels,
    )

    train_mask = groups.isin(mice_train)
    val_mask = groups.isin(mice_val)
    test_mask = groups.isin(mice_test)

    train_set = set(groups[train_mask])
    val_set = set(groups[val_mask])
    test_set = set(groups[test_mask])
    assert train_set.isdisjoint(val_set), "Data leakage: mice shared between train and val"
    assert train_set.isdisjoint(test_set), "Data leakage: mice shared between train and test"
    assert val_set.isdisjoint(test_set), "Data leakage: mice shared between val and test"

    return (
        X[train_mask], X[val_mask], X[test_mask],
        y[train_mask], y[val_mask], y[test_mask],
    )


def log_split_info(X_train, y_train, X_val, y_val, X_test, y_test,
                   groups, is_group_split):
    """Print split diagnostics to the log."""
    print('\n=== Split Info ===')
    strategy = "group-aware (by mouse_idx)" if is_group_split else "random (row-level)"
    print(f'Strategy: {strategy}')
    print(f'Train: {len(X_train)} rows | Val: {len(X_val)} rows | Test: {len(X_test)} rows')

    train_mice = set(groups[X_train.index])
    val_mice = set(groups[X_val.index])
    test_mice = set(groups[X_test.index])

    if is_group_split:
        print(f'Train mice ({len(train_mice)}): {sorted(train_mice)}')
        print(f'Val mice   ({len(val_mice)}): {sorted(val_mice)}')
        print(f'Test mice  ({len(test_mice)}): {sorted(test_mice)}')
    else:
        shared_tv = len(train_mice & val_mice)
        shared_tt = len(train_mice & test_mice)
        shared_vt = len(val_mice & test_mice)
        if shared_tv or shared_tt or shared_vt:
            print(f'WARNING: mouse overlap -- train/val: {shared_tv}, '
                  f'train/test: {shared_tt}, val/test: {shared_vt} shared mice')

    for name, y_sub in [('Train', y_train), ('Val', y_val), ('Test', y_test)]:
        counts = y_sub.value_counts().sort_index()
        total = len(y_sub)
        parts = [
            f'{GENOTYPE_NUM_TO_LABEL.get(int(lbl), lbl)}={cnt} ({100*cnt/total:.1f}%)'
            for lbl, cnt in counts.items()
        ]
        print(f'  {name} labels: {", ".join(parts)}')

    print('==================\n')


def main():
    args = parse_args()

    model_name = args.model

    # --- results directory ---------------------------------------------------
    data_csv = resolve_training_csv_path(args)
    if not os.path.isfile(data_csv):
        print(f'Error: data CSV not found: {data_csv}', file=sys.stderr)
        sys.exit(1)

    if args.results_dir:
        results_dir = args.results_dir
    else:
        subdir = default_results_subdir(model_name, args.group_split, data_csv,
                                        strain=args.strain, legacy=args.legacy)
        results_dir = os.path.join('results', 'tabular_models', subdir)

    plots_dir = os.path.join(results_dir, 'plots')
    model_dir = os.path.join(results_dir, 'model')
    logs_dir = os.path.join(results_dir, 'logs')
    for d in [plots_dir, model_dir, logs_dir]:
        os.makedirs(d, exist_ok=True)

    # --- redirect stdout to log ----------------------------------------------
    orig_stdout = sys.stdout
    log_file = open(os.path.join(logs_dir, 'out.txt'), 'w')
    sys.stdout = log_file

    active_flags = []
    if model_name != 'xgboost':
        active_flags.append(f'--model {model_name}')
    if args.group_split:
        active_flags.append('--independent')
    if getattr(args, 'baseline', False):
        active_flags.append('--baseline')
    elif args.external:
        active_flags.append('--external')
    if args.data_csv:
        active_flags.append(f'--data-csv {args.data_csv}')
    if args.strain is not None:
        active_flags.append(f'--strain {args.strain}')
    if args.legacy:
        active_flags.append('--legacy')
    print(f'Active flags: {active_flags if active_flags else "none (baseline)"}')
    print(f'Model: {model_name}')
    print(f'Results directory: {results_dir}')

    # --- load data -----------------------------------------------------------
    print(f'Data source: {data_csv}')
    dataset = pd.read_csv(data_csv, header=None, names=COL_NAMES)

    if args.strain is not None:
        total_before = len(dataset)
        dataset = dataset[dataset['pup_strain'] == args.strain].reset_index(drop=True)
        print(f'Strain filter: kept {len(dataset)}/{total_before} rows '
              f'(pup_strain == {args.strain})')
        print(f'Mice after filter: {dataset["mouse_idx"].nunique()}')
        print(f'pup_gen balance: {dataset["pup_gen"].value_counts().to_dict()}')
        if len(dataset) == 0:
            print('Error: no rows remain after strain filter.', file=sys.stderr)
            sys.exit(1)

    exclude = {'pup_gen', 'mouse_idx'}
    if args.strain is not None:
        exclude.add('pup_strain')
    feature_cols = [c for c in COL_NAMES if c not in exclude]
    X = dataset[feature_cols]
    y = dataset['pup_gen']
    groups = dataset['mouse_idx']

    seed = 100

    # --- train / val / test split --------------------------------------------
    if args.group_split:
        X_train, X_val, X_test, y_train, y_val, y_test = group_aware_split(
            X, y, groups, seed,
        )
    else:
        X_train, X_val, X_test, y_train, y_val, y_test = random_split(X, y, seed)

    log_split_info(X_train, y_train, X_val, y_val, X_test, y_test,
                   groups, args.group_split)

    # TabPFN has no validation step (no early stopping, no hyperparameter tuning
    # at fit time), so the val split is wasted for this model. Merging val back
    # into train gives TabPFN 80% of the data instead of 60%, matching the
    # effective training budget that XGBoost gets when val is used only for
    # training-curve monitoring (not for any model selection decision).
    if merges_val_into_train(model_name):
        X_train = pd.concat([X_train, X_val])
        y_train = pd.concat([y_train, y_val])
        print(f'[tabpfn] val merged into train: {len(X_train)} train rows, '
              f'{len(X_test)} test rows')

    # --- train ---------------------------------------------------------------
    # Class balance: scale_pos_weight=n_WT/n_HT (HT=positive).
    # --legacy ALSO applies sample_weight=balanced (pre-fix double-weighting).
    if model_name in XGBOOST_FAMILY:
        n_wt = int((y_train == 0).sum())
        n_ht = int((y_train == 1).sum())
        scale_pos_weight = n_wt / max(n_ht, 1)
        if args.legacy:
            balance_desc = (
                f'sample_weight=balanced + scale_pos_weight={scale_pos_weight:.4f} '
                f'(LEGACY double-weighting; effective HT:WT ratio ~ '
                f'(n_WT/n_HT)^2 = {scale_pos_weight**2:.2f})'
            )
        else:
            balance_desc = (
                f'scale_pos_weight={scale_pos_weight:.4f} '
                f'(n_WT/n_HT, HT=positive; corrected single-weighting)'
            )
        print(f'Class balance: {balance_desc}')
        model = MODEL_REGISTRY[model_name](seed, scale_pos_weight=scale_pos_weight)
    else:
        if args.legacy:
            print('Warning: --legacy has no effect for non-XGBoost models; ignoring.',
                  file=sys.stderr)
        model = MODEL_REGISTRY[model_name](seed)


    fit_kwargs = extra_fit_kwargs(model_name)
    if supports_sample_weight(model_name) and args.legacy:
        fit_kwargs['sample_weight'] = compute_sample_weight(
            class_weight='balanced', y=y_train,
        )
    if supports_eval_set(model_name):
        fit_kwargs['eval_set'] = [(X_train, y_train), (X_val, y_val)]
        fit_kwargs['verbose'] = False

    model.fit(X_train, y_train, **fit_kwargs)

    # --- evaluate ------------------------------------------------------------
    pred_train = model.predict(X_train)
    train_acc = accuracy_score(y_train, pred_train)
    print('Train Accuracy: ', train_acc)

    pred_test = model.predict(X_test)
    test_acc = accuracy_score(y_test, pred_test)
    print('Test Accuracy: ', test_acc)

    print('Classification Report:')
    print(classification_report(
        y_test, pred_test, zero_division=0, target_names=CLASS_NAMES,
    ))
    report_dict = classification_report(
        y_test, pred_test, zero_division=0, target_names=CLASS_NAMES,
        output_dict=True,
    )

    # --- AUC / error curves (XGBoost only) ------------------------------------
    if has_training_curves(model_name):
        import xgboost as xgb

        eval_results = model.evals_result()
        epochs = len(eval_results['validation_0']['error'])
        x_axis = range(0, epochs)

        fig, ax = plt.subplots(1, 2, figsize=(16, 6))
        ax[0].plot(x_axis, eval_results['validation_0']['auc'], label='Train', linewidth=3)
        ax[0].plot(x_axis, eval_results['validation_1']['auc'], label='Validation', linewidth=3)
        ax[0].set_title('XGBoost AUC-ROC', fontsize=20)
        ax[0].set_ylabel('AUC-ROC', fontsize=20)
        ax[0].set_xlabel('N estimators', fontsize=20)
        ax[0].tick_params(axis='both', which='major', labelsize=16)
        ax[0].legend(fontsize=16)

        ax[1].plot(x_axis, eval_results['validation_0']['error'], label='Train', linewidth=3)
        ax[1].plot(x_axis, eval_results['validation_1']['error'], label='Validation', linewidth=3)
        ax[1].set_title('XGBoost Classification Error', fontsize=20)
        ax[1].set_ylabel('Classification Error', fontsize=20)
        ax[1].set_xlabel('N estimators', fontsize=20)
        ax[1].tick_params(axis='both', which='major', labelsize=16)
        ax[1].legend(fontsize=16)

        plt.savefig(os.path.join(plots_dir, 'AUC_error.png'), dpi=200)
        plt.show()
        plt.tight_layout()

    # --- confusion matrices --------------------------------------------------
    print('\n Confusion Matrix:')
    plot_confusion_matrix(
        confusion_matrix(y_test, pred_test), plots_dir,
        numbers_type='numbers_and_percentage', class_names=CLASS_NAMES,
    )

    plt.rcParams['figure.figsize'] = [15, 10]

    # --- save model ----------------------------------------------------------
    model_filename = f"{model_name}_model.pkl"
    with open(os.path.join(model_dir, model_filename), "wb") as fp:
        pickle.dump(model, fp)

    # --- per-strain evaluation -----------------------------------------------
    if hasattr(X_test, 'columns') and 'pup_strain' in X_test.columns:
        strain1 = np.where(X_test['pup_strain'] == 1)
        strain2 = np.where(X_test['pup_strain'] == 2)
        y_test_arr = np.array(y_test)

        print('\n Confusion Matrix - New pup:')
        if len(strain1[0]) > 0:
            plot_confusion_matrix(
                confusion_matrix(y_test_arr[strain1[0]], pred_test[strain1[0]]),
                plots_dir, numbers_type='numbers_and_percentage',
                class_names=CLASS_NAMES,
                file_name='confusionmatrix_strain1.png',
            )
        else:
            print('No strain 1 data in test set, skipping.')

        print('\n Confusion Matrix - Old pup:')
        if len(strain2[0]) > 0:
            plot_confusion_matrix(
                confusion_matrix(y_test_arr[strain2[0]], pred_test[strain2[0]]),
                plots_dir, numbers_type='numbers_and_percentage',
                class_names=CLASS_NAMES,
                file_name='confusionmatrix_strain2.png',
            )
        else:
            print('No strain 2 data in test set, skipping.')
    else:
        print(f'\nSingle-strain run (strain {args.strain}), skipping per-strain CM split.')

    # --- confusion matrix heatmap --------------------------------------------
    cf_matrix = confusion_matrix(y_test, pred_test)
    print(cf_matrix)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.set(font_scale=1.6)
    ax = sns.heatmap(cf_matrix / cf_matrix.sum(axis=1)[:, np.newaxis],
                     annot=True, fmt='.2%', cmap='Blues')
    ax.set_title('Confusion matrix', fontsize=20)
    ax.set_xlabel('Predicted label', fontsize=18)
    ax.set_ylabel('True label', fontsize=18)
    ax.xaxis.set_ticklabels(CLASS_NAMES)
    ax.yaxis.set_ticklabels(CLASS_NAMES)
    ax.tick_params(axis='both', which='major', labelsize=16)
    plt.savefig(os.path.join(plots_dir, 'conf_matrix.png'), dpi=300)
    plt.show()

    # --- feature importance (XGBoost only) ------------------------------------
    if has_feature_importance(model_name):
        import xgboost as xgb

        print(model.feature_importances_)

        plt.figure()
        plt.bar(range(len(model.feature_importances_)), model.feature_importances_)
        plt.xticks(range(len(model.feature_importances_)), list(X_train.columns),
                   rotation=45, ha="right")
        plt.savefig(os.path.join(plots_dir, 'feature_importances_0.png'), dpi=300)

        fig, ax = plt.subplots(1, 3, figsize=(30, 15))

        xgb.plot_importance(booster=model, importance_type='weight', title='Feature Weight',
                            show_values=False, height=0.5, ax=ax[0])
        ax[0].set_ylabel('Features', fontsize=20)
        ax[0].set_xlabel('F score', fontsize=20)
        ax[0].set_title('Feature Weight', fontsize=24)
        ax[0].tick_params(axis='both', which='major', labelsize=16)

        xgb.plot_importance(booster=model, importance_type='gain', title='Split Mean Gain',
                            show_values=False, height=0.5, ax=ax[1])
        ax[1].set_ylabel('Features', fontsize=20)
        ax[1].set_xlabel('F score', fontsize=20)
        ax[1].set_title('Split Mean Gain', fontsize=24)
        ax[1].tick_params(axis='both', which='major', labelsize=16)

        xgb.plot_importance(model, importance_type='cover', title='Sample Coverage',
                            show_values=False, height=0.5, ax=ax[2])
        ax[2].set_ylabel('Features', fontsize=20)
        ax[2].set_xlabel('F score', fontsize=20)
        ax[2].set_title('Sample Coverage', fontsize=24)
        ax[2].tick_params(axis='both', which='major', labelsize=16)

        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, 'feature_importance_1.png'), dpi=300)
        plt.show()

    # --- comparison vs baseline ----------------------------------------------
    generate_comparison(results_dir, test_acc, train_acc, report_dict, active_flags)

    # --- restore stdout ------------------------------------------------------
    sys.stdout = orig_stdout
    log_file.close()

    print(f'Done. Results saved to {results_dir}/')


if __name__ == '__main__':
    main()
