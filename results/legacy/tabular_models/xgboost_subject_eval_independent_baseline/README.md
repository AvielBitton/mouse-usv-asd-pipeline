# xgboost_subject_eval_independent_baseline — XGBoost (untuned legacy) · subject-independent

**Status:** archived — superseded by `results/tabular_models/xgboost_subject_eval_independent_baseline`.

> Untuned legacy XGBoost on the baseline data, evaluated **leak-free** (split grouped by mouse) — collapses toward HT.

## Overview
- **Model:** XGBoost, untuned legacy recipe (`sample_weight=balanced`, `scale_pos_weight=2.9344`).
  No hyperparameter search — the tuned variants live in separate folders.
- **Evaluation split:** subject-independent — group-aware train/val/test split **by `mouse_idx`**
  (`--independent`), so no mouse appears in two sets. This is the honest "generalize to unseen mice"
  setting (harder than the dependent base model, which splits rows randomly and lets mice leak across
  train/test).
- **Dataset:** official baseline (`all_data_external_baseline.csv`; Issue #46 filters; April-2026
  HET→WT correction). Train 6,893 rows / 63 mice, val 2,595 / 21 mice, test 2,486 / 22 mice.
  Test = WT 70.1% / HT 29.9%.
- **What was adapted vs the base model:** evaluation moves from subject-dependent to
  subject-independent; the model family (XGBoost) is unchanged from the base.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.977 | 0.417 | — |
| Recall | 0.417 | 0.977 | — |
| F1 | 0.584 | 0.584 | weighted **0.584** |
| Accuracy | | | **0.584** (train 0.790) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 726, WT→HT 1017], [HT→WT 17, HT→HT 726]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.584 | 0.733 | −0.149 |
| Weighted F1 | 0.584 | 0.749 | −0.165 |
| WT F1 | 0.584 | 0.785 | −0.201 |
| HT F1 | 0.584 | 0.649 | −0.065 |
| HT recall | 0.977 | 0.940 | +0.037 |
| HT precision | 0.417 | 0.496 | −0.079 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- **Degenerate collapse toward HT:** the model predicts HT for almost everyone — HT recall 0.977 but
  WT recall only 0.417 (it mislabels 1,017 of 1,743 WT recordings as HT). Accuracy 0.584 sits barely
  above the WT base rate the model abandons.
- Moving dependent → independent costs the full honest gap here: −0.149 accuracy and −0.165 weighted
  F1 vs the dependent base, far worse than the typical 10–15 pt drop, because the untuned recipe
  over-weights the minority class on unseen mice.
- **HT precision ≈ 0.42** — well under half of HT calls are correct; the high HT recall is bought by
  flooding the positive class, not by genuine separation (HT F1 only 0.584).
- Train 0.790 vs test 0.584 (0.21 gap) confirms the recipe does not generalize across mice.

## Recommendations
- Do not use this untuned-on-independent configuration; prefer `xgboost_tuned_independent_baseline`,
  whose heavily regularized/shallow hyperparameters were searched for exactly this split type.
- If this recipe must be kept, lower class weighting (the `--independent` collapse is driven by
  `scale_pos_weight`) and threshold-tune toward a controlled `target_recall` (~0.80).

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per strain).
- `plots/AUC_error.png` — training/validation AUC and error curves.
- `plots/feature_importances_0.png`, `plots/feature_importance_1.png` — feature importance.
- `model/xgboost_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, split info, class balance.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
