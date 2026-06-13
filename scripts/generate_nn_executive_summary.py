"""Generate the neural-network (sequence models) executive summary.

Reads the per-run ``results.json`` files produced by
``src/classification/neural_networks/sequence_pipeline.py --baseline`` and emits:

  results/neural_networks/executive_summaries/sequence_models/
    ├── master_metrics.csv     # one row per run (machine-readable)
    ├── master_metrics.md      # the same table, rendered for the PR / stakeholders
    └── executive_summary.html # styled report, mirrors the legacy sequence summary

Robustness — HT (disease) class detection
------------------------------------------
HT is the **minority** class. The current pipeline encodes ``0=WT, 1=HT`` so HT metrics
live under ``classification_report["1.0"]`` — but a *legacy* results.json had the mapping
**inverted** (``HT (0)``). To never hardcode the index, HT is detected as the class key
with the **smaller support**, and that choice is cross-checked against the ``HT (N)`` row
printed in the run's ``logs/out.txt``. A mismatch aborts under ``--strict``.

Usage
-----
    .venv/bin/python scripts/generate_nn_executive_summary.py [--strict]
"""

from __future__ import annotations

import argparse
import csv
import datetime
import glob
import html
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Display + ordering -----------------------------------------------------------
MODEL_DISPLAY = {"bilstm": "BiLSTM", "cnn1d": "1D-CNN", "transformer": "Transformer"}
MODEL_ORDER = ["bilstm", "cnn1d", "transformer"]
SPLIT_ORDER = ["dependent", "independent"]
MODEL_PARAM_NOTE = {  # how each architecture reads the sequence (for the Approach table)
    "bilstm": "Step-by-step with memory, reads forward and backward",
    "cnn1d": "Sliding window (size 3) detecting local patterns",
    "transformer": "Every syllable attends to every other syllable simultaneously",
}
MODEL_TYPE = {"bilstm": "Recurrent (LSTM)", "cnn1d": "Convolutional", "transformer": "Self-Attention"}

CLASS_KEY_RE = re.compile(r"^\d+\.\d+$")
OUT_HT_INDEX_RE = re.compile(r"\bHT\s*\((\d+)\)")


class SummaryError(RuntimeError):
    """Raised when the inputs are inconsistent and --strict is set."""


# --- loading / parsing --------------------------------------------------------
def find_runs(results_root: str) -> list[str]:
    """Return run result.json paths one level under the root, excluding summaries.

    Matches both the baseline runs (``*_subject_eval_*_baseline/``) and the
    experiment runs under an ``experiments/`` root with arbitrary dir names.
    """
    pattern = os.path.join(results_root, "*", "results.json")
    return sorted(p for p in glob.glob(pattern) if "executive_summaries" not in p)


