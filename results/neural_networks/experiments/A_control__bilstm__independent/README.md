# A_control__bilstm__independent — BiLSTM · subject-independent · control experiment

> BiLSTM with default settings on the baseline sequence data, evaluated **leak-free** (split by mouse) — collapses to predicting HT for almost everyone.

## Overview
- **Model:** BiLSTM (~149K params; 2 layers, hidden 64, dropout 0.3). Input is the chronological
  per-syllable sequence (order preserved, max 256 syllables/session), not the 48 aggregated tabular
  features. Scored at **session level**, not recording level.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`,
  group-aware), so no mouse appears in two sets. This is the honest "generalize to unseen mice" setting
  (harder than the dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice (HT 97 / WT 311). Test = 90 held-out sessions from 22 mice (WT 79% / HT 21%);
  train 238, val 80.
- **What was adapted vs the base model:** this is the **A control** config — defaults, no special
  levers (`pos_weight_beta=1.0` → pos_weight 3.25, sampler none, BCE loss). Plus two structural changes
  vs base: model family (BiLSTM instead of XGBoost) **and** evaluation moves dependent → independent.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 1.000 | 0.279 | — |
| Recall | 0.310 | 1.000 | — |
| F1 | 0.473 | 0.437 | weighted **0.465** |
| Accuracy | | | **0.456** (train 0.622) |

AUC-ROC 0.749 · PR-AUC 0.347 · balanced acc 0.655 · MCC 0.294 · best val AUC 0.847 · early-stopped at
epoch 16/100. Confusion matrix (rows = true, cols = pred): WT recall 0.310 on 71 WT sessions and HT
recall 1.000 on 19 HT sessions.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.456 | 0.733 | −0.277 |
| Weighted F1 | 0.465 | 0.749 | −0.284 |
| WT F1 | 0.473 | 0.785 | −0.312 |
| HT F1 | 0.437 | 0.649 | −0.212 |
| HT recall | 1.000 | 0.940 | +0.060 |
| HT precision | 0.279 | 0.496 | −0.217 |

*NN are scored on session-level sequence data (90 test sessions) vs the tabular base's recording-level
data (~2,465 rows), so the Δ is directional, not like-for-like.*

## Key insights
- **Degenerate collapse.** The model predicts HT for nearly everyone: **HT recall = 1.000** while
  **WT recall = 0.310** (precision 1.00 / recall 0.31 on WT). Accuracy (0.456) falls *below* the
  21% HT prevalence baseline because it sacrifices the 79% WT majority — the default class weighting
  (pos_weight 3.25) over-pushes toward the minority class.
- **Ranking is fine, the threshold is not.** AUC-ROC 0.749 and best val AUC 0.847 show the network
  *can* separate the classes; the failure is the 0.5 operating point, where HT precision is only 0.279
  (≈3 of every 4 HT calls are false positives). MCC 0.294 confirms weak-but-nonzero signal.
- **Tiny independent split amplifies instability.** Only 238 train / 90 test sessions across 22 test
  mice; train accuracy 0.622 vs val acc oscillating 0.56–0.79 indicates the run never settled, and
  early stopping fired at epoch 16 on val AUC, not on a stable operating point.

## Recommendations
- This control run is **not deployable** at the default threshold. Compare against the lever variants
  built to fix exactly this collapse — `D` (balanced minibatch sampler, the most reliable fix),
  `B`/`C` (milder/no class weighting), and `F` (regsmall for the tiny independent split).
- Since AUC is healthy but the 0.5 cut collapses, a tuned decision threshold (or `target_recall`) would
  recover a usable WT/HT trade-off without retraining.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — ROC (AUC 0.749). `plots/training_curves.png` — loss/acc/AUC over 16 epochs.
- `model/bilstm_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`. `logs/out.txt` — flags, split info, class balance, per-epoch log.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
