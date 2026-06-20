# A_control__cnn1d__independent — 1D-CNN · subject-independent · experiment A (control)

> Default-config 1D-CNN on chronological per-syllable sequences, evaluated **leak-free** (split grouped by mouse).

## Overview
- **Model:** 1D-CNN (86,041 params) over an ordered per-syllable sequence (chronology preserved,
  `max_seq_len=256`), unlike the tabular base model's 48 aggregated per-recording features. Scored at
  **session level** (~82–90 test sessions), not at recording level.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`,
  group-aware), so no mouse appears in two sets. This is the honest "generalize to unseen mice" setting
  (harder than the dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice → train 238 (63 mice, HT 24%), val 80 (21 mice, HT 28%), test 90 (22 mice, HT 21%).
- **What was adapted vs the base model:** experiment **A = control** — defaults, no extra lever
  (`pos_weight_beta=1.0` → pos_weight 3.250, `sampler=none`, `loss=bce`, `dropout=0.3`,
  `weight_decay=0.0`). Two things change together vs base: model family (1D-CNN instead of XGBoost) **and**
  evaluation moves from subject-dependent to subject-independent. Early stopping at epoch 17/100
  (best val AUC 0.753).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.797 | 0.231 | — |
| Recall | 0.718 | 0.316 | — |
| F1 | 0.756 | 0.267 | weighted **0.652** |
| Accuracy | | | **0.633** (train 0.731) |

AUC 0.609 · balanced acc 0.517 · macro-F1 0.511 · MCC 0.031.
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

*Δ is directional, not like-for-like: this NN is scored on 90 session-level sequences while the tabular base is scored on ~2,465 recording-level rows.*

## Key insights
- The control 1D-CNN does **not** collapse — both classes get predicted (HT recall 0.316, WT recall
  0.718) — but it is barely better than chance: **MCC 0.031, balanced acc 0.517, AUC 0.609**. The
  separation it learned on val (best val AUC 0.753) does not transfer to held-out mice (test AUC 0.609).
- The minority class is the weak point: **HT F1 0.267** (precision 0.231, recall 0.316). It catches only
  6 of 19 ASD-model sessions and over half of its HT calls are false positives — far worse than the
  dependent base's HT recall 0.940 (−0.624).
- Headline accuracy (0.633) is propped up by the WT majority (79% of test); on the balanced view there
  is almost no signal. Train 0.731 vs test 0.633 shows mild overfit, but the bigger gap is val→test,
  i.e. the leak-free split, not memorization.

## Recommendations
- This control run is the reference for the other A–H levers; it confirms class weighting alone
  (`pos_weight 3.25`) is insufficient on the tiny independent split. Compare against the D balanced
  sampler and F regsmall configs, which target exactly this under-performance.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.609). `plots/training_curves.png` — train/val loss & AUC over 17 epochs.
- `model/cnn1d_best.pt` — best-val checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
