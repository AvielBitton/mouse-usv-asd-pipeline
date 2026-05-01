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

## Input: `all_data.csv`

Each row = **one recording** of one mouse. 48 columns total:

```
 Columns   Name pattern          Description
 ───────   ────────────          ───────────
  0 – 9    syll{1..10}_s_freq    Avg start frequency per syllable type
 10 – 19   syll{1..10}_e_freq    Avg end frequency per syllable type
 20 – 29   syll{1..10}_dist      Syllable distribution (sums to 1.0)
 30 – 39   syll{1..10}_dur       Avg duration per syllable type
 40        mother_gen            Mother genotype (0=HET, 1=WT)
 41        pup_sex               Pup sex (encoded)
 42        avg_ISI_time          Mean inter-syllable interval
 43        pup_age               Age in days
 44        session               Session number
 45        pup_strain            Strain (1=2022, 2=other)
 ──────────────────────────────────────────────────
 46        pup_gen               TARGET — offspring genotype (WT/HET)
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
| scale_pos_weight   | 0.8   |
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
python train_classifier.py [--model MODEL] [--group-split] [--external] [--results-dir DIR]
```

| Flag            | Description                                                  |
|-----------------|--------------------------------------------------------------|
| `--model`       | Model to train: `xgboost` (default), `tabpfn`               |
| `--group-split` | Group-aware split by mouse identity (prevents data leakage)  |
| `--external`    | Use external aggregated data (`all_data_external.csv`)       |
| `--results-dir` | Override default results directory                           |

### Results directory naming

When `--results-dir` is not set, the output directory is composed automatically:

```
results/<model>[_base][_group_split][_external]
```

All results live under the `results/` parent directory. The `_base` suffix is
added when no `--group-split` or `--external` flags are active, to clearly
identify the baseline run.

**Examples:**

| Flags                                       | Directory                                  |
|---------------------------------------------|--------------------------------------------|
| *(none)*                                    | `results/xgboost_base`                     |
| `--model tabpfn`                            | `results/tabpfn_base`                      |
| `--group-split`                             | `results/xgboost_group_split`              |
| `--model tabpfn --group-split`              | `results/tabpfn_group_split`               |
| `--external`                                | `results/xgboost_external`                 |
| `--model tabpfn --external`                 | `results/tabpfn_external`                  |
| `--group-split --external`                  | `results/xgboost_group_split_external`     |
| `--model tabpfn --group-split --external`   | `results/tabpfn_group_split_external`      |

## Common evaluation

- **Task:** Binary classification (WT vs HET offspring)
- **Split:** 60% train / 20% validation / 20% test
- **Class balancing:** `compute_sample_weight(class_weight='balanced')` (XGBoost only)
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
