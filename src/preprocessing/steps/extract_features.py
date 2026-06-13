from __future__ import annotations

import glob
import logging
import os
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from legacy.audio_feature_extraction_reduction_by_recording import feature_extraction
from utils import (
    AGGREGATE_COL_NAMES,
    FEATURE_COLUMNS,
    GENOTYPE_NUM_TO_LABEL,
    OUTPUTS_EXTERNAL_AGGREGATED_DIR,
    replace_extension,
    strain_from_year,
)

# Per-file segmentations and internal aggregate live under outputs/legacy/ (see run_pipeline).
AGGREGATED_SUBDIR = "aggregated"
ALL_DATA_XLSX_NAME = "all_data.xlsx"
ALL_DATA_CSV_NAME = "all_data.csv"


def read_segmentation_data(file_path: str) -> pd.DataFrame:
    """Read a segmentation Excel file into a DataFrame."""
    return pd.read_excel(file_path)


def add_strain_column(dataset: pd.DataFrame, year: str) -> pd.DataFrame:
    """Add a Strain column to the DataFrame based on the recording year.

    Uses `strain_from_year` to map the year to a strain identifier
    (1 for 2022+ recordings, 2 for 2015/2018).
    """
    dataset["Strain"] = strain_from_year(year)
    return dataset


def add_strain_from_path(dataset: pd.DataFrame) -> pd.DataFrame:
    """Add a Strain column by extracting the year from the Path column.

    The Path column contains recording file paths like
    ``USV_Recordings/2022/...``. The second path component is the year.
    """
    dataset["Strain"] = [
        strain_from_year(x.split('/')[1]) for x in dataset["Path"]
    ]
    return dataset


def select_feature_columns(dataset: pd.DataFrame) -> pd.DataFrame:
    """Select only the columns required by the feature extraction pipeline."""
    return dataset[FEATURE_COLUMNS]


def compute_features(X: pd.DataFrame) -> np.ndarray:
    """Run the feature extraction algorithm on the selected columns.

    Groups data by mouse, day, session, and recording, then computes
    per-recording features: average start/end frequencies per syllable type,
    syllable distribution, average duration, mother genotype, pup sex,
    mean ISI time, age, session, strain, offspring genotype, and mouse index.
    """
    return feature_extraction(X)


def save_features_csv(
    mouse_final_data: np.ndarray,
    file_path: str,
) -> str:
    """Save the extracted feature matrix to a CSV file.

    The CSV is saved alongside the source Excel file, with the same
    base name but a .csv extension.

    Returns the path to the saved CSV file.
    """
    output_csv = replace_extension(file_path, ".csv")
    np.savetxt(output_csv, X=mouse_final_data, delimiter=",")
    return output_csv


def load_all_segmentation_files(outputs_dir: str) -> List[str]:
    """Return paths to per-file segmentation workbooks (``segmentation_*.xlsx``) in *outputs_dir* root.

    Only the flat ``outputs_dir`` is scanned; ``aggregated/`` and other subfolders are ignored.
    This avoids picking up ``all_data.xlsx`` or other unrelated Excel files.
    """
    pattern = os.path.join(outputs_dir, "segmentation_*.xlsx")
    return sorted(glob.glob(pattern))


def concat_segmentation_files(file_paths: List[str]) -> pd.DataFrame:
    """Read and concatenate multiple segmentation Excel files into one DataFrame."""
    return pd.concat(
        (pd.read_excel(f) for f in file_paths), ignore_index=True
    )


