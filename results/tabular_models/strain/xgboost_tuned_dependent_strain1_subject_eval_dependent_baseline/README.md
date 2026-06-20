# xgboost_tuned_dependent_strain1_subject_eval_dependent_baseline — XGBoost (tuned-dependent) · subject-dependent · strain1

> Tuned XGBoost on the strain1 cohort, evaluated **subject-dependent** (rows split randomly, mice leak across train/test — optimistic).

## Overview
- **Model:** XGBoost with the `tuned_dependent` recipe (hyperparameters from a 200-trial random search
  tuned for the dependent split). `scale_pos_weight=3.5284` applied for the HT minority.
- **Evaluation split:** subject-dependent — random row-level split. The log flags **mouse overlap**
  (59 mice shared across train/val/test), so the same mouse appears in train and test. This is the
  leaky, optimistic setting that matches the base model's split type.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction), restricted to
  **strain1** (2022–2024, mixed BALB/C+C57). Strain filter kept 7,572/12,323 rows over 59 mice.
  Test = 1,515 recordings (WT 76.4% / HT 23.6%).
- **What was adapted vs the base model:** two levers change together — the tuned-dependent recipe
  (vs the untuned legacy XGBoost) **and** the cohort narrows to strain1 only.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.936 | 0.533 | — |
| Recall | 0.776 | 0.829 | — |
| F1 | 0.849 | 0.649 | weighted **0.802** |
| Accuracy | | | **0.789** (train 0.903) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 899, WT→HT 259], [HT→WT 61, HT→HT 296]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.789 | 0.733 | +0.056 |
| Weighted F1 | 0.802 | 0.749 | +0.053 |
| WT F1 | 0.849 | 0.785 | +0.064 |
| HT F1 | 0.649 | 0.649 | +0.000 |
| HT recall | 0.829 | 0.940 | −0.111 |
| HT precision | 0.533 | 0.496 | +0.037 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- On the same leaky dependent split, tuning + the cleaner strain1 cohort lifts headline numbers:
  **accuracy 0.789 (+0.056)** and **weighted F1 0.802 (+0.053)** over the base model, driven mostly by
  WT (F1 0.849, +0.064).
- The operating point trades minority recall for precision: **HT recall drops to 0.829 (−0.111)** while
  **HT precision rises to 0.533 (+0.037)**. The two cancel out — **HT F1 is unchanged at 0.649**.
- Class separation on HT is still weak — about half of HT predictions are false positives (precision
  0.533); the model misses ~1 in 6 ASD-model pups (61 of 357).
- Train 0.903 vs test 0.789 (0.11 gap) plus the explicit mouse-overlap warning mean these numbers are
  optimistic; treat them as an upper bound, not a generalization estimate.

## Recommendations
- For an honest "new-mouse" estimate, use the subject-independent strain1 run rather than this
  dependent one — this split lets mice leak across train/test.
- HT recall sits below the base model at the default 0.5 cut; if minority recall matters, see the
  threshold runs (`../../threshold/`, `../../threshold_objectives/`).

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices.
- `plots/AUC_error.png` — training/validation AUC + error curves.
- `plots/feature_importances_0.png`, `plots/feature_importance_1.png` — feature importances.
- `model/xgboost_tuned_dependent_model.pkl` — fitted model. `logs/out.txt` — flags, split info, class balance.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
