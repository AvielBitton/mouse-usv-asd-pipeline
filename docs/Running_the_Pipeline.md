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
python ASD_Tool/asd_tool.py
```

## Process Single File

**New format:**
```bash
python ASD_Tool/asd_tool.py --metadata-file "Metadata Recording Mapping (2015).xlsx"
```

**Old format (legacy):**
```bash
python ASD_Tool/asd_tool.py --metadata-file "Data 2015 For Syl Segmentation_1.xlsx"
```

The file must exist in the `metadata/` directory. If not found, a `FileNotFoundError` is raised with available files.

## Output

For each processed file in `outputs/`:
- `{filename}.xlsx` - Segmentation results and features
- `{filename}.csv` - Extracted features
- `{filename}.npy` - Classification samples

The script skips already processed files (if outputs exist) for safe resumption.
