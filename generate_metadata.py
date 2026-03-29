"""
Script to generate metadata Excel files from WAV files in local directory or Google Drive.

This script:
1. Scans a directory (local or Google Drive) recursively for all WAV files
2. Extracts metadata from the folder path structure
3. Groups records by year
4. Creates full-year index Excel files under ``metadata/mapping/`` named
   ``Metadata Recording Mapping ({year}).xlsx`` (reference listing; not used by
   ``run_pipeline`` discovery).

Each scanned year can produce one such mapping file (see script logic for skips).

Usage:
    # Local mode
    python generate_metadata.py --local --source-dir dumps
    
    # Google Drive mode
    python generate_metadata.py --drive --drive-folder-id <folder_id>
    python generate_metadata.py --drive --drive-folder-url <folder_url>
"""

import re
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
import pandas as pd
from collections import defaultdict

# Full cross-year index files written here (not scanned by run_pipeline; see list_metadata_files).
MAPPING_SUBDIR = "mapping"

try:
    from drive_scanner import GoogleDriveScanner, DriveFile
    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False
    # Define dummy class for type hints when Drive is not available
    class GoogleDriveScanner:
        pass
    class DriveFile:
        pass


_KNOWN_GENOTYPES = {'WT', 'HET', 'HT'}

# Matches the pup number part: one digit followed by one letter (e.g. 1A, 2B, 3D)
_PUP_NUM_RE = re.compile(r'\b(\d[A-Za-z])\b')


def _parse_mother_folder(folder_name: str):
    """Parse a mother folder name into (mother_id, genotype).

    Supports both underscore-separated ("22731O_HT") and space-separated
    ("13128K WT", "13130I HET SUPP", "24277J WT - litter 2 (2.7.24)").

    Returns (mother, matgen) or (None, None) on failure.
    """
    if '_' in folder_name:
        mother, matgen = folder_name.rsplit('_', 1)
        return mother, matgen

    tokens = folder_name.split()
    if len(tokens) >= 2:
        mother = tokens[0]
        matgen = tokens[1].upper()
        if matgen in _KNOWN_GENOTYPES or matgen in ('HOM',):
            return mother, matgen
        return mother, matgen

    return None, None


def _parse_pup_folder(folder_name: str, mother_genotype: str):
    """Parse a pup folder name into (name, offspring_genotype).

    Supports underscore-separated ("22731O_1A_BLUE_HT") and the
    space/dash-separated variants found in 2023/2024 data:
      "13128K 1A WT-WT-WT RED"
      "14120P-1A RED"
      "13131J Het SUP 1A red"
      "24229L-1B (RED) WT-WT-WT"

    Falls back to *mother_genotype* when the offspring genotype cannot be
    determined from the folder name.

    Returns (name, pupgen) or (None, None) on failure.
    """
    if '_' in folder_name:
        name, pupgen = folder_name.rsplit('_', 1)
        return name, pupgen

    # Extract the mother-id prefix: sequence of digits followed by letter(s)
    id_match = re.match(r'^(\d+[A-Za-z]+)', folder_name)
    if not id_match:
        return None, None
    mother_id = id_match.group(1)

    # Find the pup number (e.g. "1A", "2B") after the mother-id
    remainder = folder_name[len(mother_id):]
    pup_match = _PUP_NUM_RE.search(remainder)
    if not pup_match:
        return None, None

    pup_num = pup_match.group(1).upper()
    name = f"{mother_id.upper()}-{pup_num}"

    # Try to determine offspring genotype from the remaining text
    text_after_pup = remainder[pup_match.end():]
    pupgen = None
    for token in text_after_pup.replace('-', ' ').split():
        if token.upper() in _KNOWN_GENOTYPES:
            pupgen = token.upper()
            break
    if pupgen is None:
        pupgen = mother_genotype

    return name, pupgen


