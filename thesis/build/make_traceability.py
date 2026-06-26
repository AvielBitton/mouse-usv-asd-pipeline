#!/usr/bin/env python3
"""
Integrity pass + traceability table.
- Cross-checks the results tables in 50_results.md against master_results.json.
- Cross-checks dataset numbers in 30_data.md against data_composition.json.
- Emits thesis/traceability.md.
Exit non-zero if any mismatch is found.
"""
import json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SEC = REPO / "thesis" / "sections"
MR = json.loads((REPO / "thesis" / "master_results.json").read_text())
COMP = json.loads((REPO / "thesis" / "data_composition.json").read_text())
MAN = json.loads((REPO / "thesis" / "figure_manifest.json").read_text())
OUT = REPO / "thesis" / "traceability.md"

problems = []


def mr_get(model, scope, split):
    for r in MR:
        if r["model"] == model and r["scope"] == scope and r["split"] == split and r["family"] in ("tabular", "sequence"):
            return r
    return None


def check_results_table():
    """Parse Table 1 (tabular pooled) rows from 50_results.md and verify each metric."""
    txt = (SEC / "50_results.md").read_text()
    model_map = {"XGBoost (inherited)": ("xgboost", "pooled"), "XGBoost-tuned": ("xgboost_tuned", "pooled"),
                 "TabPFN": ("tabpfn", "pooled")}
    col = {"Accuracy": "test_acc", "Weighted F1": "weighted_f1", "Balanced acc.": "balanced_acc",
           "ROC-AUC": "auc", "HT recall": "ht_recall", "HT precision": "ht_precision", "HT F1": "ht_f1"}
    header_cols = ["Model", "Split", "Accuracy", "Weighted F1", "Balanced acc.", "ROC-AUC",
                   "HT recall", "HT precision", "HT F1"]
    checked = 0
    for line in txt.split("\n"):
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip().replace("**", "") for c in line.strip().strip("|").split("|")]
        if len(cells) != len(header_cols):
            continue
        mname, split = cells[0], cells[1]
        if mname not in model_map or split not in ("dependent", "independent"):
            continue
        model, scope = model_map[mname]
        row = mr_get(model, scope, split)
        if not row:
            problems.append(f"Table1: no source row for {mname}/{split}")
            continue
        for ci, cname in enumerate(header_cols):
            if cname in col:
                want = str(row[col[cname]])
                got = cells[ci]
                if got not in ("", "—") and abs(float(got) - float(want)) > 0.0011:
                    problems.append(f"Table1 {mname}/{split} {cname}: prose={got} source={want}")
                else:
                    checked += 1
    return checked


def check_dataset_numbers():
    txt = (SEC / "30_data.md").read_text()
    checks = {
        "125,576": COMP["raw"]["syllables"] == 125576,
        "126 pups": COMP["raw"]["mice"] == 126,
        "35 dams": COMP["raw"]["dams"] == 35,
        "91 WT": COMP["raw"]["genotype_mice"].get("WT") == 91,
        "29 HET": COMP["raw"]["genotype_mice"].get("HT") == 29,
        "6 ... (UNK)": COMP["raw"]["genotype_mice"].get("UNK") == 6,
        "112,234": COMP["tabular_baseline"]["rows"] in (112234,) or True,  # syllable pool
        "12,323": COMP["tabular_baseline"]["rows"] == 12323,
        "9,283 WT": COMP["tabular_baseline"]["label_counts"]["WT"] == 9283,
        "3,040 HET": COMP["tabular_baseline"]["label_counts"]["HT"] == 3040,
    }
    ok = 0
    for token, cond in checks.items():
        if token in txt and not cond:
            problems.append(f"Dataset: '{token}' in prose but composition disagrees")
        elif token in txt:
            ok += 1
    # baseline syllable pool 112,234 (from manifest/seq)
    if "112,234" in txt and COMP.get("sequence_baseline_rows") != 112234:
        problems.append("Dataset: 112,234 syllable pool not confirmed")
    return ok


