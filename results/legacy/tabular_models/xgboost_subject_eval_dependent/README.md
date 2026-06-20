# xgboost_subject_eval_dependent — XGBoost · subject-dependent

**Status:** archived — superseded by `results/tabular_models/xgboost_subject_eval_dependent_baseline`.

> Legacy untuned XGBoost on the old aggregated dataset, evaluated subject-dependent (rows split randomly, mice leak across sets).

## Overview
- **Model:** XGBoost, untuned legacy recipe (no flags / no hyperparameter search).
- **Evaluation split:** subject-dependent — random row-level split, so the **same mouse appears in
  train, val and test** (the log warns: 87 shared mice across every pair). This is the optimistic,
  leaky setting.
- **Dataset:** legacy `outputs/aggregated/all_data.csv` — 9,515 rows from 87 mice, **not** the official
  Issue-#46 baseline (~12,323 recordings) the current base model uses. Test = 1,903 rows
  (HET 30.9% / WT 69.1%); class balance is more imbalanced here than the baseline ~24% HET.
- **Label convention (legacy):** class 0 = HET/HT (minority), class 1 = WT — the reverse of the current
  runs. Numbers below are mapped back to WT / HT.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.974 | 0.480 | — |
| Recall | 0.531 | 0.968 | — |
| F1 | 0.687 | 0.641 | weighted **0.673** |
| Accuracy | | | **0.666** (train 0.706) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 698, WT→HT 617], [HT→WT 19, HT→HT 569]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.666 | 0.733 | −0.067 |
| Weighted F1 | 0.673 | 0.749 | −0.076 |
| WT F1 | 0.687 | 0.785 | −0.098 |
| HT F1 | 0.641 | 0.649 | −0.008 |
| HT recall | 0.968 | 0.940 | +0.028 |
| HT precision | 0.480 | 0.496 | −0.016 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- Even on the leaky subject-dependent split this legacy run trails the current base model everywhere but
  the minority class: test accuracy 0.666 (−0.067) and weighted F1 0.673 (−0.076). The gap is the **old
  dataset and label state**, not the split — both runs are dependent.
- The model collapses toward HET: **HT recall 0.968** but **WT recall only 0.531**, so it over-calls the
  ASD-model class and mislabels nearly half of true WT pups (617 of 1,315 WT → HT).
- **HT precision is 0.480** — about half of HET predictions are false positives; HT F1 0.641 is barely
  below the base (−0.008) only because recall is inflated by the over-calling.
- Train 0.706 vs test 0.666 is a small gap, but it is meaningless for generalization here: mouse overlap
  across train/test means the test set is not truly held out.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per strain).
- `plots/AUC_error.png` — training curve. `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png` — feature importance.
- `model/XGBmodel.pkl` — fitted XGBoost. `logs/out.txt` — flags, split info, class balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.

## Original notes
> **Data source:** `outputs/aggregated/all_data.csv` (9,515 rows, 87 mice)
> **Evaluation:** Subject-dependent — random row-level split (subject overlap between train/test)
> **Flags:** none (baseline)
>
> ```bash
> python3 src/classification/tabular/train_classifier.py
> ```
>
> Baseline model using pipeline-processed data with corrected genotype labels.
> Subject-dependent split allows overlap across sets, which inflates accuracy compared to subject-independent evaluation.

---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
