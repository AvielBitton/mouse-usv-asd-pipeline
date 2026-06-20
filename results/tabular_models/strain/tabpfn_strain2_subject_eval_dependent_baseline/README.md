# tabpfn_strain2_subject_eval_dependent_baseline — TabPFN · subject-dependent · strain2

> TabPFN on the strain2 (pure BALB/c, 2015/2018) baseline cohort, evaluated subject-**dependent** (random row split — mice leak across train/test).

## Overview
- **Model:** TabPFN (prior-data-fitted transformer; no hyperparameter tuning; validation set is merged
  into train, so there is no early-stopping/learning curve or feature importance).
- **Evaluation split:** subject-dependent — random **row-level** split, so the same mouse appears in
  train, val and test (`mouse overlap -- train/test: 47 shared mice`). This is the optimistic,
  leak-prone setting (matches the base model's split type).
- **Cohort:** strain2 — the pure BALB/c classic published cohort (years 2015/2018). The strain filter
  kept 4,751 / 12,323 rows (`pup_strain == 2`), 47 mice.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 951 recordings (WT 72.0% / HT 28.0%); train+val 3,800 rows after the val→train merge.
- **What was adapted vs the base model:** two levers change together — model family (TabPFN instead of
  XGBoost) **and** the data is restricted to the single strain2 cohort (same dependent split type).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.928 | 0.604 | — |
| Recall | 0.785 | 0.842 | — |
| F1 | 0.851 | 0.703 | weighted **0.809** |
| Accuracy | | | **0.801** (train 0.926) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 538, WT→HT 147], [HT→WT 42, HT→HT 224]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.801 | 0.733 | +0.068 |
| Weighted F1 | 0.809 | 0.749 | +0.060 |
| WT F1 | 0.851 | 0.785 | +0.066 |
| HT F1 | 0.703 | 0.649 | +0.054 |
| HT recall | 0.842 | 0.940 | −0.098 |
| HT precision | 0.604 | 0.496 | +0.108 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- On the clean single-strain BALB/c cohort TabPFN beats the base model on the aggregate metrics:
  accuracy 0.801 (+0.068) and weighted F1 0.809 (+0.060) — the homogeneous 2015/2018 data is
  easier to separate than the mixed-background full set.
- The operating point is far better balanced than the base model: **HT precision jumps to 0.604**
  (+0.108) while HT recall eases to 0.842 (−0.098), lifting HT F1 to 0.703 (+0.054). Fewer false
  positives at a modest cost in catching ASD-model pups.
- This is still the **optimistic dependent split** — all 47 mice leak across train/test, so these
  numbers overstate generalization to unseen mice (expect ~10–15 pts lower under an independent split).
- Train 0.926 vs test 0.801 (0.13 gap); TabPFN merges val into train, which inflates the train figure.

## Recommendations
- Treat these as an in-distribution ceiling for the strain2 cohort, not a new-mouse estimate; pair with
  a subject-independent strain2 run before claiming generalization.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices (single-strain run, no
  per-strain split).
- `model/tabpfn_model.pkl` — fitted TabPFN. `logs/out.txt` — flags, split info, class balance.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
