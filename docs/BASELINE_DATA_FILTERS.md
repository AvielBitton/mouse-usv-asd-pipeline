# Official Baseline Data Filters

This document defines the **official training baseline** for all model runs in
the training matrix (Issue #42). Every training scenario (full cohort, classic
BALB/C, mixed strain) and every model type (XGBoost, TabPFN, BiLSTM, 1D-CNN,
Transformer) must use the baseline-filtered dataset as its data source.

---

## Data source

**Input:**
`outputs/external/input/segmentation_classification_all_data.xlsx`
(the externally aggregated segmentation workbook with correct individual genotyping)

**Output — tabular pipeline:**
`outputs/external/aggregated/all_data_external_baseline.csv`
(48-column numeric aggregate, one row per recording)

**Output — sequence pipeline:**
`outputs/external/aggregated/all_data_external_baseline.xlsx`
(syllable-level rows after baseline filtering, used directly by sequence models)

Both outputs are generated unconditionally every time the preprocessing pipeline
runs (`src/preprocessing/run_pipeline.py`).

---

## Filter definitions

Filters are applied in order to every syllable-level row before aggregation.

| # | Filter name | Column(s) | Removed when |
|---|-------------|-----------|--------------|
| 1 | `invalid_genotype` | `Mother Genotype`, `Offspring Genotype` | Either genotype is not `WT` or `HET` after `HT`→`HET` normalization (e.g. `UNK`, `NAN`, empty) |
| 2 | `invalid_sex` | `Sex` | Value is not `M` or `F` (e.g. `U`, missing) |
| 3 | `noise` | `Noise` | `Noise == 1` (syllable where start frequency equals end frequency) |
| 4 | `supplement_offspring` | `Supplement (Offspring)`, `Name` | Pup belongs to a litter flagged as supplement offspring |

**Note:** Filter 1 (`invalid_genotype`) is always applied to every external
aggregate, not just the baseline. Filters 2–4 are the additional layer that
defines the baseline.

---

## Implementation

All four filters are applied inside
`src/preprocessing/steps/extract_features.py`:

- `drop_non_binary_genotype_rows_for_external` — filter 1, always runs
- `apply_single_external_filter("invalid_sex", ...)` — filter 2
- `apply_single_external_filter("noise", ...)` — filter 3
- `apply_single_external_filter("supplement_offspring", ...)` — filter 4

The combined baseline export is triggered unconditionally in
`run_external_aggregated_feature_extraction` via the `BASELINE_FILTERS` tuple.
Row counts before and after each filter step are written to the preprocessing log.

---

## Usage

### Tabular pipeline

```bash
python src/classification/tabular/train_classifier.py --baseline
python src/classification/tabular/train_classifier.py --baseline --independent
python src/classification/tabular/train_classifier.py --baseline --independent --strain 1
```

### Sequence pipeline

```bash
python src/classification/neural_networks/sequence_pipeline.py --baseline
python src/classification/neural_networks/sequence_pipeline.py --baseline --independent
python src/classification/neural_networks/sequence_pipeline.py --baseline --model transformer --independent
```

`--baseline` takes precedence over `--external` (tabular) and `--data-path`
(sequence). It is overridden only by an explicit `--data-csv` / `--data-path`
when those are set intentionally for ablation runs.

---

## Versioning

When the source workbook (`segmentation_classification_all_data.xlsx`) is
updated or regenerated, rerun the full preprocessing pipeline to refresh
the baseline exports. Record the date and input file hash in run metadata
so that all training results remain traceable.
