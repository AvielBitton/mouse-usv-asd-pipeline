# Preprocessing & Feature Aggregation — End-to-End Documentation

> **Purpose.** This document is the canonical, research-grade reference for **how the
> syllable-level table becomes training-ready data** — the step between
> `segmentation_classification_all_data.xlsx` (one row per syllable) and the matrices the
> models actually consume. It is the third document in the series:
>
> 1. [`research_data_and_recording.md`](research_data_and_recording.md) — *where the
>    recordings come from* (animals, rig, cohort).
> 2. [`segmentation_process.md`](segmentation_process.md) — *how a WAV becomes a syllable
>    row* (segmentation + CNN typing).
> 3. **this document** — *how syllable rows become a training matrix* (aggregation,
>    encoding, filtering, splitting), for **both** the tabular and the sequence models.
>
> Audience: the authors of the project's research paper (and Claude, when drafting the
> *Feature extraction / Preprocessing* and *Experimental setup* subsections of a Methods
> section). Every column, encoding, filter and design choice is tied to a concrete code
> path so it can be verified and cited.
>
> Resolves Issue #64.

---

## 0. TL;DR — two preprocessing tracks from one syllable table

The same 125,576-row syllable table feeds **two independent preprocessing tracks**, because
the project trains two families of models that need two different data shapes:

| | **Tabular track** | **Sequence track** |
|---|---|---|
| Consumers | **XGBoost, TabPFN** (`train_classifier.py`) | **BiLSTM, 1D-CNN, Transformer** (`sequence_pipeline.py`) |
| Grain (one row / sample =) | **one recording** | **one isolation session** (Name × Day × Session) |
| Representation | **48-column fixed feature vector** (syllables aggregated per type) | **ordered variable-length sequence** of raw syllables (padded to 256) |
| Built by | `legacy/audio_feature_extraction_reduction_by_recording.py` via `extract_features.py` | inline inside `sequence_pipeline.py → load_and_prepare` |
| Persisted artifact | `outputs/external/aggregated/all_data_external_*.csv` | none — built in-memory each run (Excel/CSV cache only) |
| Undefined syllables (type 10) | **dropped** (→ NaN → row drop) | **kept** (embedding has 11 types) |
| Feature scaling | none (tree models) | **StandardScaler**, fit on **train only** |
| Label | `pup_gen` = offspring genotype (WT 0 / HET 1) | `Offspring Genotype (binary)` (WT 0 / HT 1) |

> **One-paragraph summary for the paper.** From the per-syllable segmentation table we
> derive two training sets. For the **tabular** classifiers, syllables are aggregated **per
> recording** into a fixed **48-dimensional** vector — for each of the 10 syllable types we
> store the recording's mean start-frequency, mean end-frequency, relative frequency, and
> mean duration (40 values), plus maternal genotype, pup sex, mean inter-syllable interval,
> age, session, and strain — labeled by offspring genotype. For the **sequence** models,
> each isolation **session** is kept as an ordered list of syllables, each carrying four
> continuous acoustic features (start/end frequency, duration, ISI) plus an embedded
> syllable-type token and two flags, padded/truncated to 256 steps, with continuous features
> standardized on the training split only. Both tracks encode genotype as **WT = 0, HET = 1**
> and use **subject-grouped** train/val/test splits to prevent identity leakage.

---

## 1. Where this sits in the pipeline

