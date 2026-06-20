# F_regsmall__cnn1d__independent — 1D-CNN · subject-independent · experiment F (regsmall)

> Regularized, shrunk 1D-CNN for the tiny leak-free split — no collapse, but the minority class is barely learned.

## Overview
- **Model:** 1D-CNN over chronological per-syllable sequences (86,041 params; `max_seq_len=256`).
  Input is the order-preserved syllable stream, not the 48 aggregated per-recording tabular features;
  scoring is at **session level** (90 test sessions), not recording level.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`,
  group-aware), so no mouse appears in two sets. Honest "generalize to unseen mice" setting (harder than
  the dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions / 106
  mice → Train 238 (63 mice, HT 24%), Val 80 (21 mice, HT 28%), Test 90 (22 mice, **HT 21% / WT 79%**).
- **What was adapted vs the base model:** experiment **F = regsmall** — anti-overfit recipe sized for the
  tiny independent split: weight decay 0.001 + dropout 0.5 + a smaller net (`hidden_size=32`,
  `num_layers=1`), with mild class weighting (`pos_weight_beta=0.5` → pos_weight 1.803, BCE loss, no
  sampler). Two levers move together vs base: model family (1D-CNN instead of XGBoost) **and** dependent →
  independent evaluation.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.833 | 0.389 | — |
| Recall | 0.845 | 0.368 | — |
| F1 | 0.839 | 0.378 | weighted **0.742** |
| Accuracy | | | **0.744** (train 0.782) |

Other test metrics: AUC-ROC 0.539, balanced accuracy 0.607, PR-AUC 0.335, MCC 0.218; best val AUC 0.760.
Confusion matrix (rows = true, cols = pred): `[[WT→WT 60, WT→HT 11], [HT→WT 12, HT→HT 7]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.744 | 0.733 | +0.011 |
| Weighted F1 | 0.742 | 0.749 | −0.007 |
| WT F1 | 0.839 | 0.785 | +0.054 |
| HT F1 | 0.378 | 0.649 | −0.271 |
| HT recall | 0.368 | 0.940 | −0.572 |
| HT precision | 0.389 | 0.496 | −0.107 |

*Directional comparison only: this NN is scored on 90 session-level sequences, while the tabular base is
scored on ~2,465 recording-level rows — not a like-for-like benchmark.*

## Key insights
- **No degenerate collapse** — both classes get predicted (WT recall 0.845, HT recall 0.368), so the
  regsmall recipe avoids the all-HT / all-WT failure that plagues the independent split. But the win is
  shallow: it mostly classifies WT well and treats HT as noise.
- **The minority class is barely learned.** HT recall 0.368 and HT F1 0.378 mean the model catches only
  7 of 19 ASD-model sessions and is wrong on more HT calls than it gets right (precision 0.389). The
  headline accuracy 0.744 is essentially the WT base rate (79%) lightly beaten.
- **Test AUC 0.539 ≈ chance**, far below best val AUC 0.760 — the ranking learned on validation mice does
  not transfer to held-out test mice. Class weighting is so mild here that the operating point sits near
  the majority class; balanced accuracy 0.607 / MCC 0.218 confirm weak-but-real signal.
- Train 0.782 vs test 0.744 is a small gap (regularization worked), and early stopping fired at epoch 22
  — so the failure is generalization of the *signal*, not overfitting; the independent split simply has
  too few HT examples (56 train / 19 test sessions) for this sequence model.

## Recommendations
- The mild `pos_weight_beta=0.5` is too weak here — compare against the **D balanced-sampler** config
  (the most reliable anti-collapse fix) and **H cv_Dsampler** to see if HT recall can be raised without
  re-triggering collapse.
- For any "new-mouse" estimate, prefer the tabular independent runs over this NN: at AUC ≈ chance and
  HT F1 0.378, this 1D-CNN is not yet usable for ASD-model detection on unseen mice.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.539). `plots/training_curves.png` — train/val loss, acc, AUC vs epoch.
- `model/cnn1d_best.pt` — best checkpoint (epoch with val AUC 0.760). `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
