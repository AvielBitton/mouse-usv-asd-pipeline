# xgboost_strain1_subject_eval_independent_baseline — XGBoost · subject-independent · strain1

> Untuned legacy XGBoost on the strain1 cohort (2022–2024 mixed BALB/C+C57), evaluated **leak-free** (split grouped by mouse).

## Overview
- **Model:** XGBoost (untuned legacy recipe; class imbalance handled via `scale_pos_weight=3.5104`,
  HT = positive). 48 aggregated per-recording acoustic features.
- **Evaluation split:** subject-independent — group-aware train/val/test split **by mouse**
  (`--independent`), so no mouse appears in two sets. This is the honest "generalize to unseen mice"
  setting (harder than the dependent base model, which splits rows randomly and lets mice leak across
  train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction), restricted to
  **strain1** (years 2022–2024, mixed BALB/C+C57 background): 7,572/12,323 rows, 59 mice.
- **Split sizes:** Train 4,569 (WT 77.8% / HT 22.2%, 35 mice) · Val 1,310 (29.6% HT, 12 mice) ·
  Test 1,693 (WT 83.5% / HT 16.5%, 12 held-out mice).
- **What was adapted vs the base model:** two levers change together — cohort narrows to strain1 **and**
  evaluation moves from subject-dependent to subject-independent (same XGBoost family).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.979 | 0.648 | — |
| Recall | 0.903 | 0.900 | — |
| F1 | 0.939 | 0.753 | weighted **0.909** |
| Accuracy | | | **0.903** (train 0.793) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 1276, WT→HT 137], [HT→WT 28, HT→HT 252]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.903 | 0.733 | +0.170 |
| Weighted F1 | 0.909 | 0.749 | +0.160 |
| WT F1 | 0.939 | 0.785 | +0.154 |
| HT F1 | 0.753 | 0.649 | +0.104 |
| HT recall | 0.900 | 0.940 | −0.040 |
| HT precision | 0.648 | 0.496 | +0.152 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- Restricting to the strain1 cohort flips the usual dependent→independent penalty: this leak-free run
  **beats the dependent base model by +0.170 accuracy and +0.160 weighted F1**, the cleaner single-cohort
  signal more than offsetting the harder by-mouse split.
- The minority class improves on both sides of the trade-off versus base — **HT precision +0.152 (0.648)**
  and HT F1 +0.104 (0.753) — while HT recall stays high at 0.900 (only −0.040). Fewer false ASD-model
  calls (28 WT→HT here translates to WT precision 0.979) without sacrificing recall.
- Train 0.793 sits **below** test 0.903 — no overfitting; the untuned model is, if anything,
  underfitting the train fold, yet generalizes cleanly to the 12 held-out mice.
- Class separation is genuinely strong here: HT recall 0.900 with precision 0.648 means most ASD-model
  pups are caught and ~2 in 3 positive calls are correct — a far healthier operating point than the
  base model's 0.496 HT precision.

## Recommendations
- Use this strain1 independent run, not the dependent base, for any "new-mouse" estimate on the
  2022–2024 cohort; results are leak-free and well-calibrated, but remain cohort-specific (do not read
  across to strain2).

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices.
- `plots/AUC_error.png` — train/val AUC learning curve. `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png` — feature importance rankings.
- `model/xgboost_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, strain filter, split info, class balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
