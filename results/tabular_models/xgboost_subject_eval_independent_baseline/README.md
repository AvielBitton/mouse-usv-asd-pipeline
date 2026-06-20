# xgboost_subject_eval_independent_baseline — XGBoost · subject-independent

> Untuned legacy XGBoost on the official baseline data, evaluated **leak-free** (split grouped by mouse).

## Overview
- **Model:** XGBoost (untuned legacy recipe; `scale_pos_weight=3.07` to weight the HT minority).
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`), so no
  mouse appears in two sets. This is the honest "generalize to unseen mice" setting (harder than the
  dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  Train 7,866 / Val 2,318 / Test 2,139 recordings across 63 / 21 / 22 mice respectively.
  Test = 2,139 recordings from 22 held-out mice (WT 72.9% / HT 27.1%).
- **What was adapted vs the base model:** only the evaluation moves from subject-dependent to
  subject-independent; the model family (XGBoost) is unchanged, isolating the cost of the leak-free split.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.841 | 0.452 | — |
| Recall | 0.713 | 0.637 | — |
| F1 | 0.772 | 0.529 | weighted **0.706** |
| Accuracy | | | **0.693** (train 0.806) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 1113, WT→HT 447], [HT→WT 210, HT→HT 369]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.693 | 0.733 | −0.040 |
| Weighted F1 | 0.706 | 0.749 | −0.043 |
| WT F1 | 0.772 | 0.785 | −0.013 |
| HT F1 | 0.529 | 0.649 | −0.120 |
| HT recall | 0.637 | 0.940 | −0.303 |
| HT precision | 0.452 | 0.496 | −0.044 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- The leak-free split exacts the expected toll: every headline metric drops, with overall accuracy
  −0.040 (0.693) and weighted F1 −0.043 (0.706) vs the optimistic dependent base.
- The minority class collapses hardest — **HT recall falls to 0.637** (−0.303) and **HT F1 to 0.529**
  (−0.120). The dependent base caught 94% of ASD-model pups; on unseen mice this run misses ~1 in 3.
- Class separation stays weak: **HT precision 0.452** (−0.044) means more than half of HT predictions
  are false positives. The model no longer over-predicts HT (447 WT→HT) the way the recall-heavy base did.
- Train 0.806 vs test 0.693 (0.11 gap) reflects honest generalization to new mice, not the inflated
  dependent-split fit — but the untuned recipe still leaves the HT class largely unresolved.

## Recommendations
- Use this independent run, not the dependent base, for any "new-mouse" performance estimate.
- HT recall is poor at the default 0.5 cut — see the threshold runs (`../threshold/`,
  `../threshold_objectives/`) to recover a controlled operating point; and compare against
  `xgboost_tuned_independent_subject_eval_independent_baseline`, whose hyperparameters were tuned
  specifically for this leak-free split.

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png`, `plots/confusionmatrix_strain1.png`,
  `plots/confusionmatrix_strain2.png` — confusion matrices (overall + per strain).
- `plots/feature_importances_0.png`, `plots/feature_importance_1.png` — feature importance.
  `plots/AUC_error.png` — AUC / error learning curve.
- `model/xgboost_model.pkl` — fitted XGBoost. `logs/out.txt` — flags, split info, class balance.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
