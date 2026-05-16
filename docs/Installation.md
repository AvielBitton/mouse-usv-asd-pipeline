# USV_Project

This project aims to classify mouse pups into two categories: **healthy** or **ASD**, based on their ultrasonic vocalizations (USVs).

---

## Installation

Use **Python 3.8** and install the required packages:

```bash
pip install --upgrade pip
python3 -m pip install -r requirements.txt
````

For the full original project (data, notebooks, scripts):
https://drive.google.com/drive/folders/1zZ_ZmjBKjN3HmpYadLwvXXlHkCyi5dM9

If there are TensorFlow incompatibility issues:

```bash
pip install ~/Downloads/tensorflow-2.4.1-py3-none-any.whl
```

---

## Input

### 1. Metadata files (`running_files/`)

Manually created according to the recording hierarchy (mother name, pup name, session, etc.).
Columns include:

* Name
* Day
* Session
* Start Point (Hz)
* End Point (Hz)
* Duration (time)
* Syllable number
* Recording Number
* Mother Genotype
* Sex
* ISI_time
* Offspring Genotype

**Note:** An automated script (`generate_metadata.py`) is now available to generate metadata files automatically from WAV file paths. See `GENERATE_METADATA_README.md` for details.

### 2. Audio recordings

Located in `USD_Recordings/`.

### 3. Mouse strain values (`pup_strain` in aggregated CSV)

Derived from recording year via `strain_from_year()` in `src/preprocessing/utils/io_utils.py`:

* **2022, 2023, 2024** → `pup_strain` **1** (mixed: `BALB/C+BLACK/C57`)
* **2015, 2018** (and other years) → `pup_strain` **2** (classic: `BALB/C`)

See [`COHORT_DEFINITIONS.md`](COHORT_DEFINITIONS.md) for training-matrix cohorts.

---

## Pipeline Steps (`src/preprocessing/run_pipeline.py`)

### 1. Load Metadata & Audio

Reads metadata Excel file and loads WAV recordings.

### 2. Segmentation

Detects syllables (USVs) from raw audio using `src/preprocessing/legacy/Segmentation.py`.

### 3. Basic Features

Adds ISI time, start/end frequencies using `src/preprocessing/legacy/features.py`.

### 4. Syllable Classification

Classifies each syllable (types 0–10) using a CNN model (`src/models/model_weights.h6`) via `src/preprocessing/legacy/statistics_generator.py`.

### 5. Column Enrichment

Adds derived columns (index, year, genotype binary flags, syllable order, noise indicator, supplement flags, syllable type labels, complexity levels).

### 6. Feature Extraction

Extracts per-recording acoustic features using `src/preprocessing/legacy/audio_feature_extraction_reduction_by_recording.py`.

### 7. Aggregation

Combines all per-file outputs into `outputs/legacy/aggregated/all_data.xlsx` and `outputs/legacy/aggregated/all_data.csv` (overwrites on re-run).

### Feature Definitions

* freq_s_0syll … freq_s_9syll — average start frequency per syllable
* freq_e_0syll … freq_e_9syll — average end frequency per syllable
* dist_0syll … dist_9syll — syllable distribution
* dur_0syll … dur_9syll — syllable duration
* Mother Gen: WT → 1, HT → 0
* Sex: male → 0, female → 1
* time_ISI_avg — average time between syllables
* Age — mouse age
* Session — session number
* Strain: BALB.C → 2, BALB.C × C57B6 → 1
* Pup Gen: WT → 1, HT → 0
* idx_mouse — mouse ID

### ASD Classification (`src/classification/tabular/train_classifier.py`)

Reads `outputs/legacy/aggregated/all_data.csv` for the internal default, or `outputs/external/aggregated/all_data_external_main.csv` with `--external` (or any path via `--data-csv`), trains an XGBoost model, and generates:

* confusion matrix
* AUC-ROC curve
* feature importance plot
* saved model file

---

## Segmentation Labels

* Complex — 0
* Frequency steps — 1
* Composite — 2
* Two syllables — 3
* Upward — 4
* Flat — 5
* Harmonic — 6
* Downward — 7
* Chevron — 8
* Short — 9
* Undefined — 10

---

## Dataset

* 7,923 audio recordings
* ~60,000 syllables
* 70 young mice
* Two different strains
* Variation in strain, genotype, sex, and age


