# Appendix

## A.1 Reproducing the results

The pipeline runs end-to-end from a clean checkout. After installing the pinned environment (`requirements.txt`, or the provided `Dockerfile`), the canonical data is aggregated and models are trained through documented command-line entry points. Representative commands:

- Aggregate the canonical segmentation file into the tabular and sequence baselines: `python scripts/run_external_aggregation.py`.
- Train the inherited baseline and the new tabular models, in either regime: `python src/classification/tabular/train_classifier.py --baseline --model {xgboost,tabpfn} [--independent] [--strain {1,2}]`.
- Train a sequence model: `python src/classification/neural_networks/sequence_pipeline.py --baseline --model {bilstm,cnn1d,transformer} [--independent]`.

Each run writes a result directory containing its configuration, metrics, plots, and a human-readable README. The machine-readable master results table used to build every results figure in this thesis is `thesis/master_results.csv`; the figure manifest (caption and data source for each figure) is `thesis/figure_manifest.json`; the verified dataset composition is `thesis/data_composition.json`.

## A.2 Project timelines

[[REF:F20]] redraws the planned schedule from the interim report. [[REF:F21]] reconstructs the actual work chronology from the version-control history (used for sequence and scope only, never for metrics): from the inherited single-model prototype, through the takeover and whole-pipeline refactor, the discovery of subject leakage, the genotype correction, and the successive additions of the tuned XGBoost, TabPFN, the sequence models, per-strain analysis, and threshold tuning.

[[FIG:F20]]

## A.3 The graphical segmentation tool

The *USV Segmentation* application (v1.0.2; Zenodo doi:10.5281/zenodo.20096810 [20]) wraps the segmentation and typing algorithms behind a simple interface: the user selects a data folder and an output folder, chooses which recording years to process, runs the pipeline, and inspects the results. It runs the same algorithms as the Python pipeline and produces the canonical segmentation file that all model training consumes. It was the vehicle for the parallel data-curation work by the biology researcher, including the review that surfaced the genotype-labelling error.

## A.4 Supplementary results

The complete set of runs (74 model runs, including the threshold and per-objective variants and the full A–H sequence-model lever sweep) is provided in machine-readable form in `thesis/master_results.csv`. The threshold-objective comparison summarised for TabPFN in [[REF:F17]] is available in full in the project's `threshold_objectives/summary_objectives.csv`. The five-fold cross-validation per-fold values underlying the deflation result in [[REF:F18]] are recorded in the corresponding sequence-model run reports.

## A.5 Traceability and gaps

A traceability table mapping each key claim, figure, and number to its source artifact is provided as `thesis/traceability.md`. Open items and known gaps are listed in `thesis/GAPS.md`; the most important are the unresolved strain-label change between the 2018 and 2022 cohorts, the absence of a per-subject (per-mouse) aggregated metric, the unvalidated segmentation detector and un-carded typing CNN, and the recommendation to add richer per-call acoustic features. None of these affects the integrity of the reported numbers, which are all sourced from the result reports.
