# B_beta0.5__transformer__dependent — Transformer · subject-dependent · experiment B (beta0.5)

> Transformer on the baseline sequence data, milder class weighting (`pos_weight_beta=0.5`) — **collapses to predicting WT for everyone**.

## Overview
- **Model:** Transformer (~73K params; chronological per-syllable sequence input, order preserved,
  scored at session level — not the tabular 48 aggregated per-recording features).
- **Evaluation split:** subject-dependent — random **session-level** split, so the same mouse can land
  in train and test (the log warns `train/test: 61 shared mice`). This is the leaky, optimistic setting,
  matching the base model.
- **Dataset:** baseline sequence cache (Issue #46 filters; April-2026 HET→WT correction).
  408 sessions / 106 mice → train 244 / val 82 / test 82; test is WT 77% / HT 23% (63 WT, 19 HT).
- **What was adapted vs the base model:** experiment **B** — milder class weighting
  (`pos_weight_beta=0.5`, giving `pos_weight=1.791`; sampler none, BCE loss). The lever is meant to
  push the minority HT class up without the over-aggressive weighting that flips a model to all-HT.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.768 | 0.000 | — |
| Recall | 1.000 | 0.000 | — |
| F1 | 0.869 | 0.000 | weighted **0.668** |
| Accuracy | | | **0.768** (train 0.787) |

AUC 0.682 · PR-AUC 0.350 · balanced accuracy **0.500** · MCC **0.000** · macro F1 0.434.
Early stopping at epoch 30 (best val AUC 0.724).

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.768 | 0.733 | +0.035 |
| Weighted F1 | 0.668 | 0.749 | −0.081 |
| WT F1 | 0.869 | 0.785 | +0.084 |
| HT F1 | 0.000 | 0.649 | −0.649 |
| HT recall | 0.000 | 0.940 | −0.940 |
| HT precision | 0.000 | 0.496 | −0.496 |

*Comparison is directional, not like-for-like: this NN is scored on 82 session-level sequences, while the
tabular base is scored on ~2,465 recording-level rows.*

## Key insights
- **Degenerate collapse — predicts WT for everyone.** HT recall 0.0, HT precision 0.0, HT F1 0.0; WT
  recall is 1.0. Balanced accuracy is exactly 0.500 and MCC is 0.000 — the model has learned nothing
  beyond the majority class.
- The headline "+0.035 accuracy vs base" is a **mirage**: it is simply the WT base rate (0.768 ≈ test WT
  share 77%). Every minority-class metric is zero, so this run is useless for ASD-model detection.
- AUC 0.682 / best val AUC 0.724 show the ranking signal is weak but non-random — the scores carry *some*
  separation, yet the default 0.5 threshold never crosses for any HT session, so the decisions all fall
  to WT.
- Milder weighting (`beta=0.5`) was **not enough** to escape collapse on this tiny dependent split (244
  train sessions); training loss kept dropping (0.79 → 0.53) while val AUC plateaued ~0.70, i.e. it
  overfit the majority instead of learning HT.

## Recommendations
- Do not use this run. For the collapse, prefer the **D balanced-minibatch sampler** variant (the most
  reliable fix per the experiment brief); the AUC≈0.68 here suggests the signal exists and a better
  operating point / sampler could recover non-zero HT recall.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.682). `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/transformer_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- `results.json` — full metrics, config, split sizes. `logs/out.txt` — flags, split info, per-epoch log, early stopping.
- Metrics source: `results.json` + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
