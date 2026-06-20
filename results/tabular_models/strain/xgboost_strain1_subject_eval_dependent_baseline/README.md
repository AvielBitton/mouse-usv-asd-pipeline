# xgboost_strain1_subject_eval_dependent_baseline — XGBoost · subject-dependent · strain1

> Untuned XGBoost on the strain1 cohort (2022–2024, mixed BALB/C+C57), evaluated on the leaky dependent split.

## Overview
- **Model:** XGBoost (untuned legacy recipe; `scale_pos_weight=3.53` to up-weight the HT minority).
- **Evaluation split:** subject-dependent — random row-level split, so the same mouse appears in train,
  val and test (the log warns: 59/59/59 shared mice). This leaks and reads optimistically vs an
  independent split.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction), restricted to
  **strain1** (`--strain 1`, 2022–2024, mixed BALB/C+C57): kept 7,572/12,323 rows over 59 mice
  (WT 5,891 / HT 1,681). Train 4,542 / Val 1,515 / Test 1,515 rows; test is WT 76.4% / HT 23.6%.
- **What was adapted vs the base model:** one lever — the data is restricted to the strain1 cohort;
  model family and dependent split match the base.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.967 | 0.512 | — |
| Recall | 0.730 | 0.919 | — |
| F1 | 0.832 | 0.657 | weighted **0.791** |
| Accuracy | | | **0.774** (train 0.811) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 845, WT→HT 313], [HT→WT 29, HT→HT 328]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.774 | 0.733 | +0.041 |
| Weighted F1 | 0.791 | 0.749 | +0.042 |
| WT F1 | 0.832 | 0.785 | +0.047 |
| HT F1 | 0.657 | 0.649 | +0.008 |
| HT recall | 0.919 | 0.940 | −0.021 |
| HT precision | 0.512 | 0.496 | +0.016 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- Restricting to the **strain1 cohort lifts every headline metric** vs the full-data base: accuracy
  +0.041 (0.774), weighted F1 +0.042 (0.791), WT F1 +0.047. A single more-homogeneous cohort is easier
  to separate than the pooled dataset.
- The minority class barely moves: **HT F1 0.657 (+0.008)** — HT precision nudges up to 0.512 (+0.016)
  while HT recall dips to 0.919 (−0.021). Both gains land entirely on the WT side.
- Class separation is still weak — **HT precision ≈ 0.51**, so about half of HT predictions are false
  positives (313 WT mislabeled HT vs 328 true HT). The model keeps the base's aggressive high-recall
  operating point on the minority.
- Train 0.811 vs test 0.774 (0.04 gap) is modest, but the dependent split leaks (mice shared across all
  three sets), so this is an optimistic read — expect ~10–15 pts lower on a leak-free strain1 split.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices (single-strain run, no
  per-strain CM split).
- `plots/feature_importances_0.png`, `plots/feature_importance_1.png` — feature importances.
  `plots/AUC_error.png` — training/eval curve.
- `model/xgboost_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, strain filter, split info, class
  balance, confusion matrix.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
