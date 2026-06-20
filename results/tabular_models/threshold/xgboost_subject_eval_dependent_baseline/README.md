# xgboost_subject_eval_dependent_baseline — XGBoost · subject-dependent · threshold (Youden)

> The base XGBoost model with a tuned decision threshold (Youden J) replacing the default 0.5 cut — **no retraining**.

## Overview
- **Model:** XGBoost (untuned legacy recipe), the same fitted model as the base run — this folder only
  swaps the decision threshold.
- **What was adapted vs the base model:** decision-threshold tuning only. The 0.5 cut is replaced by a
  threshold chosen from **leak-free validation probabilities** via Youden's J; the model weights are
  unchanged (`model/xgboost_model.pkl`).
- **Evaluation split:** subject-dependent — random row-level split (`logs/out.txt` warns of mouse overlap:
  106 train/val, 105 train/test shared mice). Optimistic/leaky vs the honest independent setting.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 2,465 recordings (WT 73.8% / HT 26.2%).
- **Tuned threshold:** 0.5281 (Youden). Candidates were youden 0.5281, f1 0.6174, target_recall 0.6297,
  balanced 0.5280. Val AUC 0.891, test AUC 0.876 (threshold-independent).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.957 | 0.499 | — |
| Recall | 0.673 | 0.915 | — |
| F1 | 0.790 | 0.646 | weighted **0.753** |
| Accuracy | | | **0.737** (train 0.782) |

Balanced accuracy 0.794 · test AUC 0.876.
Confusion matrix @tuned (rows = true, cols = pred): `[[WT→WT 1224, WT→HT 594], [HT→WT 55, HT→HT 592]]`.

**@0.5 (default) vs @tuned (0.5281):**
| Metric | @0.5 | @tuned | Δ |
|---|---|---|---|
| Accuracy | 0.727 | 0.737 | +0.009 |
| Balanced accuracy | 0.795 | 0.794 | −0.001 |
| HT recall | 0.937 | 0.915 | −0.022 |
| HT precision | 0.490 | 0.499 | +0.009 |
| HT F1 | 0.643 | 0.646 | +0.003 |
| WT recall | 0.653 | 0.673 | +0.020 |
| WT precision | 0.967 | 0.957 | −0.010 |
| WT F1 | 0.779 | 0.790 | +0.011 |

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.737 | 0.733 | +0.004 |
| Weighted F1 | 0.753 | 0.749 | +0.004 |
| WT F1 | 0.790 | 0.785 | +0.005 |
| HT F1 | 0.646 | 0.649 | −0.003 |
| HT recall | 0.915 | 0.940 | −0.025 |
| HT precision | 0.499 | 0.496 | +0.003 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

The base model is reported at the default 0.5 cut; this run's Δ uses the **tuned (0.5281)** operating point.

## Key insights
- The Youden threshold sits just above 0.5 (0.5281), so it barely moves the operating point: the tuned
  cut buys +0.009 accuracy and +0.011 WT F1 over @0.5 while trading 0.022 of HT recall — a small,
  near-neutral shift, as expected when validation AUC is high (0.891) and the data is class-imbalanced.
- Balanced accuracy is essentially flat (0.795 → 0.794): for this already-recall-heavy model, Youden has
  little left to optimize. The win is almost entirely on the majority class (WT recall 0.653 → 0.673).
- Versus the base 0.5-cut model the gains are marginal (+0.004 accuracy, +0.004 weighted F1) and HT
  recall actually drops 0.025 — the threshold cannot fix the core weakness: **HT precision stays ≈ 0.50**,
  so half of all HT calls remain false positives.

## Recommendations
- Youden gives almost nothing here. If the goal is fewer false alarms, the `f1`/`balanced` thresholds
  (~0.62) are higher — see the cross-objective runs in `../../threshold_objectives/` for the full sweep.
- This is a dependent (leaky) run; do not quote it as generalization. Use the independent threshold run
  for any new-mouse estimate.

## Artifacts
- `plots/roc_curve.png` — ROC with the tuned operating point. `plots/conf_matrix_thr0.5.png` and
  `plots/conf_matrix_thr_tuned.png` — confusion matrices at each cut.
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per strain).
  `plots/AUC_error.png`, `plots/feature_importance_1.png`, `plots/feature_importances_0.png`.
- `model/xgboost_model.pkl` — the (unchanged) fitted model. `probabilities_val.csv`,
  `probabilities_test.csv` — per-recording probabilities the threshold was derived/applied on.
- Metrics source: `threshold_metrics.json`, `threshold_report.txt`, `comparison_vs_baseline.txt`
  (run column only), `logs/out.txt`. Parent summary: `../README.md`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `threshold_metrics.json` + `threshold_report.txt` + `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