def _parse_out_txt_ht_index(run_dir: str) -> int | None:
    """Recover the HT class index from the ``HT (N)`` row printed in logs/out.txt."""
    out_txt = os.path.join(run_dir, "logs", "out.txt")
    if not os.path.isfile(out_txt):
        return None
    with open(out_txt, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = OUT_HT_INDEX_RE.search(line)
            if m:
                return int(m.group(1))
    return None


def load_run(results_json: str, strict: bool) -> dict:
    """Load one run, detect the HT class, and return a flat metrics dict."""
    run_dir = os.path.dirname(results_json)
    with open(results_json, encoding="utf-8") as fh:
        data = json.load(fh)

    report = data["classification_report"]
    class_keys = [k for k in report if CLASS_KEY_RE.match(k)]
    if len(class_keys) != 2:
        raise SummaryError(f"{results_json}: expected 2 class keys, got {class_keys}")

    # HT = minority class (smaller support).
    ht_key = min(class_keys, key=lambda k: report[k]["support"])
    wt_key = next(k for k in class_keys if k != ht_key)

    # Cross-check against the index the pipeline itself printed (HT (N)).
    logged_idx = _parse_out_txt_ht_index(run_dir)
    detected_idx = int(float(ht_key))
    if logged_idx is not None and logged_idx != detected_idx:
        msg = (f"{results_json}: HT-class mismatch — minority support says index "
               f"{detected_idx}, but logs/out.txt printed 'HT ({logged_idx})'.")
        if strict:
            raise SummaryError(msg)
        print(f"WARNING: {msg} Using the logged index.", file=sys.stderr)
        ht_key, wt_key = f"{logged_idx}.0", f"{1 - logged_idx}.0"

    ht, wt = report[ht_key], report[wt_key]
    independent = bool(data.get("subject_eval_independent", data.get("group_split", False)))
    return {
        "model": data["model"],
        "split": "independent" if independent else "dependent",
        "label": os.path.basename(run_dir),
        "test_accuracy": data["test_accuracy"],
        "test_auc": data["test_auc"],
        # balanced metrics (additive; None on older runs -> rendered as n/a)
        "test_balanced_accuracy": data.get("test_balanced_accuracy"),
        "test_average_precision": data.get("test_average_precision"),
        "test_mcc": data.get("test_mcc"),
        "test_macro_f1": data.get("test_macro_f1"),
        "train_accuracy": data.get("train_accuracy"),
        "ht_precision": ht["precision"], "ht_recall": ht["recall"], "ht_f1": ht["f1-score"],
        "ht_support": int(ht["support"]),
        "wt_precision": wt["precision"], "wt_recall": wt["recall"], "wt_f1": wt["f1-score"],
        "wt_support": int(wt["support"]),
        "epochs_trained": data.get("epochs_trained"),
        "best_val_auc": data.get("best_val_auc"),
        "total_params": data.get("total_params"),
        "num_train": data.get("num_train"), "num_val": data.get("num_val"),
        "num_test": data.get("num_test"),
        "cv_folds": (data.get("cv") or {}).get("n_folds"),
        "results_dir": os.path.relpath(run_dir, REPO_ROOT),
        "ht_class_index": detected_idx,
    }


_FLOAT_RE = re.compile(r"[-+]?\d*\.?\d+")


def parse_tabular_comparison(txt_path: str) -> dict | None:
    """Parse the current-run metrics out of a tabular comparison_vs_baseline.txt."""
    if not os.path.isfile(txt_path):
        return None
    out: dict = {}
    section = None
    with open(txt_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            s = line.strip()
            if s.startswith("Test Accuracy:"):
                m = _FLOAT_RE.search(s.split(":", 1)[1])
                if m:
                    out["test_accuracy"] = float(m.group())
            elif s.startswith("--- WT ---"):
                section = "wt"
            elif s.startswith("--- HT ---"):
                section = "ht"
            elif section and s.split(":", 1)[0].strip() in ("Precision", "Recall", "F1"):
                key, rest = s.split(":", 1)
                m = _FLOAT_RE.search(rest)
                if m:
                    out[f"{section}_{key.strip().lower()}"] = float(m.group())
    return out or None


# --- formatting helpers -------------------------------------------------------
def pct(x) -> str:
    return "n/a" if x is None else f"{x * 100:.1f}%"


def f2(x) -> str:
    return "n/a" if x is None else f"{x:.2f}"


def f3(x) -> str:
    return "n/a" if x is None else f"{x:.3f}"


def cls(value, good_at, bad_below) -> str:
    """Return a CSS class for a metric cell."""
    if value is None:
        return "neutral"
    if value < bad_below:
        return "highlight"
    if value >= good_at:
        return "good"
    return ""


# --- master table -------------------------------------------------------------
MASTER_COLUMNS = [
    "label", "model", "split", "test_balanced_accuracy", "test_auc",
    "test_average_precision", "test_mcc", "test_accuracy", "ht_recall",
    "ht_precision", "ht_f1", "wt_f1", "test_macro_f1", "epochs_trained",
    "total_params", "num_test", "ht_support", "wt_support", "cv_folds",
    "ht_class_index", "results_dir",
]


def write_master_csv(runs: list[dict], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=MASTER_COLUMNS, extrasaction="ignore",
                           lineterminator="\n")
        w.writeheader()
        for r in runs:
            w.writerow(r)


def write_master_md(runs: list[dict], path: str) -> None:
    head = ("| Run | Model | Split | Bal Acc | AUC | PR-AUC | MCC | Acc "
            "| HT Recall | HT Prec | WT F1 | Epochs |")
    sep = "|" + "---|" * 12
    lines = [head, sep]
    # rank by balanced accuracy (the imbalance-robust metric) when available
    ordered = sorted(runs, key=lambda r: (r.get("test_balanced_accuracy") or -1), reverse=True)
    for r in ordered:
        lines.append(
            f"| {r.get('label', '')} | {MODEL_DISPLAY.get(r['model'], r['model'])} | {r['split']} "
            f"| {pct(r.get('test_balanced_accuracy'))} | {f3(r['test_auc'])} "
            f"| {f3(r.get('test_average_precision'))} | {f2(r.get('test_mcc'))} "
            f"| {pct(r['test_accuracy'])} | {pct(r['ht_recall'])} | {pct(r['ht_precision'])} "
            f"| {f2(r['wt_f1'])} | {r['epochs_trained']} |"
        )
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# --- HTML rendering -----------------------------------------------------------
STYLE = """
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Inter', sans-serif; color: #1a1a2e; background: #f8f9fb; padding: 40px; line-height: 1.6; }
  .container { max-width: 1100px; margin: 0 auto; background: #fff; border-radius: 12px; box-shadow: 0 2px 20px rgba(0,0,0,0.06); overflow: hidden; }
  .header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #fff; padding: 36px 44px; }
  .header h1 { font-size: 22px; font-weight: 700; margin-bottom: 4px; }
  .header p { font-size: 13px; color: #a8b2d1; }
  .body { padding: 36px 44px; }
  h2 { font-size: 15px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #16213e; margin: 32px 0 12px; border-bottom: 2px solid #e8ecf4; padding-bottom: 6px; }
  h2:first-child { margin-top: 0; }
  h3 { font-size: 14px; font-weight: 700; color: #16213e; margin: 20px 0 8px; }
  p, li { font-size: 14px; color: #333; }
  ul { padding-left: 20px; margin: 8px 0; }
  li { margin-bottom: 6px; }
  table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }
  th { background: #16213e; color: #fff; padding: 10px 14px; text-align: left; font-weight: 600; }
  td { padding: 9px 14px; border-bottom: 1px solid #e8ecf4; }
  tr:last-child td { border-bottom: none; }
  .highlight { color: #e63946; font-weight: 600; }
  .good { color: #2a9d8f; font-weight: 600; }
  .neutral { color: #6c757d; font-weight: 600; }
  .banner { border-radius: 8px; padding: 20px 24px; margin: 16px 0; }
  .banner-warn { background: linear-gradient(135deg, #e63946 0%, #c1121f 100%); color: #fff; }
  .banner-warn p { color: #fde8e8; }
  .banner-warn h3 { color: #fff; margin-top: 0; }
  .banner-info { background: linear-gradient(135deg, #457b9d 0%, #1d3557 100%); color: #fff; }
  .banner-info p { color: #d4e4f0; }
  .banner-info h3 { color: #fff; margin-top: 0; }
  .banner-ok { background: linear-gradient(135deg, #2a9d8f 0%, #264653 100%); color: #fff; }
  .banner-ok p { color: #d4f0e8; }
  .banner-ok h3 { color: #fff; margin-top: 0; }
  .config-table td:first-child { font-weight: 600; }
  .config-table tr:nth-child(even) { background: #f8f9fb; }
  .legend { background: #f4f6fb; border-radius: 8px; padding: 16px 20px; margin: 12px 0; font-size: 13px; }
  .legend strong { color: #16213e; }
  code { background: #eef2ff; padding: 2px 6px; border-radius: 4px; font-size: 12px; }
  th code { background: rgba(255,255,255,0.15); color: #fff; }
  pre { background: #1a1a2e; color: #a8b2d1; border-radius: 8px; padding: 16px 20px; margin: 12px 0; overflow-x: auto; font-size: 13px; line-height: 1.5; }
  pre code { background: none; padding: 0; color: inherit; }
  .footer { padding: 20px 44px; background: #f4f6fb; font-size: 11px; color: #888; text-align: center; }
  @media print { body { padding: 0; background: #fff; } .container { box-shadow: none; } }
"""


def _results_table(runs: list[dict]) -> str:
    rows = []
    for r in runs:
        rows.append(
            "      <tr>\n"
            f"        <td>{MODEL_DISPLAY.get(r['model'], r['model'])}</td>"
            f"<td>{r['split'].capitalize()}</td>\n"
            f"        <td class=\"{cls(r.get('test_balanced_accuracy'), 0.65, 0.50)}\">{pct(r.get('test_balanced_accuracy'))}</td>"
            f"<td class=\"{cls(r['test_auc'], 0.70, 0.55)}\">{f3(r['test_auc'])}</td>"
            f"<td>{f3(r.get('test_average_precision'))}</td>\n"
            f"        <td>{pct(r['test_accuracy'])}</td>"
            f"<td class=\"{cls(r['ht_recall'], 0.50, 0.10)}\">{pct(r['ht_recall'])}</td>"
            f"<td>{pct(r['ht_precision'])}</td>\n"
            f"        <td class=\"{cls(r['wt_f1'], 0.70, 0.40)}\">{f2(r['wt_f1'])}</td>"
            f"<td>{r['epochs_trained']}</td>\n"
            "      </tr>"
        )
    return (
        '    <table>\n'
        '      <tr><th>Model</th><th>Split</th><th>Bal Acc</th><th>Test AUC</th>'
        '<th>PR-AUC</th><th>Test Acc</th><th>HT Recall</th><th>HT Prec</th>'
        '<th>WT F1</th><th>Epochs</th></tr>\n'
        + "\n".join(rows) + "\n    </table>\n"
    )


def _comparison_table(runs: list[dict], tabular: dict[str, dict | None]) -> str:
    """Sequence (group/independent) vs tabular XGBoost baseline, per split."""
    rows = []
    for split in SPLIT_ORDER:
        tab = tabular.get(split)
        if tab:
            rows.append(
                "      <tr>\n"
                f"        <td>XGBoost (tabular)</td><td>{split.capitalize()}</td>\n"
                f"        <td>{pct(tab.get('test_accuracy'))}</td>"
                f"<td class=\"{cls(tab.get('ht_recall'), 0.50, 0.10)}\">{pct(tab.get('ht_recall'))}</td>"
                f"<td>{f2(tab.get('ht_f1'))}</td><td>{f2(tab.get('wt_f1'))}</td>\n"
                "        <td>Recording (~12,323)</td>\n      </tr>"
            )
        for r in (x for x in runs if x["split"] == split):
            rows.append(
                "      <tr>\n"
                f"        <td>{MODEL_DISPLAY.get(r['model'], r['model'])} (seq)</td>"
                f"<td>{split.capitalize()}</td>\n"
                f"        <td>{pct(r['test_accuracy'])}</td>"
                f"<td class=\"{cls(r['ht_recall'], 0.50, 0.10)}\">{pct(r['ht_recall'])}</td>"
                f"<td>{f2(r['ht_f1'])}</td><td>{f2(r['wt_f1'])}</td>\n"
                "        <td>Session (~408)</td>\n      </tr>"
            )
    return (
        '    <table>\n'
        '      <tr><th>Model</th><th>Split</th><th>Test Acc</th><th>HT Recall</th>'
        '<th>HT F1</th><th>WT F1</th><th>Data Level</th></tr>\n'
        + "\n".join(rows) + "\n    </table>\n"
    )


def _dir_guide(runs: list[dict]) -> str:
    rows = "\n".join(
        f"      <tr><td><code>{html.escape(r['results_dir'])}/</code></td>"
        f"<td>{MODEL_DISPLAY.get(r['model'], r['model'])}, {r['split']} split</td></tr>"
        for r in runs
    )
    return ('    <table>\n      <tr><th>Directory</th><th>Description</th></tr>\n'
            + rows + "\n    </table>\n")


def _analysis(runs: list[dict]) -> str:
    by = {(r["model"], r["split"]): r for r in runs}
    best = max(runs, key=lambda r: (r["ht_recall"] or 0))
    collapsed = [r for r in runs if (r["ht_recall"] or 0) < 0.10]
    parts = [
        f"<p>Across the six configurations, the highest HT (disease) recall is "
        f"<strong>{MODEL_DISPLAY.get(best['model'], best['model'])} "
        f"({best['split']})</strong> at <strong>{pct(best['ht_recall'])}</strong> "
        f"(test accuracy {pct(best['test_accuracy'])}, AUC {f3(best['test_auc'])}).</p>"
    ]
    if collapsed:
        names = ", ".join(f"{MODEL_DISPLAY.get(r['model'], r['model'])} ({r['split']})"
                          for r in collapsed)
        parts.append(
            f"<p>HT recall <strong>collapses below 10%</strong> for: {names}. "
            "These models default to the majority (WT) class — high headline accuracy "
            "masks a failure to detect the disease class. Compare HT recall, not accuracy.</p>"
        )
    # dependent vs independent gap, per model
    gaps = []
    for m in MODEL_ORDER:
        dep, ind = by.get((m, "dependent")), by.get((m, "independent"))
        if dep and ind:
            gaps.append(f"{MODEL_DISPLAY[m]}: {pct(dep['test_accuracy'])} → "
                        f"{pct(ind['test_accuracy'])} test accuracy")
    if gaps:
        parts.append("<p><strong>Dependent → Independent (subject-level) split:</strong> "
                     + "; ".join(gaps) + ". The independent split removes subject leakage "
                     "and is the honest generalization estimate.</p>")
    return "\n    ".join(parts)


def render_html(runs: list[dict], tabular: dict[str, dict | None], date_label: str) -> str:
    n_sessions = runs[0]["num_train"] + runs[0]["num_val"] + runs[0]["num_test"] if runs else 0
    head = (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"UTF-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        "<title>Neural Networks Executive Summary — Mouse USV ASD Classification</title>\n"
        "<style>" + STYLE + "</style>\n</head>\n<body>\n<div class=\"container\">\n"
    )
    header = (
        '  <div class="header">\n'
        '    <h1>Neural Networks Executive Summary &mdash; Sequence Models (Baseline)</h1>\n'
        f'    <p>BiLSTM vs 1D-CNN vs Transformer &nbsp;|&nbsp; 6 Configurations &nbsp;|&nbsp; '
        f'<code>--baseline</code> dataset &nbsp;|&nbsp; {html.escape(date_label)}</p>\n'
        '  </div>\n'
    )
    objective = (
        '    <h2>Objective</h2>\n'
        '    <p>Evaluate whether <strong>sequence-based deep learning models</strong> '
        '(BiLSTM, 1D-CNN, Transformer) can classify mouse pups as <strong>Wild-Type (WT)</strong> '
        'or <strong>ASD-model (HT)</strong> from the temporal ordering of ultrasonic vocalizations '
        '(USVs), on the official <code>--baseline</code> dataset. This complements the tabular '
        'models (XGBoost, TabPFN) that use aggregated per-recording features and discard ordering. '
        'See <code>docs/NEURAL_NETWORK_BASELINE.md</code>.</p>\n'
    )
    approach = (
        '    <h2>Approach</h2>\n'
        '    <h3>Data Representation</h3>\n'
        '    <p>Instead of aggregating syllables into one feature vector per recording, we preserve '
        'the <strong>ordered sequence of syllables</strong> within each mouse-day-session '
        f'(<strong>{n_sessions} sessions</strong> in the baseline split; median ~236 syllables/session). '
        'Each syllable is a 14-dimensional vector:</p>\n'
        '    <ul>\n'
        '      <li><strong>Continuous (4):</strong> Start Point (Hz), End Point (Hz), Duration, ISI time</li>\n'
        '      <li><strong>Syllable type (8):</strong> learned embedding (11 types &rarr; 8 dims)</li>\n'
        '      <li><strong>Binary flags (2):</strong> Noise indicator, Recording-boundary marker</li>\n'
        '    </ul>\n'
        '    <p>Static metadata (mother genotype, sex, day, session) is concatenated to the encoder '
        'output before classification.</p>\n'
        '    <h3>Models</h3>\n'
        '    <table class="config-table">\n'
        '      <tr><th>Model</th><th>Type</th><th>Parameters</th><th>How It Reads the Sequence</th></tr>\n'
        + "".join(
            f'      <tr><td>{MODEL_DISPLAY[m]}</td><td>{MODEL_TYPE[m]}</td>'
            f'<td>{next((r["total_params"] for r in runs if r["model"] == m), "n/a"):,}</td>'
            f'<td>{MODEL_PARAM_NOTE[m]}</td></tr>\n'
            for m in MODEL_ORDER if any(r["model"] == m for r in runs)
        )
        + '    </table>\n'
        '    <h3>Training Setup</h3>\n'
        '    <ul>\n'
        '      <li><strong>Framework:</strong> PyTorch, CPU training</li>\n'
        '      <li><strong>Max sequence length:</strong> 256 syllables</li>\n'
        '      <li><strong>Loss:</strong> BCEWithLogitsLoss with pos_weight for class balancing</li>\n'
        '      <li><strong>Optimizer:</strong> Adam (lr=0.001) with ReduceLROnPlateau</li>\n'
        '      <li><strong>Early stopping:</strong> patience 15 on validation AUC; seed 100</li>\n'
        '      <li><strong>Split:</strong> 60% train / 20% val / 20% test</li>\n'
        '    </ul>\n'
    )
    results = (
        '    <h2>Results &mdash; All 6 Configurations</h2>\n'
        + _results_table(runs)
        + '    <div class="legend"><strong>Reading the table:</strong> HT is the minority '
        '(disease) class — <strong>HT Recall</strong> is the clinically important metric '
        '(what fraction of ASD-model pups are caught). High accuracy with low HT recall means '
        'the model is just predicting the majority WT class.</div>\n'
    )
    comparison = (
        '    <h2>Comparison vs Tabular Baseline</h2>\n'
        '    <p>Same <code>--baseline</code> dataset; tabular XGBoost numbers parsed from its '
        '<code>comparison_vs_baseline.txt</code>. Tabular operates on aggregated recordings, '
        'sequence models on ordered per-session syllables.</p>\n'
        + _comparison_table(runs, tabular)
    )
    analysis = '    <h2>Analysis</h2>\n    ' + _analysis(runs) + "\n"
    guide = '    <h2>Results Directory Guide</h2>\n' + _dir_guide(runs)
    appendix = (
        '    <h2>Appendix &mdash; Reproduce &amp; Read</h2>\n'
        '    <h3>Commands (CPU)</h3>\n'
        '    <pre><code>for m in bilstm cnn1d transformer; do\n'
        '  .venv/bin/python src/classification/neural_networks/sequence_pipeline.py --model $m --baseline\n'
        '  .venv/bin/python src/classification/neural_networks/sequence_pipeline.py --model $m --baseline --independent\n'
        'done\n'
        '.venv/bin/python scripts/generate_nn_executive_summary.py --strict</code></pre>\n'
        '    <h3>Per-run output files</h3>\n'
        '    <ul>\n'
        '      <li><code>results.json</code> — metrics (accuracy, AUC, per-class precision/recall/F1)</li>\n'
        '      <li><code>plots/</code> — training_curves, confusion_matrix(+counts), roc_curve</li>\n'
        '      <li><code>model/&lt;model&gt;_best.pt</code> + <code>scaler.pkl</code></li>\n'
        '      <li><code>logs/out.txt</code> — full training log</li>\n'
        '    </ul>\n'
        '    <h3>Target variable</h3>\n'
        '    <p>Binary genotype, encoded <strong>0 = WT, 1 = HT</strong> (current pipeline). '
        'HT metrics therefore live under <code>classification_report["1.0"]</code> and are the '
        'minority class. (Legacy pre-baseline runs used the inverted encoding; this report '
        'detects HT by minority support and cross-checks the printed <code>HT (N)</code> index, '
        'so it is correct regardless.)</p>\n'
    )
    footer = (
        '  <div class="footer">Generated by scripts/generate_nn_executive_summary.py '
        f'from results/neural_networks/*_baseline/results.json &nbsp;|&nbsp; {html.escape(date_label)}</div>\n'
        '</div>\n</body>\n</html>\n'
    )
    return (head + header + '  <div class="body">\n' + objective + approach + results
            + comparison + analysis + guide + appendix + '  </div>\n' + footer)


# --- main ---------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results-root", default=os.path.join("results", "neural_networks"))
    ap.add_argument("--tabular-root", default=os.path.join("results", "tabular_models"))
    ap.add_argument("--out-dir", default=os.path.join(
        "results", "neural_networks", "executive_summaries", "sequence_models"))
    ap.add_argument("--date-label", default=None,
                    help="Label shown in the report header (default: current YYYY-MM).")
    ap.add_argument("--strict", action="store_true",
                    help="Fail if fewer than 6 runs are found or an HT-class mismatch occurs.")
    args = ap.parse_args()

    run_paths = find_runs(args.results_root)
    if args.strict and len(run_paths) != 6:
        print(f"ERROR: expected 6 baseline runs, found {len(run_paths)}: {run_paths}",
              file=sys.stderr)
        return 1
    if not run_paths:
        print(f"ERROR: no runs found under {args.results_root}", file=sys.stderr)
        return 1

    runs = [load_run(p, args.strict) for p in run_paths]
    # canonical ordering: model, then dependent before independent
    runs.sort(key=lambda r: (MODEL_ORDER.index(r["model"]) if r["model"] in MODEL_ORDER else 99,
                             SPLIT_ORDER.index(r["split"]) if r["split"] in SPLIT_ORDER else 99))

    tabular = {
        split: parse_tabular_comparison(os.path.join(
            args.tabular_root, f"xgboost_subject_eval_{split}_baseline",
            "comparison_vs_baseline.txt"))
        for split in SPLIT_ORDER
    }

    date_label = args.date_label or datetime.date.today().strftime("%B %Y")
    os.makedirs(args.out_dir, exist_ok=True)
    write_master_csv(runs, os.path.join(args.out_dir, "master_metrics.csv"))
    write_master_md(runs, os.path.join(args.out_dir, "master_metrics.md"))
    with open(os.path.join(args.out_dir, "executive_summary.html"), "w", encoding="utf-8") as fh:
        fh.write(render_html(runs, tabular, date_label))

    print(f"Wrote summary for {len(runs)} runs to {args.out_dir}")
    for r in runs:
        print(f"  {r['model']:<11} {r['split']:<11} acc={pct(r['test_accuracy'])} "
              f"HT_recall={pct(r['ht_recall'])} (HT=class {r['ht_class_index']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
