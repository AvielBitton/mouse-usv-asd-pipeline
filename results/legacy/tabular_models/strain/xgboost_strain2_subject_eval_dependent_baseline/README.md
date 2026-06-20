# xgboost_strain2_subject_eval_dependent_baseline — XGBoost · subject-dependent · strain2

**Status:** archived — superseded by `results/tabular_models/xgboost_subject_eval_dependent_baseline`.

> Untuned legacy XGBoost on the pure BALB/c strain2 cohort only, evaluated subject-dependent (leaky row-level split).

## Overview
- **Model:** XGBoost (untuned legacy recipe; `sample_weight=balanced`, `scale_pos_weight=2.4108`).
- **Evaluation split:** subject-dependent — random row-level split (`Strategy: random`), so the same mouse
  appears in train, val and test (the log warns `mouse overlap -- train/test: 47 shared mice`). This is
  the optimistic, leaky setting, the same family as the base model.
- **Cohort:** strain2 only — pure BALB/c classic published cohort (years 2015/2018). The strain filter
  keeps 4,651/11,974 rows (`pup_strain == 2`) across 47 mice.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 931 recordings (WT 71.2% / HT 28.8%); train 2,790 / val 930.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.952 | 0.464 | — |
| Recall | 0.566 | 0.929 | — |
| F1 | 0.710 | 0.619 | weighted **0.683** |
| Accuracy | | | **0.670** (train 0.741) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 375, WT→HT 288], [HT→WT 19, HT→HT 249]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.670 | 0.733 | −0.063 |
| Weighted F1 | 0.683 | 0.749 | −0.066 |
| WT F1 | 0.710 | 0.785 | −0.075 |
| HT F1 | 0.619 | 0.649 | −0.030 |
| HT recall | 0.929 | 0.940 | −0.011 |
| HT precision | 0.464 | 0.496 | −0.032 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- Restricting to the strain2 cohort costs accuracy across the board even in this leaky split: test
  accuracy 0.670 (−0.063) and weighted F1 0.683 (−0.066) both trail the full-data dependent base model.
- The operating point is the familiar over-predict-HT pattern: **HT recall 0.929** but **HT precision
  0.464** — over half of HT calls are false positives, and WT recall collapses to 0.566 (375/663),
  with 288 WT recordings misclassified as HT.
- HT precision drops 0.032 vs base; with only ~4.7K rows from 47 mice, the smaller strain2 cohort gives
  XGBoost less signal than the full baseline, so class separation is weaker, not stronger.
- The train→test gap is modest (0.741 → 0.670), but that is on a leaky split — the dependent setting
  flatters generalization, so treat these numbers as an upper bound.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices.
- `plots/AUC_error.png` — training curve / AUC error. `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png` — feature importances.
- `model/xgboost_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, split info, class balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
