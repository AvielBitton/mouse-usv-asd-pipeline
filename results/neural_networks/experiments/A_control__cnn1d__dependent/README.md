# A_control__cnn1d__dependent — 1D-CNN · subject-dependent · A control (defaults)

> 1D-CNN on chronological per-syllable sequences, default config, subject-dependent split — collapses to ~chance (test accuracy 0.500).

## Overview
- **Model:** 1D-CNN (~86K params; convolutions over the chronological per-syllable sequence, order
  preserved). Scored at **session level** (82 test sessions), unlike the tabular base which scores
  per-recording rows.
- **Evaluation split:** subject-dependent — random **session-level** split (`subject_eval_independent:
  false`, `group_split: false`). The log warns of heavy mouse overlap (61 of 64 test mice also in train),
  so this is the leaky, optimistic setting — yet it still underperforms badly here.
- **Dataset:** official baseline (`--baseline`; Issue #46 filters; April-2026 HET→WT correction).
  408 sessions from 106 mice (HT 97 / WT 311); split 244 train / 82 val / 82 test, ~24% HT throughout.
- **What was adapted vs the base model:** lever **A control** — pure defaults (`pos_weight_beta=1.0`,
  `sampler=none`, `loss=bce`, `dropout=0.3`, no augmentation/CV). This is the reference NN run before any
  collapse-mitigation lever (B–H). Two things change vs the tabular base: model family (1D-CNN vs XGBoost)
  and input (per-syllable sequence vs 48 aggregated features).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.824 | 0.271 | — |
| Recall | 0.444 | 0.684 | — |
| F1 | 0.577 | 0.388 | weighted **0.533** |
| Accuracy | | | **0.500** (train 0.672) |

AUC 0.604 · balanced acc 0.564 · MCC 0.110 · PR-AUC 0.328 · best val AUC 0.710 · early-stopped epoch 22.
Confusion matrix (rows = true, cols = pred): `[[WT→WT 28, WT→HT 35], [HT→WT 6, HT→HT 13]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.500 | 0.733 | −0.233 |
| Weighted F1 | 0.533 | 0.749 | −0.216 |
| WT F1 | 0.577 | 0.785 | −0.208 |
| HT F1 | 0.388 | 0.649 | −0.261 |
| HT recall | 0.684 | 0.940 | −0.256 |
| HT precision | 0.271 | 0.496 | −0.225 |

*Comparison is directional, not like-for-like: this NN is scored on 82 session-level sequences, while the
tabular base is scored on ~2,465 recording-level rows.*

## Key insights
- **Near-chance and degenerate.** Test accuracy 0.500 with the model tagging HT for most sessions —
  WT recall collapses to 0.444 (35 of 63 WT sessions called HT) while it still misses HT (recall 0.684).
  This is the classic over-prediction of the minority class driven by `pos_weight=3.207`, and it lands
  well below the trivial majority-class (all-WT) baseline of ~0.77.
- **No real signal carried to test.** AUC 0.604 / MCC 0.110 / PR-AUC 0.328 are barely above random,
  despite this being the *leaky* subject-dependent split (61/64 test mice seen in train) that should be the
  easiest possible setting.
- **Train/val/test all weak.** Train accuracy only 0.672 and val AUC plateaus at 0.710 by epoch 7 before
  early stopping at epoch 22 — the 1D-CNN never fits the sequences well, so this is underfitting plus a
  bad operating point, not classic overfitting.
- Every headline metric is 0.20–0.26 below the tabular base; default-config 1D-CNN on raw sequences is not
  competitive here and motivates the collapse-mitigation levers (D sampler, F regsmall, etc.).

## Recommendations
- Do not use this run as an NN baseline of record — the default BCE + `pos_weight` recipe collapses.
  Compare against the balanced-sampler config (`../*__cnn1d__*` D/H runs), which the brief flags as the
  most reliable collapse fix.
- If 1D-CNN is pursued, address underfitting first (longer/larger training, milder class weighting per
  lever B/C) before tuning the decision threshold.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.604). `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/cnn1d_best.pt` — best checkpoint (val AUC 0.710). `model/scaler.pkl` — feature scaler.
- `results.json` — full metrics + config. `logs/out.txt` — flags, split/overlap warning, class balance, early stopping.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