```
segmentation_classification_all_data.xlsx           ← INPUT (one row per syllable; segmentation_process.md §7)
   │
   ├──────────────── TABULAR TRACK ────────────────────────────────────────────────
   │   run_external_aggregation.py
   │     → extract_features.run_external_aggregated_feature_extraction()
   │         1. drop non-binary genotype rows (always)           §2.7
   │         2. Session 0 → 1                                     §2.7
   │         3. Strain text → numeric 1/2                         §2.4
   │         4. feature_extraction()  ── per-recording aggregate  §2.2
   │     → all_data_external_main.csv      (13,342 recording rows, 48 cols, headerless)
   │     → all_data_external_baseline.csv  (12,323 rows; +invalid_sex +supplement_offspring)
   │         │
   │         ▼  train_classifier.py  (read_csv header=None, names=COL_NAMES)
   │            X = 46 features, y = pup_gen, groups = mouse_idx → XGBoost / TabPFN
   │
   └──────────────── SEQUENCE TRACK ───────────────────────────────────────────────
       sequence_pipeline.py → load_and_prepare()
         group by Name × Day × Session → ordered syllable sequences  §3
         (continuous ×4 + syllable-type embedding + noise + rec-boundary)
         pad/truncate to max_seq_len=256, StandardScaler(train only)
         → BiLSTM / 1D-CNN / Transformer
```

**Two data sources (tabular).** The aggregation can run over either:
- **External / preferred** — the single corrected workbook
  `outputs/external/input/segmentation_classification_all_data.xlsx`
  (`run_external_aggregated_feature_extraction`). **Always use this** (`--external`); it has
  correct individual genotyping (§2.8).
- **Internal / legacy** — the per-file workbooks under `outputs/legacy/` concatenated
  (`run_aggregated_feature_extraction` → `all_data.csv`). Carries the old genotype-labeling
  error unless regenerated. Kept for reproduction only.

---

## 2. Tabular track — per-recording feature aggregation

**Code:** `steps/extract_features.py` (orchestration) →
`legacy/audio_feature_extraction_reduction_by_recording.py → feature_extraction(X)` (the
algorithm). The 48 column names live in `utils/io_utils.py → AGGREGATE_COL_NAMES`.

### 2.1 Aggregation grain — *recording*, not subject

Despite the informal phrase "subject-level," the aggregation produces **one row per
recording**. `feature_extraction` loops, nested, over:

```
for each mouse Name → for each Day → for each Session → for each Recording Number:
    emit one 48-value row
```

So a row is keyed by **(Name, Day, Session, Recording Number)**. The **last column,
`mouse_idx`**, is the loop index over unique `Name`s — it is the **grouping key** that lets
the trainer split by animal without leakage (§2.9).

> ⚠️ **Grouping-key caveat.** `mouse_idx` is derived from **`Name` alone** (the set of
> unique names), not the cohort document's `(Year, Mother, Name)` triple. If any pup `Name`
> were reused across years, two animals would share a `mouse_idx` and the group-split would
> under-separate them. Confirm `Name` is globally unique (the cohort analysis treats it as
> unique within the corrected file).

### 2.2 The `feature_extraction` algorithm (per recording)

For every recording's slice of syllable rows, four **per-syllable-type aggregates** (each a
length-10 vector indexed by syllable type) and seven **scalars** are computed:

| Block | Columns | How computed (within one recording) |
|-------|---------|--------------------------------------|
| Start frequency | `syll1_s_freq … syll10_s_freq` (0–9) | mean of `Start Point (Hz)` grouped by syllable type; absent types → 0 |
| End frequency | `syll1_e_freq … syll10_e_freq` (10–19) | mean of `End Point (Hz)` grouped by type; absent → 0 |
| Distribution | `syll1_dist … syll10_dist` (20–29) | histogram of type counts, **normalized to sum 1** (relative frequency of each type) |
| Duration | `syll1_dur … syll10_dur` (30–39) | mean of `Duration (time)` grouped by type; absent → 0 |
| `mother_gen` (40) | maternal genotype | first row, binary WT 0 / HET 1 |
| `pup_sex` (41) | pup sex | first row, `LabelEncoder` (F 0 / M 1; see §2.4) |
| `avg_ISI_time` (42) | mean inter-syllable interval | mean of `ISI_time` over the recording's syllables |
| `pup_age` (43) | postnatal day | first row `Day` |
| `session` (44) | isolation session | first row `Session` |
| `pup_strain` (45) | strain id | first row `Strain` (numeric 1/2; §2.4) |
| `pup_gen` (46) | **label** = offspring genotype | first row, binary WT 0 / HET 1 |
| `mouse_idx` (47) | grouping key | the loop index over unique `Name` |

