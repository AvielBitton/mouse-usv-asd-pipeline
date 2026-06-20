# G_augment__bilstm__dependent — BiLSTM · subject-dependent · experiment G (augment)

> BiLSTM on the baseline sequence data with sliding-window augmentation, evaluated on the leaky (mouse-overlap) dependent split.

## Overview
- **Model:** BiLSTM (~149K params; 2 layers, hidden 64, dropout 0.3) over a chronological per-syllable
  sequence (`max_seq_len` 256, order preserved), scored at **session** level — not the 48 aggregated
  per-recording tabular features of the base model.
- **Evaluation split:** subject-dependent — random session-level split (`subject_eval_independent=false`,
  `group_split=false`). The log flags **mouse overlap** (train/test 61 shared mice), so the same pup can
  appear in train and test (leakage; optimistic vs an honest by-mouse split).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions / 106
  mice → train 244 / val 82 / **test 82** sessions (HT 23%, WT 77%).
- **What was adapted vs the base model (lever G):** sliding-window augmentation (`augment_windows=4`,
  `window_stride=128`) expanding 244 sessions into 369 train windows, on top of mild class weighting
  (`pos_weight_beta=0.5` → pos_weight 1.791); plain BCE, no sampler, no weight decay.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.800 | 0.353 | — |
| Recall | 0.825 | 0.316 | — |
| F1 | 0.813 | 0.333 | weighted **0.701** |
| Accuracy | | | **0.707** (train 0.791) |

AUC 0.673 · balanced accuracy 0.571 · MCC 0.147 · PR-AUC 0.378 · best val AUC 0.748 · early-stopped at epoch 28/100.

Confusion matrix (rows = true, cols = pred): `[[WT→WT 52, WT→HT 11], [HT→WT 13, HT→HT 6]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.707 | 0.733 | −0.026 |
| Weighted F1 | 0.701 | 0.749 | −0.048 |
| WT F1 | 0.813 | 0.785 | +0.028 |
| HT F1 | 0.333 | 0.649 | −0.316 |
| HT recall | 0.316 | 0.940 | −0.624 |
| HT precision | 0.353 | 0.496 | −0.143 |

*Directional only: this BiLSTM is scored on 82 session-level sequences, whereas the tabular base is scored on ~2,465 recording-level rows — not a like-for-like comparison.*

## Key insights
- The minority class is badly under-served, the **opposite** of the usual NN collapse: HT recall **0.316**
  and HT F1 **0.333** mean the model only catches 6 of 19 ASD-model pups and leans toward calling WT.
  HT recall is −0.624 below the base model — augmentation did not rescue the positive class here.
- Headline accuracy (0.707) sits near the WT prior (77%); balanced accuracy 0.571 and MCC 0.147 confirm
  the model is barely above chance once class imbalance is accounted for.
- Overfitting is visible despite augmentation: train accuracy climbs to ~0.91 while val loss rises after
  ~epoch 13 (val AUC peaks 0.748, then drifts down), triggering early stopping at 28. Test AUC is only
  0.673, below best val AUC.
- WT metrics improved (+0.028 F1) only because predictions shifted toward the majority class — that gain
  is the flip side of the HT collapse, not a real win.

## Recommendations
- For collapse toward WT, the balanced minibatch sampler (lever D) is the most reliable fix in this
  brief; mild `pos_weight_beta=0.5` plus window augmentation was insufficient. If keeping this config,
  threshold tuning on the HT score is needed to recover usable HT recall.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.673). `plots/training_curves.png` — loss/accuracy/AUC per epoch.
- `model/bilstm_best.pt` — best checkpoint (val AUC 0.748). `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`; split/data/training trace: `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
