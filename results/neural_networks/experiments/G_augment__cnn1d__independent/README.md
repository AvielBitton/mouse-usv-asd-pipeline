# G_augment__cnn1d__independent — 1D-CNN · subject-independent · experiment G (augment)

> 1D-CNN on chronological per-syllable sequences, leak-free split, with sliding-window augmentation — degenerates to near-chance on the tiny held-out test set.

## Overview
- **Model:** 1D-CNN (~86K params) over a chronological per-syllable sequence (`max_seq_len=256`,
  order preserved), scored at the **session** level — not the 48 aggregated per-recording features the
  tabular base model uses.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`,
  `group_split`), so no mouse appears in two sets. This is the honest "generalize to unseen mice"
  setting (harder than the dependent base model, which splits rows randomly and lets mice leak across
  train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice (HT 97 / WT 311). Train 238 sessions (63 mice, HT 24%), val 80 (21 mice), test **90 sessions
  from 22 held-out mice** (HT 19 / WT 71, i.e. 21% HT).
- **What was adapted vs the base model (lever G):** sliding-window augmentation
  (`augment_windows=4`, `window_stride=128` → 367 train windows from 238 sessions) layered on the
  config-B class weighting (`pos_weight_beta=0.5` → `pos_weight=1.803`, BCE loss, `sampler=none`).
  Two things move at once vs base: model family (1D-CNN instead of XGBoost) **and** dependent →
  independent evaluation. Trained 39/100 epochs (early stopped, best val AUC 0.783).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.776 | 0.188 | — |
| Recall | 0.634 | 0.316 | — |
| F1 | 0.698 | 0.235 | weighted **0.600** |
| Accuracy | | | **0.567** (train 0.924) |

Test AUC 0.449 · balanced acc 0.475 · PR-AUC 0.210 · MCC **−0.043** (below random).
Confusion matrix (rows = true, cols = pred): `[[WT→WT 45, WT→HT 26], [HT→WT 13, HT→HT 6]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.567 | 0.733 | −0.166 |
| Weighted F1 | 0.600 | 0.749 | −0.149 |
| WT F1 | 0.698 | 0.785 | −0.087 |
| HT F1 | 0.235 | 0.649 | −0.414 |
| HT recall | 0.316 | 0.940 | −0.624 |
| HT precision | 0.188 | 0.496 | −0.308 |

*Directional only, not like-for-like: this NN is scored on 90 session-level sequences, whereas the
tabular base model is scored on ~2,465 recording-level rows.*

## Key insights
- **The model fails to generalize.** Test AUC 0.449 and MCC −0.043 are at/below chance — the learned
  scores carry essentially no signal on unseen mice, despite a healthy val AUC (0.783). Train accuracy
  0.924 vs test 0.567 is a ~0.36 gap: the augmented CNN overfit the 63 train mice.
- **Minority class barely detected, not collapsed.** Unlike the usual degenerate failure (HT recall
  ~1.0 or HT F1 0), here HT recall is only **0.316** (6 of 19 HT sessions caught) at precision **0.188**
  — both classes are predicted, but HT calls are wrong ~4 times out of 5 (HT F1 0.235).
- **Sliding-window augmentation did not help.** Adding 4 windows/session (367 windows) on top of the
  mild B weighting produced the weakest minority-class result of the lever set; the extra views appear
  to amplify train-mouse memorization rather than improve robustness to new mice.
- Held-out test is tiny (90 sessions, 19 HT) — single-split estimates here are high-variance; see the
  H `cv_Dsampler` cross-validation run for a more stable read.

## Recommendations
- Do not use this run for any new-mouse performance estimate — AUC < 0.5 means it underperforms a coin
  flip on ranking. Prefer the D (balanced sampler) family or the tabular independent runs.
- If 1D-CNN is kept on the independent split, drop augmentation and try the balanced minibatch sampler
  (lever D) and/or `regsmall` (lever F) to fight the train-mouse overfit before retuning class weights.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.449). `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/cnn1d_best.pt` — best checkpoint (val AUC 0.783). `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
