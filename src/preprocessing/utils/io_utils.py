import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd

OUTPUTS_DIR = "outputs"
OUTPUTS_EXTERNAL_DIR = os.path.join(OUTPUTS_DIR, "external")
OUTPUTS_EXTERNAL_INPUT_DIR = os.path.join(OUTPUTS_EXTERNAL_DIR, "input")
OUTPUTS_EXTERNAL_AGGREGATED_DIR = os.path.join(OUTPUTS_EXTERNAL_DIR, "aggregated")
# Aggregated outputs are split by consumer so the two pipelines never collide on a
# shared file name (see docs/NEURAL_NETWORK_BASELINE.md): the tabular pipeline reads the
# 48-column aggregate CSVs, the sequence pipeline reads the syllable-level XLSX exports.
OUTPUTS_EXTERNAL_AGGREGATED_TABULAR_DIR = os.path.join(OUTPUTS_EXTERNAL_AGGREGATED_DIR, "tabular")
OUTPUTS_EXTERNAL_AGGREGATED_SEQUENCE_DIR = os.path.join(OUTPUTS_EXTERNAL_AGGREGATED_DIR, "sequence")
# Metadata-driven pipeline artifacts: per-file segmentations, internal aggregate, default logs.
OUTPUTS_LEGACY_DIR = os.path.join(OUTPUTS_DIR, "legacy")


