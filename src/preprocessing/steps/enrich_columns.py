from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

SYLLABLE_TYPE_MAP = {
    0: "Complex",
    1: "Frequency steps",
    2: "Composite",
    3: "Two syllables",
    4: "Upward",
    5: "Flat",
    6: "Harmonic",
    7: "Downward",
    8: "Chevron",
    9: "Short",
    10: "Undefined",
}

_UNDEFINED = {10}
_SINGLE_VOWEL = {0, 4, 5, 7, 8, 9}
_MULTIPLE_VOWELS = {1, 3}
_ADVANCED_HARMONIC = {2, 6}


def _complexity_numeric(syl_num) -> Optional[int]:
    """Map a syllable number to its complexity level (0/1/2/3)."""
    if pd.isna(syl_num):
        return None
    syl_num = int(syl_num)
    if syl_num in _UNDEFINED:
        return 0
    if syl_num in _SINGLE_VOWEL:
        return 1
    if syl_num in _MULTIPLE_VOWELS:
        return 2
    if syl_num in _ADVANCED_HARMONIC:
        return 3
    return None


_COMPLEXITY_TEXT = {
    0: "Undefined",
    1: "Single Vowel",
    2: "Multiple Vowels",
    3: "Advanced Harmonic",
}

# Columns written by the CNN classification step. They are dropped (and omitted
# from the final column order) when ``include_syllable_classification_columns``
# is False, so a segmentation-only run still produces a clean workbook.
SYLLABLE_CLASSIFICATION_OUTPUT_COLUMNS = (
    "Syllable number",
    "Syllable type",
    "Complexity level",
    "Complexity level (numeric)",
)

FINAL_COLUMN_ORDER = [
    "Index",
    "Path",
    "Year",
    "Mother",
    "Mother Genotype",
    "Mother Genotype (binary)",
    "Supplement (Mother)",
    "Name",
    "Sex",
    "Offspring Genotype",
    "Offspring Genotype (binary)",
    "Supplement (Offspring)",
    "Day",
    "Session",
    "Strain",
    "Recording Number",
    "Syllable order (in recording)",
    "Syllables per recording",
    "Start point(s)",
    "End point(s)",
    "Duration (time)",
    "ISI_time",
    "Start Point (Hz)",
    "End Point (Hz)",
    "Noise",
    "Syllable number",
    "Syllable type",
    "Complexity level",
    "Complexity level (numeric)",
]


def _strain_label_from_year(y) -> str:
    """Map a recording year to its descriptive strain label.

    Mirrors the labels used in the external segmentation workbook produced by
    ``segmentation-app``: 2015 / 2018 cohorts → ``"BALB/C"``; everything else
    (2022+, including 2023 / 2024) → ``"BALB/C+BLACK/C57"``.

    Note: this is a *display* label written into the per-file segmentation
    workbook for human inspection. The tabular feature extraction step
    (``extract_features.add_strain_column`` / ``add_strain_from_path``)
    overwrites this column with a numeric strain identifier (1 / 2) before
    training, so the trained models always see the numeric value defined by
    ``utils.io_utils.STRAIN_1_YEARS``.
    """
    s = str(y).strip()
    try:
        yi = int(float(s))
    except ValueError:
        yi = 0
    return "BALB/C" if yi in (2015, 2018) else "BALB/C+BLACK/C57"


def _supplement_flag(value) -> Optional[int]:
    """Parse a supplement cell into 0/1; ``None`` when unknown / empty."""
    if pd.isna(value):
        return None
    s = str(value).strip().lower()
    if not s or s in {"nan", "none", "-", "—"}:
        return None
    if s in {"0", "false", "no", "ללא תיסוף"}:
        return 0
    if s in {"1", "true", "yes", "עם תיסוף"}:
        return 1
    return None


