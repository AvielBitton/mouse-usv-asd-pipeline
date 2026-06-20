# F_regsmall__bilstm__independent — BiLSTM · subject-independent · experiment F (regsmall)

> Heavily regularized, downsized BiLSTM on baseline sequence data, evaluated **leak-free** (split grouped by mouse).

## Overview
- **Model:** BiLSTM over chronological per-syllable sequences (order preserved), scored at **session
  level** — unlike the tabular base, which uses 48 aggregated per-recording features. Shrunk for the
  tiny independent split: `hidden_size=32`, `num_layers=1`, only **16,857 params** (the full BiLSTM is
  ~149K). Trained 35 epochs (early-stopped, best val AUC 0.811).
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`), so no
  mouse appears in two sets. This is the honest "generalize to unseen mice" setting (harder than the
  dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice. Test = **90 held-out sessions** from 22 mice (WT 79% / HT 21%).
- **What was adapted vs the base model:** lever **F (regsmall)** — weight decay (`0.001`) + high dropout
  (`0.5`) + a smaller net, plus milder class weighting (`pos_weight_beta=0.5`, pos_weight 1.80). Two
  things change together: model family (BiLSTM instead of XGBoost) **and** dependent → independent eval.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.812 | 0.286 | — |
| Recall | 0.789 | 0.316 | — |
| F1 | 0.800 | 0.300 | weighted **0.694** |
| Accuracy | | | **0.689** (train 0.840) |

Test AUC 0.701 · balanced acc 0.552 · MCC 0.101 · PR-AUC 0.356.
Confusion matrix (rows = true, cols = pred): `[[WT→WT 56, WT→HT 15], [HT→WT 13, HT→HT 6]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.689 | 0.733 | −0.044 |
| Weighted F1 | 0.694 | 0.749 | −0.055 |
| WT F1 | 0.800 | 0.785 | +0.015 |
| HT F1 | 0.300 | 0.649 | −0.349 |
| HT recall | 0.316 | 0.940 | −0.624 |
| HT precision | 0.286 | 0.496 | −0.210 |

*Directional only, not like-for-like: this NN is scored on 90 session-level sequences, while the
tabular base is scored on ~2,465 recording-level rows.*

## Key insights
- Regularization avoids the usual degenerate collapse — both classes get predicted (HT recall 0.316,
  WT recall 0.789, no all-one-class output) — but the minority class is barely learned: **HT F1 0.300**,
  HT precision 0.286, MCC 0.101 and balanced accuracy 0.552 are only just above chance.
- The minority class craters versus the dependent base: **HT recall −0.624** and **HT F1 −0.349**.
  Only 6 of 19 HT sessions are caught; 13 are missed as WT. Headline accuracy (0.689) holds up only
  because the test set is 79% WT and WT is predicted well (F1 0.800).
- Val AUC peaked at 0.811 (epoch 20) but **test AUC is 0.701** — a ~0.11 generalization gap on truly
  unseen mice, with train acc 0.840 vs test 0.689 confirming the split is the hard part, not capacity.
- The tiny independent split (238 train / 80 val / 90 test sessions; only 56 HT train sessions) leaves
  too little minority signal for a sequence model to separate the classes reliably.

## Recommendations
- For a sequence model on this independent split, prefer the balanced-sampler line (lever **D /
  cv_Dsampler**), which is the most reliable fix for minority under-prediction; regsmall alone is not
  enough here.
- At the default 0.5 cut HT recall is unusable (0.316); if this run is kept, threshold tuning toward a
  `target_recall` operating point is required before any "new-mouse" use.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.701). `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/bilstm_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
