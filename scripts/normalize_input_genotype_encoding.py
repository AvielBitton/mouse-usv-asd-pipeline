"""Verify and normalize binary genotype columns in external input files.

Canonical encoding: WT=0, HT/HET=1 in ``Mother Genotype (binary)`` and
``Offspring Genotype (binary)``. Syncs xlsx and csv under outputs/external/input/.

Usage:
    .venv/bin/python scripts/normalize_input_genotype_encoding.py
"""

from __future__ import annotations

import os
import shutil
from datetime import date
from typing import Tuple

import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(REPO_ROOT, "outputs", "external", "input")
XLSX_NAME = "segmentation_classification_all_data.xlsx"
CSV_NAME = "segmentation_classification_all_data.csv"


def _normalize_genotype_text(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.upper().replace("HT", "HET")


def _binary_from_text(series: pd.Series) -> pd.Series:
    normalized = _normalize_genotype_text(series)
    return normalized.apply(lambda g: 1 if g == "HET" else 0)


def normalize_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Recompute binary genotype columns; return (df, mismatch_count)."""
    required = ("Mother Genotype", "Offspring Genotype")
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    mother_bin = _binary_from_text(df["Mother Genotype"])
    offspring_bin = _binary_from_text(df["Offspring Genotype"])

    mismatches = 0
    if "Mother Genotype (binary)" in df.columns:
        old = pd.to_numeric(df["Mother Genotype (binary)"], errors="coerce")
        mismatches += int((old != mother_bin).sum())
    if "Offspring Genotype (binary)" in df.columns:
        old = pd.to_numeric(df["Offspring Genotype (binary)"], errors="coerce")
        mismatches += int((old != offspring_bin).sum())

    df = df.copy()
    df["Mother Genotype (binary)"] = mother_bin
    df["Offspring Genotype (binary)"] = offspring_bin
    return df, mismatches


def main() -> None:
    xlsx_path = os.path.join(INPUT_DIR, XLSX_NAME)
    csv_path = os.path.join(INPUT_DIR, CSV_NAME)

    if not os.path.isfile(xlsx_path):
        raise SystemExit(f"Input not found: {xlsx_path}")

    backup_dir = os.path.join(INPUT_DIR, "backup")
    os.makedirs(backup_dir, exist_ok=True)
    stamp = date.today().isoformat()
    for name in (XLSX_NAME, CSV_NAME):
        src = os.path.join(INPUT_DIR, name)
        if os.path.isfile(src):
            dst = os.path.join(backup_dir, f"{stamp}_pre_genotype_encoding_{name}")
            if not os.path.isfile(dst):
                shutil.copy2(src, dst)
                print(f"Backed up: {dst}")

    print(f"Loading {xlsx_path}")
    df = pd.read_excel(xlsx_path)
    df, mismatches = normalize_dataframe(df)
    print(f"Rows: {len(df)}; binary column mismatches fixed: {mismatches}")

    df.to_excel(xlsx_path, index=False)
    df.to_csv(csv_path, index=False)
    print(f"Wrote {xlsx_path}")
    print(f"Wrote {csv_path}")
    print("Encoding: WT=0, HT/HET=1 in Mother/Offspring Genotype (binary)")


if __name__ == "__main__":
    main()
