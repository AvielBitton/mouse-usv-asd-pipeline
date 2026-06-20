# H_cv_Dsampler__bilstm__independent — BiLSTM · subject-independent · experiment H (5-fold CV of config D)

> 5-fold cross-validation of the balanced-sampler BiLSTM, evaluated **leak-free** (folds grouped by mouse).

## Overview
- **Model:** BiLSTM (2 layers, hidden 64, dropout 0.3; ~149K params). Input is a chronological
  per-syllable sequence (order preserved, `max_seq_len=256`), scored at **session level** — not the 48
  aggregated per-recording features the tabular base uses.
- **Evaluation split:** subject-independent — folds split **by mouse** (`--independent` / group-split),
  so no mouse appears in two sets. This is the honest "generalize to unseen mice" setting (harder than
  the dependent base model, which splits rows randomly and lets mice leak across train/test).
- **Dataset:** official baseline (Issue #46 filters; April-2026 HET→WT correction). 408 sessions from
  106 mice (HT 97 / WT 311, ~24% positive). Sequence lengths min 1 / median 236 / P95 704.
- **What was adapted vs the base model (lever H = CV of config D):** config D (**balanced minibatch
  sampler**, `pos_weight_beta=0.0`, BCE loss) re-run as **5-fold CV**, so the headline metrics are
  out-of-fold over all 408 sessions instead of a single test split. Two levers also change vs base:
  model family (BiLSTM instead of XGBoost) **and** evaluation moves from subject-dependent to
  subject-independent.

## Results (test set)
Out-of-fold over all 408 sessions (5 folds, ~81–83 test sessions each):

| Metric | WT | HT | Overall |
|---|---|---|---|
| Precision | 0.802 | 0.285 | — |
| Recall | 0.572 | 0.546 | — |
| F1 | 0.668 | 0.375 | weighted **0.598** |
| Accuracy | | | **0.566** (balanced 0.559) |

AUC 0.586 (OOF) · macro-F1 0.521 · MCC 0.101. Per-fold CV: AUC **0.689 ± 0.089**, balanced
accuracy 0.563 ± 0.063, accuracy 0.566 ± **0.167** (folds range 0.284 → 0.753), MCC 0.141 ± 0.112.

## Δ vs base model (`xgboost_subject_eval_dependent_baseline`)
| Metric | This run | Base | Δ |
|---|---|---|---|
| Test accuracy | 0.566 | 0.733 | −0.167 |
| Weighted F1 | 0.598 | 0.749 | −0.151 |
| WT F1 | 0.668 | 0.785 | −0.117 |
| HT F1 | 0.375 | 0.649 | −0.274 |
| HT recall | 0.546 | 0.940 | −0.394 |
| HT precision | 0.285 | 0.496 | −0.211 |

*Comparison is directional, not like-for-like: this BiLSTM is scored on 408 session-level sequences
(~81–83 per fold), while the tabular base is scored on ~2,465 recording-level rows under the easier
subject-dependent split.*

## Key insights
- **No degenerate collapse, but weak separation.** Both classes get real predictions (WT recall 0.572,
  HT recall 0.546), so the balanced sampler avoids the all-HT / all-WT failure seen elsewhere — yet OOF
  AUC is only 0.586 and accuracy 0.566, barely above chance for this ~24%-positive task.
- **HT is essentially unusable at the default cut:** precision 0.285 (≈7 of 10 HT calls are false
  positives), F1 0.375. The model trades the base's HT-heavy operating point (recall 0.940) for a
  symmetric-but-noisy one (HT recall 0.546), losing on every HT metric.
- **High cross-fold variance is the real story:** per-fold accuracy spans 0.284 → 0.753 and AUC 0.556 →
  0.825 across only ~81 test sessions per fold. With 106 mice the leak-free signal is fold-dependent;
  the fold-mean AUC 0.689 looks healthier than the OOF AUC 0.586, but the ±0.089 / ±0.167 spreads show
  it is not reliable.
- Early stopping fired at 16–35 epochs per fold (best val AUC 0.671–0.912); train accuracy is not
  reported (`train_accuracy: null`) because metrics are aggregated across folds.

## Recommendations
- CV confirms config D does not generalize on this small independent split — the leak-free signal is
  too weak and fold-variance too high for a session-level BiLSTM at ~408 sessions. Prefer the tabular
  independent runs (e.g. `../../tabular_models/`) for any honest "new-mouse" estimate.
- If pursuing NN further, gather more sequences or pool strains before re-tuning; the current per-fold
  AUC range (0.556–0.825) indicates results are dominated by which mice land in each fold, not by the
  recipe.

## Artifacts
- `plots/confusion_matrix.png`, `plots/confusion_matrix_counts.png` — aggregated confusion matrix
  (normalized + counts). `plots/roc_curve.png` — OOF ROC. `plots/training_curves.png` — per-fold
  loss/accuracy/AUC curves.
- `model/bilstm_fold1.pt` … `bilstm_fold5.pt` — the five fitted fold checkpoints.
- Metrics source: `results.json` (`cv` block + out-of-fold `classification_report`) · `logs/out.txt`
  (flags, split info, class balance, per-epoch / per-fold history).
---
*Base model: `xgboost_subject_eval_dependent_baseline` · metrics from `results.json` + `logs/out.txt` · summary auto-generated*
