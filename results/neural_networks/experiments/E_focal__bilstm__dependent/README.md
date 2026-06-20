# E_focal__bilstm__dependent — BiLSTM · subject-dependent · experiment E (focal loss)

> BiLSTM on per-syllable sequences with **focal loss** and no class weighting, evaluated on the leaky subject-dependent split.

## Overview
- **Model:** BiLSTM (~149K params, hidden 64, 2 layers, dropout 0.3) over chronological per-syllable
  sequences (order preserved, `max_seq_len=256`), unlike the tabular base which uses 48 aggregated
  per-recording features. Scored at **session level**.
- **Evaluation split:** subject-dependent — random session-level split (`subject_eval_independent=false`,
  `group_split=false`). The log confirms heavy leakage: 61 mice shared between train and test, 56 between
  train and val. Optimistic, like the base model.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions / 106 mice;
  Train 244 / Val 82 / Test 82, HT ≈ 23–24% throughout.
- **What was adapted vs the base model (lever E):** loss switched to **focal loss** (`focal_gamma=2.0`) with
  **no class weighting and no sampler** (`pos_weight_beta=0.0`, `sampler=none`, effective `pos_weight=1.000`).
  Trained 29 epochs, early-stopped on val AUC (best 0.702).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.778 | 0.300 | — |
| Recall | 0.889 | 0.158 | — |
| F1 | 0.830 | 0.207 | weighted **0.685** |
| Accuracy | | | **0.720** (train 0.824) |

Test AUC 0.679 · balanced acc 0.523 · MCC 0.060 · PR-AUC 0.402.

Confusion matrix (rows = true, cols = pred): `[[WT→WT 56, WT→HT 7], [HT→WT 16, HT→HT 3]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.720 | 0.733 | −0.013 |
| Weighted F1 | 0.685 | 0.749 | −0.064 |
| WT F1 | 0.830 | 0.785 | +0.045 |
| HT F1 | 0.207 | 0.649 | −0.442 |
| HT recall | 0.158 | 0.940 | −0.782 |
| HT precision | 0.300 | 0.496 | −0.196 |

*Directional only, not like-for-like: this NN is scored on 82 session-level sequences, whereas the tabular
base is scored on ~2,465 recording-level rows.*

## Key insights
- **Minority-class failure.** Focal loss without any class weighting tilts the model toward the majority:
  HT recall collapses to **0.158** (3 of 19 HT sessions caught) and HT F1 drops to **0.207** — the opposite
  failure mode from a HT-everyone collapse. MCC 0.060 and balanced accuracy 0.523 confirm the model is
  barely above chance on the harder axis despite headline accuracy 0.720.
- **Accuracy is carried entirely by WT.** WT F1 0.830 (+0.045 vs base) is the only metric that beats the
  base; the 0.720 accuracy mostly reflects the 77% WT prior, not genuine class separation.
- **Overfitting on a leaky split.** Train accuracy 0.824 vs test 0.720, with val loss rising monotonically
  after ~epoch 9 while train loss keeps falling — early stopping fired at epoch 29 on a flat val AUC ≈ 0.70.
  Even with train/test mouse leakage, the model does not transfer to the minority class.

## Recommendations
- Focal loss alone underweights HT here. Prefer the **balanced sampler** (lever D) or explicit `pos_weight`
  (levers A/B) to recover HT recall; focal could be revisited only combined with class weighting.
- Do not use this run for any honest generalization estimate — the split leaks mice across train/test.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.679). `plots/training_curves.png` — loss/acc/AUC over 29 epochs.
- `model/bilstm_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler. `logs/out.txt` — flags,
  split/leakage info, class balance, per-epoch log, test report.
- Metrics source: `results.json` + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