def parse_path_to_metadata(
    path_str: str, 
    root_path_str: str,
    is_drive: bool = False
) -> Optional[Dict[str, str]]:
    """
    Parse a WAV file path to extract metadata.
    
    Expected structure: {year}/{mother}_{matgen}/{name}_{pupgen}/day_{day}/session{session}/{rec_num}.wav
    
    Args:
        path_str: Path string to the WAV file
        root_path_str: Root path string (for relative path calculation)
        is_drive: Whether this is a Google Drive path
        
    Returns:
        Dictionary with metadata fields or None if path doesn't match expected structure
    """
    try:
        # Normalize path separators
        if is_drive:
            # Drive paths use /
            parts = path_str.split('/')
            # Remove empty parts
            parts = [p for p in parts if p]
        else:
            # Local paths
            path_obj = Path(path_str)
            root_obj = Path(root_path_str)
            try:
                rel_path = path_obj.relative_to(root_obj)
                parts = rel_path.parts
            except ValueError:
                # If not relative, try to extract from full path
                parts = path_obj.parts
        
        # Expected structure: 
        # {year}/{mother}_{matgen}/{name}_{pupgen}/day_{day}/session{session}/{rec_num}.wav
        # {year}/{mother}_{matgen}/{name}_{pupgen}/day_{day}/session{session}/ch{channel}/{rec_num}.wav
        # {year}/{mother}_{matgen}/{name}_{pupgen}/day_{day}/ch{channel}/{rec_num}.wav
        # OR if root is year: same but without year at start
        
        # Check if year is in parts or in root_path_str
        # First, try to determine if we have both session and channel by checking parts
        has_both_session_and_channel = False
        if len(parts) >= 5:
            # Check if we have session followed by channel
            # Look for pattern: .../sessionX/chY/...
            for i in range(len(parts) - 2):
                if parts[i].startswith('session') and parts[i+1].lower().startswith('ch'):
                    has_both_session_and_channel = True
                    break
        
        if len(parts) == 7:
            # Full path with year and both session and channel: {year}/{mother}/{name}/day_{day}/session/ch/{rec}
            year = parts[0]
            mother_idx = 1
            name_idx = 2
            day_idx = 3
            session_idx = 4
            channel_idx = 5
            rec_idx = 6
        elif len(parts) == 6:
            # Could be: {year}/{mother}/{name}/day_{day}/session_or_ch/{rec}
            # OR: {mother}/{name}/day_{day}/session/ch/{rec} (without year)
            if has_both_session_and_channel:
                # Relative path without year, but with both session and channel
                # Extract year from root_path_str or path_str
                if root_path_str and (root_path_str.isdigit() or '/' in root_path_str):
                    if root_path_str.isdigit():
                        year = root_path_str
                    elif '/' in root_path_str:
                        year_parts = root_path_str.replace('\\', '/').split('/')
                        year = year_parts[-1] if year_parts[-1].isdigit() else year_parts[0] if year_parts[0].isdigit() else 'Unknown'
                    else:
                        year = 'Unknown'
                else:
                    path_parts_full = path_str.replace('\\', '/').split('/')
                    year = path_parts_full[0] if path_parts_full[0].isdigit() else 'Unknown'
                mother_idx = 0
                name_idx = 1
                day_idx = 2
                session_idx = 3
                channel_idx = 4
                rec_idx = 5
            else:
                # Full path with year: {year}/{mother}/{name}/day_{day}/session_or_ch/{rec}
                year = parts[0]
                mother_idx = 1
                name_idx = 2
                day_idx = 3
                session_idx = 4
                rec_idx = 5
                channel_idx = None
        elif len(parts) == 5:
            # Relative path without year: {mother}/{name}/day_{day}/session_or_ch/{rec}
            # Extract year from root_path_str or path_str
            if root_path_str and (root_path_str.isdigit() or '/' in root_path_str):
                if root_path_str.isdigit():
                    year = root_path_str
                elif '/' in root_path_str:
                    year_parts = root_path_str.replace('\\', '/').split('/')
                    year = year_parts[-1] if year_parts[-1].isdigit() else year_parts[0] if year_parts[0].isdigit() else 'Unknown'
                else:
                    year = 'Unknown'
            else:
                path_parts_full = path_str.replace('\\', '/').split('/')
                year = path_parts_full[0] if path_parts_full[0].isdigit() else 'Unknown'
            mother_idx = 0
            name_idx = 1
            day_idx = 2
            session_idx = 3
            rec_idx = 4
            channel_idx = None
        else:
            return None
        
        # Parse mother and genotype: e.g., "22731O_HT" -> mother="22731O", matgen="HT"
        # Also supports space-separated: "13128K WT", "13130I HET SUPP",
        # "24277J WT - litter 2 (2.7.24)"
        mother_full = parts[mother_idx]
        mother, matgen = _parse_mother_folder(mother_full)
        if mother is None:
            return None
        
        # Parse name and pup genotype: e.g., "22731O_1A_BLUE_HT" -> name="22731O_1A_BLUE", pupgen="HT"
        # Also supports space-separated: "13128K 1A WT-WT-WT RED", "14120P-1A RED",
        # "13131J Het SUP 1A red", "24229L-1B (RED) WT-WT-WT"
        name_full = parts[name_idx]
        name, pupgen = _parse_pup_folder(name_full, matgen)
        if name is None:
            return None
        
        # Parse day: e.g., "day_4" -> day="4"
        day_str = parts[day_idx]
        if day_str.startswith('day_'):
            day = day_str.replace('day_', '')
        else:
            return None
        
        # Parse session and channel
        # Can have: session{session}/ch{channel} or just ch{channel} (no session) or just session{session} (no channel)
        session = None
        channel = None
        
        # Check what we have at session_idx position
        session_str = parts[session_idx]
        
        if channel_idx is not None:
            # We have both session and channel
            if session_str.startswith('session'):
                session = session_str.replace('session', '')
                channel_str = parts[channel_idx]
                if channel_str.lower().startswith('ch'):
                    channel = channel_str.lower().replace('ch', '')
                else:
                    return None
            else:
                return None
        else:
            # We have either session or channel, but not both
            if session_str.startswith('session'):
                # We have a session
                session = session_str.replace('session', '')
            elif session_str.lower().startswith('ch'):
                # Only channel, no session
                channel = session_str.lower().replace('ch', '')
            else:
                # Neither session nor channel found
                return None
        
        # Parse recording number: e.g., "T0000001.wav" -> rec_num="T0000001"
        rec_file = parts[rec_idx]
        rec_num = rec_file.replace('.wav', '').replace('.WAV', '').replace('.wave', '').replace('.WAVE', '')
        
        result = {
            'Mother': mother,
            'Mother Genotype': matgen,
            'Name': name,
            'Sex': '',  # Will be filled from table if available
            'Offspring Genotype': pupgen,
            'Day': int(day),
            'Recording Number': rec_num,
        }
        
        if session:
            result['Session'] = int(session)
        else:
            result['Session'] = ''
        
        if channel:
            result['Channel'] = int(channel)
        else:
            result['Channel'] = ''
        
        return result
    except (ValueError, IndexError) as e:
        print(f"Error parsing path {path_str}: {e}")
        return None


