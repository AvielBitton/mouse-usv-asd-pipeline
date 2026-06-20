# bilstm_subject_eval_dependent — BiLSTM · subject-dependent

**Status:** archived — superseded by `results/neural_networks/bilstm_subject_eval_dependent_baseline`.

> BiLSTM over per-syllable USV sequences, dependent (leaky) split — **collapses to predicting WT for every session**.

## Overview
- **Model:** BiLSTM (~149K params) over chronological per-syllable sequences (order preserved,
  `MAX_SEQ_LEN=256`), not the 48 aggregated per-recording tabular features. Scored at **session level**.
- **Evaluation split:** subject-dependent — random session-level split (`group_split=false`), so the same
  mouse can land in both train and test (train/val: 57, train/test: 61 shared mice per the log → leaky,
  optimistic).
- **Dataset:** external/all-data CSV cache — 442 sessions from 119 mice (WT 336 / HT 106 ≈ 24% HT);
  split into 264 train / 89 val / 89 test sessions, each ~76% WT / 24% HT.
- **Levers:** control run (defaults, "none (baseline)"). Class weighting `pos_weight=0.320`,
  Adam LR 1e-3 with decay, early stopping at epoch 16 (best val AUC 0.828).

## Results (test set)
| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.764 | 0.000 | — |
| Recall | 1.000 | 0.000 | — |
| F1 | 0.866 | 0.000 | weighted **0.662** |
| Accuracy | | | **0.764** (train 0.758) |

Test AUC 0.742 · best val AUC 0.828. The "accuracy" 0.764 is exactly the WT share of the 89 test
sessions (68/89) — the model assigns WT to **every** session, so HT recall = 0.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.764 | 0.733 | +0.031 |
| Weighted F1 | 0.662 | 0.749 | −0.087 |
| WT F1 | 0.866 | 0.785 | +0.081 |
| HT F1 | 0.000 | 0.649 | −0.649 |
| HT recall | 0.000 | 0.940 | −0.940 |
| HT precision | 0.000 | 0.496 | −0.496 |

*Comparison is directional, not like-for-like: this NN is scored on 89 session-level sequences, whereas
the tabular base is scored on ~2,465 recording-level rows.*

## Key insights
- **Degenerate collapse:** the model predicts WT (the majority class) for all 89 test sessions — WT recall
  1.000 / HT recall 0.000, HT F1 0.000. The headline "accuracy" 0.764 is just the test WT base rate, not
  real skill.
- The Δ table is dominated by this collapse: every HT metric drops to 0 (HT F1 −0.649, HT recall −0.940,
  HT precision −0.496), and the only "gains" — WT F1 +0.081 and accuracy +0.031 — come trivially from
  always predicting the majority class. The base model, by contrast, actually detects HT (recall 0.940).
- Training did learn signal early (val AUC peaked 0.828 at epoch 1) but then **degraded every epoch**
  (val AUC → 0.597, val loss rising) while train loss fell — overfitting to the leaky split before
  early stopping fired. Test AUC 0.742 confirms weak separation despite the collapsed hard predictions.
- Label mapping: `logs/out.txt` and `results.json` agree — support 68 (key `1.0`, "WT (1)") = WT and
  support 21 (key `0.0`, "HT (0)") = HT, matching the ~76% WT / 24% HT test balance — i.e. the all-WT
  collapse described above.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — confusion matrices (normalized + counts).
- `plots/roc_curve.png` — ROC (test AUC 0.742). `plots/training_curves.png` — loss/acc/AUC vs epoch.
- `model/bilstm_best.pt` — best checkpoint. `model/scaler.pkl` — feature scaler.
- Metrics source: `results.json`; `logs/out.txt` — flags, split/leakage info, per-epoch trace.
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
