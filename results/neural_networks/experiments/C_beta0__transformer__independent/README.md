# C_beta0__transformer__independent — Transformer · subject-independent · experiment C (no class weighting)

> Transformer on per-syllable sequences, leak-free split, with class weighting turned **off** — collapses to predicting WT for every session.

## Overview
- **Model:** Transformer (~73K params; 2 layers, d_model 64, dropout 0.3). Input is the chronological
  per-syllable sequence (order preserved, `MAX_SEQ_LEN=256`), not the 48 aggregated tabular features.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent`,
  group-aware), so no mouse appears in two sets. Honest "generalize to unseen mice" setting (harder than
  the dependent base model, which splits rows randomly and leaks mice across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions / 106
  mice → train 238 / val 80 / test 90 sessions. Test = 22 held-out mice (WT 79% / HT 21%).
- **What was adapted vs the base model:** experiment **C = beta0** — `pos_weight_beta=0.0`, i.e. **no
  class weighting** (`pos_weight=1.000`), plain BCE, no sampler/focal/augmentation. Scored at session
  level, not recording level.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.789 | 0.000 | — |
| Recall | 1.000 | 0.000 | — |
| F1 | 0.882 | 0.000 | weighted **0.696** |
| Accuracy | | | **0.789** (train 0.765) |

AUC 0.710 · balanced accuracy 0.500 · MCC 0.000 · macro F1 0.441 · best val AUC 0.781 · early stop epoch 22/100.

**Degenerate collapse:** the model predicts **WT for all 90 test sessions** — HT recall 0.000, HT F1
0.000, WT recall 1.000. Accuracy 0.789 is exactly the WT prior (71/90), so the classifier learns nothing
discriminative at the 0.5 cut despite a non-trivial AUC of 0.710.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.789 | 0.733 | +0.056 |
| Weighted F1 | 0.696 | 0.749 | −0.053 |
| WT F1 | 0.882 | 0.785 | +0.097 |
| HT F1 | 0.000 | 0.649 | −0.649 |
| HT recall | 0.000 | 0.940 | −0.940 |
| HT precision | 0.000 | 0.496 | −0.496 |

*Directional only: this NN is scored on session-level sequence data (90 test sessions) while the tabular
base is scored on recording-level data (~2,465 rows) — not a like-for-like comparison.*

## Key insights
- **Collapse, not generalization.** The +0.056 accuracy gain over base is an artifact of always
  guessing the majority class — every HT metric is 0.000. The model identifies zero ASD-model pups.
- **Removing class weighting causes it.** With `pos_weight=1.000` (beta0) and a 24% minority, plain BCE
  has no pressure to predict HT; train accuracy (0.765) also sits near the train WT prior, so collapse
  starts in training, not just at the decision threshold.
- **Signal exists but is unused.** Val AUC peaked at 0.781 and test AUC is 0.710 — ranking is better than
  chance, yet the fixed 0.5 cut maps all probabilities below it. A threshold sweep or class rebalancing
  would be required to recover any HT.

## Recommendations
- Use a class-imbalance lever instead of beta0: the **D balanced sampler** is the most reliable fix for
  this collapse; B (beta0.5) or E (focal) are alternatives.
- If keeping this run, do not score at the default 0.5 cut — calibrate a threshold against the 0.710 AUC;
  but the absent HT signal at this operating point makes this run unfit as a "new-mouse" estimate.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (all sessions → WT).
- `plots/roc_curve.png` — ROC (AUC 0.710). `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/transformer_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