def list_metadata_files(metadata_dir: str = "metadata") -> List[str]:
    """
    Returns a sorted list of Excel filenames in the specified directory.

    Only the top level of ``metadata_dir`` is scanned; subdirectories (e.g.
    ``metadata/mapping/``) are ignored so reference index files are not picked
    up by the preprocessing pipeline.

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


def is_segmentation_file_exist(file_name: str, outputs_dir: str = OUTPUTS_LEGACY_DIR) -> bool:
    """
    Check if segmentation Excel file exists for a metadata file.

    Args:
        file_name: Name of the metadata file (e.g., "Data 2015 For Syl Segmentation_1.xlsx")
        outputs_dir: Path to the outputs directory (default: ``outputs/legacy``)

    Returns:
        True if the segmentation Excel file exists, False otherwise
    """
    outputs_path = Path(outputs_dir)
    output_filename = get_output_filename(file_name)
    xlsx_file = outputs_path / output_filename
    return xlsx_file.exists()


def is_already_processed(file_name: str, outputs_dir: str = OUTPUTS_LEGACY_DIR) -> bool:
    """
    Check if a metadata file has already been fully processed.

    A file is considered processed if all expected output files exist under
    the selected ``outputs_dir``:
    - <outputs_dir>/<file_name> (xlsx)
    - <outputs_dir>/<stem>.csv
    - <outputs_dir>/<stem>.npy

    Args:
        file_name: Name of the metadata file (e.g., "metadata_2022.xlsx")
        outputs_dir: Path to the outputs directory (default: ``outputs/legacy``)

    Returns:
        True if all expected output files exist, False otherwise
    """
    outputs_path = Path(outputs_dir)
    output_filename = get_output_filename(file_name)
    output_stem = Path(output_filename).stem

    # Expected output files
    xlsx_file = outputs_path / output_filename
    csv_file = outputs_path / f"{output_stem}.csv"
    npy_file = outputs_path / f"{output_stem}.npy"

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


def _header_match_key(name: str) -> str:
    """Normalize a header label for alias lookup (case- and separator-insensitive)."""
    s = str(name).strip()
    if not s:
        return ""
    s = s.lower()
    for ch in (" ", "\t", "\n", "_", "-", "/", "\\", "(", ")", "[", "]", "{", "}", ".", ",", ":", ";", "|", '"', "'"):
        s = s.replace(ch, "")
    return s


# Alternate Excel headers → canonical METADATA_REQUIRED_COLUMNS.
# Covers Hebrew lab sheets, common typos and English variants seen in field workbooks.
_METADATA_CANONICAL_ALIASES: Dict[str, Tuple[str, ...]] = {
    "Mother": (
        "Mother",
        "mother",
        "MOTHER",
        "אם",
        "אמא",
        "עכברת אם",
        "אם עכברוש",
    ),
    "Mother Genotype": (
        "Mother Genotype",
        "mother genotype",
        "Maternal genotype",
        "maternal genotype",
        "MATERNAL GENOTYPE",
        "גנוטיפ אם",
        "גנטיקת אם",
        "גנוטיפ האם",
    ),
    "Name": (
        "Name",
        "name",
        "MOUSE NAME",
        "mouse name",
        "שם גור",
        "שם הגור",
        "שם פרטי גור",
        "גור",
        "Pup",
        "pup name",
        "Pup name",
    ),
    "Sex": (
        "Sex",
        "sex",
        "gender",
        "Gender",
        "GENDER",
        "gender/sex",
        "sex/gender",
        "gender sex",
        "sex gender",
        "מין",
        "מגדר",
    ),
    "Offspring Genotype": (
        "Offspring Genotype",
        "offspring genotype",
        "OFFSPRING GENOTYPE",
        "pup genotype",
        "Pup genotype",
        "Genotype",
        "genotype",
        "Genotytpe",
        "גנוטיפ גור",
        "גנטיקת גור",
        "גנוטיפ הצאצא",
    ),
    "Day": (
        "Day",
        "day",
        "יום",
        "גיל",
        "גיל (ימים)",
        "גיל בימים",
    ),
    "Session": (
        "Session",
        "session",
        "סשן",
        "מפגש",
    ),
    "Recording Number": (
        "Recording Number",
        "recording number",
        "Recording number",
        "מספר הקלטה",
        "מספר קובץ",
    ),
}


def _metadata_alias_lookup() -> Dict[str, str]:
    """Map normalized header key → canonical column (first alias wins per key)."""
    out: Dict[str, str] = {}
    for canon, aliases in _METADATA_CANONICAL_ALIASES.items():
        for a in aliases:
            k = _header_match_key(a)
            if k and k not in out:
                out[k] = canon
    return out


def get_metadata_alias_lookup() -> Dict[str, str]:
    """Public accessor for the alias map (callers should treat the return as read-only)."""
    return _metadata_alias_lookup()


def normalize_metadata_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strip headers and rename known aliases (English / Hebrew) to ``METADATA_REQUIRED_COLUMNS``.

    Workbooks with Hebrew headers (e.g. ``טבלת עכברים``) or non-canonical English headers
    (``GENDER`` instead of ``Sex``) are still accepted by downstream steps after this pass.
    """
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    lookup = get_metadata_alias_lookup()
    rename: Dict[str, str] = {}
    assigned = {c for c in out.columns if c in METADATA_REQUIRED_COLUMNS}

    for col in list(out.columns):
        if col in METADATA_REQUIRED_COLUMNS:
            continue
        k = _header_match_key(col)
        if not k or k not in lookup:
            continue
        canon = lookup[k]
        if canon in assigned:
            continue
        rename[col] = canon
        assigned.add(canon)

    return out.rename(columns=rename)


def metadata_columns_satisfied(column_names: Set[str]) -> bool:
    """Return True if *column_names* covers every METADATA_REQUIRED_COLUMNS (after alias rules)."""
    dummy = pd.DataFrame(columns=sorted(column_names))
    normalized = normalize_metadata_columns(dummy)
    have = {str(c).strip() for c in normalized.columns}
    return all(req in have for req in METADATA_REQUIRED_COLUMNS)


