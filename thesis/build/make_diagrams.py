#!/usr/bin/env python3
"""F1-F4 conceptual diagrams + F4b reported-vs-corrected baseline (matplotlib only)."""
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import figstyle as S

REPO = Path(__file__).resolve().parents[2]
OI = S.OI


def f1_pipeline():
    fig, ax = S.blank_ax(13, 7.2)
    top_y, th = 80, 13
    xs = [1, 20.5, 40, 59.5, 79]
    bw = 18
    labels = [
        "Recording rig\nAvisoft · 250 kHz\nP4–P12 isolation",
        "Raw WAV\nrecordings\n(16,561)",
        "Segmentation\nERB gammatone\ndetector",
        "CNN syllable typing\nBiT ResNet-50×3\n10 types + Undefined",
        "Syllable rows\n125,576\n(31 columns)",
    ]
    cols = [OI["grey"], "#FFFFFF", OI["skyblue"], OI["skyblue"], OI["yellow"]]
    boxes = []
    for x, lab, c in zip(xs, labels, cols):
        boxes.append(S.box(ax, x, top_y, bw, th, lab, fc=c, fontsize=8.6))
    for i in range(4):
        S.arrow(ax, (xs[i] + bw, top_y + th / 2), (xs[i + 1], top_y + th / 2))
    # fork down from syllable rows
    fork_x = xs[4] + bw / 2
    S.arrow(ax, (fork_x, top_y), (30 + 9, 64.5), rad=-0.15)
    S.arrow(ax, (fork_x, top_y), (66 + 9, 64.5), rad=0.0)
    ax.text(50, 73, "preprocessing — two representations", ha="center",
            fontsize=9, style="italic", color=OI["black"])
    # track boxes
    S.box(ax, 30, 52, 18, 12, "Tabular aggregation\nrecording matrix\n12,323 × 48", fc="#EAF3FB", fontsize=8.4)
    S.box(ax, 66, 52, 18, 12, "Sequence assembly\nper-session order\n408 sessions × ≤256", fc="#FBEFE7", fontsize=8.4)
    # models
    S.arrow(ax, (39, 52), (39, 42))
    S.arrow(ax, (75, 52), (75, 42))
    S.box(ax, 30, 30, 18, 12, "XGBoost · XGBoost-tuned\nTabPFN", fc="#EAF3FB", fontsize=8.6, bold=True)
    S.box(ax, 66, 30, 18, 12, "BiLSTM · 1D-CNN\nTransformer", fc="#FBEFE7", fontsize=8.6, bold=True)
    # evaluation
    S.arrow(ax, (39, 30), (44, 22), rad=0.1)
    S.arrow(ax, (75, 30), (56, 22), rad=-0.1)
    S.box(ax, 28, 11, 44, 11,
          "Evaluation protocol\nsubject-dependent vs subject-independent · per-strain vs pooled · call & subject level",
          fc=OI["yellow"], fontsize=8.8, bold=True)
    # interpretation
    S.arrow(ax, (50, 11), (50, 6.5))
    S.box(ax, 22, -1, 56, 7,
          "Interpretation — feature importance (which acoustic cues) · operating points · generalization",
          fc="#FFFFFF", fontsize=8.6)
    S.save(fig, "F1", "End-to-end USV-to-decision pipeline",
           "Signature figure: the full pipeline from the recording rig through segmentation and CNN "
           "syllable typing to the two preprocessing representations (tabular and sequence), the model "
           "families, the evaluation protocol, and interpretation.",
           ["docs/segmentation_process.md", "docs/preprocessing_pipeline.md",
            "docs/model_development_and_experiments.md", "thesis/data_composition.json"])


