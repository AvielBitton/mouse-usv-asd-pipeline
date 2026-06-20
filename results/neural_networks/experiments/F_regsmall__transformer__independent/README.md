# F_regsmall__transformer__independent — Transformer · subject-independent · experiment F (regsmall)

> Heavily-regularized small Transformer on session-level sequences, leak-free split — **collapses to predicting WT for everyone**.

## Overview
- **Model:** Transformer (~39K params; `d_model` 64, `hidden_size` 32, 1 layer). Input is a chronological
  per-syllable sequence (order preserved, `max_seq_len` 256), scored at **session level**, unlike the
  tabular base's 48 aggregated per-recording features.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent` /
  group-aware), so no mouse appears in two sets. Honest "generalize to unseen mice" setting, harder than
  the dependent base model (random row split, mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions / 106 mice
  → Train 238 (63 mice, HT 24%) · Val 80 (21 mice, HT 28%) · **Test 90 sessions (22 mice, HT 21% / WT 79%)**.
- **What was adapted vs the base model:** lever **F regsmall** — weight decay (`1e-3`) + high dropout (0.5)
  + a smaller net, intended to fight overfitting on the tiny independent split. Mild class weighting kept
  (`pos_weight_beta=0.5`, `pos_weight=1.803`, BCE loss, no sampler). Two things change together vs base:
  model family (Transformer instead of XGBoost) **and** dependent → independent evaluation.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.789 | 0.000 | — |
| Recall | 1.000 | 0.000 | — |
| F1 | 0.882 | 0.000 | weighted **0.696** |
| Accuracy | | | **0.789** (train 0.765) |

AUC-ROC 0.815 · PR-AUC 0.616 · balanced accuracy **0.500** · MCC **0.000** · macro-F1 0.441.
Best val AUC 0.868, early-stopped at epoch 23/100.

Confusion (rows = true, cols = pred): `[[WT→WT 71, WT→HT 0], [HT→WT 19, HT→HT 0]]` — **every session predicted WT**.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.789 | 0.733 | +0.056 |
| Weighted F1 | 0.696 | 0.749 | −0.053 |
| WT F1 | 0.882 | 0.785 | +0.097 |
| HT F1 | 0.000 | 0.649 | −0.649 |
| HT recall | 0.000 | 0.940 | −0.940 |
| HT precision | 0.000 | 0.496 | −0.496 |

*Comparison is directional, not like-for-like: this NN is scored on 90 session-level sequences, while the tabular base is scored on ~2,465 recording-level rows.*

## Key insights
- **Degenerate collapse: predicts WT for all 90 test sessions** (HT recall 0.000, HT F1 0.000, WT recall
  1.000). The 0.789 "accuracy" and +0.056 vs base are an artifact of the 79% WT majority — balanced
  accuracy 0.500 and MCC 0.000 confirm the model has zero discriminative output at the 0.5 cut.
- **The ranking is not random — the threshold is.** Test AUC-ROC 0.815 / PR-AUC 0.616 (and best val AUC
  0.868) mean the logits *do* separate classes, but the decision boundary sits above every HT score, so
  all positives are missed. This is a thresholding/calibration failure, not a no-signal failure.
- **The regsmall lever over-corrected.** Aggressive regularization (dropout 0.5, weight decay 1e-3,
  tiny net) plus only mild class weighting (`beta=0.5`) pushed the model to the safe majority prediction;
  train accuracy 0.765 ≈ the 76% WT train prior, so it never actually learned the minority class.

## Recommendations
- Do not use this run as-is — at the default 0.5 cut it detects no ASD-model pups. Since AUC ≈ 0.82, a
  recall-targeted threshold (e.g. `target_recall` ~0.80) on the validation set would likely recover usable
  HT detection from the same logits.
- For fixing the collapse at train time, prefer the **D balanced-sampler** config (most reliable
  anti-collapse fix in this study) over the regsmall recipe, or pair regsmall with stronger class
  weighting (`beta=0`) / focal loss rather than `beta=0.5`.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (all-WT column).
- `plots/roc_curve.png` — ROC (AUC 0.815). `plots/training_curves.png` — loss/acc/AUC vs epoch.
- `model/transformer_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
