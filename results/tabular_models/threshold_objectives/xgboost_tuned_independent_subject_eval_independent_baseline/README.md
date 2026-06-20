# xgboost_tuned_independent_subject_eval_independent_baseline — XGBoost (tuned) · subject-independent · threshold objectives

> Re-derive the decision threshold under four objectives from saved validation probabilities — same tuned model, no retraining.

## Overview
- **Model:** XGBoost with the independent-tuned hyperparameters (200-trial random search; heavily
  regularized/shallow recipe), evaluated **leak-free** (train/val/test split **by mouse**,
  `--independent`), so no mouse appears in two sets — the honest "generalize to unseen mice" setting.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 2,139 recordings (WT 1,560 / HT 579 ≈ 27.1% HT); validation WT 1,788 / HT 530.
- **What was adapted vs the base model:** **decision-threshold objective selection only** — identical
  fitted model, the cut is re-derived from saved validation probabilities under four objectives
  (`youden`, `f1`, `target_recall`, `balanced`) plus the 0.5 default. Val AUC 0.641, test AUC 0.753.
- **Recommended objective:** for **independent** splits, `target_recall` (HT-recall floor 0.80). Note the
  weak validation signal (AUC 0.641) pushed its chosen threshold to 0.523 — *above* the 0.5 default — so
  on test it actually **lowers** HT recall to 0.731 rather than hitting the 0.80 floor.

## Results (test set)
| Objective | thr | acc | bal-acc | HT rec | HT prec | HT F1 | WT rec |
|---|---|---|---|---|---|---|---|
| @0.5 (default) | 0.500 | 0.695 | 0.725 | 0.791 | 0.463 | 0.584 | 0.660 |
| youden | 0.288 | 0.704 | 0.797 | **1.000** | 0.477 | 0.646 | 0.594 |
| f1 | 0.288 | 0.704 | 0.797 | **1.000** | 0.477 | 0.646 | 0.594 |
| target_recall *(rec.)* | 0.523 | 0.694 | 0.706 | 0.731 | 0.459 | 0.564 | 0.681 |
| balanced | 0.223 | 0.704 | 0.797 | **1.000** | 0.477 | 0.646 | 0.594 |

youden / f1 / balanced all collapse to the same operating point (**HT recall 1.000, WT recall 0.594** —
every HT caught at the cost of 634 false positives): `[[WT→WT 926, WT→HT 634], [HT→WT 0, HT→HT 579]]`.
target_recall confusion matrix: `[[1062, 498], [156, 423]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
Recommended objective (`target_recall`, thr 0.523) vs base (at the 0.5 cut):
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.694 | 0.733 | −0.039 |
| Weighted F1 | 0.710 | 0.749 | −0.039 |
| WT F1 | 0.765 | 0.785 | −0.020 |
| HT F1 | 0.564 | 0.649 | −0.085 |
| HT recall | 0.731 | 0.940 | −0.209 |
| HT precision | 0.459 | 0.496 | −0.037 |

Weighted F1 = 0.765·(1560/2139) + 0.564·(579/2139) = **0.710**.

## Key insights
- Re-thresholding cannot fix a **weak ranker**: test AUC 0.753 means the score barely separates the
  classes, so every objective trades the same recall-for-precision along one flat curve. The three
  recall-maximizing objectives (youden/f1/balanced) degenerate to **HT recall 1.000 / WT recall 0.594** —
  catching all HT only by flagging 634 of 1,560 WT pups.
- The recommended `target_recall` objective **misses its own 0.80 floor on test** (lands at 0.731): the
  low-AUC validation signal placed the threshold at 0.523, slightly conservative, so it under-delivers
  recall rather than over-delivering it. The floor is honored on validation, not on held-out mice.
- Against the dependent base, this leak-free run loses across the board — HT recall −0.209, HT F1 −0.085,
  accuracy −0.039 — the expected dependent→independent penalty plus a still-poor minority class
  (HT precision ≈ 0.46, about half of HT calls are false positives at every objective).
- No objective beats the 0.5 default on overall F1; the only real choice is recall-vs-precision posture,
  not an accuracy gain.

## Recommendations
- For a maximum-recall screen, use the youden/f1/balanced cut (thr 0.288, HT recall 1.000) but treat WT
  recall 0.594 and HT precision 0.477 as the cost — positive calls need confirmation.
- Do not rely on `target_recall` to guarantee the 0.80 floor here; the AUC-0.641 validation signal is too
  weak to transfer. A stronger ranker (better features/model) is the real lever — see the sibling threshold
  and objective runs in [`../README.md`](../README.md).

## Artifacts
- `objective_comparison.txt` — per-objective thresholds, test metrics, and confusion matrices (human-readable).
- `objective_metrics.json` — same data as JSON (thresholds, per-class precision/recall/F1, support, AUC).
- Source probabilities: `results/tabular_models/threshold/xgboost_tuned_independent_subject_eval_independent_baseline/probabilities_*.csv` (no retraining).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `objective_comparison.txt` + `objective_metrics.json` · summary auto-generated*
