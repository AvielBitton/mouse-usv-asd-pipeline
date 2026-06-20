# D_sampler__transformer__independent — Transformer · subject-independent · D balanced-sampler experiment

> Transformer on per-syllable sequences, evaluated **leak-free** with a balanced minibatch sampler — and it still collapsed onto HT.

## Overview
- **Model:** Transformer (~73K params; chronological per-syllable sequence input, `max_seq_len=256`,
  `d_model=64`, 2 layers, dropout 0.3). Scored at **session level**, not recording level.
- **Evaluation split:** subject-independent — train/val/test split **by mouse** (`--independent` /
  `--group-split`), so no mouse appears in two sets. Honest "generalize to unseen mice" setting (harder
  than the dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions / 106
  mice → train 238 (63 mice, 24% HT) · val 80 (21 mice) · **test 90 sessions** (22 mice, HT 21% / WT 79%).
- **What was adapted vs the base model (lever D):** balanced minibatch **sampler** (`sampler=balanced`)
  with class weighting off (`pos_weight_beta=0.0`, `loss=bce`) — the usual most-reliable fix for
  collapse — on top of the model-family change (Transformer instead of XGBoost) and the dependent →
  subject-independent split change.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 1.000 | 0.213 | — |
| Recall | 0.014 | 1.000 | — |
| F1 | 0.028 | 0.352 | weighted **0.096** |
| Accuracy | | | **0.222** (train 0.269) |

AUC-ROC 0.749 · PR-AUC 0.558 · balanced acc 0.507 · MCC 0.055 · best val AUC 0.824 · early-stopped at
epoch 19/100. Confusion matrix (rows = true, cols = pred): `[[WT→WT 1, WT→HT 70], [HT→WT 0, HT→HT 19]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.222 | 0.733 | −0.511 |
| Weighted F1 | 0.096 | 0.749 | −0.653 |
| WT F1 | 0.028 | 0.785 | −0.757 |
| HT F1 | 0.352 | 0.649 | −0.297 |
| HT recall | 1.000 | 0.940 | +0.060 |
| HT precision | 0.213 | 0.496 | −0.283 |

*Directional only, not like-for-like: this NN is scored on 90 session-level sequences vs the tabular
base's ~2,465 recording-level rows.*

## Key insights
- **Degenerate collapse.** The model predicts **HT for nearly every session** — HT recall 1.000, WT
  recall 0.014 (1 of 71 WT sessions correct). Accuracy 0.222 just tracks the HT base rate. The balanced
  sampler (lever D) did **not** prevent collapse here; it tipped the model the opposite way from the
  WT-everyone failure.
- **Ranking ≠ thresholding.** Test AUC-ROC is a respectable 0.749 (best val AUC 0.824), so the network
  learned *some* separation, but the default 0.5 cut sits entirely on one side — MCC 0.055 and balanced
  accuracy 0.507 confirm the operating point is no better than chance.
- **Training never settled.** Val accuracy swung wildly epoch-to-epoch (0.31 → 0.78) while AUC peaked at
  0.824 by epoch 4; early stopping on AUC locked in a checkpoint whose decision boundary is degenerate.
  Train accuracy 0.269 (also below the WT majority rate) signals the sampler is over-balancing the
  minority class.
- The +0.060 HT-recall "win" over base is meaningless — it is the artifact of calling everything HT,
  paid for with WT F1 collapsing to 0.028.

## Recommendations
- Do **not** use this checkpoint. AUC 0.749 shows signal exists, so re-threshold off the probability
  ranking — a recall-targeted cut (e.g. `target_recall` ~0.80) tuned on the validation logits — rather
  than trusting the degenerate 0.5 cut.
- The balanced sampler alone over-corrects on this tiny independent split (238 train sessions); compare
  against the regularized lever-F run and the CV lever-H run (`H_cv_Dsampler__*`) before drawing any
  conclusion on the sampler fix for the Transformer.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — ROC (AUC 0.749). `plots/training_curves.png` — loss/acc/AUC over 19 epochs.
- `model/transformer_best.pt` — best checkpoint (val AUC). `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
