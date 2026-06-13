# Running the Pipeline

## Step 0: Generate Metadata Files (If Needed)

Before running the main pipeline, ensure you have metadata files. You can generate them automatically:

**From local directory:**
```bash
python generate_metadata.py --local --source-dir dumps
```

**From Google Drive:**
```bash
python generate_metadata.py --drive --drive-folder-url "https://drive.google.com/drive/folders/YOUR_FOLDER_ID"
```

This creates `Metadata Recording Mapping ({year}).xlsx` files under `metadata/mapping/` (full cross-year index; not scanned by `run_pipeline`).

**📖 For detailed instructions:** See `GENERATE_METADATA_README.md`  
**☁️ For Google Drive setup:** See `GOOGLE_DRIVE_SETUP.md`

## Process All Files

```bash
python src/preprocessing/run_pipeline.py
```

Generate one or more external filtered variants in the same run:

```bash
python src/preprocessing/run_pipeline.py \
  --external-filter noise \
  --external-filter supplement_offspring
```

## Process Single File

Use a **`Data {year} For Syl Segmentation_*.xlsx`** file at the top level of `metadata/` (these are what the pipeline is designed to run on):

```bash
python src/preprocessing/run_pipeline.py --metadata-file "Data 2015 For Syl Segmentation_1.xlsx"
```

The file must exist in the `metadata/` directory (not in subfolders). If not found, a `FileNotFoundError` is raised with available files.

**Note:** `Metadata Recording Mapping ({year}).xlsx` files live under `metadata/mapping/` as a generated **reference index** (all recordings per year). They are **not** listed for batch runs and should not be passed to `run_pipeline` unless you intentionally want to reprocess the entire year in one job (heavy memory use).

## Output

Under `outputs/` there are two top-level areas: **`external/`** (your external
dataset) and **`legacy/`** (metadata-driven pipeline outputs).

**`outputs/external/`** has two roles:
- **`input/`** — files **you place here** (e.g. `segmentation_classification_all_data.xlsx`).
- **`aggregated/`** — **generated** tabular aggregates derived from that workbook
  (`all_data_external_main.*`, optional `all_data_external_filter_*.*`).

Everything else the metadata-driven pipeline produces (per-file workbooks,
internal combined table, default log file) lives under **`outputs/legacy/`**. The
`outputs/` root is only `external/`, `legacy/`, and any stray top-level logs you add.

For each processed metadata file under `outputs/legacy/`:
- `{filename}.xlsx` - Segmentation results, features, and enrichment columns
- `{filename}.csv` - Extracted per-recording features
- `{filename}.npy` - Classification samples (raw model predictions)

After all files are processed, the pipeline writes:
- `outputs/legacy/aggregated/all_data.xlsx` - Combined data from all per-file segmentation workbooks
- `outputs/legacy/aggregated/all_data.csv` - Combined per-recording features

External aggregation writes under `outputs/external/aggregated/`, split by consumer
(the tabular pipeline reads the CSV aggregates, the sequence pipeline reads the
syllable-level XLSX — see [NEURAL_NETWORK_BASELINE.md](NEURAL_NETWORK_BASELINE.md)):
- `sequence/all_data_external_main.xlsx`
- `tabular/all_data_external_main.csv`

When `--external-filter` is repeated, extra **single-filter** variants are generated:
- `sequence/all_data_external_filter_<filter>.xlsx`
- `tabular/all_data_external_filter_<filter>.csv`

Before any aggregate is written, rows where **Mother Genotype** or **Offspring Genotype** is not **WT** or **HET** (after `HT`→`HET`) are **dropped**, so the tabular CSV stays **binary** for `pup_gen`.

Supported `--external-filter` names (optional ablation variants only):
- `invalid_sex`
- `noise`
- `supplement_offspring`
- `undefined_syllable`

The script skips already processed files (if outputs exist) for safe resumption.

### Segmentation Excel columns (`outputs/legacy/segmentation_*.xlsx`)

