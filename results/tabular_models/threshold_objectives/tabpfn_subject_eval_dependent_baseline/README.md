# tabpfn_subject_eval_dependent_baseline — TabPFN · subject-dependent · threshold objectives

> Re-derives the decision threshold for the dependent TabPFN run under four objectives — **same model, no retraining**.

## Overview
- **Model:** TabPFN (prior-data-fitted transformer; no hyperparameter tuning; validation merged into
  train). Identical fitted model as the dependent base TabPFN run.
- **Evaluation split:** subject-dependent — train/val/test split by **row/session** (same mouse can
  appear in train and test). Optimistic vs the leak-free independent setting.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). Val labels
  WT=1865 / HT=600; test support WT=1818 / HT=647. Val AUC 0.912, test AUC 0.908.
- **What was adapted vs the base model:** decision-threshold **objective selection only** — the cut is
  re-derived from saved validation probabilities under youden / f1 / target_recall / balanced, plus the
  0.5 default. No weights, features, or training change.
- **Recommended objective:** **f1** for dependent splits (target_recall is the pick for independent
  splits). Here f1 and target_recall land on the **same threshold 0.617** because the f1-optimal cut
  already satisfies the 0.80 HT-recall floor.

## Results (test set)
Per-objective performance at each derived threshold (AUC is threshold-invariant at 0.908):

| Objective | thr | Acc | BalAcc | HT rec | HT prec | HT F1 | WT rec |
|---|---|---|---|---|---|---|---|
| @0.5 | 0.500 | 0.783 | 0.828 | 0.921 | 0.552 | 0.691 | 0.734 |
| youden | 0.454 | 0.766 | 0.822 | 0.938 | 0.531 | 0.678 | 0.705 |
| **f1** (recommended) | 0.617 | **0.819** | 0.817 | 0.811 | 0.619 | **0.702** | 0.822 |
| target_recall | 0.617 | 0.819 | 0.817 | 0.811 | 0.619 | 0.702 | 0.822 |
| balanced | 0.453 | 0.766 | 0.821 | 0.938 | 0.531 | 0.678 | 0.705 |

f1 confusion matrix (rows = true, cols = pred): `[[WT→WT 1495, WT→HT 323], [HT→WT 122, HT→HT 525]]`.
target_recall floor = HT recall ≥ 0.80.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
Recommended **f1** objective (thr 0.617) vs base at its 0.5 cut:

| Metric | This run (f1) | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.819 | 0.733 | +0.086 |
| Weighted F1 | 0.826 | 0.749 | +0.077 |
| WT F1 | 0.870 | 0.785 | +0.085 |
| HT F1 | 0.702 | 0.649 | +0.053 |
| HT recall | 0.811 | 0.940 | −0.129 |
| HT precision | 0.619 | 0.496 | +0.123 |

## Key insights
- Raising the cut to **0.617** trades minority recall for balance: HT recall drops to 0.811 (−0.129 vs
  base) but HT **precision climbs to 0.619** (+0.123) — far fewer false ASD-model calls (483→323 WT
  misfires at default, vs base's recall-heavy 0.5 operating point).
- The f1 cut beats the base model on every aggregate metric — accuracy +0.086, weighted F1 +0.077,
  HT F1 +0.053 — while keeping HT recall above the 0.80 floor; this is the strongest dependent operating
  point in the threshold sweep.
- youden and balanced collapse to the recall-greedy end (thr ≈0.45, HT recall 0.938, HT precision 0.531),
  essentially reproducing the base model's behavior and adding nothing over the 0.5 default.
- All numbers are threshold re-reads of one fixed TabPFN model (test AUC 0.908) — the gains are pure
  operating-point selection, not better discrimination.

## Recommendations
- Ship the **f1 threshold (0.617)** for dependent-split deployment: best balance of HT recall (0.811)
  and precision (0.619). Avoid youden/balanced here — they only inflate false positives.
- For honest new-mouse estimates use the independent run with `target_recall`; see `../README.md` for the
  cross-run objective summary (`summary_objectives.txt`).

## Artifacts
- `objective_comparison.txt` — per-objective thresholds, test metrics, and confusion matrices (table source).
- `objective_metrics.json` — full per-objective per-class precision/recall/F1, support, AUC, thresholds, diagnostics.
- Probabilities source: `results/tabular_models/threshold/tabpfn_subject_eval_dependent_baseline/probabilities_*.csv` (no model file re-saved; thresholds re-derived).
- Cross-run rollup: `../summary_objectives.txt`, `../summary_objectives.csv`, `../README.md`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `objective_comparison.txt` + `objective_metrics.json` · summary auto-generated*
