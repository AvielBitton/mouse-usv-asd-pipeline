# xgboost_subject_eval_independent_external — XGBoost · subject-independent · external dataset

**Status:** archived — superseded by the current `--baseline` runs under `results/`.

> Untuned legacy XGBoost on the early *external* dataset, evaluated **leak-free** (split grouped by mouse) — the most rigorous legacy setting, and it collapses.

## Overview
- **Model:** plain XGBoost (untuned legacy recipe; no per-split hyperparameter search).
- **Evaluation split:** subject-independent — group-aware split **by `mouse_idx`** (`--group-split` / `--independent`), so no mouse appears in two sets. This is the honest "generalize to unseen mice" setting (harder than the dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** legacy **external** corpus (`--external`): `outputs/aggregated_external/all_data_external.csv`, 13,081 rows from 115 mice. Predates the official baseline (Issue #46 filters + April-2026 HET→WT correction), so numbers are not directly comparable to current `--baseline` runs.
- **Class convention here is inverted vs the base model:** in this run class 0 = HET (the ASD-model positive minority) and class 1 = WT (majority). Test = 2,357 recordings from 23 held-out mice (HT 20.2% / WT 79.8%).
- **What was adapted vs the base model:** two levers change together — dataset (legacy external vs official baseline) **and** evaluation moves from subject-dependent to subject-independent.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.948 | 0.302 | — |
| Recall | 0.476 | 0.897 | — |
| F1 | 0.634 | 0.452 | weighted **0.597** |
| Accuracy | | | **0.561** (train 0.752) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 896, WT→HT 986], [HT→WT 49, HT→HT 426]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.561 | 0.733 | −0.172 |
| Weighted F1 | 0.597 | 0.749 | −0.152 |
| WT F1 | 0.634 | 0.785 | −0.151 |
| HT F1 | 0.452 | 0.649 | −0.197 |
| HT recall | 0.897 | 0.940 | −0.043 |
| HT precision | 0.302 | 0.496 | −0.194 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- **Near-collapse onto the minority class:** the model predicts HET for almost everyone (HT recall 0.897, WT recall only 0.476). It mislabels 986 of 1,882 true WT recordings as HET, dragging test accuracy down to 0.561 — well below the 79.8% WT prior.
- The leak-free external split is brutal here: **−0.172 test accuracy** and **−0.197 HT F1** vs the dependent base model, far past the usual 10–15 pt dependent→independent drop, compounded by the noisier pre-Issue-#46 external data.
- Class separation is essentially gone — **HT precision 0.302** (≈7 in 10 HET calls are false positives); HT F1 0.452 is mostly recall, not real discrimination.
- Train 0.752 vs test 0.561 (0.19 gap): even on its own training mice the untuned recipe is weak, so this is under-fitting plus poor generalization, not classic overfitting.

## Recommendations
- Do not use this run for any operating-point or generalization estimate — it is superseded by the current `--baseline` XGBoost runs (Issue #46 filters + HET→WT correction). Prefer those for the honest "new-mouse" number.

## Artifacts
- `plots/confusionmatrix.png`, `plots/conf_matrix.png`, `plots/confusionmatrix_strain1.png`, `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per strain).
- `plots/AUC_error.png` — training/validation AUC curve. `plots/feature_importances_0.png`, `plots/feature_importance_1.png` — feature importances.
- `model/XGBmodel.pkl` — fitted XGBoost. `logs/out.txt` — flags, split info, class balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.

## Original notes
> # Results — External Data, Subject-Independent Evaluation
>
> **Data source:** `outputs/external/aggregated/all_data_external.csv` (13,081 rows, 115 mice)
> **Evaluation:** Subject-independent — group split by subject (no subject in more than one set)
> **Flags:** `--external --group-split` (or `--external --independent`)
>
> ```bash
> python3 src/classification/tabular/train_classifier.py --external --group-split
> ```
>
> Most rigorous setting: correct genotyping and no leakage across subjects.

---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
