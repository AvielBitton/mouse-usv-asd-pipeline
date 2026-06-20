# xgboost_subject_eval_independent — XGBoost (untuned legacy) · subject-independent

**Status:** archived — superseded by `results/tabular_models/xgboost_subject_eval_dependent_baseline`.

> Legacy untuned XGBoost on the old pipeline data, evaluated **leak-free** (split grouped by mouse).

## Overview
- **Model:** XGBoost, untuned legacy recipe (no hyperparameter search).
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--group-split` /
  `--independent`), so no mouse appears in two sets. This is the honest "generalize to unseen mice"
  setting (harder than the dependent base model, which splits rows randomly and lets mice leak across
  train/test).
- **Dataset:** legacy `outputs/aggregated/all_data.csv` — predates the official baseline (this run does
  **not** apply the Issue #46 filters or the April-2026 HET→WT correction). Note the label encoding is
  inverted vs the current base model: here class 0 = HT (minority, 28.0% of test), class 1 = WT.
- **Split:** group-aware by `mouse_idx` — train 6,000 rows / 51 mice, val 2,049 / 18, test 1,466 / 18.
  Test balance WT 72.0% / HT 28.0%.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.820 | 0.370 | — |
| Recall | 0.539 | 0.696 | — |
| F1 | 0.651 | 0.484 | weighted **0.604** |
| Accuracy | | | **0.583** (train 0.824) |

Confusion matrix (rows = true, cols = pred): `[[HT→HT 286, HT→WT 125], [WT→HT 486, WT→WT 569]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.583 | 0.733 | −0.150 |
| Weighted F1 | 0.604 | 0.749 | −0.145 |
| WT F1 | 0.651 | 0.785 | −0.134 |
| HT F1 | 0.484 | 0.649 | −0.165 |
| HT recall | 0.696 | 0.940 | −0.244 |
| HT precision | 0.370 | 0.496 | −0.126 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- The leak-free split is brutal here: accuracy collapses to **0.583** (−0.150 vs the dependent base) and
  weighted F1 to **0.604** (−0.145) — the full ~15-pt dependent→independent drop lands on this untuned
  legacy model with no regularization to absorb it.
- The minority class is barely separable — **HT precision 0.370** (about 2 in 3 HT calls are false
  positives) and HT F1 0.484; HT recall 0.696 means it still misses ~30% of ASD-model pups.
- WT recall also caves to 0.539: the model over-predicts HT (486 true-WT pushed to HT in the confusion
  matrix), so neither class is reliably called.
- Train 0.824 vs test 0.583 (0.24 gap) shows heavy overfitting to the training mice — expected for an
  untuned tree model on a by-mouse split.

## Recommendations
- Do not use this run for reporting — it is on legacy unfiltered data with no tuning. Use the current
  baseline tabular runs under `results/tabular_models/` instead.
- For a leak-free XGBoost estimate, prefer the tuned independent recipe
  (`results/tabular_models/xgboost_tuned_independent_subject_eval_independent_baseline`, heavily
  regularized/shallow), which targets exactly this split.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per cohort).
- `plots/AUC_error.png` — training/AUC curve. `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png` — feature-importance plots.
- `model/XGBmodel.pkl` — fitted XGBoost. `logs/out.txt` — flags, split info, class balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.

## Original notes
*Preserved from the original hand-written README before auto-summarization.*

> # Results — Pipeline Data, Subject-Independent Evaluation
>
> **Data source:** `outputs/aggregated/all_data.csv` (9,515 rows, 87 mice)
> **Evaluation:** Subject-independent — group split by subject (no subject in more than one set)
> **Flags:** `--group-split` or `--independent`
>
> ```bash
> python3 src/classification/tabular/train_classifier.py --group-split
> ```
>
> Fair evaluation of the pipeline data — prevents data leakage by keeping
> all recordings from a given subject in the same split.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
