# cnn1d_subject_eval_dependent — 1D-CNN · subject-dependent

**Status:** archived — superseded by `results/neural_networks/cnn1d_subject_eval_dependent_baseline`.

> 1D-CNN over per-syllable sequences, evaluated **session-level** on a leaky (row-level) random split.

## Overview
- **Model:** 1D-CNN (86,041 params) over a chronological per-syllable sequence (order preserved,
  `MAX_SEQ_LEN=256`), unlike the tabular base model's 48 aggregated per-recording features.
- **Evaluation split:** subject-dependent — random **session-level** split (`group_split=false`), so the
  same mouse leaks across train/val/test (the log warns of 61 shared mice between train and test). This
  is the optimistic, leakage-prone setting.
- **Dataset:** legacy pre-baseline cache (`segmentation_classification_all_data.csv`) — 442 sessions
  from 119 mice (WT=336, HT=106), **not** the Issue-#46 baseline data. Scored at **session level**:
  test = 89 sessions (WT 68 / 76%, HT 21 / 24%).
- **Training:** `pos_weight=0.320` class weighting, early-stopped at epoch 33/50 (best val AUC 0.638).
- **Label note:** this run encodes **class 0 = HT, class 1 = WT** (inverted vs the baseline convention);
  numbers below are reported per genotype, not per raw class index.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.808 | 0.297 | — |
| Recall | 0.618 | 0.524 | — |
| F1 | 0.700 | 0.379 | weighted **0.624** |
| Accuracy | | | **0.596** (train 0.822) |

Test AUC 0.653. Confusion matrix counts (rows = true, cols = pred): `[[HT→HT 11, HT→WT 10], [WT→HT 26, WT→WT 42]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.596 | 0.733 | −0.137 |
| Weighted F1 | 0.624 | 0.749 | −0.125 |
| WT F1 | 0.700 | 0.785 | −0.085 |
| HT F1 | 0.379 | 0.649 | −0.270 |
| HT recall | 0.524 | 0.940 | −0.416 |
| HT precision | 0.297 | 0.496 | −0.199 |

*Directional only: this NN is scored on ~89 session-level sequences from a legacy cache, while the
tabular base is scored on ~2,465 recording-level rows of the Issue-#46 baseline data — not a like-for-like comparison.*

## Key insights
- The 1D-CNN underperforms the tabular base on every metric: accuracy 0.596 (−0.137), weighted F1 0.624
  (−0.125). Both the dataset (legacy cache, not baseline) and the unit (sessions, not recordings) differ,
  so treat the gap as directional.
- No degenerate collapse — both classes get predicted (HT recall 0.524, WT recall 0.618) — but minority
  detection is weak: **HT precision 0.297 / F1 0.379**, with 10 of 21 HT sessions called WT and only 11
  of 37 HT predictions correct.
- Heavy overfit despite the leaky split: train accuracy 0.822 / train AUC 0.941 vs test accuracy 0.596 /
  test AUC 0.653, and val accuracy swung erratically (0.36–0.72 across epochs), never tracking train.
- AUC 0.653 shows only modest ranking signal; the small 89-session test set makes per-class metrics noisy.

## Recommendations
- Use the superseding `results/neural_networks/cnn1d_subject_eval_dependent_baseline` run (Issue-#46
  baseline data, corrected labels) for any current 1D-CNN comparison; do not cite these legacy numbers.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC. `plots/training_curves.png` — loss/accuracy/AUC over 33 epochs.
- `model/cnn1d_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`; `logs/out.txt` — flags, split info, class balance, early stopping.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
