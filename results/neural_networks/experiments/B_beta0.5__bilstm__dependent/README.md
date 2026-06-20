# B_beta0.5__bilstm__dependent — BiLSTM · subject-dependent · experiment B (beta0.5)

> BiLSTM on baseline sequences with milder class weighting (`pos_weight_beta=0.5`) — collapses to all-WT.

## Overview
- **Model:** BiLSTM (~149K params; 2 layers, hidden 64). Input is a chronological per-syllable
  sequence (order preserved, `max_seq_len=256`), not the tabular 48 aggregated per-recording features.
- **Evaluation split:** subject-dependent — random **session-level** split (`subject_eval_independent=false`,
  `group_split=false`), so the same mouse can appear in train and test. The log flags this leakage:
  `train/test: 61 shared mice`. Optimistic setting, same family as the base model.
- **What was adapted vs base (experiment B):** milder class weighting — `pos_weight_beta=0.5` gives
  `pos_weight=1.791` instead of the full inverse-frequency weight used by control (A). No sampler, plain
  BCE loss, no augmentation.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice; scored at **session level**: 244 train / 82 val / 82 test sessions (test HT 23% / WT 77%).
- **Training:** early-stopped at epoch 16 (best val AUC 0.690); LR decayed 1e-3 → 2.5e-4.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.768 | 0.000 | — |
| Recall | 1.000 | 0.000 | — |
| F1 | 0.869 | 0.000 | weighted **0.668** |
| Accuracy | | | **0.768** (train 0.762) |

Test AUC 0.665 · PR-AUC 0.501 · balanced accuracy **0.500** · MCC **0.000** · macro-F1 0.434.

**Degenerate collapse: the model predicts WT for all 82 test sessions** — HT recall 0.0, HT F1 0.0, so
"accuracy 0.768" is just the WT base rate (63/82), not real skill.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.768 | 0.733 | +0.035 |
| Weighted F1 | 0.668 | 0.749 | −0.081 |
| WT F1 | 0.869 | 0.785 | +0.084 |
| HT F1 | 0.000 | 0.649 | −0.649 |
| HT recall | 0.000 | 0.940 | −0.940 |
| HT precision | 0.000 | 0.496 | −0.496 |

*Comparison is directional, not like-for-like: this NN is scored on session-level sequence data
(82 test sessions) while the tabular base is scored on recording-level data (~2,465 rows).*

## Key insights
- **The run is a degenerate collapse to the majority class** — every test session is called WT
  (HT recall 0.0, HT F1 0.0). The headline accuracy 0.768 only matches the WT prevalence; balanced
  accuracy 0.500 and MCC 0.000 confirm zero discriminative skill at the 0.5 cut.
- **Milder weighting (beta=0.5) was too weak to break the collapse.** `pos_weight=1.791` did not push
  the model off the all-WT optimum; train accuracy (0.762) tracks the same base rate, and val accuracy
  never moved past ~0.78 across all 16 epochs.
- **There is some latent signal that the threshold throws away:** test AUC 0.665 / best val AUC 0.690
  sit above chance, so the ranking is not random — but the operating point is useless, the opposite
  failure mode to the base model (HT recall 0.940).
- The +0.035 accuracy / +0.084 WT-F1 "wins" over base are artifacts of predicting the majority class;
  the −0.649 HT-F1 and −0.940 HT-recall are the real story.

## Recommendations
- Stronger minority handling is needed: the balanced minibatch **sampler (config D)** is the most
  reliable fix for this collapse; focal loss (E) or full inverse-frequency weighting (control A) are
  next to try before beta0.5.
- Because AUC > 0.5, a threshold sweep could recover some HT recall from this exact checkpoint, but the
  default-cut model should not be used as-is.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (collapsed to
  the WT column). `plots/roc_curve.png` — ROC (AUC 0.665). `plots/training_curves.png` — loss/acc/AUC vs epoch.
- `model/bilstm_best.pt` — best checkpoint (epoch with val AUC 0.690). `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`; split info, class balance and early stopping in `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
