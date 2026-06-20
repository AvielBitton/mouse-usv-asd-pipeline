# tabpfn_subject_eval_independent_baseline — TabPFN · subject-independent

> TabPFN on the official baseline data, evaluated **leak-free** (split grouped by mouse).

## Overview
- **Model:** TabPFN (prior-data-fitted transformer; no hyperparameter tuning; validation set is merged
  into train, so there is no early-stopping/learning curve).
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`), so no
  mouse appears in two sets. This is the honest "generalize to unseen mice" setting (harder than the
  dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Test = 2,139 recordings from 22 held-out mice (WT 72.9% / HT 27.1%).
- **What was adapted vs the base model:** two levers change together — model family (TabPFN instead of
  XGBoost) **and** evaluation moves from subject-dependent to subject-independent.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.898 | 0.499 | — |
| Recall | 0.709 | 0.782 | — |
| F1 | 0.792 | 0.610 | weighted **0.743** |
| Accuracy | | | **0.729** (train 0.911) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 1106, WT→HT 454], [HT→WT 126, HT→HT 453]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.729 | 0.733 | −0.004 |
| Weighted F1 | 0.743 | 0.749 | −0.006 |
| WT F1 | 0.792 | 0.785 | +0.007 |
| HT F1 | 0.610 | 0.649 | −0.039 |
| HT recall | 0.782 | 0.940 | −0.158 |
| HT precision | 0.499 | 0.496 | +0.003 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- Despite the **harder leak-free split**, overall accuracy (0.729) and weighted F1 (0.743) land within
  ~0.005 of the dependent base model — TabPFN largely absorbs the difficulty that usually costs
  10–15 pts when moving dependent → independent.
- The operating point shifts conservative on the minority class: **HT recall falls to 0.782** (−0.158
  vs base) while WT recall rises to 0.709. The model now misses ~1 in 5 ASD-model pups.
- Class separation is still weak — **HT precision ≈ 0.50** (about half of HT predictions are false
  positives); HT F1 0.610.
- Train 0.911 vs test 0.729 (0.18 gap) reflects the cost of unseen mice; TabPFN merges val into train,
  which inflates the train figure.

## Recommendations
- HT recall is low at the default 0.5 cut — see the threshold runs (`../threshold/`,
  `../threshold_objectives/`); for independent splits `target_recall` (~0.80) keeps a controlled
  operating point.
- Use this independent run, not the dependent base, for any "new-mouse" performance estimate; but note
  HT precision remains ~0.50, so positive calls need confirmation.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per strain).
- `model/tabpfn_model.pkl` — fitted TabPFN. `logs/out.txt` — flags, split info, class balance.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
