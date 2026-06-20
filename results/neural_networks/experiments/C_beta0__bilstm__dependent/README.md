# C_beta0__bilstm__dependent — BiLSTM · subject-dependent · experiment C (no class weighting)

> BiLSTM on chronological per-syllable sequences, trained with **no class weighting** and evaluated on a leaky (session-level) split.

## Overview
- **Model:** BiLSTM (~149K params; 2 layers, hidden 64, dropout 0.3) over the per-syllable acoustic
  sequence in recording order (`max_seq_len` 256), scored at **session level** — not the tabular
  recording level.
- **Evaluation split:** subject-dependent — random **session-level** split (`group_split=false`), so the
  same mouse leaks across train/val/test (log: 61 shared mice train/test). Optimistic by design.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice → train 244 / val 82 / test 82. Test = 82 sessions (WT 63 / HT 19, ~23% positive).
- **What was adapted vs the base model:** experiment **C — beta0** (`pos_weight_beta=0.0`, sampler none,
  plain BCE loss → `pos_weight=1.000`, i.e. **no class weighting**), plus the model family and input
  representation change (BiLSTM on sequences vs XGBoost on 48 aggregated features).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.797 | 0.385 | — |
| Recall | 0.873 | 0.263 | — |
| F1 | 0.833 | 0.313 | weighted **0.713** |
| Accuracy | | | **0.732** (train 0.865) |

AUC 0.662 · balanced accuracy 0.568 · macro F1 0.573 · MCC 0.157 · PR-AUC 0.391.
Early stopping at epoch 34/100 (best val AUC 0.665).

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.732 | 0.733 | −0.001 |
| Weighted F1 | 0.713 | 0.749 | −0.036 |
| WT F1 | 0.833 | 0.785 | +0.048 |
| HT F1 | 0.313 | 0.649 | −0.336 |
| HT recall | 0.263 | 0.940 | −0.677 |
| HT precision | 0.385 | 0.496 | −0.111 |

*Comparison is directional, not like-for-like: this NN is scored on 82 session-level sequences, while the tabular base is scored on ~2,465 recording-level rows.*

## Key insights
- Removing class weighting tips the model toward the WT majority: **HT recall collapses to 0.263**
  (−0.677 vs base) and HT F1 drops to 0.313, while accuracy survives (0.732) only because the test set is
  ~77% WT. This is a majority-leaning failure — it misses ~3 of every 4 ASD-model pups.
- HT precision is also weak (0.385): even the few positive calls it makes are wrong more often than not.
  Balanced accuracy 0.568 and MCC 0.157 confirm the model is barely above chance on the minority class.
- AUC 0.662 means the ranking signal exists but the **default 0.5 cut is mis-placed**; with no pos_weight
  the threshold sits far on the WT side, the opposite of the base model's HT-heavy operating point.
- Despite the leaky dependent split (which should be optimistic), this run still trails the tabular base
  on every minority-class metric — the no-weighting lever, not the split, is the binding constraint.

## Recommendations
- Re-introduce minority-class pressure: the **D balanced-sampler** config is the most reliable fix for
  this collapse; B (pos_weight_beta=0.5) and E (focal) are the next levers to try.
- If keeping beta0, move the decision threshold off 0.5 toward HT to recover recall (AUC 0.662 leaves
  headroom); evaluate against the leak-free independent split before trusting any number here.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.662). `plots/training_curves.png` — loss/acc/AUC vs epoch.
- `model/bilstm_best.pt` — best checkpoint (epoch 34). `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`; split info, data stats and early stopping in `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
