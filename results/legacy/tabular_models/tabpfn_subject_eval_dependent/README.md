# tabpfn_subject_eval_dependent — TabPFN · subject-dependent

**Status:** archived — superseded by `results/tabular_models/tabpfn_subject_eval_independent_baseline` (the current baseline TabPFN run).

> Legacy TabPFN on the pre-baseline `all_data.csv`, evaluated with a leaky row-level split.

## Overview
- **Model:** TabPFN (prior-data-fitted transformer; no hyperparameter tuning; validation set is merged
  into train, so there is no early-stopping/learning curve and no feature-importance output).
- **Evaluation split:** subject-dependent — `random` row-level split (train 5,709 / val 1,903 /
  test 1,903 rows). The log explicitly warns of mouse overlap (87 shared mice across train/val,
  train/test and val/test), so the same mouse appears in train and test — leaky and optimistic.
- **Dataset:** legacy `outputs/aggregated/all_data.csv` — pre-baseline, before the Issue #46 filters
  and the April-2026 HET→WT correction. Class indices are also the legacy mapping (class 0 = HT/HET,
  class 1 = WT); test class balance is HT 30.9% / WT 69.1%, the inverse of the baseline runs.
- **What was adapted vs the base model:** model family (TabPFN instead of XGBoost) on the old data and
  the leaky dependent split.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.743 | 0.678 | — |
| Recall | 0.942 | 0.272 | — |
| F1 | 0.831 | 0.388 | weighted **0.694** |
| Accuracy | | | **0.735** (train 0.762) |

Confusion matrix (rows = true, cols = pred): `[[HT→HT 160, HT→WT 428], [WT→HT 76, WT→WT 1239]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.735 | 0.733 | +0.002 |
| Weighted F1 | 0.694 | 0.749 | −0.055 |
| WT F1 | 0.831 | 0.785 | +0.046 |
| HT F1 | 0.388 | 0.649 | −0.261 |
| HT recall | 0.272 | 0.940 | −0.668 |
| HT precision | 0.678 | 0.496 | +0.182 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- The model collapses toward the **majority class**: WT recall is 0.942 but **HT recall is only 0.272**
  (−0.668 vs base) — it misses ~3 of every 4 ASD-model pups. The confusion matrix confirms it
  (HT→WT 428 vs HT→HT 160).
- Headline accuracy (0.735) matches the base model almost exactly, but that is an artifact of the
  WT-heavy 69%/31% balance plus the leaky split — **weighted F1 drops to 0.694** (−0.055) once the
  minority class is weighted in.
- The operating point is the mirror image of the base model: HT precision rises to 0.678 (+0.182) only
  because the model rarely predicts HT, trading nearly all HT recall away. HT F1 0.388 is the worst of
  any tabular dependent run.
- This run is doubly outdated — pre-baseline data (no Issue #46 filters, no HET→WT correction) and a
  split with explicit train/test mouse leakage — so its numbers are not comparable to current runs.

## Recommendations
- Do not use for any performance estimate; refer to the current baseline TabPFN run
  (`results/tabular_models/tabpfn_subject_eval_independent_baseline`) instead.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per strain).
- `logs/out.txt` — flags, split info, mouse-overlap warning, class balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
