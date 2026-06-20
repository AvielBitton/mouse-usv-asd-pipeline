# tabpfn_subject_eval_independent_baseline — TabPFN · subject-independent · threshold (Youden)

> Youden-J decision threshold applied to the leak-free TabPFN independent run — no retraining, just a new cut.

## Overview
- **Model:** TabPFN (prior-data-fitted transformer; no hyperparameter tuning). In threshold mode the
  validation set is **held OUT** (not merged into train), so its probabilities are leak-free for deriving
  the cut — this run trains on ~60% of the data (7,866 rows) vs the 80% used by the non-threshold TabPFN
  run, so its @0.5 numbers differ slightly (not a regression).
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`), so no
  mouse appears in two sets. The honest "generalize to unseen mice" setting (harder than the dependent
  base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 2,139 recordings from 22 held-out mice (WT 72.9% / HT 27.1%).
- **What was adapted vs the base model:** decision-threshold tuning (Youden's J) — the 0.5 cut is replaced
  by a threshold chosen from leak-free validation probabilities. **No retraining.** See
  [`../README.md`](../README.md) for the curated threshold-folder summary.

## Results (test set)
Tuned threshold (Youden) = **0.0055**; val AUC 0.679, test AUC **0.783** (threshold-independent).

| Metric | @0.5 (default) | @tuned (0.0055) | Δ |
|---|---|---|---|
| Accuracy | 0.713 | 0.703 | −0.010 |
| Balanced accuracy | 0.662 | 0.796 | +0.134 |
| HT recall | 0.551 | 0.998 | +0.447 |
| HT precision | 0.474 | 0.477 | +0.003 |
| HT F1 | 0.510 | 0.645 | +0.136 |
| WT recall | 0.773 | 0.594 | −0.179 |
| WT precision | 0.823 | 0.999 | +0.176 |
| WT F1 | 0.797 | 0.745 | −0.052 |

Confusion matrix @0.5 (rows = true, cols = pred): `[[WT→WT 1206, WT→HT 354], [HT→WT 260, HT→HT 319]]`.
Confusion matrix @tuned: `[[WT→WT 926, WT→HT 634], [HT→WT 1, HT→HT 578]]` — 578/579 HT caught, only 1 missed.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
Comparing this run's **tuned**-threshold test metrics to the base model (base is at its default **0.5** cut).

| Metric | This run (tuned) | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.703 | 0.733 | −0.030 |
| Weighted F1 | 0.718 | 0.749 | −0.031 |
| WT F1 | 0.745 | 0.785 | −0.040 |
| HT F1 | 0.645 | 0.649 | −0.004 |
| HT recall | 0.998 | 0.940 | +0.058 |
| HT precision | 0.477 | 0.496 | −0.019 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- The Youden cut is extreme (**0.0055**): it flips this run into near-total HT detection — **HT recall 0.998**
  (1 of 579 missed), balanced accuracy jumps +0.134 (0.662 → 0.796) for almost no accuracy cost (−0.010).
- The trade-off is paid in **WT recall, which collapses to 0.594** (−0.179): 634 of 1,560 WT pups are now
  flagged HT. HT precision barely moves (0.477), so positive calls are still ~half false alarms.
- Threshold tuning recovers the recall that the leak-free split had cost the @0.5 operating point, landing
  HT F1 (0.645) essentially level with the dependent base (0.649, Δ −0.004) — but via the opposite
  precision/recall mix (high recall, low precision).
- Class separation is fundamentally weak here: **val AUC is only 0.679** (test AUC 0.783), so the cut is
  derived from a poorly-separated validation distribution, which is why such a low threshold is needed.

## Recommendations
- This tuned point is an aggressive **screening** operating mode (catch almost every ASD-model pup, accept
  many WT false positives). For a controlled balance use `target_recall` (~0.80, threshold 0.0948) — see
  [`../../threshold_objectives/`](../../threshold_objectives/) for the full objective sweep.
- Positive (HT) calls still need confirmation: HT precision ≈ 0.48 even after tuning.

## Artifacts
- `plots/roc_curve.png` — validation ROC with operating points. `plots/conf_matrix_thr0.5.png`,
  `plots/conf_matrix_thr_tuned.png` — confusion matrices at each cut.
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — overall + per-strain confusion matrices.
- `model/tabpfn_model.pkl` — fitted TabPFN (~225 MB, gitignored).
- `probabilities_val.csv` / `probabilities_test.csv` — per-sample P(HT); the val file is the leak-free
  source the threshold is derived from.
- Metrics source: `threshold_report.txt` + `threshold_metrics.json`; `logs/out.txt` — flags, split info,
  class balance.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `threshold_report.txt` + `threshold_metrics.json` · summary auto-generated*
