# tabpfn_subject_eval_independent_baseline — TabPFN · subject-independent · threshold objectives

> Same TabPFN model, leak-free split — the decision threshold is re-derived under four objectives from saved validation probabilities (no retraining).

## Overview
- **Model:** TabPFN (prior-data-fitted transformer; no hyperparameter tuning; validation merged into
  train). The fitted model is **identical** to the base TabPFN independent run — only the cut point moves.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`), so no
  mouse appears in two sets (the honest "generalize to unseen mice" setting).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). Test = 2,139
  recordings (WT 1,560 / HT 579); validation labels WT 1,788 / HT 530.
- **What was adapted vs the base model:** decision-threshold objective selection only. From the saved
  validation probabilities the threshold is re-derived under `youden`, `f1`, `target_recall` (HT recall
  floor 0.80) and `balanced`, alongside the 0.5 default. **For this independent split the recommended
  objective is `target_recall` (~0.80).** Val AUC 0.679, test AUC 0.783 (unchanged by thresholding).

## Results (test set)
| Objective | thr | acc | balacc | HT rec | HT prec | HT F1 | WT rec |
|---|---|---|---|---|---|---|---|
| @0.5 | 0.500 | 0.713 | 0.662 | 0.551 | 0.474 | 0.510 | 0.773 |
| youden | 0.005 | 0.703 | 0.796 | 0.998 | 0.477 | 0.645 | 0.594 |
| f1 | 0.005 | 0.703 | 0.796 | 0.998 | 0.477 | 0.645 | 0.594 |
| **target_recall** | 0.095 | 0.687 | 0.742 | 0.864 | 0.458 | 0.599 | 0.621 |
| balanced | 0.005 | 0.704 | 0.797 | 1.000 | 0.477 | 0.646 | 0.594 |

`target_recall` confusion matrix (rows = true, cols = pred): `[[WT→WT 969, WT→HT 591], [HT→WT 79, HT→HT 500]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
Recommended objective (`target_recall`) on test vs the base model at its 0.5 cut:
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.687 | 0.733 | −0.046 |
| Weighted F1 | 0.704 | 0.749 | −0.045 |
| WT F1 | 0.743 | 0.785 | −0.042 |
| HT F1 | 0.599 | 0.649 | −0.050 |
| HT recall | 0.864 | 0.940 | −0.076 |
| HT precision | 0.458 | 0.496 | −0.038 |

## Key insights
- The default 0.5 cut is far too high for this model: probabilities are crushed toward 0, so every
  re-derived threshold lands at ~0.005–0.095. At 0.5, HT recall is only 0.551 (HT F1 0.510); any
  objective threshold roughly **doubles balanced accuracy's lift** (0.662 → 0.74–0.80).
- `youden`/`f1`/`balanced` all collapse to ~0.005 and predict HT for nearly everyone (HT recall
  0.998–1.000, WT recall 0.594) — high balanced accuracy but operationally degenerate.
- `target_recall` (thr 0.095) is the only non-degenerate operating point: HT recall 0.864 with WT recall
  held at 0.621, balanced accuracy 0.742. It trades raw accuracy (0.687) for a controlled, recall-floored
  cut — appropriate for the leak-free independent split.
- HT precision stays ~0.46–0.48 across every objective: class separation is weak (val AUC 0.679), so
  thresholding moves the recall/precision balance but cannot fix the false-positive rate.

## Recommendations
- For this independent run use the **`target_recall`** cut (thr ≈ 0.095): HT recall 0.864 without the
  predict-everything-HT collapse of `youden`/`f1`/`balanced`. Treat the latter three as diagnostic only.
- Because HT precision remains ~0.46, positive calls still need confirmation regardless of objective.

## Artifacts
- `objective_comparison.txt` — per-objective thresholds, test metrics, and confusion matrices.
- `objective_metrics.json` — machine-readable per-objective metrics (per-class precision/recall/F1,
  supports, confusion matrices, AUC).
- Probabilities source: `../../threshold/tabpfn_subject_eval_independent_baseline/probabilities_*.csv`.
- Model context and base TabPFN independent run: [`../README.md`](../README.md).
---
*Base model: `xgboost_subject_eval_dependent_baseline` (0.5 cut) · metrics from `objective_comparison.txt` + `objective_metrics.json` · summary auto-generated*
