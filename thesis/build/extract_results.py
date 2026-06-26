#!/usr/bin/env python3
"""
extract_results.py — Single source of truth for all model metrics in the thesis.

Reads result reports / data files ONLY (never git). Emits:
  thesis/master_results.csv / .json  — one row per run
  thesis/best_in_scenario.json       — best model per (scope, split)

Sources:
  - tabular runs:   results/tabular_models/**/comparison_vs_baseline.txt   (run column + legacy 0.829 ref)
  - NN runs:        results/neural_networks/**/master_metrics.csv           (balanced acc, AUC, AP, MCC ...)
  - threshold runs: results/tabular_models/threshold*/**/threshold_metrics.json
Excludes anything under a legacy/ path.
"""
import csv, json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "results"
OUT_CSV = REPO / "thesis" / "master_results.csv"
OUT_JSON = REPO / "thesis" / "master_results.json"
OUT_BEST = REPO / "thesis" / "best_in_scenario.json"

COLUMNS = [
    "run_id", "family", "model", "eval_level", "split", "scope",
    "test_acc", "train_acc", "balanced_acc", "weighted_f1",
    "wt_precision", "wt_recall", "wt_f1",
    "ht_precision", "ht_recall", "ht_f1",
    "auc", "avg_precision", "mcc",
    "ht_support", "wt_support", "num_test",
    "threshold", "legacy_baseline_acc", "source_path",
]


def blank_row():
    return {c: "" for c in COLUMNS}


def f(x):
    try:
        return round(float(x), 4)
    except (TypeError, ValueError):
        return ""


def split_of(path_str):
    return "independent" if "independent" in path_str else "dependent"


def scope_of(path_str):
    if "strain1" in path_str:
        return "strain1"
    if "strain2" in path_str:
        return "strain2"
    return "pooled"


def model_of(dirname):
    d = dirname.lower()
    if "tabpfn" in d:
        return "tabpfn"
    if "tuned" in d:
        return "xgboost_tuned"
    if "xgboost" in d:
        return "xgboost"
    return "unknown"


# ---------- tabular: comparison_vs_baseline.txt ----------
NUM = r"([-+]?\d*\.?\d+)"
RE_LINE = {
    "test_acc": re.compile(r"Test Accuracy:\s*" + NUM + r"\s*\(baseline:\s*" + NUM),
    "train_acc": re.compile(r"Train Accuracy:\s*" + NUM),
    "weighted_f1": re.compile(r"Weighted F1:\s*" + NUM),
}


def parse_comparison(txt):
    out = {}
    m = RE_LINE["test_acc"].search(txt)
    if m:
        out["test_acc"] = f(m.group(1))
        out["legacy_baseline_acc"] = f(m.group(2))
    for key in ("train_acc", "weighted_f1"):
        m = RE_LINE[key].search(txt)
        if m:
            out[key] = f(m.group(1))
    # per-class blocks
    for cls in ("WT", "HT"):
        block = re.search(r"---\s*" + cls + r"\s*---(.*?)(?:---|=====|$)", txt, re.S)
        if not block:
            continue
        b = block.group(1)
        for metric in ("Precision", "Recall", "F1"):
            mm = re.search(metric + r":\s*" + NUM, b)
            if mm:
                out[f"{cls.lower()}_{metric.lower().replace('precision','precision').replace('recall','recall')}"] = f(mm.group(1))
    return out


def collect_tabular(rows):
    for cmp_path in sorted(RESULTS.glob("tabular_models/**/comparison_vs_baseline.txt")):
        s = str(cmp_path)
        if "legacy" in s or "/threshold" in s:  # threshold handled separately
            continue
        run_dir = cmp_path.parent
        parsed = parse_comparison(cmp_path.read_text())
        r = blank_row()
        r.update(parsed)
        r["run_id"] = run_dir.name
        r["family"] = "tabular"
        r["model"] = model_of(run_dir.name)
        r["eval_level"] = "recording"
        r["split"] = split_of(s)
        r["scope"] = scope_of(s)
        r["threshold"] = 0.5
        r["source_path"] = str(run_dir.relative_to(REPO)) + "/comparison_vs_baseline.txt"
        rows.append(r)


# ---------- NN: master_metrics.csv (baselines + experiments) ----------
def collect_nn(rows):
    csvs = [
        RESULTS / "neural_networks/executive_summaries/sequence_models/master_metrics.csv",
        RESULTS / "neural_networks/experiments/_summary/master_metrics.csv",
    ]
    seen = set()
    for csv_path in csvs:
        if not csv_path.exists():
            continue
        with open(csv_path) as fh:
            for d in csv.DictReader(fh):
                rid = d.get("label") or f'{d["model"]}_{d["split"]}_baseline'
                key = (rid, d["split"])
                if key in seen:
                    continue
                seen.add(key)
                r = blank_row()
                r["run_id"] = rid
                r["family"] = "sequence"
                r["model"] = d["model"]
                r["eval_level"] = "session"
                r["split"] = d["split"]
                r["scope"] = "pooled" if "experiments" not in str(csv_path) else rid.split("__")[0]
                r["test_acc"] = f(d.get("test_accuracy"))
                r["balanced_acc"] = f(d.get("test_balanced_accuracy"))
                r["auc"] = f(d.get("test_auc"))
                r["avg_precision"] = f(d.get("test_average_precision"))
                r["mcc"] = f(d.get("test_mcc"))
                r["ht_recall"] = f(d.get("ht_recall"))
                r["ht_precision"] = f(d.get("ht_precision"))
                r["ht_f1"] = f(d.get("ht_f1"))
                r["wt_f1"] = f(d.get("wt_f1"))
                r["ht_support"] = d.get("ht_support", "")
                r["wt_support"] = d.get("wt_support", "")
                r["num_test"] = d.get("num_test", "")
                r["threshold"] = 0.5
                r["source_path"] = str(csv_path.relative_to(REPO))
                rows.append(r)


