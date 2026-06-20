# cnn1d_subject_eval_independent_baseline — 1D-CNN · subject-independent

> 1D-CNN over per-syllable sequences on the official baseline data, evaluated **leak-free** (split grouped by mouse).

## Overview
- **Model:** 1D-CNN (~86K params; control/default config, no class-weighting lever beyond the built-in
  `pos_weight=3.250`). Input is a **chronological per-syllable sequence** (order preserved, `MAX_SEQ_LEN=256`),
  not the 48 aggregated per-recording features the tabular base uses; scoring is at **session level**.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`), so no
  mouse appears in two sets. This is the honest "generalize to unseen mice" setting (harder than the
  dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions / 106 mice.
  Test = **90 held-out sessions** from 22 mice (WT 79% / HT 21%). Train 238 sessions (63 mice), val 80 (21 mice).
- **What was adapted vs the base model:** two levers change together — model family (sequence 1D-CNN instead
  of XGBoost) **and** evaluation moves from subject-dependent to subject-independent.
- **Training:** early-stopped at epoch 17/100 on val AUC (best val AUC 0.753).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.797 | 0.231 | — |
| Recall | 0.718 | 0.316 | — |
| F1 | 0.756 | 0.267 | weighted **0.652** |
| Accuracy | | | **0.633** (train 0.731) |
| AUC | | | test **0.609** (best val 0.753) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 51, WT→HT 20], [HT→WT 13, HT→HT 6]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.633 | 0.733 | −0.100 |
| Weighted F1 | 0.652 | 0.749 | −0.097 |
| WT F1 | 0.756 | 0.785 | −0.029 |
| HT F1 | 0.267 | 0.649 | −0.382 |
| HT recall | 0.316 | 0.940 | −0.624 |
| HT precision | 0.231 | 0.496 | −0.265 |

*Comparison is directional, not like-for-like: this NN is scored on **90 session-level sequences**, whereas
the tabular base is scored on ~2,465 recording-level rows.*

## Key insights
- **No degenerate collapse, but the minority class fails anyway.** The model predicts both classes (it is
  not stuck on one label), yet HT performance collapses on its own merits: **HT recall 0.316, HT precision
  0.231, HT F1 0.267** — it catches only 6 of 19 ASD-model sessions and is wrong on most HT calls.
- **Class separation is near chance.** Test AUC is **0.609** (vs best val AUC 0.753), so the held-out mice
  are barely separable; the model defaults toward the WT majority (79% of test), which props up overall
  accuracy 0.633 while the positive class carries the loss.
- **Big honest drop vs the dependent base.** HT recall falls −0.624 and HT F1 −0.382 — far beyond the usual
  10–15 pt dependent→independent penalty. The session-level sequence view plus the tiny leak-free split
  (only 19 HT test sessions, 56 HT train sessions) gives the CNN very little positive signal to learn from.
- **Mild train/test gap, large val/test gap.** Train 0.731 vs test 0.633 is modest, but best val AUC 0.753
  vs test AUC 0.609 shows the val mice were not representative of the test mice — small-N variance dominates.

## Recommendations
- This control config does not give a usable HT operating point. Compare the class-imbalance levers —
  especially **D (balanced minibatch sampler)** and **E (focal loss)** — which are the more reliable fixes
  for minority underperformance on the tiny independent split.
- Treat the headline number as a **floor** for sequence models on leak-free data, not a deployable classifier;
  HT precision 0.231 means positive calls are unreliable.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.609). `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/cnn1d_best.pt` — best checkpoint (val-AUC selected). `model/scaler.pkl` — feature scaler.
- `results.json` — full metrics/config. `logs/out.txt` — flags, split info, class balance, early stopping.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