The four aggregate blocks turn an arbitrary number of syllables into a **fixed 40-number
acoustic fingerprint** of the recording: *what each call type sounds like* (start/end
frequency, duration) and *how often each type occurs* (distribution).

### 2.3 The 48 columns (`AGGREGATE_COL_NAMES`)

```
[0–9]   syll1_s_freq … syll10_s_freq   mean start frequency (Hz) per syllable type
[10–19] syll1_e_freq … syll10_e_freq   mean end frequency (Hz) per syllable type
[20–29] syll1_dist … syll10_dist       relative frequency (fraction) of each syllable type
[30–39] syll1_dur … syll10_dur         mean duration (s) per syllable type
[40]    mother_gen                     maternal genotype  (WT 0 / HET 1)
[41]    pup_sex                         pup sex            (F 0 / M 1)
[42]    avg_ISI_time                    mean inter-syllable interval (s)
[43]    pup_age                         postnatal day
[44]    session                         isolation session (1 / 2)
[45]    pup_strain                      strain id          (1 = 2022+, 2 = 2015/2018)
[46]    pup_gen                         LABEL: offspring genotype (WT 0 / HET 1)
[47]    mouse_idx                       grouping key (unique-Name index)
```

The persisted `all_data_external_*.csv` is **headerless** (`np.savetxt`); the column meaning
is positional and defined entirely by `AGGREGATE_COL_NAMES`. A companion
`*_labeled.csv` is also written with these headers and `mother_gen`/`pup_gen` mapped back to
`WT`/`HT` strings for human inspection.

> ⚠️ **The `syllN` ↔ syllable-type off-by-one (document this precisely).** The code fills the
> vectors with `vec[type − 1] = value`. Syllable types run 0–9 (type 10 is dropped, §2.6),
> so the mapping wraps:
>
> | Column suffix | `syll1` | `syll2` | … | `syll9` | **`syll10`** |
> |---|---|---|---|---|---|
> | Syllable **type** | type 1 (Frequency steps) | type 2 (Composite) | … | type 9 (Short) | **type 0 (Complex)** |
>
> i.e. `syllN_*` holds statistics for **type N** for N = 1…9, while **`syll10_*` holds type
> 0 (Complex)** (because `0 − 1 = −1` indexes the last slot). This is **internally consistent
> across all four blocks**, so models are unaffected — but any paper figure that labels
> `syll10` as "type 10 / Undefined" would be **wrong**. (Type labels: `segmentation_process.md`
> §5.3.)

### 2.4 Encodings

- **Genotype** (`mother_gen`, `pup_gen`): `HT`/`HET` unified to `HET`, then **WT = 0, HET = 1**
  (positive class = the ASD model). Done by an explicit dict — *not* `LabelEncoder` — because
  alphabetical encoding would invert it (`HET` < `WT`). If a binary column already exists in
  the sheet it is used directly.
- **Sex** (`pup_sex`): `sklearn LabelEncoder` on the `Sex` column. After the baseline
  `invalid_sex` filter only `{F, M}` remain → **F = 0, M = 1**. (In the *main* aggregate, `U`
  is still present → F 0 / M 1 / U 2.)
- **Strain** (`pup_strain`): the numeric **1 (2022/2023/2024) / 2 (2015/2018)** id from
  `add_strain_from_column` (text `BALB/C+BLACK/C57` → 1, `BALB/C` → 2; see
  `segmentation_process.md` §6). *Note:* `feature_extraction` also builds a `LabelEncoder` on
  strain but writes the **original numeric** value, so `pup_strain ∈ {1, 2}` (the encoder
  output is dead code).

