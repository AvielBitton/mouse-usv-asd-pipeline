# cnn1d_subject_eval_dependent_baseline — 1D-CNN · subject-dependent

> 1D-CNN on chronological per-syllable sequences, baseline data, evaluated on the **leaky** random session split.

## Overview
- **Model:** 1D-CNN (86,041 params) over a per-session chronological syllable sequence (order preserved,
  `MAX_SEQ_LEN=256`), not the 48 aggregated per-recording features the tabular base uses. Trained with
  class weighting (`pos_weight=3.207`), Adam + LR decay, early-stopped at epoch 22 (best val AUC 0.710).
- **Evaluation split:** subject-dependent — random **session-level** split, so the same mouse leaks across
  sets (train/test share 61 mice). This is the optimistic in-sample setting, same split family as the base.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions / 106
  mice; HT=97 / WT=311. Train 244 · Val 82 · **Test 82 sessions** (HT 23% / WT 77%).
- **What was adapted vs the base model:** model family only — 1D-CNN over sequences instead of XGBoost over
  aggregated features; the dependent split is held constant.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.824 | 0.271 | — |
| Recall | 0.444 | 0.684 | — |
| F1 | 0.577 | 0.388 | weighted **0.533** |
| Accuracy | | | **0.500** (train 0.672) |

Test AUC 0.604 (best val AUC 0.710; train AUC 0.843). Support: WT 63, HT 19.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.500 | 0.733 | −0.233 |
| Weighted F1 | 0.533 | 0.749 | −0.216 |
| WT F1 | 0.577 | 0.785 | −0.208 |
| HT F1 | 0.388 | 0.649 | −0.261 |
| HT recall | 0.684 | 0.940 | −0.256 |
| HT precision | 0.271 | 0.496 | −0.225 |

*Comparison is directional, not like-for-like: this NN is scored on 82 session-level sequences, while the
tabular base is scored on ~2,465 recording-level rows.*

## Key insights
- The run is **weak across the board** — test accuracy 0.500 with AUC only 0.604, so the model barely
  separates the classes even on the leaky in-sample split. It trails the base by 0.20–0.26 on every metric.
- This is not the classic full collapse (neither class is fully ignored: WT recall 0.444, HT recall 0.684),
  but the WT side is badly degraded — the model misses **56% of WT** sessions, dragging WT F1 to 0.577.
- Minority class is poorly resolved: **HT precision 0.271** means ~3 of every 4 HT calls are false
  positives; HT F1 0.388. Class weighting (`pos_weight=3.207`) tilts the model toward HT without buying
  real separation.
- Heavy overfitting: train AUC 0.843 vs test AUC 0.604, and val accuracy never stabilizes
  (0.44–0.72 across epochs) before early stopping at epoch 22 — symptomatic of only 244 training sessions.

## Recommendations
- The default 0.5 cut is mis-calibrated here; the sampler/regularization NN variants (D balanced sampler,
  F regsmall) are the standard fixes for this small-data instability and should be tried before trusting
  this architecture.
- Do not use this run as a performance estimate — even on the optimistic dependent split it sits at chance
  accuracy; the tabular base remains the anchor.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.604). `plots/training_curves.png` — loss/acc/AUC over 22 epochs.
- `model/cnn1d_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
