#!/usr/bin/env python3
"""
compute_dataset.py — verified dataset composition straight from the data files.
Emits thesis/data_composition.json for figures + prose (single source of truth).
"""
import json
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CSV = REPO / "outputs/external/input/segmentation_classification_all_data.csv"
TAB_BASE = REPO / "outputs/external/aggregated/tabular/all_data_external_baseline.csv"
SEQ_BASE = REPO / "outputs/external/aggregated/sequence/all_data_external_baseline.xlsx"
MANIFEST = REPO / "docs/BASELINE_DATA_MANIFEST.json"
OUT = REPO / "thesis" / "data_composition.json"

GENO = "Offspring Genotype"
NAME = "Name"


def vc(series):
    return {str(k): int(v) for k, v in series.value_counts(dropna=False).items()}


def by(df, col):
    """rows + unique mice per category of col."""
    rows = vc(df[col])
    mice = {str(k): int(df[df[col] == k][NAME].nunique()) for k in df[col].dropna().unique()}
    return {"rows": rows, "mice": mice}


def main():
    df = pd.read_csv(CSV, low_memory=False)
    out = {"source_csv": str(CSV.relative_to(REPO))}

    out["raw"] = {
        "syllables": int(len(df)),
        "mice": int(df[NAME].nunique()),
        "dams": int(df["Mother"].nunique()),
        "genotype_syllables": vc(df[GENO]),
        "genotype_mice": {str(k): int(df[df[GENO] == k][NAME].nunique())
                          for k in df[GENO].dropna().unique()},
    }
    for col, key in [("Year", "year"), ("Strain", "strain"), ("Sex", "sex"),
                     ("Day", "day"), ("Session", "session"), ("Syllable type", "syllable_type")]:
        if col in df.columns:
            out[key] = by(df, col)

    # acoustic feature stats by genotype
    feats = {}
    for col in ["Duration (time)", "ISI_time", "Start Point (Hz)", "End Point (Hz)"]:
        if col in df.columns:
            s = df[col]
            feats[col] = {"n": int(s.notna().sum()), "min": float(s.min()),
                          "mean": float(s.mean()), "median": float(s.median()),
                          "max": float(s.max())}
    out["acoustic_overall"] = feats

    if "Noise" in df.columns:
        out["noise"] = vc(df["Noise"])

    # syllables-per-mouse distribution
    spm = df.groupby(NAME).size()
    out["syllables_per_mouse"] = {"min": int(spm.min()), "median": float(spm.median()),
                                  "mean": float(spm.mean()), "max": int(spm.max())}

    # aggregated tabular baseline (recording-level) — labeled file has WT/HT strings
    tb_lab = TAB_BASE.parent / "all_data_external_baseline_labeled.csv"
    if tb_lab.exists():
        tb = pd.read_csv(tb_lab, low_memory=False)
        unlabeled_rows = int(len(pd.read_csv(TAB_BASE, low_memory=False))) if TAB_BASE.exists() else None
        strain_geno = {f"strain{int(k[0])}_{k[1]}": int(v)
                       for k, v in tb.groupby("pup_strain")["pup_gen"].value_counts().items()}
        out["tabular_baseline"] = {
            "path": str(tb_lab.relative_to(REPO)), "rows": int(len(tb)),
            "rows_unlabeled_csv": unlabeled_rows, "cols": int(tb.shape[1]),
            "label_counts": vc(tb["pup_gen"]),
            "by_strain_genotype": strain_geno,
            "unique_mouse_idx": int(tb["mouse_idx"].nunique()) if "mouse_idx" in tb.columns else None,
        }

    # sequence baseline (session-level) — file is syllable-level; sessions via key
    if SEQ_BASE.exists():
        sq = pd.read_excel(SEQ_BASE)
        out["sequence_baseline_cols"] = list(map(str, sq.columns))
        out["sequence_baseline_rows"] = int(len(sq))
        if NAME in sq.columns:
            out["sequence_baseline_mice"] = int(sq[NAME].nunique())

    # manifest declared values for cross-check
    if MANIFEST.exists():
        out["manifest"] = json.loads(MANIFEST.read_text())

    OUT.write_text(json.dumps(out, indent=2, default=str))
    print("Wrote", OUT.relative_to(REPO))
    print("raw syllables:", out["raw"]["syllables"], "| mice:", out["raw"]["mice"], "| dams:", out["raw"]["dams"])
    print("genotype mice:", out["raw"]["genotype_mice"])
    print("tabular baseline rows:", out.get("tabular_baseline", {}).get("rows"),
          "label:", out.get("tabular_baseline", {}).get("label_counts"))


if __name__ == "__main__":
    main()
