"""Decision-threshold tuning for the tabular ASD classifiers.

Pure functions, no I/O. Derive a leak-free decision threshold from the
*validation* set and evaluate predictions at an arbitrary threshold on test.

Why this exists: at the hard-coded 0.5 cut, the tabular models
(``scale_pos_weight`` on XGBoost, ``balance_probabilities`` on TabPFN) sit at an
operating point with very high HT recall but low HT precision / low WT recall.
The probabilities separate the classes; the 0.5 cut just doesn't exploit it.
See issues #29 / #51.

Threshold convention: ``predict_at_threshold(score, thr)`` labels HT (class 1)
iff ``score >= thr`` -- the same convention sklearn ``roc_curve`` uses to place
its operating points, so the derived Youden/target-recall thresholds are applied
consistently. At ``thr=0.5`` this matches the model's default prediction for
every realistic probability; it can differ only at the exact-0.5 tie (XGBoost
binary uses strict ``> 0.5``, TabPFN uses argmax), which is measure-zero for
continuous probabilities. The threshold-OFF path in ``train_classifier.py`` still
calls ``model.predict()`` directly, so default-threshold outputs are unchanged.
"""

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)

# WT=0 (negative), HT=1 (positive = ASD model). Matches train_classifier.CLASS_NAMES.
CLASS_NAMES = ["WT", "HT"]

DEFAULT_OBJECTIVE = "youden"
DEFAULT_TARGET_RECALL = 0.80
OBJECTIVES = ("youden", "f1", "target_recall", "balanced")


def _clamp01(x) -> float:
    """Clamp to [0, 1] (guards roc_curve's prepended inf threshold)."""
    return float(min(max(float(x), 0.0), 1.0))


def positive_proba(model, X) -> np.ndarray:
    """P(HT) -- column 1 of predict_proba. HT (class 1) is the positive class."""
    return np.asarray(model.predict_proba(X))[:, 1]


def derive_thresholds(y_val, p_val, target_recall: float = DEFAULT_TARGET_RECALL) -> dict:
    """Derive candidate thresholds from validation probabilities.

    Returns a dict with one threshold per objective plus the validation AUC and
    diagnostics. All thresholds are clamped to [0, 1].

    On a degenerate (single-class) validation set ROC/PR are undefined, so every
    objective falls back to 0.5, ``val_auc`` is None, and
    ``diagnostics['degenerate_val']`` is True.
    """
    y_val = np.asarray(y_val).astype(int)
    p_val = np.asarray(p_val, dtype=float)
    n_pos = int((y_val == 1).sum())
    n_neg = int((y_val == 0).sum())
    diagnostics = {"n_pos": n_pos, "n_neg": n_neg, "degenerate_val": False}

    if len(np.unique(y_val)) < 2:
        diagnostics["degenerate_val"] = True
        return {
            "youden": 0.5,
            "f1": 0.5,
            "target_recall": 0.5,
            "balanced": 0.5,
            "val_auc": None,
            "target_recall_value": float(target_recall),
            "diagnostics": diagnostics,
        }

    # --- Youden's J (headline): maximise TPR - FPR on the val ROC ---
    fpr, tpr, thr = roc_curve(y_val, p_val)
    youden_idx = int(np.argmax(tpr - fpr))
    youden = _clamp01(thr[youden_idx])

    # --- Target HT recall: tpr IS HT recall; highest threshold meeting the floor
    #     (= the highest-precision operating point that still clears the recall bar).
    meets = thr[tpr >= target_recall]
    target_thr = _clamp01(meets.max()) if meets.size else 0.0

    # --- Max F1 on HT via the PR curve. precision_recall_curve returns
    #     len(prec) == len(thr_pr) + 1; drop the trailing recall=0 anchor to align.
    prec, rec, thr_pr = precision_recall_curve(y_val, p_val)
    p, r = prec[:-1], rec[:-1]
    f1 = 2 * p * r / np.clip(p + r, 1e-12, None)
    f1_thr = _clamp01(thr_pr[int(np.argmax(f1))]) if thr_pr.size else 0.5

    # --- Balanced accuracy: dense sweep over [0, 1] ---
    grid = np.linspace(0.0, 1.0, 1001)
    bal = [balanced_accuracy_score(y_val, (p_val >= t).astype(int)) for t in grid]
    balanced = float(grid[int(np.argmax(bal))])

    return {
        "youden": youden,
        "f1": f1_thr,
        "target_recall": target_thr,
        "balanced": balanced,
        "val_auc": float(roc_auc_score(y_val, p_val)),
        "target_recall_value": float(target_recall),
        "diagnostics": diagnostics,
    }


def select_threshold(thresholds: dict, objective: str = DEFAULT_OBJECTIVE) -> float:
    """Pick the headline threshold by objective name."""
    if objective not in OBJECTIVES:
        raise ValueError(f"Unknown objective {objective!r}; choose from {OBJECTIVES}")
    return float(thresholds[objective])


def predict_at_threshold(proba, thr: float) -> np.ndarray:
    """Hard HT/WT labels: HT (1) iff P(HT) >= thr."""
    return (np.asarray(proba, dtype=float) >= thr).astype(int)


def evaluate(y_true, proba, thr: float) -> dict:
    """Metrics for predictions thresholded at ``thr``.

    AUC is threshold-independent (computed from the probabilities) and is None
    when ``y_true`` has a single class.
    """
    y_true = np.asarray(y_true).astype(int)
    proba = np.asarray(proba, dtype=float)
    y_pred = predict_at_threshold(proba, thr)

    try:
        auc = float(roc_auc_score(y_true, proba)) if len(np.unique(y_true)) > 1 else None
    except ValueError:
        auc = None

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])  # [[tn, fp], [fn, tp]]
    report = classification_report(
        y_true, y_pred, labels=[0, 1], target_names=CLASS_NAMES,
        output_dict=True, zero_division=0,
    )
    per_class = {
        name: {
            "precision": float(report.get(name, {}).get("precision", 0.0)),
            "recall": float(report.get(name, {}).get("recall", 0.0)),
            "f1": float(report.get(name, {}).get("f1-score", 0.0)),
            "support": int(report.get(name, {}).get("support", 0)),
        }
        for name in CLASS_NAMES
    }

    return {
        "threshold": float(thr),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "auc": auc,
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
        "report_dict": report,
    }
