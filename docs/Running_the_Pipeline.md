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

This creates `Metadata Recording Mapping ({year}).xlsx` files in the `metadata/` directory.

**📖 For detailed instructions:** See `GENERATE_METADATA_README.md`  
**☁️ For Google Drive setup:** See `GOOGLE_DRIVE_SETUP.md`

## Process All Files

```bash
python src/preprocessing/run_pipeline.py
```

## Process Single File

**New format:**
```bash
python src/preprocessing/run_pipeline.py --metadata-file "Metadata Recording Mapping (2015).xlsx"
```

**Old format (legacy):**
```bash
python src/preprocessing/run_pipeline.py --metadata-file "Data 2015 For Syl Segmentation_1.xlsx"
```

The file must exist in the `metadata/` directory. If not found, a `FileNotFoundError` is raised with available files.

## Output

For each processed file in `outputs/`:
- `{filename}.xlsx` - Segmentation results, features, and enrichment columns
- `{filename}.csv` - Extracted per-recording features
- `{filename}.npy` - Classification samples (raw model predictions)

After all files are processed, the pipeline also produces:
- `all_data.xlsx` - Combined data from all segmentation files
- `all_data.csv` - Combined per-recording features

The script skips already processed files (if outputs exist) for safe resumption.

### Segmentation Excel columns (`outputs/segmentation_*.xlsx`)

| # | Column | Description |
|---|--------|-------------|
| 1 | Index | Serial row number (1, 2, 3, …) |
| 2 | Path | Full path to the WAV recording file |
| 3 | Year | Recording year, derived from the Path |
| 4 | Mother | Mother mouse identifier |
| 5 | Mother Genotype | Mother genotype (e.g. HT, WT) |
| 6 | Mother Genotype (binary) | Binary flag: WT = 1, other = 0 |
| 7 | Supplement (Mother) | 1 if Mother name contains "sup", else 0 |
| 8 | Name | Pup/offspring identifier |
| 9 | Sex | Pup sex |
| 10 | Offspring Genotype | Pup genotype (e.g. HT, WT) |
| 11 | Offspring Genotype (binary) | Binary flag: WT = 1, other = 0 |
| 12 | Supplement (Offspring) | 1 if Name contains "sup", else 0 |
| 13 | Day | Age of the mouse in days |
| 14 | Session | Recording session number |
| 15 | Recording Number | Recording identifier (e.g. T0000001) |
| 16 | Syllable order (in recording) | Order of this syllable within the recording (1, 2, 3, … by ascending start time) |
| 17 | Syllables per recording | Total number of syllables detected in this recording |
| 18 | Start point(s) | Syllable start time in seconds |
| 19 | End point(s) | Syllable end time in seconds |
| 20 | Duration (time) | Syllable duration in seconds |
| 21 | ISI_time | Inter-Syllable Interval (time gap to the previous syllable) |
| 22 | Start Point (Hz) | Frequency at the start of the syllable |
| 23 | End Point (Hz) | Frequency at the end of the syllable |
| 24 | Noise | 1 if Start Point (Hz) == End Point (Hz), else 0 |
| 25 | Syllable number | Syllable type (0–10) assigned by the CNN classifier |
| 26 | Syllable type | English label for the syllable number (Complex, Frequency steps, Composite, Two syllables, Upward, Flat, Harmonic, Downward, Chevron, Short, Undefined) |
| 27 | Complexity level | Complexity category: "Single Vowel", "Multiple Vowels", or "Advanced Harmonic" |
| 28 | Complexity level (numeric) | Numeric complexity: 1 (Single Vowel), 2 (Multiple Vowels), 3 (Advanced Harmonic) |

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
| 10 | Undefined | Advanced Harmonic (3) |

