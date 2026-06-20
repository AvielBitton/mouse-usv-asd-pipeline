# xgboost_tuned_dependent_strain2_subject_eval_dependent_baseline — XGBoost (tuned-dependent) · subject-dependent · strain2

> Tuned XGBoost on the pure-BALB/c strain2 cohort, evaluated subject-**dependent** (optimistic row-level split).

## Overview
- **Model:** XGBoost with the `xgboost_tuned_dependent` recipe — hyperparameters from the 200-trial
  random search tuned for the dependent split (matches this run's split, so no cross-check caveat).
  `scale_pos_weight=2.446` weights the HT minority.
- **Evaluation split:** subject-dependent — random row-level split (47 mice shared across
  train/val/test, logged as a mouse-overlap warning). This is the leaky, optimistic setting; expect
  10–15 pts above an honest by-mouse split.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction), restricted to
  **strain2** (2015/2018 pure-BALB/c classic published cohort) — kept 4,751/12,323 rows, 47 mice
  (WT 71.4% / HT 28.6%). Test = 951 recordings (WT 72.0% / HT 28.0%).
- **What was adapted vs the base model:** two levers change together — the tuned-dependent recipe
  (vs the untuned legacy base) **and** the cohort narrows to strain2 only.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.888 | 0.590 | — |
| Recall | 0.800 | 0.741 | — |
| F1 | 0.842 | 0.657 | weighted **0.790** |
| Accuracy | | | **0.783** (train 0.924) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 548, WT→HT 137], [HT→WT 69, HT→HT 197]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.783 | 0.733 | +0.050 |
| Weighted F1 | 0.790 | 0.749 | +0.041 |
| WT F1 | 0.842 | 0.785 | +0.057 |
| HT F1 | 0.657 | 0.649 | +0.008 |
| HT recall | 0.741 | 0.940 | −0.199 |
| HT precision | 0.590 | 0.496 | +0.094 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- On the clean strain2 cohort the tuned recipe **beats the base across headline metrics** — accuracy
  0.783 (+0.050), weighted F1 0.790 (+0.041), WT F1 0.842 (+0.057) — consistent with the
  homogeneous pure-BALB/c data being easier than the full mixed-background base.
- The operating point rebalances: **HT precision climbs to 0.590** (+0.094) while **HT recall drops to
  0.741** (−0.199). The base caught ~94% of ASD-model pups; this run misses ~1 in 4 (69 of 266 HT
  fall through to WT), trading sensitivity for fewer false positives.
- Net HT F1 barely moves (0.657, +0.008) — the precision gain and recall loss roughly cancel, so
  minority-class separation is about the same despite the friendlier cohort and tuning.
- Train 0.924 vs test 0.783 (0.14 gap) on a leaky dependent split: this is an optimistic number, not a
  generalization estimate. Use the independent strain2 / independent runs for honest "new-mouse" claims.

## Recommendations
- HT recall fell well below the base at the default 0.5 cut — if catching ASD-model pups is the
  priority, lower the threshold (see `../threshold/`, `../threshold_objectives/`) toward a
  `target_recall` operating point.
- Keep this run as a strain2-specific dependent reference only; do not compare it head-to-head with the
  mixed-cohort base as a generalization result.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices.
- `plots/AUC_error.png` — training/validation AUC + error learning curves.
- `plots/feature_importances_0.png`, `plots/feature_importance_1.png` — XGBoost feature importance.
- `model/xgboost_tuned_dependent_model.pkl` — fitted model. `logs/out.txt` — flags, split info, class balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
