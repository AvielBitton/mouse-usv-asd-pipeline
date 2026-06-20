"""Run decision-threshold tuning across the 6 primary tabular runs (issues #29/#51).

Invokes ``src/classification/tabular/train_classifier.py --baseline --threshold auto``
once per (model x split) in the primary matrix, then reads each run's
``threshold_metrics.json`` and prints + writes a consolidated 0.5-vs-tuned table.

The matrix (matching the existing non-threshold runs):
    1. xgboost                  / dependent
    2. xgboost                  / independent
    3. xgboost_tuned_dependent  / dependent
    4. xgboost_tuned_independent/ independent
    5. tabpfn                   / dependent
    6. tabpfn                   / independent

Outputs land under results/tabular_models/threshold/<run_subdir>/ and a summary
at results/tabular_models/threshold/summary_matrix.txt.

Usage:
    python scripts/run_threshold_matrix.py                       # all 6, youden
    python scripts/run_threshold_matrix.py --objective f1
    python scripts/run_threshold_matrix.py --runs 1,5            # subset by index
    python scripts/run_threshold_matrix.py --runs tabpfn         # subset by substring
    python scripts/run_threshold_matrix.py --dry-run             # print commands only

Note: the tabpfn runs require TABPFN_TOKEN in .env (loaded by train_classifier.py).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRAIN_SCRIPT = "src/classification/tabular/train_classifier.py"
THRESHOLD_ROOT = REPO_ROOT / "results" / "tabular_models" / "threshold"

RUNS = [
    {"name": "xgboost / dependent",
     "subdir": "xgboost_subject_eval_dependent_baseline",
     "args": ["--model", "xgboost"]},
    {"name": "xgboost / independent",
     "subdir": "xgboost_subject_eval_independent_baseline",
     "args": ["--model", "xgboost", "--independent"]},
    {"name": "xgboost_tuned_dependent / dependent",
     "subdir": "xgboost_tuned_dependent_subject_eval_dependent_baseline",
     "args": ["--model", "xgboost_tuned_dependent"]},
    {"name": "xgboost_tuned_independent / independent",
     "subdir": "xgboost_tuned_independent_subject_eval_independent_baseline",
     "args": ["--model", "xgboost_tuned_independent", "--independent"]},
    {"name": "tabpfn / dependent",
     "subdir": "tabpfn_subject_eval_dependent_baseline",
     "args": ["--model", "tabpfn"]},
    {"name": "tabpfn / independent",
     "subdir": "tabpfn_subject_eval_independent_baseline",
     "args": ["--model", "tabpfn", "--independent"]},
]


def select_runs(tokens):
    """Filter RUNS by 1-based index or case-insensitive substring of the name."""
    if not tokens:
        return list(range(len(RUNS)))
    chosen = []
    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        if tok.isdigit():
            i = int(tok) - 1
            if 0 <= i < len(RUNS):
                chosen.append(i)
            else:
                print(f"Warning: run index {tok} out of range 1..{len(RUNS)}", file=sys.stderr)
        else:
            matches = [i for i, r in enumerate(RUNS) if tok.lower() in r["name"].lower()]
            if not matches:
                print(f"Warning: no run matches {tok!r}", file=sys.stderr)
            chosen.extend(matches)
    seen, ordered = set(), []
    for i in chosen:
        if i not in seen:
            seen.add(i)
            ordered.append(i)
    return ordered


def build_cmd(run, objective, target_recall):
    return [
        sys.executable, TRAIN_SCRIPT,
        "--baseline", "--threshold", "auto",
        "--threshold-objective", objective,
        "--target-recall", str(target_recall),
        *run["args"],
    ]


def _g(d, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d


def load_metrics(run):
    path = THRESHOLD_ROOT / run["subdir"] / "threshold_metrics.json"
    if not path.is_file():
        return None
    with open(path) as f:
        return json.load(f)


def fmt(x, spec="{:.3f}"):
    return "n/a" if x is None else spec.format(x)


def consolidated_table(indices, results):
    """Build the printable 0.5-vs-tuned summary table as a list of lines."""
    header = (
        f"{'Run':<40}{'thr':>7}{'tAUC':>7}"
        f"{'acc.5':>7}{'acc.t':>7}{'bal.5':>7}{'bal.t':>7}"
        f"{'HTr.5':>7}{'HTr.t':>7}{'HTp.5':>7}{'HTp.t':>7}{'WTr.5':>7}{'WTr.t':>7}"
    )
    lines = ["=" * len(header),
             "THRESHOLD MATRIX -- 0.5 (.5) vs tuned (.t)",
             "=" * len(header), header, "-" * len(header)]
    for i in indices:
        run = RUNS[i]
        m = results.get(i)
        if m is None:
            lines.append(f"{run['name'][:39]:<40}{'-- no metrics (run failed or skipped) --':>0}")
            continue
        a05 = _g(m, "metrics", "test_at_0.5", default={})
        at = _g(m, "metrics", "test_at_tuned", default={})
        lines.append(
            f"{run['name'][:39]:<40}"
            f"{fmt(_g(m, 'tuned_threshold')):>7}{fmt(_g(m, 'test_auc')):>7}"
            f"{fmt(_g(a05, 'accuracy')):>7}{fmt(_g(at, 'accuracy')):>7}"
            f"{fmt(_g(a05, 'balanced_accuracy')):>7}{fmt(_g(at, 'balanced_accuracy')):>7}"
            f"{fmt(_g(a05, 'per_class', 'HT', 'recall')):>7}{fmt(_g(at, 'per_class', 'HT', 'recall')):>7}"
            f"{fmt(_g(a05, 'per_class', 'HT', 'precision')):>7}{fmt(_g(at, 'per_class', 'HT', 'precision')):>7}"
            f"{fmt(_g(a05, 'per_class', 'WT', 'recall')):>7}{fmt(_g(at, 'per_class', 'WT', 'recall')):>7}"
        )
    lines += ["-" * len(header),
              "Legend: thr=applied threshold, tAUC=test AUC, acc=accuracy, "
              "bal=balanced acc,",
              "        HTr/HTp=HT recall/precision, WTr=WT recall. "
              ".5=@0.5, .t=@tuned.",
              "=" * len(header)]
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--objective", default="youden",
                        choices=["youden", "f1", "target_recall", "balanced"],
                        help="Threshold objective for every run (default: youden).")
    parser.add_argument("--target-recall", type=float, default=0.80,
                        help="HT recall floor for --objective target_recall (default: 0.80).")
    parser.add_argument("--runs", default=None,
                        help="Comma-separated subset by 1-based index or name substring "
                             "(e.g. '1,5' or 'tabpfn'). Default: all 6.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the commands without running them.")
    args = parser.parse_args()

    tokens = args.runs.split(",") if args.runs else []
    indices = select_runs(tokens)
    if not indices:
        print("No runs selected.", file=sys.stderr)
        sys.exit(1)

    print(f"Selected {len(indices)} run(s); objective={args.objective}\n")
    failures = []
    for n, i in enumerate(indices, 1):
        run = RUNS[i]
        cmd = build_cmd(run, args.objective, args.target_recall)
        print(f"[{n}/{len(indices)}] {run['name']}")
        print("    " + " ".join(cmd))
        if args.dry_run:
            continue
        result = subprocess.run(cmd, cwd=REPO_ROOT)
        if result.returncode != 0:
            print(f"    FAILED (exit {result.returncode})", file=sys.stderr)
            failures.append(run["name"])

    if args.dry_run:
        return

    results = {i: load_metrics(RUNS[i]) for i in indices}
    lines = consolidated_table(indices, results)
    print("\n" + "\n".join(lines))

    THRESHOLD_ROOT.mkdir(parents=True, exist_ok=True)
    summary_path = THRESHOLD_ROOT / "summary_matrix.txt"
    with open(summary_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nSummary written to {summary_path}")

    if failures:
        print(f"\n{len(failures)} run(s) failed: {', '.join(failures)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