def f2_provenance():
    fig, ax = S.blank_ax(12.5, 6.5)
    # before
    S.box(ax, 1, 70, 30, 22,
          "BEFORE — scattered & undocumented\n• code on personal Google Drive\n• monolithic prototype, dormant 2.5 yrs\n• no versioning, no data manifest\n• genotype labels inherited unchecked",
          fc="#F5E6E6", ec=OI["vermillion"], fontsize=8.2)
    S.arrow(ax, (31, 81), (40, 81), lw=2)
    # curation app
    S.box(ax, 40, 70, 28, 22,
          "USV Segmentation app (GUI)\nwraps the segmentation algorithms\nfor the biology researcher\n→ data curation & review\n(Zenodo 10.5281/zenodo.20096810)",
          fc="#EAF3FB", ec=OI["blue"], fontsize=8.2)
    S.arrow(ax, (54, 70), (54, 60), lw=2)
    # canonical file
    S.box(ax, 33, 44, 42, 14,
          "Canonical input — single source of truth\nsegmentation_classification_all_data.xlsx\n125,576 syllable rows · individual genotyping",
          fc=OI["yellow"], fontsize=8.6, bold=True)
    # genotype correction callout
    S.box(ax, 78, 44, 21, 14,
          "Data-integrity fix\n14 mice / 2,495 rows\nHET → WT\n(individual genotyping)",
          fc="#F5E6E6", ec=OI["vermillion"], fontsize=8.0)
    S.arrow(ax, (78, 51), (75, 51), color=OI["vermillion"], rad=0.0)
    S.arrow(ax, (54, 44), (54, 35), lw=2)
    # manifest + filters
    S.box(ax, 20, 22, 34, 12,
          "Baseline manifest + filters\nBASELINE_DATA_MANIFEST.json\n→ 112,234 syllables / 12,323 recordings",
          fc="#FFFFFF", fontsize=8.4)
    S.box(ax, 58, 22, 30, 12,
          "Versioned, documented repo\nmodular src/ · docs/ · per-run READMEs",
          fc="#E7F3EE", ec=OI["green"], fontsize=8.4)
    S.arrow(ax, (37, 44), (37, 34), rad=0.0)
    S.arrow(ax, (54, 28), (58, 28))
    S.arrow(ax, (50, 22), (50, 14))
    S.box(ax, 26, 2, 48, 11,
          "Reproducible pipeline\nrun_external_aggregation → train_classifier / sequence_pipeline → results/",
          fc=OI["yellow"], fontsize=8.6, bold=True)
    S.save(fig, "F2", "Data provenance & single source of truth",
           "From scattered, undocumented inputs to a curated canonical dataset (single source of truth) "
           "with a versioned manifest and a reproducible pipeline; the genotype data-integrity correction "
           "is applied at the canonical-file stage.",
           ["README.md", "docs/BASELINE_DATA_MANIFEST.md", "docs/segmentation_process.md",
            "outputs/external/input/README.md"])


