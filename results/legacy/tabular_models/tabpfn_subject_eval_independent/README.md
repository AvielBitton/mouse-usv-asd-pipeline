# tabpfn_subject_eval_independent — TabPFN · subject-independent

**Status:** archived — superseded by `results/tabular_models/tabpfn_subject_eval_independent_baseline`.

> Legacy TabPFN on the pre-baseline data, evaluated **leak-free** (split grouped by mouse) — collapses to near-chance.

## Overview
- **Model:** TabPFN (prior-data-fitted transformer; no hyperparameter tuning; validation set is merged
  into train, so there is no early-stopping/learning curve or feature importance).
- **Evaluation split:** subject-independent — group-aware split **by mouse** (`--group-split`), so no
  mouse appears in two sets. This is the honest "generalize to unseen mice" setting (harder than the
  dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** legacy `outputs/aggregated/all_data.csv` — predates the Issue #46 filters and the
  April-2026 HET→WT label correction. Test = 1,466 rows from 18 held-out mice (WT 72.0% / HT 28.0%);
  train 6,000 / val 2,049.
- **Label note:** this legacy run encodes class 0 = HT (minority, 28.0%) and class 1 = WT (majority);
  numbers below are remapped to the standard WT/HT naming used by the base model.
- **What was adapted vs the base model:** two levers change together — model family (TabPFN instead of
  XGBoost) **and** evaluation moves from subject-dependent to subject-independent, on the older dataset.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.744 | 0.308 | — |
| Recall | 0.544 | 0.521 | — |
| F1 | 0.629 | 0.387 | weighted **0.561** |
| Accuracy | | | **0.538** (train 0.862) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 574, WT→HT 481], [HT→WT 197, HT→HT 214]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.538 | 0.733 | −0.195 |
| Weighted F1 | 0.561 | 0.749 | −0.188 |
| WT F1 | 0.629 | 0.785 | −0.156 |
| HT F1 | 0.387 | 0.649 | −0.262 |
| HT recall | 0.521 | 0.940 | −0.419 |
| HT precision | 0.308 | 0.496 | −0.188 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- This legacy leak-free run is **near chance**: accuracy 0.538 and weighted F1 0.561, ~0.19 below the
  dependent base model on every overall metric. The combination of the older un-filtered data and the
  honest group split breaks generalization to unseen mice.
- The minority class fails badly — **HT F1 0.387** (precision 0.308, recall 0.521): roughly two-thirds of
  HT predictions are false positives and nearly half of true HT pups are missed.
- WT is no longer carried: WT recall drops to 0.544 (574/1055 correct), so the model is closer to a coin
  flip than to a usable WT-vs-HT separator.
- Train 0.862 vs test 0.538 (0.32 gap) shows the model fits the training mice but does not transfer;
  TabPFN merges val into train, which inflates the train figure.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per strain).
- `logs/out.txt` — flags, split info, class balance, classification report, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
