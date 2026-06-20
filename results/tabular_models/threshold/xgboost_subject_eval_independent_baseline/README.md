# xgboost_subject_eval_independent_baseline — XGBoost · subject-independent · threshold (Youden)

> Decision-threshold tuning (Youden J) on the leak-free independent XGBoost model — no retraining, only the 0.5 cut is replaced.

## Overview
- **Model:** XGBoost (untuned legacy recipe). This run does **not** retrain — it takes the already-fitted
  independent model and replaces the default 0.5 decision cut with a threshold chosen from leak-free
  **validation** probabilities (Youden J).
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`,
  group-aware on `mouse_idx`), so no mouse appears in two sets. This is the honest "generalize to unseen
  mice" setting (harder than the dependent base model, which splits rows randomly and lets mice leak
  across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 2,139 recordings from 22 held-out mice (WT 72.9% / HT 27.1%); val = 2,318 rows from 21 mice.
- **What was adapted vs the base model:** decision-threshold tuning only — the operating point moves from
  0.5 to **0.1280** (Youden), and evaluation moves from subject-dependent to subject-independent. No
  hyperparameters change.

## Results (test set)
Tuned threshold = **0.1280** (Youden J, val-derived). Validation AUC 0.691 / **test AUC 0.770**
(threshold-independent).

| Metric | @0.5 (default) | @tuned (0.1280) | Δ |
|---|---|---|---|
| Accuracy | 0.692 | 0.705 | +0.013 |
| Balanced accuracy | 0.678 | 0.797 | +0.119 |
| HT recall | 0.646 | 0.998 | +0.352 |
| HT precision | 0.452 | 0.478 | +0.026 |
| HT F1 | 0.532 | 0.647 | +0.115 |
| WT recall | 0.710 | 0.596 | −0.113 |
| WT precision | 0.844 | 0.999 | +0.155 |
| WT F1 | 0.771 | 0.747 | −0.024 |

Confusion matrix @tuned (rows = true, cols = pred): `[[WT→WT 930, WT→HT 630], [HT→WT 1, HT→HT 578]]`
(vs @0.5: `[[1107, 453], [205, 374]]`).

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run (tuned) | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.705 | 0.733 | −0.028 |
| Weighted F1 | 0.720 | 0.749 | −0.029 |
| WT F1 | 0.747 | 0.785 | −0.038 |
| HT F1 | 0.647 | 0.649 | −0.002 |
| HT recall | 0.998 | 0.940 | +0.058 |
| HT precision | 0.478 | 0.496 | −0.018 |

The base model is at its default 0.5 cut; this run's column is the **tuned** 0.1280 operating point.

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- The tuned threshold is a strong **recall-maximizing** move: dropping the cut from 0.5 to 0.1280 lifts
  HT recall from 0.646 to **0.998** (+0.352) and balanced accuracy from 0.678 to **0.797** (+0.119) —
  only 1 of 579 ASD-model pups is missed.
- That recall is bought with WT cost: WT recall falls to 0.596 (630 WT calls flipped to HT), so **HT
  precision stays ≈ 0.48** — roughly half of HT predictions are still false positives. The cut trades WT
  false negatives for WT false positives rather than improving separation.
- Class separation is genuinely modest: **test AUC 0.770** with **val AUC only 0.691**, so the threshold
  is tuned on a weaker val signal — expect the operating point to be slightly optimistic on test.
- vs the dependent base, the tuned run lands ~0.03 below on accuracy/weighted F1 (the honest
  independent penalty), but matches HT F1 (0.647 vs 0.649) while pushing HT recall above base (0.998 vs
  0.940) — a near-complete-coverage operating point for the minority class.

## Recommendations
- Use this run when **catching every ASD-model pup matters more than false alarms** (HT recall 0.998);
  for a balanced operating point with controlled WT loss, prefer the `target_recall` candidate (0.4392,
  HT recall ≥ 0.80) from `threshold_report.txt` or compare across `../threshold_objectives/`.
- Positive (HT) calls still need confirmation — HT precision ≈ 0.48 — so do not treat an HT prediction
  as a diagnosis at this threshold.
- See the curated parent summary at [`../README.md`](../README.md) for the cross-objective threshold picture.

## Artifacts
- `plots/roc_curve.png` — ROC + AUC. `plots/conf_matrix_thr0.5.png` / `plots/conf_matrix_thr_tuned.png`
  — confusion matrices at the default and tuned cuts; `plots/conf_matrix.png`,
  `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`, `plots/confusionmatrix_strain2.png`
  (overall + per strain); `plots/AUC_error.png`, `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png`.
- `model/xgboost_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, split info, class balance,
  applied threshold. `probabilities_val.csv` / `probabilities_test.csv` — raw scores.
- Metrics source: `threshold_report.txt` + `threshold_metrics.json` (`comparison_vs_baseline.txt` run column only).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `threshold_report.txt` + `threshold_metrics.json` · summary auto-generated*
