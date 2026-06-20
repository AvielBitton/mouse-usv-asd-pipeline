# B_beta0.5__cnn1d__dependent — 1D-CNN · subject-dependent · experiment B (beta0.5)

> 1D-CNN over chronological per-syllable sequences, scored at session level; milder class weighting (`pos_weight_beta=0.5`).

## Overview
- **Model:** 1D-CNN (~86K params) over a chronological per-syllable sequence (`max_seq_len=256`,
  order preserved), not the 48 aggregated per-recording features the tabular base uses.
- **Evaluation split:** subject-dependent — random **session-level** split, so the same mouse leaks
  across sets (log: train/test share 61 mice, train/val 56). Optimistic by construction.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice (HT 97 / WT 311). Scored at **session level**: train 244 / val 82 / test 82 sessions
  (test HT 23% / WT 77%).
- **What was adapted vs the base model:** experiment **B** — milder class weighting
  (`pos_weight_beta=0.5` → `pos_weight=1.791`), default BCE loss, no sampler, dropout 0.3. Two levers
  move together vs base: model family (1D-CNN instead of XGBoost) and sequence vs aggregated input.
  Early-stopped at epoch 22 (best val AUC 0.719).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.774 | 0.250 | — |
| Recall | 0.762 | 0.263 | — |
| F1 | 0.768 | 0.256 | weighted **0.649** |
| Accuracy | | | **0.646** (train 0.828) |

Test AUC 0.583 · balanced acc 0.513 · macro-F1 0.512 · MCC 0.025 · PR-AUC 0.340 (82 test sessions).

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.646 | 0.733 | −0.087 |
| Weighted F1 | 0.649 | 0.749 | −0.100 |
| WT F1 | 0.768 | 0.785 | −0.017 |
| HT F1 | 0.256 | 0.649 | −0.393 |
| HT recall | 0.263 | 0.940 | −0.677 |
| HT precision | 0.250 | 0.496 | −0.246 |

*Directional only: this NN is scored on 82 session-level sequences, while the tabular base is scored on
~2,465 recording-level rows — not a like-for-like comparison.*

## Key insights
- The 1D-CNN is **worse than the base model on every axis** and barely above chance: AUC 0.583, MCC
  0.025, balanced acc 0.513 — it has almost no real WT/HT separation despite the leaky dependent split.
- The minority class essentially fails: **HT precision 0.250 / recall 0.263 / F1 0.256** (5 of 19 HT
  sessions caught). This is not degenerate collapse — milder weighting (beta 0.5) keeps it from
  predicting one class for everyone — but the model lands close to random on HT.
- Train 0.828 vs test 0.646 with val AUC drifting down after epoch 7 (peak 0.719) signals overfitting,
  not capacity: the network memorizes train sessions but the val/test signal stays flat near chance.
- The accuracy (0.646) is mostly carried by the 77% WT majority; weighted F1 (0.649) confirms the
  headline number is a majority-class artifact, not genuine skill.

## Recommendations
- Prefer the balanced-sampler config (experiment **D**), the most reliable fix for the weak/collapsing
  minority class on this data; beta-only weighting (this run) does not give the CNN usable HT signal.
- Do not read these numbers as generalization — the split is subject-dependent (mice leak). Use a
  subject-independent run for any honest "new-mouse" estimate.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png`, `plots/training_curves.png` — test ROC and train/val loss-acc-AUC curves.
- `model/cnn1d_best.pt` — best checkpoint (epoch 22). `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
