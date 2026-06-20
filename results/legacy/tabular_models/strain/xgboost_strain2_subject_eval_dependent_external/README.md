# xgboost_strain2_subject_eval_dependent_external — XGBoost (untuned) · subject-dependent · strain2 (external)

**Status:** archived — superseded by `results/tabular_models/xgboost_subject_eval_dependent_baseline`.

> Untuned XGBoost on the externally-validated strain2 (pure BALB/c, 2015/2018) cohort, evaluated leaky (random row-level split).

## Overview
- **Model:** XGBoost, untuned legacy recipe.
- **Evaluation split:** subject-dependent — random **row-level** split (`Strategy: random`), so the same
  mouse appears in train, val and test (the log warns of 49–50 shared mice across every pair). This is the
  optimistic, leaky setting, same family as the base model.
- **Dataset:** externally-validated set (`--external`) filtered to **strain2** (`--strain 2`, pure BALB/c
  classic 2015/2018 cohort): kept 5,009/13,625 rows, 50 mice. This predates the official Issue-#46 baseline
  filters and the April-2026 HET→WT correction.
- **Class encoding (note):** this legacy run flips the label convention — **class 0 = HET** (the ASD-model
  minority, 30.8% of test, support 309) and **class 1 = WT** (majority, 69.2%, support 693). Metrics below
  are reported by genotype, not class id.
- **What was adapted vs the base model:** restricted to the strain2 external cohort instead of the full
  baseline data; model family and the leaky dependent split are unchanged.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.918 | 0.569 | — |
| Recall | 0.710 | 0.858 | — |
| F1 | 0.801 | 0.684 | weighted **0.765** |
| Accuracy | | | **0.755** (train 0.811) |

Confusion matrix (rows = true, cols = pred; class 0 = HET, class 1 = WT): `[[HT→HT 265, HT→WT 44], [WT→HT 201, WT→WT 492]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.755 | 0.733 | +0.022 |
| Weighted F1 | 0.765 | 0.749 | +0.016 |
| WT F1 | 0.801 | 0.785 | +0.016 |
| HT F1 | 0.684 | 0.649 | +0.035 |
| HT recall | 0.858 | 0.940 | −0.082 |
| HT precision | 0.569 | 0.496 | +0.073 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- On the pure-BALB/c strain2 cohort the untuned model edges out the base on most aggregate metrics
  (accuracy +0.022, weighted F1 +0.016, HT F1 +0.035) — the cleaner single-strain data is easier to
  separate, but this is still a leaky dependent split so the figures are optimistic.
- The operating point is less aggressive on the minority class than the base: **HT recall drops to 0.858**
  (−0.082), so ~14% of ASD-model pups are missed, while **HT precision rises to 0.569** (+0.073) — fewer
  false positives among HT calls than the base's 0.496.
- Class separation is still weak: **HT precision ≈ 0.57** means roughly four in ten HT predictions are
  wrong; the 201 WT→HT false positives dominate the error budget.
- Train 0.811 vs test 0.755 (0.056 gap) is modest, but the 49–50 shared mice across splits mean the test
  score reflects memorized mice, not generalization to new animals.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices (single-strain run, no
  per-strain split). `plots/AUC_error.png` — training/AUC curve.
- `plots/feature_importances_0.png`, `plots/feature_importance_1.png` — feature importances.
- `model/xgboost_model.pkl` — fitted model. `logs/out.txt` — flags, split info, class balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
