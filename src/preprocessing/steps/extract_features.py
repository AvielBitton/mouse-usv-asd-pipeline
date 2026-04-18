from __future__ import annotations

import glob
import logging
import os
from typing import List, Optional

import numpy as np
import pandas as pd

from legacy.audio_feature_extraction_reduction_by_recording import feature_extraction
from utils import FEATURE_COLUMNS, strain_from_year, replace_extension

# Combined pipeline outputs (per-run); avoids mixing with per-file segmentation_*.xlsx in outputs root.
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
    4. Save the combined dataset as ``aggregated/all_data.xlsx``
    5. Select the feature columns and compute per-recording features
    6. Save the aggregated feature matrix as ``aggregated/all_data.csv``

    Existing ``all_data.*`` files in that subdirectory are overwritten.

    Args:
        outputs_dir: Directory containing the per-file ``segmentation_*.xlsx`` workbooks
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


AGGREGATED_EXTERNAL_SUBDIR = "aggregated_external"
ALL_DATA_EXTERNAL_XLSX_NAME = "all_data_external.xlsx"
ALL_DATA_EXTERNAL_CSV_NAME = "all_data_external.csv"


def run_external_aggregated_feature_extraction(
    external_file: str,
    output_dir: str = "",
    logger: Optional[logging.Logger] = None,
) -> str:
    """Run feature extraction on a single external Excel file containing all segmentation data.

    Same pipeline as ``run_aggregated_feature_extraction`` but reads one
    pre-concatenated workbook instead of globbing individual per-file
    segmentation workbooks.

    Args:
        external_file: Path to the external Excel file
            (e.g. ``outputs/external/segmentation_classification_all_data.xlsx``).
        output_dir: Directory to write ``all_data.xlsx`` and ``all_data.csv``.
            Defaults to ``outputs/aggregated_external``.
        logger: Optional logger instance.

    Returns:
        Path to the aggregated CSV file.
    """
    if not output_dir:
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(external_file)),
            AGGREGATED_EXTERNAL_SUBDIR,
        )

    if logger:
        logger.info(
            f"Aggregating features from external file: {external_file} -> {output_dir}"
        )

    os.makedirs(output_dir, exist_ok=True)

    dataset = pd.read_excel(external_file)
    if logger:
        logger.info(f"Loaded {len(dataset)} rows from {external_file}")

    invalid_labels = {"UNK", "NAN"}
    valid_sex = {"M", "F"}
    mask = (
        dataset["Offspring Genotype"].isin(invalid_labels)
        | dataset["Mother Genotype"].isin(invalid_labels)
        | ~dataset["Sex"].isin(valid_sex)
    )
    if mask.any():
        dataset = dataset[~mask].reset_index(drop=True)
        if logger:
            logger.info(
                f"Filtered {mask.sum()} rows with invalid genotype labels "
                f"(UNK/NAN) or unknown sex, {len(dataset)} rows remaining"
            )

    # Session 0 means no session subfolder existed (single session) -- treat as 1
    zero_sessions = dataset["Session"] == 0
    if zero_sessions.any():
        dataset.loc[zero_sessions, "Session"] = 1
        if logger:
            logger.info(
                f"Replaced {zero_sessions.sum()} Session=0 values with 1"
            )

    dataset = add_strain_from_path(dataset)

    os.makedirs(output_dir, exist_ok=True)
    output_xlsx = os.path.join(output_dir, ALL_DATA_EXTERNAL_XLSX_NAME)
    if logger and os.path.isfile(output_xlsx):
        logger.info(f"Overwriting existing file: {output_xlsx}")
    dataset.to_excel(output_xlsx, index=False)

    X = select_feature_columns(dataset)
    mouse_final_data = compute_features(X)

    output_csv = os.path.join(output_dir, ALL_DATA_EXTERNAL_CSV_NAME)
    if logger and os.path.isfile(output_csv):
        logger.info(f"Overwriting existing file: {output_csv}")
    np.savetxt(output_csv, X=mouse_final_data, delimiter=",")

    if logger:
        logger.info(f"Finished external aggregation: {output_csv}")

    return output_csv
