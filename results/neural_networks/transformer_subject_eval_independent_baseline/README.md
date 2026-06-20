# transformer_subject_eval_independent_baseline — Transformer · subject-independent

> Transformer on the official baseline sequences, evaluated **leak-free** (split grouped by mouse).

## Overview
- **Model:** Transformer encoder over per-syllable sequences (72,537 params). Input is the chronological
  per-syllable sequence (order preserved, `MAX_SEQ_LEN=256`), not the 48 aggregated per-recording
  features the tabular base model uses. Scored at **session level**.
- **Evaluation split:** subject-independent — group-aware split **by mouse** (`--independent`), so no
  mouse appears in two sets. This is the honest "generalize to unseen mice" setting (harder than the
  dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions (HT=97 / WT=311) from
  106 mice. Test = 90 sessions from 22 held-out mice (WT 79% / HT 21%);
  train 238 / val 80.
- **Training:** `pos_weight=3.250` (control-style class weighting), early-stopped at epoch 29 on best
  val AUC 0.810. Test AUC drops to 0.675 — the validation operating point did not transfer.

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.895 | 0.288 | — |
| Recall | 0.479 | 0.789 | — |
| F1 | 0.624 | 0.423 | weighted **0.581** |
| Accuracy | | | **0.544** (train 0.605) |

Confusion matrix (rows = true, cols = pred): `[[WT→WT 34, WT→HT 37], [HT→WT 4, HT→HT 15]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.544 | 0.733 | −0.189 |
| Weighted F1 | 0.581 | 0.749 | −0.168 |
| WT F1 | 0.624 | 0.785 | −0.161 |
| HT F1 | 0.423 | 0.649 | −0.226 |
| HT recall | 0.789 | 0.940 | −0.151 |
| HT precision | 0.288 | 0.496 | −0.208 |

*Directional only, not like-for-like: this NN is scored on 90 session-level sequences, whereas the
tabular base model is scored on ~2,465 recording-level rows.*

## Key insights
- **Minority-leaning collapse.** The model tips toward HT: HT recall 0.789 but WT recall only 0.479, so
  it mislabels 37 of 71 WT sessions as HT. This is the milder side of the common NN collapse — driven by
  the `pos_weight=3.250` weighting — and it sinks overall accuracy to 0.544.
- **The operating point did not transfer.** Best val AUC 0.810 vs test AUC 0.675, and at the
  best-AUC checkpoint the 0.5 threshold yields val acc ~0.70 but test acc 0.544 — the tiny
  independent split (22 test mice, 19 HT) makes the chosen cut unstable.
- **HT precision ≈ 0.29** (−0.208 vs base): nearly 3 of every 4 HT calls are false positives, the worst
  HT precision among the baseline runs; HT F1 0.423.
- Train acc 0.605 is barely above test 0.544 — this is underfitting, not overfitting; the Transformer
  never found a clean WT/HT boundary on these sequences.

## Recommendations
- Prefer the balanced-sampler config (`D` prefix) over raw `pos_weight` weighting — it is the most
  reliable fix for this minority-leaning collapse on the independent split.
- Do not deploy this 0.5-threshold operating point; if this architecture is pursued, retune the cut on a
  validation set that better matches the test distribution (see `../threshold/`,
  `../threshold_objectives/`).

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — test ROC (AUC 0.675). `plots/training_curves.png` — loss/acc/AUC per epoch.
- `model/transformer_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json` + `logs/out.txt` (flags, split info, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
