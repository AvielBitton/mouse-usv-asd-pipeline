"""Reporting for the threshold-tuning runs.

Writes the human-readable ``threshold_report.txt`` (chosen threshold + objective
+ rationale, with a side-by-side 0.5-vs-tuned test block), the machine-readable
``threshold_metrics.json`` (for issue #51 Phase E packs), per-sample probability
CSVs, the validation ROC plot with operating points marked, and confusion-matrix
plots at both thresholds.

Kept separate from ``report.py`` (the existing paper-baseline comparison), which
is left untouched and still called once at the tuned operating point.
"""

import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import roc_auc_score, roc_curve

CLASS_NAMES = ["WT", "HT"]


def _json_default(o):
    """Make numpy scalars/arrays JSON-serialisable."""
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def save_probabilities(results_dir, *, split_name, index, y_true, proba, thr_tuned=None):
    """Write per-sample P(HT) to ``probabilities_<split_name>.csv``.

    Includes the original row index (traceable back to the source CSV), the true
    label, P(HT), the default-0.5 prediction, and -- for test -- the tuned
    prediction.
    """
    proba = np.asarray(proba, dtype=float)
    df = pd.DataFrame({
        "row_index": np.asarray(index),
        "y_true": np.asarray(y_true).astype(int),
        "p_ht": proba,
        "pred_thr0.5": (proba >= 0.5).astype(int),
    })
    if thr_tuned is not None:
        df["pred_tuned"] = (proba >= thr_tuned).astype(int)
    path = os.path.join(results_dir, f"probabilities_{split_name}.csv")
    df.to_csv(path, index=False)
    return path


def _operating_point(y_val, p_val, thr):
    """(FPR, TPR) achieved on val at a given threshold (exact, not interpolated)."""
    y_val = np.asarray(y_val).astype(int)
    pred = (np.asarray(p_val, dtype=float) >= thr).astype(int)
    pos, neg = y_val == 1, y_val == 0
    tpr = float(pred[pos].mean()) if pos.any() else 0.0
    fpr = float(pred[neg].mean()) if neg.any() else 0.0
    return fpr, tpr


def plot_roc_with_operating_points(results_dir, y_val, p_val, thresholds):
    """Validation ROC curve with the 0.5 / Youden / max-F1 / target-recall points."""
    plots_dir = os.path.join(results_dir, "plots")
    path = os.path.join(plots_dir, "roc_curve.png")
    fig, ax = plt.subplots(figsize=(7, 7))

    if thresholds.get("val_auc") is None:
        ax.text(0.5, 0.5, "Validation set is single-class;\nROC undefined (threshold fell back to 0.5).",
                ha="center", va="center", fontsize=14)
        ax.set_axis_off()
        plt.tight_layout()
        plt.savefig(path, dpi=200)
        plt.close(fig)
        return path

    fpr, tpr, _ = roc_curve(y_val, p_val)
    auc = roc_auc_score(y_val, p_val)
    ax.plot(fpr, tpr, lw=2, color="#1f77b4", label=f"Val ROC (AUC = {auc:.3f})")
    ax.plot([0, 1], [0, 1], "--", color="grey", lw=1)

    tr = thresholds["target_recall_value"]
    points = [
        ("default 0.5", 0.5, "#000000", "o"),
        (f"Youden (J) = {thresholds['youden']:.3f}", thresholds["youden"], "#d62728", "*"),
        (f"max-F1 = {thresholds['f1']:.3f}", thresholds["f1"], "#2ca02c", "s"),
        (f"recall>={tr:.2f} = {thresholds['target_recall']:.3f}", thresholds["target_recall"], "#9467bd", "D"),
    ]
    for label, thr, color, marker in points:
        fp, tp = _operating_point(y_val, p_val, thr)
        ax.scatter([fp], [tp], s=120, color=color, marker=marker, zorder=5,
                   edgecolors="white", linewidths=0.8, label=label)

    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("False positive rate (1 - WT recall)", fontsize=13)
    ax.set_ylabel("True positive rate (HT recall)", fontsize=13)
    ax.set_title("Validation ROC + operating points", fontsize=15)
    ax.legend(loc="lower right", fontsize=10)
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close(fig)
    return path


def plot_confusion_at(results_dir, y_true, proba, thr, file_name, title):
    """Test confusion matrix (counts + row-normalised %) at threshold ``thr``."""
    from sklearn.metrics import confusion_matrix

    plots_dir = os.path.join(results_dir, "plots")
    path = os.path.join(plots_dir, file_name)
    pred = (np.asarray(proba, dtype=float) >= thr).astype(int)
    cm = confusion_matrix(y_true, pred, labels=[0, 1])
    row_sums = cm.sum(axis=1, keepdims=True)

    annot = np.empty(cm.shape, dtype=object)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            pct = cm[i, j] / row_sums[i, 0] if row_sums[i, 0] else 0.0
            annot[i, j] = f"{cm[i, j]}\n{pct:.1%}"

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.set(font_scale=1.3)
    sns.heatmap(cm, annot=annot, fmt="", cmap="Blues", cbar=False,
                xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES, ax=ax)
    ax.set_title(title, fontsize=16)
    ax.set_xlabel("Predicted label", fontsize=13)
    ax.set_ylabel("True label", fontsize=13)
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close(fig)
    return path


