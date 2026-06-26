# 7. Reproducibility and Engineering Contribution

This chapter documents what is, by effort and by impact, the largest part of the project: turning an inherited, non-runnable prototype into a versioned, documented, end-to-end-reproducible system with a single source of truth, and building a graphical tool that lets the biology researcher curate the data in parallel. The chronology in this chapter is reconstructed from the project's version-control history and is used **only** to establish the sequence and scope of the work; every quantitative result elsewhere in the thesis is sourced from the result reports, never from commit messages.

## 7.1 The starting point: a broken inheritance

At handoff the repository was a monolithic prototype with hard-coded paths, authored years earlier and then left dormant. It contained a **single classifier — a basic, subject-dependent XGBoost — and no other models**, no modular structure, no documentation of the data, and no way to run the pipeline from a clean checkout. Reaching a state in which even that one model could be reproduced required rebuilding the whole pipeline. [[REF:F21]] reconstructs the timeline of this work from the commit history, from the inherited prototype through the takeover, the whole-pipeline refactor, the discovery of data leakage, the genotype correction, and the successive additions of models.

[[FIG:F21]]

## 7.2 Inherited versus new

A precise accounting of what was inherited and what this project built is given in Table 5 and visualised in [[REF:F4]]. The distinction matters for both the scientific narrative (everything beyond the inherited model is a new result) and the assessment of the engineering contribution.

**Table 5 — Inherited versus new capabilities.**

| Capability | Status |
|---|---|
| Basic subject-dependent XGBoost | Inherited (only model at handoff) |
| Modular, runnable pipeline (`src/preprocessing`, `src/classification`) | New |
| Subject-independent / group-aware evaluation | New |
| Tuned XGBoost (hyperparameter search) | New |
| TabPFN tabular model | New |
| Sequence models (BiLSTM, 1D-CNN, Transformer) | New |
| Per-strain cohort analysis | New |
| Decision-threshold tuning (leak-free, multi-objective) | New |
| Canonical external data source + baseline manifest | New |
| Genotype data-integrity correction | New |
| Graphical segmentation app for the researcher | New |

[[FIG:F4]]

## 7.3 Single source of truth and data provenance

The data-integrity backbone of the rebuilt system is a **single canonical input file** with a versioned manifest, replacing the previous practice of scattered, undocumented spreadsheets. The provenance chain ([[REF:F2]]) runs: raw recordings → metadata extraction → the graphical segmentation tool → the canonical `segmentation_classification_all_data.xlsx` → baseline filters and manifest → the aggregated tabular and sequence training matrices → per-run result directories. Each stage has a documented script and, for the data, a manifest recording the exact input, the filter rules, and the resulting row counts (Section 3.4).

Two integrity findings emerged from this work and are recorded honestly in the thesis: the **genotype mislabelling** (14 mice / 2,495 rows corrected from HET to WT; Section 3.5) and the resulting, correct, lower baseline (Section 5.2). Both are consequences of having established a single, auditable source of truth where previously there was none.

## 7.4 The graphical segmentation app

To let the biology researcher (Dr. Hava Golan) curate and review the USV data without using the command line, the project built a **graphical segmentation application** that wraps the existing segmentation and typing algorithms behind a simple interface (select data and output folders, choose recording years, run, and inspect results). The tool runs the same algorithms as the Python pipeline and produces the canonical segmentation file that all model training consumes; it is the mechanism by which the data-curation process (and the discovery of the prior-data errors) was carried out in parallel with the modelling work. The application is published as a citable artifact: *USV Segmentation* (v1.0.2), Zenodo, doi:10.5281/zenodo.20096810 [20].

## 7.5 End-to-end reproducibility

The rebuilt system is runnable end-to-end from a clean checkout. Environment setup is pinned (a requirements file and a Dockerfile); the preprocessing pipeline is decomposed into documented steps (ingestion, segmentation, feature computation, typing, enrichment, aggregation); and training is driven by documented command-line flags that select the model, the split regime (`--independent`), the cohort scope (`--strain`), and the baseline data. Every run writes a result directory with its configuration, metrics, plots, and a human-readable README, so that each number in this thesis is traceable to a specific, reproducible run. The documentation set itself — the data manifest, the segmentation and preprocessing references, the CLI reference, and the per-run reports — is a deliverable of the project, and is what makes the integrity claims in this thesis checkable.
