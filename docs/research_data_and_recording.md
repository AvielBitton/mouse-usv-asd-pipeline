# Research Data, Animals & Recording Environment — End-to-End Documentation

> **Purpose.** This document is the canonical, research-grade reference for **the
> biological study behind the data** — *which mice were studied, how they were bred and
> housed, how the ultrasonic-vocalization (USV) recordings were made, and under what
> conditions* — and for the **exact composition of our dataset**
> (`outputs/external/input/segmentation_classification_all_data.csv`). It is the companion
> to [`segmentation_process.md`](segmentation_process.md): that document explains how a WAV
> becomes a syllable row; **this** document explains *where the WAVs come from and what
> animals/experiments they represent*.
>
> Audience: the authors of the project's research paper (and Claude, when drafting the
> *Animals*, *Experimental design*, and *Ultrasonic vocalization recording* subsections of
> a Methods section, and the cohort/sample-size description of a Results section).
>
> **Two sources of truth are combined here:**
> 1. **The published methods** of the lab that generated the recordings, from the two papers
>    that describe this exact rig and these exact models:
>    - **Shekel et al. (2021)**, *Isolation-Induced Ultrasonic Vocalization in Environmental
>      and Genetic Mice Models of Autism*, Front. Neurosci. 15:769670.
>    - **Gal et al. (2023)**, *Temporal dynamics of isolation calls emitted by pups in
>      environmental and genetic mouse models of autism spectrum disorder*,
>      Front. Neurosci. 17:1274039.
> 2. **Our own dataset**, measured directly from the 125,576-row syllable table (counts in
>    §5–§9 were computed by `scripts/analyze_cohort.py` and `scripts/analyze_cohort2.py`,
>    which can be re-run to reproduce every number below).
>
> Where our data and the published descriptions agree, that is stated; where they differ
> (e.g. new years, a new strain label, the genotype-relabeling fix), it is **explicitly
> flagged** so nothing is over-claimed in the paper.

---

## 0. TL;DR — the study in one paragraph

Mouse pups were isolated from the nest and their **isolation-induced ultrasonic
vocalizations** were recorded as an early, pre-verbal readout of social-communication
deficits in **autism-spectrum-disorder (ASD) mouse models**. Two model families exist in
the lab's program: a **genetic** model — *Methylenetetrahydrofolate reductase* (**Mthfr**)
haploinsufficiency on a **Balb/c** background — and an **environmental** model — gestational
exposure to the organophosphate pesticide **chlorpyrifos (CPF)** on a **C57Bl/6 (B6)**
background (Shekel et al., 2021; Gal et al., 2023). **Our dataset is the genetic (Mthfr)
line of this program**: it contains the maternal-genotype × offspring-genotype cross
(**WT-WT / HT-WT / HT-HT**) and **no CPF treatment arm** (see §10). It spans **five recording
years (2015, 2018, 2022, 2023, 2024)**, **126 pups** from **35 dams**, **16,561 recordings**,
and **125,576 detected syllables**. The 2015/2018 material corresponds to the cohorts behind
Shekel (2021) and Gal (2023); 2022–2024 **extend** that cohort with new litters.

---

## 1. Relation to the published studies (provenance)

| | **Shekel et al. (2021)** | **Gal et al. (2023)** | **This project's dataset** |
|---|---|---|---|
| Core question | Spectral–temporal USV features altered by the ASD factor | *Temporal dynamics* of calls within/between isolation sessions | Re-analysis + extension; ML modeling of genotype from USVs |
| Models covered | **Both** Mthfr (genetic) **and** CPF (environmental) | **Both** Mthfr and CPF | **Mthfr genetic model only** (no CPF arm in the table — §10) |
| Sessions analyzed | Single isolation, **P8 only** for cross-model comparison | **Two** sessions (maternal potentiation), P8 | **All recorded days & both sessions are present** (P4–P12; S1/S2) |
| Recording rig | Avisoft (§4) | Avisoft (§4, identical) | Same rig/lab (file paths + settings consistent with §4) |
| Years | ~2015 era | ~2015–2018 era | **2015, 2018, 2022, 2023, 2024** |

