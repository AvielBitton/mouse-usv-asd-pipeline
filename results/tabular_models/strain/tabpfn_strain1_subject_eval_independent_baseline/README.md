# tabpfn_strain1_subject_eval_independent_baseline — TabPFN · subject-independent · strain1

> TabPFN on the strain1 cohort (2022–2024, mixed BALB/C+C57), evaluated **leak-free** (split grouped by mouse).

## Overview
- **Model:** TabPFN (prior-data-fitted transformer; no hyperparameter tuning; validation set is merged
  into train, so there is no early-stopping/learning curve).
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`,
  group-aware by `mouse_idx`), so no mouse appears in two sets. This is the honest "generalize to unseen
  mice" setting (harder than the dependent base model, which splits rows randomly and lets mice leak
  across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction), restricted to
  **strain1** (2022–2024, mixed BALB/C+C57): kept 7,572/12,323 rows (`pup_strain == 1`) from 59 mice.
  Test = 1,693 recordings from 12 held-out mice (WT 83.5% / HT 16.5%).
- **What was adapted vs the base model:** three levers change together — model family (TabPFN instead of
  XGBoost), evaluation moves from subject-dependent to subject-independent, **and** the data is narrowed
  to the strain1 cohort.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.984 | 0.629 | — |
| Recall | 0.892 | 0.925 | — |
| F1 | 0.935 | 0.749 | weighted **0.905** |
| Accuracy | | | **0.897** (train 0.859) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 1260, WT→HT 153], [HT→WT 21, HT→HT 259]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.897 | 0.733 | +0.164 |
| Weighted F1 | 0.905 | 0.749 | +0.156 |
| WT F1 | 0.935 | 0.785 | +0.150 |
| HT F1 | 0.749 | 0.649 | +0.100 |
| HT recall | 0.925 | 0.940 | −0.015 |
| HT precision | 0.629 | 0.496 | +0.133 |

*Ignore the `baseline:` column inside `comparison_vs_baseline.txt` — it is a legacy 0.829 reference, not our base model.*

## Key insights
- The strain1 cohort is the strongest TabPFN result yet: **accuracy 0.897 and weighted F1 0.905**, both
  ~0.16 above the dependent base model — and this is the *honest* leak-free split, which usually costs
  10–15 pts rather than gaining them. The narrower, more recent cohort is clearly easier to separate.
- Minority-class quality jumps: **HT precision 0.629 (+0.133)** with HT recall held at 0.925 (−0.015),
  lifting HT F1 to 0.749 (+0.100). Far fewer false positives than the full-data TabPFN (where HT
  precision sat at ~0.50) while still catching ~93% of ASD-model pups.
- WT is almost airtight — precision 0.984, recall 0.892 — so the 153 WT→HT misses dominate the error
  budget; only 21 HT pups are missed.
- Train 0.859 sits **below** test 0.897, an unusual inverted gap: the test cohort (16.5% HT) is more
  WT-skewed than train (22.2% HT), and TabPFN merges val into train, so the train figure is not a clean
  fit estimate.

## Recommendations
- Treat this strain1 score as cohort-specific, not a general headline: the gain partly reflects an
  easier, more recent, lower-HT-prevalence cohort (16.5% vs ~24% overall). Cross-check against
  strain2 before claiming broad generalization.
- HT precision (0.63) still leaves ~1 in 3 positive calls as false alarms; if a higher-purity operating
  point is needed, see the threshold runs (`../../threshold/`, `../../threshold_objectives/`).

## Artifacts
- `plots/conf_matrix.png`, `plots/confusionmatrix.png` — confusion matrices (single-strain run, no
  per-strain split).
- `model/tabpfn_model.pkl` — fitted TabPFN. `logs/out.txt` — flags, split info, class balance.
- Metrics source: `comparison_vs_baseline.txt` (run column only) + `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `comparison_vs_baseline.txt` + `logs/out.txt` · summary auto-generated*
