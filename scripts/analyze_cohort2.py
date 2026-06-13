"""Second pass: longitudinal design (days/sessions per pup) and sex x genotype."""

import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSV = os.path.join(ROOT, "outputs", "external", "input",
                   "segmentation_classification_all_data.csv")


def hr(t):
    print("\n" + "=" * 78 + "\n" + t + "\n" + "=" * 78)


df = pd.read_csv(CSV, low_memory=False)
df["pup_key"] = (df["Year"].astype(str) + "|" + df["Mother"].astype(str)
                 + "|" + df["Name"].astype(str))

hr("DISTINCT DAYS recorded per pup (longitudinal depth)")
days_per_pup = df.groupby("pup_key")["Day"].nunique()
print(days_per_pup.value_counts().sort_index().to_string())
print("mean distinct days/pup:", round(days_per_pup.mean(), 2))

hr("(pup x day) combinations per year")
pd_combo = df.drop_duplicates(["pup_key", "Day"])
print(pd_combo.groupby("Year").size().to_string())

hr("Which DAYS appear in each year (any pup)")
print(df.groupby("Year")["Day"].agg(lambda s: sorted(s.unique().tolist())).to_string())

hr("(pup x day) by Day across all years")
print(pd_combo.groupby("Day").size().to_string())

hr("SEX x OFFSPRING GENOTYPE (pup-level)")
pup_level = df.drop_duplicates("pup_key")
print(pd.crosstab(pup_level["Sex"], pup_level["Offspring Genotype"], margins=True).to_string())

hr("SEX x GENOTYPE GROUP (pup-level)")
print(pd.crosstab(pup_level["Genotype Group"], pup_level["Sex"], margins=True).to_string())

hr("GENOTYPE GROUP x YEAR excluding supplement pups")
ns = pup_level[pup_level["Supplement (Offspring)"] == 0]
print(pd.crosstab(ns["Year"], ns["Genotype Group"], margins=True).to_string())

hr("Sessions recorded per pup")
sess_per_pup = df.groupby("pup_key")["Session"].nunique()
print(sess_per_pup.value_counts().sort_index().to_string())

hr("Recordings per pup (summary)")
rpp = df.groupby("pup_key")["Path"].nunique()
print(f"mean={rpp.mean():.1f} median={rpp.median():.0f} min={rpp.min()} max={rpp.max()}")

hr("UNK genotype / U sex pups detail")
unk = pup_level[(pup_level["Offspring Genotype"] == "UNK") | (pup_level["Sex"] == "U")]
print(unk[["Year", "Mother", "Name", "Sex", "Offspring Genotype",
           "Genotype Group", "Supplement (Offspring)"]].to_string(index=False))
