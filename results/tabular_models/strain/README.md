# `strain/` — per-cohort tabular runs (strain1 vs strain2)

Index of the 12 tabular runs trained on a **single strain cohort** instead of the pooled corpus, to
test whether the two cohorts behave differently. Each child folder has its own `README.md` with the full
summary, results, and Δ vs the base model (`results/tabular_models/xgboost_subject_eval_dependent_baseline`).

## Cohorts
- **strain1** — years **2022–2024**, mixed `BALB/C+C57` background (the newer litters).
- **strain2** — years **2015/2018**, pure `BALB/c` (the classic published cohort).

Matrix: 3 models (`xgboost`, `xgboost_tuned_dependent`, `tabpfn`) × 2 strains × 2 eval splits
(dependent / independent). All on the official `--baseline` data (Issue #46 filters + April-2026 HET→WT
correction).

## Runs at a glance (test set)
| Run | Acc | Weighted F1 | HT F1 |
|---|---|---|---|
| [xgboost_strain1 · dependent](xgboost_strain1_subject_eval_dependent_baseline/) | 0.774 | 0.791 | 0.657 |
| [xgboost_strain1 · independent](xgboost_strain1_subject_eval_independent_baseline/) | 0.903 | 0.909 | 0.753 |
| [xgboost_strain2 · dependent](xgboost_strain2_subject_eval_dependent_baseline/) | 0.748 | 0.759 | 0.642 |
| [xgboost_strain2 · independent](xgboost_strain2_subject_eval_independent_baseline/) | 0.657 | 0.609 | 0.122 |
| [xgboost_tuned_dependent_strain1 · dependent](xgboost_tuned_dependent_strain1_subject_eval_dependent_baseline/) | 0.789 | 0.802 | 0.649 |
| [xgboost_tuned_dependent_strain1 · independent](xgboost_tuned_dependent_strain1_subject_eval_independent_baseline/) | 0.899 | 0.903 | 0.729 |
| [xgboost_tuned_dependent_strain2 · dependent](xgboost_tuned_dependent_strain2_subject_eval_dependent_baseline/) | 0.783 | 0.790 | 0.657 |
| [xgboost_tuned_dependent_strain2 · independent](xgboost_tuned_dependent_strain2_subject_eval_independent_baseline/) | 0.653 | 0.597 | 0.081 |
| [tabpfn_strain1 · dependent](tabpfn_strain1_subject_eval_dependent_baseline/) | 0.785 | 0.801 | 0.680 |
| [tabpfn_strain1 · independent](tabpfn_strain1_subject_eval_independent_baseline/) | 0.897 | 0.905 | 0.749 |
| [tabpfn_strain2 · dependent](tabpfn_strain2_subject_eval_dependent_baseline/) | 0.801 | 0.809 | 0.703 |
| [tabpfn_strain2 · independent](tabpfn_strain2_subject_eval_independent_baseline/) | 0.654 | 0.659 | 0.388 |

## Key takeaways
- **strain1 independent is the standout** (~0.90 acc / 0.73–0.75 HT F1 across all three models) — higher
  than its own dependent split, the opposite of the usual dependent→independent drop. Read it cautiously:
  it is a single favourable group split on the larger, more homogeneous newer cohort, not necessarily a
  robust generalization gain.
- **strain2 independent collapses** (acc ~0.65, HT F1 0.08–0.39): the smaller 2015/2018 cohort has too
  few held-out HT mice for a leak-free split — TabPFN (HT F1 0.388) degrades least, the tuned XGBoost
  (0.081) most.
- **Dependent splits are consistent across strains** (~0.75–0.80 acc), in line with the pooled base model.
- Model choice matters little within a cohort/split; the **cohort × split interaction** dominates —
  evidence the two strains are not interchangeable and should not be pooled blindly.

## Regenerate
```bash
python src/classification/tabular/train_classifier.py --baseline --strain {1,2} [--independent] --model {xgboost,xgboost_tuned_dependent,tabpfn}
```
