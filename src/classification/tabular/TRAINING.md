# ASD Classifier – Training Overview

## Data Flow

```
segmentation_*.xlsx          (per-file, all syllable rows + enrichment columns)
        │
        ▼
  select 13 FEATURE_COLUMNS  (Name, Day, Session, Start/End Hz, Duration,
        │                      Syllable number, Recording Number,
        │                      Mother Genotype, Sex, ISI_time,
        │                      Offspring Genotype, Strain)
        ▼
  feature_extraction()        aggregate per recording → 48 numeric columns
        │
        ▼
  all_data.csv                no headers, raw numbers
        │
        ▼
  train_classifier.py         reads CSV, assigns col_names, trains model
```

> Enrichment columns (Complexity level, Syllable type, Noise, etc.) exist
> only in the `.xlsx` files and **never reach the model**.

## Preferred Data Source

> **The external dataset (`--external` flag / `all_data_external_main.csv`) is the
> preferred data source for all training runs.** It contains correct individual
> genotyping data, unlike the pipeline-aggregated `all_data.csv` which had
> genotype labeling errors (all pups of HET mothers were labeled HET, when in
> reality ~50% are WT). Always use `--external` unless you have a specific
> reason not to.

When building `all_data_external.csv`, the pipeline **drops** syllable-level rows whose **Mother Genotype** or **Offspring Genotype** is not **WT** or **HET** after the same `HT`→`HET` normalization as in legacy feature extraction (e.g. **UNK** is excluded). That keeps `pup_gen` strictly **binary** for XGBoost.

## Input: `all_data.csv`

Default CSV locations:
- Internal: `outputs/legacy/aggregated/all_data.csv`
- External (`--external`): `outputs/external/aggregated/tabular/all_data_external_main.csv`
- Specific variant: pass `--data-csv PATH` (overrides default selection)

Each row = **one recording** of one mouse. 48 columns total:

```
 Columns   Name pattern          Description
 ───────   ────────────          ───────────
  0 – 9    syll{1..10}_s_freq    Avg start frequency per syllable type
 10 – 19   syll{1..10}_e_freq    Avg end frequency per syllable type
 20 – 29   syll{1..10}_dist      Syllable distribution (sums to 1.0)
 30 – 39   syll{1..10}_dur       Avg duration per syllable type
 40        mother_gen            Mother genotype (0=WT, 1=HT/HET)
 41        pup_sex               Pup sex (encoded)
 42        avg_ISI_time          Mean inter-syllable interval
 43        pup_age               Age in days
 44        session               Session number
 45        pup_strain            Strain (1=2022, 2=other)
 ──────────────────────────────────────────────────
 46        pup_gen               TARGET — offspring genotype (0=WT, 1=HT/HET)
 47        mouse_idx             Mouse index (used for group split, not as a feature)
```

### Column roles

```
 ┌─────────────────────────────────────────┐
 │  X = columns 0–45  (46 features)       │  → model input
 │  y = column 46     (pup_gen)           │  → binary target
 │  groups = column 47 (mouse_idx)        │  → group split key
 └─────────────────────────────────────────┘
```

## Syllable types (0–9)

Syllable 10 (Undefined) is **dropped as NaN** before feature extraction.

| # | Type            |   | # | Type            |
|---|-----------------|---|---|-----------------|
| 0 | Complex         |   | 5 | Flat            |
| 1 | Frequency steps |   | 6 | Harmonic        |
| 2 | Composite       |   | 7 | Downward        |
| 3 | Two syllables   |   | 8 | Chevron         |
| 4 | Upward          |   | 9 | Short           |

## Models

The `--model` flag selects which classifier to train. All models use the same
data, split, and evaluation pipeline — only the estimator and model-specific
outputs differ.

| Model   | Flag               | Description                                                    |
|---------|--------------------|----------------------------------------------------------------|
| XGBoost | `--model xgboost`  | Gradient boosting (default). Tuned hyperparams, sample weights |
| TabPFN  | `--model tabpfn`   | Prior-data fitted network. No tuning needed, good for small data |

### XGBoost hyperparameters

| Parameter          | Value |
|--------------------|-------|
| n_estimators       | 50    |
| max_depth          | 5     |
| learning_rate      | 0.1   |
| reg_lambda         | 1.5   |
| reg_alpha          | 0.05  |
| scale_pos_weight   | dynamic `n_WT / n_HT` on train (HT=1) |
| colsample_bytree   | 0.6   |

### TabPFN notes

- **Prior-Data Fitted Network** — a transformer pre-trained on synthetic tabular
  datasets, requiring no hyperparameter tuning.
- Works well on small-to-medium datasets (up to ~10K rows, ~100 features).
- Does **not** support `sample_weight` or `eval_set`; training curves and
  feature importance plots are skipped.
- Paper: https://arxiv.org/abs/2207.01848

## CLI Flags

```
python train_classifier.py [--model MODEL] [--group-split] [--external] [--strain {1,2}] [--data-csv PATH] [--results-dir DIR]
```

