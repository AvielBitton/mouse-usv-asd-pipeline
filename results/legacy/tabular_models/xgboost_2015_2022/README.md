# xgboost_2015_2022 — XGBoost · subject-dependent · strain2 (2015/2018)

**Status:** archived — superseded by `results/tabular_models/strain/xgboost_strain2_subject_eval_dependent_baseline`.

> Early XGBoost run on the 2015/2018-only cohort (pure BALB/c), before the strain2 baseline pipeline.

## Overview
- **Model:** XGBoost, untuned legacy recipe — no 200-trial search, the old default hyperparameters.
- **Cohort:** strain2 predecessor — only the 2015/2018 years (pure BALB/c classic published cohort),
  not the mixed strain1 background. This run predates the Issue #46 baseline filters and the
  April-2026 HET→WT correction, so its data slice differs from the current strain2 baseline.
- **Evaluation split:** subject-dependent — rows split randomly, so a mouse can appear in both train
  and test (leakage; optimistic vs a leak-free split). Same setting as the base model.
- **Label encoding (legacy quirk):** this run encodes class `1.0` = WT (majority, support 992) and
  class `0.0` = HT (minority, support 473); the minority fraction here is ~32%, higher than the
  ~24% baseline. Metrics below are restated in WT/HT terms.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.94 | 0.58 | — |
| Recall | 0.69 | 0.92 | — |
| F1 | 0.80 | 0.71 | weighted **0.77** |
| Accuracy | | | **0.760** (train 0.798) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 681, WT→HT 311], [HT→WT 40, HT→HT 433]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.760 | 0.733 | +0.027 |
| Weighted F1 | 0.770 | 0.749 | +0.021 |
| WT F1 | 0.800 | 0.785 | +0.015 |
| HT F1 | 0.710 | 0.649 | +0.061 |
| HT recall | 0.920 | 0.940 | −0.020 |
| HT precision | 0.580 | 0.496 | +0.084 |

## Key insights
- Numbers beat the base model across the board (accuracy +0.027, weighted F1 +0.021, HT F1 +0.061),
  but the comparison is not apples-to-apples: this is a narrower, easier slice — only the 2015/2018
  pure-BALB/c cohort, with a ~32% HT minority and pre-baseline filtering.
- The minority class is the strong point here: **HT precision 0.58 (+0.084 vs base)** with HT recall
  still high at 0.92, so HT F1 0.71 — the cleaner single-strain data separates WT vs HT better than
  the mixed-background baseline.
- The subject-dependent split means mice leak across train/test, so the train→test gap is small
  (0.798 → 0.760) and these figures are optimistic; a leak-free split would land lower.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices.
- `plots/confusionmatrix_strain1.png`, `plots/confusionmatrix_strain2.png` — per-subgroup ("new pup" /
  "old pup") confusion matrices. `plots/AUC_error.png` — AUC/error training curve.
- `plots/feature_importances_0.png`, `plots/feature_importance_1.png` — XGBoost feature importances.
- `model/XGBmodel.pkl` — fitted XGBoost model. `logs/out.txt` — accuracies, classification report,
  confusion matrix, feature-importance vector.
- Metrics source: `logs/out.txt` (classification report; no `comparison_vs_baseline.txt` in this folder).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `logs/out.txt` · summary auto-generated*
