"""Compare decision-threshold OBJECTIVES across the 6 tabular runs (no retraining).

The threshold objective only changes which cut is selected from the validation
probabilities -- the trained model and its predicted probabilities are identical
for every objective. So instead of re-running each model four times (which would
mean ~4h of TabPFN CPU inference), this reads the per-sample probabilities each
threshold run already saved
(results/tabular_models/threshold/<run>/probabilities_{val,test}.csv),
re-derives the threshold under each objective on val, and re-evaluates on test.
The result is mathematically identical to re-running with --threshold-objective.

Outputs go to a SEPARATE folder to avoid confusion with the adopted Youden run:
    results/tabular_models/threshold_objectives/
        <run_subdir>/objective_comparison.txt   # per-run table + confusion matrices
        <run_subdir>/objective_metrics.json     # machine-readable, all objectives
        summary_objectives.txt                  # master 6-runs x objectives table
        summary_objectives.csv                  # same, for analysis

A self-check asserts the recomputed Youden metrics match the values stored in the
original threshold_metrics.json (proving the no-retrain shortcut is exact).

Usage:
    python scripts/compare_threshold_objectives.py
    python scripts/compare_threshold_objectives.py --target-recall 0.85
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src" / "classification" / "tabular"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from threshold import derive_thresholds, evaluate, select_threshold  # noqa: E402
from run_threshold_matrix import RUNS  # noqa: E402

THRESHOLD_ROOT = REPO_ROOT / "results" / "tabular_models" / "threshold"
OUT_ROOT = REPO_ROOT / "results" / "tabular_models" / "threshold_objectives"
OBJECTIVES = ["youden", "f1", "target_recall", "balanced"]


def read_probs(subdir, split):
    path = THRESHOLD_ROOT / subdir / f"probabilities_{split}.csv"
    if not path.is_file():
        return None, None
    df = pd.read_csv(path)
    return df["y_true"].to_numpy(), df["p_ht"].to_numpy()


def _cm(ev):
    (tn, fp), (fn, tp) = ev["confusion_matrix"]
    return f"[[{tn}, {fp}], [{fn}, {tp}]]"


def selfcheck_youden(subdir, eval_youden):
    """Assert recomputed Youden test accuracy matches the stored threshold_metrics.json."""
    path = THRESHOLD_ROOT / subdir / "threshold_metrics.json"
    if not path.is_file():
        return "no stored json (skipped)"
    stored = json.load(open(path))["metrics"]["test_at_tuned"]["accuracy"]
    delta = abs(stored - eval_youden["accuracy"])
    assert delta < 1e-9, f"Youden recompute mismatch for {subdir}: {delta}"
    return f"OK (matches stored, delta={delta:.2e})"


def per_run_report(run, target_recall):
    y_val, p_val = read_probs(run["subdir"], "val")
    y_test, p_test = read_probs(run["subdir"], "test")
    if y_val is None or y_test is None:
        print(f"  WARNING: missing probabilities for {run['subdir']}, skipping", file=sys.stderr)
        return None

    thresholds = derive_thresholds(y_val, p_val, target_recall=target_recall)
    rows = [("@0.5", 0.5, evaluate(y_test, p_test, 0.5))]
    for obj in OBJECTIVES:
        thr = select_threshold(thresholds, obj)
        rows.append((obj, thr, evaluate(y_test, p_test, thr)))

    check = selfcheck_youden(run["subdir"], dict(rows[1][2]))

    n_neg = int((np.asarray(y_val) == 0).sum())
    n_pos = int((np.asarray(y_val) == 1).sum())
    test_auc = rows[0][2]["auc"]
    val_auc = thresholds.get("val_auc")

    lines = [
        "=" * 80,
        "THRESHOLD OBJECTIVE COMPARISON",
        f"{run['name']}",
        "=" * 80,
        f"Source: results/tabular_models/threshold/{run['subdir']}/probabilities_*.csv",
        "Val AUC: {}   Test AUC: {}   Val labels: WT={} HT={}".format(
            "n/a" if val_auc is None else f"{val_auc:.4f}",
            "n/a" if test_auc is None else f"{test_auc:.4f}", n_neg, n_pos),
        f"Youden self-check vs stored run: {check}",
        "",
        "{:<14}{:>7}{:>8}{:>8}{:>8}{:>8}{:>8}{:>8}{:>8}".format(
            "Objective", "thr", "acc", "balacc", "HTrec", "HTprec", "HTf1", "WTrec", "WTprec"),
        "-" * 80,
    ]
    for name, thr, ev in rows:
        pc = ev["per_class"]
        lines.append("{:<14}{:>7.3f}{:>8.3f}{:>8.3f}{:>8.3f}{:>8.3f}{:>8.3f}{:>8.3f}{:>8.3f}".format(
            name, thr, ev["accuracy"], ev["balanced_accuracy"],
            pc["HT"]["recall"], pc["HT"]["precision"], pc["HT"]["f1"],
            pc["WT"]["recall"], pc["WT"]["precision"]))
    lines += [
        "",
        f"(target_recall objective uses HT recall floor {target_recall:.2f})",
        "",
        "Confusion matrices (test)  [[WT->WT, WT->HT], [HT->WT, HT->HT]]:",
    ]
    for name, _thr, ev in rows:
        lines.append(f"  {name:<14}{_cm(ev)}")
    lines.append("=" * 80)

    out_dir = OUT_ROOT / run["subdir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "objective_comparison.txt").write_text("\n".join(lines) + "\n")

    def _slim(ev):
        return {k: v for k, v in ev.items() if k != "report_dict"}

    payload = {
        "run": run["name"],
        "subdir": run["subdir"],
        "split": "independent" if "--independent" in run["args"] else "dependent",
        "target_recall": target_recall,
        "val_auc": val_auc,
        "test_auc": test_auc,
        "thresholds": thresholds,
        "by_objective": {name: {"threshold": thr, **_slim(ev)} for name, thr, ev in rows},
    }
    (out_dir / "objective_metrics.json").write_text(json.dumps(payload, indent=2, default=str))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target-recall", type=float, default=0.80,
                        help="HT recall floor for the target_recall objective (default 0.80).")
    args = parser.parse_args()

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    master = []  # (run_name, objective, thr, ev)
    for run in RUNS:
        print(f"Processing {run['name']} ...")
        rows = per_run_report(run, args.target_recall)
        if rows is None:
            continue
        for name, thr, ev in rows:
            master.append((run["name"], name, thr, ev))

    # --- master summary table ---
    header = "{:<40}{:<14}{:>7}{:>8}{:>8}{:>8}{:>8}{:>8}".format(
        "Run", "Objective", "thr", "acc", "balacc", "HTrec", "HTprec", "WTrec")
    lines = ["=" * len(header),
             "THRESHOLD OBJECTIVES -- master comparison (test set)",
             f"(target_recall floor = {args.target_recall:.2f}; @0.5 = default)",
             "=" * len(header), header, "-" * len(header)]
    last_run = None
    for run_name, obj, thr, ev in master:
        if last_run is not None and run_name != last_run:
            lines.append("")
        last_run = run_name
        pc = ev["per_class"]
        lines.append("{:<40}{:<14}{:>7.3f}{:>8.3f}{:>8.3f}{:>8.3f}{:>8.3f}{:>8.3f}".format(
            run_name[:39], obj, thr, ev["accuracy"], ev["balanced_accuracy"],
            pc["HT"]["recall"], pc["HT"]["precision"], pc["WT"]["recall"]))
    lines += ["-" * len(header),
              "Legend: thr=applied threshold, acc=accuracy, balacc=balanced acc,",
              "        HTrec/HTprec=HT recall/precision, WTrec=WT recall.",
              "=" * len(header)]
    (OUT_ROOT / "summary_objectives.txt").write_text("\n".join(lines) + "\n")
    print("\n" + "\n".join(lines))

    # --- master CSV ---
    with open(OUT_ROOT / "summary_objectives.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["run", "objective", "threshold", "accuracy", "balanced_accuracy",
                    "ht_recall", "ht_precision", "ht_f1", "wt_recall", "wt_precision", "test_auc"])
        for run_name, obj, thr, ev in master:
            pc = ev["per_class"]
            w.writerow([run_name, obj, f"{thr:.4f}", f"{ev['accuracy']:.4f}",
                        f"{ev['balanced_accuracy']:.4f}", f"{pc['HT']['recall']:.4f}",
                        f"{pc['HT']['precision']:.4f}", f"{pc['HT']['f1']:.4f}",
                        f"{pc['WT']['recall']:.4f}", f"{pc['WT']['precision']:.4f}",
                        "" if ev["auc"] is None else f"{ev['auc']:.4f}"])

    print(f"\nWritten to {OUT_ROOT}/ (summary_objectives.txt/.csv + per-run dirs)")


if __name__ == "__main__":
    main()
