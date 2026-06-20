# xgboost_tuned_dependent_subject_eval_dependent_baseline — XGBoost (tuned) · subject-dependent · threshold objectives

> Re-deriving the XGBoost-tuned decision threshold under four objectives from saved validation probabilities — same model, no retraining.

## Overview
- **Model:** XGBoost with the tuned hyperparameters from the 200-trial random search for the **dependent**
  split. No retraining here — thresholds are re-derived from stored validation probabilities.
- **Evaluation split:** subject-dependent — train/val/test split by row/session, so the same mouse can
  appear in train and test (leakage → optimistic; the honest leak-free numbers live in the independent runs).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Validation prob set: WT 1865 / HT 600; test support WT 1818 / HT 647. Val AUC 0.895, test AUC 0.885.
- **What was adapted vs the base model:** decision-threshold objective selection only — the classifier and
  features are unchanged. Four objectives (`youden`, `f1`, `target_recall` ~0.80, `balanced`) plus the 0.5
  default are compared. For a **dependent** split the recommended objective is **`f1`** (`target_recall`
  is the pick for independent splits, not this one).

## Results (test set)
| Objective | thr | acc | balacc | HT rec | HT prec | HT F1 | WT rec |
|---|---|---|---|---|---|---|---|
| @0.5 | 0.500 | 0.771 | 0.798 | 0.856 | 0.540 | 0.662 | 0.740 |
| youden | 0.366 | 0.731 | 0.800 | 0.947 | 0.493 | 0.649 | 0.653 |
| **f1** | **0.568** | **0.789** | **0.787** | **0.784** | **0.572** | **0.661** | **0.791** |
| target_recall | 0.547 | 0.785 | 0.792 | 0.808 | 0.562 | 0.663 | 0.776 |
| balanced | 0.365 | 0.731 | 0.800 | 0.947 | 0.493 | 0.649 | 0.653 |

`target_recall` uses an HT recall floor of 0.80; `youden` and `balanced` collapse to the same low cut (0.366/0.365).
Recommended-objective (`f1`) confusion matrix (rows = true, cols = pred): `[[WT→WT 1438, WT→HT 380], [HT→WT 140, HT→HT 507]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
Recommended objective (`f1`, thr 0.568) vs base at its 0.5 cut.
| Metric | This run (f1) | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.789 | 0.733 | +0.056 |
| Weighted F1 | 0.798 | 0.749 | +0.049 |
| WT F1 | 0.847 | 0.785 | +0.062 |
| HT F1 | 0.661 | 0.649 | +0.012 |
| HT recall | 0.784 | 0.940 | −0.156 |
| HT precision | 0.572 | 0.496 | +0.076 |

## Key insights
- At the `f1` cut the tuned model is a clean accuracy/precision win — test accuracy 0.789 (+0.056) and
  HT precision 0.572 (+0.076) vs base — by trading away HT recall (0.784, −0.156); it no longer flags
  almost every pup as HT the way the base 0.5 model does.
- The objective spread is wide: `youden`/`balanced` push HT recall to 0.947 but drop HT precision to
  0.493 and overall accuracy to 0.731, while `f1`/`target_recall` raise the cut (~0.55–0.57) for a more
  balanced operating point. Balanced accuracy is nearly flat across all five (0.787–0.800).
- HT F1 barely moves across objectives (0.649–0.663) — re-thresholding redistributes recall vs precision
  but cannot manufacture class separation beyond the fixed AUC (test 0.885).
- `target_recall` lands at HT recall 0.808 (just above its 0.80 floor) with accuracy 0.785 — a sensible
  middle ground if missing ~1 in 5 HT pups (the `f1` operating point) is too costly.

## Recommendations
- For this dependent split use the **`f1`** threshold (0.568): best accuracy/weighted-F1 with HT
  precision lifted to 0.572. If HT recall matters more than precision, switch to `target_recall` (0.808
  recall at 0.785 accuracy); avoid `youden`/`balanced` here — they sacrifice ~6 pts of accuracy for recall.

## Artifacts
- `objective_comparison.txt` — human-readable per-objective table + thresholds + test confusion matrices.
- `objective_metrics.json` — full per-objective metrics (accuracy, balanced accuracy, AUC, per-class
  precision/recall/F1/support, confusion matrices) and the derived thresholds.
- Probabilities source: `results/tabular_models/threshold/xgboost_tuned_dependent_subject_eval_dependent_baseline/probabilities_*.csv` (no model/plots in this folder — thresholds only).
- See the threshold-objectives index: [`../README.md`](../README.md).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `objective_comparison.txt` + `objective_metrics.json` · summary auto-generated*