# ---------- threshold runs ----------
def collect_threshold(rows):
    for jpath in sorted(RESULTS.glob("tabular_models/threshold*/**/threshold_metrics.json")):
        if "legacy" in str(jpath):
            continue
        d = json.loads(jpath.read_text())
        run_dir = jpath.parent
        for key, tag in (("test_at_0.5", "@0.5"), ("test_at_tuned", "@tuned")):
            m = d.get("metrics", {}).get(key)
            if not m:
                continue
            r = blank_row()
            r["run_id"] = f'{run_dir.name}__{tag}'
            r["family"] = "tabular-threshold"
            r["model"] = model_of(run_dir.name)
            r["eval_level"] = "recording"
            r["split"] = d.get("split", split_of(str(jpath)))
            r["scope"] = f'threshold:{d.get("objective","")}' if tag == "@tuned" else "threshold:0.5"
            r["test_acc"] = f(m.get("accuracy"))
            r["balanced_acc"] = f(m.get("balanced_accuracy"))
            r["auc"] = f(m.get("auc"))
            pc = m.get("per_class", {})
            for cls in ("WT", "HT"):
                c = pc.get(cls, {})
                r[f"{cls.lower()}_precision"] = f(c.get("precision"))
                r[f"{cls.lower()}_recall"] = f(c.get("recall"))
                r[f"{cls.lower()}_f1"] = f(c.get("f1"))
            r["threshold"] = f(m.get("threshold"))
            r["source_path"] = str(jpath.relative_to(REPO))
            rows.append(r)


def enrich_tabular_auc(rows):
    """Backfill AUC + balanced_acc onto pooled tabular rows from the matching
    threshold run's @0.5 metrics (AUC is threshold-independent; same model+data)."""
    lut = {}
    for r in rows:
        if r["family"] == "tabular-threshold" and r["scope"] == "threshold:0.5":
            lut[(r["model"], r["split"])] = (r["auc"], r["balanced_acc"])
    for r in rows:
        if r["family"] == "tabular" and r["scope"] == "pooled":
            hit = lut.get((r["model"], r["split"]))
            if hit:
                if r["auc"] == "":
                    r["auc"] = hit[0]
                if r["balanced_acc"] == "":
                    r["balanced_acc"] = hit[1]


def best_in_scenario(rows):
    """Best model per (family, scope, split) by weighted_f1 (fallback balanced_acc/test_acc)."""
    def score(r):
        for k in ("weighted_f1", "balanced_acc", "test_acc"):
            if r.get(k) not in ("", None):
                return float(r[k])
        return -1
    groups = {}
    for r in rows:
        if r["family"] == "tabular-threshold":
            continue
        g = (r["family"], r["scope"], r["split"])
        if g not in groups or score(r) > score(groups[g]):
            groups[g] = r
    return [
        {"family": k[0], "scope": k[1], "split": k[2], "run_id": v["run_id"],
         "model": v["model"], "test_acc": v["test_acc"], "weighted_f1": v["weighted_f1"],
         "balanced_acc": v["balanced_acc"], "auc": v["auc"],
         "ht_f1": v["ht_f1"], "ht_recall": v["ht_recall"], "ht_precision": v["ht_precision"],
         "source_path": v["source_path"]}
        for k, v in sorted(groups.items())
    ]


def main():
    rows = []
    collect_tabular(rows)
    collect_nn(rows)
    collect_threshold(rows)
    enrich_tabular_auc(rows)
    rows.sort(key=lambda r: (r["family"], r["scope"], r["model"], r["split"]))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    OUT_JSON.write_text(json.dumps(rows, indent=2))
    best = best_in_scenario(rows)
    OUT_BEST.write_text(json.dumps(best, indent=2))

    print(f"Wrote {len(rows)} runs -> {OUT_CSV.name}, {OUT_JSON.name}")
    from collections import Counter
    print("By family:", dict(Counter(r["family"] for r in rows)))
    print("\nBest-in-scenario (non-threshold):")
    for b in best:
        print(f"  {b['family']:18s} {b['scope']:10s} {b['split']:12s} -> {b['model']:14s} "
              f"acc={b['test_acc']} wF1={b['weighted_f1']} balacc={b['balanced_acc']} AUC={b['auc']} "
              f"HT_F1={b['ht_f1']}")


if __name__ == "__main__":
    main()
