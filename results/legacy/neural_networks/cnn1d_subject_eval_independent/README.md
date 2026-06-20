# cnn1d_subject_eval_independent — 1D-CNN · subject-independent

**Status:** archived — superseded by `results/neural_networks/cnn1d_subject_eval_independent_baseline`.

> 1D-CNN on chronological per-syllable sequences, evaluated **leak-free** (split grouped by mouse) — collapses to a near-random, below-majority-baseline operating point.

## Overview
- **Model:** 1D-CNN (~86K params; convolutions over an ordered per-syllable sequence, MAX_SEQ_LEN=256).
  Unlike the tabular base (48 aggregated per-recording features), the input is a chronological syllable
  sequence and the model is scored at **session level**.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--group-split`), so no
  mouse appears in two sets. Honest "generalize to unseen mice" setting (harder than the dependent base
  model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** legacy external cache (`segmentation_classification_all_data.csv`), 442 sessions from
  119 mice (WT=336, HT=106). Train 247 / Val 91 / Test 104 sessions. Test = 24 held-out mice
  (WT 72% / HT 28%) — this run predates the Issue-#46 baseline filters and the HET→WT correction.
- **What was adapted vs the base model:** two levers change together — model family (1D-CNN instead of
  XGBoost) **and** evaluation moves from subject-dependent (recordings) to subject-independent (sessions).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.789 | 0.318 | — |
| Recall | 0.400 | 0.724 | — |
| F1 | 0.531 | 0.442 | weighted **0.506** |
| Accuracy | | | **0.490** (train 0.623) |

AUC 0.550 (test) vs 0.908 (train); best val AUC 0.575; early stopping at epoch 29/50.
Confusion matrix (rows = true, cols = pred; class 0 = HT support 29, class 1 = WT support 75):
`[[HT→0 21, HT→1 8], [WT→0 45, WT→1 30]]` — 66 of 104 sessions are pushed onto the minority label.
(`logs/out.txt` and the plot headers label "HT (0)/WT (1)"; the supports (HT 29 / WT 75) and the data
stats — WT majority — confirm class 0 = HT, class 1 = WT.)

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.490 | 0.733 | −0.243 |
| Weighted F1 | 0.506 | 0.749 | −0.243 |
| WT F1 | 0.531 | 0.785 | −0.254 |
| HT F1 | 0.442 | 0.649 | −0.207 |
| HT recall | 0.724 | 0.940 | −0.216 |
| HT precision | 0.318 | 0.496 | −0.178 |

*Directional comparison only: this NN is scored on ~104 session-level sequences, while the tabular base
is scored on ~2,465 recording-level rows — not a like-for-like split.*

## Key insights
- **Below the majority-class baseline.** Test accuracy 0.490 is *worse* than always-guessing-WT (0.72 on
  this test mix), and test AUC 0.550 is barely above chance while train AUC is 0.908 — severe
  overfitting that does not transfer to unseen mice.
- **Collapse toward the minority label.** The model predicts class 0 (HT) for 66 of 104 sessions, so
  WT recall craters to 0.400 (45 of 75 WT sessions misclassified) and HT recall (0.724) is bought only
  by spraying HT predictions — HT precision is just 0.318.
- **Sequence model adds nothing here.** Every headline metric is 0.18–0.25 below the tabular base; the
  1D-CNN does not learn a usable WT/HT boundary from ordered syllables on this leak-free split.

## Recommendations
- Do not use this run for any performance estimate — it is below the trivial baseline. Prefer the
  current baseline NN and tabular subject-independent runs under `results/`.
- For the small independent split, the collapse points at the standard NN fixes (config D balanced
  minibatch sampler, config F regsmall regularization); this control run did neither.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png`, `plots/training_curves.png` — ROC and loss/accuracy/AUC curves.
- `model/cnn1d_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- `results.json` — metrics, config, split sizes. `logs/out.txt` — flags, split info, class balance, epoch log.
- Metrics source: `results.json` + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
