# H_cv_Dsampler__bilstm__dependent — BiLSTM · subject-dependent · 5-fold CV (D-sampler config)

> BiLSTM over per-syllable sequences, 5-fold cross-validation of the balanced-sampler (D) config, evaluated subject-**dependent** (sessions split randomly, mice may leak).

## Overview
- **Model:** BiLSTM (~149K params; `hidden_size=64`, `num_layers=2`, `dropout=0.3`). Input is a
  chronological per-syllable sequence (order preserved, `max_seq_len=256`), unlike the tabular base
  model's 48 aggregated per-recording features. Scored at **session level**, not recording level.
- **Evaluation split:** subject-dependent — sessions split randomly (`subject_eval_independent=false`,
  `group_split=false`), so the same mouse can appear in train and test (leakage; optimistic, like the base
  model).
- **Cross-validation:** 5-fold CV (`--cv-folds 5`); each fold trained on ~260 sessions, validated on 66,
  tested on 81–82. Reported test numbers are the **out-of-fold (OOF)** pool over all 408 sessions.
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice (HT 97 / WT 311 ≈ 24% positive); sequence length median 236, P95 704, capped at 256.
- **What was adapted vs the base model (lever H = CV of D):** balanced minibatch sampler
  (`--sampler balanced`) with class weighting off (`--pos-weight-beta 0.0`, `loss=bce`) — the D recipe,
  here wrapped in 5-fold CV instead of a single split. Both the model family (BiLSTM vs XGBoost) and the
  input representation (sequence vs aggregated) change too.

## Results (test set)
Out-of-fold pool over all 408 sessions (early stopping on val AUC; folds ran 17–28 epochs).

| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.840 | 0.321 | — |
| Recall | 0.572 | 0.649 | — |
| F1 | 0.681 | 0.430 | weighted **0.621** |
| Accuracy | | | **0.591** (train n/a) |

Also: test AUC 0.632, balanced accuracy 0.611, MCC 0.189, PR-AUC (avg precision) 0.327.
Per-fold AUC ranged 0.577–0.779 (fold mean 0.673 ± 0.067) and accuracy 0.354–0.765 (mean 0.591 ± 0.144) —
very unstable across folds.

Confusion matrix (rows = true, cols = pred): `[[WT→WT 178, WT→HT 133], [HT→WT 34, HT→HT 63]]`.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.591 | 0.733 | −0.142 |
| Weighted F1 | 0.621 | 0.749 | −0.128 |
| WT F1 | 0.681 | 0.785 | −0.104 |
| HT F1 | 0.430 | 0.649 | −0.219 |
| HT recall | 0.649 | 0.940 | −0.291 |
| HT precision | 0.321 | 0.496 | −0.175 |

*Directional only: this NN is scored on ~408 session-level sequences (81–82 per fold) while the tabular
base is scored on ~2,465 recording-level rows — not a like-for-like comparison.*

## Key insights
- **No degenerate collapse, but a weak model.** The balanced sampler keeps both classes alive (WT recall
  0.572, HT recall 0.649 — both well off 0/1), so it avoids the all-HT or all-WT failure. The cost is a
  mediocre operating point: overall accuracy 0.591 and AUC 0.632 are near chance for this 76/24 split.
- **HT detection collapses on every axis vs base** — HT precision 0.321, recall 0.649, F1 0.430
  (−0.219). About 2 of 3 HT calls are false positives (133 WT misrouted to HT), and it still misses ~35%
  of HT pups. The base XGBoost trades far better.
- **Folds are highly unstable** — accuracy spans 0.354 (fold 3) to 0.765 (fold 5) and AUC 0.577–0.779;
  std 0.144 on accuracy. With only ~80 test sessions per fold, any single-split BiLSTM number is unreliable
  — the CV exists precisely to expose this variance.
- **Early stopping fires fast** (best val AUC at epochs ~2–13, training stops by 17–28) while train acc
  climbs to 0.85+; the BiLSTM overfits the small session set quickly and val AUC never recovers.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — OOF confusion matrices (normalized + counts).
- `plots/roc_curve.png` — OOF ROC (AUC 0.632). `plots/training_curves.png` — per-fold loss/acc/AUC curves.
- `model/bilstm_fold1.pt` … `bilstm_fold5.pt` — one fitted BiLSTM per CV fold.
- Metrics source: `results.json` (`cv` block + OOF `classification_report`) + `logs/out.txt` (split, class balance, early stopping).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
