# xgboost_tuned_independent_subject_eval_independent_baseline — XGBoost (tuned, independent recipe) · subject-independent

> Tuned XGBoost on the official baseline data, evaluated **leak-free** (split grouped by mouse), with hyperparameters from a 200-trial search tuned for this independent split.

## Overview
- **Model:** XGBoost with the `xgboost_tuned_independent` recipe — hyperparameters from a 200-trial
  random search tuned specifically for the independent split (heavily regularized/shallow), with
  `scale_pos_weight=3.07` to weight the HT minority.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (group-aware on
  `mouse_idx`, `--independent`), so no mouse appears in two sets. This is the honest "generalize to
  unseen mice" setting (harder than the dependent base model, which splits rows randomly and lets mice
  leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Train 7,866 rows / 63 mice, Val 2,318 rows / 21 mice, Test 2,139 rows from 22 held-out mice
  (WT 72.9% / HT 27.1%).
- **What was adapted vs the base model:** two levers change together — tuned hyperparameters (vs the
  untuned legacy base recipe) **and** evaluation moves from subject-dependent to subject-independent.
  Tuning and evaluation split are matched here (independent recipe on the independent split).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.929 | 0.473 | — |
| Recall | 0.640 | 0.869 | — |
| F1 | 0.758 | 0.612 | weighted **0.719** |
| Accuracy | | | **0.702** (train 0.714) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 999, WT→HT 561], [HT→WT 76, HT→HT 503]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.702 | 0.733 | −0.031 |
| Weighted F1 | 0.719 | 0.749 | −0.030 |
| WT F1 | 0.758 | 0.785 | −0.027 |
| HT F1 | 0.612 | 0.649 | −0.037 |
| HT recall | 0.869 | 0.940 | −0.071 |
| HT precision | 0.473 | 0.496 | −0.023 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- The honest leak-free split costs only modestly here: accuracy 0.702 and weighted F1 0.719 land about
  0.03 below the dependent base model — far short of the usual 10–15 pt dependent→independent drop, so
  the regularized tuned recipe generalizes well to unseen mice.
- Train 0.714 vs test 0.702 (0.01 gap) shows almost no overfitting — the shallow, heavily regularized
  recipe is doing its job; the model is not memorizing training mice.
- The minority class stays high-recall but imprecise: **HT recall 0.869** with **HT precision 0.473**
  means more than half of HT predictions are false positives (561 WT recordings called HT). The model
  still leans toward flagging HT, much like the base.
- WT recall drops to 0.640 (−0.020 vs base) — the price of the HT-leaning operating point is missing
  ~36% of true WT recordings.

## Recommendations
- HT precision ≈ 0.47 at the default 0.5 cut, so positive calls need confirmation; tune the threshold
  (see `../threshold/`, `../threshold_objectives/`) to trade some HT recall for cleaner precision.
- Use this independent run, not the dependent base, for any "new-mouse" performance estimate — the
  hyperparameters and the evaluation split are matched, so it is the honest generalization number.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per strain).
- `plots/AUC_error.png` — training/validation AUC curve. `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png` — feature importances.
- `model/xgboost_tuned_independent_model.pkl` — fitted model. `logs/out.txt` — flags, split info,
  class balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
