# XGBoost baseline validation summary

**Date:** 2026-05-16  
**Git SHA:** `e75c998` (branch `feature/46-baseline-data-filters`)  
**Model:** XGBoost  
**Data:** `outputs/external/aggregated/all_data_external_baseline.csv` (`--baseline`)

---

## A. Static baseline data (from manifest)

| Field | Value |
|-------|--------|
| Input provenance | Commit [`791aa05`](https://github.com/AvielBitton/mouse-usv-asd-pipeline/commit/791aa05ac4b89f2de69909fcb09af25964902e1f); Session 0→1 (919 rows); Issue #34 validated |
| Syllable rows (raw → baseline) | 125,576 → 102,035 |
| Recording rows (baseline CSV) | **11,974** |
| Filters | invalid_genotype, invalid_sex, noise, supplement_offspring |
| Cohort | Full (all years in baseline file) |
| Threshold | **0.5 only** (tuned thresholds pending Issue #29) |

Full counts: [`docs/BASELINE_DATA_MANIFEST.md`](../../../docs/BASELINE_DATA_MANIFEST.md)

---

## B. Run configuration

| Field | Dependent | Independent |
|-------|-----------|-------------|
| Scenario ID | `C1_full_dependent` | `C1_full_independent` |
| CLI | `--baseline --model xgboost` | `--baseline --model xgboost --independent` |
| Split strategy | Random row-level | Group-aware by `mouse_idx` |
| Train / val / test rows | 7,184 / 2,395 / 2,395 | 7,412 / 2,314 / 2,248 |
| Mice in split | Overlap (see warning) | 63 train / 21 val / 22 test (disjoint) |
| Results dir | `results/tabular_models/xgboost_subject_eval_dependent_baseline/` | `results/tabular_models/xgboost_subject_eval_independent_baseline/` |

**Dependent split warning:** train/val/test share mice (104–105 overlapping) — metrics are optimistic.

---

## C. Test metrics

| Metric | Dependent | Independent |
|--------|-----------|-------------|
| Train accuracy | 0.756 | 0.790 |
| Test accuracy | **0.729** | **0.486** |
| Macro avg recall (test) | 0.81 | 0.63 |
| HT (class 0) precision | 0.48 | 0.26 |
| HT (class 0) recall | **0.97** | **0.88** |
| HT (class 0) F1 | 0.64 | 0.40 |
| WT (class 1) precision | 0.98 | 0.93 |
| WT (class 1) recall | 0.65 | 0.39 |
| WT (class 1) F1 | 0.78 | 0.55 |
| Test support (HT / WT) | 609 / 1,786 | 438 / 1,810 |

**Confusion matrix (test counts):**

| | | Pred HT | Pred WT |
|--|--|---------|---------|
| **Dependent** | True HT | 590 | 19 |
| | True WT | 631 | 1,155 |
| **Independent** | True HT | 384 | 54 |
| | True WT | 1,101 | 709 |

Plots: `plots/confusionmatrix.png`, `plots/feature_importance_1.png` in each results folder.

---

## D. Comparison (dependent vs independent)

On the **same baseline data** (11,974 recordings):

- **Dependent** test accuracy is much higher (0.73 vs 0.49) because the same mice appear in train and test (leakage).
- **HT recall** stays high in both splits (0.97 dependent, 0.88 independent) — model finds most HT syllable-aggregated recordings.
- **WT recall** drops sharply on independent (0.39 vs 0.65) — generalization to unseen mice is weaker for the majority class.
- **Independent** results are the appropriate estimate for mouse-level generalization; dependent is an optimistic upper bound.

---

## E. Next steps

- TabPFN + sequence models: Issue #48 / follow-up runs with `--baseline`
- Threshold tuning (0.5 vs tuned): Issue #29, #51