def load_sex_from_table_local(table_path: Path) -> Dict[Tuple[str, str], str]:
    """Load Sex information from local Excel table."""
    sex_map = {}
    if not table_path.exists():
        return sex_map
    
    try:
        df = pd.read_excel(table_path, engine='openpyxl')
        return _extract_sex_mapping(df)
    except Exception as e:
        print(f"  Warning: Could not load sex from table {table_path}: {e}")
    
    return sex_map


def load_sex_from_table_drive(scanner: GoogleDriveScanner, file_id: str) -> Dict[Tuple[str, str], str]:
    """Load Sex information from Google Drive Excel table."""
    sex_map = {}
    try:
        df = scanner.download_excel_file(file_id)
        if df is not None:
            return _extract_sex_mapping(df)
    except Exception as e:
        print(f"  Warning: Could not load sex from Drive table {file_id}: {e}")
    
    return sex_map


def _normalize_name_for_matching(name: str) -> str:
    """
    Normalize name by taking first letter of each part separated by '-'.
    This allows matching between full names and abbreviations.
    
    Examples:
    - "GREEN-RED" -> "G-R"
    - "DAVID-MOSHE" -> "D-M"
    - "DUDI-MOSHIKO" -> "D-M"
    - "G-R" -> "G-R" (unchanged)
    - "22731O_4A_GREEN-RED" -> "22731O_4A_G-R"
    """
    # Split by underscore to get parts
    parts = name.split('_')
    normalized_parts = []
    
    for part in parts:
        # If part contains '-', take first letter of each sub-part
        if '-' in part:
            sub_parts = part.split('-')
            # Take first letter (uppercase) of each sub-part
            abbreviated = '-'.join([sub_part[0].upper() if sub_part else '' for sub_part in sub_parts if sub_part])
            normalized_parts.append(abbreviated)
        else:
            # Keep part as is
            normalized_parts.append(part)
    
    return '_'.join(normalized_parts)