### 2.5 Filtering at aggregation time (the baseline definition)

Row filtering happens here, not in the syllable table. Order and effect
(syllable-level counts from `BASELINE_DATA_MANIFEST.md`):

| Stage | Syllable rows | Removed | Rule |
|-------|--------------:|--------:|------|
| Raw input | 125,576 | — | corrected workbook (incl. Session 0→1) |
| `invalid_genotype` (**always**) | 123,807 | 1,769 | mother & offspring must be WT/HET after HT→HET (keeps `pup_gen` binary) |
| `invalid_sex` (baseline) | 120,464 | 3,343 | `Sex ∈ {M, F}` |
| `supplement_offspring` (baseline) | 112,234 | 8,230 | drop **all** rows of any supplement-arm pup |
| **Baseline pool** | **112,234** | 13,342 total | **`Noise == 1` rows are KEPT** (10,199 remain) |

- **`all_data_external_main`** aggregates the **post-genotype** pool (123,807 syllables →
  **13,342 recording rows**).
- **`all_data_external_baseline`** additionally applies `invalid_sex` + `supplement_offspring`
  (→ **12,323 recording rows**). **This is the official training data** (Issue #42/#46).
- **Optional ablations** (`--external-filter`): `noise`, `undefined_syllable`, or either
  baseline filter in isolation, each written as a `all_data_external_filter_<name>.csv`.

Full filter semantics: [`BASELINE_DATA_FILTERS.md`](BASELINE_DATA_FILTERS.md); counts:
[`BASELINE_DATA_MANIFEST.md`](BASELINE_DATA_MANIFEST.md).

### 2.6 Two NaN-handling quirks that silently shrink the data

`feature_extraction` begins by setting **`Syllable number == 10` (Undefined) → NaN**, then
runs `X.dropna(how='any')` over the feature columns (which include `ISI_time`). Two
consequences worth flagging for the paper:

1. **Undefined syllables are removed** before any aggregate — the tabular features describe
   only confidently-typed calls. (The sequence track, §3, keeps them.)
2. **The first syllable of every recording is removed**, because its `ISI_time` is `NaN`
   (no predecessor; `segmentation_process.md` §4.1). So the per-type aggregates and
   `avg_ISI_time` are computed over syllables **2…N** of each recording, and **recordings
   left with no valid syllable disappear entirely** — part of why 16,561 recordings reduce to
   ~13,342 aggregate rows. This is an undocumented data-reduction step; quantify it and decide
   whether dropping first-syllables is intended (open question §7).

### 2.7 Pre-aggregation transforms (external path)

`run_external_aggregated_feature_extraction` applies, in order, before aggregating:
1. `drop_non_binary_genotype_rows_for_external` — the always-on genotype filter (§2.5).
2. `normalize_session_values` — `Session 0 → 1`.
3. `add_strain_from_column` — strain text → numeric 1/2 (§2.4).

### 2.8 External vs internal dataset

| | **External (preferred)** | **Internal (legacy)** |
|---|---|---|
| Source | one corrected workbook (`outputs/external/input/…xlsx`) | per-file `outputs/legacy/segmentation_*.xlsx`, concatenated |
| Genotype | **correct individual genotyping** | legacy "all pups of a HET dam = HET" error (`segmentation_process.md` §9.7) |
| Strain | from the sheet's `Strain` column | from the `Path` year |
| Output | `all_data_external_main/baseline.csv` | `all_data.csv` |
| Use | **all training** (`--external`) | reproduction only |

### 2.9 Consumption by `train_classifier.py`

- Reads the headerless CSV: `pd.read_csv(data_csv, header=None, names=COL_NAMES)`.
- Optional **cohort filter** `--strain {1,2}` keeps only that `pup_strain` (Phase-B cohort
  runs; see `COHORT_DEFINITIONS.md`).
- **Features / label / groups:** `exclude = {pup_gen, mouse_idx}` →
  **X = the remaining 46 columns**, **y = `pup_gen`**, **groups = `mouse_idx`**.
- **Split (60/20/20):**
  - default **random** (row-level, `random_split`) — note: leaks animal identity across
    splits, so it is the *subject-dependent* (optimistic) evaluation;
  - `--group-split` / `--independent` (`group_aware_split`) — splits **by `mouse_idx`** with
    stratification on `pup_gen` and disjointness asserts → the rigorous *subject-independent*
    evaluation.
- **Models** (`--model`, registry in `models.py`): **XGBoost** (`xgboost` default, plus
  `xgboost_tuned_dependent` / `xgboost_tuned_independent`) and **TabPFN** (`tabpfn`, TabPFN-3
  via the `tabpfn` package, needs `TABPFN_TOKEN`). Tree/PFN models need **no feature
  scaling**, so the tabular track applies none. Class imbalance is handled at fit time:
  XGBoost via **`scale_pos_weight`** (HET = positive), TabPFN natively (and it **merges val
  into train**, having no early-stopping step).
- Results land under `results/tabular_models/<model>_subject_eval_{dependent,independent}[_external]/`.

---

## 3. Sequence track — per-session ordered syllables

**Code:** `src/classification/neural_networks/sequence_pipeline.py`. Unlike the tabular
track, **no intermediate file is written** — the sequences are rebuilt in memory each run
from the syllable table (an Excel→CSV cache is created for speed only).

### 3.1 Grain & grouping key — the isolation session

Sequences are grouped by **`group_key = Name + "_d" + Day + "_s" + Session`** — i.e. **one
sequence per (mouse, postnatal day, isolation session)**. This is the natural behavioral
unit: one 10-minute isolation episode of one pup (`research_data_and_recording.md` §5).
Within a group, rows are sorted by `["Name","Day","Session","Path","Syllable order (in
recording)"]`, so the sequence is the syllables **in temporal order**, concatenated across
the session's recordings.

### 3.2 Cleaning & clipping (inline)

Applied in `load_and_prepare` before grouping:
- Keep only `Offspring Genotype ∈ {WT, HT}`.
- `Duration (time)` **clipped to ≤ 1.0 s** (caps the long-duration tail; cf. raw max 21 s in
  `research_data_and_recording.md` §9).
- `ISI_time` **clipped to [0.0, 10.0] s**, then **`NaN → 0.0`** (first-syllable ISI becomes 0
  rather than being dropped — *opposite* of the tabular track, §2.6).

### 3.3 Per-timestep features

Each syllable (one sequence step) carries:

| Feature | Source | Role |
|---|---|---|
| `Start Point (Hz)` | table | continuous (scaled, §3.6) |
| `End Point (Hz)` | table | continuous |
| `Duration (time)` | table (clipped) | continuous |
| `ISI_time` | table (clipped, NaN→0) | continuous |
| `Syllable number` | table | **embedded** (§3.4) |
| `Noise` | table | flag (0/1) appended as a feature |
| `recording_boundary` | engineered = `1[Syllable order == 1]` | marks the first syllable of each recording inside the session |

Per-timestep input dimension = 4 continuous + 8 embedding + `Noise` + `recording_boundary`
= **14**.

### 3.4 Syllable-type embedding

`nn.Embedding(NUM_SYLLABLE_TYPES = 11, SYLLABLE_EMBED_DIM = 8)` — the categorical syllable
type (0–10, **including** Undefined = 10) is mapped to a learned 8-dim vector. *Rationale:*
syllable type is nominal, not ordinal — one-hot would be sparse and impose no structure,
whereas a learned embedding lets the model place acoustically/behaviorally similar types
near each other and is the standard treatment of categorical tokens in sequence models.

### 3.5 Padding / truncation (`max_seq_len = 256`)

Each session sequence is **truncated to its first 256 syllables** and **zero-padded** up to
256, so every sample is a fixed `256 × feature` tensor with a recorded true `length`. The
models then mask padding: the BiLSTM uses `pack_padded_sequence`, the 1D-CNN length-masks
before mean-pooling, and the Transformer uses a `src_key_padding_mask` (+1 for its CLS
token). 256 comfortably exceeds typical session lengths (the script prints the length
distribution; median session is far below 256), so truncation affects only the longest
sessions.

### 3.6 Feature scaling — `StandardScaler`, **fit on train only**

`USVSequenceDataset(..., fit_scaler=True)` fits a `StandardScaler` on the **concatenated
continuous features of the training sequences only**; the **same** scaler is then applied to
val and test (`scaler=train_ds.scaler`). This is the correct, leakage-free protocol — test
statistics never influence the transform — and the fitted scaler is pickled to
`model/scaler.pkl` for inference. Only the 4 continuous features are scaled; the embedding
and flags are not.

### 3.7 Per-session metadata & label

- **Metadata vector (4-dim, session-level, from the first row):**
  `[Mother Genotype (binary), Sex_enc (M=1), Day, Session]`. Concatenated to the pooled
  sequence representation just before the classification head. *(Note: strain is **not** a
  sequence input, unlike the tabular `pup_strain`.)*
- **Label:** `Offspring Genotype (binary)` (WT 0 / HT 1), one per session.

### 3.8 Split & class imbalance

- **60/20/20**, two strategies mirroring the tabular track:
  - `random_split_sequences` — **session-level** random split (stratified on label);
    subject-dependent.
  - `group_split_sequences` (`--group-split`/`--independent`) — split **by mouse** with
    disjointness asserts; subject-independent.
- **Class weighting:** `pos_weight = n_WT / n_HT` on the training split, fed to
  `BCEWithLogitsLoss`, to offset the WT-majority imbalance (cohort is ~3:1 WT:HET at the pup
  level; `research_data_and_recording.md` §7.3).
- `--baseline` switches the input to `all_data_external_baseline.xlsx` (Issue #42). **Note:
  this `.xlsx` is the *syllable-level* baseline companion (filtered syllable rows), not the
  48-column aggregated `.csv` — the sequence track never consumes the aggregated features
  (§5).**

### 3.9 The three sequence models

All share the embedding + flags front-end (§3.3) and a `Linear(… + 4 metadata) → 64 → 1`
sigmoid head; all are **trained from scratch** (no pretraining), small by design:

| Model | Core | Notes |
|---|---|---|
| **BiLSTM** | 2-layer bidirectional LSTM (hidden 64), final fwd+bwd hidden states | `pack_padded_sequence` masking |
| **1D-CNN** | 3× `Conv1d(k=3)` (64→128→128) + BatchNorm + ReLU, masked mean-pool | length-aware pooling |
| **Transformer** | learned CLS token + sinusoidal positional encoding + 2 encoder layers (d=64, 4 heads, ffn 128) | classifies on the CLS output |

Training: Adam (lr 1e-3), `ReduceLROnPlateau` on val AUC, early stopping (patience 15) on
best val AUC, gradient clipping (max-norm 1.0), up to 100 epochs. Seed = 100 throughout.

---

## 4. Tabular vs Sequence — side-by-side

| Aspect | Tabular | Sequence |
|---|---|---|
| Sample = | recording | session (Name×Day×Session) |
| Input | 46-feature vector | 256×14 ordered tensor |
| Syllable type | aggregated per type (40 cols) | per-step 8-dim embedding |
| Undefined (10) | dropped | kept (embedded) |
| First-syllable rows | dropped (NaN ISI) | kept (ISI→0) |
| Duration handling | mean per type | per-syllable, clipped ≤1 s |
| ISI handling | mean per recording | per-syllable, clipped [0,10], NaN→0 |
| Strain | feature (`pup_strain`) | **not used** |
| Scaling | none | StandardScaler (train-fit) |
| Split unit | row, group = `mouse_idx` | session, group = mouse name |
| Models | XGBoost, TabPFN | BiLSTM, 1D-CNN, Transformer |
| Label | `pup_gen` (WT0/HET1) | `Offspring Genotype (binary)` |

> **Methodological note for the paper.** The two tracks make **different decisions about the
> same raw data** (undefined calls, first-syllable rows, duration/ISI handling, strain).
> These are not bugs but they **do** mean the tabular and sequence models are not trained on
> exactly the same information, so head-to-head accuracy comparisons should be framed as
> *representation + model* comparisons, not pure model comparisons.

---

## 5. Aggregation scripts & intermediate files

| Script / function | Produces | Notes |
|---|---|---|
| `scripts/run_external_aggregation.py` | `all_data_external_main.*`, `all_data_external_baseline.*` (+ `_labeled.csv`) | TensorFlow-free; ~11 min; the standard way to (re)build training data |
| `steps/extract_features.run_external_aggregated_feature_extraction` | the above + optional `all_data_external_filter_<name>.*` | called by the script and by `run_pipeline.py` step 7 |
| `steps/extract_features.run_aggregated_feature_extraction` | `outputs/legacy/aggregated/all_data.*` | internal/legacy path (§2.8) |
| `steps/extract_features.run_feature_extraction` | per-file `outputs/legacy/<file>.csv` | one workbook → one feature CSV |

**Output files (external, the ones you train on):**

| File | Rows | Header? | Purpose |
|---|---|---|---|
| `all_data_external_main.csv` | 13,342 | no | post-genotype aggregate (all sexes, supplement included) |
| `all_data_external_baseline.csv` | 12,323 | no | **official training set** (+invalid_sex +supplement_offspring) |
| `all_data_external_baseline_labeled.csv` | 12,323 | yes | same, genotypes as `WT`/`HT` strings |
| `all_data_external_*.xlsx` | — | — | syllable-level companions (e.g. the sequence track reads the baseline xlsx) |

---

## 6. Is this state of the art?

**Honest assessment for the methods/limitations section.**

**Tabular aggregation.** Hand-engineered per-type aggregates (mean start/end frequency,
relative frequency, mean duration) are a **classical, interpretable bioacoustic feature set**
— directly comparable to the summary statistics in the source papers (Shekel 2021, Gal 2023;
`research_data_and_recording.md` §4) and to MUPET/VocalMat repertoire summaries. Strengths:
transparent, low-dimensional, fast, and a natural fit for XGBoost/TabPFN on a small cohort.
Limitations: the aggregates **discard within-type variance and all temporal order**; only
4 acoustic descriptors per type (no bandwidth, frequency-modulation depth, spectral shape);
and the **recording grain** mixes many short takes per session.

**Sequence preprocessing.** Keeping the **ordered syllable sequence** with a learned
type embedding + masked padding is a **modern, well-founded** design that preserves exactly
what the tabular track throws away (order, per-call detail, call-to-call dynamics — the
phenomenon Gal 2023 studied). The 60/20/20 + **group-by-mouse** option and **train-only**
scaling are correct, leakage-aware practice. Limitations: models are **small and trained
from scratch** on a few-hundred-session corpus (no pretraining / self-supervision, unlike the
BiT classifier upstream); `max_seq_len = 256` and the duration/ISI clips are reasonable but
**unjustified empirically** in code.

**Splitting & evaluation.** Offering **both** subject-dependent (random) and
subject-independent (group) splits is good practice; the **subject-independent** numbers are
the publishable ones (the cohort is strongly longitudinal — `research_data_and_recording.md`
§8). The random/row-level default should be reported only as an optimistic upper bound.

**Bottom line.** A classical, interpretable tabular feature set and a modern,
leakage-aware sequence representation, both feeding appropriately-sized models for a small
cohort. The clearest upgrades are **richer per-call acoustic features** (contours, bandwidth)
and **subject-independent reporting by default**.

---

## 7. Open questions / things to verify before publishing

1. **First-syllable drop (§2.6).** Tabular aggregation silently removes the first syllable of
   every recording (NaN ISI). Quantify the lost syllables/recordings and decide whether to
   impute ISI instead — it currently differs from the sequence track (ISI→0).
2. **`syllN` ↔ type off-by-one (§2.3).** Internally consistent but a labeling trap; make sure
   every paper figure/feature-importance plot maps `syll10` → **type 0 (Complex)**.
3. **`mouse_idx` from `Name` only (§2.1).** Confirm `Name` is globally unique so the
   group-split truly isolates animals.
4. **Recording vs subject grain (§2.1).** The tabular models predict per **recording**, then
   (optionally) split per **mouse** — state clearly whether reported metrics are
   recording-level or aggregated to subject-level.
5. **`max_seq_len = 256` and the duration ≤1 s / ISI ≤10 s clips (§3.2, §3.5).** Provide the
   empirical length/duration distributions that justify these caps (the script prints them —
   capture them for the paper).
6. **Strain asymmetry (§4).** Strain is a tabular feature but absent from the sequence inputs.
   Decide whether that is intended and note it.
7. **Undefined calls treated differently across tracks.** Tabular drops type 10; sequence
   embeds it. Justify, or align, in the Methods.
8. **Main vs baseline for sequences.** Tabular trains on `baseline` (12,323 rec); the sequence
   `--baseline` reads the baseline **xlsx**, but the default path is the raw input file —
   confirm which corpus each reported sequence result used.

---

## 8. Code-path index (for citation/verification)

| Step | File | Key symbols |
|------|------|-------------|
| External aggregation entry | `scripts/run_external_aggregation.py` | `main` |
| Aggregation orchestration | `src/preprocessing/steps/extract_features.py` | `run_external_aggregated_feature_extraction`, `BASELINE_FILTERS`, `apply_single_external_filter`, `drop_non_binary_genotype_rows_for_external`, `normalize_session_values`, `add_strain_from_column` |
| **Aggregation algorithm** | `src/preprocessing/legacy/audio_feature_extraction_reduction_by_recording.py` | `feature_extraction` (the 48-column producer) |
| Column names / encodings | `src/preprocessing/utils/io_utils.py` | `AGGREGATE_COL_NAMES`, `FEATURE_COLUMNS`, `GENOTYPE_NUM_TO_LABEL`, `STRAIN_1_YEARS`, `strain_from_year` |
| Tabular training/consumption | `src/classification/tabular/train_classifier.py` | `COL_NAMES`, `random_split`, `group_aware_split`, `main` |
| Tabular models | `src/classification/tabular/models.py` | model registry (XGBoost, TabPFN) |
| Sequence pipeline | `src/classification/neural_networks/sequence_pipeline.py` | `load_and_prepare`, `USVSequenceDataset`, `random_split_sequences`, `group_split_sequences`, `BiLSTMClassifier`, `CNN1DClassifier`, `TransformerClassifier`, `CONTINUOUS_FEATURES`, `NUM_SYLLABLE_TYPES`, `SYLLABLE_EMBED_DIM` |
| Baseline definition / counts | `docs/BASELINE_DATA_FILTERS.md`, `docs/BASELINE_DATA_MANIFEST.md` | filters, row counts, provenance |
| Cohort (strain) definitions | `docs/COHORT_DEFINITIONS.md` | `--strain` cohorts |
| CLI flags | `docs/CLI_Flags.md` | all training/aggregation flags |

---

*Reproducibility: regenerate the tabular aggregates with
`.venv/bin/python scripts/run_external_aggregation.py`; the row counts in §2.5/§5 are from
`docs/BASELINE_DATA_MANIFEST.md` (re-audit after any change to
`outputs/external/input/`). Sequence sets are rebuilt in-memory by `sequence_pipeline.py`
(seed 100) and are not persisted.*
