# Traceability table

Maps each key claim, figure, and headline number to its source artifact. All metrics are sourced from result reports / data files; git history is used only for the process chronology, never for numbers.

## Headline numbers

| Claim | Value | Source |
|---|---|---|
| Best honest model (TabPFN, independent) accuracy | 0.729 | `results/tabular_models/tabpfn_subject_eval_independent_baseline/comparison_vs_baseline.txt` |
| TabPFN independent weighted F1 | 0.743 | `results/tabular_models/tabpfn_subject_eval_independent_baseline/comparison_vs_baseline.txt` |
| TabPFN independent ROC-AUC | 0.783 | `results/tabular_models/threshold/tabpfn_subject_eval_independent_baseline/threshold_metrics.json` |
| TabPFN dependent accuracy | 0.781 | `results/tabular_models/tabpfn_subject_eval_dependent_baseline/comparison_vs_baseline.txt` |
| Corrected XGBoost dependent baseline accuracy | 0.733 | `results/tabular_models/xgboost_subject_eval_dependent_baseline/comparison_vs_baseline.txt` |
| XGBoost independent accuracy | 0.693 | `results/tabular_models/xgboost_subject_eval_independent_baseline/comparison_vs_baseline.txt` |
| Legacy reported baseline (subject-dependent) | 0.829 | `results/tabular_models/xgboost_subject_eval_dependent_baseline/comparison_vs_baseline.txt (baseline column)` |
| Raw corpus syllables | 125,576 | `outputs/external/input/segmentation_classification_all_data.csv` |
| Pups / dams | 126 / 35 | `outputs/external/input/segmentation_classification_all_data.csv` |
| Baseline recordings | 12,323 | `outputs/external/aggregated/tabular/all_data_external_baseline_labeled.csv` |
| Recording-level class balance (WT/HT) | 9,283 / 3,040 | `outputs/external/aggregated/tabular/all_data_external_baseline_labeled.csv` |
| Genotype correction scope | 14 mice / 2,495 rows | `docs/BASELINE_DATA_MANIFEST.md; docs/segmentation_process.md` |
| BiLSTM independent 5-fold balanced acc | 0.563 ± 0.063 | `results/neural_networks/experiments/H_cv_Dsampler__bilstm__independent/results.json` |
| strain1 independent accuracy (XGBoost) | 0.903 | `results/tabular_models/strain/xgboost_strain1_subject_eval_independent_baseline/comparison_vs_baseline.txt` |

## Figures

| Figure | Title | Data source(s) |
|---|---|---|
| F1 | End-to-end USV-to-decision pipeline | `docs/segmentation_process.md`; `docs/preprocessing_pipeline.md`; `docs/model_development_and_experiments.md`; `thesis/data_composition.json` |
| F2 | Data provenance & single source of truth | `README.md`; `docs/BASELINE_DATA_MANIFEST.md`; `docs/segmentation_process.md`; `outputs/external/input/README.md` |
| F3 | Experimental-design matrix | `thesis/master_results.json` |
| F4 | Model taxonomy — inherited vs new | `thesis/master_results.json`; `docs/model_development_and_experiments.md` |
| F5 | Dataset composition (small multiples) | `thesis/data_composition.json`; `outputs/external/input/segmentation_classification_all_data.csv` |
| F6 | Class balance and syllables-per-subject | `thesis/data_composition.json`; `outputs/external/input/segmentation_classification_all_data.csv` |
| F7 | Syllable-type distribution | `thesis/data_composition.json`; `docs/segmentation_process.md` |
| F8 | Acoustic-feature distributions by genotype | `outputs/external/input/segmentation_classification_all_data.csv`; `hit/research/Shekel et al_2021 (3).pdf` |
| F9 | Master performance — dependent vs independent | `thesis/master_results.json` |
| F10 | Generalization gap (HT recall & precision) | `thesis/master_results.json` |
| F11 | ROC curves (headline tabular models) | `results/tabular_models/threshold/tabpfn_subject_eval_dependent_baseline/probabilities_test.csv`; `results/tabular_models/threshold/tabpfn_subject_eval_independent_baseline/probabilities_test.csv`; `results/tabular_models/threshold/xgboost_subject_eval_dependent_baseline/probabilities_test.csv`; `results/tabular_models/threshold/xgboost_subject_eval_independent_baseline/probabilities_test.csv`; `results/tabular_models/threshold/xgboost_tuned_dependent_subject_eval_dependent_baseline/probabilities_test.csv`; `results/tabular_models/threshold/xgboost_tuned_independent_subject_eval_independent_baseline/probabilities_test.csv` |
| F12 | Precision–Recall curves (HT class) | `results/tabular_models/threshold/tabpfn_subject_eval_dependent_baseline/probabilities_test.csv`; `results/tabular_models/threshold/tabpfn_subject_eval_independent_baseline/probabilities_test.csv`; `results/tabular_models/threshold/xgboost_subject_eval_dependent_baseline/probabilities_test.csv`; `results/tabular_models/threshold/xgboost_subject_eval_independent_baseline/probabilities_test.csv`; `results/tabular_models/threshold/xgboost_tuned_dependent_subject_eval_dependent_baseline/probabilities_test.csv`; `results/tabular_models/threshold/xgboost_tuned_independent_subject_eval_independent_baseline/probabilities_test.csv` |
| F13 | Confusion matrices (headline models) | `results/tabular_models/threshold/tabpfn_subject_eval_dependent_baseline/probabilities_test.csv`; `results/tabular_models/threshold/tabpfn_subject_eval_independent_baseline/probabilities_test.csv`; `results/tabular_models/threshold/xgboost_subject_eval_dependent_baseline/probabilities_test.csv` |
| F14 | Feature importance (XGBoost) | `results/tabular_models/xgboost_subject_eval_dependent_baseline/model/xgboost_model.pkl`; `results/tabular_models/xgboost_subject_eval_independent_baseline/model/xgboost_model.pkl` |
| F15 | Per-strain comparison | `thesis/master_results.json` |
| F16 | HT-precision wall | `thesis/master_results.json` |
| F17 | Threshold-objective operating points | `results/tabular_models/threshold_objectives/summary_objectives.csv` |
| F18 | Sequence-model lever sweep and CV deflation | `results/neural_networks/experiments/_summary/master_metrics.csv`; `results/neural_networks/experiments/H_cv_Dsampler__bilstm__independent/results.json`; `results/neural_networks/experiments/H_cv_Dsampler__bilstm__dependent/results.json` |
| F19 | Annotated segmentation example | `outputs/external/input/segmentation_classification_all_data.csv`; `docs/segmentation_process.md` |
| F20 | Project timeline / Gantt (interim plan) | `hit/project/Project+Midterm+-+Chen+Aharon+%26+Aviel+Bitton.pdf` |
| F21 | Commit-derived work timeline | `local git log (chronology only)` |
| F4b | Reported-vs-corrected baseline | `results/tabular_models/xgboost_subject_eval_dependent_baseline/comparison_vs_baseline.txt`; `results/tabular_models/xgboost_subject_eval_independent_baseline/comparison_vs_baseline.txt`; `results/tabular_models/tabpfn_subject_eval_independent_baseline/README.md` |