| Flag            | Description                                                  |
|-----------------|--------------------------------------------------------------|
| `--model`       | Model to train: `xgboost` (default), `tabpfn`               |
| `--group-split` / `--independent` | Subject-independent evaluation: split by subject (mouse); no leakage across sets |
| `--external`    | **Recommended.** Use the externally-validated dataset with correct individual genotyping (`all_data_external_main.csv`). This is the preferred data source. |
| `--strain {1,2}` | Keep only rows where `pup_strain` equals the given value. Filters after CSV load and before train/val/test split. `pup_strain` is dropped from the feature matrix (constant column). Default output goes under `results/tabular_models/strain/`. |
| `--data-csv`    | Explicit path to the training CSV (48 columns, no header). Use for a specific aggregate file (e.g. a filtered variant). When set, **overrides** the path implied by `--external` / the internal default. The file must exist or the script exits with an error. |
| `--legacy`      | XGBoost only. Reproduce the pre-fix recipe (`sample_weight=balanced` + `scale_pos_weight`). Use only for parity with older runs; the corrected single-weighting (default) is recommended. Output goes under `xgboost_legacy_*`. |
| `--results-dir` | Override default results directory                           |

### Choosing a specific aggregate CSV

Use `--data-csv` whenever you want to train on one exact aggregation output
(for example, an external single-filter variant):

```bash
python train_classifier.py --data-csv "outputs/external/aggregated/tabular/all_data_external_filter_noise.csv"
```

`--data-csv` overrides the dataset implied by `--external`.

### Results directory naming

When `--results-dir` is not set, the output directory is composed automatically under `results/tabular_models/`:

```
results/tabular_models/<model>[_subject_eval_dependent|_subject_eval_independent][_external|_data_<stem>]
```

- **`_external`** — data path resolves to the default `outputs/external/aggregated/tabular/all_data_external_main.csv` (with or without `--external` when that is the effective path).
- **`_data_<stem>`** — `--data-csv` points at any other file; `<stem>` is a sanitized basename (e.g. a variant CSV). Use `--results-dir` for full control of the output folder name.

- **`_subject_eval_dependent`** — random row-level split; subjects may appear in multiple sets.
- **`_subject_eval_independent`** — group-aware split by subject (mouse); use `--group-split` or `--independent`.

**Examples:**

| Flags                                       | Directory |
|---------------------------------------------|-----------|
| *(none)*                                    | `results/tabular_models/xgboost_subject_eval_dependent` |
| `--model tabpfn`                            | `results/tabular_models/tabpfn_subject_eval_dependent` |
| `--group-split`                             | `results/tabular_models/xgboost_subject_eval_independent` |
| `--model tabpfn --group-split`              | `results/tabular_models/tabpfn_subject_eval_independent` |
| `--external`                                | `results/tabular_models/xgboost_subject_eval_dependent_external` |
| `--model tabpfn --external`                 | `results/tabular_models/tabpfn_subject_eval_dependent_external` |
| `--group-split --external`                  | `results/tabular_models/xgboost_subject_eval_independent_external` |
| `--model tabpfn --group-split --external`   | `results/tabular_models/tabpfn_subject_eval_independent_external` |
| `--baseline --strain 1`                     | `results/tabular_models/strain/xgboost_strain1_subject_eval_dependent_baseline` |
| `--baseline --strain 1 --independent`       | `results/tabular_models/strain/xgboost_strain1_subject_eval_independent_baseline` |
| `--baseline --strain 2`                     | `results/tabular_models/strain/xgboost_strain2_subject_eval_dependent_baseline` |
| `--baseline --strain 2 --independent`       | `results/tabular_models/strain/xgboost_strain2_subject_eval_independent_baseline` |

### Per-strain runs

Filter the dataset to a single strain **before** splitting, so each model is
trained and evaluated only on one strain. This lets you compare per-strain
performance and see if subject-independent evaluation affects each strain
differently.

```bash
python train_classifier.py --baseline --strain 1
python train_classifier.py --baseline --strain 1 --independent
python train_classifier.py --baseline --strain 2
python train_classifier.py --baseline --strain 2 --independent
```

Strain mapping (from the external `Strain` column):

| Value | Label | Years |
|-------|-------|-------|
| 1 | BALB/C+BLACK/C57 | 2022, 2023, 2024 |
| 2 | BALB/C | 2015, 2018 |

## Common evaluation

- **Task:** Binary classification (WT vs HET offspring)
- **Split:** 60% train / 20% validation / 20% test
- **Class balancing (XGBoost):** `scale_pos_weight=n_WT/n_HT` on train (HT=1). Pass `--legacy` to additionally apply `sample_weight=balanced` (pre-fix double-weighting; kept for reproducibility — produces effective HT:WT ratio of `(n_WT/n_HT)^2`).
- **Metrics:** accuracy, classification report (precision/recall/F1), confusion matrix
- **Per-strain CMs:** separate confusion matrices for strain 1 and strain 2

## Outputs

All models produce:

| File | Description |
|------|-------------|
| `model/<model>_model.pkl` | Trained model (pickle) |
| `plots/conf_matrix.png` | Confusion matrix heatmap (overall) |
| `plots/confusionmatrix.png` | Confusion matrix with counts + percentages |
| `plots/confusionmatrix_strain1.png` | Confusion matrix – strain 1 |
| `plots/confusionmatrix_strain2.png` | Confusion matrix – strain 2 |
| `logs/out.txt` | Training log |
| `comparison_vs_baseline.txt` | Metrics delta vs baseline |

XGBoost additionally produces:

| File | Description |
|------|-------------|
| `plots/AUC_error.png` | AUC-ROC & error curves per boosting round |
| `plots/feature_importances_0.png` | Bar chart of feature importances |
| `plots/feature_importance_1.png` | Feature importance (weight, gain, cover) |

## Adding a new model

1. Add a factory function in `models.py` that returns an sklearn-compatible estimator.
2. Register it in `MODEL_REGISTRY`.
3. Update the capability sets (`_SUPPORTS_EVAL_SET`, etc.) if the model supports them.
4. The training script handles the rest automatically.
