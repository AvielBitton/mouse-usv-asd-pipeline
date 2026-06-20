# C_beta0__transformer__dependent — Transformer · subject-dependent · experiment C (no class weighting)

> Sequence Transformer on the baseline data, subject-dependent split, with class weighting turned **off** (`pos_weight_beta=0.0`).

## Overview
- **Model:** Transformer (~73K params; 2 layers, `d_model`=64, dropout 0.3) over the chronological
  per-syllable sequence (order preserved, `max_seq_len`=256), scored at **session level** — not the 48
  aggregated per-recording features the tabular base uses.
- **Evaluation split:** subject-dependent — random session-level split (`group_split=false`), so the same
  mouse can land in train and test (leakage, optimistic). Log confirms mouse overlap: 61 shared mice
  train/test, 56 train/val.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice (HT 97 / WT 311); median sequence length 236 syllables (P95 704).
- **What was adapted vs the base model (lever C):** class weighting is **disabled** — `pos_weight_beta=0.0`
  gives `pos_weight=1.0` with `loss=bce`, no sampler. The minority HT class gets no upweighting at all.
- **Train/val/test:** 244 / 82 / 82 sessions; HT share ~24% in each. Early-stopped at epoch 48 (best val
  AUC 0.727).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.781 | 0.333 | — |
| Recall | 0.905 | 0.158 | — |
| F1 | 0.838 | 0.214 | weighted **0.694** |
| Accuracy | | | **0.732** (train 0.848) |

AUC-ROC 0.702 · PR-AUC 0.385 · balanced accuracy 0.531 · MCC 0.085 (82 test sessions).
Confusion matrix (rows = true, cols = pred): `[[WT→WT 57, WT→HT 6], [HT→WT 16, HT→HT 3]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.732 | 0.733 | −0.001 |
| Weighted F1 | 0.694 | 0.749 | −0.055 |
| WT F1 | 0.838 | 0.785 | +0.053 |
| HT F1 | 0.214 | 0.649 | −0.435 |
| HT recall | 0.158 | 0.940 | −0.782 |
| HT precision | 0.333 | 0.496 | −0.163 |

*Comparison is directional, not like-for-like: this NN is scored on 82 session-level sequences, whereas the tabular base reports recording-level metrics over ~2,465 rows.*

## Key insights
- **Near-collapse toward WT.** With class weighting off, the Transformer predicts WT for almost everyone:
  HT recall 0.158 (only 3 of 19 HT sessions caught), HT F1 0.214, balanced accuracy 0.531 and MCC 0.085 —
  barely above chance despite a headline accuracy of 0.732 that just tracks the 77% WT prior.
- **Accuracy is a mirage here.** Test accuracy matches the base (−0.001) only because the majority class
  dominates; on the minority ASD-model class the model is far worse (HT recall −0.782, HT F1 −0.435 vs base).
- **The lever is the cause.** `pos_weight_beta=0.0` removes any minority upweighting, so the easy WT-everyone
  solution wins. This is the expected failure mode of the C config and the foil for the weighted/sampler
  experiments (B/D).
- AUC 0.702 shows the ranking is non-trivial — the signal exists — but the default 0.5 cut sits in the wrong
  place; train 0.848 vs test 0.732 indicates mild overfit on top of the collapse.

## Recommendations
- Do not use this config for HT detection. Prefer the class-balancing experiments — D (balanced minibatch
  sampler) is the most reliable collapse fix, with B (`beta=0.5`) and E (focal) as alternatives.
- If this checkpoint must be reused, its AUC 0.702 still ranks; move the decision threshold well below 0.5 to
  recover HT recall before trusting any positive call.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — ROC (AUC 0.702). `plots/training_curves.png` — loss/accuracy/AUC over 48 epochs.
- `model/transformer_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`; split/training detail: `logs/out.txt`.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
