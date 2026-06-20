# C_beta0__bilstm__independent — BiLSTM · subject-independent · experiment C (no class weighting)

> BiLSTM on chronological syllable sequences, evaluated **leak-free** (split by mouse), with class weighting switched **off** (`pos_weight_beta=0.0`).

## Overview
- **Model:** BiLSTM (2 layers, hidden 64, dropout 0.3; 148,953 params). Input is a chronological
  per-syllable sequence (order preserved, capped at `max_seq_len=256`), unlike the tabular base model's
  48 aggregated per-recording features. Scored at **session level**, not recording level.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`), so no
  mouse appears in two sets. This is the honest "generalize to unseen mice" setting (harder than the
  dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice → Train 238 / Val 80 / Test 90 sessions. Test = 22 held-out mice (WT 79% / HT 21%).
- **What was adapted vs the base model:** experiment **C (beta0)** turns off class weighting entirely
  (`pos_weight=1.000`, no sampler, plain BCE loss) — the opposite end from D's balanced sampler. Two
  axes also change together: model family (BiLSTM instead of XGBoost) **and** evaluation moves from
  subject-dependent to subject-independent.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.813 | 0.333 | — |
| Recall | 0.859 | 0.263 | — |
| F1 | 0.836 | 0.294 | weighted **0.721** |
| Accuracy | | | **0.733** (train 0.866) |

AUC-ROC 0.643 · PR-AUC 0.291 · balanced acc 0.561 · MCC 0.134 · macro F1 0.565.
Early stopping at epoch 32 (best val AUC 0.795); the test AUC (0.643) sits well below it.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.733 | 0.733 | +0.000 |
| Weighted F1 | 0.721 | 0.749 | −0.028 |
| WT F1 | 0.836 | 0.785 | +0.051 |
| HT F1 | 0.294 | 0.649 | −0.355 |
| HT recall | 0.263 | 0.940 | −0.677 |
| HT precision | 0.333 | 0.496 | −0.163 |

*Comparison is directional, not like-for-like: this NN is scored on 90 session-level sequences, whereas
the tabular base is scored on ~2,465 recording-level rows.*

## Key insights
- With class weighting **off**, the model swings hard toward the majority: **HT recall collapses to
  0.263** (−0.677 vs base) and HT F1 to 0.294, the mirror image of the base model's HT-heavy operating
  point. It now misses ~3 of every 4 ASD-model pups — the opposite-direction failure from degenerate
  HT-collapse, but just as damaging on the minority class.
- Headline accuracy (0.733) ties the base only because it is carried by the majority class: WT F1 0.836
  (+0.051) while HT contributes almost nothing. Balanced accuracy 0.561 and MCC 0.134 expose that the
  classifier is barely above chance on the two-class problem.
- Train 0.866 vs test 0.733 plus a test AUC (0.643) far below best val AUC (0.795) point to overfitting
  on the small independent split (only 238 train / 56 HT sessions) — val loss bottoms out at epoch 17
  (best val AUC) and climbs steadily thereafter while train accuracy keeps rising to ~0.94.

## Recommendations
- Removing class weighting is the wrong lever for this minority problem — prefer the balanced-sampler
  config (experiment **D**, the most reliable collapse fix) or focal loss (**E**); for the tiny
  independent split also try the regularized small net (**F**).
- Do not use this run for any HT-detection estimate: at the default 0.5 cut HT recall is 0.263.
  Threshold tuning toward `target_recall` could recover some, but PR-AUC 0.291 caps how much is
  achievable here.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC. `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/bilstm_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
