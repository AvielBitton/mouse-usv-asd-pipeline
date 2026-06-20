# `threshold_objectives/` — objective comparison

## Why this exists
Follow-up to [`../threshold/`](../threshold/). Youden is a fine default, but on
this data it isn't always the best operating point — on subject-dependent splits
it over-pushes HT recall and hurts accuracy. This folder compares **all four
objectives** (`youden` / `f1` / `target_recall` / `balanced`) plus the `0.5`
default across the 6 runs, so we can pick the right cut per scenario.

## No retraining
The objective only changes which threshold is selected from the (objective-
independent) validation probabilities — the trained model and its probabilities
are identical for every objective. So this reads the per-sample probabilities
already saved under `../threshold/<run>/probabilities_{val,test}.csv` and just
re-derives + re-evaluates each objective. A self-check confirms the recomputed
Youden numbers match the stored full-run metrics exactly (delta 0.0) for all 6
runs. This avoids ~4h of TabPFN CPU inference.

## What's in here
- `summary_objectives.txt` — master table: 6 runs × {0.5, youden, f1,
  target_recall, balanced}, on test.
- `summary_objectives.csv` — same data for Excel / analysis.
- One folder per run, each containing:
  - `objective_comparison.txt` — per-run table + confusion matrices per objective.
  - `objective_metrics.json` — machine-readable, all objectives.

## Key finding
- **Subject-dependent splits:** `f1` (or `target_recall`) give the best accuracy
  and a balanced operating point (e.g. tabpfn dep acc 0.78 → 0.82). Youden
  over-pushes recall.
- **Subject-independent splits:** weak AUC (~0.75–0.78); youden/f1/balanced
  collapse to a near-degenerate "predict HT for almost everyone" point (HT recall
  ~1.0, WT recall ~0.59). `target_recall` keeps a controlled operating point.

Recommendation: adopt `f1` for dependent runs, `target_recall` (≈0.80) for
independent runs. Full writeup in issue #73.

## How to regenerate
```bash
python scripts/compare_threshold_objectives.py                  # instant, from saved probabilities
python scripts/compare_threshold_objectives.py --target-recall 0.85
```
