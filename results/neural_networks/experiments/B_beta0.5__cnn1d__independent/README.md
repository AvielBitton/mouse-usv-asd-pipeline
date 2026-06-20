# B_beta0.5__cnn1d__independent — 1D-CNN · subject-independent · experiment B (beta0.5)

> 1D-CNN over per-syllable sequences, evaluated **leak-free** (split by mouse), with milder class weighting (`pos_weight_beta=0.5`).

## Overview
- **Model:** 1D-CNN (~86K params; convolutions over a chronological per-syllable sequence, order
  preserved — unlike the tabular base, which uses 48 aggregated per-recording features).
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`,
  group-aware), so no mouse appears in two sets. This is the honest "generalize to unseen mice" setting
  (harder than the dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice; test = **90 held-out sessions** from 22 mice (WT 79% / HT 21%).
- **What was adapted vs the base model:** experiment **B — `pos_weight_beta=0.5`** (milder class
  weighting; effective `pos_weight=1.803` instead of the full inverse-frequency value). Two other levers
  move together: model family (1D-CNN instead of XGBoost) **and** dependent → subject-independent
  evaluation. No sampler, plain BCE, dropout 0.3, lr 1e-3; early-stopped at epoch 22 (best val AUC 0.748).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.800 | 0.240 | — |
| Recall | 0.732 | 0.316 | — |
| F1 | 0.765 | 0.273 | weighted **0.661** |
| Accuracy | | | **0.644** (train 0.790) |

AUC 0.532 · balanced accuracy 0.524 · MCC 0.044 · PR-AUC 0.366.
Confusion matrix (rows = true, cols = pred): `[[WT→WT 52, WT→HT 19], [HT→WT 13, HT→HT 6]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.644 | 0.733 | −0.089 |
| Weighted F1 | 0.661 | 0.749 | −0.088 |
| WT F1 | 0.765 | 0.785 | −0.020 |
| HT F1 | 0.273 | 0.649 | −0.376 |
| HT recall | 0.316 | 0.940 | −0.624 |
| HT precision | 0.240 | 0.496 | −0.256 |

*Comparison is directional, not like-for-like: this NN is scored on **session-level sequences** (90 test
sessions) while the tabular base is scored on **recording-level rows** (~2,465 rows).*

## Key insights
- **Test AUC 0.532 / MCC 0.044** — the model is barely above chance at separating the classes on unseen
  mice. The best-val AUC (0.748) does not transfer to test, a clear generalization gap on the tiny
  independent split (238 train sessions, 63 mice).
- The minority class collapses on every metric: **HT recall 0.316, HT precision 0.240, HT F1 0.273**.
  Only 6 of 19 HT sessions are caught, and most HT calls are wrong — the milder `beta=0.5` weighting did
  not produce a usable positive operating point.
- This is the opposite tilt from the usual "predict-HT-for-everyone" collapse: here the model defaults
  toward WT (WT recall 0.732, HT recall 0.316), so the headline accuracy (0.644) is mostly the majority
  class and the balanced accuracy (0.524) exposes it.
- Train 0.790 vs test 0.644 plus val AUC drifting down from epoch 7 (0.748) onward signal overfitting on
  the small leak-free split well before early stopping fired at epoch 22.

## Recommendations
- This config is not deployable — HT detection (recall 0.316, precision 0.240) is too weak. The brief's
  most reliable collapse fix is the **balanced sampler (config D)**; also compare `regsmall` (F) for the
  tiny independent split before tuning the threshold.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — ROC (test AUC 0.532). `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/cnn1d_best.pt` — best checkpoint (val AUC 0.748). `model/scaler.pkl` — feature scaler.
- `results.json` — full metrics + config. `logs/out.txt` — flags, split info, class balance, early stopping.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