def f3_design_matrix():
    # representation/model rows x (split x scope) columns ; cell = run exists (with acc)
    import csv
    rows = json.loads((REPO / "thesis" / "master_results.json").read_text())
    models = ["xgboost", "xgboost_tuned", "tabpfn", "bilstm", "cnn1d", "transformer"]
    model_lab = {"xgboost": "XGBoost", "xgboost_tuned": "XGBoost-tuned", "tabpfn": "TabPFN",
                 "bilstm": "BiLSTM", "cnn1d": "1D-CNN", "transformer": "Transformer"}
    col_defs = [("pooled", "dependent"), ("pooled", "independent"),
                ("strain1", "dependent"), ("strain1", "independent"),
                ("strain2", "dependent"), ("strain2", "independent")]
    col_lab = ["pooled\ndep", "pooled\nindep", "strain1\ndep", "strain1\nindep", "strain2\ndep", "strain2\nindep"]
    grid = np.full((len(models), len(col_defs)), np.nan)
    for r in rows:
        if r["family"] not in ("tabular", "sequence"):
            continue
        if r["model"] not in models:
            continue
        try:
            j = col_defs.index((r["scope"], r["split"]))
        except ValueError:
            continue
        i = models.index(r["model"])
        if r["test_acc"] != "":
            grid[i, j] = float(r["test_acc"])
    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    cmap = plt.cm.YlGnBu
    im = ax.imshow(np.ma.masked_invalid(grid), cmap=cmap, vmin=0.45, vmax=0.95, aspect="auto")
    ax.set_xticks(range(len(col_lab)))
    ax.set_xticklabels(col_lab, fontsize=9)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels([model_lab[m] for m in models], fontsize=9.5)
    for i in range(len(models)):
        for j in range(len(col_defs)):
            v = grid[i, j]
            if np.isnan(v):
                ax.text(j, i, "—", ha="center", va="center", color=OI["grey"], fontsize=11)
            else:
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        color="white" if v > 0.72 else "black", fontsize=9, fontweight="bold")
    ax.axhline(2.5, color="black", lw=1.5)  # tabular | sequence divider
    ax.text(-0.65, 1, "tabular", rotation=90, va="center", ha="center", fontsize=9, style="italic")
    ax.text(-0.65, 4, "sequence", rotation=90, va="center", ha="center", fontsize=9, style="italic")
    ax.set_title("Experimental-design matrix — test accuracy by model × scope × split")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="test accuracy")
    ax.grid(False)
    S.save(fig, "F3", "Experimental-design matrix",
           "Which model/representation was evaluated under which split and cohort scope; "
           "cells show test accuracy (— = not run). Tabular models are evaluated at recording level, "
           "sequence models at session level.",
           ["thesis/master_results.json"])


def f4_taxonomy():
    fig, ax = S.blank_ax(12, 5.6)
    S.box(ax, 36, 86, 28, 11, "Mouse-USV ASD classifier\n(WT vs Mthfr-HET)", fc=OI["yellow"], fontsize=9.4, bold=True)
    # tabular branch
    S.box(ax, 8, 64, 36, 10, "Tabular — recording-level aggregates (48 features)", fc="#EAF3FB", fontsize=8.8, bold=True)
    S.box(ax, 56, 64, 36, 10, "Sequence — per-session ordered syllables", fc="#FBEFE7", fontsize=8.8, bold=True)
    S.arrow(ax, (44, 86), (26, 74), rad=0.1)
    S.arrow(ax, (56, 86), (74, 74), rad=-0.1)
    # leaves
    tab = [("XGBoost\n(inherited baseline)", "#F5E6E6", OI["vermillion"]),
           ("XGBoost-tuned\n(new)", "#EAF3FB", OI["blue"]),
           ("TabPFN\n(new)", "#E7F3EE", OI["green"])]
    for k, (lab, fc, ec) in enumerate(tab):
        S.box(ax, 4 + k * 13, 44, 12, 12, lab, fc=fc, ec=ec, fontsize=8.0)
        S.arrow(ax, (26, 64), (10 + k * 13, 56), rad=0.0)
    seq = [("BiLSTM\n(new)", OI["orange"]), ("1D-CNN\n(new)", OI["purple"]), ("Transformer\n(new)", OI["vermillion"])]
    for k, (lab, ec) in enumerate(seq):
        S.box(ax, 56 + k * 13, 44, 12, 12, lab, fc="#FBEFE7", ec=ec, fontsize=8.0)
        S.arrow(ax, (74, 64), (62 + k * 13, 56), rad=0.0)
    # legend
    ax.add_patch(plt.Rectangle((6, 22), 4, 4, fc="#F5E6E6", ec=OI["vermillion"]))
    ax.text(11, 24, "inherited at handoff (1 model only)", va="center", fontsize=8.8)
    ax.add_patch(plt.Rectangle((6, 14), 4, 4, fc="#E7F3EE", ec=OI["green"]))
    ax.text(11, 16, "added by this project (everything else)", va="center", fontsize=8.8)
    S.save(fig, "F4", "Model taxonomy — inherited vs new",
           "Model families tried, by representation. Only the single subject-dependent XGBoost existed at "
           "handoff; the tuned XGBoost, TabPFN, and all three sequence models were added by this project.",
           ["thesis/master_results.json", "docs/model_development_and_experiments.md"])