**Key takeaway for the paper.** The recording *environment and apparatus* (§3–§5) are
identical to those published by Shekel (2021) and Gal (2023) — we can cite their Methods
verbatim for the rig. What is *new* in our work is (a) the **multi-year extension**
(2022–2024), (b) the use of **all postnatal days and both isolation sessions** rather than a
single P8 snapshot, and (c) treating the data as a **machine-learning corpus** (one row per
syllable, see `segmentation_process.md`).

---

## 2. The ASD mouse models (background from the papers)

### 2.1 Genetic model — *Mthfr* haploinsufficiency (the model in our data)

- **Gene.** *Methylenetetrahydrofolate reductase* (Mthfr; Entrez Gene ID 4524), an essential
  enzyme of the C1 (one-carbon/folate) metabolic pathway. The human **Mthfr 677C>T**
  polymorphism (rs1801133) reduces enzyme activity and is over-represented among ASD patients
  and their mothers (Shekel et al., 2021, Introduction).
- **Background strain.** **Balb/cAnNCrlBR** (Chen et al., 2001).
- **Breeding cross.** Mthfr⁺ᐟ⁺ (**wild-type, Wt**) and Mthfr⁺ᐟ⁻ (**heterozygote, Het**)
  females mated with **Wt males**, producing three groups defined by **maternal × offspring**
  genotype:
  - **Wt:Wt** — Wt offspring of Wt mother (control);
  - **Het:Wt** — Wt offspring of Het mother (maternal-environment effect);
  - **Het:Het** — Het offspring of Het mother (combined genetic load).
  - **Mthfr⁻ᐟ⁻ is not viable.**
- These groups are exactly the **`Genotype Group`** values in our table (`WT-WT`, `HT-WT`,
  `HT-HT`; §6). Both **maternal** and **offspring** genotype matter — which is why the schema
  carries them as separate columns.
- **Face validity.** Mthfr⁺ᐟ⁻ mice show impaired social preference, restricted/repetitive
  behavior, and developmental delay (Sadigurschi & Golan, 2018; Orenbuch et al., 2019;
  Agam et al., 2020).

### 2.2 Environmental model — gestational chlorpyrifos (CPF) — *for context; not in our data*

- **Background strain.** **C57Bl/6J (B6)**, dams/sires from Envigo, Israel.
- **Exposure.** Chlorpyrifos (99.5% purity) in corn oil, by gavage, **gestation day 12–15**,
  0.1 mL/10 g body weight, 22-gauge feeding tube. Groups: **Vehicle (corn oil)**, **CPF-L
  (2.5 mg/kg)**, **CPF-H (5 mg/kg)**.
- We document this model because the published rig/Methods describe it alongside Mthfr, **but
  our dataset contains no CPF treatment groups** (see the explicit check in §10). If a CPF arm
  is added later, it would appear as a *treatment* axis orthogonal to genotype.

### 2.3 Why pup USVs at all?

