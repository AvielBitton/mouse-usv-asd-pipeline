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

**TODO:**

* Create an automated script to generate files like those in `running_files`.
* Create "קובץ עכברים" for year 2023.

### 2. Audio recordings

Located in `USD_Recordings/`.

### 3. Mouse strain values

Assigned manually based on year:

* 2015, 2018 → 1
* 2022 → 2

---

## Steps in `ASD_tool.py`

### 1. Syllable Classification

* `statistics_generator.py` — extracts features
* `statistics_tests.py` — filters out results below 50% accuracy

### 2. Audio Feature Extraction

* `audio_feature_extraction_reduction_by_recording.py`
  (converted from `audio_feature_extraction_REDUCTION_BY_RECORDING_new.ipynb`)
  → generates features
* `Features.py`
  (converted from `StartEndFrequency.ipynb`)
  → extracts start and end frequencies

### 3. Add Strain

Adds the strain value by year.

### 4. Feature Definitions

* Mother — mother's name
* Name — pup's name
* Recording Number — ID
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

### 5. Final Classification (`final_classification.py`)

Generates:

* confusion matrix
* model statistics
* final predictions 

Inputs include all syllable features:
`syl1_s_freq` … `syl10_s_freq`
`syl1_e_freq` … `syl10_e_freq`
`syl1_dist` … `syl10_dist`
`syl1_dur` … `syl10_dur`
plus: `mother_gen`, `pup_sex`, `avg_ISI_time`, `pup_age`, `session`, `pup_strain`, `pup_gen`, `mouse_idx`

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


