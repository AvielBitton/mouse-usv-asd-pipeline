# Executive Reporting — Training Matrix (Issue #42 / #52)

Checklist and content template for **audit-ready executive summaries** across the full training matrix defined in [Issue #42](https://github.com/AvielBitton/mouse-usv-asd-pipeline/issues/42).

**Deliverables (Phase E):**

1. **Per-scenario pack** (×6) — one per cohort × split mode  
2. **Master comparison table** — CSV + Markdown  
3. **Final consolidated summary** — roll-up + traffic-light commentary  

Suggested output root: `outputs/reports/training_matrix/` (create when first run completes).

---

## Matrix dimensions

| Dimension | Values |
|-----------|--------|
| **Cohort** | Full (post-baseline), Classic BALB/C (2015/2018), Mixed strain (2022–2024) |
| **Split** | Dependent (default), Independent (`--independent`) |
| **Model** | XGBoost, TabPFN, BiLSTM, 1D-CNN, Transformer |
| **Threshold regime** | Default 0.5 vs tuned (Issue #29) |

Six primary training scenarios = 3 cohorts × 2 splits. Each scenario trains all five model families.

---

## 1. Configuration snapshot (required in every pack)

Copy or link these fields so every run is reproducible and comparable.

### 1.1 Data lineage (baseline — Issue #46)

| Field | Source / value |
|-------|----------------|
| **Baseline filter version** | Documented in [`BASELINE_DATA_FILTERS.md`](BASELINE_DATA_FILTERS.md) |
| **Manifest** | [`BASELINE_DATA_MANIFEST.md`](BASELINE_DATA_MANIFEST.md) + [`.json`](BASELINE_DATA_MANIFEST.json) |
| **Input workbook** | `outputs/external/input/segmentation_classification_all_data.xlsx` |
| **Input CSV** | `outputs/external/input/segmentation_classification_all_data.csv` |
| **Input provenance** | Commit [`791aa05`](https://github.com/AvielBitton/mouse-usv-asd-pipeline/commit/791aa05ac4b89f2de69909fcb09af25964902e1f) (Issue #34: genotype/sex corrections) |
| **Session normalization** | `Session=0 → 1` applied **in input file** (919 rows as of 2026-05-16) |
| **Aggregation script** | `scripts/run_external_aggregation.py` |
| **Tabular training data** | `outputs/external/aggregated/all_data_external_baseline.csv` |
| **Sequence training data** | `outputs/external/aggregated/all_data_external_baseline.xlsx` |

**Row counts to cite in reports** (syllable → recording):

| Stage | Syllable rows | Recording rows (aggregated) |
|-------|---------------|-----------------------------|
| Raw input (post-791aa05 + Session) | 125,576 | — |
| After genotype filter (main pool) | 123,807 | 13,342 (main export) |
| **Official baseline pool** | **102,035** | **11,974** (baseline export) |

Per-filter removals (syllable level): genotype −1,769; invalid_sex −3,343; noise −10,334; supplement_offspring −8,095.

### 1.2 Cohort filter (Phase B — Issue #47)

Full specification: [`COHORT_DEFINITIONS.md`](COHORT_DEFINITIONS.md). Verification: `outputs/reports/cohort_verification/`.

State explicitly for scenarios 2 and 3:

| Scenario | Year filter | Strain label | Numeric `pup_strain` |
|----------|-------------|--------------|----------------------|
| 1 — Full | All years in baseline file | All | All |
| 2 — Classic BALB/C | `{2015, 2018}` | `BALB/C` | `2` |
| 3 — Mixed | `{2022, 2023, 2024}` | `BALB/C+BLACK/C57` | `1` |

Reference: `src/preprocessing/utils/io_utils.py` (`STRAIN_1_YEARS`, `strain_from_year`).

### 1.3 Run configuration

| Field | Example |
|-------|---------|
| **Scenario ID** | e.g. `C1_full_dependent` |
| **Git commit / branch** | e.g. `feature/46-baseline-data-filters` @ `<sha>` |
| **Split mode** | Dependent / Independent |
| **CLI flags** | e.g. `--baseline --independent --model xgboost` |
| **Model list** | All five or note partial runs |
| **Seeds** | Tabular / sequence default seeds from code |
| **Results directory** | e.g. `results/tabular_models/xgboost_subject_eval_independent_baseline/` |
| **Hardware** | CPU/GPU, runtime (optional but useful) |
| **Legacy results** | Pre-matrix runs archived under `results/legacy/` — **do not** mix with matrix metrics |

### 1.4 CLI reference

All matrix runs must use **`--baseline`** (not bare `--external`):

```bash
# Tabular
python src/classification/tabular/train_classifier.py --baseline [--independent] [--model tabpfn] [--strain N]

# Sequence
python src/classification/neural_networks/sequence_pipeline.py --baseline [--independent] [--model bilstm]
```

See [`CLI_Flags.md`](CLI_Flags.md).

---

## 2. Metrics block (required)

For **train / validation / test** (as applicable per pipeline):

| Metric | Notes |
|--------|--------|
| Accuracy | |
| Balanced accuracy | Important for class imbalance |
| ROC-AUC | |
| Precision / recall / F1 — **minority class (HT / disease)** | Primary clinical interest |
| Confusion matrix | **Figure + raw counts** |

### Issue #29 — threshold block (required after Phase D)

For **each model** in the scenario:

| Field | Default (0.5) | Tuned |
|-------|---------------|-------|
| Threshold value | 0.5 | From validation (e.g. Youden's J or target HT recall) |
| Test accuracy | | |
| Balanced accuracy | | |
| HT recall / precision / F1 | | |
| Confusion matrix | | |
| Rationale | — | Why this threshold was chosen |

Explicitly call out when **AUC is strong but HT recall collapses at 0.5** — this motivates tuned thresholds.

---

## 3. Training dynamics (where applicable)

| Pipeline | Include |
|----------|---------|
| Tabular (XGBoost) | Learning curves / eval-set AUC vs rounds if available |
| Tabular (TabPFN) | N/A or note single-pass inference |
| Sequence | Loss curves, early stopping epoch, learning-rate schedule |

Paths: `results/.../plots/` under the run directory.

---

## 4. Per-scenario executive pack structure

One folder per scenario × split, e.g.:

```text
outputs/reports/training_matrix/
  C1_full_dependent/
    config_snapshot.md      # sections 1.1–1.3 filled in
    metrics_summary.md      # section 2 per model
    plots/                  # symlinks or copies of confusion matrices, ROC, curves
  C1_full_independent/
  ...
```

Minimum content per pack:

1. Configuration snapshot (§1)  
2. Table of all models × metrics (§2)  
3. Threshold comparison table (§2, Issue #29)  
4. Links to full `results/` run directories  

---

## 5. Master comparison table (required)

Single table: **every model × scenario × split × threshold regime**.

Suggested columns:

| Column | Description |
|--------|-------------|
| `scenario` | C1 / C2 / C3 |
| `cohort_label` | Full / Classic BALB/C / Mixed 2022–24 |
| `split` | dependent / independent |
| `model` | xgboost / tabpfn / bilstm / cnn1d / transformer |
| `threshold_regime` | default_0.5 / tuned |
| `threshold_value` | numeric |
| `test_auc` | |
| `test_balanced_accuracy` | |
| `ht_recall` | minority class |
| `ht_precision` | |
| `ht_f1` | |
| `data_path` | baseline CSV or xlsx used |
| `results_dir` | path to run output |
| `git_sha` | commit used for training |

Files:

- `outputs/reports/training_matrix/master_metrics.csv`
- `outputs/reports/training_matrix/master_metrics.md` (rendered for stakeholders)

---

## 6. Final consolidated summary (required)

After all six scenarios (+ threshold variants) complete:

### 6.1 Roll-up narrative

- Overall findings across cohorts and architectures  
- Dependent vs independent gap (leakage / optimism)  
- Strain-year effects (2015/18 vs 2022–24 vs full)  

### 6.2 Traffic-light assessment

Define criteria once in the summary (example — adjust with stakeholders):

| Color | Independent split (generalization) | Dependent split (optimistic) |
|-------|-----------------------------------|------------------------------|
| **Green** | HT recall ≥ X% at tuned threshold, AUC ≥ Y | Same or noted as upper bound |
| **Amber** | Moderate recall or high variance across cohorts | |
| **Red** | HT recall near 0 at 0.5 despite AUC > 0.7; or independent ≪ dependent | |

Apply per **model** and per **cohort**.

### 6.3 Conclusions (required topics)

- Strengths / weaknesses by architecture (tabular vs sequence)  
- Effect of strain cohort and year restrictions  
- Leakage risk when dependent split inflates metrics  
- Threshold tuning impact (0.5 vs tuned) — link to Issue #29  
- Data quality notes: baseline filters, Issue #34 corrections, rows excluded (cite manifest)  

---

## 7. Path corrections vs Issue #42 text

Issue #42 references `outputs/external/segmentation_classification_all_data.*` at the external root. **Canonical paths in this repo:**

| Role | Path |
|------|------|
| Syllable input | `outputs/external/input/segmentation_classification_all_data.{xlsx,csv}` |
| Tabular aggregate (baseline) | `outputs/external/aggregated/all_data_external_baseline.csv` |
| Sequence aggregate (baseline) | `outputs/external/aggregated/all_data_external_baseline.xlsx` |

Executive reports should use these paths, not the legacy root layout.

---

## Related issues

| Issue | Role |
|-------|------|
| [#42](https://github.com/AvielBitton/mouse-usv-asd-pipeline/issues/42) | Epic — training matrix |
| [#46](https://github.com/AvielBitton/mouse-usv-asd-pipeline/issues/46) | Phase A — baseline filters (done) |
| [#47](https://github.com/AvielBitton/mouse-usv-asd-pipeline/issues/47) | Phase B — cohort CLI |
| [#48](https://github.com/AvielBitton/mouse-usv-asd-pipeline/issues/48)–[#50](https://github.com/AvielBitton/mouse-usv-asd-pipeline/issues/50) | Phase C — training runs |
| [#29](https://github.com/AvielBitton/mouse-usv-asd-pipeline/issues/29) | Threshold implementation |
| [#51](https://github.com/AvielBitton/mouse-usv-asd-pipeline/issues/51) | Phase D — apply thresholds |
| [#52](https://github.com/AvielBitton/mouse-usv-asd-pipeline/issues/52) | Phase E — this document |
