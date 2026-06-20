# xgboost_subject_eval_dependent_external — XGBoost · subject-dependent · external dataset

**Status:** archived — superseded by `results/tabular_models/xgboost_subject_eval_dependent_baseline`.

> Untuned legacy XGBoost on the early external segmentation export, evaluated subject-**dependent** (rows split randomly, mice leak across train/test).

## Overview
- **Model:** plain XGBoost (untuned legacy recipe; no hyperparameter search).
- **Evaluation split:** subject-dependent — random **row-level** split (`Strategy: random (row-level)`), so the same mouse appears in train, val and test (the log warns `mouse overlap -- train/test: 115 shared mice`). This is the optimistic/leaky setting, same family as the dependent base model.
- **Dataset:** legacy **external** export `outputs/aggregated_external/all_data_external.csv` (13,081 rows, 115 mice), pre-dating the official Issue-#46 baseline filters and the April-2026 HET→WT correction. Active flag: `--external`.
- **Label convention (note):** in this legacy run the encoding is **inverted** — class 0 = HET/HT (minority), class 1 = WT (majority) — opposite to the base model (WT=0, HT=1). Numbers below are remapped to WT/HT semantics for comparability.
- Train 7,848 / Val 2,616 / Test 2,617 rows; test class balance HT 25.0% / WT 75.0%.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.983 | 0.459 | — |
| Recall | 0.620 | 0.968 | — |
| F1 | 0.760 | 0.623 | weighted **0.726** |
| Accuracy | | | **0.707** (train 0.731) |

Confusion matrix (rows = true, cols = pred, class order 0=HT then 1=WT): `[[HT→HT 633, HT→WT 21], [WT→HT 746, WT→WT 1217]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.707 | 0.733 | −0.026 |
| Weighted F1 | 0.726 | 0.749 | −0.023 |
| WT F1 | 0.760 | 0.785 | −0.025 |
| HT F1 | 0.623 | 0.649 | −0.026 |
| HT recall | 0.968 | 0.940 | +0.028 |
| HT precision | 0.459 | 0.496 | −0.037 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- Even on the leaky dependent split, the legacy external run trails the dependent base model on every aggregate metric — accuracy 0.707 (−0.026), weighted F1 0.726 (−0.023) — confirming the unfiltered external export is weaker than the corrected baseline data.
- The model is biased hard toward the minority: **HT recall 0.968** (catches almost every ASD-model pup) but **HT precision 0.459** (more than half of HT calls are false positives), and it misclassifies 746 of 1,963 WT mice as HT.
- WT recall collapses to 0.620 as the flip side, so the apparent HT sensitivity comes at a heavy WT cost; HT F1 0.623 is below the base model's 0.649.
- Train (0.731) and test (0.707) are close, so there is little overfit here — the ceiling is the data/recipe, not variance; the small train-test gap is despite the leaky split.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`, `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per strain).
- `plots/AUC_error.png` — AUC/error training curve. `plots/feature_importance_1.png`, `plots/feature_importances_0.png` — feature importances.
- `model/XGBmodel.pkl` — fitted XGBoost. `logs/out.txt` — flags, split info, class balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.

## Original notes
**Data source:** `outputs/external/aggregated/all_data_external.csv` (13,081 rows, 115 mice)
**Evaluation:** Subject-dependent — random row-level split (subject overlap between train/test)
**Flags:** `--external`

```bash
python3 src/classification/tabular/train_classifier.py --external
```

Uses the external segmentation file which contains correct individual genotyping
and 28 additional mice (including 24 from 2024 that were missing from the pipeline due to absent Sex data).

---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
