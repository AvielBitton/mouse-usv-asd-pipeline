# Cohort definitions (Issue #47 / #42)

Official **year/strain cohorts** for the training matrix. All runs use the baseline aggregate (`--baseline`) unless noted.

**Encoding:** `WT=0`, `HT/HET=1` in CSV; `pup_strain` is numeric strain for cohort filtering.

| Scenario | Years | Strain (text in input) | `pup_strain` | CLI filter |
|----------|-------|------------------------|--------------|------------|
| 1 — Full | All (post-baseline) | All | 1 + 2 | `--baseline` only |
| 2 — Classic BALB/C | 2015, 2018 | `BALB/C` | **2** | `--baseline --strain 2` |
| 3 — Mixed | 2022, 2023, 2024 | `BALB/C+BLACK/C57` | **1** | `--baseline --strain 1` |

**Code references:** `STRAIN_1_YEARS` and `strain_from_year()` in [`src/preprocessing/utils/io_utils.py`](../src/preprocessing/utils/io_utils.py); text→numeric in [`extract_features.py`](../src/preprocessing/steps/extract_features.py).

**Verification:** `scripts/verify_cohort_encoding.py` → `outputs/reports/cohort_verification/`

---

## Split modes (every scenario)

| Mode | Flag | Use for |
|------|------|---------|
| Dependent | *(default)* | Row-level random split; optimistic (mouse overlap) |
| Independent | `--independent` | Group split by `mouse_idx`; primary generalization metric |

---

## Tabular commands (XGBoost)

Run from repo root:

```bash
# Scenario 1 — Full (Phase A / #46)
python src/classification/tabular/train_classifier.py --baseline --model xgboost
python src/classification/tabular/train_classifier.py --baseline --independent --model xgboost

# Scenario 2 — Classic BALB/C
python src/classification/tabular/train_classifier.py --baseline --strain 2 --model xgboost
python src/classification/tabular/train_classifier.py --baseline --strain 2 --independent --model xgboost

# Scenario 3 — Mixed
python src/classification/tabular/train_classifier.py --baseline --strain 1 --model xgboost
python src/classification/tabular/train_classifier.py --baseline --strain 1 --independent --model xgboost
```

### Expected results directories

| Scenario | Split | Path |
|----------|-------|------|
| 1 Full | dependent | `results/tabular_models/xgboost_subject_eval_dependent_baseline/` |
| 1 Full | independent | `results/tabular_models/xgboost_subject_eval_independent_baseline/` |
| 2 Classic | dependent | `results/tabular_models/strain/xgboost_strain2_subject_eval_dependent_baseline/` |
| 2 Classic | independent | `results/tabular_models/strain/xgboost_strain2_subject_eval_independent_baseline/` |
| 3 Mixed | dependent | `results/tabular_models/strain/xgboost_strain1_subject_eval_dependent_baseline/` |
| 3 Mixed | independent | `results/tabular_models/strain/xgboost_strain1_subject_eval_independent_baseline/` |

---

## Baseline pool (recording level)

| `pup_strain` | Cohort | Recordings (2026-05-16) |
|--------------|--------|-------------------------|
| 1 | Mixed (2022–2024) | 7,323 |
| 2 | Classic BALB/C (2015/2018) | 4,651 |
| **Total** | Full | **11,974** |

No separate per-cohort CSV files — filter at train time with `--strain`.

---

## Sequence models

Cohort runs for BiLSTM / 1D-CNN are **deferred** (Phase C). Use the same baseline syllable workbook and apply strain filtering when sequence support is added.

---

## Related docs

- [`BASELINE_DATA_FILTERS.md`](BASELINE_DATA_FILTERS.md) — Phase A filters
- [`BASELINE_DATA_MANIFEST.md`](BASELINE_DATA_MANIFEST.md) — row counts and provenance
- [`EXECUTIVE_REPORTING.md`](EXECUTIVE_REPORTING.md) — matrix reporting template
- [`CLI_Flags.md`](CLI_Flags.md) — all flags
