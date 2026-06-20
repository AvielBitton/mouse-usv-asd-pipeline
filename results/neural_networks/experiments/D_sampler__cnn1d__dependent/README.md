# D_sampler__cnn1d__dependent — 1D-CNN · subject-dependent · D balanced sampler

> 1D-CNN over per-syllable sequences, with a balanced minibatch sampler (no loss class-weighting), on the official baseline data — evaluated subject-dependent (mice leak across splits).

## Overview
- **Model:** 1D-CNN (~86K params) over a chronological per-syllable sequence (order preserved, `max_seq_len=256`), scored at the **session** level — unlike the tabular base, which uses 48 aggregated per-recording features.
- **Evaluation split:** subject-dependent — random session-level split (`subject_eval_independent=false`, `group_split=false`). The log confirms heavy leakage: **61 mice shared between train and test**, 56 between train and val. Optimistic by design.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions / 106 mice; train 244 / val 82 / test 82 sessions, all at HT≈24% / WT≈76%.
- **What was adapted vs the base model:** the **D lever** — a balanced minibatch sampler oversamples the HT minority, while loss class-weighting is turned off (`pos_weight_beta=0.0`, `pos_weight=1.000`, `loss=bce`). This is the most reliable fix for degenerate collapse. Trained 22/100 epochs (early stop, best val AUC 0.722).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.818 | 0.333 | — |
| Recall | 0.714 | 0.474 | — |
| F1 | 0.763 | 0.391 | weighted **0.677** |
| Accuracy | | | **0.659** (train 0.783) |

AUC 0.590 · balanced acc 0.594 · MCC 0.169 · PR-AUC 0.298 (best val AUC 0.722).

Confusion matrix (rows = true, cols = pred): `[[WT→WT 45, WT→HT 18], [HT→WT 10, HT→HT 9]]` (WT support 63, HT support 19).

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.659 | 0.733 | −0.074 |
| Weighted F1 | 0.677 | 0.749 | −0.072 |
| WT F1 | 0.763 | 0.785 | −0.022 |
| HT F1 | 0.391 | 0.649 | −0.258 |
| HT recall | 0.474 | 0.940 | −0.466 |
| HT precision | 0.333 | 0.496 | −0.163 |

*Directional comparison only: this NN is scored on session-level sequence data (82 test sessions) while the tabular base is scored at recording level (~2,465 rows), so these are not like-for-like.*

## Key insights
- The balanced sampler **avoids degenerate collapse** — both classes are predicted (HT recall 0.474, WT recall 0.714, neither at 0 or 1), which is the intended effect of the D lever versus the all-one-class failure mode.
- But it does not buy real separation: **AUC 0.590** and MCC 0.169 are barely above chance, and **HT precision is just 0.333** — two of every three HT predictions are false positives, so HT F1 collapses to 0.391 (−0.258 vs base).
- Despite leakage that should flatter the dependent split, every headline metric trails the tabular base: test accuracy −0.074, HT recall −0.466. The sampler trades the base model's near-perfect HT recall (0.940) for a far more conservative, lower-quality operating point.
- Train 0.783 vs test 0.659 with val accuracy oscillating (0.39–0.68 across epochs while val AUC peaked early at 0.722) signals an unstable, noisy fit on only 244 training sessions.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.590). `plots/training_curves.png` — loss/acc/AUC over 22 epochs.
- `model/cnn1d_best.pt` — best-val checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, leakage warning, class balance).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
