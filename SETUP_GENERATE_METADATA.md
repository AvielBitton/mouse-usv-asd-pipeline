# Setup Guide - Generate Metadata Script

## Quick Start

The `generate_metadata.py` script is standalone and only requires 2 basic packages.

### Quick Installation (Python 3.7+)

```bash
# If you have venv, activate it:
.venv\Scripts\activate  # Windows PowerShell
# or
source .venv/bin/activate  # Linux/Mac

# Install required packages:
pip install pandas openpyxl
```

### Installation with Separate Requirements

```bash
pip install -r requirements-generate-metadata.txt
```

## Differences from Main Project

| | Main Project | generate_metadata.py |
|---|---|---|
| Python | 3.8+ | 3.7+ |
| Requirements | `requirements.txt` (all packages) | `requirements-generate-metadata.txt` (only pandas, openpyxl) |
| Dependencies | TensorFlow, librosa, scipy, etc. | Only pandas, openpyxl |

## If You Have Python 3.7

The main project requires Python 3.8, but `generate_metadata.py` works perfectly with Python 3.7.

**Recommendation:**
- If you're only using `generate_metadata.py` → Use Python 3.7+ with `requirements-generate-metadata.txt`
- If you're using the entire project → Upgrade to Python 3.8+ and use `requirements.txt`

## Verify Installation

```bash
python generate_metadata.py --help
```

If you see the help message, everything is ready!

## Google Drive (Optional)

If you want to use Google Drive mode:

```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

Then download `credentials.json` from Google Cloud Console (see `GENERATE_METADATA_README.md`).
