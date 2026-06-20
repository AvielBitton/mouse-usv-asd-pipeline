# tabpfn_subject_eval_dependent_external — TabPFN · subject-dependent · external dataset

**Status:** archived — superseded by `results/tabular_models/tabpfn_subject_eval_dependent_baseline`.

> TabPFN on the early externally-validated data, evaluated row-level (leaky) — the minority HT class collapsed.

## Overview
- **Model:** TabPFN (prior-data-fitted transformer; no hyperparameter tuning; validation set is merged
  into train, so there is no early-stopping/learning curve or feature importance).
- **Evaluation split:** subject-dependent — random **row-level** split (`--external`), with confirmed
  leakage: the log warns of 115 mice shared between train/test (and 115 train/val, 115 val/test). The
  same mouse appears across sets, so this is the optimistic setting.
- **Dataset:** early external set `outputs/aggregated_external/all_data_external.csv` — predates the
  official Issue #46 baseline (no HET→WT correction / current filters). Test = 2,617 recordings
  (HT 25.0% / WT 75.0%); train 7,848 rows, val 2,616 rows.
- **Label convention here is flipped:** in this run **class 0 = HT** (minority) and **class 1 = WT** —
  the opposite of the current pipeline. Metrics below are mapped back to WT/HT.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.773 | 0.594 | — |
| Recall | 0.966 | 0.150 | — |
| F1 | 0.859 | 0.239 | weighted **0.704** |
| Accuracy | | | **0.762** (train 0.778) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 1896, WT→HT 67], [HT→WT 556, HT→HT 98]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.762 | 0.733 | +0.029 |
| Weighted F1 | 0.704 | 0.749 | −0.045 |
| WT F1 | 0.859 | 0.785 | +0.074 |
| HT F1 | 0.239 | 0.649 | −0.410 |
| HT recall | 0.150 | 0.940 | −0.790 |
| HT precision | 0.594 | 0.496 | +0.098 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- **The minority HT class collapsed:** HT recall is just **0.150** (−0.790 vs base) — the model finds
  fewer than 1 in 6 ASD-model pups, calling WT for almost everyone (WT recall 0.966). HT F1 drops to
  0.239, the opposite failure mode from the high-recall base XGBoost.
- The headline accuracy of 0.762 is **misleading** — it is mostly the 75% WT majority being labelled WT.
  Weighted F1 (0.704) is below the base model (−0.045) and the macro F1 is only ~0.55, exposing the
  collapse the accuracy hides.
- HT precision (0.594) is the one bright spot — the few HT calls are cleaner than the base model
  (+0.098) — but recall is far too low to be useful for screening.
- Despite the row-level leakage that should help (shared mice across train/test), TabPFN still does not
  learn the minority class on this pre-baseline external data; train 0.778 vs test 0.762 shows little
  overfitting, just weak HT signal.

## Recommendations
- Do not use this run. It predates the Issue #46 baseline filters and HET→WT correction and the HT class
  has collapsed; use the superseding `results/tabular_models/tabpfn_subject_eval_dependent_baseline`.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per strain).
- `logs/out.txt` — flags, data source, split info, leakage warning, class balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
