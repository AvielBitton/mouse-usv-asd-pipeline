"""
Split mapping files into batch segmentation files for the preprocessing pipeline.

The pipeline expects metadata files named:
    Data {year} For Syl Segmentation_{n}.xlsx

This script reads the full mapping files from ``metadata/mapping/`` and splits
them into smaller batches under ``metadata/``.

Each batch file:
  - Contains only rows with a valid Session value
  - Drops the Channel column (not used by the pipeline)
  - Has at most ``--batch-size`` rows (default 1200)

Usage:
    python split_mapping_to_segmentation.py
    python split_mapping_to_segmentation.py --batch-size 1500
    python split_mapping_to_segmentation.py --years 2023 2024
    python split_mapping_to_segmentation.py --dry-run
"""

import argparse
import re
from pathlib import Path

import pandas as pd


MAPPING_DIR = Path("metadata/mapping")
OUTPUT_DIR = Path("metadata")

REQUIRED_COLUMNS = [
    "Mother",
    "Mother Genotype",
    "Name",
    "Sex",
    "Offspring Genotype",
    "Day",
    "Session",
    "Recording Number",
]


def split_mapping_file(mapping_path: Path, batch_size: int, dry_run: bool = False) -> int:
    """Split a single mapping file into segmentation batch files.

    Returns the number of batch files created.
    """
    year_match = re.search(r'\((\d{4})\)', mapping_path.stem)
    if not year_match:
        print(f"  Skipping {mapping_path.name}: cannot extract year")
        return 0
    year = year_match.group(1)

    # Check if segmentation files already exist for this year
    existing = list(OUTPUT_DIR.glob(f"Data {year} For Syl Segmentation_*.xlsx"))
    if existing:
        print(f"  Skipping year {year}: {len(existing)} segmentation file(s) already exist")
        return 0

    df = pd.read_excel(mapping_path, engine="openpyxl")

    # Keep only rows with a valid Session
    df = df.dropna(subset=["Session"])
    df["Session"] = df["Session"].astype(int)

    # Drop Channel column if present
    if "Channel" in df.columns:
        df = df.drop(columns=["Channel"])

    # Keep only the required columns (in order)
    cols = [c for c in REQUIRED_COLUMNS if c in df.columns]
    df = df[cols]

    df = df.dropna(how="all")
    if df.empty:
        print(f"  Year {year}: no valid rows after filtering")
        return 0

    # Sort for consistency
    df = df.sort_values(
        by=["Mother", "Name", "Day", "Session", "Recording Number"]
    ).reset_index(drop=True)

    # Split into batches
    n_batches = max(1, -(-len(df) // batch_size))  # ceiling division
    batches = [df.iloc[i * batch_size : (i + 1) * batch_size] for i in range(n_batches)]

    print(f"  Year {year}: {len(df)} rows -> {n_batches} file(s) of ~{batch_size} rows")

    for i, batch_df in enumerate(batches, start=1):
        filename = f"Data {year} For Syl Segmentation_{i}.xlsx"
        output_path = OUTPUT_DIR / filename
        if dry_run:
            print(f"    [DRY] Would create: {filename} ({len(batch_df)} rows)")
        else:
            batch_df.to_excel(output_path, index=False, engine="openpyxl")
            print(f"    Created: {filename} ({len(batch_df)} rows)")

    return n_batches


def main():
    parser = argparse.ArgumentParser(
        description="Split mapping files into segmentation batch files."
    )
    parser.add_argument(
        "--batch-size", type=int, default=1200,
        help="Maximum rows per segmentation file (default: 1200)",
    )
    parser.add_argument(
        "--years", type=str, nargs="*",
        help="Only process these years (default: all)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be done without creating files",
    )
    args = parser.parse_args()

    if not MAPPING_DIR.exists():
        print(f"Error: {MAPPING_DIR} does not exist")
        return

    mapping_files = sorted(MAPPING_DIR.glob("Metadata Recording Mapping (*).xlsx"))
    if not mapping_files:
        print("No mapping files found. Run generate_metadata.py first.")
        return

    print(f"Found {len(mapping_files)} mapping file(s)")

    for mf in mapping_files:
        if args.years:
            year_match = re.search(r'\((\d{4})\)', mf.stem)
            if year_match and year_match.group(1) not in args.years:
                continue
        split_mapping_file(mf, args.batch_size, args.dry_run)

    print("\nDone.")


if __name__ == "__main__":
    main()