def f4b_reported_vs_corrected():
    """Honest decomposition of the baseline. Numbers from master_results (run col) + legacy ref."""
    rows = {(r["model"], r["split"]): r for r in json.loads((REPO / "thesis" / "master_results.json").read_text())
            if r["family"] == "tabular" and r["scope"] == "pooled"}
    xgb_dep = rows[("xgboost", "dependent")]
    xgb_ind = rows[("xgboost", "independent")]
    tab_ind = rows[("tabpfn", "independent")]
    legacy = float(xgb_dep["legacy_baseline_acc"])      # 0.829
    corrected_dep = float(xgb_dep["test_acc"])          # 0.733
    honest_xgb = float(xgb_ind["test_acc"])             # 0.693
    honest_tab = float(tab_ind["test_acc"])             # 0.729

    labels = ["Legacy reported\n(subject-dependent)",
              "Corrected\n(subject-dependent)",
              "Honest XGBoost\n(subject-independent)",
              "Honest TabPFN\n(subject-independent)"]
    vals = [legacy, corrected_dep, honest_xgb, honest_tab]
    colors = [OI["grey"], OI["blue"], OI["vermillion"], OI["green"]]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    x = np.arange(len(vals))
    bars = ax.bar(x, vals, color=colors, width=0.6, edgecolor="black", linewidth=0.8)
    for xi, v in zip(x, vals):
        ax.text(xi, v + 0.008, f"{v:.3f}", ha="center", fontsize=10, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9.2)
    ax.set_ylabel("test accuracy")
    ax.set_ylim(0.5, 0.9)
    ax.set_title("Reported-vs-corrected baseline — two distinct effects")
    # annotate the two effects
    ax.annotate("", xy=(1, 0.74), xytext=(0, 0.835),
                arrowprops=dict(arrowstyle="->", color=OI["black"], lw=1.4))
    ax.text(0.5, 0.855, "(i) data-integrity\ncorrection", ha="center", fontsize=8.6, style="italic")
    ax.annotate("", xy=(2, 0.70), xytext=(1, 0.738),
                arrowprops=dict(arrowstyle="->", color=OI["black"], lw=1.4))
    ax.text(1.5, 0.76, "(ii) leakage removed\n(regime change)", ha="center", fontsize=8.6, style="italic")
    ax.text(3, 0.755, "best honest\nmodel", ha="center", fontsize=8.6, style="italic", color=OI["green"])
    ax.grid(axis="x")
    S.save(fig, "F4b", "Reported-vs-corrected baseline",
           f"The previously reported subject-dependent accuracy ({legacy:.3f}) is not reproduced by the "
           f"corrected, leak-free pipeline. Two separable effects: (i) data-integrity correction within the "
           f"subject-dependent regime ({legacy:.3f}→{corrected_dep:.3f}), and (ii) honest generalization "
           f"under the subject-independent split ({corrected_dep:.3f}→{honest_xgb:.3f} for XGBoost; the best "
           f"honest model, TabPFN, reaches {honest_tab:.3f}).",
           ["results/tabular_models/xgboost_subject_eval_dependent_baseline/comparison_vs_baseline.txt",
            "results/tabular_models/xgboost_subject_eval_independent_baseline/comparison_vs_baseline.txt",
            "results/tabular_models/tabpfn_subject_eval_independent_baseline/README.md"])


def main():
    S.apply_style()
    f1_pipeline()
    f2_provenance()
    f3_design_matrix()
    f4_taxonomy()
    f4b_reported_vs_corrected()


if __name__ == "__main__":
    main()
