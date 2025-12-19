# Running the Pipeline

## Process All Files

```bash
python ASD_Tool/asd_tool.py
```

## Process Single File

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
