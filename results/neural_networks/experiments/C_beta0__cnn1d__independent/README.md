# C_beta0__cnn1d__independent — 1D-CNN · subject-independent · experiment C (beta0, no class weighting)

> 1D-CNN on per-syllable sequences, evaluated **leak-free** (split by mouse), with class weighting switched off.

## Overview
- **Model:** 1D-CNN (86,041 params) over a chronological per-syllable sequence (`max_seq_len=256`),
  not the 48 aggregated per-recording features the tabular base uses. Scored at **session level**.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent` /
  group-aware), so no mouse appears in two sets. Honest "generalize to unseen mice" setting, harder than
  the dependent base model (which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions / 106
  mice → train 238 / val 80 / test 90 sessions. Test = 22 held-out mice (WT 79% / HT 21%).
- **What was adapted vs the base model (experiment C, beta0):** `pos_weight_beta=0.0` →
  **no class weighting** (`pos_weight=1.000`, plain BCE, no sampler), on top of the model-family +
  dependent→independent change. Trained 25 epochs, early-stopped on val AUC (best 0.752).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.809 | 0.273 | — |
| Recall | 0.775 | 0.316 | — |
| F1 | 0.791 | 0.293 | weighted **0.686** |
| Accuracy | | | **0.678** (train 0.836) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 55, WT→HT 16], [HT→WT 13, HT→HT 6]]` (90 sessions).
Test AUC 0.517 · balanced acc 0.545 · MCC 0.086 · PR-AUC 0.297.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.678 | 0.733 | −0.055 |
| Weighted F1 | 0.686 | 0.749 | −0.063 |
| WT F1 | 0.791 | 0.785 | +0.006 |
| HT F1 | 0.293 | 0.649 | −0.356 |
| HT recall | 0.316 | 0.940 | −0.624 |
| HT precision | 0.273 | 0.496 | −0.223 |

*Directional only: this NN is scored on ~90 session-level sequences, whereas the tabular base is scored on ~2,465 recording-level rows — not a like-for-like comparison.*

## Key insights
- **No collapse, but the minority class barely works.** With class weighting off, the model defaults
  toward the WT majority: HT recall 0.316 and HT precision 0.273 → **HT F1 0.293** (−0.356 vs base). It
  catches only 6 of 19 HT sessions while the base flags 94% of HT.
- **No real signal at test.** Test AUC 0.517 (≈ chance), MCC 0.086, balanced acc 0.545 — the run sits
  just above coin-flip on the held-out mice despite val AUC reaching 0.752, a sharp val→test drop typical
  of the tiny independent split (238 train sessions).
- **Overfitting.** Train acc 0.836 vs test 0.678 (0.16 gap); train loss falls to ~0.19 while val loss
  rises after epoch 9 — early stopping fired at epoch 25.
- WT F1 (0.791) edges out base only because the model leans WT; this does not reflect genuine WT vs HT
  separation.

## Recommendations
- Removing class weighting hurts the minority class here. Prefer the **D (balanced sampler)** config —
  the most reliable collapse/imbalance fix in this sweep — over beta0 for the independent split.
- Given near-chance test AUC on 90 sessions, treat this CNN as not viable for new-mouse HT detection;
  the tabular independent runs remain the better honest estimate.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC. `plots/training_curves.png` — train/val loss, acc, AUC over epochs.
- `model/cnn1d_best.pt` — best checkpoint (by val AUC). `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`; `logs/out.txt` — flags, split/class balance, per-epoch log, early stopping.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
