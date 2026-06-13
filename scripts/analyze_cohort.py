"""Ad-hoc cohort analysis for the research-data documentation.

Reads outputs/external/input/segmentation_classification_all_data.csv and prints
the descriptive statistics needed to document the study population (animals,
recordings, syllables) broken down by year / strain / genotype / sex / age.
"""

import os
from collections import Counter, defaultdict

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSV = os.path.join(ROOT, "outputs", "external", "input",
                   "segmentation_classification_all_data.csv")


def hr(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def main():
    df = pd.read_csv(CSV, low_memory=False)
    hr("SHAPE / COLUMNS")
    print("rows (syllables):", len(df))
    print("columns:", len(df.columns))
    print(list(df.columns))

    # A "mouse" = unique pup. Use (Year, Mother, Name) to avoid id collisions across years.
    df["pup_key"] = (df["Year"].astype(str) + "|" + df["Mother"].astype(str)
                     + "|" + df["Name"].astype(str))
    df["mother_key"] = df["Year"].astype(str) + "|" + df["Mother"].astype(str)

    hr("TOTALS")
    print("unique pups (mice):", df["pup_key"].nunique())
    print("unique mothers (dams):", df["mother_key"].nunique())
    print("unique recordings (Path):", df["Path"].nunique())
    print("years:", sorted(df["Year"].dropna().unique().tolist()))

    hr("PUPS PER YEAR")
    pups_year = df.groupby("Year")["pup_key"].nunique()
    print(pups_year.to_string())

    hr("DAMS PER YEAR")
    print(df.groupby("Year")["mother_key"].nunique().to_string())

    hr("RECORDINGS PER YEAR")
    print(df.groupby("Year")["Path"].nunique().to_string())

    hr("SYLLABLES PER YEAR")
    print(df.groupby("Year").size().to_string())

    hr("STRAIN (raw text) PER YEAR")
    print(df.groupby("Year")["Strain"].agg(lambda s: Counter(s).most_common()).to_string())

    hr("PUPS BY SEX")
    pup_level = df.drop_duplicates("pup_key")
    print(pup_level["Sex"].value_counts(dropna=False).to_string())

    hr("PUPS BY SEX x YEAR")
    print(pd.crosstab(pup_level["Year"], pup_level["Sex"]).to_string())

    hr("PUPS BY OFFSPRING GENOTYPE")
    print(pup_level["Offspring Genotype"].value_counts(dropna=False).to_string())

    hr("PUPS BY MOTHER GENOTYPE")
    print(pup_level["Mother Genotype"].value_counts(dropna=False).to_string())

    hr("PUPS BY GENOTYPE GROUP (Mother-Offspring)")
    print(pup_level["Genotype Group"].value_counts(dropna=False).to_string())

    hr("PUPS BY GENOTYPE GROUP x YEAR")
    print(pd.crosstab(pup_level["Year"], pup_level["Genotype Group"]).to_string())

    hr("PUPS BY DAY (pup age)")
    print(pup_level["Day"].value_counts(dropna=False).sort_index().to_string())

    hr("DAY x YEAR (pup-level)")
    print(pd.crosstab(pup_level["Year"], pup_level["Day"]).to_string())

    hr("SESSIONS present")
    print(df["Session"].value_counts(dropna=False).to_string())
    print("\nSessions per year (recording-level):")
    rec_level = df.drop_duplicates("Path")
    print(pd.crosstab(rec_level["Year"], rec_level["Session"]).to_string())

    hr("SUPPLEMENT (Offspring) pups")
    print(pup_level["Supplement (Offspring)"].value_counts(dropna=False).to_string())
    print("\nSupplement (Mother) pups")
    print(pup_level["Supplement (Mother)"].value_counts(dropna=False).to_string())

    hr("SYLLABLE TYPE distribution")
    print(df["Syllable type"].value_counts(dropna=False).to_string())

    hr("COMPLEXITY LEVEL distribution")
    print(df["Complexity level"].value_counts(dropna=False).to_string())

    hr("NOISE flag")
    print(df["Noise"].value_counts(dropna=False).to_string())

    hr("ACOUSTIC FEATURE SUMMARY (all syllables)")
    for col in ["Duration (time)", "ISI_time", "Start Point (Hz)", "End Point (Hz)"]:
        s = pd.to_numeric(df[col], errors="coerce")
        print(f"{col}: n={s.notna().sum()} mean={s.mean():.4f} "
              f"median={s.median():.4f} sd={s.std():.4f} "
              f"min={s.min():.4f} max={s.max():.4f}")

    hr("SYLLABLES PER RECORDING")
    spr = df.groupby("Path").size()
    print(f"mean={spr.mean():.2f} median={spr.median():.0f} "
          f"min={spr.min()} max={spr.max()} total recs={len(spr)}")

    hr("SYLLABLES PER PUP")
    spp = df.groupby("pup_key").size()
    print(f"mean={spp.mean():.2f} median={spp.median():.0f} "
          f"min={spp.min()} max={spp.max()}")

    # Model assignment per year (genetic Mthfr vs environmental CPF) is inferred
    # from strain; print cross of strain x genotype group to confirm.
    hr("STRAIN x GENOTYPE GROUP (pup-level) — model inference")
    print(pd.crosstab(pup_level["Strain"], pup_level["Genotype Group"]).to_string())

    # 0 Hz fallbacks
    hr("0 Hz fallback rows")
    z = ((pd.to_numeric(df["Start Point (Hz)"], errors="coerce") == 0) |
         (pd.to_numeric(df["End Point (Hz)"], errors="coerce") == 0)).sum()
    print("rows with a 0 Hz endpoint:", int(z))


if __name__ == "__main__":
    main()