Isolated pups emit USVs (>30 kHz) that **stimulate maternal approach/retrieval and potentiate
maternal care** (Ehret, 2005; D'Amato et al., 2005; Shair, 2014). They are produced without
learning or imitation, even before ear opening, and are **not** abolished by deafness
(Fischer & Hammerschmidt, 2011; Mahrt et al., 2013) — making them a clean, early behavioral
assay of social-communication circuitry, hence their use as an **ASD-relevant phenotype**
(Scattoni et al., 2009).

---

## 3. Animal husbandry & ethics (identical across both papers)

| Item | Specification | Source |
|---|---|---|
| Light cycle | **12:12 h light/dark** | Shekel 2021; Gal 2023 |
| Temperature | **21–23 °C** | both |
| Food/water | **ad libitum** | both |
| Genotyping | PCR (Chen et al., 2001) for Mthfr/Wt | both |
| Sex/genotype determination (Mthfr) | defined when pups reached **P30** | both |
| Pup identification (CPF) | tail-tip snip on **P1** | both |
| Ethics / oversight | Israeli Council on Animal Care; **Animal Care and Use Committee of Ben-Gurion University of the Negev**, protocols **IL-16-07-14** and **IL-66-11-13**; AAALAC-accredited (per Gal 2023) | both |

> **For the Methods section.** These are directly citable: *"The mouse colonies were
> maintained on a 12:12 h light/dark schedule, temperature 21–23 °C with ad libitum food and
> water. All procedures … approved by the Animal Care and Use Committee of Ben-Gurion
> University of the Negev (protocols IL-16-07-14 and IL-66-11-13)."*

---

## 4. Recording apparatus & acoustic settings (identical across both papers)

| Component | Specification |
|---|---|
| System | **Avisoft Bioacoustics** (Berlin, Germany) |
| Interface | **UltraSoundGate 116Hm** |
| Microphone | **CM16/CMPA** ultrasound condenser microphone |
| Software | **Avisoft Recorder 4.2.17** |
| Sampling frequency | **250 kHz** (250,000 Hz) — Nyquist 125 kHz, required to capture mouse USVs (~35–125 kHz) |
| Acquisition mode | **Trigger mode** |
| Trigger threshold | **0.5 % of signal energy** in the **10–250 kHz** band |
| Microphone placement | **10 cm above the pup** |

This matches the pipeline's assumed **`Fs = 250,000 Hz`** and the 35–125 kHz band of interest
(see `segmentation_process.md` §2–§3). The 0.5%-energy trigger means each WAV is already an
energy-gated *take*, which is consistent with our high recording count and low median
syllables-per-recording (§9).

> **Spectral-variable definitions (for cross-referencing our columns to the papers).**
> Shekel (2021) extracted, per syllable, **Start Frequency** (mean frequency at syllable
> start), **End Frequency** (at syllable end), **Mean Frequency**, **Bandwidth** (max−min
> frequency sample), and **Duration**. Our table's **`Start Point (Hz)`**, **`End Point
> (Hz)`**, and **`Duration (time)`** are the direct analogues of Start/End Frequency and
> Duration (computed by our own DSP — `segmentation_process.md` §4); we do not currently emit
> a bandwidth column. Gal (2023) additionally used **inter-call interval (ICI)**, the analogue
> of our **`ISI_time`**.

---

## 5. The isolation paradigm (the actual experiment)

### 5.1 Single-isolation protocol (Shekel 2021)

Each pup is **separated from the litter** and placed in a **transparent plastic cup, 11 cm
high × 10 cm diameter**; microphone **10 cm above**. After a **10-minute isolation session**
the pup is returned to the home cage; the area is cleaned with **70 % ethanol** between pups.

### 5.2 Maternal-potentiation protocol — two sessions (Gal 2023)

To probe filial attachment/learning, a **second** isolation is added: **S1 (10 min)** →
**reunion with dam + litter (20 min)** → **S2 (10 min)**. The cup sits on a **warm pad**.
Pups typically **escalate** calling in S2 ("maternal potentiation"). **This two-session design
is present in our data:** `Session ∈ {1, 2}` (§7.5). Sessions are sampled at the **1st and
6th minute** in Gal (2023) to capture within-session dynamics.

### 5.3 Postnatal recording days

- **Mthfr model (our model):** 2–3 pups per litter recorded on **P4, 6, 8, 10, 12**; sex &
  genotype assigned at P30.
- **CPF model:** one male + one female per litter recorded on **P2, 5, 8, 14**.
- The papers analyzed **P8** for cross-model comparison (peak USV-production age; Elwood &
  Keeling, 1982). **Our dataset retains all recorded days** (§7.4), enabling developmental
  analyses the papers deferred.

---

## 6. The dataset at a glance

Measured directly from `segmentation_classification_all_data.csv` (re-run
`scripts/analyze_cohort.py` to reproduce):

| Quantity | Value |
|---|---|
| Syllable rows (one per detected call) | **125,576** |
| Columns | **31** (schema in `segmentation_process.md` §7) |
| Recording years | **2015, 2018, 2022, 2023, 2024** |
| Unique pups (mice) — keyed by (Year, Mother, Name) | **126** |
| Unique dams (mothers) | **35** |
| Unique recordings (distinct `Path`/WAV) | **16,561** |
| Mouse strain(s) | Balb/c line (label varies by year — §7.2) |
| Model | **Genetic Mthfr** cross (no CPF arm — §10) |
| Dietary-supplement pups | **10** (separate experimental arm — §7.6) |

> **Definition of "a mouse."** A unique **pup** is identified by the triple
> **(Year, Mother, Name)** to avoid id reuse across years. A pup contributes **many** rows
> (one per syllable) across **many** recordings and (usually) **multiple** days — so
> "126 mice" ≠ "126 recordings" ≠ "125,576 syllables."

---

## 7. Cohort composition (the breakdown tables for the paper)

These are the tables you asked for ("how many mice, how many per year, what types," etc.).
All counts are **pup-level** unless stated otherwise.

### 7.1 Animals, recordings, and syllables per year

| Year | Pups | Dams | Recordings | Syllables |
|------|-----:|-----:|-----------:|----------:|
| 2015 | 31 | 7 | 5,199 | 35,680 |
| 2018 | 19 | 5 | 1,309 | 10,730 |
| 2022 | 30 | 9 | 4,042 | 30,894 |
| 2023 | 22 | 7 | 2,773 | 21,543 |
| 2024 | 24 | 7 | 3,238 | 26,729 |
| **Total** | **126** | **35** | **16,561** | **125,576** |

### 7.2 Strain label by year ⚠️

| Year(s) | `Strain` text in table |
|---|---|
| 2015, 2018 | **BALB/C** |
| 2022, 2023, 2024 | **BALB/C+BLACK/C57** |

> ⚠️ **Flag for the authors.** The Mthfr model is published as **pure Balb/c**
> (Balb/cAnNCrlBR). From 2022 onward the table labels the strain **`BALB/C+BLACK/C57`**,
> implying a **change/cross in genetic background** (Balb/c × C57Bl/6) for the newer litters.
> This must be confirmed and described precisely in the paper — a background change is a
> potential confound for cross-year comparisons, and the strain field is also re-encoded to a
> numeric 1/2 id downstream (`segmentation_process.md` §6). **Open question:** was the line
> deliberately crossed onto B6 after 2018, or is this a labeling convention?

### 7.3 Genotype composition (the ASD factor)

**Offspring genotype (the label of interest):** WT = 91, HT (Het) = 29, UNK = 6.
**Maternal genotype:** HT = 66, WT = 60.

**Genotype Group (Maternal–Offspring cross) — pup counts:**

| Genotype Group | Meaning | Pups |
|---|---|---:|
| **WT-WT** | Wt pup of Wt dam (control) | 54 |
| **HT-WT** | Wt pup of Het dam (maternal effect) | 37 |
| **HT-HT** | Het pup of Het dam (full genetic load) | 29 |
| **WT-UNK** | genotype undetermined | 6 |
| **Total** | | 126 |

**Genotype Group × Year (pup counts):**

| Year | WT-WT | HT-WT | HT-HT | WT-UNK |
|------|------:|------:|------:|-------:|
| 2015 | 9  | 12 | 10 | 0 |
| 2018 | 8  | 7  | 4  | 0 |
| 2022 | 13 | 4  | 7  | 6 |
| 2023 | 8  | 9  | 5  | 0 |
| 2024 | 16 | 5  | 3  | 0 |

> **Note.** The **`WT-UNK`** group (6 pups, all 2022, all sex `U`) are animals whose offspring
> genotype was not resolved; they are dropped by the standard genotype filter downstream
> (`segmentation_process.md` §8). The **April-2026 genotype-relabeling correction**
> (HET→WT for 14 mice / 2,495 rows; `segmentation_process.md` §9.3) has **already been
> applied** in this external file, so the counts above are the *corrected* ones.

### 7.4 Sex composition

**Pups by sex:** Female = 69, Male = 47, Undetermined (U) = 10.

| Year | F | M | U |
|------|--:|--:|--:|
| 2015 | 24 | 7  | 0 |
| 2018 | 9  | 7  | 3 |
| 2022 | 13 | 11 | 6 |
| 2023 | 10 | 12 | 0 |
| 2024 | 13 | 10 | 1 |

**Sex × Offspring genotype (pups):**

| Sex | HT | WT | UNK | Total |
|-----|---:|---:|----:|------:|
| F | 18 | 51 | 0 | 69 |
| M | 9  | 38 | 0 | 47 |
| U | 2  | 2  | 6 | 10 |

> The 10 sex-`U` pups are the `invalid_sex` cases (`segmentation_process.md` §9); 6 of them
> are also the `WT-UNK` genotype pups. Sex is a documented covariate with strong main effects
> in both papers, so the F/M imbalance (≈ 1.47:1) is worth reporting.

### 7.5 Postnatal day (pup age) and sessions

**Distinct recording days present, by year** (the longitudinal grid):

| Year | Days recorded |
|------|---|
| 2015 | P6, P8, P10, P12 |
| 2018 | P4, P6, P8, P10, P12 |
| 2022 | P4, P6 |
| 2023 | P4, P6 |
| 2024 | P4, P6 |

**(pup × day) sessions by day, pooled across years:** P4 = 71, P6 = 96, P8 = 42, P10 = 32,
P12 = 26. Mean **2.12 distinct days per pup** (so most pups are recorded longitudinally on
2–3 ages).

**Isolation sessions** (maternal-potentiation paradigm, §5.2): both **S1** and **S2** are
present except in **2018, which has S1 only**. Recording-level session counts:

| Year | Session 1 (recs) | Session 2 (recs) |
|------|---:|---:|
| 2015 | 1,927 | 3,272 |
| 2018 | 1,309 | 0 |
| 2022 | 1,835 | 2,207 |
| 2023 | 1,232 | 1,541 |
| 2024 | 1,505 | 1,733 |

> **Implication.** The two-session design supports *maternal-potentiation* analyses (Gal 2023)
> for all years **except 2018** (single session). The newer years (2022–2024) concentrate on
> the **early ages P4/P6**, whereas 2015/2018 cover the later ages up to P12 — relevant when
> pooling across years.

### 7.6 Dietary-supplement arm

**10 pups** carry **`Supplement (Offspring) = 1`** (and the same 10 carry `Supplement
(Mother) = 1`). This is a **separate dietary-supplement experimental arm** (cf. Orenbuch
et al., 2019, prenatal nutritional intervention in Mthfr-deficient mice). It is offered as an
ablation filter (`--external-filter supplement_offspring`) precisely because mixing it into
the main genotype analysis would confound the genetic effect (`segmentation_process.md` §8–§9).

---

## 8. Longitudinal / repeated-measures structure (leakage warning)

A single pup appears in the table **~131 recordings on average** (median 112, range 12–455)
and **~997 syllables on average** (median 828, range 26–3,250). 101 of 126 pups have **both
sessions**; pups span **2–3 ages** on average. **For any predictive modeling, splits must be
grouped by animal (and ideally by dam):** rows from the same pup/dam are highly correlated, so
a naïve row-level shuffle would leak identity across train/test and inflate metrics. (This is
why the schema keeps `Mother` and `Name` as explicit grouping keys —
`segmentation_process.md` §7, columns 4 & 8.)

---

## 9. Syllable-level descriptive statistics

All syllables (n = 125,576). Computed by our DSP (definitions in `segmentation_process.md`
§3–§5), reported here as the dataset's acoustic profile.

| Feature | n | Mean | Median | SD | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
| Duration (s) | 125,576 | 0.0658 | 0.0606 | 0.1088 | 0.0102 | 21.136 |
| ISI_time (s) | 109,017 | 0.162 | 0.133 | 0.995 | −1.207 | 309.5 |
| Start Point (Hz) | 125,576 | 67,117 | 61,768 | 16,483 | 0 | 124,512 |
| End Point (Hz) | 125,576 | 66,275 | 62,256 | 15,464 | 0 | 124,512 |

**Syllables per recording:** mean 7.58, median 5, range 1–604.

**Syllable-type distribution** (CNN classification; taxonomy in `segmentation_process.md`
§5.3):

| Syllable type | Count | Complexity group |
|---|---:|---|
| Frequency steps | 44,547 | Multiple Vowels |
| Composite | 17,816 | Advanced Harmonic |
| Two syllables | 13,006 | Multiple Vowels |
| Undefined | 12,311 | Undefined (low-confidence) |
| Chevron | 12,105 | Single Vowel |
| Short | 6,996 | Single Vowel |
| Complex | 6,713 | Single Vowel |
| Flat | 5,246 | Single Vowel |
| Harmonic | 4,316 | Advanced Harmonic |
| Upward | 1,798 | Single Vowel |
| Downward | 722 | Single Vowel |

**Complexity level:** Multiple Vowels 57,553 · Single Vowel 33,580 · Advanced Harmonic
22,132 · Undefined 12,311. (Gal 2023 used a 3-level complexity scheme — Level 1 single-vowel,
Level 2 multiple-vowel, Level 3 harmonic — which our 4-category grouping mirrors, plus an
"Undefined" bin for low-confidence calls.)

**Data-quality flags.** `Noise = 1` on **12,342** rows (start-Hz == end-Hz heuristic;
**kept** in the baseline — `segmentation_process.md` §8); **29** rows have a **0 Hz** boundary
(Welch fallback). 12,311 rows are **Undefined** syllable type (CNN confidence < 0.5).

---

## 10. Is the CPF (environmental) model in our data? — explicit check

**No.** The papers describe two models, but the table's only experimental axis is the
**Mthfr genotype cross**:

- `Genotype Group` takes only **WT-WT / HT-WT / HT-HT / WT-UNK** — the Mthfr design.
- There is **no `Treatment` / `CPF` / `Vehicle` / dose column** anywhere in the 31-column
  schema (`segmentation_process.md` §7).
- The strain text is the **Balb/c line** (the Mthfr background), never a B6/CPF-only label
  (§7.2).

**Therefore, position our study in the paper as the *genetic Mthfr* line of the
Shekel/Gal program, extended to 2022–2024 and to all ages/sessions.** Any sentence implying we
analyze chlorpyrifos data would be incorrect for this dataset.

---

## 11. Open questions / to verify before publishing

1. **Strain change after 2018 (§7.2).** Confirm whether `BALB/C+BLACK/C57` (2022–2024) reflects
   a real Balb/c × C57Bl/6 cross or a labeling convention. This is the single most important
   item — it affects how (or whether) years can be pooled.
2. **2018 single-session (§7.5).** Confirm S2 was genuinely not recorded in 2018 (vs. lost),
   since this excludes 2018 from maternal-potentiation analyses.
3. **Age coverage by year (§7.5).** 2022–2024 cover only P4/P6 while 2015/2018 cover up to P12 —
   intentional design or in-progress collection? State explicitly.
4. **`WT-UNK` / sex-`U` pups (§7.3–7.4).** Confirm these 6 (2022) animals are genuinely
   ungenotyped and should be excluded, not recoverable.
5. **Sample-size mapping to the published Ns.** The papers report Mthfr group sizes at the
   *analyzed P8 subset* (Shekel: Wt:Wt 23 / Het:Wt 18 / Het:Het 21 across the program;
   Gal: Wt:Wt 4 / Het:Wt 13 / Het:Het 8, with 9♂/16♀). Our per-year counts (§7.3) are the
   *full recorded cohort across all days*, so they **overlap with but do not equal** the
   published analysis Ns — describe the relationship precisely rather than claiming identity.
6. **Supplement arm (§7.6).** Decide and document whether the 10 supplement pups are included,
   excluded, or analyzed separately in the paper.
7. **Genotyping at P30 vs. the April-2026 correction.** State that individual genotyping
   (per-animal, from the external segmentation file) supersedes the earlier
   "all pups of a Het dam = Het" metadata (`segmentation_process.md` §9.3), and that this
   document's counts are post-correction.

---

## 12. Citable Methods boilerplate (drop-in draft)

> **Animals & ethics.** Mice on a Balb/cAnNCrlBR background were bred to assess maternal Mthfr⁺ᐟ⁻
> genotype vs. offspring genotype. Mthfr⁺ᐟ⁺ (Wt) and Mthfr⁺ᐟ⁻ (Het) females were mated with Wt
> males, yielding Wt:Wt, Het:Wt, and Het:Het groups (Mthfr⁻ᐟ⁻ is non-viable). Colonies were kept
> on a 12:12 h light/dark cycle, 21–23 °C, with ad libitum food and water. Genotyping used PCR
> (Chen et al., 2001); sex and genotype were determined at P30. Procedures followed the Israeli
> Council on Animal Care and were approved by the Animal Care and Use Committee of Ben-Gurion
> University of the Negev (protocols IL-16-07-14, IL-66-11-13).
>
> **USV recording.** Isolation-induced USVs were recorded with an Avisoft Bioacoustics system
> (UltraSoundGate 116Hm, CM16/CMPA microphone, Avisoft Recorder 4.2.17; Berlin, Germany) at a
> 250 kHz sampling rate in trigger mode (threshold 0.5 % of signal energy in 10–250 kHz). Each
> pup was isolated from the litter in a transparent cup (11 cm high × 10 cm diameter) with the
> microphone 10 cm above; isolation sessions lasted 10 min, and the arena was cleaned with 70 %
> ethanol between pups. For the maternal-potentiation paradigm, a first 10-min isolation (S1) was
> followed by 20 min reunion with the dam and litter and a second 10-min isolation (S2).
>
> **Dataset.** The corpus comprises N = 126 pups from 35 dams recorded across 2015, 2018, 2022,
> 2023 and 2024 (postnatal days P4–P12), totaling 16,561 recordings and 125,576 segmented
> syllables (Wt:Wt = 54, Het:Wt = 37, Het:Het = 29 pups; 69 female / 47 male). [Adjust per the
> §11 confirmations.]

---

## 13. References (the two source papers)

- **Shekel, I., Giladi, S., Raykin, E., Weiner, M., Chalifa-Caspi, V., Lederman, D., Kofman, O.,
  & Golan, H. M. (2021).** Isolation-Induced Ultrasonic Vocalization in Environmental and
  Genetic Mice Models of Autism. *Frontiers in Neuroscience*, 15, 769670.
  https://doi.org/10.3389/fnins.2021.769670
- **Gal, A., Raykin, E., Giladi, S., Lederman, D., Kofman, O., & Golan, H. M. (2023).** Temporal
  dynamics of isolation calls emitted by pups in environmental and genetic mouse models of
  autism spectrum disorder. *Frontiers in Neuroscience*, 17, 1274039.
  https://doi.org/10.3389/fnins.2023.1274039

Supporting in-text citations used above (Chen et al., 2001; Ehret, 2005; D'Amato et al., 2005;
Shair, 2014; Fischer & Hammerschmidt, 2011; Mahrt et al., 2013; Scattoni et al., 2009; Elwood &
Keeling, 1982; Sadigurschi & Golan, 2018; Orenbuch et al., 2019; Agam et al., 2020) appear in
full in the reference lists of the two source papers.

---

*Reproducibility: every count in §6–§9 is produced by `scripts/analyze_cohort.py` and
`scripts/analyze_cohort2.py` over `outputs/external/input/segmentation_classification_all_data.csv`.
Re-run them after any data refresh to update this document.*
