# transformer_subject_eval_independent — Transformer · subject-independent

**Status:** archived — superseded by `results/neural_networks/transformer_subject_eval_independent_baseline`.

> Sequence Transformer evaluated **leak-free** (split grouped by mouse) — degenerates into
> over-predicting the minority (HT) class and barely beats chance.

## Overview
- **Model:** Transformer (~73K params) over the **chronological per-syllable sequence** for each
  session (order preserved, `MAX_SEQ_LEN=256`), not the 48 aggregated per-recording tabular features.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--group-split`), so no
  mouse appears in two sets. This is the honest "generalize to unseen mice" setting (harder than the
  dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** legacy NN cache (`segmentation_classification_all_data.csv`), **442 sessions from
  119 mice**, WT=336 / HT=106. Scored at **session level**: 247 train / 91 val / **104 test** sessions
  (test = 24 mice, WT 75 / HT 29). This pre-dates the official Issue-#46 baseline filters and the
  April-2026 HET→WT correction.
- **What was adapted vs the base model:** three levers change together — model family (Transformer
  instead of XGBoost), input granularity (per-syllable sequence vs aggregated features), **and**
  evaluation moves from subject-dependent to subject-independent.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.841 | 0.367 | — |
| Recall | 0.493 | 0.759 | — |
| F1 | 0.622 | 0.494 | weighted **0.586** |
| Accuracy | | | **0.567** (train 0.567) |

Test AUC 0.653 · best val AUC 0.619 · 19 epochs (early-stopped). Support: WT 75 / HT 29 sessions.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.567 | 0.733 | −0.166 |
| Weighted F1 | 0.586 | 0.749 | −0.163 |
| WT F1 | 0.622 | 0.785 | −0.163 |
| HT F1 | 0.494 | 0.649 | −0.155 |
| HT recall | 0.759 | 0.940 | −0.181 |
| HT precision | 0.367 | 0.496 | −0.129 |

*Directional only: this NN is scored on session-level sequence data (~104 test sessions) while the
tabular base is scored on recording-level rows (~2,465), so the comparison is not like-for-like.*

## Key insights
- **Degenerate bias toward the minority class.** The model over-predicts HT, not WT: WT recall is only
  0.493 while HT recall is 0.759 with HT precision just 0.367 — it tags ~3 in 4 minority pups but is wrong
  on ~2 of every 3 HT calls (it predicts HT ~60 times vs WT ~44, even though WT is the majority). Overall
  accuracy 0.567 is **below** the 0.72 WT base rate — a trivial "always-WT" classifier would beat it.
- **No real learning.** Train accuracy 0.567 ≈ test accuracy 0.567 and val AUC peaked at 0.619 by
  epoch 4, then drifted down until early stopping at epoch 19. Test AUC 0.653 indicates only weak
  ranking signal; the Transformer never fit the training sessions either.
- **Worse than the tabular base on every axis** (accuracy/F1/recall/precision all down ~0.13–0.18),
  consistent with the small leak-free split (only 247 train / 104 test sessions, 71 train mice) being
  too little data for a sequence Transformer.

## Recommendations
- Prefer the balanced-minibatch-sampler config (`D`) and the regularized small net (`F`) for this tiny
  independent split; control runs like this collapse. For an honest unseen-mouse estimate, use the
  current `results/neural_networks/` baseline runs rather than this superseded cache.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.653). `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/transformer_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
