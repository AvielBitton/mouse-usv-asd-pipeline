# transformer_subject_eval_dependent_baseline — Transformer · subject-dependent

> Transformer sequence classifier on the official baseline data, evaluated subject-**dependent** (random session-level split; mice leak across train/test).

## Overview
- **Model:** Transformer (~73K params) over a chronological per-syllable sequence (syllable order
  preserved, `MAX_SEQ_LEN=256`), unlike the tabular base model's 48 aggregated per-recording features.
  Scored at **session level**, not recording level.
- **Evaluation split:** subject-dependent — random **session-level** split (`--baseline`, no
  `--independent`/`--group-split`), so the same mouse can sit in train and test (the log flags
  `mouse overlap -- train/val: 56, train/test: 61 shared mice`). This is the optimistic, leaky setting,
  same family as the dependent base model.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice (HT 97 / WT 311). Split 244 train / 82 val / 82 test sessions; test = HT 23% / WT 77%.
- **Training:** `pos_weight=3.207` class weighting, early stopping at epoch 31/100 on best val AUC 0.688.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.872 | 0.371 | — |
| Recall | 0.651 | 0.684 | — |
| F1 | 0.745 | 0.481 | weighted **0.684** |
| Accuracy | | | **0.659** (train 0.684) |

Test AUC-ROC 0.655. Support: WT 63, HT 19 (82 test sessions).

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.659 | 0.733 | −0.074 |
| Weighted F1 | 0.684 | 0.749 | −0.065 |
| WT F1 | 0.745 | 0.785 | −0.040 |
| HT F1 | 0.481 | 0.649 | −0.168 |
| HT recall | 0.684 | 0.940 | −0.256 |
| HT precision | 0.371 | 0.496 | −0.125 |

*Directional only, not like-for-like: this NN is scored on 82 session-level sequences, whereas the
tabular base model is scored on ~2,465 recording-level rows.*

## Key insights
- The Transformer is **worse than the dependent tabular base on every headline metric**, despite the
  same leaky split that should flatter it: accuracy −0.074, weighted F1 −0.065, HT F1 −0.168. The
  per-syllable sequence view does not beat 48 aggregated features here.
- No degenerate collapse — both classes are predicted (HT recall 0.684, WT recall 0.651) — but the
  minority class is the weak spot: **HT precision 0.371** means roughly 2 of every 3 HT calls are false
  positives, and HT recall (0.684) is far below the base model's 0.940.
- Train 0.684 vs test 0.659 shows almost no train/test gap on accuracy, yet train AUC 0.817 vs test AUC
  0.655 reveals the model fits the train sequences better than it generalizes — even with mouse leakage.
- The fit is shallow overall: best val AUC plateaued at 0.688 by epoch 16 and never improved through
  early stopping at epoch 31; the tiny 244-session train set caps what a Transformer can learn.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.655). `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/transformer_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- `logs/out.txt` — flags, split info, class balance, per-epoch log, early stopping.
- Metrics source: `results.json` + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
