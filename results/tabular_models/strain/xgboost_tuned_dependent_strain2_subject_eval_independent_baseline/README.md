# xgboost_tuned_dependent_strain2_subject_eval_independent_baseline — XGBoost (tuned-dependent) · subject-independent · strain2

> Dependent-tuned XGBoost run **leak-free** on the pure BALB/c strain2 cohort — collapses on the minority class.

## Overview
- **Model:** XGBoost with hyperparameters from the 200-trial search tuned for the **subject-dependent**
  split, but here applied to the **independent** split — a deliberate cross-check (the dependent recipe
  is less regularized than the independent one and is not matched to this harder setting).
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`,
  group-aware by `mouse_idx`), so no mouse appears in two sets. Honest "generalize to unseen mice"
  setting (harder than the dependent base model, which splits rows randomly and lets mice leak).
- **Cohort:** strain2 = 2015/2018 pure BALB/c classic published cohort (`--strain 2`); strain filter
  kept 4,751/12,323 baseline rows, 47 mice.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 1,176 recordings from 10 held-out mice (WT 73.2% / HT 26.8%).
- **What was adapted vs the base model:** three levers move together — split (dependent → independent),
  cohort (all-data → strain2 only), and a tuned-dependent hyperparameter set on the wrong split.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.716 | 0.140 | — |
| Recall | 0.871 | 0.057 | — |
| F1 | 0.786 | 0.081 | weighted **0.597** |
| Accuracy | | | **0.653** (train 0.950) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 750, WT→HT 111], [HT→WT 297, HT→HT 18]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.653 | 0.733 | −0.080 |
| Weighted F1 | 0.597 | 0.749 | −0.152 |
| WT F1 | 0.786 | 0.785 | +0.001 |
| HT F1 | 0.081 | 0.649 | −0.568 |
| HT recall | 0.057 | 0.940 | −0.883 |
| HT precision | 0.140 | 0.496 | −0.356 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- **Minority-class collapse toward WT:** HT recall is 0.057 and HT F1 0.081 — the model finds only
  18 of 315 ASD-model pups and misses the rest. Accuracy (0.653) is propped up almost entirely by the
  WT majority; this run is not usable for ASD detection.
- **Severe overfit:** train 0.950 vs test 0.653 (0.30 gap). The dependent-tuned recipe is too
  unregularized for the leak-free split — it memorizes train mice and fails to generalize to the 10
  unseen test mice, the opposite of what the independent-tuned recipe is built to avoid.
- **HT precision also poor:** 0.140 (−0.356 vs base) — of the few HT calls it does make, most are
  wrong, so the collapse is not even a useful "play-it-safe" tradeoff.
- **Combined headwinds:** the small pure-BALB/c strain2 cohort (only 27 train mice) plus a leak-free
  split plus a mismatched hyperparameter set together drive a −0.152 weighted-F1 drop versus base.

## Recommendations
- For the independent split, use the **independent-tuned** recipe (heavily regularized/shallow), not
  this dependent-tuned one; the train/test gap here is the symptom of the mismatch.
- Given the near-zero HT recall at the default 0.5 cut, threshold tuning alone will not recover this
  run — the score separation is too weak. Prefer the independent-tuned strain2 run for any
  new-mouse estimate on this cohort.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices.
- `plots/AUC_error.png` — AUC/error learning curve. `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png` — feature importance.
- `model/xgboost_tuned_dependent_model.pkl` — fitted model. `logs/out.txt` — flags, split info, class balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
