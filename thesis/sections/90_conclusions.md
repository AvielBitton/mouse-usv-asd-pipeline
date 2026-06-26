# 9. Conclusions and Future Work

## 9.1 Conclusions

This project rebuilt an inherited, non-runnable USV-classification prototype into a versioned, documented, end-to-end-reproducible system with a single source of truth, and used it to evaluate — honestly and with leakage control — whether ASD-model (*Mthfr*-HET) mice can be distinguished from wild-type controls by their ultrasonic vocalizations.

Returning to the research questions:

- **RQ1 (new models).** Yes: TabPFN improves on the inherited XGBoost in both regimes and is the best pooled generalizer (independent accuracy 0.729, weighted F1 0.743, ROC-AUC 0.783). The tuned XGBoost is the best minority-aware generalizer (independent balanced accuracy 0.725, HT recall 0.869).
- **RQ2 (features).** Classification is driven by per-syllable-type boundary frequencies and durations — consistent with Shekel et al. [17] — but minority-class precision is capped near 0.50 across all models, a ceiling we attribute to the feature representation rather than the estimator.
- **RQ3 (regime and generalization).** The evaluation regime matters decisively: subject-dependent evaluation overstates generalization by several accuracy points and up to ~0.30 in HT recall. Per-strain results are strongly confounded by cohort (strain1 independent 0.903 vs strain2 collapse). Sequence models did not beat the tabular aggregates at this data scale; the most promising configuration deflated from 0.704 to 0.563 ± 0.063 under cross-validation.
- **Engineering question.** Yes: the pipeline is now reproducible end-to-end, with a single canonical data source, a versioned manifest, a graphical curation tool for the researcher, and per-run reports that make every number in this thesis traceable. The rebuild also surfaced and corrected an undocumented genotype error that had inflated a prior baseline.

The honest headline is therefore a calibrated one: USVs support **above-chance, AUC-0.78 generalization** to unseen *Mthfr* mice, with a clear feature-level precision ceiling and a strong cohort confound — findings that are now reproducible and auditable.

## 9.2 Future work

The results point to concrete next steps, in roughly descending order of expected value:

1. **Richer per-call features.** Add full frequency-contour descriptors (mean/min/max/slope, bandwidth, frequency-modulation depth) to the tabular representation to test whether the HT-precision wall is broken — the highest-leverage experiment.
2. **A genuine cross-cohort test.** Train on one strain and evaluate on the other to separate the learned ASD phenotype from cohort membership, and resolve the 2018→2022 strain-label question with the biology team.
3. **Per-subject decisions.** Aggregate recording/session predictions into a single per-mouse vote and report subject-level metrics, which is the clinically meaningful grain.
4. **More data for sequence models.** Re-test the temporal-dynamics hypothesis [18] with more animals or with per-mouse aggregation, before concluding on whether call order helps.
5. **Validate the front end.** Quantify the segmentation detector against hand-labelled ground truth and publish a model card for the syllable-typing CNN, so that downstream feature quality is characterised.
6. **Threshold-calibrated deployment.** If the tool is used to flag candidate ASD-model pups, adopt a target-recall operating point and report the expected false-alarm rate explicitly.
