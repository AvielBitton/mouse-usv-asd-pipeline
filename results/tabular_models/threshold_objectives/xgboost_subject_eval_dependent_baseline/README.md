# xgboost_subject_eval_dependent_baseline — XGBoost · subject-dependent · threshold objectives

> Re-derive the XGBoost decision threshold under four objectives (no retraining), same model as the base.

## Overview
- **Model:** XGBoost (untuned legacy recipe) — **identical** to the base model; this run only re-derives
  the decision threshold from saved validation probabilities. No retraining.
- **Evaluation split:** subject-dependent — rows split randomly, so the same mouse can appear in train and
  test (leakage; optimistic). Same split as the base model.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Val labels WT 1865 / HT 600; test 2,465 recordings (WT 1818 / HT 647). Val AUC 0.891, test AUC 0.876.
- **What was adapted vs the base model:** decision-threshold objective selection only. Four objectives —
  `youden`, `f1`, `target_recall` (HT recall floor 0.80), `balanced` — are compared against the 0.5
  default. **Recommended objective for a dependent split: `f1`.**

## Results (test set)
| Objective | thr | Acc | BalAcc | HT rec | HT prec | HT F1 | WT rec |
|---|---|---|---|---|---|---|---|
| @0.5 | 0.500 | 0.727 | 0.795 | 0.937 | 0.490 | 0.643 | 0.653 |
| youden | 0.528 | 0.737 | 0.794 | 0.915 | 0.499 | 0.646 | 0.673 |
| **f1** | 0.617 | **0.767** | 0.774 | 0.788 | 0.538 | 0.639 | 0.759 |
| target_recall | 0.630 | 0.778 | 0.776 | 0.771 | 0.555 | 0.646 | 0.780 |
| balanced | 0.528 | 0.736 | 0.794 | 0.915 | 0.499 | 0.646 | 0.673 |

Confusion matrix at `f1` (rows = true, cols = pred): `[[WT→WT 1380, WT→HT 438], [HT→WT 137, HT→HT 510]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
Recommended `f1` objective vs base (base is at the 0.5 cut):
| Metric | This run (`f1`) | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.767 | 0.733 | +0.034 |
| Weighted F1 | 0.778 | 0.749 | +0.029 |
| WT F1 | 0.828 | 0.785 | +0.043 |
| HT F1 | 0.639 | 0.649 | −0.010 |
| HT recall | 0.788 | 0.940 | −0.152 |
| HT precision | 0.538 | 0.496 | +0.042 |

## Key insights
- Raising the cut to 0.617 (the `f1` objective) trades minority recall for overall quality: **HT recall
  drops to 0.788** (−0.152) but **HT precision climbs to 0.538** (+0.042) and accuracy reaches 0.767
  (+0.034). HT F1 is essentially unchanged (−0.010) — the model just stops over-calling HT.
- The base 0.5 cut is degenerate-leaning toward the minority: HT recall 0.937 with HT precision 0.490
  means ~1 in 2 HT calls is a false positive. Every higher-threshold objective fixes precision.
- `youden` and `balanced` land at nearly the same threshold (0.528) and metrics — both barely move off the
  0.5 default. Only `f1` and `target_recall` (0.617 / 0.630) meaningfully shift the operating point.
- Balanced accuracy is best at the 0.5/youden/balanced cuts (~0.795) and dips slightly at `f1` (0.774);
  the gain there is in plain accuracy and minority precision, not in class-balanced separation.

## Recommendations
- Use the **`f1`** threshold (0.617) for this dependent split: best accuracy/precision balance with no
  retraining. If missing ASD-model pups is the dominant cost, prefer `target_recall` — note it still only
  reaches HT recall 0.771 on test (below its 0.80 val floor) because the dependent test set is harder.
- For the leak-free independent split, prefer `target_recall` (~0.80) instead; see `../README.md`.

## Artifacts
- `objective_comparison.txt` — per-objective thresholds, test metrics, and confusion matrices.
- `objective_metrics.json` — full per-objective per-class metrics + thresholds (machine-readable).
- Metrics source: `objective_comparison.txt` + `objective_metrics.json`.
- Threshold methodology and cross-objective context: `../README.md`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `objective_comparison.txt` + `objective_metrics.json` · summary auto-generated*
