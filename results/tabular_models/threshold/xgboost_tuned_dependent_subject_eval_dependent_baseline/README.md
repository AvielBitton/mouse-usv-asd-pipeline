# xgboost_tuned_dependent_subject_eval_dependent_baseline — XGBoost (tuned) · subject-dependent · threshold (Youden)

> Tuned XGBoost on the baseline data with a **Youden-J decision threshold** (0.366) swapped in for the default 0.5 cut — no retraining.

## Overview
- **Model:** XGBoost, dependent-tuned recipe (`xgboost_tuned_dependent`; hyperparameters from a 200-trial
  random search tuned for the dependent split). Same fitted model as the base run — only the decision
  cut changes.
- **What was adapted vs the base model:** decision-threshold tuning only. The Youden-J point that
  maximizes balanced accuracy is selected from **leak-free validation probabilities** and applied at
  test time. No weights are re-fit; the 0.5 cut is replaced by **0.366**.
- **Evaluation split:** subject-dependent — random row-level split (`--baseline`), so the same mouse can
  appear in train, val and test (logged overlap: 105 shared mice train/test). Optimistic by design,
  matching the base model's setting.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 2,465 recordings (WT 73.8% / HT 26.2%).
- **Threshold-independent ranking:** validation AUC 0.896, test AUC 0.885.

## Results (test set)
Tuned operating point (Youden = 0.366):
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.972 | 0.493 | — |
| Recall | 0.653 | 0.947 | — |
| F1 | 0.782 | 0.649 | weighted **0.747** |
| Accuracy | | | **0.731** (train 0.801, balanced 0.800) |

Confusion matrix @tuned (rows = true, cols = pred): `[[WT→WT 1188, WT→HT 630], [HT→WT 34, HT→HT 613]]`.

**0.5 vs tuned (0.366), test set:**
| Metric | @0.5 | @tuned | Δ |
|---|---|---|---|
| Accuracy | 0.771 | 0.731 | −0.040 |
| Balanced accuracy | 0.798 | 0.800 | +0.002 |
| HT recall | 0.856 | 0.947 | +0.091 |
| HT precision | 0.540 | 0.493 | −0.047 |
| HT F1 | 0.662 | 0.649 | −0.014 |
| WT recall | 0.740 | 0.653 | −0.087 |
| WT precision | 0.935 | 0.972 | +0.037 |
| WT F1 | 0.827 | 0.782 | −0.045 |

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run (tuned) | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.731 | 0.733 | −0.002 |
| Weighted F1 | 0.747 | 0.749 | −0.002 |
| WT F1 | 0.782 | 0.785 | −0.003 |
| HT F1 | 0.649 | 0.649 | +0.000 |
| HT recall | 0.947 | 0.940 | +0.007 |
| HT precision | 0.493 | 0.496 | −0.003 |

*Base model is reported at the default 0.5 cut; this run's column uses the tuned 0.366 threshold.*

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- The Youden cut (0.366) lands almost exactly where the untuned base model already sits: HT recall 0.947
  (+0.007) and HT F1 0.649 (+0.000) are effectively tied with base, so tuning the threshold buys nothing
  versus the base operating point on this dependent split.
- The real trade is **0.5 → tuned within this model**: dropping the cut to 0.366 lifts HT recall
  0.856 → 0.947 (+0.091) but cuts HT precision 0.540 → 0.493 and overall accuracy 0.771 → 0.731.
  Balanced accuracy barely moves (0.798 → 0.800), confirming the curve is flat near the optimum.
- Class separation stays weak — **HT precision ≈ 0.49** at the tuned cut (about half of HT predictions are
  false positives; 630 WT recordings flagged HT). AUC 0.885 caps what any threshold can deliver.
- Train 0.801 vs test 0.731 is a modest gap; the dependent split leaks mice across sets, so even this
  number is optimistic relative to a leak-free estimate.

## Recommendations
- The default-0.5 base model already matches this tuned point — keep the threshold tuning only if you
  specifically want the +0.091 HT-recall lift, and accept the precision/accuracy cost.
- For an honest "new-mouse" estimate use an independent run, not this dependent one; for a controlled
  operating point see the `target_recall` candidate (0.547, HT recall ≥ 0.80) in `threshold_report.txt`.

## Artifacts
- `plots/roc_curve.png` — ROC with the tuned operating point. `plots/conf_matrix_thr0.5.png` /
  `plots/conf_matrix_thr_tuned.png` — confusion matrices at each cut.
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — overall + per-strain matrices.
- `plots/AUC_error.png` — learning curve. `plots/feature_importances_0.png`, `plots/feature_importance_1.png` — feature importance.
- `model/xgboost_tuned_dependent_model.pkl` — fitted model. `probabilities_val.csv` /
  `probabilities_test.csv` — per-recording probabilities used for threshold selection.
- Metrics source: `threshold_report.txt`, `threshold_metrics.json`, `logs/out.txt`. Parent summary: `../README.md`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` (default 0.5 cut) · metrics from `threshold_report.txt` + `threshold_metrics.json` · summary auto-generated*
