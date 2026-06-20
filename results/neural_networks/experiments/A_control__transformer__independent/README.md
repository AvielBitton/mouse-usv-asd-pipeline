# A_control__transformer__independent — Transformer · subject-independent · experiment A (control)

> Sequence Transformer (defaults, no class-imbalance lever) on baseline data, evaluated **leak-free** (split by mouse).

## Overview
- **Model:** Transformer (~73K params) over a chronological per-syllable sequence (order preserved),
  scored at the **session** level — unlike the tabular base model's 48 aggregated per-recording features.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent` /
  group-aware), so no mouse appears in two sets. This is the honest "generalize to unseen mice" setting
  (harder than the dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions / 106 mice;
  Train 238 sessions (63 mice, HT 24%), Val 80 (21 mice), Test 90 sessions from 22 held-out mice (WT 79% / HT 21%).
- **What was adapted vs the base model:** experiment **A = control** — defaults only (`pos_weight_beta=1.0`,
  `sampler=none`, `loss=bce`, dropout 0.3, d_model 64, 2 layers). This is the reference config the
  B–H levers are tuned against. Two things change at once vs base: model family (Transformer instead of
  XGBoost) **and** evaluation moves from subject-dependent to subject-independent.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.895 | 0.288 | — |
| Recall | 0.479 | 0.789 | — |
| F1 | 0.624 | 0.423 | weighted **0.581** |
| Accuracy | | | **0.544** (train 0.605) |

AUC-ROC 0.675 · PR-AUC 0.474 · balanced acc 0.634 · MCC 0.222 · macro-F1 0.523. Best val AUC 0.810 at
early stop (epoch 29/100).

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.544 | 0.733 | −0.189 |
| Weighted F1 | 0.581 | 0.749 | −0.168 |
| WT F1 | 0.624 | 0.785 | −0.161 |
| HT F1 | 0.423 | 0.649 | −0.226 |
| HT recall | 0.789 | 0.940 | −0.151 |
| HT precision | 0.288 | 0.496 | −0.208 |

*Directional only: this NN is scored on 90 session-level sequences vs the tabular base's ~2,465
recording-level rows, so the comparison is not like-for-like.*

## Key insights
- The control Transformer is **well below the base model on every metric** — test accuracy 0.544 (−0.189)
  and weighted F1 0.581 (−0.168). The leak-free split plus no imbalance lever is costly.
- **Not a degenerate collapse, but skewed minority-biased:** with the default `pos_weight≈3.25` the model
  over-predicts HT — HT recall 0.789 / WT recall only 0.479, so it misclassifies more than half of WT
  sessions. HT precision is just 0.288 (≈ 1 in 4 HT calls correct), dragging HT F1 to 0.423.
- **Train/val/test disagree sharply:** best val AUC 0.810 but test AUC only 0.675, and train accuracy 0.605.
  On 90 test sessions (19 HT) the held-out mice generalize poorly — typical of the tiny independent split.
- Useful as the **A baseline**: it shows the imbalance handling needs work (over-shoots HT), motivating the
  B–H levers (milder/no class weighting, balanced sampler, focal loss, regularization).

## Recommendations
- Compare against the imbalance-lever experiments — especially **D (balanced sampler)** and **C/B (no/milder
  class weighting)** — which target exactly this minority over-prediction; D is usually the most reliable fix.
- For the tiny independent split, also try **F (regsmall)** to reduce the val→test AUC gap (0.810 → 0.675).

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.675). `plots/training_curves.png` — loss/acc/AUC over 29 epochs.
- `model/transformer_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
