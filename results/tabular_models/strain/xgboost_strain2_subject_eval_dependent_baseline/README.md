# xgboost_strain2_subject_eval_dependent_baseline — XGBoost · subject-dependent · strain2

> Untuned XGBoost on the strain2 (pure BALB/c, 2015/2018) baseline cohort, evaluated row-level (leaky/optimistic).

## Overview
- **Model:** XGBoost (untuned legacy recipe; `scale_pos_weight=2.4462` for the HT minority).
- **Evaluation split:** subject-dependent — random row-level split (the log warns `mouse overlap`: all
  47 mice appear in train, val **and** test). Same mouse leaks across sets, so figures are optimistic
  and match the base model's evaluation regime.
- **Cohort:** strain2 only — the pure BALB/c classic published cohort (years 2015/2018). The strain
  filter keeps 4,751/12,323 baseline rows (`pup_strain == 2`), 47 mice.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 951 recordings (WT 72.0% / HT 28.0%); train 2,850 / val 950.
- **What was adapted vs the base model:** one lever — the data is restricted to the strain2 cohort.
  Same model family and same subject-dependent split as the base.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.907 | 0.532 | — |
| Recall | 0.724 | 0.808 | — |
| F1 | 0.805 | 0.642 | weighted **0.759** |
| Accuracy | | | **0.748** (train 0.845) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 496, WT→HT 189], [HT→WT 51, HT→HT 215]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.748 | 0.733 | +0.015 |
| Weighted F1 | 0.759 | 0.749 | +0.010 |
| WT F1 | 0.805 | 0.785 | +0.020 |
| HT F1 | 0.642 | 0.649 | −0.007 |
| HT recall | 0.808 | 0.940 | −0.132 |
| HT precision | 0.532 | 0.496 | +0.036 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- Restricting to the cleaner pure-BALB/c strain2 cohort nudges overall accuracy (0.748, +0.015) and
  weighted F1 (0.759, +0.010) slightly above the full-data base, with the train→test gap tightening to
  ~0.10 (0.845 vs 0.748).
- The operating point shifts off the base's extreme HT-leaning call: **HT recall drops to 0.808**
  (−0.132 vs base) but **HT precision climbs to 0.532** (+0.036) — fewer WT pups misfired as HT (189
  false positives), at the cost of missing ~1 in 5 ASD-model pups.
- Net HT F1 is essentially flat (0.642, −0.007): the recall lost and precision gained roughly cancel,
  so strain2's gains are concentrated on the WT class (WT F1 +0.020).
- Class separation remains weak — **HT precision ≈ 0.53**, so nearly half of HT predictions are still
  false positives even on the homogeneous cohort, and the dependent split keeps these numbers optimistic.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices.
- `plots/AUC_error.png` — AUC/error learning curve. `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png` — feature importances.
- `model/xgboost_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, strain filter, split info,
  class balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
