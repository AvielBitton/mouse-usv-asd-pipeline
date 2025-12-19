from pathlib import Path
from typing import List


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
