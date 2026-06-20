# xgboost_strain2_subject_eval_independent_baseline — XGBoost · subject-independent · strain2

> Untuned XGBoost on the strain2 (pure BALB/c, 2015/2018) cohort, evaluated **leak-free** (split grouped by mouse).

## Overview
- **Model:** XGBoost — untuned legacy recipe (no hyperparameter search), `scale_pos_weight=2.47` for the
  minority HT class.
- **Cohort:** strain2 — pure BALB/c classic published cohort (years 2015/2018). Strain filter keeps
  4,751/12,323 baseline recordings (`pup_strain == 2`), 47 mice.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`), so no
  mouse appears in two sets. This is the honest "generalize to unseen mice" setting (harder than the
  dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Train 2,844 rows / 27 mice, Val 731 / 10 mice, Test 1,176 recordings from 10 held-out mice
  (WT 73.2% / HT 26.8%).
- **What was adapted vs the base model:** three levers change together — cohort narrows to strain2 only,
  evaluation moves from subject-dependent to subject-independent, and the same untuned recipe is applied
  to a much smaller pool of mice.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.722 | 0.194 | — |
| Recall | 0.865 | 0.089 | — |
| F1 | 0.787 | 0.122 | weighted **0.609** |
| Accuracy | | | **0.657** (train 0.916) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 745, WT→HT 116], [HT→WT 287, HT→HT 28]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.657 | 0.733 | −0.076 |
| Weighted F1 | 0.609 | 0.749 | −0.140 |
| WT F1 | 0.787 | 0.785 | +0.002 |
| HT F1 | 0.122 | 0.649 | −0.527 |
| HT recall | 0.089 | 0.940 | −0.851 |
| HT precision | 0.194 | 0.496 | −0.302 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- The minority class **collapses**: HT recall crashes to 0.089 (−0.851 vs base) — only 28 of 315 true HT
  recordings are caught, while 287 are called WT. The classifier defaults to WT for almost everyone on the
  strain2 independent split.
- HT precision is also poor at 0.194 (−0.302), so even the few positive calls are mostly wrong; HT F1 of
  0.122 is effectively a non-working detector for ASD-model pups.
- Train 0.916 vs test 0.657 (0.26 gap) signals heavy overfitting: the untuned recipe memorizes the 27
  train mice but does not generalize to the 10 unseen mice in the small pure-BALB/c cohort.
- Headline accuracy (0.657) is misleading — it rides almost entirely on WT recall (0.865) and the 73%
  WT base rate; weighted F1 (0.609) exposes the real weakness once the minority class is counted.

## Recommendations
- This untuned recipe does not transfer to unseen strain2 mice — use a tuned-independent recipe (heavily
  regularized/shallow) and/or compare against the full-cohort independent runs before trusting any
  new-mouse estimate on strain2.
- At the default 0.5 cut HT is near-undetected; tuning the decision threshold (see `../../threshold/`,
  `../../threshold_objectives/`) cannot rescue this without first fixing the collapse, given HT precision
  ≈ 0.19.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices.
- `plots/AUC_error.png` — AUC/error training curve. `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png` — feature importance.
- `model/xgboost_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, split info, class balance.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
