# xgboost_strain1_subject_eval_dependent_baseline — XGBoost · subject-dependent · strain1

**Status:** archived — superseded by `results/tabular_models/xgboost_subject_eval_dependent_baseline`.

> Untuned legacy XGBoost on the strain1 cohort only, evaluated subject-dependent (rows leak across train/test).

## Overview
- **Model:** XGBoost, untuned legacy recipe (no hyperparameter search). Class imbalance handled with
  `sample_weight=balanced` and `scale_pos_weight=3.5195` (n_WT/n_HT, HT positive).
- **Evaluation split:** subject-dependent — random **row-level** split, so the same mouse appears in
  train, val and test (the log warns 59 shared mice across all three sets). This leaks and is optimistic.
- **Cohort:** strain1 only (years 2022–2024, mixed BALB/C+C57 background). The strain filter kept
  7,323/11,974 rows (`pup_strain == 1`), 59 mice; `pup_gen` balance 5,683 WT / 1,640 HT.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction), strain1 subset.
  Train 4,393 / Val 1,465 / Test 1,465 rows; test WT 77.1% / HT 22.9%.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.996 | 0.483 | — |
| Recall | 0.685 | 0.991 | — |
| F1 | 0.812 | 0.650 | weighted **0.774** |
| Accuracy | | | **0.755** (train 0.759) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 773, WT→HT 356], [HT→WT 3, HT→HT 333]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.755 | 0.733 | +0.022 |
| Weighted F1 | 0.774 | 0.749 | +0.025 |
| WT F1 | 0.812 | 0.785 | +0.027 |
| HT F1 | 0.650 | 0.649 | +0.001 |
| HT recall | 0.991 | 0.940 | +0.051 |
| HT precision | 0.483 | 0.496 | −0.013 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- Restricting to the strain1 cohort nudges every headline number up a touch (accuracy +0.022, weighted
  F1 +0.025) vs the all-cohort dependent base — but this is still a **leaky** split (59 mice shared
  across train/val/test), so the numbers are optimistic, not a generalization estimate.
- The model is near-degenerate toward the minority class: **HT recall 0.991** (it misses only 3 of 336
  HT pups) but at the cost of flooding WT with false positives — 356 of 1,129 true WT are called HT.
- Class separation stays poor — **HT precision 0.483** (about half of HT predictions are wrong), so
  HT F1 (0.650) is essentially tied with the base (+0.001) despite the higher recall.
- Train 0.759 vs test 0.755 sit almost on top of each other; with row-level leakage a tight train/test
  gap is expected and does not indicate good generalization.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices.
- `plots/AUC_error.png` — training/eval curve. `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png` — feature importance.
- `model/xgboost_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, split info, class balance.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