def _read_excel_with_header_detection(
    metadata_path: str,
    required_columns: Tuple[str, ...],
    max_scan_rows: int = 20,
):
    """
    Read first sheet while detecting the header row in the first *max_scan_rows* rows.

    Some lab workbooks place a title row above the headers, or use mixed labels like
    ``GENDER/SEX``. We scan early rows and pick the first one that maps to all required
    canonical columns after alias normalization.
    """
    engines = ("openpyxl", "xlrd")
    for engine in engines:
        try:
            probe = pd.read_excel(
                metadata_path,
                sheet_name=0,
                header=None,
                nrows=max_scan_rows,
                engine=engine,
            )
        except Exception:
            continue
        if probe.empty:
            continue
        for ridx in range(min(max_scan_rows, len(probe))):
            raw_headers = [str(v).strip() for v in probe.iloc[ridx].tolist()]
            dummy = pd.DataFrame(columns=raw_headers)
            mapped = normalize_metadata_columns(dummy)
            have = {str(c).strip() for c in mapped.columns}
            if all(req in have for req in required_columns):
                return pd.read_excel(
                    metadata_path,
                    sheet_name=0,
                    header=ridx,
                    engine=engine,
                )
    # Fall back to the default header row when no candidate row matched.
    for engine in engines:
        try:
            return pd.read_excel(metadata_path, sheet_name=0, engine=engine)
        except Exception:
            continue
    raise ValueError(f"Could not read workbook: {metadata_path}")


# Pup summary workbooks (e.g. ``USV pups 2024 summary.xlsx``, ``טבלת עכברים``):
# one row per pup with Gender. Used as a Sex / supplement lookup when WAV layout
# alone supplies the per-recording rows (mirrors generate_metadata.py behaviour).
PUP_SUMMARY_REQUIRED_COLUMNS: Tuple[str, str, str] = ("Mother", "Name", "Sex")


def pup_summary_columns_satisfied(column_names: Set[str]) -> bool:
    """True if the sheet has Mother, Name and Sex (or Gender / GENDER / …) after header normalization."""
    dummy = pd.DataFrame(columns=sorted(column_names))
    normalized = normalize_metadata_columns(dummy)
    have = {str(c).strip() for c in normalized.columns}
    return all(req in have for req in PUP_SUMMARY_REQUIRED_COLUMNS)


def build_sex_lookup_from_pup_summary_xlsx(metadata_path: str) -> Dict[Tuple[str, str], str]:
    """
    Load a pup-summary Excel and return mapping ``(mother, name_key) -> M | F | U``.

    Keys include both ``(mother.upper(), pup_identity_key(name))`` and ``(mother, name)``
    so callers can match either folder-derived keys or exact Excel labels.
    """
    from .audio_paths import pup_identity_key

    df = _read_excel_with_header_detection(
        metadata_path,
        PUP_SUMMARY_REQUIRED_COLUMNS,
    )
    df = normalize_metadata_columns(df)
    if not all(c in df.columns for c in PUP_SUMMARY_REQUIRED_COLUMNS):
        return {}
    out: Dict[Tuple[str, str], str] = {}
    for _, row in df.iterrows():
        m = str(row["Mother"]).strip()
        n = str(row["Name"]).strip()
        if not m or not n or m.lower() in ("nan", "none"):
            continue
        if n.lower() in ("nan", "none"):
            continue
        sx = normalize_sex_cell(row["Sex"])
        mu = m.upper()
        nk = pup_identity_key(n)
        out[(mu, nk)] = sx
        out[(m, n)] = sx
    return out


def _find_first_matching_column(df: pd.DataFrame, aliases: Tuple[str, ...]) -> Optional[str]:
    """Return the first column in *df* whose normalized header matches one of *aliases*."""
    wanted = {_header_match_key(a) for a in aliases}
    for c in df.columns:
        if _header_match_key(c) in wanted:
            return str(c)
    return None


