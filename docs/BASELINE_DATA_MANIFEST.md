# Baseline Data Manifest

Audit record for the **official external baseline** (Issue #46 / #42).  
Regenerate aggregates after any change to `outputs/external/input/` and update this file.

**Last updated:** 2026-05-16  
**Git branch (code):** `feature/46-baseline-data-filters`  
**Input source commit:** [`791aa05`](https://github.com/AvielBitton/mouse-usv-asd-pipeline/commit/791aa05ac4b89f2de69909fcb09af25964902e1f) (Issue #34 genotype/sex corrections)

---

## Input preparation

| Step | Detail |
|------|--------|
| Restored from git | `791aa05` → `outputs/external/input/segmentation_classification_all_data.xlsx` + `.csv` |
| Previous input | Moved to `outputs/external/input/backup/` |
| Session fix (in input file) | **919** syllable rows: `Session` 0 → 1 (applied 2026-05-16 before aggregation) |
| Issue #34 validation | `14164P_1C`: 985 rows, Offspring Genotype `HT`; `08146L`: 97 rows, Sex `F`, Offspring Genotype `WT` |

**Canonical input paths:**

- `outputs/external/input/segmentation_classification_all_data.xlsx`
- `outputs/external/input/segmentation_classification_all_data.csv` (synced with xlsx)

**Aggregation command:**

```bash
.venv/bin/python scripts/run_external_aggregation.py
```

(Runtime ~19 min on 2026-05-16; exit code 0.)

---

## Row counts — syllable level

Counts from input CSV after preparation; filter logic matches `extract_features.py`.

| Stage | Syllable rows | Removed | Notes |
|-------|---------------|---------|--------|
| Raw input | **125,576** | — | After 791aa05 + Session fix |
| After `invalid_genotype` | **123,807** | 1,769 | Mother/offspring must be WT or HET (HT→HET) |
| After `invalid_sex` | 120,464 | 3,343 | Sex must be M or F |
| After `noise` | 110,130 | 10,334 | `Noise == 1` |
| After `supplement_offspring` | **102,035** | 8,095 | All rows for supplement-offspring pups |
| **Baseline syllable pool** | **102,035** | **23,541** total from raw input | Used for `all_data_external_baseline.xlsx` |

`all_data_external_main` uses the post–genotype pool only (**123,807** syllable rows) before aggregation.

---

## Row counts — recording level (48-column CSV)

One row = one recording (aggregated features). No header in CSV.

| Output | Recording rows | Path |
|--------|----------------|------|
| **main** | **13,342** | `outputs/external/aggregated/all_data_external_main.csv` |
| **baseline** | **11,974** | `outputs/external/aggregated/all_data_external_baseline.csv` |
| Delta (main − baseline) | **1,368** | Fewer recordings after filters 2–4 |

Companion syllable-level workbooks:

- `outputs/external/aggregated/all_data_external_main.xlsx`
- `outputs/external/aggregated/all_data_external_baseline.xlsx`

---

## Training usage

| Pipeline | Flag | Data path |
|----------|------|-----------|
| Tabular | `--baseline` | `all_data_external_baseline.csv` |
| Sequence | `--baseline` | `all_data_external_baseline.xlsx` |

Filter definitions: [`BASELINE_DATA_FILTERS.md`](BASELINE_DATA_FILTERS.md)

---

## Machine-readable snapshot

Same numbers in [`BASELINE_DATA_MANIFEST.json`](BASELINE_DATA_MANIFEST.json) for scripts and run metadata.
