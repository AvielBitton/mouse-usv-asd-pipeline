# tabpfn_subject_eval_dependent_baseline — TabPFN · subject-dependent

> TabPFN on the official baseline data, evaluated with a **row-level random split** (mice leak across train/test — optimistic).

## Overview
- **Model:** TabPFN (prior-data-fitted transformer; no hyperparameter tuning; validation set is merged
  into train, so there is no early-stopping/learning curve).
- **Evaluation split:** subject-dependent — train/val/test split randomly at the **row/session level**, so
  the same mouse appears in multiple sets (train/val 106, train/test 105, val/test 105 shared mice). This
  is the optimistic, leakage-prone setting — the same family as the base model.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 2,465 recordings (WT 73.8% / HT 26.2%); train 7,393 + val 2,465 merged into 9,858 train rows.
- **What was adapted vs the base model:** one lever changes — model family (TabPFN instead of XGBoost) —
  while the dependent evaluation split is held the same, so this isolates the model effect.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.962 | 0.550 | — |
| Recall | 0.733 | 0.918 | — |
| F1 | 0.832 | 0.688 | weighted **0.794** |
| Accuracy | | | **0.781** (train 0.888) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 1332, WT→HT 486], [HT→WT 53, HT→HT 594]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.781 | 0.733 | +0.048 |
| Weighted F1 | 0.794 | 0.749 | +0.045 |
| WT F1 | 0.832 | 0.785 | +0.047 |
| HT F1 | 0.688 | 0.649 | +0.039 |
| HT recall | 0.918 | 0.940 | −0.022 |
| HT precision | 0.550 | 0.496 | +0.054 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- On the same leaky dependent split, **TabPFN beats the XGBoost base on every aggregate**: accuracy
  0.781 (+0.048), weighted F1 0.794 (+0.045), and both per-class F1s improve — a clean model-only win.
- The biggest gain is **HT precision +0.054** (0.550 vs 0.496): false positives drop, so HT F1 rises to
  0.688 (+0.039) while HT recall stays near-saturated at 0.918 (−0.022, still catching ~92% of ASD pups).
- Class separation is still the limit — **HT precision is only 0.550**, so nearly half of HT calls remain
  false positives (486 of WT mislabeled HT in the confusion matrix).
- Train 0.888 vs test 0.781 (0.11 gap) plus the shared-mouse leakage means these numbers are optimistic;
  the leak-free read lives in `../tabpfn_subject_eval_independent_baseline/` (~0.73 accuracy there).

## Recommendations
- Use this run only as an upper-bound, leaky estimate; quote the subject-independent TabPFN run for any
  honest "new-mouse" claim.
- HT precision ≈ 0.55 at the default 0.5 cut — the threshold runs (`../threshold/`,
  `../threshold_objectives/`) can trade some of the spare HT recall for cleaner positive calls.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per strain).
- `model/tabpfn_model.pkl` — fitted TabPFN. `logs/out.txt` — flags, split info, class balance.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
