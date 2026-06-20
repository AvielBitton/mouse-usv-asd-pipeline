# bilstm_subject_eval_dependent_baseline — BiLSTM · subject-dependent

> BiLSTM on the official baseline data, evaluated subject-**dependent** (random session split) — collapses to predicting HT for everyone.

## Overview
- **Model:** BiLSTM (~149K params) over chronological per-syllable sequences (order preserved), unlike
  the tabular base model's 48 aggregated per-recording features. Scored at the **session** level.
- **Evaluation split:** subject-dependent — random **session-level** split, so the same mouse can sit in
  train, val and test (the log confirms train/test overlap of 61 shared mice). This is the leaky,
  optimistic setting, the same family as the dependent base model.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice (HT 97 / WT 311). Split 244 train / 82 val / 82 test sessions; test is HT 23% / WT 77%.
- **Training:** `pos_weight=3.207`, lr 1e-3 with decay, early-stopped at epoch 16 (best val AUC 0.778).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.000 | 0.232 | — |
| Recall | 0.000 | 1.000 | — |
| F1 | 0.000 | 0.376 | weighted **0.087** |
| Accuracy | | | **0.232** (train 0.242) |

Test AUC-ROC 0.790 (best val AUC 0.778). The model predicts **HT for every test session** — WT recall
0.0, HT recall 1.0 — so accuracy collapses to the HT prevalence (0.232).

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.232 | 0.733 | −0.501 |
| Weighted F1 | 0.087 | 0.749 | −0.662 |
| WT F1 | 0.000 | 0.785 | −0.785 |
| HT F1 | 0.376 | 0.649 | −0.273 |
| HT recall | 1.000 | 0.940 | +0.060 |
| HT precision | 0.232 | 0.496 | −0.264 |

*Caveat: NN are scored on session-level sequence data (82 test sessions here) vs the tabular base's
recording-level data (~2,465 rows), so this comparison is directional, not like-for-like.*

## Key insights
- **Degenerate collapse.** The argmax classifier labels every test session HT (HT recall 1.0, WT recall
  and WT F1 both 0.0); accuracy 0.232 just equals the HT base rate. The model learned nothing usable at
  the default 0.5 cut.
- **AUC tells a different story than accuracy.** Test AUC 0.790 means the ranking carries real signal —
  the collapse is a thresholding/calibration failure, not an absence of separability. With `pos_weight=3.207`
  the decision boundary is pushed all the way onto the minority class.
- **Train mirrors test** (train acc 0.242, train AUC 0.807): this is not overfitting but a stuck,
  all-HT operating point on both sets, despite the leaky dependent split that usually flatters scores.
- Validation accuracy peaked early (0.707 at epoch 5) then drifted down while loss rose — the chosen
  best-AUC checkpoint sits at a non-discriminative threshold.

## Recommendations
- Fix the collapse before trusting this config: the **balanced minibatch sampler (D)** is the most
  reliable remedy; milder class weighting (B `pos_weight_beta=0.5`) or removing it (C `beta0`) and
  threshold tuning on the 0.790-AUC scores are the cheap next levers.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (all-HT column).
- `plots/roc_curve.png` — ROC (AUC 0.790). `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/bilstm_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