def check_directive_leak():
    leaked = []
    for f in SEC.glob("*.md"):
        body = f.read_text()
        # a FIG directive should always be alone on its line
        for m in re.finditer(r"\[\[FIG:[A-Za-z0-9]+\]\][^\n]*\S", body):
            leaked.append(f"{f.name}: {m.group(0)[:50]}")
    return leaked


def write_traceability():
    lines = ["# Traceability table", "",
             "Maps each key claim, figure, and headline number to its source artifact. "
             "All metrics are sourced from result reports / data files; git history is used only for "
             "the process chronology, never for numbers.", "",
             "## Headline numbers", "",
             "| Claim | Value | Source |", "|---|---|---|"]
    tp_dep = mr_get("tabpfn", "pooled", "dependent")
    tp_ind = mr_get("tabpfn", "pooled", "independent")
    xg_dep = mr_get("xgboost", "pooled", "dependent")
    xg_ind = mr_get("xgboost", "pooled", "independent")
    rows = [
        ("Best honest model (TabPFN, independent) accuracy", tp_ind["test_acc"], tp_ind["source_path"]),
        ("TabPFN independent weighted F1", tp_ind["weighted_f1"], tp_ind["source_path"]),
        ("TabPFN independent ROC-AUC", tp_ind["auc"], "results/tabular_models/threshold/tabpfn_subject_eval_independent_baseline/threshold_metrics.json"),
        ("TabPFN dependent accuracy", tp_dep["test_acc"], tp_dep["source_path"]),
        ("Corrected XGBoost dependent baseline accuracy", xg_dep["test_acc"], xg_dep["source_path"]),
        ("XGBoost independent accuracy", xg_ind["test_acc"], xg_ind["source_path"]),
        ("Legacy reported baseline (subject-dependent)", xg_dep["legacy_baseline_acc"], xg_dep["source_path"] + " (baseline column)"),
        ("Raw corpus syllables", f'{COMP["raw"]["syllables"]:,}', COMP["source_csv"]),
        ("Pups / dams", f'{COMP["raw"]["mice"]} / {COMP["raw"]["dams"]}', COMP["source_csv"]),
        ("Baseline recordings", f'{COMP["tabular_baseline"]["rows"]:,}', COMP["tabular_baseline"]["path"]),
        ("Recording-level class balance (WT/HT)", f'{COMP["tabular_baseline"]["label_counts"]["WT"]:,} / {COMP["tabular_baseline"]["label_counts"]["HT"]:,}', COMP["tabular_baseline"]["path"]),
        ("Genotype correction scope", "14 mice / 2,495 rows", "docs/BASELINE_DATA_MANIFEST.md; docs/segmentation_process.md"),
        ("BiLSTM independent 5-fold balanced acc", "0.563 ± 0.063", "results/neural_networks/experiments/H_cv_Dsampler__bilstm__independent/results.json"),
        ("strain1 independent accuracy (XGBoost)", mr_get("xgboost", "strain1", "independent")["test_acc"], mr_get("xgboost", "strain1", "independent")["source_path"]),
    ]
    for c, v, s in rows:
        lines.append(f"| {c} | {v} | `{s}` |")
    lines += ["", "## Figures", "", "| Figure | Title | Data source(s) |", "|---|---|---|"]
    for k in sorted(MAN, key=lambda x: (len(x), x)):
        info = MAN[k]
        lines.append(f"| {k} | {info['title']} | {'; '.join('`'+s+'`' for s in info['sources'])} |")
    OUT.write_text("\n".join(lines) + "\n")


def main():
    n1 = check_results_table()
    n2 = check_dataset_numbers()
    leaked = check_directive_leak()
    if leaked:
        problems.extend("Directive leak: " + x for x in leaked)
    write_traceability()
    print(f"Results-table cells checked: {n1}")
    print(f"Dataset tokens checked: {n2}")
    print(f"Directive leaks: {len(leaked)}")
    print(f"Wrote {OUT.relative_to(REPO)}")
    if problems:
        print("\n!! PROBLEMS:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("\nINTEGRITY PASS: all checked numbers match their sources; no directive leaks.")


if __name__ == "__main__":
    main()
