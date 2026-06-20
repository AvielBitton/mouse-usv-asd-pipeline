# xgboost_strain2_subject_eval_independent_external — XGBoost · subject-independent · strain2 (external)

**Status:** archived — superseded by the current `--baseline` runs under `results/`.

> Untuned XGBoost on the strain2 (2015/2018 BALB/c) external cohort, evaluated **leak-free** (split grouped by mouse).

## Overview
- **Model:** plain XGBoost (untuned legacy recipe; no hyperparameter search).
- **Evaluation split:** subject-independent — group-aware split **by mouse** (`--independent`), so no mouse
  appears in two sets. This is the honest "generalize to unseen mice" setting (harder than the dependent
  base model, which splits rows randomly and lets mice leak across train/test).
- **Cohort / dataset:** strain2 = 2015/2018 pure BALB/c classic published cohort, on the early external
  dataset (`outputs/external/aggregated/all_data_external_main.csv`, pre-Issue-#46 / pre-April-2026
  correction). Strain filter kept 5,009/13,625 rows (50 mice).
- **Label convention here is inverted vs the base model:** in this legacy run class 0 = HET (ASD model)
  and class 1 = WT. Test = 751 recordings from 10 held-out mice, but the split landed very imbalanced
  (HET only 13.6% / WT 86.4%), unlike the ~24–27% HET elsewhere.
- **What was adapted vs the base model:** three levers change together — cohort (strain2 external instead
  of full baseline), evaluation moves subject-dependent → subject-independent, and the train/test class
  balance is heavily skewed by the small 10-mouse test split.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.875 | 0.158 | — |
| Recall | 0.689 | 0.373 | — |
| F1 | 0.771 | 0.222 | weighted **0.696** |
| Accuracy | | | **0.646** (train 0.866) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 447, WT→HT 202], [HT→WT 64, HT→HT 38]]`
(from the logged class-0=HET / class-1=WT matrix `[[38 64],[202 447]]`).

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.646 | 0.733 | −0.087 |
| Weighted F1 | 0.696 | 0.749 | −0.053 |
| WT F1 | 0.771 | 0.785 | −0.014 |
| HT F1 | 0.222 | 0.649 | −0.427 |
| HT recall | 0.373 | 0.940 | −0.567 |
| HT precision | 0.158 | 0.496 | −0.338 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- The minority HET class essentially **collapses**: HT recall 0.373 and HT precision 0.158 (HT F1 0.222,
  −0.427 vs base). The model finds only 38 of 102 true HET pups and is wrong on 84% of its HET calls.
- The honest leak-free split on a tiny 10-mouse test set is brutal: overall accuracy 0.646 (−0.087) and
  weighted F1 0.696 (−0.053) sit well below the dependent base, and the 13.6% HET test balance means
  accuracy is propped up almost entirely by the WT majority.
- Train 0.866 vs test 0.646 (0.22 gap) is the cost of unseen mice plus a small, mismatched cohort — train
  is 28.9% HET while test is only 13.6% HET.
- This is an early external-dataset, strain2-only experiment predating the Issue-#46 filters and the
  April-2026 HET→WT correction; treat its numbers as historical, not as a current generalization estimate.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices.
- `plots/AUC_error.png` — AUC / error learning curve. `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png` — XGBoost feature importance.
- `model/xgboost_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, data source, split info, class balance.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
