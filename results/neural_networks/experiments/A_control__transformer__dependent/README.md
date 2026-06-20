# A_control__transformer__dependent — Transformer · subject-dependent · experiment A (control)

> Transformer baseline run on session sequences, evaluated on a **leaky** session-level split (default config, no class-imbalance lever).

## Overview
- **Model:** Transformer (~73K params; 2 layers, `d_model`/`hidden_size` 64, dropout 0.3). Input is a
  chronological per-syllable sequence (order preserved, `max_seq_len` 256), scored at session level —
  not the 48 aggregated per-recording features the tabular base uses.
- **Evaluation split:** subject-dependent — random **session-level** split (`subject_eval_independent=false`,
  `group_split=false`). The log confirms heavy leakage: 61 mice shared between train and test, 56 between
  train and val, so this is the optimistic in-distribution setting (not generalize-to-unseen-mice).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice (HT 97 / WT 311). Split 244 train / 82 val / 82 test sessions; test HT 23% / WT 77%.
- **What was adapted vs the base model:** experiment A = control (defaults). `pos_weight_beta=1.0`
  (full inverse-frequency weighting, `pos_weight=3.207`), BCE loss, no sampler, no augmentation, no CV —
  the reference point the B–H levers are measured against. Switches model family (Transformer vs XGBoost)
  and granularity (session sequences vs recording rows); the split type stays dependent.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.872 | 0.371 | — |
| Recall | 0.651 | 0.684 | — |
| F1 | 0.745 | 0.481 | weighted **0.684** |
| Accuracy | | | **0.659** (train 0.684) |

AUC-ROC 0.655 · balanced accuracy 0.668 · MCC 0.286 · PR-AUC 0.350. Early stopping at epoch 31/100
(best val AUC 0.688). Confusion matrix (rows = true, cols = pred): `[[WT→WT 41, WT→HT 22], [HT→WT 6, HT→HT 13]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.659 | 0.733 | −0.074 |
| Weighted F1 | 0.684 | 0.749 | −0.065 |
| WT F1 | 0.745 | 0.785 | −0.040 |
| HT F1 | 0.481 | 0.649 | −0.168 |
| HT recall | 0.684 | 0.940 | −0.256 |
| HT precision | 0.371 | 0.496 | −0.125 |

*Directional only, not like-for-like: this Transformer is scored on 82 session-level sequences, while the
tabular base is scored on ~2,465 recording-level rows.*

## Key insights
- **No degenerate collapse** — both classes are predicted (HT recall 0.684, WT recall 0.651), so the full
  `pos_weight=3.207` weighting kept the control run off the all-one-class trap that hits other NN configs.
- It trails the tabular base on every metric, worst on the minority class: **HT F1 0.481 (−0.168), HT recall
  0.684 (−0.256), HT precision 0.371 (−0.125)** — barely above the 23% prior, so most HT calls are wrong.
- Weak separation overall: AUC-ROC 0.655, MCC 0.286, balanced accuracy 0.668 — only modestly above chance,
  and the small dependent split (82 sessions) makes these numbers high-variance.
- Train accuracy 0.684 ≈ test 0.659: the model is not overfitting, it is **underfitting** the sequence task —
  even with leakage it cannot match the aggregated-feature tabular recipe.

## Recommendations
- Use this control run only as the A reference point for the B–H levers; for any reported "dependent NN"
  number prefer a config that lifts HT separation, and benchmark new-mouse performance on an independent split.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — normalized + count confusion matrices.
- `plots/roc_curve.png` — test ROC (AUC 0.655). `plots/training_curves.png` — loss/acc/AUC over 31 epochs.
- `model/transformer_best.pt` — best checkpoint (val AUC 0.688). `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`; split/data stats and early stopping in `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