def _match_names(name_from_path: str, name_from_table: str) -> bool:
    """
    Check if two names match by normalizing both to abbreviations.
    
    Examples:
    - "22731O_4A_GREEN-RED" matches "22734A_4A_G-R" (both normalize to "22731O_4A_G-R")
    - "22731O_4A_DAVID-MOSHE" matches "22734A_4A_D-M" (both normalize to "22731O_4A_D-M")
    """
    # Normalize both names to abbreviations (take first letter of each part separated by '-')
    normalized_path = _normalize_name_for_matching(name_from_path)
    normalized_table = _normalize_name_for_matching(name_from_table)
    
    # Direct match after normalization
    if normalized_path.upper() == normalized_table.upper():
        return True
    
    # Try matching by splitting and comparing parts
    path_parts = normalized_path.split('_')
    table_parts = normalized_table.split('_')
    
    if len(path_parts) != len(table_parts):
        return False
    
    # Compare parts - allow minor differences in first part (mother name)
    # but require exact match for other parts (number, abbreviations)
    for i, (p_part, t_part) in enumerate(zip(path_parts, table_parts)):
        if i == 0:
            # First part (mother name) - allow minor differences (e.g., 22731O vs 22734A)
            # Check if they're similar (same length, mostly same characters)
            if len(p_part) == len(t_part):
                # Allow 1-2 character differences in mother name
                diff_count = sum(1 for a, b in zip(p_part.upper(), t_part.upper()) if a != b)
                if diff_count > 2:
                    return False
            else:
                return False
        else:
            # Other parts must match exactly (after normalization)
            if p_part.upper() != t_part.upper():
                return False
    
    return True


def _extract_sex_mapping(df: pd.DataFrame) -> Dict:
    """
    Extract sex mapping from DataFrame.
    Returns a dict with 'original' and 'normalized' mappings for flexible matching.
    """
    sex_map_original = {}
    sex_map_normalized = {}
    
    print(f"  Table columns: {list(df.columns)}")
    
    mother_col = None
    name_col = None
    sex_col = None
    
    # Search for columns by English and Hebrew keywords (supports legacy Hebrew tables)
    for col in df.columns:
        col_str = str(col)
        col_lower = col_str.lower()
        if 'mother' in col_lower or 'אמא' in col_str:
            mother_col = col
        elif 'name' in col_lower or 'שם' in col_str or 'pup' in col_lower or 'גור' in col_str:
            name_col = col
        elif 'sex' in col_lower or 'מין' in col_str or 'gender' in col_lower:
            sex_col = col
    
    if mother_col and name_col and sex_col:
        print(f"  Using columns: Mother={mother_col}, Name={name_col}, Sex={sex_col}")
        for _, row in df.iterrows():
            try:
                mother = str(row[mother_col]).strip()
                name = str(row[name_col]).strip()
                sex = str(row[sex_col]).strip()
                if mother and name and sex and mother != 'nan' and name != 'nan' and sex != 'nan':
                    # Store original mapping
                    sex_map_original[(mother, name)] = sex
                    # Also store normalized version for flexible matching (abbreviated)
                    name_normalized = _normalize_name_for_matching(name)
                    sex_map_normalized[(mother, name_normalized)] = sex
            except Exception:
                continue
        print(f"  Loaded {len(sex_map_original)} sex mappings from table")
    else:
        print(f"  Warning: Could not identify required columns in table")
        print(f"    Found: Mother={mother_col}, Name={name_col}, Sex={sex_col}")
    
    # Return both mappings - will use flexible matching when looking up
    return {'original': sex_map_original, 'normalized': sex_map_normalized}


