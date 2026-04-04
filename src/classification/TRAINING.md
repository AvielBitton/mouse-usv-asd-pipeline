# XGBoost Classifier – Training Overview

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
  train_classifier.py         reads CSV, assigns col_names, trains XGBoost
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
 47        mouse_idx             Mouse index (not used in training)
```

### Column roles

```
 ┌─────────────────────────────────────────┐
 │  X = columns 0–45  (46 features)       │  → model input
 │  y = column 46     (pup_gen)           │  → binary target
 │  groupsM = column 47 (mouse_idx)       │  → unused
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

## Model

- **Algorithm:** XGBoost (`XGBClassifier`)
- **Task:** Binary classification (WT vs HET offspring)
- **Split:** 60% train / 20% validation / 20% test
- **Class balancing:** `compute_sample_weight(class_weight='balanced')`
- **Eval metrics:** AUC-ROC, classification error

### Key hyperparameters

| Parameter          | Value |
|--------------------|-------|
| n_estimators       | 50    |
| max_depth          | 5     |
| learning_rate      | 0.1   |
| reg_lambda         | 1.5   |
| reg_alpha          | 0.05  |
| scale_pos_weight   | 0.8   |
| colsample_bytree   | 0.6   |

## Outputs (`results/`)

| File | Description |
|------|-------------|
| `model/XGBmodel.pkl` | Trained model (pickle) |
| `plots/AUC_error.png` | AUC-ROC & error curves |
| `plots/conf_matrix.png` | Confusion matrix (overall) |
| `plots/confusionmatrix_strain1.png` | Confusion matrix – strain 1 |
| `plots/confusionmatrix_strain2.png` | Confusion matrix – strain 2 |
| `plots/feature_importance_*.png` | Feature importance (weight, gain, cover) |
| `logs/out.txt` | Training log |
