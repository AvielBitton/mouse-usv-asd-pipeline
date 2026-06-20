# tabpfn_strain1_subject_eval_dependent_baseline — TabPFN · subject-dependent · strain1

> TabPFN on the strain1 cohort (2022–2024, mixed BALB/c+C57), evaluated **subject-dependent** (rows split randomly, mice leak across train/test).

## Overview
- **Model:** TabPFN (prior-data-fitted transformer; no hyperparameter tuning; validation set is merged
  into train, so there is no early-stopping/learning curve and no feature importance).
- **Evaluation split:** subject-dependent — train/val/test split at the **row level** (random), so the
  same mouse appears in train, val and test (the run logs a 59-mouse overlap across all three). This is
  the optimistic/leaky setting, matching the dependent base model.
- **Cohort:** strain1 only — years 2022–2024, mixed BALB/c+C57 background. The strain filter keeps
  7,572/12,323 baseline recordings (`pup_strain == 1`) from 59 mice.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 1,515 recordings (WT 76.4% / HT 23.6%); train 4,542 + val 1,515 rows, with val merged into the
  6,057 fitting rows.
- **What was adapted vs the base model:** model family (TabPFN instead of XGBoost) **and** the data is
  restricted to the strain1 sub-cohort; the dependent split itself is unchanged.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.987 | 0.523 | — |
| Recall | 0.728 | 0.969 | — |
| F1 | 0.838 | 0.680 | weighted **0.801** |
| Accuracy | | | **0.785** (train 0.847) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 843, WT→HT 315], [HT→WT 11, HT→HT 346]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.785 | 0.733 | +0.052 |
| Weighted F1 | 0.801 | 0.749 | +0.052 |
| WT F1 | 0.838 | 0.785 | +0.053 |
| HT F1 | 0.680 | 0.649 | +0.031 |
| HT recall | 0.969 | 0.940 | +0.029 |
| HT precision | 0.523 | 0.496 | +0.027 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- On the cleaner strain1 cohort TabPFN beats the full-data XGBoost base on **every** headline metric —
  accuracy 0.785 (+0.052), weighted F1 0.801 (+0.052) — but the comparison is partly apples-to-oranges
  (a single, more homogeneous strain vs the all-strains base).
- The operating point is aggressive on the minority class: **HT recall 0.969** (catches all but 11 of
  357 ASD-model pups) at the cost of **HT precision 0.523** — roughly half of HT calls are false
  positives (315 WT→HT). HT F1 0.680.
- WT recall is the weak side (0.728): 315 of 1,158 controls are mislabelled HT, mirroring the high WT
  precision / low HT precision asymmetry seen across these tabular runs.
- Train 0.847 vs test 0.785 (≈0.06 gap) is small — but this is the leaky dependent split, so it
  flatters generalization; treat it as an upper bound, not a new-mouse estimate.

## Recommendations
- Read alongside an independent (by-mouse) strain1 run before trusting these numbers — dependent splits
  on a single cohort are especially optimistic given the 59-mouse train/test overlap.
- HT precision ≈ 0.52 at the default 0.5 cut means positive calls need confirmation; a threshold sweep
  would let you trade some of the near-perfect HT recall for fewer false positives.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices (single-strain run; no
  per-strain split).
- `model/tabpfn_model.pkl` — fitted TabPFN. `logs/out.txt` — flags, strain filter, split info, class
  balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
