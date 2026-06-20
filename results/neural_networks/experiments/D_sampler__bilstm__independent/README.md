# D_sampler__bilstm__independent — BiLSTM · subject-independent · D balanced-sampler experiment

> BiLSTM with a balanced minibatch sampler on the leak-free (by-mouse) split — the collapse fix that here over-corrects toward the HT minority.

## Overview
- **Model:** BiLSTM (~149K params; 2 layers, hidden 64, dropout 0.3). Input is a chronological
  per-syllable sequence (order preserved), scored at the **session** level — unlike the tabular base
  model's 48 aggregated per-recording features.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent` /
  group-aware), so no mouse appears in two sets. This is the honest "generalize to unseen mice"
  setting (harder than the dependent base model, which splits rows randomly and lets mice leak).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice → Train 238 (63 mice) / Val 80 (21 mice) / **Test 90 sessions (22 mice, HT 21% / WT 79%)**.
- **What was adapted vs the base model (lever D):** add a **balanced minibatch sampler** to fight
  degenerate collapse, with class weighting turned off (`pos_weight_beta=0.0`, `loss=bce`); plus the
  two structural changes shared by all NN runs — model family (BiLSTM instead of XGBoost) **and**
  evaluation moving from subject-dependent to subject-independent.
- Trained 17/100 epochs (early stop, best val AUC 0.865).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 1.000 | 0.311 | — |
| Recall | 0.408 | 1.000 | — |
| F1 | 0.580 | 0.475 | weighted **0.558** |
| Accuracy | | | **0.533** (train 0.681) |

Other test metrics: AUC-ROC 0.767 · balanced accuracy 0.704 · PR-AUC 0.354 · MCC 0.357 · macro-F1 0.528.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.533 | 0.733 | −0.200 |
| Weighted F1 | 0.558 | 0.749 | −0.191 |
| WT F1 | 0.580 | 0.785 | −0.205 |
| HT F1 | 0.475 | 0.649 | −0.174 |
| HT recall | 1.000 | 0.940 | +0.060 |
| HT precision | 0.311 | 0.496 | −0.185 |

*Directional comparison only: this NN is scored on **90 session-level sequences**, while the tabular base is scored on ~2,465 recording-level rows — not a like-for-like split or unit.*

## Key insights
- **Degenerate collapse toward the minority.** The sampler over-corrects: **HT recall = 1.000 with WT
  recall only 0.408** — the model calls HT for the majority of sessions. HT precision is just 0.311
  (~7 in 10 HT calls are false positives), so the +0.060 HT-recall "win" vs base is hollow.
- Accuracy (0.533) and weighted F1 (0.558) sit ~0.19–0.20 below the dependent base, the worst possible
  side of the collapse — every WT cost is paid to chase HT recall.
- Ranking is healthier than the operating point: **AUC-ROC 0.767 / balanced accuracy 0.704 / MCC 0.357**
  show the model does separate the classes; the default 0.5 threshold is simply mis-placed far into the
  HT-favoring region.
- WT precision pinned at 1.000 with recall 0.408 is the signature of this regime — every WT prediction
  is correct, but only 4 in 10 WT sessions are recovered.

## Recommendations
- Do not ship the 0.5 cut. With AUC 0.767 there is room to recover via thresholding — pick a cut that
  trades the saturated HT recall back for WT recall before reading any per-class metric.
- The balanced sampler alone over-shoots on this tiny independent split; compare against the
  regularized-small variant (lever F) and the focal/beta variants, and prefer the CV config (lever H)
  for a stable estimate before trusting any single 90-session test number.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — ROC (AUC 0.767). `plots/training_curves.png` — loss/acc/AUC over 17 epochs.
- `model/bilstm_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
