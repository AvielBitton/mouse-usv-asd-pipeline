# xgboost_subject_eval_independent_baseline — XGBoost · subject-independent · threshold-objective sweep

> Re-derives the XGBoost decision threshold under four objectives on the **leak-free** (by-mouse) split — same model, no retraining.

## Overview
- **Model:** XGBoost (untuned legacy recipe), the identical fitted model from the
  subject-independent base run — only the decision threshold is changed.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`), so no
  mouse appears in two sets. Honest "generalize to unseen mice" setting (harder than the dependent base
  model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 2,139 recordings (WT 1,560 / HT 579); validation labels WT 1,788 / HT 530.
- **What was adapted vs the base model:** decision-threshold objective selection only — no feature,
  model, or split change. Five operating points are scored: the 0.5 default plus four thresholds picked
  from **saved validation probabilities** under `youden`, `f1`, `target_recall` (HT-recall floor 0.80),
  and `balanced`. **Recommended objective for this independent split: `target_recall` (thr 0.439).**

## Results (test set)
Per-objective metrics on test (AUC fixed at 0.770; same model throughout):
```
Objective       thr     acc  balacc   HTrec  HTprec    HTf1   WTrec
@0.5          0.500   0.692   0.678   0.646   0.452   0.532   0.710
youden        0.128   0.705   0.797   0.998   0.478   0.647   0.596
f1            0.128   0.705   0.797   0.998   0.478   0.647   0.596
target_recall 0.439   0.704   0.728   0.779   0.472   0.588   0.676
balanced      0.086   0.704   0.796   0.998   0.477   0.646   0.594
```
Recommended `target_recall` confusion matrix (rows = true, cols = pred): `[[WT→WT 1055, WT→HT 505], [HT→WT 128, HT→HT 451]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
Recommended objective (`target_recall`, thr 0.439) vs base (0.5 cut):
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.704 | 0.733 | −0.029 |
| Weighted F1 | 0.720 | 0.749 | −0.029 |
| WT F1 | 0.769 | 0.785 | −0.016 |
| HT F1 | 0.588 | 0.649 | −0.061 |
| HT recall | 0.779 | 0.940 | −0.161 |
| HT precision | 0.472 | 0.496 | −0.024 |

See the parent sweep [`../README.md`](../README.md) for the cross-run objective comparison.

## Key insights
- **`youden`, `f1`, and `balanced` all collapse to a near-degenerate operating point** (thr 0.086–0.128):
  HT recall 0.998 with only 1 of 579 HT misses, but WT recall drops to ~0.59 — the model labels HT for
  almost everyone. They post the best balanced accuracy (~0.797) by sacrificing the majority class.
- **`target_recall` (thr 0.439) is the only controlled point:** HT recall 0.779 (near the 0.80 floor),
  WT recall 0.676, balanced accuracy 0.728 — a genuine trade rather than a collapse.
- Even at the recommended cut the run trails the dependent base on every metric (HT recall −0.161,
  HT F1 −0.061), reflecting the honest cost of unseen mice; the base's strong HT recall (0.940) is partly
  a leakage artifact of the dependent split.
- Class separation stays weak under the leak-free split — **HT precision ≈ 0.47** at every objective
  (validation AUC only 0.691), so roughly half of HT calls are false positives regardless of threshold.

## Recommendations
- Use `target_recall` (thr 0.439) for this independent split — the other three objectives are
  effectively degenerate (predict HT for nearly all mice) and not deployable.
- Treat any HT prediction as low-confidence (precision ≈ 0.47) and confirm before acting.

## Artifacts
- `objective_comparison.txt` — human-readable per-objective table + test confusion matrices.
- `objective_metrics.json` — full per-objective metrics, thresholds, and diagnostics.
- Source probabilities: `../../threshold/xgboost_subject_eval_independent_baseline/probabilities_*.csv`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `objective_metrics.json` + `objective_comparison.txt` · summary auto-generated*
