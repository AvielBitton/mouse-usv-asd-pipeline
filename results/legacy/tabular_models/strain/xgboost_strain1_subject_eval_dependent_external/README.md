# xgboost_strain1_subject_eval_dependent_external — XGBoost · subject-dependent · strain1 (external)

**Status:** archived — superseded by the current `--baseline` runs under `results/`.

> Untuned legacy XGBoost on the external strain1 cohort, evaluated subject-**dependent** (rows split randomly, mice leak across train/test).

## Overview
- **Model:** XGBoost, untuned legacy recipe (no hyperparameter search).
- **Cohort:** strain1 (years 2022–2024, mixed BALB/C + C57 background), pulled from the externally-validated dataset (`--external --strain 1`); the strain filter keeps 8,616 / 13,625 rows and 70 mice.
- **Evaluation split:** subject-dependent — random **row-level** split (train 5,169 / val 1,723 / test 1,724). The log flags `mouse overlap -- train/test: 70 shared mice`, so the same mouse appears in train and test: this is the optimistic, leak-prone setting (like the base model).
- **Class balance:** this run inverts the label convention — class 0 = HET/HT (ASD-model, minority 23.0% of test), class 1 = WT (control, majority 77.0%). Read the per-class numbers below by genotype, not by index.
- **What differs vs the base model:** same untuned recipe and dependent split, but a different data source (external) and only the strain1 sub-cohort instead of the full baseline data.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.985 | 0.473 | — |
| Recall | 0.680 | 0.965 | — |
| F1 | 0.804 | 0.635 | weighted **0.766** |
| Accuracy | | | **0.745** (train 0.772) |

Confusion matrix (rows = true, cols = pred; class 0 = HT, class 1 = WT): `[[HT→HT 382, HT→WT 14], [WT→HT 425, WT→WT 903]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.745 | 0.733 | +0.012 |
| Weighted F1 | 0.766 | 0.749 | +0.017 |
| WT F1 | 0.804 | 0.785 | +0.019 |
| HT F1 | 0.635 | 0.649 | −0.014 |
| HT recall | 0.965 | 0.940 | +0.025 |
| HT precision | 0.473 | 0.496 | −0.023 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- On the dependent split the strain1 external cohort edges the base model on headline metrics — accuracy 0.745 (+0.012) and weighted F1 0.766 (+0.017) — but this is the leaky setting, so treat the gain as optimistic, not honest generalization.
- The operating point is heavily skewed toward calling HT: **HT recall 0.965** (catches almost every ASD-model pup) but **HT precision 0.473** (more than half of HT calls are false positives). The confusion matrix confirms it — 425 of 1,328 true WT are mislabeled HT.
- WT precision is near-perfect (0.985) while WT recall sags to 0.680: when the model says WT it is almost always right, but it under-calls the majority class to chase HT recall.
- Train 0.772 vs test 0.745 is a tight 0.027 gap — little overfitting — but with mice leaking across the split that closeness overstates real-world performance.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices. `plots/AUC_error.png` — train/val AUC learning curve. `plots/feature_importances_0.png`, `plots/feature_importance_1.png` — feature importance.
- `model/xgboost_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, data source, split info, class balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
