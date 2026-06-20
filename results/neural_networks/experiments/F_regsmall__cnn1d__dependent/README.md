# F_regsmall__cnn1d__dependent — 1D-CNN · subject-dependent · experiment F (regsmall)

> A regularized, shrunk 1D-CNN on the baseline sequence data, scored on the optimistic (leaky) dependent split.

## Overview
- **Model:** 1D-CNN over a chronological per-syllable sequence (order preserved; `max_seq_len=256`),
  86,041 params. Scored at **session level** (82 test sessions), not recording level.
- **Evaluation split:** subject-dependent — random session-level split (`group_split=false`), so the same
  mouse appears in train, val and test. The log confirms leakage: **61 shared mice train/test**, 56 train/val.
  This is the optimistic setting (no mouse-level isolation).
- **Dataset:** official baseline sequence cache (Issue #46 filters; April-2026 HET→WT correction).
  408 sessions / 106 mice → train 244 · val 82 · test 82; test balance HT 23% / WT 77%.
- **What was adapted vs the base model:** experiment **F regsmall** — heavy regularization for a tiny split:
  `weight_decay=0.001`, `dropout=0.5`, shrunk net (`hidden_size=32`, `num_layers=1`), with mild class
  weighting (`pos_weight_beta=0.5` → pos_weight 1.791, BCE loss). Trained on sequences instead of the
  base model's 48 aggregated tabular features.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.774 | 0.250 | — |
| Recall | 0.762 | 0.263 | — |
| F1 | 0.768 | 0.256 | weighted **0.649** |
| Accuracy | | | **0.646** (train 0.803) |

AUC 0.588 · balanced acc 0.513 · macro-F1 0.512 · MCC 0.025. Best val AUC 0.710, early-stopped at epoch 22.
Confusion matrix (rows = true, cols = pred): `[[WT→WT 48, WT→HT 15], [HT→WT 14, HT→HT 5]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.646 | 0.733 | −0.087 |
| Weighted F1 | 0.649 | 0.749 | −0.100 |
| WT F1 | 0.768 | 0.785 | −0.017 |
| HT F1 | 0.256 | 0.649 | −0.393 |
| HT recall | 0.263 | 0.940 | −0.677 |
| HT precision | 0.250 | 0.496 | −0.246 |

*Comparison is directional, not like-for-like: this NN is scored on 82 session-level sequences, while the
tabular base model is scored on ~2,465 recording-level rows.*

## Key insights
- **No collapse, but no signal either.** The regsmall recipe avoids the usual degenerate all-HT/all-WT
  failure (HT recall 0.263, WT recall 0.762, both classes predicted), yet **MCC 0.025 and AUC 0.588** show
  the model is barely above chance — predictions track class priors more than genotype.
- **The minority class is essentially missed:** HT F1 0.256 (−0.393 vs base) with precision 0.250 — 3 of
  every 4 HT calls are wrong, and only 5 of 19 true HT sessions are caught.
- **Heavy regularization did not buy generalization.** Even on the leaky dependent split, test acc 0.646
  trails train acc 0.803 (0.16 gap) and the base model's 0.733; val AUC peaked at 0.710 by epoch 7 then
  decayed, suggesting the tiny 244-session sequence set offers little for the CNN to learn.
- Sequence-level NN on this dependent split underperforms the aggregated-feature tabular base across every
  metric, most severely on minority-class recovery.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.588). `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/cnn1d_best.pt` — best checkpoint (val AUC). `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