def save_aggregated_excel(
    dataset: pd.DataFrame,
    aggregated_dir: str,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Save the combined dataset as ``all_data.xlsx`` under *aggregated_dir*.

    Overwrites an existing file at the same path. Returns the path written.
    """
    os.makedirs(aggregated_dir, exist_ok=True)
    output_path = os.path.join(aggregated_dir, ALL_DATA_XLSX_NAME)
    if logger:
        if os.path.isfile(output_path):
            logger.info(f"Overwriting existing file: {output_path}")
    dataset.to_excel(output_path, index=False)
    return output_path


def run_feature_extraction(
    file_path: str,
    year: str,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Run feature extraction on a single segmentation Excel file.

    Orchestrates five steps:
    1. Read the segmentation Excel into a DataFrame
    2. Add a Strain column derived from the recording year
    3. Select the feature columns required by the extraction algorithm
    4. Compute per-recording features (frequencies, distribution, duration, etc.)
    5. Save the feature matrix as a CSV file

    Args:
        file_path: Path to the segmentation Excel file
        year: Recording year (used to derive Strain)
        logger: Optional logger instance

    Returns:
        Path to the output CSV file
    """
    if logger:
        logger.info("Feature extraction started")

    dataset = read_segmentation_data(file_path)
    dataset = add_strain_column(dataset, year)
    X = select_feature_columns(dataset)
    mouse_final_data = compute_features(X)
    output_csv = save_features_csv(mouse_final_data, file_path)

    if logger:
        logger.info(f"Feature extraction finished: {output_csv}")

    return output_csv


def run_aggregated_feature_extraction(
    outputs_dir: str,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Aggregate all segmentation Excel files and run feature extraction.

    Orchestrates six steps:
    1. Find all segmentation Excel files in the outputs directory
    2. Concatenate them into a single DataFrame
    3. Add a Strain column derived from the year in each recording Path
    4. Save the combined dataset as ``outputs/legacy/aggregated/all_data.xlsx``
    5. Select the feature columns and compute per-recording features
    6. Save the aggregated feature matrix as ``outputs/legacy/aggregated/all_data.csv``

    Existing ``all_data.*`` files in that subdirectory are overwritten.

    Args:
        outputs_dir: Directory containing the per-file ``segmentation_*.xlsx`` workbooks
            (typically ``outputs/legacy``).
        logger: Optional logger instance

    Returns:
        Path to the aggregated CSV file
    """
    if logger:
        logger.info("Aggregating features from all processed files")

    aggregated_dir = os.path.join(outputs_dir, AGGREGATED_SUBDIR)
    os.makedirs(aggregated_dir, exist_ok=True)

    all_files = load_all_segmentation_files(outputs_dir)
    if logger:
        logger.info(f"Found {len(all_files)} processed file(s)")

    dataset = concat_segmentation_files(all_files)
    dataset = add_strain_from_path(dataset)
    save_aggregated_excel(dataset, aggregated_dir, logger=logger)

    X = select_feature_columns(dataset)
    mouse_final_data = compute_features(X)

    output_csv = os.path.join(aggregated_dir, ALL_DATA_CSV_NAME)
    if logger and os.path.isfile(output_csv):
        logger.info(f"Overwriting existing file: {output_csv}")
    np.savetxt(output_csv, X=mouse_final_data, delimiter=",")

    if logger:
        logger.info(f"Finished aggregating features: {output_csv}")

    return output_csv


ALL_DATA_EXTERNAL_MAIN_XLSX_NAME = "all_data_external_main.xlsx"
ALL_DATA_EXTERNAL_MAIN_CSV_NAME = "all_data_external_main.csv"
ALL_DATA_EXTERNAL_BASELINE_XLSX_NAME = "all_data_external_baseline.xlsx"
ALL_DATA_EXTERNAL_BASELINE_CSV_NAME = "all_data_external_baseline.csv"

# Filters applied together to produce the official training baseline.
# invalid_genotype is already enforced via drop_non_binary_genotype_rows_for_external.
# Noise==1 syllables are kept in the baseline (flat start/end frequency USVs).
# Use --external-filter noise for a variant that excludes them.
BASELINE_FILTERS = ("invalid_sex", "supplement_offspring")

EXTERNAL_FILTERS: Dict[str, str] = {
    "invalid_sex": "invalid_sex",
    "noise": "noise",
    "supplement_offspring": "supplement_offspring",
    "undefined_syllable": "undefined_syllable",
}

_BINARY_GENOTYPES = frozenset({"WT", "HET"})

_STRAIN_TEXT_TO_NUMERIC = {
    "balb/c": 2,
    "balb/c+black/c57": 1,
}

_VALID_SEX = {"M", "F"}


def _normalize_token(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip().upper()


def _to_bool_mask(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    mask_numeric = numeric == 1
    text = series.astype(str).str.strip().str.lower()
    mask_text = text.isin({"1", "true", "yes", "y"})
    return mask_numeric.fillna(False) | mask_text


def normalize_session_values(
    dataset: pd.DataFrame,
    logger: Optional[logging.Logger] = None,
) -> pd.DataFrame:
    """Normalize Session=0 to 1."""
    if "Session" not in dataset.columns:
        return dataset

    zero_sessions = dataset["Session"] == 0
    if zero_sessions.any():
        dataset.loc[zero_sessions, "Session"] = 1
        if logger:
            logger.info(
                f"Replaced {zero_sessions.sum()} Session=0 values with 1"
            )
    return dataset


def add_strain_from_column(
    dataset: pd.DataFrame,
    logger: Optional[logging.Logger] = None,
) -> pd.DataFrame:
    """Map textual Strain labels to the numeric 1/2 encoding."""
    if "Strain" not in dataset.columns:
        if logger:
            logger.warning("Strain column missing, falling back to Path-derived strain.")
        return add_strain_from_path(dataset)

    values: List[int] = []
    fallback_count = 0
    missing_count = 0

    has_path = "Path" in dataset.columns
    for idx, strain_value in enumerate(dataset["Strain"]):
        path_value = dataset["Path"].iloc[idx] if has_path else None
        num_value: Optional[int] = None

        if isinstance(strain_value, (int, float)) and not pd.isna(strain_value):
            iv = int(strain_value)
            if iv in (1, 2):
                num_value = iv

        if num_value is None:
            key = " ".join(str(strain_value).strip().lower().split())
            num_value = _STRAIN_TEXT_TO_NUMERIC.get(key)

        if num_value is None:
            fallback_count += 1
            try:
                year = str(path_value).split("/")[1]
                num_value = strain_from_year(year)
            except Exception:
                missing_count += 1
                num_value = np.nan

        values.append(num_value)

    dataset["Strain"] = values

    if logger:
        if fallback_count:
            logger.warning(
                f"Strain mapping fallback used for {fallback_count} row(s) based on Path year."
            )
        if missing_count:
            logger.warning(
                f"Could not map Strain for {missing_count} row(s); values left as NaN."
            )

    return dataset


def drop_non_binary_genotype_rows_for_external(
    dataset: pd.DataFrame,
    logger: Optional[logging.Logger] = None,
) -> pd.DataFrame:
    """Keep rows where mother and offspring genotypes are WT or HET after HT→HET.

    Matches ``audio_feature_extraction_reduction_by_recording`` so ``LabelEncoder``
    in legacy feature extraction sees only two classes for binary training.
    Applied to every external aggregate (main and ``--external-filter`` variants).
    """
    required = ("Offspring Genotype", "Mother Genotype")
    if any(c not in dataset.columns for c in required):
        if logger:
            logger.warning(
                "drop_non_binary_genotype_rows_for_external: genotype columns missing; "
                "skipping row filter."
            )
        return dataset

    before = len(dataset)
    mother = dataset["Mother Genotype"].replace("HT", "HET")
    offspring = dataset["Offspring Genotype"].replace("HT", "HET")
    m_norm = mother.map(_normalize_token)
    o_norm = offspring.map(_normalize_token)
    keep = m_norm.isin(_BINARY_GENOTYPES) & o_norm.isin(_BINARY_GENOTYPES)
    out = dataset.loc[keep].reset_index(drop=True)
    removed = before - len(out)
    if logger:
        logger.info(
            f"Dropped {removed} row(s) with non-binary genotype "
            f"(mother and offspring must be WT or HET after HT→HET); "
            f"{len(out)} row(s) remaining"
        )
    return out


def apply_single_external_filter(
    dataset: pd.DataFrame,
    filter_name: str,
    logger: Optional[logging.Logger] = None,
) -> Tuple[pd.DataFrame, int]:
    """Apply one external aggregation filter and return filtered data + removed count."""
    if filter_name == "invalid_sex":
        if "Sex" not in dataset.columns:
            if logger:
                logger.warning("Filter invalid_sex requested but Sex column is missing.")
            return dataset, 0
        sex = dataset["Sex"].map(_normalize_token)
        mask = ~sex.isin(_VALID_SEX)
    elif filter_name == "noise":
        if "Noise" not in dataset.columns:
            if logger:
                logger.warning("Filter noise requested but Noise column is missing.")
            return dataset, 0
        mask = pd.to_numeric(dataset["Noise"], errors="coerce").fillna(0) == 1
    elif filter_name == "supplement_offspring":
        if "Supplement (Offspring)" not in dataset.columns or "Name" not in dataset.columns:
            if logger:
                logger.warning(
                    "Filter supplement_offspring requested but required columns are missing."
                )
            return dataset, 0
        supplemented = _to_bool_mask(dataset["Supplement (Offspring)"])
        names = set(dataset.loc[supplemented, "Name"].dropna().astype(str))
        mask = dataset["Name"].astype(str).isin(names)
    elif filter_name == "undefined_syllable":
        if "Syllable number" not in dataset.columns:
            if logger:
                logger.warning(
                    "Filter undefined_syllable requested but Syllable number column is missing."
                )
            return dataset, 0
        mask = pd.to_numeric(dataset["Syllable number"], errors="coerce") == 10
    else:
        if logger:
            logger.warning(f"Unknown filter requested: {filter_name}")
        return dataset, 0

    removed = int(mask.sum())
    filtered = dataset.loc[~mask].reset_index(drop=True)
    if logger:
        logger.info(
            f"Applied external filter '{filter_name}': removed {removed} row(s), "
            f"{len(filtered)} row(s) remaining"
        )
    return filtered, removed


def save_labeled_aggregate_csv(
    mouse_final_data: np.ndarray,
    output_csv: str,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Write human-readable aggregate CSV with HT/WT genotype labels."""
    base, ext = os.path.splitext(output_csv)
    labeled_path = f"{base}_labeled{ext}"
    df = pd.DataFrame(mouse_final_data, columns=AGGREGATE_COL_NAMES)
    for col in ("mother_gen", "pup_gen"):
        df[col] = df[col].map(GENOTYPE_NUM_TO_LABEL)
    df.to_csv(labeled_path, index=False)
    if logger:
        logger.info(f"Wrote labeled aggregate: {labeled_path}")
    return labeled_path


def save_external_aggregate_outputs(
    dataset: pd.DataFrame,
    output_dir: str,
    xlsx_name: str,
    csv_name: str,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Save one external aggregate trio, routed by consumer to avoid name collisions:

    - syllable-level ``xlsx`` -> ``<output_dir>/sequence/`` (read by the sequence pipeline)
    - 48-column aggregate ``csv`` + labeled csv -> ``<output_dir>/tabular/`` (read by the
      tabular pipeline)

    Previously both were written side-by-side in ``output_dir``; the sequence pipeline
    caches its xlsx as ``<name>.csv``, which clobbered the tabular ``<name>.csv``.
    See docs/NEURAL_NETWORK_BASELINE.md.
    """
    tabular_dir = os.path.join(output_dir, "tabular")
    sequence_dir = os.path.join(output_dir, "sequence")
    os.makedirs(tabular_dir, exist_ok=True)
    os.makedirs(sequence_dir, exist_ok=True)
    output_xlsx = os.path.join(sequence_dir, xlsx_name)
    output_csv = os.path.join(tabular_dir, csv_name)

    if logger and os.path.isfile(output_xlsx):
        logger.info(f"Overwriting existing file: {output_xlsx}")
    dataset.to_excel(output_xlsx, index=False)

    X = select_feature_columns(dataset)
    mouse_final_data = compute_features(X)

    if logger and os.path.isfile(output_csv):
        logger.info(f"Overwriting existing file: {output_csv}")
    np.savetxt(output_csv, X=mouse_final_data, delimiter=",")
    save_labeled_aggregate_csv(mouse_final_data, output_csv, logger=logger)

    return output_csv


def run_external_aggregated_feature_extraction(
    external_file: str,
    output_dir: str = "",
    enabled_filters: Optional[Iterable[str]] = None,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Run feature extraction on the external segmentation file (preferred dataset).

    This produces the **preferred** training data. The external file contains
    correct individual genotyping, unlike the pipeline-aggregated data which
    had genotype labeling errors. Always use this output (``--external``) for
    training unless you have a specific reason not to.

    Same pipeline as ``run_aggregated_feature_extraction`` but reads one
    pre-concatenated workbook instead of globbing individual per-file
    segmentation workbooks.

    Args:
        external_file: Path to the external Excel file
            (e.g. ``outputs/external/input/segmentation_classification_all_data.xlsx``).
        output_dir: Directory to write ``all_data_external_*.xlsx/csv``.
            Defaults to ``outputs/external/aggregated``.
        enabled_filters: Optional iterable of single-filter variant keys to generate.
            Supported values are ``invalid_sex``, ``noise``,
            ``supplement_offspring``, ``undefined_syllable``.
            Rows with non-binary mother/offspring genotype (not WT/HET after HT→HET)
            are always dropped before any output is written.
        logger: Optional logger instance.

    Returns:
        Path to the main external aggregated CSV file.
    """
    if not output_dir:
        output_dir = OUTPUTS_EXTERNAL_AGGREGATED_DIR

    if logger:
        logger.info(
            f"Aggregating features from external file: {external_file} -> {output_dir}"
        )

    os.makedirs(output_dir, exist_ok=True)

    dataset = pd.read_excel(external_file)
    if logger:
        logger.info(f"Loaded {len(dataset)} rows from {external_file}")

    dataset = drop_non_binary_genotype_rows_for_external(dataset, logger=logger)
    dataset = normalize_session_values(dataset, logger=logger)
    dataset = add_strain_from_column(dataset, logger=logger)

    main_csv = save_external_aggregate_outputs(
        dataset=dataset,
        output_dir=output_dir,
        xlsx_name=ALL_DATA_EXTERNAL_MAIN_XLSX_NAME,
        csv_name=ALL_DATA_EXTERNAL_MAIN_CSV_NAME,
        logger=logger,
    )

    if logger:
        logger.info(f"Finished main external aggregation: {main_csv}")

    # --- official baseline export (always generated) ----------------------------
    # Applies invalid_sex + supplement_offspring on top of the genotype binary
    # drop that is already embedded in `dataset` (Noise==1 rows retained).
    # Required data source for all training-matrix runs (Issue #42 / #46).
    baseline = dataset.copy()
    for _f in BASELINE_FILTERS:
        baseline, _removed = apply_single_external_filter(baseline, _f, logger=logger)
    baseline_csv = save_external_aggregate_outputs(
        dataset=baseline,
        output_dir=output_dir,
        xlsx_name=ALL_DATA_EXTERNAL_BASELINE_XLSX_NAME,
        csv_name=ALL_DATA_EXTERNAL_BASELINE_CSV_NAME,
        logger=logger,
    )
    if logger:
        logger.info(
            f"Finished baseline external aggregation "
            f"({len(baseline)} rows remaining): {baseline_csv}"
        )
    # ---------------------------------------------------------------------------

    requested = list(dict.fromkeys(enabled_filters or []))
    requested = [name for name in requested if name in EXTERNAL_FILTERS]
    for filter_name in requested:
        filtered, removed = apply_single_external_filter(
            dataset.copy(),
            filter_name,
            logger=logger,
        )
        suffix = EXTERNAL_FILTERS[filter_name]
        variant_csv = save_external_aggregate_outputs(
            dataset=filtered,
            output_dir=output_dir,
            xlsx_name=f"all_data_external_filter_{suffix}.xlsx",
            csv_name=f"all_data_external_filter_{suffix}.csv",
            logger=logger,
        )
        if logger:
            logger.info(
                f"Finished external variant '{filter_name}' "
                f"(removed={removed}): {variant_csv}"
            )

    return main_csv
