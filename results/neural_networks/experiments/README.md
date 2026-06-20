# `experiments/` — sequence-model lever sweep (A–H)

Index of the neural-network experiment matrix: each lever is tried to fix the two problems the
[baseline NN runs](../) hit — **class imbalance** (HT ≈ 24%) and **data scarcity** (only ~19 HT test
sessions on the independent split), which together cause the models to collapse onto a single class.

Every experiment runs on the official `--baseline` sequence data across both eval splits and (most) three
architectures (BiLSTM / 1D-CNN / Transformer). Each child folder has its own `README.md` with full
results and Δ vs the base model (`../../tabular_models/xgboost_subject_eval_dependent_baseline`).

## The levers
| Prefix | Lever | What it changes |
|---|---|---|
| **A** | control | defaults (`pos_weight_beta=1.0`, no sampler, BCE) — the unmodified starting point |
| **B** | beta0.5 | milder class weighting: `pos_weight = (n_WT/n_HT)^0.5` |
| **C** | beta0 | no class weighting (`pos_weight=1.0`), raw BCE |
| **D** | sampler | balanced minibatch sampler (~50/50 per batch) + `beta=0` — **most reliable fix** |
| **E** | focal | focal loss (γ=2.0), confidence-based reweighting |
| **F** | regsmall | weight-decay + high dropout + smaller net, to fight overfit on the tiny independent split |
| **G** | augment | sliding-window augmentation of long train sessions |
| **H** | cv_Dsampler | 5-fold cross-validation of the **D** config (robustness check) |

## Full results
The ranked master table and the styled report live in [`_summary/`](_summary/):
- [`_summary/master_metrics.md`](_summary/master_metrics.md) — all runs ranked by balanced accuracy.
- `_summary/master_metrics.csv` — same data for analysis.
- `_summary/executive_summary.html` — narrative report.

## Key takeaways
- **D (balanced sampler) is the most reliable lever** — it rescues the BiLSTM all-HT collapse
  (dependent balanced-acc 0.500 → 0.628; WT recall 0% → 73%) where pure loss-weighting (A/B/C) does not.
- **The Transformer rarely collapses** — its control (A) is often already its best config.
- **H (CV) is the honesty check:** the dependent improvement holds up (≈0.61 ± 0.06), but the strong
  single-split *independent* numbers are a lucky-fold artifact — the 5-fold estimate (≈0.56 ± 0.06)
  confirms independent generalization is **data-limited**, not recoverable by these levers alone.

## Regenerate
```bash
python src/classification/neural_networks/sequence_pipeline.py --baseline --model {bilstm,cnn1d,transformer} [--independent] <lever flags>
python scripts/generate_nn_executive_summary.py --results-root results/neural_networks/experiments
```
