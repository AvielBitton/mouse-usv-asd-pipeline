# B_beta0.5__transformer__independent — Transformer · subject-independent · experiment B (beta0.5)

> Sequence Transformer on the baseline data, evaluated **leak-free** (split by mouse), with milder class weighting (`pos_weight_beta=0.5`).

## Overview
- **Model:** Transformer (~73K params) over the chronological per-syllable sequence (order preserved),
  scored at **session level** — not the 48 aggregated per-recording features the tabular base uses.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`), so no
  mouse appears in two sets. This is the honest "generalize to unseen mice" setting (harder than the
  dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice; test = 90 held-out sessions from 22 mice (WT 79% / HT 21%). Train 238 / val 80.
- **What was adapted vs the base model (experiment B = beta0.5):** sequence Transformer instead of
  XGBoost, subject-independent instead of dependent, and class weighting softened to
  `pos_weight_beta=0.5` (effective `pos_weight=1.803`, sampler off, plain BCE). Trained 33 epochs,
  early-stopped on best val AUC 0.807.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.848 | 0.375 | — |
| Recall | 0.789 | 0.474 | — |
| F1 | 0.818 | 0.419 | weighted **0.733** |
| Accuracy | | | **0.722** (train 0.828) |

Test AUC 0.725 · balanced acc 0.631 · PR-AUC 0.531 · MCC 0.242.
Confusion matrix (rows = true, cols = pred): `[[WT→WT 56, WT→HT 15], [HT→WT 10, HT→HT 9]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.722 | 0.733 | −0.011 |
| Weighted F1 | 0.733 | 0.749 | −0.016 |
| WT F1 | 0.818 | 0.785 | +0.033 |
| HT F1 | 0.419 | 0.649 | −0.230 |
| HT recall | 0.474 | 0.940 | −0.466 |
| HT precision | 0.375 | 0.496 | −0.121 |

*Comparison is directional, not like-for-like: this NN is scored on 90 session-level sequences, while the tabular base is scored on ~2,465 recording-level rows.*

## Key insights
- No degenerate collapse here — the milder weighting keeps both classes alive (HT recall 0.474, WT
  recall 0.789), unlike the all-HT or all-WT failure modes common to these NN runs.
- The minority class is the weak spot: **HT F1 collapses to 0.419** (−0.230 vs base) because the model
  now both misses HT (recall 0.474, catches 9 of 19) **and** over-fires (precision 0.375) — only 9 of 24
  HT predictions are correct. With 19 HT test sessions, every miss moves the metric a lot.
- Headline accuracy (0.722) and weighted F1 (0.733) sit near the base, but that is carried by the
  dominant WT class (F1 0.818); discrimination is mediocre — AUC 0.725, MCC 0.242, balanced acc 0.631.
- Train 0.828 vs test 0.722 (0.11 gap) plus val AUC 0.807 vs test AUC 0.725 shows modest overfit and the
  expected dependent→independent penalty on a tiny 90-session test set.

## Recommendations
- HT detection is poor at the 0.5 cut; for the minority class prefer the sampler-based fix (experiment D)
  or focal loss (E) over softened weighting, and consider threshold tuning toward a target HT recall.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — normalized + raw-count confusion.
- `plots/roc_curve.png` — ROC (test AUC 0.725). `plots/training_curves.png` — loss/acc/AUC over 33 epochs.
- `model/transformer_best.pt` — best checkpoint (early-stopped). `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`; split info, class balance and early stopping in `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
