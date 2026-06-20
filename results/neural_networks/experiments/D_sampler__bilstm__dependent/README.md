# D_sampler__bilstm__dependent — BiLSTM · subject-dependent · D balanced-sampler experiment

> BiLSTM on the official baseline data, evaluated on the **optimistic** (leaky) session-level split, with a balanced minibatch sampler as the anti-collapse lever.

## Overview
- **Model:** BiLSTM (~149K params; 2 layers, hidden 64, dropout 0.3). Input is a chronological
  per-syllable sequence (order preserved), scored at the **session level**, unlike the tabular base
  model's 48 aggregated per-recording features.
- **Evaluation split:** subject-dependent — random session-level split (`subject_eval_independent=false`,
  `group_split=false`), so the same mouse can appear in train and test (the log warns of 61 shared
  train/test mice). This is the optimistic, leaky setting that flatters scores.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  408 sessions from 106 mice (HT 97 / WT 311). Test = 82 sessions (WT 63 / HT 19, ~23% HT).
- **What was adapted vs the base model:** the **D lever** — a balanced minibatch sampler with class
  weighting off (`pos_weight_beta=0.0`, `sampler=balanced`, `loss=bce`) — the most reliable fix for
  degenerate collapse. Note this also swaps model family (BiLSTM vs XGBoost) and granularity (sessions
  vs recordings).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.836 | 0.370 | — |
| Recall | 0.730 | 0.526 | — |
| F1 | 0.780 | 0.435 | weighted **0.700** |
| Accuracy | | | **0.683** (train 0.738) |

Test AUC-ROC 0.776 · PR-AUC 0.526 · balanced acc 0.628 · MCC 0.230. Best val AUC 0.820 (epoch 1),
early-stopped at epoch 16 / 100.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.683 | 0.733 | −0.050 |
| Weighted F1 | 0.700 | 0.749 | −0.049 |
| WT F1 | 0.780 | 0.785 | −0.005 |
| HT F1 | 0.435 | 0.649 | −0.214 |
| HT recall | 0.526 | 0.940 | −0.414 |
| HT precision | 0.370 | 0.496 | −0.126 |

*Comparison is directional, not like-for-like: this BiLSTM is scored on 82 session-level sequences,
whereas the tabular base reports recording-level metrics over ~2,465 rows.*

## Key insights
- **No collapse** — the balanced sampler did its job: the model predicts both classes (HT recall 0.526,
  WT recall 0.730), avoiding the degenerate all-HT or all-WT failure that plagues the un-sampled NN runs.
- But the operating point is weak on the minority class: **HT precision 0.370 and HT F1 0.435** mean
  about 2 in 3 HT calls are false positives and roughly half the ASD-model sessions are missed.
- Despite the leaky dependent split, every headline metric trails the tabular base (accuracy −0.050,
  weighted F1 −0.049, HT recall −0.414); MCC 0.230 confirms only modest class separation.
- Training is unstable and front-loaded — **best val AUC (0.820) lands at epoch 1**, then drifts down
  while train accuracy climbs to 0.779; the 0.05 train/test accuracy gap is small only because val/test
  performance never improved past the start.

## Recommendations
- The sampler fixes collapse but not class separation; HT precision 0.37 makes positive calls
  unreliable. Compare against the CV variant (`../H_cv_Dsampler__bilstm__dependent/`) to gauge whether
  this single split is representative before trusting these numbers.
- For any honest generalization estimate, prefer the subject-independent runs — this dependent split
  leaks 61 mice across train/test and still underperforms the tabular base.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — ROC curve (test AUC 0.776). `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/bilstm_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
