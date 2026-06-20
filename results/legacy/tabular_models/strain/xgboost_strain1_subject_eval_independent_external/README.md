# xgboost_strain1_subject_eval_independent_external — XGBoost · subject-independent · strain1 (external)

**Status:** archived — superseded by the current `--baseline` runs under `results/`.

> Untuned legacy XGBoost on the strain1 external cohort, evaluated **leak-free** (split grouped by mouse).

## Overview
- **Model:** XGBoost, untuned legacy recipe (no 200-trial search applied).
- **Evaluation split:** subject-independent — group-aware train/val/test split **by mouse**
  (`--independent`), so no mouse appears in two sets. This is the honest "generalize to unseen mice"
  setting (harder than the dependent base model, which splits rows randomly and lets mice leak across
  train/test).
- **Dataset:** legacy **external** data (`outputs/external/aggregated/all_data_external_main.csv`),
  **not** the official Issue-#46 baseline. Strain filter kept 8,616 / 13,625 rows
  (`pup_strain == 1`, the 2022–2024 mixed BALB/C+C57 cohort), 70 mice. `pup_gen` balance WT 6,624 /
  HT 1,992.
- **Label encoding (legacy/external):** class 0 = HT/HET (ASD-model, minority positive),
  class 1 = WT — the **opposite** of the baseline convention. Test = 1,750 recordings from 14 held-out
  mice (WT 82.3% / HT 17.7%).
- **What was adapted vs the base model:** three levers change together — external dataset (not baseline),
  strain1-only cohort, **and** evaluation moves from subject-dependent to subject-independent.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.994 | 0.359 | — |
| Recall | 0.623 | 0.984 | — |
| F1 | 0.766 | 0.526 | weighted **0.724** |
| Accuracy | | | **0.687** (train 0.813) |

Confusion matrix (rows = true, cols = pred; legacy order HT then WT):
`[[HT→HT 304, HT→WT 5], [WT→HT 543, WT→WT 898]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.687 | 0.733 | −0.046 |
| Weighted F1 | 0.724 | 0.749 | −0.025 |
| WT F1 | 0.766 | 0.785 | −0.019 |
| HT F1 | 0.526 | 0.649 | −0.123 |
| HT recall | 0.984 | 0.940 | +0.044 |
| HT precision | 0.359 | 0.496 | −0.137 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- The model **leans degenerate toward the minority class**: HT recall 0.984 (only 5 of 309 HT pups
  missed) but WT recall collapses to 0.623 — it predicts HT for far too many WT pups
  (543 WT→HT false positives), which is why HT precision is just 0.359.
- The harder leak-free split plus the strain1-only external cohort drops overall accuracy to 0.687
  (−0.046 vs base) and weighted F1 to 0.724 (−0.025); the test set is also heavily WT-skewed
  (82.3%), so high HT recall comes cheap.
- Class separation is poor — **HT F1 0.526** (−0.123 vs base), driven entirely by precision; about two
  of every three HT calls are false alarms.
- Train 0.813 vs test 0.687 (0.13 gap) reflects the cost of unseen mice on this untuned recipe.

## Recommendations
- Do not use this archived external run for reporting; prefer the current `--baseline` XGBoost runs
  under `results/tabular_models/`, which apply the Issue-#46 filters and the HET→WT label correction.
- If revisited, the operating point needs rebalancing (threshold tuning / regularization) — at the
  default 0.5 cut it sacrifices nearly 40% of WT pups to chase HT recall.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices.
- `plots/AUC_error.png` — train/val AUC error curve.
- `plots/feature_importances_0.png`, `plots/feature_importance_1.png` — feature importance.
- `model/xgboost_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, split info, class balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