def normalize_supplement_cell(value: Any) -> Optional[int]:
    """Map supplement labels to 1/0; return None for unknown / empty values."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    s = str(value).strip()
    if not s:
        return None
    low = s.lower()
    if low in ("0", "false", "no", "none", "ללא תיסוף"):
        return 0
    if low in ("1", "true", "yes", "עם תיסוף"):
        return 1
    return None


def build_pup_summary_details_lookup_xlsx(
    metadata_path: str,
) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """
    Load a pup-summary workbook and return per-pup details by (mother, normalized name).

    Details include normalized sex, offspring genotype and a 0/1 supplement flag
    when the workbook exposes those columns.
    """
    from .audio_paths import pup_identity_key

    df = _read_excel_with_header_detection(
        metadata_path,
        PUP_SUMMARY_REQUIRED_COLUMNS,
    )
    df = normalize_metadata_columns(df)
    if not all(c in df.columns for c in PUP_SUMMARY_REQUIRED_COLUMNS):
        return {}

    supp_col = _find_first_matching_column(df, ("Supplements", "Supplement", "SUPP", "SUP"))
    out: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for _, row in df.iterrows():
        m = str(row["Mother"]).strip()
        n = str(row["Name"]).strip()
        if not m or not n or m.lower() in ("nan", "none") or n.lower() in ("nan", "none"):
            continue
        mu = m.upper()
        nk = pup_identity_key(n)
        detail = {
            "sex": normalize_sex_cell(row["Sex"]),
            "offspring_genotype": str(row.get("Offspring Genotype", "")).strip(),
            "supplement": normalize_supplement_cell(row[supp_col]) if supp_col else None,
        }
        out[(mu, nk)] = detail
        out[(m, n)] = detail
    return out


# Column names for segmentation results Excel file
# These are the metadata columns plus segmentation-specific columns
SEGMENTATION_RESULT_COLUMNS = METADATA_REQUIRED_COLUMNS + [
    "Start point(s)",
    "End point(s)",
]

# Column names used by the feature extraction step
FEATURE_COLUMNS = [
    "Name", "Day", "Session",
    "Start Point (Hz)", "End Point (Hz)", "Duration (time)",
    "Syllable number", "Recording Number",
    "Mother Genotype", "Sex", "ISI_time", "Offspring Genotype",
    "Strain",
]

# 48-column aggregated CSV (headerless training file); matches train_classifier.COL_NAMES
AGGREGATE_COL_NAMES = [
    'syll1_s_freq', 'syll2_s_freq', 'syll3_s_freq', 'syll4_s_freq', 'syll5_s_freq',
    'syll6_s_freq', 'syll7_s_freq', 'syll8_s_freq', 'syll9_s_freq', 'syll10_s_freq',
    'syll1_e_freq', 'syll2_e_freq', 'syll3_e_freq', 'syll4_e_freq', 'syll5_e_freq',
    'syll6_e_freq', 'syll7_e_freq', 'syll8_e_freq', 'syll9_e_freq', 'syll10_e_freq',
    'syll1_dist', 'syll2_dist', 'syll3_dist', 'syll4_dist', 'syll5_dist',
    'syll6_dist', 'syll7_dist', 'syll8_dist', 'syll9_dist', 'syll10_dist',
    'syll1_dur', 'syll2_dur', 'syll3_dur', 'syll4_dur', 'syll5_dur',
    'syll6_dur', 'syll7_dur', 'syll8_dur', 'syll9_dur', 'syll10_dur',
    'mother_gen', 'pup_sex', 'avg_ISI_time', 'pup_age', 'session', 'pup_strain',
    'pup_gen', 'mouse_idx',
]

# Binary genotype in aggregated CSV: WT=0, HT/HET=1
GENOTYPE_NUM_TO_LABEL = {0: 'WT', 1: 'HT'}

# Year-to-strain mapping: 2022+ recordings are strain 1, 2015/2018 are strain 2.
# Kept distinct from segmentation-app's text label ("BALB/C+BLACK/C57") because the
# numeric Strain feeds the tabular classifier (see ``train_classifier.COL_NAMES``).
STRAIN_1_YEARS = {2022, 2023, 2024}


def strain_from_year(year) -> int:
    """Return the strain identifier (1 or 2) for a given recording year."""
    return 1 if int(year) in STRAIN_1_YEARS else 2


def replace_extension(file_path: str, new_ext: str) -> str:
    """Return *file_path* with its extension replaced by *new_ext*.

    >>> replace_extension("outputs/segmentation_2015_1.xlsx", ".csv")
    'outputs/segmentation_2015_1.csv'
    """
    base, _ = os.path.splitext(file_path)
    if not new_ext.startswith('.'):
        new_ext = f'.{new_ext}'
    return base + new_ext


# Regular expression pattern to extract 4-digit year (1900-2099) from filenames
# Used to identify the year from metadata file names (e.g., "metadata_2022.xlsx" -> "2022")
_YEAR_REGEX_PATTERN = re.compile(r"(19|20)\d{2}")


def extract_year_from_filename(file_name: str) -> str:
    """Extract a 4-digit year (e.g., 2015) from the filename."""
    m = _YEAR_REGEX_PATTERN.search(file_name)
    if not m:
        raise ValueError(f"Could not extract year from filename: {file_name}")
    return m.group(0)


def get_output_filename(metadata_file_name: str) -> str:
    """
    Generate output filename from metadata file name.

    Converts metadata filename like "Data 2015 For Syl Segmentation_1.xlsx"
    to output filename like "segmentation_2015_1.xlsx"

    Args:
        metadata_file_name: Name of the metadata file

    Returns:
        Output filename for segmentation/features/classification results
    """
    year = extract_year_from_filename(metadata_file_name)

    # Extract the number from the filename (e.g., "_1" from "Segmentation_1.xlsx")
    number_match = re.search(r'_(\d+)\.xlsx$', metadata_file_name)
    if number_match:
        number = number_match.group(1)
    else:
        # Fallback: use the whole filename stem if no number found
        stem = Path(metadata_file_name).stem
        number = stem.replace(' ', '_').lower()

    return f"segmentation_{year}_{number}.xlsx"


def normalize_sex_cell(value: Any) -> str:
    """
    Map spreadsheet sex values to ``M`` / ``F`` / ``U``.

    Handles empty cells, common English words and short Hebrew labels so that
    workbooks with mixed conventions still produce a clean Sex column.
    """
    if value is None:
        return "U"
    if isinstance(value, float) and pd.isna(value):
        return "U"
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none", "-", "—", "n/a", "na"):
        return "U"
    low = s.lower()
    if low in ("m", "male", "זכר", "גבר"):
        return "M"
    if low in ("f", "female", "נקבה", "אשה"):
        return "F"
    if low in ("u", "unk", "unknown"):
        return "U"
    u = s.upper()
    if u in ("M", "F", "U"):
        return u
    if len(u) == 1 and u in "MFU":
        return u
    return "U"


def read_metadata_as_lists(metadata_path: str) -> Dict[str, List]:
    """
    Read the first sheet of the metadata Excel file and return a dict:
    {column_name: list_of_values}, for METADATA_REQUIRED_COLUMNS only.

    Header rows are auto-detected within the first 20 rows so workbooks with
    title banners are still accepted; aliases (Hebrew, ``GENDER``, ``Pup name``…)
    are renamed to their canonical English labels and the ``Sex`` column is
    normalized to ``M`` / ``F`` / ``U``.
    """
    df = _read_excel_with_header_detection(
        metadata_path,
        tuple(METADATA_REQUIRED_COLUMNS),
    )
    df = normalize_metadata_columns(df)

    missing = [c for c in METADATA_REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {metadata_path}: {missing}")

    df = df[METADATA_REQUIRED_COLUMNS].dropna(how="all")
    if df.empty:
        raise ValueError(f"No metadata rows found in {metadata_path}")

    out = {c: df[c].tolist() for c in METADATA_REQUIRED_COLUMNS}
    out["Sex"] = [normalize_sex_cell(v) for v in out["Sex"]]
    return out
