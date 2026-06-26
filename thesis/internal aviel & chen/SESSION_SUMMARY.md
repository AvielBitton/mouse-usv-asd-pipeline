# Internal session summary — thesis generation (Aviel & Chen)

> Internal handoff note (not part of the submitted thesis). Captures everything from the session that
> produced `thesis/Thesis.docx`, so we can continue iterating efficiently. Date: 2026-06-26.

## 1. What we produced
- **`thesis/Thesis.docx`** — the M.Sc. project book. Word format, English body + Hebrew תקציר + English
  Abstract, bilingual title page, 22 figures, 8 tables, 20 IEEE references, ~30–40 pp.
- Supporting deliverables in `thesis/`: `master_results.{csv,json}`, `best_in_scenario.json`,
  `data_composition.json`, `figure_manifest.json`, `figures/*.{png,pdf}`, `traceability.md`,
  `GAPS.md`, `rubric_self_assessment.md`.
- Reusable build scripts in `thesis/build/`.

## 2. Confirmed decisions (don't re-litigate)
- **Format:** Word `.docx` (not LaTeX). **Language:** English body + Hebrew תקציר + English Abstract;
  bilingual title page. **Scope:** most-complete submission-grade draft + a Gaps List. **Narrative:**
  balanced — reproducibility/data-integrity contribution *and* honest ML findings.
- **Roles (corrected):** Advisor = **Dr. Dror Lederman**; **Dr. Hava Golan** = biology lead researcher /
  data owner / collaborator. The interim PDF wrongly lists Golan as advisor — we surface this, don't hide it.
- **Citations:** IEEE numbered `[n]`, 20 refs (interim's 16 + Shekel 2021 [17] + Gal 2023 [18] + prior HIT
  project [19] + Zenodo software [20]).
