# bilstm_subject_eval_independent — BiLSTM · subject-independent

**Status:** archived — superseded by `results/neural_networks/bilstm_subject_eval_independent_baseline`.

> BiLSTM on chronological per-syllable sequences, evaluated **leak-free** (split grouped by mouse) — but the model collapsed to predicting WT for nearly everyone.

## Overview
- **Model:** BiLSTM (~149K params), trained on per-syllable sequences with order preserved (input is a
  chronological sequence per session, not the 48 aggregated tabular features). `pos_weight=0.286`.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--group-split`), so no
  mouse appears in two sets. This is the honest "generalize to unseen mice" setting (harder than the
  dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** 442 sessions from 119 mice (WT 336 / HT 106); `MAX_SEQ_LEN=256` (sequence lengths
  min 1 / median 236 / max 1202). Scored at **session level**: 247 train / 91 val / 104 test sessions
  (test = 24 held-out mice, WT 72% / HT 28%).
- **Training:** early stopping at epoch 17/50 (best val AUC 0.659); train accuracy 0.785.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.728 | 1.000 | — |
| Recall | 1.000 | 0.034 | — |
| F1 | 0.843 | 0.067 | weighted **0.626** |
| Accuracy | | | **0.731** (train 0.785) |

Test AUC-ROC 0.796. WT support 75 sessions, HT support 29 — note the test split is WT-majority at the
session level, so "predict WT" alone scores 0.72 accuracy.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.731 | 0.733 | −0.002 |
| Weighted F1 | 0.626 | 0.749 | −0.123 |
| WT F1 | 0.843 | 0.785 | +0.058 |
| HT F1 | 0.067 | 0.649 | −0.582 |
| HT recall | 0.034 | 0.940 | −0.906 |
| HT precision | 1.000 | 0.496 | +0.504 |

*Comparison is directional, not like-for-like: this NN is scored on ~104 session-level sequences,
whereas the tabular base model is scored on ~2,465 recording-level rows.*

## Key insights
- **Degenerate collapse:** the model predicts WT for almost everyone — WT recall 1.000, HT recall 0.034
  (1 of 29 HT sessions correct), HT F1 0.067. The headline 0.731 accuracy is an artifact of the
  WT-majority test split, not real class separation.
- **Validation never improved:** best val AUC peaked at 0.659 in epoch 2 and decayed thereafter while
  train loss kept falling — overfitting/collapse rather than learning a useful WT vs HT boundary.
- The "good-looking" deltas (WT F1 +0.058, HT precision +0.504) are entirely a side effect of the
  collapse: by labelling nearly all sessions WT on a WT-heavy test set, WT metrics inflate while HT
  detection is destroyed (HT recall −0.906, HT F1 −0.582). Macro F1 is only 0.455.
- Test AUC 0.796 vs best val AUC 0.659 — the ranking signal is weak and unstable; the chosen 0.5
  decision threshold lands almost entirely on one class.

## Recommendations
- Do not use this run; it is a collapsed baseline. The balanced-minibatch sampler config (`D`) is the
  most reliable fix for this failure mode; see the current
  `results/neural_networks/bilstm_subject_eval_independent_baseline`.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC. `plots/training_curves.png` — loss/accuracy/AUC per epoch.
- `model/bilstm_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
