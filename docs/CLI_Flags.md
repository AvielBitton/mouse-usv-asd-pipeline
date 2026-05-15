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

## Tabular Classifier

Entrypoint:

```bash
python src/classification/tabular/train_classifier.py
```

| Flag | Status | Description |
|---|---|---|
| `--model MODEL` | Available | Select the tabular model. Supported models depend on the current branch; current work includes `xgboost` and `tabpfn`. |
| `--external` | Available | Use the externally validated aggregate as the preferred training source. |
| `--data-csv PATH` | Available | Train on an explicit 48-column aggregate CSV. Overrides the default selected by `--external`. Useful for filtered variants. |
| `--group-split` | Available | Use subject-independent evaluation by splitting train/validation/test by mouse identity. |
| `--independent` | Available | Preferred alias for `--group-split`. Use this name in new commands and docs. |
| `--strain {1,2}` | Available | Filter rows by `pup_strain` before splitting and training. Drops `pup_strain` from features (constant). Default output under `results/tabular_models/strain/`. |
| `--results-dir DIR` | Available | Write results to an explicit output directory instead of the default path. |

Strain runs (Issue #28):

```bash
python src/classification/tabular/train_classifier.py --external --strain 1
python src/classification/tabular/train_classifier.py --external --strain 1 --independent
python src/classification/tabular/train_classifier.py --external --strain 2
python src/classification/tabular/train_classifier.py --external --strain 2 --independent
```

Default output layout for strain runs:

```text
results/tabular_models/strain/
  xgboost_strain1_subject_eval_dependent_external/
  xgboost_strain1_subject_eval_independent_external/
  xgboost_strain2_subject_eval_dependent_external/
  xgboost_strain2_subject_eval_independent_external/
```

## Sequence Models

Entrypoint:

```bash
python src/classification/neural_networks/sequence_pipeline.py
```

| Flag | Status | Description |
|---|---|---|
| `--model MODEL` | Available | Select the sequence model architecture. Default is `bilstm`. |
| `--group-split` | Available | Use subject-independent evaluation by splitting by mouse identity. |
| `--independent` | Available | Preferred alias for `--group-split`. |
| `--data-path PATH` | Available | Path to the syllable-level Excel input file. |
| `--max-seq-len N` | Available | Maximum sequence length. Default is `256`. |
| `--epochs N` | Available | Number of training epochs. Default is `100`. |
| `--batch-size N` | Available | Training batch size. Default is `32`. |
| `--lr FLOAT` | Available | Learning rate. Default is `1e-3`. |
| `--results-dir DIR` | Available | Write results to an explicit output directory. |

