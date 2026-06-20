# C_beta0__cnn1d__dependent — 1D-CNN · subject-dependent · experiment C (no class weighting)

> 1D-CNN on the baseline sequence data with class weighting **off** (beta=0); the model collapses to all-WT.

## Overview
- **Model:** 1D-CNN over chronological per-syllable sequences (~86K params; `hidden_size` 64,
  `num_layers` 2, dropout 0.3, `max_seq_len` 256). Scored at **session level**, not recording level.
- **Evaluation split:** subject-dependent — random session-level split, so the **same mouse can sit in
  train and test** (the log warns of 61 shared train/test mice). Optimistic/leaky, matching the base model.
- **Dataset:** official baseline sequence cache — 408 sessions from 106 mice (HT=97, WT=311).
  Test = 82 sessions (HT 23% / WT 77%). Train 244 / val 82.
- **What was adapted vs base (lever C — beta0):** `pos_weight_beta=0.0` → **no class weighting**
  (`pos_weight=1.000`, sampler none, BCE loss). With the minority class un-upweighted on top of the model
  family change (1D-CNN vs XGBoost), training has no incentive to predict the 23% HT class.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.765 | 0.000 | — |
| Recall | 0.984 | 0.000 | — |
| F1 | 0.861 | 0.000 | weighted **0.662** |
| Accuracy | | | **0.756** (train 0.799) |

AUC 0.568 · balanced acc 0.492 · MCC −0.061 · PR-AUC 0.285 · best val AUC 0.714 · early-stopped epoch 21.
Confusion matrix (rows = true, cols = pred): `[[WT→WT 62, WT→HT 1], [HT→WT 19, HT→HT 0]]` — every HT
session is misclassified as WT.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.756 | 0.733 | +0.023 |
| Weighted F1 | 0.662 | 0.749 | −0.087 |
| WT F1 | 0.861 | 0.785 | +0.076 |
| HT F1 | 0.000 | 0.649 | −0.649 |
| HT recall | 0.000 | 0.940 | −0.940 |
| HT precision | 0.000 | 0.496 | −0.496 |

*Directional only: this NN is scored on **82 session-level sequences**, whereas the tabular base is scored
on ~2,465 recording-level rows — not a like-for-like comparison.*

## Key insights
- **Degenerate collapse to the majority class.** HT recall 0.000, HT F1 0.000, WT recall 0.984 — the
  network predicts WT for all but one session. The headline 0.756 accuracy is just the WT base rate (77%),
  not learning: balanced accuracy 0.492 and MCC −0.061 confirm performance at/below chance.
- **Removing class weighting (beta0) is the direct cause.** With `pos_weight=1.000` and a 23% positive
  rate, BCE is minimized by ignoring HT entirely. Train accuracy climbs to 0.91 by epoch 21 while val AUC
  peaks at 0.714 then decays — the model overfits WT-leaning structure rather than separating classes.
- Test AUC 0.568 (vs best val 0.714) shows the ranking ability barely beats random on the held-out
  sessions, so the collapse is not just a threshold problem — there is little real signal to recover.
- The +0.023 accuracy / +0.076 WT-F1 "wins" over the base are artifacts of the all-WT prediction; the
  −0.940 HT-recall and −0.649 HT-F1 are the honest story.

## Recommendations
- Do not use this config — it is the negative control. Prefer the class-weighted / sampler variants
  (lever **D** balanced sampler is the most reliable fix for this collapse; **B** beta0.5 is a milder
  middle ground) for any usable dependent-split CNN.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (all HT → WT).
- `plots/roc_curve.png` — ROC (test AUC 0.568). `plots/training_curves.png` — loss/acc/AUC over 21 epochs.
- `model/cnn1d_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`; split/data stats and early-stopping in `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
