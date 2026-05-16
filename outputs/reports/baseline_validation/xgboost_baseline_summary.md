# XGBoost baseline validation summary

**Date:** 2026-05-16  
**Branch:** `feature/46-baseline-data-filters`  
**Model:** XGBoost  
**Data:** `outputs/external/aggregated/all_data_external_baseline.csv` (`--baseline`)  
**Encoding:** `WT=0`, `HT/HET=1` (positive class = HT)  
**Class balance:** `both_dynamic` — `sample_weight=balanced` + `scale_pos_weight=n_WT/n_HT` on train

---

## A. Static baseline data

| Field | Value |
|-------|--------|
| Input | `outputs/external/input/segmentation_classification_all_data.{xlsx,csv}` (Issue #34 + Session fix) |
| Aggregation | `scripts/run_external_aggregation.py` |
| Baseline recordings | **11,974** |
| Human-readable CSV | `all_data_external_baseline_labeled.csv` (`pup_gen` / `mother_gen` as WT/HT) |

See [`docs/BASELINE_DATA_MANIFEST.md`](../../../docs/BASELINE_DATA_MANIFEST.md).

---

## B. Run configuration

| Field | Dependent | Independent |
|-------|-----------|-------------|
| CLI | `--baseline --model xgboost` | `--baseline --model xgboost --independent` |
| Split | Random row-level (mouse overlap) | Group by `mouse_idx` (disjoint mice) |
| Train / val / test | 7,184 / 2,395 / 2,395 | 6,893 / 2,595 / 2,486 |
| `scale_pos_weight` (train) | 3.11 | 2.93 |

---

## C. Test metrics

| Metric | Dependent | Independent |
|--------|-----------|-------------|
| Test accuracy | **0.71** | **0.58** |
| HT recall | **0.99** | **0.98** |
| HT precision | 0.48 | 0.42 |
| HT F1 | 0.65 | 0.58 |
| WT recall | 0.61 | 0.42 |
| WT precision | 0.99 | 0.98 |
| Test support (WT / HT) | 1,756 / 639 | 1,743 / 743 |

**Confusion matrix (test counts):**

| | | Pred HT | Pred WT |
|--|--|---------|---------|
| **Dependent** | True WT | 681 | 1,075 |
| | True HT | 7 | 632 |
| **Independent** | True WT | 1,017 | 726 |
| | True HT | 17 | 726 |

Plots/logs: `results/tabular_models/xgboost_subject_eval_*_baseline/`

**Note:** Dependent metrics are optimistic (same mice in train and test). Prefer **independent** for generalization. High HT recall trades off many WT recordings classified as HT.

---

## D. Next steps

- TabPFN + sequence with `--baseline`: Issue #48
- Threshold tuning: Issue #29
