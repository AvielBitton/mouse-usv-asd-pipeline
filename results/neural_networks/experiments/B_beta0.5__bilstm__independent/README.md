# B_beta0.5__bilstm__independent — BiLSTM · subject-independent · experiment B (pos_weight_beta=0.5)

> BiLSTM on baseline sequences, evaluated **leak-free** (split by mouse), with milder class weighting (β=0.5) — and it slides toward predicting WT for almost everyone.

## Overview
- **Model:** BiLSTM (2 layers, hidden 64, dropout 0.3; 148,953 params). Input is the chronological
  per-syllable sequence (order preserved, `max_seq_len=256`), scored at **session level** — not the 48
  aggregated per-recording features the tabular base uses.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent` /
  group-aware), so no mouse appears in two sets. This is the honest "generalize to unseen mice" setting
  (harder than the dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions / 106
  mice. Train 238 (63 mice, HT 24%) · Val 80 (21 mice, HT 28%) · Test 90 sessions (22 mice, HT 21%).
- **What was adapted vs base (experiment B):** `pos_weight_beta=0.5` — a **milder** positive-class
  weight (effective `pos_weight=1.803` instead of the full ~3.25 inverse-frequency) on top of plain BCE;
  no sampler, no focal, no weight decay. Trained 24 epochs (early-stopped on val AUC 0.800).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.807 | 0.429 | — |
| Recall | 0.944 | 0.158 | — |
| F1 | 0.870 | 0.231 | weighted **0.735** |
| Accuracy | | | **0.778** (train 0.790) |

Test AUC-ROC 0.623 · PR-AUC 0.305 · balanced acc 0.551 · MCC 0.155 · macro-F1 0.550.
Confusion matrix (rows = true, cols = pred): `[[WT→WT 67, WT→HT 4], [HT→WT 16, HT→HT 3]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.778 | 0.733 | +0.045 |
| Weighted F1 | 0.735 | 0.749 | −0.014 |
| WT F1 | 0.870 | 0.785 | +0.085 |
| HT F1 | 0.231 | 0.649 | −0.418 |
| HT recall | 0.158 | 0.940 | −0.782 |
| HT precision | 0.429 | 0.496 | −0.067 |

*Directional only: this NN is scored on ~90 session-level sequences, whereas the tabular base is scored on ~2,465 recording-level rows — not a like-for-like comparison.*

## Key insights
- **Near-WT collapse.** HT recall drops to **0.158** (HT F1 0.231) — the model catches only 3 of 19
  ASD-model sessions and defaults to WT for the rest. The headline accuracy 0.778 is almost entirely the
  79% WT majority being predicted correctly; balanced accuracy 0.551 and MCC 0.155 expose how little real
  signal there is.
- **β=0.5 is too weak to fix the imbalance.** Halving the positive weight (effective 1.803) was not
  enough to keep the minority class alive on this tiny independent split; the conservative cut here is the
  opposite failure mode from the "predict HT for everyone" collapse.
- **Train↔test gap is modest** (train 0.790 vs test 0.778), so this is not classic overfitting — the
  model simply learned a majority-leaning decision rule. Val AUC peaked at 0.800 but **test AUC is only
  0.623**, a large val→test drop that signals the 22-mouse test set is hard and the operating point did
  not transfer.

## Recommendations
- Prefer stronger imbalance handling for this split: the balanced minibatch sampler (experiment D) is the
  most reliable fix for collapse; β=0 (C) or focal loss (E) are alternatives. β=0.5 alone is insufficient.
- Do not use this run for any "new-mouse" HT-detection estimate — at the default 0.5 cut it misses ~84%
  of ASD-model sessions.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.623). `plots/training_curves.png` — loss/acc/AUC over 24 epochs.
- `model/bilstm_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`; split info, class balance and early-stopping in `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
