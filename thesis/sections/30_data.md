# 3. Data

## 3.1 Provenance and recording rig

The corpus consists of pup-isolation USV recordings collected over five years (2015, 2018, 2022, 2023, 2024) in the laboratory of Dr. Hava M. Golan, the biology lead researcher and data owner for this project. Animals are *Mthfr* mice on a BALB/c background; the ASD-model (positive) class is the heterozygous (HET) pup and the control class is the wild-type (WT) pup, as described in Section 2.1 and in the project's data documentation.

Recordings were made with an Avisoft ultrasonic system: an UltraSoundGate 116Hm interface and a CM16/CMPA condenser microphone placed approximately 10 cm above the pup, sampling at **250 kHz** (Nyquist 125 kHz, comfortably covering the 35–125 kHz mouse-USV band). Pups were recorded under an isolation paradigm at postnatal days P4–P12, in a single-session protocol [17] and, in later cohorts, a two-session maternal-potentiation protocol [18].

## 3.2 Cohort composition

The raw corpus comprises **125,576 detected syllables** from **126 pups** born to **35 dams**, across the five recording years. At the level of unique animals, the offspring-genotype composition is **91 WT, 29 HET, and 6 of undetermined genotype (UNK)**; the UNK pups are dropped from analysis. [[REF:F5]] summarises the composition across genotype, year, strain, sex, and postnatal day, and [[REF:F6]] shows the class balance and the per-mouse syllable counts.

[[FIG:F5]]

[[FIG:F6]]

Two structural features of the cohort are important for everything that follows. First, the cohort is **WT-skewed**: at the recording level the baseline class balance is roughly three WT to one HET (Section 3.4). Second, the cohort is **strongly longitudinal**: each pup contributes many recordings across multiple ages and sessions (a median of several hundred syllables per pup), so syllables and recordings from the same animal are highly correlated. This longitudinal structure is the single most important fact for the evaluation design (Section 4.5): a naive row-level split lets the same animal appear in both training and test data, inflating apparent performance.

A further cohort distinction is **strain/background**, used as a cohort scope in the experiments: the 2015 and 2018 recordings are labelled pure BALB/c ("strain2"), while the 2022–2024 recordings are labelled with a mixed BALB/c+C57 background ("strain1"). Whether this label reflects a genuine genetic cross or a labelling-convention change is an open question carried forward to the limitations (Section 8); regardless, it confounds genotype with cohort and must be treated with care.

## 3.3 From recordings to syllables

Each WAV recording is processed into a table of **syllables**, one row per detected call, carrying the animal metadata (genotype, sex, day, session, strain), the call's timing (start, end, duration, inter-syllable interval), two boundary-frequency features (start and end frequency in Hz), a CNN-assigned syllable type, and a noise flag. The detection and typing algorithm is described in Section 4.1; [[REF:F19]] shows a representative recording with its detected syllables overlaid. The corpus is dominated by frequency-modulated call types — "Frequency steps" alone accounts for 44,547 syllables — with a long tail of rarer types and a post-hoc "Undefined" class for low-confidence detections ([[REF:F7]]). At the syllable level, the spectral and temporal features (start/end frequency, duration, inter-syllable interval) differ between WT and HET pups in the directions reported by Shekel et al. [17] ([[REF:F8]]).

[[FIG:F19]]

[[FIG:F7]]

[[FIG:F8]]

## 3.4 The baseline dataset and class balance

Not all syllables enter model training. A documented filtering pipeline defines the **baseline dataset**: rows with invalid genotype or invalid sex are removed, and the separate dietary-supplement experimental arm is excluded, while noise-flagged rows are *retained*. This yields a baseline pool of **112,234 syllables from 106 mice**, aggregated to **12,323 recording-level rows** for the tabular models (the unlabelled aggregate exports 12,322 rows; the one-row difference is an export artefact and does not affect training). At the recording level the baseline class balance is **9,283 WT and 3,040 HET recordings** — about 75% / 25%, the ~3:1 imbalance that governs metric choice throughout. For the sequence models the same baseline is grouped into **408 isolation sessions**.

## 3.5 Single source of truth and a data-integrity correction

A defining feature of this project is that all model training draws from **one canonical data file** — the segmentation output `segmentation_classification_all_data.xlsx` — rather than from scattered, undocumented spreadsheets. This file is produced by the graphical segmentation tool (Section 7.4) and is versioned through a baseline data manifest that records the exact input, the filter stages, and the resulting row counts. The provenance chain is shown in [[REF:F2]].

[[FIG:F2]]

During the curation of this canonical file, the project discovered and corrected an **undocumented genotype-labelling error in the prior data**: the original metadata had labelled *all* pups of a HET dam as HET, which is genetically impossible (a HET × WT cross yields roughly half HET and half WT offspring). Using individual genotyping, **14 mice (2,495 metadata rows) were corrected from HET to WT**. This correction, applied at the canonical-file stage, is one reason the project's clean baseline differs from previously reported numbers — a point developed quantitatively in Section 5.2 and [[REF:F4b]]. We treat this as a **data-integrity result, not a regression**: the corrected labels are the genetically correct ones, and the lower accuracy they produce is the honest one.