def enrich_segmentation_columns(
    file_path: str,
    year: str,
    logger: Optional[logging.Logger] = None,
    *,
    include_syllable_classification_columns: bool = True,
) -> str:
    """Add enrichment columns to the segmentation Excel file.

    Reads the Excel produced by the earlier pipeline steps (segmentation,
    basic features, classification), computes the columns specified in
    Issue #5, reorders to ``FINAL_COLUMN_ORDER``, and writes back.

    Args:
        file_path: Path to the segmentation Excel file (will be updated).
        year: Recording year (fallback when Path is unavailable).
        logger: Optional logger instance.
        include_syllable_classification_columns: If False, drop CNN-derived
            syllable columns (``Syllable number``, ``Syllable type``,
            ``Complexity level``, ``Complexity level (numeric)``) and omit
            them from the final column order — useful for segmentation-only
            runs that have no classifier output.

    Returns:
        Path to the updated Excel file.

    Notes:
        ``Strain`` is added here as a descriptive **text** label
        (``BALB/C`` for 2015 / 2018, ``BALB/C+BLACK/C57`` otherwise) to
        keep the per-file segmentation workbook visually identical to the
        external ``segmentation_classification_all_data.xlsx`` produced by
        ``segmentation-app``. The tabular feature extraction step
        (``run_feature_extraction`` / ``run_aggregated_feature_extraction``)
        overwrites this column with a numeric strain identifier (1 / 2)
        from ``strain_from_year`` before training, so the XGBoost /
        TabPFN models always see the numeric value defined by
        ``utils.io_utils.STRAIN_1_YEARS``.
    """
    if logger:
        logger.info("Enriching segmentation columns")

    df = pd.read_excel(file_path, engine="openpyxl")

    if not include_syllable_classification_columns:
        for c in SYLLABLE_CLASSIFICATION_OUTPUT_COLUMNS:
            if c in df.columns:
                df.drop(columns=[c], inplace=True)

    # 1. Row index (1-based serial ID)
    df["Index"] = range(1, len(df) + 1)

    # 2. Year — derive from Path when possible
    if "Path" in df.columns:
        df["Year"] = df["Path"].apply(
            lambda p: str(p).split("/")[1] if "/" in str(p) else year
        )
    else:
        df["Year"] = year

    # 3. Mother Genotype (binary): WT → 1, anything else → 0
    df["Mother Genotype (binary)"] = (
        df["Mother Genotype"]
        .apply(lambda x: 1 if str(x).strip().upper() == "WT" else 0)
    )

    # 4. Offspring Genotype (binary): WT → 1, anything else → 0
    df["Offspring Genotype (binary)"] = (
        df["Offspring Genotype"]
        .apply(lambda x: 1 if str(x).strip().upper() == "WT" else 0)
    )

    # 5a. Syllable order within recording (by ascending Start point).
    #     Group by Path (unique per recording) so repeated Recording Numbers
    #     across different mice are kept separate.
    #     Missing Start point(s) → NaN rank; nullable ``Int64`` avoids
    #     "Cannot convert non-finite values (NA or inf) to integer".
    _rank = df.groupby("Path")["Start point(s)"].rank(method="first")
    df["Syllable order (in recording)"] = _rank.astype("Int64")

    # 5b. Number of syllables in each recording
    df["Syllables per recording"] = (
        df.groupby("Path")["Path"].transform("count")
    )

    # 6. Noise indicator: 1 when Start Point (Hz) == End Point (Hz)
    if "Start Point (Hz)" in df.columns and "End Point (Hz)" in df.columns:
        _noise = df["Start Point (Hz)"] == df["End Point (Hz)"]
        df["Noise"] = _noise.fillna(False).astype("int64")
    else:
        df["Noise"] = 0

    # 7a. Supplement (Mother): 1 if Mother name OR Path contains "sup"
    path_has_sup = (
        df["Path"].astype(str).str.contains("sup", case=False, na=False)
        if "Path" in df.columns
        else pd.Series(False, index=df.index)
    )
    df["Supplement (Mother)"] = (
        df["Mother"].astype(str)
        .str.contains("sup", case=False, na=False)
        .astype(int) | path_has_sup.astype(int)
    )

    # 7b. Supplement (Offspring): metadata value first, fallback to Name/Path heuristics.
    if "Supplement (Offspring)" in df.columns:
        parsed = df["Supplement (Offspring)"].apply(_supplement_flag)
        fallback = (
            df["Name"].astype(str).str.contains("sup", case=False, na=False).astype(int)
            | path_has_sup.astype(int)
        )
        df["Supplement (Offspring)"] = parsed.fillna(fallback).astype(int)
    else:
        df["Supplement (Offspring)"] = (
            df["Name"].astype(str)
            .str.contains("sup", case=False, na=False)
            .astype(int) | path_has_sup.astype(int)
        )

    # 8. Strain (text label by year). Overwritten to numeric (1 / 2) by the
    #    tabular feature-extraction step before any model training, so this
    #    label only affects how the per-file segmentation workbook reads.
    df["Strain"] = df["Year"].apply(_strain_label_from_year)

    # 9–10. Syllable type / complexity (require CNN ``Syllable number`` column).
    if include_syllable_classification_columns:
        if "Syllable number" in df.columns:
            df["Syllable type"] = df["Syllable number"].map(SYLLABLE_TYPE_MAP)
        else:
            df["Syllable type"] = None

        if "Syllable number" in df.columns:
            df["Complexity level (numeric)"] = df["Syllable number"].apply(
                _complexity_numeric
            )
            df["Complexity level"] = df["Complexity level (numeric)"].map(
                _COMPLEXITY_TEXT
            )
        else:
            df["Complexity level"] = None
            df["Complexity level (numeric)"] = None

    # Reorder: known columns first (in spec order), then any extras
    col_order = (
        FINAL_COLUMN_ORDER
        if include_syllable_classification_columns
        else [c for c in FINAL_COLUMN_ORDER if c not in SYLLABLE_CLASSIFICATION_OUTPUT_COLUMNS]
    )
    ordered = [c for c in col_order if c in df.columns]
    extras = [c for c in df.columns if c not in FINAL_COLUMN_ORDER]
    df = df[ordered + extras]

    df.to_excel(file_path, index=False, engine="openpyxl")

    if logger:
        logger.info(
            f"Enrichment complete: {len(df)} rows, {len(df.columns)} columns "
            f"in {file_path}"
        )

    return file_path
