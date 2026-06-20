# xgboost_strain2_subject_eval_independent_baseline — XGBoost · subject-independent · strain2

**Status:** archived — superseded by `results/tabular_models/xgboost_subject_eval_dependent_baseline`.

> Untuned legacy XGBoost on the pure-BALB/c strain2 cohort, evaluated **leak-free** (split grouped by mouse).

## Overview
- **Model:** XGBoost, untuned legacy recipe (no hyperparameter search; `sample_weight=balanced`,
  `scale_pos_weight=2.069` = n_WT/n_HT with HT as positive).
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`,
  group-aware by `mouse_idx`), so no mouse appears in two sets. This is the honest "generalize to
  unseen mice" setting (harder than the dependent base model, which splits rows randomly and lets
  mice leak across train/test).
- **Cohort:** strain2 = years 2015/2018, the pure BALB/c classic published cohort. Strain filter kept
  4,651/11,974 rows (`pup_strain == 2`), 47 mice.
- **Dataset:** official baseline (`all_data_external_baseline.csv`; Issue #46 filters; April-2026
  HET→WT correction). Test = 1,119 recordings from 10 held-out mice (WT 76.9% / HT 23.1%);
  train 2,452 rows / 27 mice, val 1,080 rows / 10 mice.
- **What was adapted vs the base model:** two levers change together — cohort is restricted to strain2
  **and** evaluation moves from subject-dependent to subject-independent.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.855 | 0.401 | — |
| Recall | 0.740 | 0.581 | — |
| F1 | 0.793 | 0.475 | weighted **0.720** |
| Accuracy | | | **0.703** (train 0.842) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 637, WT→HT 224], [HT→WT 108, HT→HT 150]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.703 | 0.733 | −0.030 |
| Weighted F1 | 0.720 | 0.749 | −0.029 |
| WT F1 | 0.793 | 0.785 | +0.008 |
| HT F1 | 0.475 | 0.649 | −0.174 |
| HT recall | 0.581 | 0.940 | −0.359 |
| HT precision | 0.401 | 0.496 | −0.095 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- Overall accuracy (0.703) and weighted F1 (0.720) land ~0.030 below the dependent base model — a
  modest top-line drop, but the per-class picture is much worse than the headline suggests.
- The minority class collapses on unseen mice: **HT recall 0.581** (−0.359 vs base) and **HT precision
  0.401** (−0.095), so HT F1 falls to 0.475 (−0.174). The model misses ~42% of ASD-model pups and is
  wrong on ~60% of the HT calls it does make.
- WT carries the accuracy: WT F1 0.793 (+0.008 vs base) holds up, so the strain2 + leak-free regime
  trades almost all of its loss out of the positive class.
- Train 0.842 vs test 0.703 (0.14 gap) reflects the cost of unseen mice on the smaller pure-BALB/c
  cohort (only 27 train mice), with no tuning to regularize the split.

## Recommendations
- Use the current full-baseline runs under `results/tabular_models/`, not this strain2-only legacy run,
  for any reported performance — this folder is archived.
- If a strain2 estimate is still needed, HT recall (0.581) is too low at the default 0.5 cut for a
  screening use case; a tuned/regularized independent recipe and threshold tuning would be required
  before trusting positive calls.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices.
- `plots/AUC_error.png` — AUC / error learning curve.
- `plots/feature_importances_0.png`, `plots/feature_importance_1.png` — feature importance.
- `model/xgboost_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, split info, class balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
