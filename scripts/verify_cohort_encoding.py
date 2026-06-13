#!/usr/bin/env python3
"""Verify year / Strain text / numeric strain encoding for Issue #47 cohorts."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src" / "preprocessing"))

from utils.io_utils import (  # noqa: E402
    STRAIN_1_YEARS,
    strain_from_year,
)

INPUT_XLSX = REPO_ROOT / "outputs/external/input/segmentation_classification_all_data.xlsx"
INPUT_CSV = REPO_ROOT / "outputs/external/input/segmentation_classification_all_data.csv"
BASELINE_CSV = REPO_ROOT / "outputs/external/aggregated/tabular/all_data_external_baseline.csv"
REPORT_DIR = REPO_ROOT / "outputs/reports/cohort_verification"

CLASSIC_YEARS = {2015, 2018}
MIXED_YEARS = STRAIN_1_YEARS
EXPECTED_TEXT = {
    2: {"balb/c"},
    1: {"balb/c+black/c57", "balb/c+black/c57 ".strip()},  # normalized below
}


def _norm_strain_text(value) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().lower().split())


def _year_int(value) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _path_year(path) -> int | None:
    if pd.isna(path):
        return None
    parts = str(path).replace("\\", "/").split("/")
    for part in parts:
        if part.isdigit() and len(part) == 4:
            y = int(part)
            if 1900 <= y <= 2099:
                return y
    return None


def load_input(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".xlsx":
        return pd.read_excel(path)
    return pd.read_csv(path)


def verify_input(df: pd.DataFrame) -> dict:
    required = {"Year", "Strain", "Path"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    rows = []
    mismatches = []
    year_groups = df.groupby("Year", dropna=False)

    for year_raw, grp in year_groups:
        year = _year_int(year_raw)
        if year is None:
            continue
        expected_num = strain_from_year(year)
        strain_texts = grp["Strain"].map(_norm_strain_text)
        dominant_text = strain_texts.mode().iloc[0] if len(strain_texts) else ""
        n = len(grp)
        n_recordings = grp[["Mother", "Name", "Recording Number"]].drop_duplicates().shape[0]

        bad_text = 0
        bad_path_year = 0
        for idx, row in grp.iterrows():
            st = _norm_strain_text(row["Strain"])
            if expected_num == 2 and st != "balb/c":
                bad_text += 1
                mismatches.append(
                    {"year": year, "issue": "strain_text", "strain": row["Strain"], "index": int(idx)}
                )
            elif expected_num == 1 and st != "balb/c+black/c57":
                bad_text += 1
                mismatches.append(
                    {"year": year, "issue": "strain_text", "strain": row["Strain"], "index": int(idx)}
                )
            py = _path_year(row.get("Path"))
            if py is not None and py != year:
                bad_path_year += 1

        rows.append(
            {
                "year": year,
                "syllable_rows": n,
                "recording_keys": int(n_recordings),
                "dominant_strain_text": dominant_text,
                "expected_pup_strain": expected_num,
                "strain_text_mismatches": bad_text,
                "path_year_mismatches": bad_path_year,
                "cohort": (
                    "classic_balbc"
                    if year in CLASSIC_YEARS
                    else "mixed"
                    if year in MIXED_YEARS
                    else "other"
                ),
            }
        )

    return {"by_year": rows, "mismatches": mismatches[:50], "mismatch_total": len(mismatches)}


def verify_baseline_aggregate() -> dict:
    if not BASELINE_CSV.is_file():
        return {"error": f"Missing {BASELINE_CSV}"}
    cols = [
        "syll1_s_freq", "syll2_s_freq", "syll3_s_freq", "syll4_s_freq", "syll5_s_freq",
        "syll6_s_freq", "syll7_s_freq", "syll8_s_freq", "syll9_s_freq", "syll10_s_freq",
        "syll1_e_freq", "syll2_e_freq", "syll3_e_freq", "syll4_e_freq", "syll5_e_freq",
        "syll6_e_freq", "syll7_e_freq", "syll8_e_freq", "syll9_e_freq", "syll10_e_freq",
        "syll1_dist", "syll2_dist", "syll3_dist", "syll4_dist", "syll5_dist",
        "syll6_dist", "syll7_dist", "syll8_dist", "syll9_dist", "syll10_dist",
        "syll1_dur", "syll2_dur", "syll3_dur", "syll4_dur", "syll5_dur",
        "syll6_dur", "syll7_dur", "syll8_dur", "syll9_dur", "syll10_dur",
        "mother_gen", "pup_sex", "avg_ISI_time", "pup_age", "session", "pup_strain",
        "pup_gen", "mouse_idx",
    ]
    df = pd.read_csv(BASELINE_CSV, header=None, names=cols)
    counts = df["pup_strain"].value_counts().to_dict()
    return {
        "recording_rows": len(df),
        "pup_strain_counts": {str(int(k)): int(v) for k, v in counts.items()},
        "strain_1_mixed_cohort": int(counts.get(1.0, counts.get(1, 0))),
        "strain_2_classic_cohort": int(counts.get(2.0, counts.get(2, 0))),
    }


def write_reports(result: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "cohort_encoding_report.json"
    md_path = out_dir / "cohort_encoding_report.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    lines = [
        "# Cohort encoding verification",
        "",
        f"**Generated:** {result['generated_at']}",
        f"**Input:** `{result['input_path']}`",
        f"**Status:** {'PASS' if result['pass'] else 'FAIL'}",
        "",
        "## Summary",
        "",
        result["summary"],
        "",
        "## By year (syllable-level input)",
        "",
        "| Year | Syllable rows | Recordings | Dominant Strain text | Expected `pup_strain` | Text mismatches |",
        "|------|---------------|------------|----------------------|----------------------|-----------------|",
    ]
    for row in result["input"]["by_year"]:
        lines.append(
            f"| {row['year']} | {row['syllable_rows']:,} | {row['recording_keys']:,} | "
            f"{row['dominant_strain_text']} | {row['expected_pup_strain']} | "
            f"{row['strain_text_mismatches']} |"
        )

    lines.extend(
        [
            "",
            "## Baseline aggregate (`pup_strain`)",
            "",
            f"- Recording rows: **{result['baseline'].get('recording_rows', 'n/a'):,}**"
            if isinstance(result["baseline"].get("recording_rows"), int)
            else "",
        ]
    )
    b = result["baseline"]
    if "pup_strain_counts" in b:
        lines.append(f"- `pup_strain=1` (Mixed cohort): **{b.get('strain_1_mixed_cohort', 0):,}**")
        lines.append(f"- `pup_strain=2` (Classic BALB/C): **{b.get('strain_2_classic_cohort', 0):,}**")

    if result["input"]["mismatch_total"]:
        lines.extend(
            [
                "",
                f"## Mismatches (showing up to 50 of {result['input']['mismatch_total']})",
                "",
            ]
        )
        for m in result["input"]["mismatches"][:20]:
            lines.append(f"- year {m['year']}: {m['issue']} — Strain=`{m.get('strain', '')}`")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify cohort year/strain encoding.")
    parser.add_argument("--input", type=Path, default=None, help="Input xlsx/csv (default: canonical external input)")
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()

    input_path = args.input
    if input_path is None:
        input_path = INPUT_XLSX if INPUT_XLSX.is_file() else INPUT_CSV
    if not input_path.is_file():
        print(f"Input not found: {input_path}", file=sys.stderr)
        return 1

    df = load_input(input_path)
    input_result = verify_input(df)
    baseline_result = verify_baseline_aggregate()

    mismatch_total = input_result["mismatch_total"]
    classic_years = [r for r in input_result["by_year"] if r["cohort"] == "classic_balbc"]
    mixed_years = [r for r in input_result["by_year"] if r["cohort"] == "mixed"]
    classic_ok = all(r["strain_text_mismatches"] == 0 for r in classic_years)
    mixed_ok = all(r["strain_text_mismatches"] == 0 for r in mixed_years)
    passed = mismatch_total == 0 and classic_ok and mixed_ok

    summary = (
        f"Classic years {sorted(CLASSIC_YEARS)} → pup_strain=2: "
        f"{'OK' if classic_ok else 'ISSUES'}. "
        f"Mixed years {sorted(MIXED_YEARS)} → pup_strain=1: "
        f"{'OK' if mixed_ok else 'ISSUES'}. "
        f"Total strain text mismatches: {mismatch_total}."
    )

    result = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "input_path": str(input_path.relative_to(REPO_ROOT)),
        "pass": passed,
        "summary": summary,
        "input": input_result,
        "baseline": baseline_result,
    }
    write_reports(result, args.report_dir)
    print(summary)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
