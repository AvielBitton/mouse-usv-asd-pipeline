# xgboost_subject_eval_dependent_baseline — XGBoost · subject-dependent

> Untuned XGBoost on the official baseline data, evaluated subject-**dependent** (random row-level split). **This is the reference base model.**

## Overview
- **Model:** XGBoost, untuned legacy recipe (`scale_pos_weight=3.12` from n_WT/n_HT; no hyperparameter
  search). HT is the positive minority class.
- **Evaluation split:** subject-dependent — train/val/test split **randomly at the row level**, so the
  same mouse can appear in train and test (logged overlap: 105 mice shared train↔test). This leaks
  per-mouse signal and gives an **optimistic** read; the leak-free `--independent` runs typically land
  10–15 pts lower.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Train 7,393 / Val 2,465 / Test 2,465 recordings; test class balance WT 73.8% / HT 26.2%.
- **Role:** this run **is** the anchor every other tabular run is measured against (Δ vs base).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.968 | 0.496 | — |
| Recall | 0.660 | 0.940 | — |
| F1 | 0.785 | 0.649 | weighted **0.749** |
| Accuracy | | | **0.733** (train 0.771) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 1199, WT→HT 619], [HT→WT 39, HT→HT 608]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
This folder **is** the base model, so there is no delta to report. Every other tabular run's
"Δ vs base model" table is measured against the numbers above (Test accuracy 0.733, Weighted F1 0.749,
WT F1 0.785, HT F1 0.649, HT recall 0.940, HT precision 0.496).

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- The operating point is **heavily tilted toward catching HT**: HT recall 0.940 (misses only 39 of 647
  ASD-model pups) at the cost of WT recall 0.660 — 619 WT recordings are flagged as HT.
- **Class separation is weak** — HT precision is only 0.496, so roughly half of HT predictions are false
  positives; HT F1 lands at 0.649 despite the strong recall.
- Train 0.771 vs test 0.733 (0.038 gap) looks well-fit, but that small gap is **inflated by leakage** —
  the random split lets the same mouse appear on both sides, so this is an optimistic ceiling, not an
  unseen-mouse estimate.

## Recommendations
- Treat these numbers as an **optimistic upper bound**, not a generalization estimate; use the
  `--independent` runs for any "new-mouse" claim.
- HT precision ~0.50 at the default 0.5 cut means positive calls need confirmation — see the threshold
  runs (`../threshold/`, `../threshold_objectives/`) to pick a calibrated operating point.

## Artifacts
- `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`, `plots/confusionmatrix_strain2.png`,
  `plots/conf_matrix.png` — confusion matrices (overall + per strain).
- `plots/AUC_error.png` — training/validation learning curve. `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png` — feature importances.
- `model/xgboost_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, split info, class balance.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
