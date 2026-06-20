# A_control__bilstm__dependent — BiLSTM · subject-dependent · experiment A (control)

> Control-config BiLSTM on the baseline sequences, dependent split — **collapsed**: predicts HT for every test session.

## Overview
- **Model:** BiLSTM (2 layers, hidden 64, dropout 0.3; ~149K params). Input is a chronological
  per-syllable sequence (`max_seq_len` 256), scored at the **session level**, unlike the tabular base's
  48 aggregated per-recording features.
- **Evaluation split:** subject-dependent — random **session-level** split, so the same mouse appears in
  train and test (the log confirms train/test share 61 mice). Optimistic/leaky, matching the base model's
  split type.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice (HT 97 / WT 311 ≈ 24% positive). Test = 82 sessions (WT 63 / HT 19, 23%).
- **What was adapted vs the base model:** experiment **A = control** — default NN levers
  (`pos_weight_beta=1.0`, `sampler=none`, `loss=bce`); the change vs base is the model family
  (BiLSTM instead of XGBoost) and the sequence/session representation, not the lever.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.000 | 0.232 | — |
| Recall | 0.000 | 1.000 | — |
| F1 | 0.000 | 0.376 | weighted **0.087** |
| Accuracy | | | **0.232** (train 0.242) |

AUC 0.790 · PR-AUC 0.492 · balanced accuracy 0.500 · MCC 0.000. Early-stopped at epoch 16
(best val AUC 0.778). Confusion matrix (rows = true, cols = pred): `[[WT→WT 0, WT→HT 63], [HT→WT 0, HT→HT 19]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.232 | 0.733 | −0.501 |
| Weighted F1 | 0.087 | 0.749 | −0.662 |
| WT F1 | 0.000 | 0.785 | −0.785 |
| HT F1 | 0.376 | 0.649 | −0.273 |
| HT recall | 1.000 | 0.940 | +0.060 |
| HT precision | 0.232 | 0.496 | −0.264 |

*NN are scored on session-level sequence data (~82 test sessions) vs the tabular base's recording-level
data (~2,465 rows), so this comparison is directional, not like-for-like.*

## Key insights
- **Degenerate collapse.** The model predicts HT for all 82 test sessions: HT recall 1.000, WT recall
  0.000, WT F1 0.000, balanced accuracy 0.500, MCC 0.000. Test accuracy (0.232) just equals the HT base
  rate — there is no real classifier here.
- **The ranking is not random — only the decision rule is broken.** Test AUC 0.790 (PR-AUC 0.492) shows
  the probabilities separate the classes reasonably, but the default 0.5 threshold under `pos_weight=3.2`
  pushes every score above the cut. Collapse is a thresholding/class-weight artifact, not a feature
  problem.
- **Train mirrors test** (train acc 0.242 ≈ test 0.232): the collapse is present on training data too, so
  it is not overfitting — the run never learned a usable WT decision boundary. Val accuracy oscillated
  (0.24→0.71→0.61) while val AUC stayed ~0.68–0.78, the classic signature of an unstable operating point.

## Recommendations
- This control run is unusable as-is. Use the AUC (0.790) only as a ranking sanity check, never the 0.5
  predictions. Move the threshold or rebalance: the **D balanced-minibatch sampler** is the most reliable
  fix for this collapse; **B (`beta=0.5`)** / **C (`beta=0`)** dial back the class weighting that drove
  every score over the cut.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — all-HT confusion (normalized + counts).
- `plots/roc_curve.png` — ROC (AUC 0.790). `plots/training_curves.png` — loss/acc/AUC over 16 epochs.
- `model/bilstm_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
