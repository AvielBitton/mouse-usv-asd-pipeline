# D_sampler__transformer__dependent — Transformer · subject-dependent · D balanced-sampler experiment

> Transformer on per-syllable USV sequences with a balanced minibatch sampler, evaluated on the leaky (row-level) dependent split.

## Overview
- **Model:** Transformer (~73K params; chronological per-syllable sequence input, order preserved,
  scored at the session level — unlike the tabular base's 48 aggregated per-recording features).
- **Evaluation split:** subject-dependent — random **session-level** split (`group_split=false`), so the
  same mouse appears in train, val and test (the log warns of 61 shared train/test mice). This is the
  leaky, optimistic setting, matching the dependent base model.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction).
  408 sessions from 106 mice (HT 97 / WT 311); split 244 train / 82 val / 82 test sessions.
  Test = 82 sessions (WT 63 / HT 19 ≈ 23% positive).
- **What was adapted vs the base model:** lever **D** — a **balanced minibatch sampler** (the most
  reliable fix for collapse) replaces XGBoost. Class weighting is off (`pos_weight_beta=0.0`, `loss=bce`),
  so the sampler alone carries the imbalance handling. Trained 25 epochs (early-stopped, best val AUC 0.706).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.806 | 0.400 | — |
| Recall | 0.857 | 0.316 | — |
| F1 | 0.831 | 0.353 | weighted **0.720** |
| Accuracy | | | **0.732** (train 0.774) |

AUC 0.652 · balanced accuracy 0.586 · MCC 0.189 · PR-AUC 0.341.
Confusion matrix (rows = true, cols = pred): `[[WT→WT 54, WT→HT 9], [HT→WT 13, HT→HT 6]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.732 | 0.733 | −0.001 |
| Weighted F1 | 0.720 | 0.749 | −0.029 |
| WT F1 | 0.831 | 0.785 | +0.046 |
| HT F1 | 0.353 | 0.649 | −0.296 |
| HT recall | 0.316 | 0.940 | −0.624 |
| HT precision | 0.400 | 0.496 | −0.096 |

*NN are scored on session-level sequence data (82 test sessions here) vs the tabular base's recording-level
data (~2,465 rows), so this comparison is directional, not like-for-like.*

## Key insights
- **The sampler did not deliver minority-class performance here.** Overall accuracy (0.732) matches the
  base, but it is carried entirely by WT (recall 0.857, F1 0.831) — **HT recall collapses to 0.316**
  (−0.624 vs base) and HT F1 to 0.353. The model now catches only 6 of 19 ASD-model sessions.
- This is the **opposite of the classic "predict HT for everyone" collapse**: the sampler pushed the
  model toward the WT majority instead, so it misses two-thirds of positives. With no class weighting,
  random per-session sampling alone was not enough to hold the operating point on the minority class.
- Weak class separation overall — **AUC 0.652, balanced accuracy 0.586, MCC 0.189** — barely above
  chance on a leaky split that should be the *easy* setting. Val AUC peaked at 0.706 by epoch 10 then
  drifted, while val accuracy oscillated wildly (0.37–0.77), a sign of an unstable fit on only 244 train
  sessions.
- Even with mouse leakage in its favour, this Transformer is well below the tabular base on every
  minority-class metric; the 73K-param model is data-starved at session granularity.

## Recommendations
- Pair the balanced sampler with explicit class weighting (compare against the B/A/E levers) — sampler
  alone left the positive class under-served. Threshold tuning cannot rescue an AUC of 0.652.
- Treat session-level NN counts (82 test sessions, 19 HT) as too small for confident minority-class
  estimates; the dependent split's optimism is not even visible here.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — test confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.652). `plots/training_curves.png` — loss/accuracy/AUC over 25 epochs.
- `model/transformer_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- `results.json` — full metrics, config, split sizes. `logs/out.txt` — flags, split info, class balance, early stopping.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