| # | Column | Description |
|---|--------|-------------|
| 1 | Index | Serial row number (1, 2, 3, …) |
| 2 | Path | Full path to the WAV recording file |
| 3 | Year | Recording year, derived from the Path |
| 4 | Mother | Mother mouse identifier |
| 5 | Mother Genotype | Mother genotype (e.g. HT, WT) |
| 6 | Mother Genotype (binary) | Binary flag: HT = 1, WT / UNK / NAN (and anything else) = 0 |
| 7 | Supplement (Mother) | 1 if Mother name **or Path** contains "sup", else 0 |
| 8 | Name | Pup/offspring identifier |
| 9 | Sex | Pup sex (normalized to `M` / `F` / `U`) |
| 10 | Offspring Genotype | Pup genotype (e.g. HT, WT) |
| 11 | Offspring Genotype (binary) | Binary flag: HT = 1, WT / UNK / NAN (and anything else) = 0 |
| 12 | Genotype Group | `"<Mother>-<Offspring>"` text label combining both genotypes (e.g. `WT-WT`, `HT-WT`, `HT-HT`, `WT-UNK`). Empty/missing → `NAN`; any other label → `UNK` |
| 13 | Genotype Group (numeric) | Numeric encoding: `WT-WT = 1`, `HT-WT = 2`, `HT-HT = 3`, anything else (including UNK / NAN combinations) = `0` |
| 14 | Supplement (Offspring) | Metadata cell first; falls back to 1 if `Name` or `Path` contains "sup", else 0 |
| 15 | Day | Age of the mouse in days |
| 16 | Session | Recording session number |
| 17 | Strain | Descriptive strain label by year: `BALB/C` (2015 / 2018) or `BALB/C+BLACK/C57` (2022 / 2023 / 2024). See note below. |
| 18 | Recording Number | Recording identifier (e.g. T0000001) |
| 19 | Syllable order (in recording) | Order of this syllable within the recording (1, 2, 3, … by ascending start time; nullable `Int64`) |
| 20 | Syllables per recording | Total number of syllables detected in this recording |
| 21 | Start point(s) | Syllable start time in seconds |
| 22 | End point(s) | Syllable end time in seconds |
| 23 | Duration (time) | Syllable duration in seconds |
| 24 | ISI_time | Inter-Syllable Interval (time gap to the previous syllable) |
| 25 | Start Point (Hz) | Frequency at the start of the syllable |
| 26 | End Point (Hz) | Frequency at the end of the syllable |
| 27 | Noise | 1 if Start Point (Hz) == End Point (Hz), else 0 |
| 28 | Syllable number | Syllable type (0–10) assigned by the CNN classifier |
| 29 | Syllable type | English label for the syllable number (Complex, Frequency steps, Composite, Two syllables, Upward, Flat, Harmonic, Downward, Chevron, Short, Undefined) |
| 30 | Complexity level | Complexity category: "Undefined", "Single Vowel", "Multiple Vowels", or "Advanced Harmonic" |
| 31 | Complexity level (numeric) | Numeric complexity: 0 (Undefined), 1 (Single Vowel), 2 (Multiple Vowels), 3 (Advanced Harmonic) |

> **Note about `Strain`.** The per-file `outputs/legacy/segmentation_*.xlsx` workbooks store `Strain` as a descriptive **text label** (`BALB/C` for 2015 / 2018, `BALB/C+BLACK/C57` for 2022 / 2023 / 2024). In external aggregation, the tabular feature-extraction step maps the **table value** of `Strain` to the numeric classifier encoding (`BALB/C` → 2, `BALB/C+BLACK/C57` → 1). If a row has an unknown `Strain` text, the pipeline falls back to deriving strain from `Path` year and logs a warning.

### Pipeline Behaviour Notes

- **Metadata header detection**: `read_metadata_as_lists` scans the first 20 rows of the metadata workbook to find the header row, so workbooks with a banner / title row above the headers are accepted automatically. See `Metadata_Structure.md → Header Flexibility` for the full alias map (English variants and Hebrew labels).
- **Sex normalization**: every value in the `Sex` column is coerced to `M` / `F` / `U` (English, single-letter and Hebrew labels supported) before the segmentation workbook is written.
- **Path resolution**: WAVs are resolved through `build_recording_base_path` + `resolve_wav_path`. The resolver tries the canonical `<root>/<year>/<mother>_<matgen>/<name>_<pupgen>/day_<d>/sessionN/<rec>` layout first, then identity-key matching (handles colour/genotype/parenthetical decorators on pup folders), and finally a prefix / token fallback. The same resolver is used by both the loader step and the CNN classification step so they stay consistent.
- **CNN classification performance**: `Syl_Class_Vec` (in `legacy/statistics_generator.py`) caches the loaded waveform across consecutive syllables of the same recording, then stacks every spectrogram and runs `model.predict` in chunks of `_GLOBAL_INFERENCE_CHUNK = 2048` (capped lower for huge jobs) with `_PREDICT_BATCH_SIZE = 32`. For multi-thousand-syllable workbooks this is dramatically faster than per-syllable `librosa.load` + `model.predict`.
- **Welch PSD robustness**: `_welch_psd` clamps `nperseg` / `noverlap` to the segment length, so syllables near the very end of a recording (where the slice can be shorter than 1024 samples) no longer crash; `StartEndFreq` also wraps each row in a `try`/`except` and logs the first 25 failures.
- **Idempotent column writes**: all enrichment / classification columns are overwritten in place if they already exist, so re-running the pipeline on a workbook is safe.

#### Syllable type mapping

| Number | Label | Complexity |
|--------|-------|------------|
| 0 | Complex | Single Vowel (1) |
| 1 | Frequency steps | Multiple Vowels (2) |
| 2 | Composite | Advanced Harmonic (3) |
| 3 | Two syllables | Multiple Vowels (2) |
| 4 | Upward | Single Vowel (1) |
| 5 | Flat | Single Vowel (1) |
| 6 | Harmonic | Advanced Harmonic (3) |
| 7 | Downward | Single Vowel (1) |
| 8 | Chevron | Single Vowel (1) |
| 9 | Short | Single Vowel (1) |
| 10 | Undefined | Undefined (0) |

