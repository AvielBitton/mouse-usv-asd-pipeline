# transformer_subject_eval_dependent — Transformer · subject-dependent

**Status:** archived — superseded by `results/neural_networks/transformer_subject_eval_dependent_baseline`.

> Sequence Transformer on per-syllable USV sequences, scored at session level; collapses toward predicting HT for almost everyone.

## Overview
- **Model:** Transformer (~72.5K params) over chronological per-syllable sequences (`MAX_SEQ_LEN=256`),
  unlike the tabular base's 48 aggregated per-recording features. Scored at the session level.
- **Evaluation split:** subject-dependent — random session-level split (`group_split=false`), so mice
  leak across sets (the log warns: 61 shared mice train/test, 57 train/val). Optimistic by construction.
- **Dataset:** legacy external CSV cache (`segmentation_classification_all_data.csv`) — 442 sessions
  from 119 mice (WT 336 / HT 106 ≈ 24% positive); pre-dates the official Issue-#46 baseline filters.
- **Run:** train 264 / val 89 / test 89 sessions (each ~76% WT / 24% HT). Trained with `pos_weight=0.320`,
  early-stopped at epoch 23/50 (best val AUC 0.695).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.889 | 0.268 | — |
| Recall | 0.235 | 0.905 | — |
| F1 | 0.372 | 0.413 | weighted **0.382** |
| Accuracy | | | **0.393** (train 0.405) · test AUC 0.754 |

Support: WT 68, HT 21 (89 test sessions). Note `results.json` labels its class keys `0.0`/`1.0` swapped
relative to the support counts; figures above follow the support-correct WT=68 / HT=21 mapping.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.393 | 0.733 | −0.340 |
| Weighted F1 | 0.382 | 0.749 | −0.367 |
| WT F1 | 0.372 | 0.785 | −0.413 |
| HT F1 | 0.413 | 0.649 | −0.236 |
| HT recall | 0.905 | 0.940 | −0.035 |
| HT precision | 0.268 | 0.496 | −0.228 |

NN are scored on session-level sequence data (89 test sessions here) vs the tabular base's recording-level
data (~2,465 rows), so this comparison is directional, not like-for-like.

## Key insights
- **Degenerate collapse.** The model predicts HT for almost everyone: HT recall 0.905 with WT recall only
  0.235. It calls most sessions positive, so accuracy (0.393) falls *below* a majority-class baseline.
- **AUC vs accuracy mismatch.** Test AUC 0.754 says the ranking carries real signal, but the chosen
  operating point is badly miscalibrated — the decision threshold sits where nearly all sessions tip to HT.
- **No fit, not just bad calibration.** Train accuracy 0.405 ≈ test 0.393; the model never learned the
  WT class even on the (leaky) training data. `pos_weight=0.320` plus the tiny 264-session train set drove
  the collapse rather than overfitting.
- Despite subject-dependent leakage (61 shared train/test mice), which usually inflates scores, this run
  lands far under the tabular base — the failure is the model, not the split.

## Recommendations
- Treat this as a known-bad headline NN run. Use the current `transformer_subject_eval_dependent_baseline`
  on the official Issue-#46 data, and prefer the balanced-minibatch-sampler (D) configs that fix collapse.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — ROC (AUC 0.754). `plots/training_curves.png` — loss/acc/AUC across 23 epochs.
- `model/transformer_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`; split/training detail in `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
