# xgboost_strain1_subject_eval_independent_baseline — XGBoost · subject-independent · strain1

**Status:** archived — superseded by `results/tabular_models/xgboost_subject_eval_dependent_baseline`.

> Untuned legacy XGBoost on the strain1 cohort, evaluated **leak-free** (split grouped by mouse).

## Overview
- **Model:** XGBoost (untuned legacy recipe; balanced sample weights, `scale_pos_weight=3.31`).
- **Cohort:** strain1 — years 2022–2024, mixed BALB/C + C57 background. Strain filter kept
  7,323/11,974 rows (`pup_strain == 1`), 59 mice.
- **Evaluation split:** subject-independent — group-aware split **by mouse** (`--independent`), so no
  mouse appears in two sets. This is the honest "generalize to unseen mice" setting (harder than the
  dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Train 4,068 rows / 35 mice, Val 1,433 rows / 12 mice, Test 1,822 rows / 12 mice
  (test WT 79.6% / HT 20.4%).
- **What was adapted vs the base model:** two levers change together — cohort is restricted to strain1
  **and** evaluation moves from subject-dependent to subject-independent.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.893 | 0.401 | — |
| Recall | 0.751 | 0.651 | — |
| F1 | 0.816 | 0.496 | weighted **0.751** |
| Accuracy | | | **0.731** (train 0.856) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 1089, WT→HT 361], [HT→WT 130, HT→HT 242]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.731 | 0.733 | −0.002 |
| Weighted F1 | 0.751 | 0.749 | +0.002 |
| WT F1 | 0.816 | 0.785 | +0.031 |
| HT F1 | 0.496 | 0.649 | −0.153 |
| HT recall | 0.651 | 0.940 | −0.289 |
| HT precision | 0.401 | 0.496 | −0.095 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- Headline numbers look flat — accuracy 0.731 (−0.002) and weighted F1 0.751 (+0.002) sit on top of the
  dependent base — but that parity is carried entirely by the WT majority; the leak-free split costs the
  minority class heavily.
- The minority class collapses: **HT recall falls to 0.651** (−0.289 vs base) and **HT precision to
  0.401** (−0.095), dragging HT F1 to 0.496 (−0.153). The model misses ~1 in 3 ASD-model pups and is
  wrong on ~6 of every 10 HT calls it makes.
- The strain1-only restriction (mixed BALB/C + C57 background, 59 mice) plus by-mouse grouping leaves a
  small, heterogeneous training set; the untuned recipe overfits, with train 0.856 vs test 0.731
  (0.125 gap).
- WT F1 actually improves (+0.031): the conservative shift on HT trades minority recall for cleaner
  majority calls (WT precision 0.893).

## Recommendations
- HT detection is too weak at the default 0.5 cut for any deployment use; prefer the tuned independent
  recipe (`xgboost_tuned_independent`, heavily regularized/shallow) over this untuned one for the
  leak-free setting.
- Use the current full-cohort `--baseline` runs under `results/tabular_models/` for honest
  new-mouse estimates; this strain1-only archived run narrows the data and is superseded.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices.
- `plots/AUC_error.png` — AUC / error learning curve. `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png` — feature importances.
- `model/xgboost_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, split info, class balance.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
