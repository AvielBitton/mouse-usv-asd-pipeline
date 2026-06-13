# CLI Flags Reference

Central reference for command-line flags used by the preprocessing and
classification pipelines.

## Preprocessing Pipeline

Entrypoint:

```bash
python src/preprocessing/run_pipeline.py
```

| Flag | Status | Description |
|---|---|---|
| `--metadata-file FILE` | Available | Process one metadata workbook instead of all metadata files. The file must exist in the metadata directory. |
| `--external-filter FILTER` | Available | Generate an additional filtered external aggregate. Repeat the flag to create multiple single-filter variants. |

Supported `--external-filter` values:

| Filter | Removes rows where |
|---|---|
| `invalid_sex` | Sex is missing or not a valid `M` / `F` value. |
| `noise` | The derived `Noise` column marks the syllable as noise. |
| `supplement_offspring` | The pup is marked as supplement offspring. |
| `undefined_syllable` | `Syllable number` is `10` / undefined. |

Example:

```bash
python src/preprocessing/run_pipeline.py \
  --external-filter noise \
  --external-filter supplement_offspring
```

### Baseline outputs (always generated)

Every preprocessing run unconditionally produces the official baseline aggregate
in addition to the main external aggregate:

| Output file | Description |
|---|---|
| `outputs/external/aggregated/tabular/all_data_external_main.csv` | All external data after genotype binary filter only. |
| `outputs/external/aggregated/tabular/all_data_external_baseline.csv` | Official baseline: genotype + `invalid_sex` + `supplement_offspring` removed; **`Noise == 1` rows retained**. Use for all training-matrix runs. |
| `outputs/external/aggregated/sequence/all_data_external_baseline.xlsx` | Syllable-level baseline export used by sequence models. |

See `docs/BASELINE_DATA_FILTERS.md` for the full filter specification.

## Tabular Classifier

Entrypoint:

```bash
python src/classification/tabular/train_classifier.py
```

| Flag | Status | Description |
|---|---|---|
| `--model MODEL` | Available | Select the tabular model. Supported models depend on the current branch; current work includes `xgboost` and `tabpfn`. |
| `--baseline` | Available | **Recommended for all training-matrix runs.** Use the official baseline dataset (`all_data_external_baseline.csv`). Takes precedence over `--external`; overridden only by `--data-csv`. |
| `--external` | Available | Use the externally validated aggregate (`all_data_external_main.csv`) without the full baseline filters. Prefer `--baseline` for all Issue #42 runs. |
| `--data-csv PATH` | Available | Train on an explicit 48-column aggregate CSV. Overrides `--baseline` and `--external`. Useful for custom filtered variants. |
| `--group-split` | Available | Use subject-independent evaluation by splitting train/validation/test by mouse identity. |
| `--independent` | Available | Preferred alias for `--group-split`. Use this name in new commands and docs. |
| `--strain {1,2}` | Available | Filter rows by `pup_strain` before splitting and training. Drops `pup_strain` from features (constant). Default output under `results/tabular_models/strain/`. |
| `--results-dir DIR` | Available | Write results to an explicit output directory instead of the default path. |

Cohort strain runs (Issue #47 — use with `--baseline`):

```bash
# Scenario 2 — Classic BALB/C (pup_strain=2)
python src/classification/tabular/train_classifier.py --baseline --strain 2 --model xgboost
python src/classification/tabular/train_classifier.py --baseline --strain 2 --independent --model xgboost

# Scenario 3 — Mixed (pup_strain=1)
python src/classification/tabular/train_classifier.py --baseline --strain 1 --model xgboost
python src/classification/tabular/train_classifier.py --baseline --strain 1 --independent --model xgboost
```

See [`COHORT_DEFINITIONS.md`](COHORT_DEFINITIONS.md) for the full 3×2 matrix.

Default output layout for baseline strain runs:

```text
results/tabular_models/strain/
  xgboost_strain1_subject_eval_dependent_baseline/
  xgboost_strain1_subject_eval_independent_baseline/
  xgboost_strain2_subject_eval_dependent_baseline/
  xgboost_strain2_subject_eval_independent_baseline/
```

## Sequence Models

Entrypoint:

```bash
python src/classification/neural_networks/sequence_pipeline.py
```

| Flag | Status | Description |
|---|---|---|
| `--model MODEL` | Available | Select the sequence model architecture. Default is `bilstm`. |
| `--baseline` | Available | **Recommended for all training-matrix runs.** Use the official baseline dataset (`all_data_external_baseline.xlsx`). Takes precedence over `--data-path`. |
| `--group-split` | Available | Use subject-independent evaluation by splitting by mouse identity. |
| `--independent` | Available | Preferred alias for `--group-split`. |
| `--data-path PATH` | Available | Path to the syllable-level Excel input file. Overridden by `--baseline`. |
| `--max-seq-len N` | Available | Maximum sequence length. Default is `256`. |
| `--epochs N` | Available | Number of training epochs. Default is `100`. |
| `--batch-size N` | Available | Training batch size. Default is `32`. |
| `--lr FLOAT` | Available | Learning rate. Default is `1e-3`. |
| `--results-dir DIR` | Available | Write results to an explicit output directory. |

