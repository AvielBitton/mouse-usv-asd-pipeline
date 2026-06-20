# tabpfn_subject_eval_independent_external — TabPFN · subject-independent · external dataset

**Status:** archived — superseded by `results/tabular_models/tabpfn_subject_eval_independent_baseline`.

> TabPFN on the older externally-validated dataset, evaluated **leak-free** (split grouped by mouse) — the minority class collapses.

## Overview
- **Model:** TabPFN (prior-data-fitted transformer; no hyperparameter tuning; no feature-importance or
  learning curve; the validation set is merged into train).
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--group-split`), so no
  mouse appears in two sets. Honest "generalize to unseen mice" setting, harder than the dependent base
  model (which splits rows randomly and lets mice leak across train/test).
- **Dataset:** older `--external` cohort (`outputs/aggregated_external/all_data_external.csv`), predating
  the official Issue #46 baseline filters and the April-2026 HET→WT correction.
  Train 7,706 / Val 3,018 / Test 2,357 rows; Test = 2,357 recordings from 23 held-out mice
  (WT 79.8% / HT 20.2%).
- **Label note:** this legacy run encodes class 0 = HT and class 1 = WT (the opposite of the current
  pipeline); the numbers below are reported by class name, not by index.
- **What was adapted vs the base model:** model family (TabPFN instead of XGBoost), evaluation moves
  from subject-dependent to subject-independent, **and** the data is the older external cohort.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.788 | 0.163 | — |
| Recall | 0.778 | 0.171 | — |
| F1 | 0.783 | 0.166 | weighted **0.659** |
| Accuracy | | | **0.656** (train 0.831) |

Confusion matrix (rows = true, cols = pred): `[[HT→HT 81, HT→WT 394], [WT→HT 417, WT→WT 1465]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.656 | 0.733 | −0.077 |
| Weighted F1 | 0.659 | 0.749 | −0.090 |
| WT F1 | 0.783 | 0.785 | −0.002 |
| HT F1 | 0.166 | 0.649 | −0.483 |
| HT recall | 0.171 | 0.940 | −0.769 |
| HT precision | 0.163 | 0.496 | −0.333 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- The minority class **collapses**: HT recall 0.171 and HT F1 0.166 mean the model misses ~5 of every 6
  ASD-model pups. It predicts WT for almost everyone (only 498 of 2,357 test rows called HT, 81 of them
  correct), so overall accuracy 0.656 is carried almost entirely by the 79.8% WT majority.
- HT precision 0.163 is even below the 20.2% HT prevalence — HT calls are no better than random (a
  blind guess at the base rate would score ~0.202), the worst tabular run on this anchor (HT F1 −0.483
  vs base).
- WT performance is intact (F1 0.783, −0.002 vs base), which is what props up the weighted score and
  masks the failure on the class that matters.
- The leak-free split plus the older external cohort (no Issue #46 filters, no HET→WT correction)
  compound: the same TabPFN on the corrected `--baseline` data reaches HT F1 0.610 — this external run
  is why it was superseded.

## Recommendations
- Do not use this run for any new-mouse estimate; prefer the superseding
  `results/tabular_models/tabpfn_subject_eval_independent_baseline`, which fixes the minority collapse.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per strain).
- `logs/out.txt` — flags, split info, class balance, classification report, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
