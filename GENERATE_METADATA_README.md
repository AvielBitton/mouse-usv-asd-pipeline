# Generate Metadata - Usage Guide

Script to generate metadata Excel files from WAV files, supports local scanning or Google Drive.

## System Requirements

- **Python 3.7+** (The script works with Python 3.7, unlike the main project which requires 3.8)
- Packages: `pandas`, `openpyxl`
- Optional: Google Drive packages (only if using `--drive` mode)

## Installation

### Option 1: Minimal Installation (for generate_metadata script only)

The script only requires `pandas` and `openpyxl`:

```bash
pip install pandas openpyxl
```

Or with a separate requirements file:
```bash
pip install -r requirements-generate-metadata.txt
```

### Option 2: Full Installation (for entire project)

If you're using the entire project (including TensorFlow, segmentation, etc.):
```bash
pip install -r requirements.txt
```

**Note:** `requirements.txt` is designed for Python 3.8. If you have Python 3.7, use `requirements-generate-metadata.txt`.

### Google Drive (Optional)

If you want to use Google Drive mode, also install:
```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

2. For Google Drive - download credentials file:
   
   **📖 Detailed Guide:** See `GOOGLE_DRIVE_SETUP.md` for step-by-step instructions
   
   **Quick steps:**
   - Go to https://console.cloud.google.com/
   - Create a project (or select existing)
   - Enable Google Drive API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download as `credentials.json` in the project folder

## Usage

### Local Mode

Scan a local directory:

```bash
python generate_metadata.py --local --source-dir dumps
```

Or with a custom metadata directory:

```bash
python generate_metadata.py --local --source-dir dumps --metadata-dir metadata
```

### Google Drive Mode

**Option 1: Using Folder ID**

```bash
python generate_metadata.py --drive --drive-folder-id <FOLDER_ID>
```

**Option 2: Using URL**

```bash
python generate_metadata.py --drive --drive-folder-url "https://drive.google.com/drive/folders/XXXXX"
```

**With custom credentials file:**

```bash
python generate_metadata.py --drive --drive-folder-id <FOLDER_ID> --credentials my_credentials.json
```

## Folder Structure

The script expects the following structure:

```
{year}/{mother}_{matgen}/{name}_{pupgen}/day_{day}/session{session}/{rec_num}.wav
```

Example:
```
2025/22731O_HT/22731O_1A_BLUE_HT/day_4/session1/T0000001.wav
```

## Output Files

The script creates Excel files under `metadata/mapping/` with the name:
- `Metadata Recording Mapping ({year}).xlsx`

Each year gets a single file containing all its records.

## Sex Table

The script automatically searches for Excel files in year folders (e.g., 2015, 2018, 2022) and attempts to load sex information for the mice.

**How it works:**
- For each year folder (4-digit folder name), the script looks for Excel files (`.xlsx` or `.xls`)
- It loads the Excel file and extracts sex information by matching the `name` column
- The sex data is joined with WAV file metadata based on the `name` field

**For local mode:** Searches for Excel files directly in each year folder (e.g., `dumps/2015/*.xlsx`)

**For Drive mode:** Searches for Excel files in each year folder on Google Drive

**Expected structure:**
```
Root/
  2015/
    [Excel file with sex data].xlsx
    [mother folders]/
      [WAV files]
  2018/
    [Excel file with sex data].xlsx
    [mother folders]/
      [WAV files]
```

## Examples

### Local
```bash
# Basic scan
python generate_metadata.py --local

# With custom directory
python generate_metadata.py --local --source-dir /path/to/my/data
```

### Google Drive
```bash
# With Folder ID
python generate_metadata.py --drive --drive-folder-id 1zZ_ZmjBKjN3HmpYadLwvXXlHkCyi5dM9

# With URL
python generate_metadata.py --drive --drive-folder-url "https://drive.google.com/drive/folders/1zZ_ZmjBKjN3HmpYadLwvXXlHkCyi5dM9"
```

## Troubleshooting

### Google Drive Authentication Error
- See `GOOGLE_DRIVE_SETUP.md` for detailed guide
- Make sure you downloaded `credentials.json` from the console and saved it in the project folder
- Make sure you enabled Google Drive API in the project
- Make sure you created OAuth credentials of type "Desktop app" (not Web)
- On first run, the script will open a browser for authentication - this is normal

### No WAV Files Found
- Make sure the folder structure matches the expected structure
- Make sure files end with `.wav` or `.WAV`

### Parsing Error
- Make sure all path components exist (year, mother, name, day, session)
- Make sure the format matches (e.g., `day_4` not `day4`)
