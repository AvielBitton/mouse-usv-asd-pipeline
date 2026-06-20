# tabpfn_strain2_subject_eval_independent_baseline — TabPFN · subject-independent · strain2

> TabPFN on the **strain2** (2015/2018 pure BALB/c) cohort, evaluated **leak-free** (split grouped by mouse).

## Overview
- **Model:** TabPFN (prior-data-fitted transformer; no hyperparameter tuning; validation set is merged
  into train, so there is no early-stopping/learning curve).
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`), so no
  mouse appears in two sets. This is the honest "generalize to unseen mice" setting (harder than the
  dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Cohort:** strain2 — the 2015/2018 pure BALB/c classic published cohort (`--strain 2`).
  Filter kept 4,751 / 12,323 recordings (47 mice).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 1,176 recordings from 10 held-out mice (WT 73.2% / HT 26.8%); train 2,844 / val 731 rows.
- **What was adapted vs the base model:** three levers change together — model family (TabPFN instead of
  XGBoost), evaluation moves subject-dependent → subject-independent, **and** the data is narrowed to the
  strain2 sub-cohort rather than the full baseline.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.775 | 0.369 | — |
| Recall | 0.743 | 0.410 | — |
| F1 | 0.759 | 0.388 | weighted **0.659** |
| Accuracy | | | **0.654** (train 0.941) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 640, WT→HT 221], [HT→WT 186, HT→HT 129]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.654 | 0.733 | −0.079 |
| Weighted F1 | 0.659 | 0.749 | −0.090 |
| WT F1 | 0.759 | 0.785 | −0.026 |
| HT F1 | 0.388 | 0.649 | −0.261 |
| HT recall | 0.410 | 0.940 | −0.530 |
| HT precision | 0.369 | 0.496 | −0.127 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- The minority class collapses: **HT recall drops to 0.410** (−0.530 vs base) — the model now misses
  nearly 6 in 10 ASD-model pups (186 of 315 HT cases predicted WT). HT F1 falls to 0.388 (−0.261).
- HT precision is also weak at **0.369** (−0.127): under half the strain2 test mice are HT, and the
  model is wrong on most of its positive calls (221 false positives vs 129 true positives).
- Overall accuracy (0.654) and weighted F1 (0.659) sit ~0.08–0.09 below the dependent base model — the
  combined cost of the leak-free split plus the much smaller, single-cohort strain2 training pool (only
  27 train mice, ~2.8k rows after merging val).
- Train 0.941 vs test 0.654 (0.29 gap) is the widest of the TabPFN runs and reflects the difficulty of
  generalizing across unseen mice within the small strain2 cohort; TabPFN merges val into train, which
  inflates the train figure.

## Recommendations
- HT performance is poor on both axes at the default 0.5 cut; this strain2-only independent run is not a
  usable operating point — prefer the full-baseline TabPFN independent run, and see the threshold runs
  for recall-controlled cuts.
- If a strain2-specific model is needed, the 47-mouse cohort is likely too small for leak-free TabPFN;
  consider pooling strains or treating strain as a feature rather than a hard filter.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices (single-strain run, no
  per-strain split).
- `model/tabpfn_model.pkl` — fitted TabPFN. `logs/out.txt` — flags, split info, class balance.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
