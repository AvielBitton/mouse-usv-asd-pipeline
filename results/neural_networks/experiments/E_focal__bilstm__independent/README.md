# E_focal__bilstm__independent — BiLSTM · subject-independent · experiment E (focal loss)

> BiLSTM with focal loss (no class weighting) on the baseline data, evaluated **leak-free** (split by mouse) — collapses toward WT.

## Overview
- **Model:** BiLSTM (~149K params; bidirectional LSTM over chronological per-syllable sequences, order
  preserved — unlike the tabular base, which uses 48 aggregated per-recording features). Scored at
  **session level**, not recording level.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent` /
  `--group-split`), so no mouse appears in two sets. The honest "generalize to unseen mice" setting,
  harder than the dependent base model (which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice; test = **90 held-out sessions** from 22 mice (WT 79% / HT 21%).
- **What was adapted vs the base model (lever E — focal loss):** loss is **focal** (`focal_gamma=2.0`)
  with **no** class weighting (`pos_weight_beta=0.0`, no sampler), intended to refocus learning on the
  hard minority class. Plus two levers change together: model family (BiLSTM instead of XGBoost) **and**
  evaluation moves from subject-dependent to subject-independent.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.786 | 0.167 | — |
| Recall | 0.930 | 0.053 | — |
| F1 | 0.852 | 0.080 | weighted **0.689** |
| Accuracy | | | **0.744** (train 0.819) |

Test AUC 0.640 · balanced accuracy 0.491 · MCC −0.029 · PR-AUC 0.284. Best val AUC 0.817; early stopped
at epoch 27. Confusion matrix (rows = true, cols = pred): `[[WT→WT 66, WT→HT 5], [HT→WT 18, HT→HT 1]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.744 | 0.733 | +0.011 |
| Weighted F1 | 0.689 | 0.749 | −0.060 |
| WT F1 | 0.852 | 0.785 | +0.067 |
| HT F1 | 0.080 | 0.649 | −0.569 |
| HT recall | 0.053 | 0.940 | −0.887 |
| HT precision | 0.167 | 0.496 | −0.329 |

*Comparison is directional, not like-for-like: this NN is scored on 90 session-level sequences, while
the tabular base is scored on ~2,465 recording-level rows.*

## Key insights
- **Degenerate collapse toward WT.** HT recall is **0.053** (1 of 19 HT sessions caught) and HT F1 is
  **0.080** — the model predicts WT for almost everyone. Balanced accuracy 0.491 and MCC −0.029 are at
  chance/slightly-negative, so the headline 0.744 accuracy is just the WT majority rate (79%).
- **Focal loss did not rescue the minority class.** With no class weighting and no sampler
  (`pos_weight_beta=0.0`), focal `gamma=2.0` on this tiny 238-session train set (HT 24%) left the model
  unable to learn HT — the exact failure focal loss was meant to prevent here.
- **The model can rank but not decide.** Best val AUC reached 0.817 and test AUC is 0.640, yet at the
  default 0.5 cut almost nothing crosses into HT — a threshold/calibration problem on top of the
  collapse. Train 0.819 vs test 0.744 also shows overfitting on so few sessions.
- Versus the base, accuracy and WT F1 nudge up only because the base trades WT recall for HT recall
  (HT recall 0.940); this run does the opposite and loses essentially all minority-class signal.

## Recommendations
- Prefer the class-balancing levers for this split: the **D balanced minibatch sampler** is the most
  reliable fix for collapse here; focal loss alone is not sufficient.
- If keeping focal loss, re-introduce class weighting (`pos_weight_beta>0`) or a sampler, and tune the
  decision threshold (AUC 0.64–0.82 suggests usable ranking the 0.5 cut throws away).

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.640). `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/bilstm_best.pt` — best-checkpoint weights. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`. `logs/out.txt` — flags, split info, class balance, early stopping.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
