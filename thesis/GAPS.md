# Gaps List — open items for the authors

Items flagged during thesis construction. None affects the integrity of the reported numbers (all sourced from result reports); these are open questions, data caveats, and optional additions.

## Data / biology (for the biology team)
1. **Strain-label change 2018→2022.** The label moves from `BALB/C` (strain2) to `BALB/C+BLACK/C57` (strain1). Is this a genuine genetic cross onto C57, or a labelling-convention change? This determines whether the strain1/strain2 split is biological or administrative, and underlies the strain confound (§6.4, §8).
2. **2018 single-session.** Confirm that the second isolation session was genuinely not recorded in 2018 (vs lost).
3. **UNK / sex-U animals.** 6 UNK-genotype and 10 sex-U pups are dropped; confirm they are genuinely unresolvable.
4. **Supplement arm.** 10 dietary-supplement pups are excluded from the baseline; confirm this is the intended scope for the final paper.

## Method / data engineering
5. **Per-subject metric.** Metrics are recording/session-level, not aggregated to one decision per mouse. A per-mouse vote should be reported as a separate, clinically meaningful analysis.
6. **First-syllable drop.** The tabular track drops each recording's first syllable (undefined ISI); consider imputing ISI instead and quantifying the lost rows.
7. **Tabular CSV row count.** Labeled aggregate = 12,323 rows (matches the manifest); unlabeled aggregate = 12,322 (1-row export artefact). Cosmetic; the thesis cites 12,323.
8. **Segmentation validation.** No hand-labelled ground truth; segmentation precision/recall and boundary accuracy are unquantified.
9. **Typing CNN model card.** No training set / per-class accuracy published; a weight shard is absent from the public checkout.

## Optional additions (ask the authors before building)
10. **Cross-cohort experiment.** Train on strain1, test on strain2 (and vice versa) to separate phenotype from cohort — the single most valuable next experiment.
11. **Richer per-call features.** Add frequency-contour / bandwidth / FM-depth descriptors to test whether the ~0.50 HT-precision wall can be broken.
12. **Bonus draft manuscript.** The supervisor rubric awards bonus points for a draft journal manuscript; not produced by default. Decide whether to prepare one.
13. **Final-grade weighting.** The rubric .docx files define component scores (supervisor / examiner / defence, each /100) but not the final weighting formula; confirm with the department.

## Reference / framing notes
14. **Reference count.** Final list is 20 (the interim's 16 + Shekel 2021 + Gal 2023 + the Zenodo software + the prior HIT project). Confirm acceptable.
15. **Roles conflict.** The interim PDF lists Dr. Hava Golan as "Advisor"; per the authors, Dr. Dror Lederman is the advisor and Dr. Golan is the biology lead / data owner. The thesis uses the corrected roles and notes the discrepancy.
