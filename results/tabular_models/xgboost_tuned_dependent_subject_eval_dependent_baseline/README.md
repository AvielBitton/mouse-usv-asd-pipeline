# xgboost_tuned_dependent_subject_eval_dependent_baseline — XGBoost (tuned-dependent) · subject-dependent

> Tuned XGBoost on the official baseline data, evaluated **subject-dependent** (random row-level split, same split type the tuning targeted).

## Overview
- **Model:** XGBoost with hyperparameters from a 200-trial random search tuned for the
  subject-dependent split (`--model xgboost_tuned_dependent`), vs the untuned legacy recipe in the
  base model. `scale_pos_weight=3.123` keeps the minority HT class weighted.
- **Evaluation split:** subject-dependent — random row-level split (`random (row-level)`), so the
  same mouse appears across train/val/test (logged overlap: 106 train/val, 105 train/test, 105
  val/test shared mice). This is the optimistic, leaky setting — the same as the base model.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Train 7,393 / Val 2,465 / Test 2,465 rows. Test = WT 73.8% / HT 26.2%.
- **What was adapted vs the base model:** one lever — same dependent split, but the tree
  hyperparameters are the tuned-dependent set instead of the legacy untuned recipe.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.931 | 0.543 | — |
| Recall | 0.747 | 0.844 | — |
| F1 | 0.829 | 0.661 | weighted **0.785** |
| Accuracy | | | **0.772** (train 0.875) |

Test support: WT 1,818 / HT 647 (2,465 rows). The full overall confusion matrix is not printed in
`logs/out.txt`; the only matrix block is the "Old pup" subset `[[1358 460], [101 546]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.772 | 0.733 | +0.039 |
| Weighted F1 | 0.785 | 0.749 | +0.036 |
| WT F1 | 0.829 | 0.785 | +0.044 |
| HT F1 | 0.661 | 0.649 | +0.012 |
| HT recall | 0.844 | 0.940 | −0.096 |
| HT precision | 0.543 | 0.496 | +0.047 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- Tuning helps overall on its native split: accuracy 0.772 (+0.039) and weighted F1 0.785 (+0.036)
  both beat the untuned dependent base, driven mostly by WT (recall 0.747, F1 0.829 / +0.044).
- The minority-class operating point shifts: **HT recall drops to 0.844** (−0.096), but **HT
  precision rises to 0.543** (+0.047) — fewer false positives at the cost of missing more
  ASD-model pups. Net HT F1 is a small gain (0.661, +0.012).
- HT separation is still weak — precision ~0.54 means roughly half of HT calls are false positives.
- Train 0.875 vs test 0.772 (0.10 gap) is modest, but remember the dependent split lets the same
  mice leak across train/test, so this remains an optimistic estimate, not new-mouse performance.

## Recommendations
- For an honest "generalize to unseen mice" estimate, use the subject-independent runs, not this
  dependent split.
- HT recall fell at the default 0.5 cut — see the threshold runs (`../threshold/`,
  `../threshold_objectives/`) to set a deliberate operating point if recall matters more than
  precision.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per strain).
- `plots/AUC_error.png` — training/validation learning curve. `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png` — feature importances.
- `model/xgboost_tuned_dependent_model.pkl` — fitted model. `logs/out.txt` — flags, split info,
  class balance, classification report.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