def find_all_wav_files_local(dumps_root: Path) -> List[Tuple[str, str]]:
    """
    Find all WAV files in local directory.
    
    Returns:
        List of (file_path, path_string) tuples
    """
    wav_files = {}  # Use dict with normalized path as key to avoid duplicates
    for wav_path in dumps_root.rglob('*.wav'):
        normalized = str(wav_path).lower()
        if normalized not in wav_files:
            wav_files[normalized] = (str(wav_path), str(wav_path))
    for wav_path in dumps_root.rglob('*.WAV'):
        normalized = str(wav_path).lower()
        if normalized not in wav_files:
            wav_files[normalized] = (str(wav_path), str(wav_path))
    
    return sorted(wav_files.values())


def find_all_wav_files_drive(scanner: GoogleDriveScanner, root_folder_id: str) -> List[Tuple[str, str]]:
    """
    Find all WAV files in Google Drive.
    
    Returns:
        List of (file_id, path_string) tuples
    """
    drive_files = scanner.find_all_wav_files(root_folder_id)
    return [(f.file_id, f.path_str) for f in drive_files]


def group_records_by_year(records: List[Dict]) -> Dict[str, List[Dict]]:
    """Group records by year."""
    grouped = defaultdict(list)
    for record in records:
        year = record.get('Year', 'Unknown')
        grouped[year].append(record)
    return dict(grouped)


def generate_metadata_files_local(
    dumps_root: str = "dumps",
    metadata_dir: str = "metadata"
):
    """Generate metadata files from local directory."""
    dumps_path = Path(dumps_root)
    metadata_path = Path(metadata_dir)
    
    if not dumps_path.exists():
        print(f"Error: Directory not found: {dumps_root}")
        return
    
    metadata_path.mkdir(exist_ok=True)
    mapping_path = metadata_path / MAPPING_SUBDIR
    mapping_path.mkdir(parents=True, exist_ok=True)

    # Find Excel files in year folders (for Sex mapping)
    print("Searching for Excel files in year folders...")
    year_excel_files = {}
    
    # Look for year folders (4-digit folder names)
    for year_folder in dumps_path.iterdir():
        if year_folder.is_dir() and year_folder.name.isdigit() and len(year_folder.name) == 4:
            year = year_folder.name
            # Look for Excel files in this year folder
            excel_files = list(year_folder.glob('*.xlsx')) + list(year_folder.glob('*.xls'))
            if excel_files:
                year_excel_files[year] = excel_files[0]
                print(f"  Found Excel file for year {year}: {excel_files[0].name}")
    
    # Load sex mappings from year-specific Excel files
    year_sex_maps = {}
    for year, excel_file in year_excel_files.items():
        try:
            print(f"  Loading sex data from year {year} Excel file...")
            sex_map = load_sex_from_table_local(excel_file)
            if sex_map:
                year_sex_maps[year] = sex_map
                print(f"    Loaded {len(sex_map)} sex mappings for year {year}")
        except Exception as e:
            print(f"  Warning: Could not load sex data for year {year}: {e}")
    
    # Check which years already have mapping index files
    existing_years = set()
    for existing_file in mapping_path.glob("Metadata Recording Mapping (*).xlsx"):
        # Extract year from filename: "Metadata Recording Mapping (2015).xlsx" -> "2015"
        try:
            year_str = existing_file.stem.split('(')[1].split(')')[0]
            existing_years.add(year_str)
        except (IndexError, ValueError):
            continue
    
    if existing_years:
        print(f"Found existing mapping files for years: {sorted(existing_years)}")
        print("These years will be skipped during scanning.")
    
    # Find all WAV files
    print(f"Scanning {dumps_root} for WAV files...")
    wav_files = find_all_wav_files_local(dumps_path)
    print(f"Found {len(wav_files)} WAV files")
    
    # Parse all WAV files, but filter out years that already have files
    records = []
    skipped_years = set()
    for file_path, path_str in wav_files:
        metadata = parse_path_to_metadata(path_str, str(dumps_path), is_drive=False)
        if metadata:
            # Extract year from path: find the source dir in the path
            # parts, then the next component is the year folder.
            path_obj = Path(file_path)
            parts = path_obj.parts
            source_dir_name = dumps_path.resolve().name
            if source_dir_name in parts:
                year_idx = parts.index(source_dir_name) + 1
                year = parts[year_idx] if year_idx < len(parts) else 'Unknown'
            else:
                year = 'Unknown'
            
            # Skip if file already exists for this year
            if year in existing_years:
                if year not in skipped_years:
                    skipped_years.add(year)
                    print(f"Skipping year {year}: Metadata file already exists")
                continue
            
            metadata['Year'] = year
            
            # Try to fill Sex from year-specific table with flexible matching
            if year in year_sex_maps:
                sex_map_data = year_sex_maps[year]
                mother = metadata['Mother']
                name = metadata['Name']
                
                # Try direct match first
                key = (mother, name)
                if isinstance(sex_map_data, dict) and 'original' in sex_map_data:
                    # New format with normalized matching
                    if key in sex_map_data['original']:
                        metadata['Sex'] = sex_map_data['original'][key]
                    else:
                        # Try normalized matching (abbreviated)
                        name_normalized = _normalize_name_for_matching(name)
                        key_normalized = (mother, name_normalized)
                        if key_normalized in sex_map_data['normalized']:
                            metadata['Sex'] = sex_map_data['normalized'][key_normalized]
                        else:
                            # Try flexible matching - check all entries
                            for (table_mother, table_name), table_sex in sex_map_data['original'].items():
                                if table_mother == mother and _match_names(name, table_name):
                                    metadata['Sex'] = table_sex
                                    break
                else:
                    # Old format (backward compatibility)
                    if key in sex_map_data:
                        metadata['Sex'] = sex_map_data[key]
            
            records.append(metadata)
        else:
            print(f"Warning: Could not parse path: {path_str}")
    
    print(f"Parsed {len(records)} records")
    
    # Generate Excel files
    _generate_excel_files(records, metadata_path)


