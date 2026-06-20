# D_sampler__cnn1d__independent — 1D-CNN · subject-independent · D balanced sampler

> 1D-CNN on per-syllable sequences, leak-free split by mouse, with a balanced minibatch sampler to fight collapse.

## Overview
- **Model:** 1D-CNN over the chronological per-syllable sequence (order preserved), 86,041 params.
  Input is the raw syllable stream (`max_seq_len` 256), not the 48 aggregated per-recording features the
  tabular base uses; scoring is at **session** level.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent` /
  `--group-split`), so no mouse appears in two sets. Honest "generalize to unseen mice" setting (harder
  than the dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice → train 238 / val 80 / test 90 sessions. Test = 22 held-out mice (WT 79% / HT 21%).
- **What was adapted vs the base model (lever D):** model family swaps to a 1D-CNN on sequences, the
  evaluation moves dependent → independent, **and** a balanced minibatch sampler replaces class
  weighting (`pos_weight_beta=0.0`, `sampler=balanced`, `loss=bce`) — the most reliable fix for the
  degenerate collapse the NN runs hit on this tiny split.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.800 | 0.267 | — |
| Recall | 0.845 | 0.211 | — |
| F1 | 0.822 | 0.235 | weighted **0.698** |
| Accuracy | | | **0.711** (train 0.761) |

Test AUC 0.557 · balanced accuracy 0.528 · MCC 0.061 · PR-AUC 0.359. Best val AUC 0.770; early stopped
at epoch 17/100.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.711 | 0.733 | −0.022 |
| Weighted F1 | 0.698 | 0.749 | −0.051 |
| WT F1 | 0.822 | 0.785 | +0.037 |
| HT F1 | 0.235 | 0.649 | −0.414 |
| HT recall | 0.211 | 0.940 | −0.729 |
| HT precision | 0.267 | 0.496 | −0.229 |

*Directional only: this NN is scored on ~90 session-level sequences, while the tabular base is scored on
~2,465 recording-level rows — not a like-for-like comparison.*

## Key insights
- The balanced sampler **avoids the all-HT collapse** seen elsewhere, but trades into the opposite
  failure: the model leans toward WT (WT recall 0.845) and the minority class falls apart —
  **HT recall 0.211, HT F1 0.235**, catching ~1 in 5 ASD-model sessions. HT precision 0.267 means most
  of the few HT calls are also wrong.
- Discrimination is near chance on the held-out mice: **test AUC 0.557, balanced accuracy 0.528,
  MCC 0.061** — the 0.711 accuracy is essentially the WT base rate (79%), not real signal.
- The big val→test gap (best val AUC 0.770 vs test AUC 0.557) on only 22 test mice shows severe
  overfitting to the validation fold; the model does not generalize to unseen subjects.
- WT F1 beats the base (+0.037) only because the run defaults to predicting the majority; that is not a
  win — every minority-class metric collapses (HT F1 −0.414, HT recall −0.729).

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — ROC (test AUC 0.557). `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/cnn1d_best.pt` — best checkpoint (epoch with val AUC 0.770). `model/scaler.pkl` — feature scaler.
- `logs/out.txt` — flags, split info, class balance, per-epoch log, early stopping.
- Metrics source: `results.json` + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
