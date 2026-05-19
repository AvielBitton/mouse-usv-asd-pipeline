"""Generate external aggregates from the corrected input workbook.

Runs ONLY the external aggregation step — no legacy pipeline, no TensorFlow.
Produces:
  outputs/external/aggregated/all_data_external_main.csv / .xlsx
  outputs/external/aggregated/all_data_external_baseline.csv / .xlsx
    (baseline retains Noise==1 syllables; see docs/BASELINE_DATA_FILTERS.md)

Usage:
    .venv/bin/python scripts/run_external_aggregation.py

Input:
    outputs/external/input/segmentation_classification_all_data.xlsx
    (Issue #34-corrected + Session=0→1 applied — see docs/BASELINE_DATA_FILTERS.md)
"""

import logging
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "src", "preprocessing"))

from utils import (
    OUTPUTS_EXTERNAL_AGGREGATED_DIR,
    OUTPUTS_EXTERNAL_INPUT_DIR,
    setup_logger,
)

# Import directly from the module to avoid triggering TensorFlow via steps/__init__
from steps.extract_features import run_external_aggregated_feature_extraction


def main():
    logger = setup_logger()

    external_file = os.path.join(
        OUTPUTS_EXTERNAL_INPUT_DIR,
        "segmentation_classification_all_data.xlsx",
    )

    if not os.path.isfile(external_file):
        logger.error(f"Input file not found: {external_file}")
        sys.exit(1)

    logger.info(f"Input:      {external_file}")
    logger.info(f"Output dir: {OUTPUTS_EXTERNAL_AGGREGATED_DIR}")

    main_csv = run_external_aggregated_feature_extraction(
        external_file=external_file,
        output_dir=OUTPUTS_EXTERNAL_AGGREGATED_DIR,
        enabled_filters=None,
        logger=logger,
    )

    logger.info(f"Done. Main CSV: {main_csv}")
    baseline_csv = os.path.join(
        OUTPUTS_EXTERNAL_AGGREGATED_DIR, "all_data_external_baseline.csv"
    )
    baseline_xlsx = os.path.join(
        OUTPUTS_EXTERNAL_AGGREGATED_DIR, "all_data_external_baseline.xlsx"
    )
    logger.info(f"Baseline CSV:  {baseline_csv}  exists={os.path.isfile(baseline_csv)}")
    logger.info(f"Baseline XLSX: {baseline_xlsx}  exists={os.path.isfile(baseline_xlsx)}")


if __name__ == "__main__":
    main()
