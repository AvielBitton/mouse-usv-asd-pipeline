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
