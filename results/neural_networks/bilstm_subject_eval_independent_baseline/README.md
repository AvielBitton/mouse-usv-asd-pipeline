# bilstm_subject_eval_independent_baseline — BiLSTM · subject-independent

> BiLSTM (~149K params) on the official baseline data, evaluated **leak-free** (split grouped by mouse) — **collapses to predicting HT for almost everyone**.

## Overview
- **Model:** BiLSTM (~149K params) over a chronological per-syllable sequence (syllable order preserved),
  unlike the tabular base model's 48 aggregated per-recording features. Scored at **session level**.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`), so no
  mouse appears in two sets. This is the honest "generalize to unseen mice" setting (harder than the
  dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice (HT 97 / WT 311). Test = 90 sessions from 22 held-out mice (WT 79% / HT 21%).
- **Training:** `pos_weight=3.250` class weighting; 16/100 epochs (early-stopped on val AUC 0.847);
  238 train / 80 val / 90 test sessions; `MAX_SEQ_LEN=256` (median seq length 236).
- **What was adapted vs the base model:** model family (sequence BiLSTM instead of XGBoost) **and**
  evaluation moves from subject-dependent to subject-independent.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 1.000 | 0.279 | — |
| Recall | 0.310 | 1.000 | — |
| F1 | 0.473 | 0.437 | weighted **0.465** |
| Accuracy | | | **0.456** (train 0.622) |
| AUC | | | **0.749** (best val 0.847) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 22, WT→HT 49], [HT→WT 0, HT→HT 19]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.456 | 0.733 | −0.277 |
| Weighted F1 | 0.465 | 0.749 | −0.284 |
| WT F1 | 0.473 | 0.785 | −0.312 |
| HT F1 | 0.437 | 0.649 | −0.212 |
| HT recall | 1.000 | 0.940 | +0.060 |
| HT precision | 0.279 | 0.496 | −0.217 |

*Directional only, not like-for-like: this NN is scored on 90 session-level sequences, whereas the
tabular base model is scored on ~2,465 recording-level rows.*

## Key insights
- **Degenerate collapse on the minority class.** HT recall = 1.000 with WT recall = 0.310 — the model
  predicts HT for 68 of 90 test sessions (49 of 71 WT sessions misclassified as HT). Accuracy 0.456 is
  worse than a WT-majority guess (~0.79), and HT precision 0.279 ≈ the test HT base rate (21%), i.e. no
  real separation at the 0.5 cut.
- **Ranking is intact even though the operating point is broken.** Test AUC 0.749 (val AUC peaked 0.847)
  shows the model orders sessions usefully, but the decision threshold is far off — a classic
  weighting/threshold problem (`pos_weight=3.250` over-pushes toward HT), not an inability to learn.
- **The tiny independent split is the root cause.** Only 238 train / 80 val / 90 test sessions across
  63 train mice (HT 56) leaves almost no signal to calibrate the head; the loss/val curves are noisy and
  early-stop fires at epoch 16. Train accuracy 0.622 is itself low, so this is under-fit, not over-fit.

## Recommendations
- Treat the headline metrics as a **collapsed baseline**: the +0.060 HT-recall "win" is an artifact of
  predicting HT for nearly everyone, not a usable gain.
- Mitigate collapse before trusting any session-level NN number — milder/zero class weighting
  (B `beta=0.5`, C `beta0`), the balanced minibatch sampler (D, the most reliable collapse fix),
  the small-net regularized config for tiny independent splits (F `regsmall`), or post-hoc threshold
  tuning given the healthy AUC.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — ROC (test AUC 0.749). `plots/training_curves.png` — loss/acc/AUC vs epoch.
- `model/bilstm_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
