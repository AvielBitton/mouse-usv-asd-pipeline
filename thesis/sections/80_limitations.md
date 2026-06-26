# 8. Limitations

This work is deliberately explicit about what it cannot claim.

**Data scale and cohort.** The corpus is 126 pups (29 HET) from one laboratory and one genetic model (*Mthfr* on BALB/c). After subject-grouped splitting, an independent test fold contains only a few dozen mice, and the sequence representation reduces to ~19 HT test sessions. This limits the power of any model — especially the neural sequence models — and means confidence intervals on the headline numbers are wide. The single-fold sequence results in particular must be read together with their cross-validated, deflated estimates (Section 5.4).

**Strain/cohort confound.** Recording year, strain/background label, and HT prevalence covary with genotype (Section 6.4). The strong strain1-independent result (0.903) and the strain2 collapse both reflect this confound. Without a cross-cohort experiment, we cannot fully separate a learned ASD phenotype from learned cohort membership. The strain label change between the 2018 and 2022 cohorts (pure BALB/c vs mixed BALB/c+C57) is itself unresolved — a genuine genetic cross or a labelling-convention change — and is flagged for the biology team.

**Evaluation grain.** Metrics are reported at the recording level (tabular) and session level (sequence); they are **not** aggregated to a single per-mouse decision. A per-subject vote (e.g. majority over a mouse's recordings) might change both the numbers and their interpretation and is left to future work. Consequently, tabular and sequence results are directional, not like-for-like.

**Feature representation.** The tabular features are per-syllable-type aggregates of boundary frequencies, relative frequencies, and durations. They lack richer per-call descriptors (full frequency contour, bandwidth, frequency-modulation depth). Section 6.2 argues this is the most likely cause of the HT-precision wall; it is a limitation of the inherited feature set, not a fundamental limit of USV-based classification.

**Segmentation and typing provenance.** The segmentation detector uses fixed, hand-set thresholds and has **not** been validated against hand-labelled ground truth, so its precision/recall and boundary accuracy are unquantified. The CNN syllable-typer has **no published model card** (training set, class balance, and per-class accuracy are unknown), and a weight shard is absent from the public checkout. Downstream features inherit any errors from these stages.

**Preprocessing choices.** The tabular track silently drops each recording's first syllable (undefined ISI) and all Undefined-typed syllables; the sequence track keeps both. These undocumented-in-prior-work choices were surfaced during the rebuild and are reasonable but not validated (e.g. ISI could be imputed instead of dropped).

**Methodological scope vs. the original plan.** The interim report proposed spectrogram-based CNN classifiers; the delivered system instead uses tabular tree-based models and syllable-sequence networks. This was a deliberate, advisor-guided pivot toward what the rebuilt, leakage-aware infrastructure could evaluate rigorously, but it means the spectrogram-CNN approach of the original plan (and of the prior project [19]) is not evaluated here.
