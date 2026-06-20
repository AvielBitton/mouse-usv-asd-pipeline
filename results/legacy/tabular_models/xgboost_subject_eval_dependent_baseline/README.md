# xgboost_subject_eval_dependent_baseline — XGBoost · subject-dependent

**Status:** archived — superseded by `results/tabular_models/xgboost_subject_eval_dependent_baseline`.

> Untuned legacy XGBoost on the baseline data, evaluated subject-**dependent** (rows split randomly, mice leak across sets).

## Overview
- **Model:** XGBoost, untuned legacy recipe (no hyperparameter search; `sample_weight=balanced`,
  `scale_pos_weight=3.1145` for the ~24% HT minority).
- **Evaluation split:** subject-dependent — random row-level split, so the same mouse appears in
  train/val/test (the log warns of 106 shared mice across each pair). This is the optimistic,
  leakage-prone setting, not honest "unseen mouse" generalization.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction), from the external
  aggregated CSV. Train 7,184 / Val 2,395 / Test 2,395 rows; test WT 73.3% / HT 26.7%.
- **What was adapted vs the base model:** this is the legacy precursor of the current base run — same
  model family and same dependent split, but an earlier external CSV and code path.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.994 | 0.481 | — |
| Recall | 0.612 | 0.989 | — |
| F1 | 0.758 | 0.648 | weighted **0.728** |
| Accuracy | | | **0.713** (train 0.709) |

Confusion matrix from the log (rows = true, cols = pred): `[[WT→WT 1075, WT→HT 681], [HT→WT 7, HT→HT 632]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.713 | 0.733 | −0.020 |
| Weighted F1 | 0.728 | 0.749 | −0.021 |
| WT F1 | 0.758 | 0.785 | −0.027 |
| HT F1 | 0.648 | 0.649 | −0.001 |
| HT recall | 0.989 | 0.940 | +0.049 |
| HT precision | 0.481 | 0.496 | −0.015 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- The model runs **HT-recall-hungry**: HT recall 0.989 (only 7 of 639 HT pups missed) but HT precision
  0.481, so roughly half of HT calls are false positives. WT recall collapses to 0.612 as the cost.
- Net effect vs the current base is a near-wash on minority-class quality (**HT F1 −0.001**) but a small
  loss on overall accuracy (−0.020) and weighted F1 (−0.021), driven by the weaker WT recall.
- Train 0.709 ≈ test 0.713 — no train/test gap, expected here because the random split leaks mice across
  sets, so "test" is not held out at the mouse level. Treat these numbers as optimistic.
- This legacy run lands close to the current base on aggregate metrics but at a more extreme operating
  point; the current base trades a little HT recall (0.940) for much better WT recall (0.660).

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per strain).
- `plots/AUC_error.png` — training/AUC curve; `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png` — feature importances.
- `model/xgboost_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, split info, class balance, matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
