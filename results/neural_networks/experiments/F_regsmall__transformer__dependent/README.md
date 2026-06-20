# F_regsmall__transformer__dependent — Transformer · subject-dependent · experiment F (regsmall)

> Heavily-regularized small Transformer on per-syllable sequences, evaluated on the optimistic (leaky) session-level split.

## Overview
- **Model:** Transformer (sequence classifier over the chronological per-syllable feature sequence;
  order preserved). 39,065 params — smaller than the ~73K default; `d_model=64`, `hidden_size=32`,
  1 layer.
- **Evaluation split:** subject-dependent — random **session-level** split (`subject_eval_independent=false`,
  `group_split=false`). Same mouse can land in train and test (the log warns of 61 shared train/test
  mice), so this is the optimistic, leakage-prone setting.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions / 106
  mice; split 244 train / 82 val / 82 test sessions. Test class balance: WT 63 (77%) / HT 19 (23%).
- **What was adapted vs the base model (lever F = regsmall):** anti-collapse regularization for the tiny
  split — `weight_decay=0.001`, `dropout=0.5`, shrunken net (`hidden_size=32`, `num_layers=1`), plus
  mild class weighting (`pos_weight_beta=0.5`, BCE loss, no sampler). Model family also moves from
  XGBoost to a Transformer over sequences.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.776 | 0.333 | — |
| Recall | 0.937 | 0.105 | — |
| F1 | 0.849 | 0.160 | weighted **0.689** |
| Accuracy | | | **0.744** (train 0.840) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 59, WT→HT 4], [HT→WT 17, HT→HT 2]]`.
Test AUC-ROC 0.773 · balanced accuracy 0.521 · MCC 0.068 · best val AUC 0.794 · early-stopped at epoch 92/100.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.744 | 0.733 | +0.011 |
| Weighted F1 | 0.689 | 0.749 | −0.060 |
| WT F1 | 0.849 | 0.785 | +0.064 |
| HT F1 | 0.160 | 0.649 | −0.489 |
| HT recall | 0.105 | 0.940 | −0.835 |
| HT precision | 0.333 | 0.496 | −0.163 |

*Comparison is directional, not like-for-like: this NN is scored on 82 session-level sequences, while the tabular base is scored on ~2,465 recording-level rows.*

## Key insights
- **Near-total WT collapse on the minority class.** HT recall is 0.105 — only 2 of 19 ASD-model pups
  are caught, 17 are called WT — and HT F1 is 0.160. The headline accuracy 0.744 is almost entirely the
  majority-class score (WT recall 0.937); it barely beats the 0.77 always-WT rate.
- Balanced accuracy 0.521 and MCC 0.068 confirm the model is doing little better than constant-WT
  prediction, even though ranking is non-trivial (test AUC 0.773). The threshold, not the scores, is the
  problem.
- The `regsmall` regularization did **not** prevent collapse here. Mild `pos_weight_beta=0.5` (pos_weight
  1.79) was too weak against the 24% HT base rate; the heavy dropout/weight-decay capped capacity without
  fixing the operating point.
- The +0.011 accuracy and +0.064 WT F1 over base are mirages from the leaky dependent split and the
  collapse toward WT — the −0.489 HT F1 / −0.835 HT recall are the real story.

## Recommendations
- This config is not deployable: at the default 0.5 cut it misses ~9 in 10 ASD-model pups. Because AUC is
  healthy (0.773), a lower decision threshold or stronger class weighting/sampler would recover HT recall.
  The balanced-minibatch sampler (lever D) is the more reliable anti-collapse fix than `regsmall` on this
  tiny split.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.773). `plots/training_curves.png` — loss/acc/AUC over 92 epochs.
- `model/transformer_best.pt` — best checkpoint (by val AUC). `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`; split/data stats and early stopping in `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
