# xgboost_tuned_dependent_strain1_subject_eval_independent_baseline — XGBoost (tuned-dependent recipe) · subject-independent · strain1

> Dependent-tuned XGBoost on the strain1 cohort, evaluated **leak-free** (split grouped by mouse) — a cross-split check.

## Overview
- **Model:** XGBoost with `xgboost_tuned_dependent` hyperparameters (200-trial random search tuned for the
  subject-*dependent* split). Here they run on the *independent* split, so the tuning was optimized for a
  different, easier setting — treat this as a cross-check, not a matched configuration.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`, group-aware
  by `mouse_idx`), so no mouse appears in two sets. This is the honest "generalize to unseen mice" setting
  (the dependent base model splits rows randomly and lets mice leak across train/test).
- **Cohort:** strain1 (years 2022–2024, mixed BALB/C + C57 background). Strain filter kept 7,572/12,323
  baseline rows (`pup_strain == 1`), 59 mice.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 1,693 recordings from 12 held-out mice (WT 83.5% / HT 16.5%); class weighting via
  `scale_pos_weight = 3.51`.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.963 | 0.655 | — |
| Recall | 0.914 | 0.821 | — |
| F1 | 0.938 | 0.729 | weighted **0.903** |
| Accuracy | | | **0.899** (train 0.903) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 1292, WT→HT 121], [HT→WT 50, HT→HT 230]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.899 | 0.733 | +0.166 |
| Weighted F1 | 0.903 | 0.749 | +0.154 |
| WT F1 | 0.938 | 0.785 | +0.153 |
| HT F1 | 0.729 | 0.649 | +0.080 |
| HT recall | 0.821 | 0.940 | −0.119 |
| HT precision | 0.655 | 0.496 | +0.159 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- Despite the **harder leak-free split**, this run beats the dependent base model across the board on
  aggregate metrics — accuracy 0.899 (+0.166) and weighted F1 0.903 (+0.154). That gain is largely the
  strain1 restriction (a cleaner, easier 12-mouse test cohort, 83.5% WT) rather than the split being
  forgiving; the leak-free score is high because the cohort is narrow, not because generalization is solved.
- The operating point is far more balanced than the base model: **HT precision jumps to 0.655** (+0.159)
  while **HT recall drops to 0.821** (−0.119). The base model caught nearly every HT (recall 0.940) but at
  ~0.50 precision; this run trades ~12 pts of HT recall for ~16 pts of precision, halving false-positive HT
  calls. It still misses ~1 in 5 ASD-model pups (50 of 280 HT → WT).
- Train 0.903 vs test 0.899 shows almost no train–test gap — unusual for an independent split, and a sign
  the strain1 test mice happen to be well-separated, not that the dependent-tuned recipe transfers cleanly.
- Hyperparameters were tuned for the **dependent** split; the matched `xgboost_tuned_independent` recipe
  (heavily regularized/shallow) is the right comparison for honest independent-split performance.

## Recommendations
- Treat these numbers as cohort-specific (strain1 only) and tuning-mismatched; do not read them as
  general independent-split performance. Compare against the strain1 `xgboost_tuned_independent` run before
  drawing conclusions.
- If higher HT recall is needed, tune the decision threshold — see the threshold runs (`../../threshold/`,
  `../../threshold_objectives/`); `target_recall` keeps a controlled operating point on independent splits.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices.
- `plots/AUC_error.png` — AUC / error learning curve. `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png` — feature importance.
- `model/xgboost_tuned_dependent_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, split info, class balance.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
