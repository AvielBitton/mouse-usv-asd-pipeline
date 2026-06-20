# G_augment__cnn1d__dependent — 1D-CNN · subject-dependent · sliding-window augmentation

> 1D-CNN on the baseline sequence data with sliding-window augmentation; evaluated subject-dependent (leaky) — collapses toward predicting WT for almost everyone.

## Overview
- **Model:** 1D-CNN (~86K params; chronological per-syllable sequence input, order preserved,
  `max_seq_len=256`). Scored at **session level** (82 test sessions), not per recording.
- **Evaluation split:** subject-dependent — random session-level split (`subject_eval_independent=false`,
  `group_split=false`). Mice leak across sets (log: 61 shared mice train/test), so this is the
  optimistic setting, like the base model.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions /
  106 mice; train 244 / val 82 / test 82, HT ≈ 23–24% throughout.
- **What was adapted vs the base model (lever G):** sliding-window augmentation
  (`augment_windows=4`, `window_stride=128` → 369 train windows from 244 sessions), on top of milder
  class weighting (`pos_weight_beta=0.5` → pos_weight 1.79, BCE loss, no sampler).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.776 | 0.333 | — |
| Recall | 0.937 | 0.105 | — |
| F1 | 0.849 | 0.160 | weighted **0.689** |
| Accuracy | | | **0.744** (train 0.832) |

AUC 0.587 · balanced acc 0.521 · macro F1 0.504 · MCC 0.068 · PR-AUC 0.331. Early-stopped at epoch 24
(best val AUC 0.702). Confusion matrix (rows = true): `[[WT→WT 59, WT→HT 4], [HT→WT 17, HT→HT 2]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.744 | 0.733 | +0.011 |
| Weighted F1 | 0.689 | 0.749 | −0.060 |
| WT F1 | 0.849 | 0.785 | +0.064 |
| HT F1 | 0.160 | 0.649 | −0.489 |
| HT recall | 0.105 | 0.940 | −0.835 |
| HT precision | 0.333 | 0.496 | −0.163 |

*Directional only: this NN is scored on ~82 session-level sequences, whereas the tabular base is scored
on ~2,465 recording-level rows — not a like-for-like comparison.*

## Key insights
- **Degenerate collapse toward WT.** The model calls HT for only 2 of 19 positives (HT recall 0.105,
  HT F1 0.160); the +0.011 accuracy bump is purely from the 77% WT majority. Despite augmentation and
  pos_weight 1.79, it learned to predict WT for almost everyone.
- **No real discrimination.** Test AUC 0.587, balanced accuracy 0.521 and MCC 0.068 are barely above
  chance — the headline 0.744 accuracy is misleading.
- **Train/val divergence.** Train accuracy climbs to 0.93 while val loss rises after ~epoch 10 (val AUC
  plateaus ~0.70); the model overfits the WT majority rather than learning HT structure, and the gap
  carries straight into the collapsed test result.
- Augmentation (369 windows) did not rescue the minority class on this leaky split — it mostly
  reinforced the WT prior.

## Recommendations
- Prefer the balanced-minibatch sampler config (lever D / H) over augmentation for collapse; pos_weight
  alone (lever G here) is insufficient on this data.
- Do not use this run for any HT-detection claim — HT recall 0.105 means it misses ~9 in 10 ASD-model
  pups. If kept, threshold tuning toward `target_recall` is mandatory before use.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.587). `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/cnn1d_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`; split info, data stats and early stopping in `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
