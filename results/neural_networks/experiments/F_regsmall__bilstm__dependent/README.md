# F_regsmall__bilstm__dependent — BiLSTM · subject-dependent · experiment F (regsmall)

> Heavily-regularized small BiLSTM on the baseline sequences, dependent split — collapses to near-all-WT.

## Overview
- **Model:** BiLSTM over chronological per-syllable sequences (order preserved), scored at session level
  — not the 48 aggregated per-recording features the tabular base uses. This is the **regsmall**
  variant: shrunk to `hidden_size=32`, `num_layers=1` with `weight_decay=0.001` and `dropout=0.5`
  (16,857 params, far below the ~149K full BiLSTM).
- **Evaluation split:** subject-**dependent** — random session-level split, so the same mouse can sit in
  train and test (logged overlap: 61 shared mice train/test). Optimistic/leaky, same family as the base.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice; 244 train / 82 val / 82 test sessions (test HT 23% / WT 77%).
- **What was adapted vs the base model:** lever **F (regsmall)** — extra regularization + a smaller net
  intended to curb overfitting on the tiny independent split, here run on the dependent split. Mild
  class weighting carried in (`pos_weight_beta=0.5`, `pos_weight≈1.79`, BCE loss, no sampler).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.778 | 1.000 | — |
| Recall | 1.000 | 0.053 | — |
| F1 | 0.875 | 0.100 | weighted **0.695** |
| Accuracy | | | **0.780** (train 0.762) |

AUC 0.683 · balanced accuracy 0.526 · MCC 0.202 · PR-AUC 0.426 · early-stopped at epoch 24 (best val AUC 0.720).

Confusion matrix (rows = true, cols = pred): `[[WT→WT 63, WT→HT 0], [HT→WT 18, HT→HT 1]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.780 | 0.733 | +0.047 |
| Weighted F1 | 0.695 | 0.749 | −0.054 |
| WT F1 | 0.875 | 0.785 | +0.090 |
| HT F1 | 0.100 | 0.649 | −0.549 |
| HT recall | 0.053 | 0.940 | −0.887 |
| HT precision | 1.000 | 0.496 | +0.504 |

*Comparison is directional, not like-for-like: this NN is scored on 82 session-level sequences, whereas the tabular base is scored on ~2,465 recording-level rows.*

## Key insights
- **Degenerate collapse toward WT.** The net predicts WT for 81 of 82 sessions: WT recall 1.000, HT
  recall 0.053 (1 of 19 HT sessions caught), HT F1 just 0.100. The headline 0.780 accuracy is the
  majority-class baseline (test WT share 77%), not real learning.
- **Balanced accuracy 0.526 and MCC 0.202** confirm the model barely separates classes — the +0.047
  accuracy and +0.504 HT precision over base are artifacts of the all-WT operating point (the single HT
  call happens to be correct), while HT recall craters −0.887.
- **Over-regularization, wrong split.** regsmall was designed for the small leak-free independent split;
  applied to the dependent split it just suppresses the minority class. Val AUC peaked at 0.720 (epoch 9)
  then drifted down — the small net never found a usable HT decision region at the 0.5 cut.

## Recommendations
- Do not use this run as a dependent reference — it is a collapsed model. The base XGBoost dependent run
  (HT recall 0.940) is the comparison anchor.
- For BiLSTM collapse, the balanced-minibatch sampler (lever **D**) is the most reliable fix; pair with a
  lower decision threshold (see threshold runs) rather than stacking weight decay + dropout + shrinkage.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.683). `plots/training_curves.png` — loss/accuracy/AUC over 24 epochs.
- `model/bilstm_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` (classification_report, config) + `logs/out.txt` (split info, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
