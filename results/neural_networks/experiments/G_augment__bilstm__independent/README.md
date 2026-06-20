# G_augment__bilstm__independent — BiLSTM · subject-independent · sliding-window augmentation

> BiLSTM on the leak-free split with sliding-window sequence augmentation; does not recover the minority class.

## Overview
- **Model:** BiLSTM (2-layer bidirectional LSTM, hidden 64, dropout 0.3; 148,953 params). Input is the
  chronological per-syllable sequence (order preserved, capped at `max_seq_len=256`), not the 48
  aggregated per-recording tabular features.
- **Evaluation split:** subject-independent — group-aware train/val/test split **by mouse**
  (`--independent`), so no mouse appears in two sets. This is the honest "generalize to unseen mice"
  setting, harder than the dependent base model (which splits rows randomly and lets mice leak).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions / 106
  mice → Train 238 (63 mice, HT 24%), Val 80 (21 mice, HT 28%), Test 90 sessions from 22 held-out mice
  (WT 79% / HT 21%). Scoring is **session-level**, not recording-level.
- **What was adapted vs the base model:** lever **G — sliding-window augmentation** (`augment_windows=4`,
  `window_stride=128`, yielding 367 train windows from 238 sessions), kept on top of mild class weighting
  (`pos_weight_beta=0.5` → pos_weight 1.803), BCE loss, no sampler. Plus the model family (BiLSTM) and
  the dependent → independent evaluation change together.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.831 | 0.290 | — |
| Recall | 0.690 | 0.474 | — |
| F1 | 0.754 | 0.360 | weighted **0.671** |
| Accuracy | | | **0.644** (train 0.777) |

Test AUC 0.581 · balanced acc 0.582 · macro-F1 0.557 · MCC 0.141 · PR-AUC 0.297. Best val AUC 0.833
(epoch 10); early stopping at epoch 25.
Confusion matrix (rows = true, cols = pred): `[[WT→WT 49, WT→HT 22], [HT→WT 10, HT→HT 9]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.644 | 0.733 | −0.089 |
| Weighted F1 | 0.671 | 0.749 | −0.078 |
| WT F1 | 0.754 | 0.785 | −0.031 |
| HT F1 | 0.360 | 0.649 | −0.289 |
| HT recall | 0.474 | 0.940 | −0.466 |
| HT precision | 0.290 | 0.496 | −0.206 |

*Comparison is directional, not like-for-like: this NN is scored on 90 session-level sequences from 22
held-out mice, whereas the tabular base is scored on ~2,465 recording-level rows from a leaky dependent
split.*

## Key insights
- The minority class is the weak point: **HT precision 0.290 and HT recall 0.474** — the model catches
  fewer than half the ASD-model pups and is wrong on ~7 of every 10 positive calls (9 of 19 HT correct,
  10 missed). Not a degenerate collapse (both classes get predicted), but well below useful.
- **Augmentation did not buy generalization.** Val AUC peaked at 0.833 (epoch 10) then the model
  overfit — train acc climbed to 0.94 while val loss rose to ~1.1 — and **test AUC collapsed to 0.581**,
  barely above chance. The 0.777 train vs 0.644 test gap confirms overfitting on the tiny 238-session
  independent split that augmentation does not cure.
- Every headline metric trails the base model (HT F1 −0.289, HT recall −0.466), but recall the caveat:
  this is the honest leak-free, session-level setting versus the optimistic leaky recording-level base.
- MCC 0.141 and balanced acc 0.582 show only marginal class separation overall.

## Recommendations
- On this tiny independent split the balanced minibatch sampler (lever D) is the more reliable fix for
  minority-class weakness than window augmentation; prefer it over G here.
- Use early-stopping on val AUC at the epoch-10 peak (0.833) rather than letting training run to 25 —
  the held-out test AUC of 0.581 suggests the late-epoch checkpoint generalizes poorly.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — normalized and count confusion
  matrices. `plots/roc_curve.png` — test ROC. `plots/training_curves.png` — loss/acc/AUC over epochs.
- `model/bilstm_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`; split info, class balance and early stopping in `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