def _fmt_cm(cm):
    """Render a 2x2 confusion matrix [[tn, fp], [fn, tp]] as text rows."""
    (tn, fp), (fn, tp) = cm
    return [
        "             pred WT   pred HT",
        f"  true WT  {tn:>8} {fp:>9}",
        f"  true HT  {fn:>8} {tp:>9}",
    ]


_METRIC_ROWS = [
    ("Accuracy", lambda e: e["accuracy"]),
    ("Balanced accuracy", lambda e: e["balanced_accuracy"]),
    ("HT recall", lambda e: e["per_class"]["HT"]["recall"]),
    ("HT precision", lambda e: e["per_class"]["HT"]["precision"]),
    ("HT F1", lambda e: e["per_class"]["HT"]["f1"]),
    ("WT recall", lambda e: e["per_class"]["WT"]["recall"]),
    ("WT precision", lambda e: e["per_class"]["WT"]["precision"]),
    ("WT F1", lambda e: e["per_class"]["WT"]["f1"]),
]


def write_threshold_report(results_dir, *, model_name, objective, thresholds,
                           eval_05, eval_tuned, eval_val, tabpfn_no_merge, active_flags):
    """Write the human-readable threshold_report.txt."""
    tuned_thr = eval_tuned["threshold"]
    diag = thresholds.get("diagnostics", {})
    lines = [
        "=" * 64,
        "DECISION-THRESHOLD TUNING",
        "=" * 64,
        f"Model: {model_name}",
        f"Objective (headline): {objective}",
        "Active flags: {}".format(", ".join(active_flags) if active_flags else "none"),
        "",
        "Validation AUC: {}".format(
            "n/a" if thresholds.get("val_auc") is None else f"{thresholds['val_auc']:.4f}"),
        "Test AUC:       {}   (threshold-independent)".format(
            "n/a" if eval_tuned.get("auc") is None else f"{eval_tuned['auc']:.4f}"),
        f"Val label counts: WT={diag.get('n_neg', '?')}, HT={diag.get('n_pos', '?')}",
        "",
        "Candidate thresholds (derived from the VALIDATION set):",
    ]
    tr = thresholds["target_recall_value"]
    labels = {
        "youden": "youden        ",
        "f1": "f1            ",
        "target_recall": "target_recall ",
        "balanced": "balanced      ",
    }
    extra = {"target_recall": f"  (target HT recall >= {tr:.2f})"}
    for key in ("youden", "f1", "target_recall", "balanced"):
        marker = "   <-- HEADLINE" if key == objective else ""
        lines.append(f"  {labels[key]}: {thresholds[key]:.4f}{extra.get(key, '')}{marker}")
    lines.append("")

    if diag.get("degenerate_val"):
        lines += ["WARNING: validation set is single-class -- ROC/PR undefined; "
                  "threshold fell back to 0.5.", ""]
    if tabpfn_no_merge:
        lines += ["NOTE: TabPFN val held OUT (not merged into train) so its probabilities are",
                  "      leak-free for threshold derivation -- this model trains on ~60% of the",
                  "      data instead of the 80% used by the non-threshold TabPFN run, so the",
                  "      @0.5 numbers here differ slightly from that run (not a regression).", ""]

    lines += [
        "-" * 64,
        f"TEST METRICS:  @0.5 (default)   vs   @tuned ({objective} = {tuned_thr:.4f})",
        "-" * 64,
        "{:<22}{:>10}{:>10}{:>10}".format("", "@0.5", "@tuned", "delta"),
    ]
    for label, getter in _METRIC_ROWS:
        v05, vt = getter(eval_05), getter(eval_tuned)
        delta = vt - v05
        sign = "+" if delta >= 0 else ""
        lines.append("{:<22}{:>10.3f}{:>10.3f}{:>10}".format(
            label, v05, vt, f"{sign}{delta:.3f}"))

    lines += ["", "Confusion matrix @0.5:"]
    lines += _fmt_cm(eval_05["confusion_matrix"])
    lines += ["", f"Confusion matrix @tuned ({tuned_thr:.4f}):"]
    lines += _fmt_cm(eval_tuned["confusion_matrix"])

    lines += [
        "",
        "Note: comparison_vs_baseline.txt in this directory reflects the TUNED",
        "operating point. The @0.5 column above is the default-threshold reference.",
        "=" * 64,
    ]

    path = os.path.join(results_dir, "threshold_report.txt")
    with open(path, "w") as fout:
        fout.write("\n".join(lines) + "\n")
    return path


def write_metrics_json(results_dir, payload):
    """Write the machine-readable threshold_metrics.json."""
    path = os.path.join(results_dir, "threshold_metrics.json")
    with open(path, "w") as fout:
        json.dump(payload, fout, indent=2, default=_json_default)
    return path
