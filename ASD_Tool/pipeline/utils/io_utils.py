import re
from pathlib import Path
from typing import Dict, List
import pandas as pd


def list_metadata_files(metadata_dir: str = "metadata") -> List[str]:
    """
    Returns a sorted list of Excel filenames in the specified directory.
    
    Args:
        metadata_dir: Path to the metadata directory (default: "metadata")
    
    Returns:
        Sorted list of .xlsx/.xls filenames, excluding temporary Excel files
        (those starting with "~$")
    """
    metadata_path = Path(metadata_dir)
    
    # Get all Excel files (.xlsx and .xls)
    excel_files = []
    for file_path in metadata_path.iterdir():
        if file_path.is_file():
            # Check if it's an Excel file
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                # Skip temporary Excel files (starting with ~$)
                if not file_path.name.startswith('~$'):
                    excel_files.append(file_path.name)
    
    # Return sorted list
    return sorted(excel_files)


def is_segmentation_file_exist(file_name: str, outputs_dir: str = "outputs") -> bool:
    """
    Check if segmentation Excel file exists for a metadata file.
    
    Args:
        file_name: Name of the metadata file (e.g., "Data 2015 For Syl Segmentation_1.xlsx")
        outputs_dir: Path to the outputs directory (default: "outputs")
    
    Returns:
        True if the segmentation Excel file exists, False otherwise
    """
    outputs_path = Path(outputs_dir)
    xlsx_file = outputs_path / file_name
    return xlsx_file.exists()


def is_already_processed(file_name: str, outputs_dir: str = "outputs") -> bool:
    """
    Check if a metadata file has already been fully processed.
    
    A file is considered processed if all expected output files exist:
    - outputs/<file_name> (xlsx)
    - outputs/<stem>.csv
    - outputs/<stem>.npy
    
    Args:
        file_name: Name of the metadata file (e.g., "metadata_2022.xlsx")
        outputs_dir: Path to the outputs directory (default: "outputs")
    
    Returns:
        True if all expected output files exist, False otherwise
    """
    outputs_path = Path(outputs_dir)
    file_stem = Path(file_name).stem
    
    # Expected output files
    xlsx_file = outputs_path / file_name
    csv_file = outputs_path / f"{file_stem}.csv"
    npy_file = outputs_path / f"{file_stem}.npy"
    
    # Check if all files exist
    return xlsx_file.exists() and csv_file.exists() and npy_file.exists()


# Required column names from metadata Excel files
# These columns contain essential mouse information needed for processing:
# - Mother: mother mouse identifier
# - Mother Genotype: genetic type of the mother
# - Name: pup mouse identifier
# - Sex: gender of the pup
# - Offspring Genotype: genetic type of the pup
# - Day: age of the mouse in days
# - Session: recording session number
# - Recording Number: unique identifier for each audio recording
METADATA_REQUIRED_COLUMNS = [
    "Mother",
    "Mother Genotype",
    "Name",
    "Sex",
    "Offspring Genotype",
    "Day",
    "Session",
    "Recording Number",
]


# Regular expression pattern to extract 4-digit year (1900-2099) from filenames
# Used to identify the year from metadata file names (e.g., "metadata_2022.xlsx" -> "2022")
_YEAR_REGEX_PATTERN = re.compile(r"(19|20)\d{2}")


def extract_year_from_filename(file_name: str) -> str:
    """Extract a 4-digit year (e.g., 2015) from the filename."""
    m = _YEAR_REGEX_PATTERN.search(file_name)
    if not m:
        raise ValueError(f"Could not extract year from filename: {file_name}")
    return m.group(0)


def read_metadata_as_lists(metadata_path: str) -> Dict[str, List]:
    """
    Read the first sheet of the metadata Excel file and return a dict:
    {column_name: list_of_values}, for METADATA_REQUIRED_COLUMNS only.
    Assumes the first row is a header (matches the metadata files in this project).
    """
    df = pd.read_excel(metadata_path, sheet_name=0, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]

    missing = [c for c in METADATA_REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {metadata_path}: {missing}")

    df = df[METADATA_REQUIRED_COLUMNS].dropna(how="all")
    if df.empty:
        raise ValueError(f"No metadata rows found in {metadata_path}")

    return {c: df[c].tolist() for c in METADATA_REQUIRED_COLUMNS}

