# xgboost_tuned_independent_subject_eval_independent_baseline — XGBoost (tuned) · subject-independent · threshold (Youden)

> Tuned independent XGBoost on the baseline data, leak-free split, with the 0.5 cut replaced by a Youden-J threshold from validation probabilities.

## Overview
- **Model:** `xgboost_tuned_independent` — XGBoost with hyperparameters from a 200-trial random search
  tuned for the independent split (heavily regularized / shallow). Class balance handled via
  `scale_pos_weight=3.07`.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`,
  group-aware on `mouse_idx`), so no mouse appears in two sets. Honest "generalize to unseen mice"
  setting (harder than the dependent base model, which splits rows randomly and lets mice leak).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 2,139 recordings from 22 held-out mice (WT 72.9% / HT 27.1%).
- **What was adapted vs the base model:** **decision-threshold tuning only** — no retraining. The 0.5
  cut is replaced by the Youden-J threshold (0.288) chosen from leak-free **validation** probabilities;
  the underlying split also moves dependent → independent.

## Results (test set)
Tuned threshold = **0.288** (Youden J). Val AUC 0.641 / test AUC 0.753 (threshold-independent).

@0.5 (default) vs @tuned:
| Metric | @0.5 | @tuned | Δ |
|---|---|---|---|
| Accuracy | 0.695 | 0.704 | +0.008 |
| Balanced accuracy | 0.725 | 0.797 | +0.071 |
| HT recall | 0.791 | 1.000 | +0.209 |
| HT precision | 0.463 | 0.477 | +0.014 |
| HT F1 | 0.584 | 0.646 | +0.062 |
| WT recall | 0.660 | 0.594 | −0.066 |
| WT precision | 0.895 | 1.000 | +0.105 |
| WT F1 | 0.759 | 0.745 | −0.014 |

Per-class @tuned: WT precision 1.000 / recall 0.594 / F1 0.745; HT precision 0.477 / recall 1.000 /
F1 0.646; weighted F1 **0.718**; accuracy **0.704** (train 0.678).

Confusion matrix @tuned (rows = true, cols = pred): `[[WT→WT 926, WT→HT 634], [HT→WT 0, HT→HT 579]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
Base is at its default 0.5 cut; this run is at the tuned 0.288 cut.
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.704 | 0.733 | −0.029 |
| Weighted F1 | 0.718 | 0.749 | −0.031 |
| WT F1 | 0.745 | 0.785 | −0.040 |
| HT F1 | 0.646 | 0.649 | −0.003 |
| HT recall | 1.000 | 0.940 | +0.060 |
| HT precision | 0.477 | 0.496 | −0.019 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- The tuned threshold trades WT recall for total HT recall: **HT recall hits 1.000** (every ASD-model pup
  caught, +0.209 over the 0.5 cut), lifting balanced accuracy from 0.725 to 0.797 — but **HT precision
  stays ~0.48**, so the model now predicts HT for 634 of 1,560 true-WT recordings.
- This is a near-degenerate operating point on the positive class: zero HT misses (0 in the HT→WT cell)
  comes only because the cut is low; HT F1 (0.646) is barely above base (−0.003) despite perfect recall.
- AUC is the real ceiling here — **test AUC 0.753** vs **val AUC 0.641**. The low val AUC means the
  Youden cut is tuned on weakly-separated validation probabilities, which is why it lands so aggressive.
- Threshold tuning recovers most of the accuracy gap that the leak-free split opens (−0.029 vs base at
  tuned, vs the −0.125 legacy reference in the comparison file), but cannot fix class separation.

## Artifacts
- `plots/roc_curve.png` — ROC (test AUC 0.753). `plots/conf_matrix_thr0.5.png`,
  `plots/conf_matrix_thr_tuned.png` — confusion matrices at each cut.
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per strain).
- `plots/AUC_error.png` — learning curve. `plots/feature_importances_0.png`,
  `plots/feature_importance_1.png` — feature importance.
- `model/xgboost_tuned_independent_model.pkl` — fitted model (threshold applied post-hoc, no retrain).
- `threshold_report.txt`, `threshold_metrics.json` — candidate thresholds + 0.5-vs-tuned metrics.
- `probabilities_val.csv`, `probabilities_test.csv` — per-recording probabilities.
- `logs/out.txt` — flags, split info, class balance. Parent summary: [`../README.md`](../README.md).
- Metrics source: `threshold_metrics.json` + `threshold_report.txt` + `comparison_vs_baseline.txt` (run column only).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `threshold_metrics.json` + `threshold_report.txt` · summary auto-generated*
