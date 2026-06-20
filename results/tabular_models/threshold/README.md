# `threshold/` — adopted decision-threshold runs (Youden)

## Why this exists
Issues #29 / #51. At the hard-coded **0.5** cut the tabular models sit at a poor
operating point (very high HT recall but low HT precision / WT recall on
dependent splits; HT *under*-detection on independent splits). The predicted
probabilities separate the classes — 0.5 just doesn't exploit it. These runs
derive a decision threshold from the **validation** set (leak-free) and apply it
to **test**, reporting metrics at both **0.5** and the **tuned** threshold.

Objective here is **Youden's J** (max TPR−FPR), the headline choice in #29. For a
comparison of all objectives see [`../threshold_objectives/`](../threshold_objectives/).

## What's in here
- `summary_matrix.txt` — one-glance table of all 6 runs, 0.5 vs tuned.
- One folder per run (6 primary runs: xgboost / xgboost_tuned / tabpfn ×
  dependent / independent), each containing:
  - `threshold_report.txt` — 0.5-vs-tuned side-by-side + confusion matrices.
  - `threshold_metrics.json` — machine-readable metrics for both thresholds.
  - `probabilities_val.csv` / `probabilities_test.csv` — per-sample P(HT) (the
    val file is the leak-free source the threshold is derived from).
  - `plots/roc_curve.png` (val ROC + operating points), `conf_matrix_thr0.5.png`,
    `conf_matrix_thr_tuned.png`.

TabPFN model pickles (~225 MB) are gitignored; everything else is committed.

## How to regenerate
```bash
python scripts/run_threshold_matrix.py                  # all 6 runs, Youden
python scripts/run_threshold_matrix.py --objective f1   # any other objective
```
TabPFN runs need `TABPFN_TOKEN` in `.env`. Splits are reproducible (`seed=100`).
In threshold mode TabPFN keeps its validation split held out (no merge into
train) so the threshold is derived leak-free.
