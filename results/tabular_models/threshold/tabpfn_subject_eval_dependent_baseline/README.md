# tabpfn_subject_eval_dependent_baseline — TabPFN · subject-dependent · threshold (Youden)

> TabPFN on the official baseline data (subject-dependent split), with a **tuned decision threshold** (Youden J) replacing the default 0.5 cut — no retraining.

## Overview
- **Model:** TabPFN (prior-data-fitted transformer; no hyperparameter tuning).
- **Evaluation split:** subject-dependent — train/val/test split **at the row level** (random), so the
  same mouse appears across sets (train/test share 105 mice). Leaky/optimistic, matching the base model.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 2,465 recordings (WT 73.8% / HT 26.2%).
- **What was adapted vs the base model:** a single lever — **decision-threshold tuning (Youden J)** on
  top of an already-trained TabPFN. Only the 0.5 cut is replaced by a threshold chosen from **leak-free
  validation probabilities**; the model is not retrained. Here TabPFN's val set is held **out** (not
  merged into train) so its probabilities stay leak-free for threshold derivation — this run trains on
  ~60% of the data vs the 80% of the non-threshold TabPFN run, so the @0.5 numbers differ slightly.
- See the curated parent summary at [`../README.md`](../README.md).

## Results (test set)
Tuned threshold = **0.4540** (Youden J, from validation). Val AUC **0.912**, test AUC **0.908**
(threshold-independent).

| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.970 | 0.531 | — |
| Recall | 0.705 | 0.938 | — |
| F1 | 0.817 | 0.678 | weighted **0.780** |
| Accuracy | | | **0.766** (train 0.866) |

Confusion matrix @tuned (rows = true, cols = pred): `[[WT→WT 1282, WT→HT 536], [HT→WT 40, HT→HT 607]]`.

**0.5 vs tuned (0.4540) on the test set:**
| Metric | @0.5 | @tuned | Δ |
|---|---|---|---|
| Accuracy | 0.783 | 0.766 | −0.017 |
| Balanced accuracy | 0.828 | 0.822 | −0.006 |
| HT recall | 0.921 | 0.938 | +0.017 |
| HT precision | 0.552 | 0.531 | −0.021 |
| HT F1 | 0.691 | 0.678 | −0.012 |
| WT recall | 0.734 | 0.705 | −0.029 |
| WT precision | 0.963 | 0.970 | +0.007 |
| WT F1 | 0.833 | 0.817 | −0.017 |

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run (@tuned) | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.766 | 0.733 | +0.033 |
| Weighted F1 | 0.780 | 0.749 | +0.031 |
| WT F1 | 0.817 | 0.785 | +0.032 |
| HT F1 | 0.678 | 0.649 | +0.029 |
| HT recall | 0.938 | 0.940 | −0.002 |
| HT precision | 0.531 | 0.496 | +0.035 |

*Base model is at its default 0.5 cut; this run is at the tuned 0.4540 threshold.*

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- TabPFN beats the XGBoost base on every headline metric: **+0.033 accuracy, +0.031 weighted F1**, while
  matching HT recall (0.938 vs 0.940) — so the minority class is caught just as often, with better
  precision (0.531 vs 0.496) and far fewer WT false positives.
- Youden tuning here **lowers** the cut (0.4540 < 0.5), trading a bit of accuracy (−0.017) and WT recall
  (−0.029) for +0.017 HT recall. The model was already HT-aggressive at 0.5; the tuned point pushes
  slightly further toward catching positives.
- AUC is strong (test **0.908**), so the model ranks WT vs HT well; the limiting factor is HT precision
  (~0.53 — about half of HT calls are false positives), which threshold moves cannot fix.
- Train 0.866 vs test 0.766 (0.10 gap) is modest for a leaky dependent split — but remember this split is
  optimistic; use the independent runs for honest new-mouse estimates.

## Recommendations
- The default 0.5 cut already gives higher accuracy (0.783) and balanced accuracy (0.828) than the tuned
  point; **Youden buys little here** (+0.017 HT recall for −0.017 accuracy). Prefer 0.5 unless maximizing
  HT recall is the explicit goal.
- For a controlled HT-recall operating point, see the objective sweep in
  [`../../threshold_objectives/`](../../threshold_objectives/) (`f1` / `target_recall` ≈ 0.6171 here trade
  recall for precision).

## Artifacts
- `plots/roc_curve.png` — ROC (test AUC 0.908). `plots/conf_matrix_thr0.5.png`,
  `plots/conf_matrix_thr_tuned.png` — confusion matrices at the two cuts.
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — overall + per-strain confusion matrices.
- `threshold_report.txt`, `threshold_metrics.json` — tuned threshold, candidate cuts, val/test AUC,
  @0.5-vs-@tuned metrics. `probabilities_val.csv`, `probabilities_test.csv` — raw scores.
- `model/tabpfn_model.pkl` — fitted TabPFN. `logs/out.txt` — flags, split info, class balance.
- Metrics source: `threshold_metrics.json` + `threshold_report.txt`; `comparison_vs_baseline.txt` (run column only).
---
*Base model: `xgboost_subject_eval_dependent_baseline` (default 0.5 cut) · metrics from `threshold_metrics.json` + `threshold_report.txt` · summary auto-generated*