def generate_metadata_files_drive(
    drive_folder_id: Optional[str] = None,
    drive_folder_url: Optional[str] = None,
    metadata_dir: str = "metadata",
    credentials_path: str = "credentials.json"
):
    """Generate metadata files from Google Drive."""
    if not DRIVE_AVAILABLE:
        print("Error: Google Drive support not available. Install dependencies:")
        print("  pip install google-api-python-client google-auth-oauthlib")
        return
    
    # Initialize scanner
    try:
        scanner = GoogleDriveScanner(credentials_path=credentials_path)
    except Exception as e:
        print(f"Error initializing Google Drive scanner: {e}")
        return
    
    # Get folder ID
    if drive_folder_url:
        folder_id = scanner.get_folder_id_from_url(drive_folder_url)
        if not folder_id:
            print(f"Error: Could not extract folder ID from URL: {drive_folder_url}")
            return
    elif drive_folder_id:
        folder_id = drive_folder_id
    else:
        print("Error: Must provide either --drive-folder-id or --drive-folder-url")
        return
    
    metadata_path = Path(metadata_dir)
    metadata_path.mkdir(exist_ok=True)
    mapping_path = metadata_path / MAPPING_SUBDIR
    mapping_path.mkdir(parents=True, exist_ok=True)

    # Check which years already have mapping index files
    existing_years = set()
    for existing_file in mapping_path.glob("Metadata Recording Mapping (*).xlsx"):
        # Extract year from filename: "Metadata Recording Mapping (2015).xlsx" -> "2015"
        try:
            year_str = existing_file.stem.split('(')[1].split(')')[0]
            existing_years.add(year_str)
        except (IndexError, ValueError):
            continue
    
    if existing_years:
        print(f"Found existing mapping files for years: {sorted(existing_years)}")
        print("These years will be skipped during scanning.")
    
    # Find all year folders in Google Drive
    print("Finding year folders in Google Drive...")
    all_year_folders = scanner.find_year_folders(folder_id)
    print(f"Found {len(all_year_folders)} year folder(s): {sorted(all_year_folders.keys())}")
    
    # Filter to only years that don't have metadata files yet
    years_to_scan = {year: folder_id for year, folder_id in all_year_folders.items() 
                     if year not in existing_years}
    
    if not years_to_scan:
        print("All years already have metadata files. Nothing to scan.")
        return
    
    if existing_years:
        skipped_list = [y for y in all_year_folders.keys() if y in existing_years]
        print(f"Skipping year folders: {sorted(skipped_list)}")
    
    print(f"Will scan {len(years_to_scan)} year folder(s): {sorted(years_to_scan.keys())}")
    
    # Find Excel files in year folders (for Sex mapping) - only for years we're scanning
    print("Searching for Excel files in year folders...")
    year_excel_files = {}
    for year, year_folder_id in years_to_scan.items():
        # Look for Excel files in this year folder
        try:
            files_in_year = scanner.list_files_in_folder(year_folder_id)
            for file_item in files_in_year:
                file_name = file_item['name']
                file_mime = file_item.get('mimeType', '')
                
                # Check if it's an Excel file
                if (file_name.lower().endswith(('.xlsx', '.xls')) or 
                    'spreadsheet' in file_mime.lower() or
                    file_mime == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
                    year_excel_files[year] = file_item['id']
                    print(f"  Found Excel file for year {year}: {file_name}")
                    break  # Take first Excel file found in year folder
        except Exception as e:
            print(f"  Warning: Could not search for Excel files in year folder {year}: {e}")
    
    print(f"Found Excel files for {len(year_excel_files)} year(s)")
    
    # Load sex mappings from year-specific Excel files
    year_sex_maps = {}
    for year, excel_file_id in year_excel_files.items():
        try:
            print(f"  Loading sex data from year {year} Excel file...")
            sex_map = load_sex_from_table_drive(scanner, excel_file_id)
            if sex_map:
                year_sex_maps[year] = sex_map
                print(f"    Loaded {len(sex_map)} sex mappings for year {year}")
        except Exception as e:
            print(f"  Warning: Could not load sex data for year {year}: {e}")
    
    # Find all WAV files only in years that need scanning
    print(f"Scanning Google Drive folders for WAV files...")
    all_wav_files = []
    for year, year_folder_id in years_to_scan.items():
        print(f"  Scanning year {year}...")
        year_wav_files = scanner.find_all_wav_files_in_year_folder(year_folder_id, year)
        all_wav_files.extend([(f.file_id, f.path_str) for f in year_wav_files])
        print(f"    Found {len(year_wav_files)} WAV files in year {year}")
    
    print(f"Found {len(all_wav_files)} WAV files total")
    
    # Parse all WAV files
    records = []
    for file_id, path_str in all_wav_files:
        # Extract root folder name for relative path
        path_parts = path_str.split('/')
        if len(path_parts) > 0:
            root_name = path_parts[0]
        else:
            root_name = ""
        
        metadata = parse_path_to_metadata(path_str, root_name, is_drive=True)
        if metadata:
            # Extract year from path (first part)
            year = path_parts[0] if path_parts else 'Unknown'
            metadata['Year'] = year
            
            # Try to fill Sex from year-specific table with flexible matching
            if year in year_sex_maps:
                sex_map_data = year_sex_maps[year]
                mother = metadata['Mother']
                name = metadata['Name']
                
                # Try direct match first
                key = (mother, name)
                if isinstance(sex_map_data, dict) and 'original' in sex_map_data:
                    # New format with normalized matching
                    if key in sex_map_data['original']:
                        metadata['Sex'] = sex_map_data['original'][key]
                    else:
                        # Try normalized matching (abbreviated)
                        name_normalized = _normalize_name_for_matching(name)
                        key_normalized = (mother, name_normalized)
                        if key_normalized in sex_map_data['normalized']:
                            metadata['Sex'] = sex_map_data['normalized'][key_normalized]
                        else:
                            # Try flexible matching - check all entries
                            for (table_mother, table_name), table_sex in sex_map_data['original'].items():
                                if table_mother == mother and _match_names(name, table_name):
                                    metadata['Sex'] = table_sex
                                    break
                else:
                    # Old format (backward compatibility)
                    if key in sex_map_data:
                        metadata['Sex'] = sex_map_data[key]
            
            records.append(metadata)
        else:
            print(f"Warning: Could not parse path: {path_str}")
    
    print(f"Parsed {len(records)} records")
    
    # Generate Excel files
    _generate_excel_files(records, metadata_path)


def _generate_excel_files(records: List[Dict], metadata_path: Path):
    """Generate Excel files from records grouped by year."""
    mapping_path = metadata_path / MAPPING_SUBDIR
    mapping_path.mkdir(parents=True, exist_ok=True)

    records_by_year = group_records_by_year(records)
    
    for year, year_records in records_by_year.items():
        # Check if file already exists
        filename = f"Metadata Recording Mapping ({year}).xlsx"
        output_path = mapping_path / filename
        
        if output_path.exists():
            print(f"\nSkipping year {year}: File already exists ({filename})")
            continue
        
        print(f"\nProcessing year {year}: {len(year_records)} records")
        
        # Sort records for consistency
        year_records.sort(key=lambda x: (
            x['Mother'], x['Name'], x['Day'], x.get('Session', ''), x['Recording Number']
        ))
        
        # Create DataFrame
        df = pd.DataFrame(year_records)
        
        # Reorder columns
        columns_order = [
            'Mother',
            'Mother Genotype',
            'Name',
            'Sex',
            'Offspring Genotype',
            'Day',
            'Session',
            'Channel',
            'Recording Number'
        ]
        # Only include columns that exist in the dataframe
        columns_order = [col for col in columns_order if col in df.columns]
        df = df[columns_order]
        
        # Save to Excel
        df.to_excel(output_path, index=False, engine='openpyxl')
        print(f"  Created: {filename} ({len(year_records)} records)")


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='Generate metadata Excel files from WAV files (local or Google Drive)'
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=False)
    mode_group.add_argument('--local', action='store_true', help='Use local directory mode')
    mode_group.add_argument('--drive', action='store_true', help='Use Google Drive mode')
    
    # Local mode arguments
    parser.add_argument('--source-dir', type=str, default='dumps',
                       help='Local directory to scan for WAV files (default: dumps)')
    
    # Drive mode arguments
    parser.add_argument('--drive-folder-id', type=str,
                       help='Google Drive folder ID to scan')
    parser.add_argument('--drive-folder-url', type=str,
                       help='Google Drive folder URL to scan')
    parser.add_argument('--credentials', type=str, default='credentials.json',
                       help='Path to Google Drive credentials JSON file (default: credentials.json)')
    
    # Common arguments
    parser.add_argument('--metadata-dir', type=str, default='metadata',
                       help='Directory where metadata files will be saved (default: metadata)')
    
    args = parser.parse_args()
    
    # Interactive mode if no mode specified
    if not args.local and not args.drive:
        print("=" * 60)
        print("Generate Metadata - Mode Selection")
        print("=" * 60)
        print("\nSelect mode:")
        print("1. Local directory (scan local folder)")
        print("2. Google Drive (connect to Google Drive)")
        print()
        
        while True:
            choice = input("Enter your choice (1 or 2): ").strip()
            if choice == '1':
                args.local = True
                # Ask for directory in interactive mode
                print("\nEnter the local directory to scan (press Enter for 'dumps'):")
                user_input = input("Directory: ").strip()
                if user_input:
                    args.source_dir = user_input
                break
            elif choice == '2':
                args.drive = True
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")
        
        print()
    
    if args.local:
        # Interactive source directory only in fully interactive mode (no --local flag)
        # If --local was provided, use default or provided value
        generate_metadata_files_local(
            dumps_root=args.source_dir,
            metadata_dir=args.metadata_dir
        )
    elif args.drive:
        # Interactive folder ID/URL if not provided
        if not args.drive_folder_id and not args.drive_folder_url:
            print("\nGoogle Drive folder selection:")
            print("1. Enter folder ID")
            print("2. Enter folder URL")
            print()
            
            while True:
                choice = input("Enter your choice (1 or 2): ").strip()
                if choice == '1':
                    args.drive_folder_id = input("Enter Google Drive folder ID: ").strip()
                    break
                elif choice == '2':
                    args.drive_folder_url = input("Enter Google Drive folder URL: ").strip()
                    break
                else:
                    print("Invalid choice. Please enter 1 or 2.")
        
        generate_metadata_files_drive(
            drive_folder_id=args.drive_folder_id,
            drive_folder_url=args.drive_folder_url,
            metadata_dir=args.metadata_dir,
            credentials_path=args.credentials
        )


if __name__ == "__main__":
    main()