- **The `hit/example/` "Lederman" thesis is prior art / template only** (same advisor's earlier PANNs project);
  its content is NOT ours.

## 3. Source-of-truth rule (critical)
- **Every metric/count comes ONLY from result reports & data files** (`results/**/README.md`,
  `results.json`, `threshold_metrics.json`, `master_metrics.csv`, the derived `master_results.{csv,json}`,
  `comparison_vs_baseline.txt`, the segmentation CSV, `docs/` manifests).
- **`git log` is used ONLY for the work/process chronology — never for any number.** If a number appears in
  a commit message, ignore it and cite the report.
- Ignore the legacy `0.829` value except in the reported-vs-corrected figure (Fig. F4b) and its narrative.

## 4. Established facts / headline numbers (verified)
```
Data (from segmentation CSV / manifest):
  raw 125,576 syllables · 126 pups (WT 91 / HET 29 / UNK 6) · 35 dams · 5 years (2015,2018,2022-24)
  baseline pool 112,234 syllables / 106 mice · 12,323 recording rows (WT 9,283 / HT 3,040) · 408 sessions
  strain1 = 2022-24 (mixed BALB/c+C57, 76 mice) · strain2 = 2015/18 (pure BALB/c, 50 mice)
  genotype data-integrity fix: 14 mice / 2,495 rows HET->WT

Tabular pooled (recording level):
  TabPFN  indep  acc 0.729 · wF1 0.743 · balacc 0.662 · AUC 0.783 · HT rec 0.782 · HT prec 0.499  <- HEADLINE
  TabPFN  dep    acc 0.781 · wF1 0.794 · balacc 0.828 · AUC 0.908
  XGBoost dep    acc 0.733 · wF1 0.749 (corrected baseline anchor) ; indep 0.693
  XGBoost-tuned indep acc 0.702 · balacc 0.725 · HT recall 0.869 (best minority-aware)
  Reported-vs-corrected: 0.829 (legacy dep) -> 0.733 (data fix, dep) -> 0.693 XGB / 0.729 TabPFN (indep)
  HT-precision wall ~0.45-0.55 across ALL tabular configs (feature ceiling, not estimator)

Strain (XGBoost): strain1 indep 0.903 (confounded) · strain2 indep collapse 0.654 (HT recall 0.089)
Sequence (session level, weak): Transformer dep 0.659 best baseline; BiLSTM indep 0.704 single-split
  -> 0.563 ± 0.063 under 5-fold grouped CV (dep 0.609 ± 0.055)
Threshold (TabPFN dep, f1/target_recall): acc ~0.82, HT prec ~0.62 (only place the wall is beaten, dep only)
```

## 5. Thesis structure & where each chapter is sourced
Chapters are `thesis/sections/*.md`:
- `10_introduction` (motivation, broken-handoff start, evolved RQs, contributions)
- `20_background` (ASD/USV/Mthfr, Shekel/Gal, ML lit, prior project)
- `30_data` (provenance, rig, composition, single-source-of-truth + genotype fix)
- `40_methods` (segmentation+CNN typing, tabular vs sequence reps, models, **evaluation protocol**)
- `50_results` (Table 1 tabular, Table 2 sequence, F4b decomposition, generalization, CV deflation,
  threshold, per-strain, feature importance, Table 4 best-in-scenario)
- `60_discussion` · `70_reproducibility` (inherited-vs-new Table 5, GUI app, provenance) ·
  `80_limitations` · `90_conclusions`
- Front: `01_abstract_he`, `02_abstract_en`, `03_abbreviations`. Back: `95_references`, `99_appendix`.

## 6. Build pipeline — how to regenerate
Run from repo root with the venv (figures need `PYTHONPATH=thesis/build`):
```
.venv/bin/python thesis/build/extract_results.py        # -> master_results.{csv,json}, best_in_scenario.json
.venv/bin/python thesis/build/compute_dataset.py        # -> data_composition.json
PYTHONPATH=thesis/build .venv/bin/python thesis/build/make_diagrams.py   # F1-F4, F4b
PYTHONPATH=thesis/build .venv/bin/python thesis/build/make_figures.py    # F5-F21 + figure_manifest.json
.venv/bin/python thesis/build/make_traceability.py      # traceability.md + INTEGRITY PASS (fails on mismatch)
PYTHONPATH=thesis/build .venv/bin/python thesis/build/build_docx.py      # -> Thesis.docx
```
Conventions:
- In `sections/*.md`: `[[FIG:Fx]]` places a figure, `[[REF:Fx]]` cross-references it. **Both MUST be alone
  on their own line** (blank line before/after) or they leak as literal text and the figure won't embed.
- Figure numbers are assigned in document order at build time; the List of Figures is generated statically.
- The Word TOC is a live field — open the docx and "Update Field" to populate it.
- `figstyle.py` = Okabe-Ito colorblind-safe palette + diagram primitives + manifest helper.
- New python dependency installed this session: `python-docx`. matplotlib/seaborn/librosa already present.

## 7. Integrity status
`make_traceability.py` cross-checked 42 results-table cells + dataset tokens against the JSON sources —
all match; 0 directive leaks; all 22 figures embedded; 0 stray TODO markers; 20 references.

## 8. Open items / next iterations (see `thesis/GAPS.md` for the full list)
High-value next experiments:
1. **Richer per-call features** (frequency contour, bandwidth, FM depth) to test whether the ~0.50
   HT-precision wall can be broken — highest leverage.
2. **Cross-cohort test** (train strain1 / test strain2 and vice-versa) to separate phenotype from cohort;
   resolve the 2018->2022 strain-label question with the biology team.
3. **Per-subject (per-mouse) aggregated metric** (vote over a mouse's recordings) — clinically meaningful grain.
4. More data / per-mouse aggregation before concluding on sequence models.
5. Validate the segmentation detector vs ground truth; publish a model card for the typing CNN.
Optional: bonus draft manuscript (supervisor rubric); confirm final-grade weighting with the department.

## 9. Things to double-check before submission
- Open `Thesis.docx` in Word and **Update Field** for the Table of Contents (and page numbers).
- Confirm authors' ID numbers on the title page if the department requires them (interim listed
  Chen 305672255, Aviel 204415418 — not currently on the generated title page).
- Confirm the reference list (20) and the roles credit lines read as intended.
- Decide whether `hit/` (rubric, example theses, research PDFs) should stay in the repo long-term.
