# Model Development & Experiments — End-to-End Documentation

> **Purpose.** This document is the canonical, research-grade reference for **how the
> training-ready matrices become trained, evaluated, and compared models** — the modeling
> stage downstream of feature aggregation. It covers the prediction task and evaluation
> protocol, **why** each model family was chosen, the technical details and experiments for
> the tabular and sequence models, decision-threshold tuning, the strain-cohort runs, and a
> head-to-head comparison of results. Every number is tied to a per-run summary under
> `results/**/README.md` so it can be verified and cited.
>
> Audience: the authors of the project's MSc Data Science thesis / research paper (and Claude,
> when drafting the *Modeling*, *Experiments*, and *Results* sections of a write-up).
>
> **Fourth in the documentation series:**
> 1. [`research_data_and_recording.md`](research_data_and_recording.md) — *where the recordings come from* (animals, rig, cohort).
> 2. [`segmentation_process.md`](segmentation_process.md) — *how a WAV becomes a syllable row* (segmentation + CNN typing).
> 3. [`preprocessing_pipeline.md`](preprocessing_pipeline.md) — *how syllable rows become a training matrix* (aggregation, encoding, splitting).
> 4. **this document** — *how the training matrix becomes trained, evaluated, and compared models*.
>
> The **base-model anchor** for every comparison is the run
> `results/tabular_models/xgboost_subject_eval_dependent_baseline` (test accuracy **0.733**,
> weighted F1 **0.749**); the legacy `baseline: 0.829` reference inside the raw
> `comparison_vs_baseline.txt` files is **not** used.
>
> Resolves Issue #77.

---

## 0. TL;DR — the modeling program in one paragraph

The task is binary classification of **offspring genotype** — wild-type (WT, control, label `0`) vs *Mthfr*-haploinsufficient heterozygote (HET/HT, the genetic ASD model, positive minority class ~24 %, label `1`) — from isolation-induced ultrasonic-vocalization (USV) acoustic features (cohort and labels in [`research_data_and_recording.md`](research_data_and_recording.md) §6–§8, §2.1). Two data **grains** are used: **tabular** models (XGBoost, TabPFN) consume one row **per recording** as a 46-feature aggregate vector, while **sequence** models (BiLSTM, 1D-CNN, Transformer) consume one ordered, padded syllable sequence **per isolation session** (Name × Day × Session); the two preprocessing tracks are detailed in [`preprocessing_pipeline.md`](preprocessing_pipeline.md) §2–§3. Every run is reported under both an optimistic **subject-dependent** split (random rows, the same mouse leaks across train/test) and the honest, leak-free **subject-independent** split (grouped by mouse). The **headline honest (subject-independent) result is weak but above chance**: the strongest leak-free model is **TabPFN at test accuracy 0.729 / balanced accuracy 0.662 / ROC-AUC 0.783** (`results/tabular_models/tabpfn_subject_eval_independent_baseline`), essentially matching the dependent base model on accuracy but losing the minority class (HT recall 0.782); on the **dependent** split the best is **TabPFN at accuracy 0.781 / balanced accuracy 0.828 / ROC-AUC 0.908** (`tabpfn_subject_eval_dependent_baseline`). The single most important caveat: genotype is **barely separable across unseen mice** with these features — a 5-fold cross-validated subject-independent sequence balanced accuracy of only **0.563 ± 0.063** (the headline single-split 0.704 was a lucky fold), so the dependent numbers are an optimistic ceiling, not a generalization estimate.

## 1. The modeling problem & evaluation protocol

### 1.1 Prediction task and label

Every model in this program solves the same supervised binary problem: **predict the pup's offspring genotype from its USV acoustics.** The target is `pup_gen` / `Offspring Genotype (binary)`, encoded **WT = 0, HET/HT = 1** with the *ASD-model carrier as the positive class* (the encoding is an explicit dict — not `LabelEncoder` — because alphabetical encoding would invert it; [`preprocessing_pipeline.md`](preprocessing_pipeline.md) §2.4). The biological motivation is that isolation-induced USVs are an early, pre-verbal, learning-independent readout of social-communication circuitry, hence an ASD-relevant phenotype ([`research_data_and_recording.md`](research_data_and_recording.md) §2.3); the *Mthfr* line is the genetic ASD model in this dataset (no CPF environmental arm — §2.1, §10 there).

### 1.2 Two data grains — and why they differ

The same syllable table feeds two tracks at two grains, because the two model families need two data shapes ([`preprocessing_pipeline.md`](preprocessing_pipeline.md) §0, §4):

| | **Tabular grain** | **Sequence grain** |
|---|---|---|
| One sample = | one **recording** (Name × Day × Session × Recording) | one **isolation session** (Name × Day × Session) |
| Representation | fixed **46-feature** aggregate vector (X; 48 columns minus `pup_gen` label and `mouse_idx` group key) | ordered, variable-length syllable sequence, **256 × 14**, padded/truncated |
| Temporal order | averaged away (per-type means + type distribution) | preserved, chronological |
| Approx. count (baseline) | ~12,323 recordings | ~408 sessions from 106 mice (97 HT / 311 WT sessions) |
| Models | XGBoost, TabPFN | BiLSTM, 1D-CNN, Transformer |

The grains differ because a single recording has a **median of only ~5 syllables** (mean 7.58; [`research_data_and_recording.md`](research_data_and_recording.md) §9) — far too short to learn call-to-call "syntax," so the sequence track aggregates recordings up to the **session** level (median ~236 syllables per session; [`NEURAL_NETWORK_BASELINE.md`](NEURAL_NETWORK_BASELINE.md) §2). The tabular track instead collapses each recording's syllables into per-type acoustic summaries, trading temporal structure for a small, dense feature vector that suits tree/PFN models.

> **For the paper.** The tabular and sequence tracks make *different decisions about the same raw data* (undefined calls dropped vs embedded; first-syllable rows dropped vs ISI→0; recording grain vs session grain), so head-to-head numbers are **representation + model** comparisons, not pure model comparisons ([`preprocessing_pipeline.md`](preprocessing_pipeline.md) §4 methodological note).

### 1.3 Class imbalance (~3:1 WT:HET)

The cohort is strongly imbalanced toward the control class. At the **pup level** the corrected cohort is WT = 91, HT = 29, UNK = 6 ([`research_data_and_recording.md`](research_data_and_recording.md) §7.3); after dropping ungenotyped pups this is the **~3:1 WT:HET** ratio quoted throughout. At the **recording level** in the official baseline test set, the balance is **WT 73.8 % / HT 26.2 %** (dependent) and **WT 72.9 % / HT 27.1 %** (independent) — so the positive HET class is ~24–27 % of samples. Imbalance is handled **at fit time**, not by resampling the data: XGBoost uses `scale_pos_weight ≈ 3.07–3.12` (= n_WT/n_HT), TabPFN natively, and the sequence models use `pos_weight = n_WT/n_HT ≈ 3.2` in `BCEWithLogitsLoss` (with optional `--pos-weight-beta`, balanced sampler, or focal loss; [`preprocessing_pipeline.md`](preprocessing_pipeline.md) §2.9, §3.8). A consequence to keep in view: the default `pos_weight ≈ 3.2` plus the fixed 0.5 decision threshold can push the smaller sequence models into an **all-HT collapse** (e.g. baseline BiLSTM dependent: accuracy 23.2 %, WT recall 0 %, HT recall 100 % — `results/neural_networks/executive_summaries/sequence_models/master_metrics.md`), which is an operating-point failure, not a ranking failure (its ROC-AUC is still 0.790).

### 1.4 Subject-DEPENDENT vs subject-INDEPENDENT splits (the honest number)

Two evaluation protocols are reported for **every** run, mirrored across both tracks ([`preprocessing_pipeline.md`](preprocessing_pipeline.md) §2.9, §3.8; [`CLI_Flags.md`](CLI_Flags.md)):

| Split | Flag | How it splits | Leakage | Interpretation |
|---|---|---|---|---|
| **Subject-dependent** | default (random) | 60/20/20 at the **row/session** level | the same mouse appears in train **and** test (logged: 105 mice shared train↔test for the base model) | **optimistic upper bound** |
| **Subject-independent** | `--independent` / `--group-split` | 60/20/20 **by mouse** (group-aware on `mouse_idx` / mouse name), with disjointness asserts | none — no mouse spans two sets | **the honest "generalize to unseen mice" number** |

This distinction is load-bearing because the cohort is strongly longitudinal: a single pup contributes **~131 recordings on average** (median 112, range 12–455) and ~997 syllables, so rows from one pup are highly correlated and a naïve row-level shuffle leaks identity ([`research_data_and_recording.md`](research_data_and_recording.md) §8). The empirical cost of removing that leak is the documented **~10–15 pt drop** dependent → independent ([`xgboost_subject_eval_dependent_baseline/README.md`](../results/tabular_models/xgboost_subject_eval_dependent_baseline/README.md)), concentrated in the minority class: for untuned XGBoost, HT recall falls **0.940 → 0.637 (−0.303)** and HT F1 **0.649 → 0.529 (−0.120)** when moving to the leak-free split. (TabPFN and the regularized tuned XGBoost recipe absorb more of this cost on aggregate accuracy — within ~0.005–0.03 — but still lose the minority class; §1.6.)

> ⚠️ **Always report the subject-independent number for any "new-mouse" claim.** The dependent split is an optimistic ceiling. The clearest illustration is the sequence track: a single subject-independent split gave BiLSTM balanced accuracy **0.704**, but the 5-fold grouped-CV honest estimate is only **0.563 ± 0.063** — with only ~19 test HT, the single split was a lucky fold ([`NEURAL_NETWORK_BASELINE.md`](NEURAL_NETWORK_BASELINE.md) §"CV verification"). Subject-independent generalization is genuinely limited by the data, not recoverable by tuning.

### 1.5 The metric suite and why each matters under imbalance

Because accuracy alone is misleading at ~3:1 imbalance (a constant-WT predictor scores ~0.74), every run reports the following suite (tabular: `comparison_vs_baseline.txt` + per-run `README.md`; sequence: `results.json` / `master_metrics.{md,csv}`):

| Metric | What it measures | Why it matters here |
|---|---|---|
| **Accuracy** | overall fraction correct | familiar, but inflated by the WT majority — interpret only against the ~0.74 majority-baseline |
| **Balanced accuracy** | mean of per-class recall | the headline imbalance-robust score; a constant predictor sits at 0.500, so it exposes the all-HT / all-WT collapses accuracy hides |
| **ROC-AUC** | threshold-free ranking quality | separates *ranking* from *operating point* — a model can have AUC ≈ 0.79 yet collapse at the 0.5 cut (a ranking-vs-threshold diagnostic) |
| **PR-AUC** (average precision) | precision-recall area, focused on the **positive (HET) class** | more informative than ROC-AUC for the rare class; the relevant ceiling on detecting ASD-model pups |
| **Weighted F1** | support-weighted mean F1 | single aggregate that still respects both classes' frequencies |
| **Per-class WT/HT precision, recall, F1** | per-class behavior | the clinically meaningful breakdown — **HT recall** (catching ASD-model pups) and **HT precision** (false-positive rate) are the numbers to watch, since high accuracy can hide low HT recall |
| **MCC** | Matthews correlation, balanced over the confusion matrix | a single imbalance-robust correlation that is near 0 for any degenerate single-class predictor (e.g. the all-HT BiLSTM has MCC 0.00) |

The per-run trade-off is consistent: at the default 0.5 threshold the models are **tilted toward catching HT** (high HT recall) at the cost of **weak HT precision (~0.45–0.55)**, i.e. roughly half of HT predictions are false positives. Threshold tuning to alternative objectives (Youden, F1, target-recall ≥ 0.80, balanced) is reported separately (`results/tabular_models/threshold/summary_matrix.txt`, `threshold_objectives/summary_objectives.txt`) to expose calibrated operating points.

### 1.6 The base-model anchor

Every tabular run's "Δ vs base model" table is measured against a single anchor: **untuned XGBoost on the official baseline, evaluated subject-dependent** (`results/tabular_models/xgboost_subject_eval_dependent_baseline`). Its exact test-set numbers:

```
Base model — xgboost_subject_eval_dependent_baseline (test set)
  Test Accuracy   0.733   (Train Accuracy 0.771)
  Weighted F1     0.749
  WT  P / R / F1  0.968 / 0.660 / 0.785
  HT  P / R / F1  0.496 / 0.940 / 0.649
  scale_pos_weight 3.12 ; test balance WT 73.8% / HT 26.2%
  confusion (true×pred): [[WT→WT 1199, WT→HT 619], [HT→WT 39, HT→HT 608]]
```

The base model's small train–test gap (0.771 → 0.733) **looks** well-fit but is inflated by leakage (the random split shares 105 mice across train↔test), so it is an optimistic ceiling. For context, the best **honest** subject-independent tabular run is TabPFN (accuracy 0.729, balanced accuracy 0.662, ROC-AUC 0.783, HT recall 0.782; `tabpfn_subject_eval_independent_baseline`), and the matched tuned-independent XGBoost recipe lands at accuracy 0.702 with an almost-zero train–test gap (0.714 → 0.702); the best **dependent** run is TabPFN (accuracy 0.781, balanced accuracy 0.828, ROC-AUC 0.908).

> ⚠️ **Ignore the legacy `0.829` reference.** Each tabular run ships a `comparison_vs_baseline.txt` whose `baseline:` column shows `0.829`. **That is a legacy artifact, not our base model** — read only each run's own metrics (the run column) and compare against the anchor above. This caveat is restated in every per-run `README.md`.

### 1.7 The baseline data

All numbers above are on the **official baseline dataset** (Issue #46 filters; full spec in `docs/BASELINE_DATA_FILTERS.md`, counts in `docs/BASELINE_DATA_MANIFEST.md`). Starting from the 125,576-row corrected syllable table, the baseline applies, on top of the always-on binary-genotype filter: **`invalid_sex`** (keep `Sex ∈ {M, F}`) and **`supplement_offspring`** (drop all rows of any dietary-supplement-arm pup), while **retaining `Noise == 1` syllables**. This yields **12,323 aggregated recording rows** for the tabular track (`all_data_external_baseline.csv`) and the parallel syllable-level `all_data_external_baseline.xlsx` for the sequence track ([`preprocessing_pipeline.md`](preprocessing_pipeline.md) §2.5; [`CLI_Flags.md`](CLI_Flags.md)). Two data-provenance points are essential to state in the paper:

- **Individual genotyping (April-2026 HET→WT correction).** The original metadata mislabeled *all* pups of a HET dam as HET; a HET × WT cross is genetically ~50/50, so **14 mice (2,495 rows across 6 metadata files)** were corrected HET→WT using per-animal genotyping from the external segmentation file. This correction is **already applied** in the baseline, and is why training must use the external file ([`segmentation_process.md`](segmentation_process.md) §9.7; [`research_data_and_recording.md`](research_data_and_recording.md) §7.3, §11.7).
- **Genotype filter (always on).** Rows whose mother *or* offspring genotype is not WT/HET (after HT→HET unification) are dropped, which removes the 6 `WT-UNK` pups and keeps the label strictly binary.

---

## 2. Why these models — research motivation

> **Purpose.** This section justifies the **model ladder** the project trains —
> untuned XGBoost → tuned XGBoost → TabPFN → three sequence models (BiLSTM, 1D-CNN,
> Transformer) — against two fixed constraints: the **research question** (predict
> offspring genotype WT vs HET/HT from isolation-call USVs) and the **shape of the
> data** (a small, longitudinal, class-imbalanced single-lab cohort). Each rung
> answers one specific methodological question, and each is tied to a concrete result
> file under [`results/`](../results/). The data structure it must respect is set out
> in [`research_data_and_recording.md`](research_data_and_recording.md) §6–§9, the two
> training representations in [`preprocessing_pipeline.md`](preprocessing_pipeline.md)
> §2–§4, and the SOTA framing of the upstream DSP in
> [`segmentation_process.md`](segmentation_process.md) §10.

### 2.1 What the data forces on the model choice

Three properties of the corpus dictate the ladder before any model is picked. They are
documented in detail in [`research_data_and_recording.md`](research_data_and_recording.md)
and summarized here because every model choice below is a response to one of them.

| Data property | Value | Modeling consequence |
|---|---|---|
| **Small cohort** | **126 pups** from **35 dams** (`research_data_and_recording.md` §6) | After subject-grouped splitting the *independent* test fold holds only **22 mice / ~19 HT sessions** (`docs/NEURAL_NETWORK_BASELINE.md` §9). Deep nets trained from scratch are easy to overfit; favour low-capacity / strong-prior models. |
| **Class imbalance** | Offspring **WT 91 / HT 29 / UNK 6** pups → positive minority **~24 %** (`research_data_and_recording.md` §7.3); ~3:1 WT:HET at fit time | Accuracy is misleading; HT (the ASD model) is the minority *and* the clinically important class. Every model must handle imbalance (XGBoost `scale_pos_weight≈3.1`, TabPFN natively, NNs via `pos_weight`/sampler — `preprocessing_pipeline.md` §2.9, §3.8). |
| **Longitudinal / repeated-measures** | one pup ≈ **131 recordings / ~997 syllables**, spanning 2–3 ages, both sessions (`research_data_and_recording.md` §8) | Rows from the same pup/dam are highly correlated → naïve row shuffles leak identity and inflate metrics. Mandates **subject-grouped** evaluation; the *independent* split is the publishable number. |

> **For the paper.** The cohort is *small, imbalanced, and longitudinal*. That triad —
> not a preference for any one algorithm — is the reason the ladder runs from a
> reproducible classical baseline up to small, regularized or prior-loaded models, and
> why every claim is reported under a **subject-independent** split. There is no large
> held-out population to absorb high-capacity models, so the ladder is deliberately a
> ladder of *inductive bias and data efficiency*, not of raw parameter count.

A second structural fact splits the ladder in two. The same syllable table is turned
into **two different representations** (`preprocessing_pipeline.md` §0): a per-recording
**48-column aggregate** that *averages away temporal order*, and a per-session **ordered
sequence** that *preserves it*. The tabular rungs (§2.2–§2.4) all consume the aggregate;
the sequence rungs (§2.5) consume the ordered sequences. This is what makes the ladder a
genuine experiment about the data and not only about classifiers — see §2.6.

### 2.2 Rung 1 — Untuned XGBoost: a reproducible classical baseline that mirrors the lab tradition

The base model is **untuned XGBoost** on the official baseline aggregate, evaluated
subject-dependent
([`results/tabular_models/xgboost_subject_eval_dependent_baseline/`](../results/tabular_models/xgboost_subject_eval_dependent_baseline/)).
It exists for two reasons.

**(a) It speaks the lab's own language.** The tabular features are hand-engineered
per-syllable-type aggregates — mean start/end frequency, relative frequency, mean
duration per type, plus maternal genotype, sex, mean ISI, age, session, strain
(`preprocessing_pipeline.md` §2.2–§2.3). These are *exactly* the summary-statistic
descriptors that Shekel et al. (2021) and Gal et al. (2023) used (Start/End Frequency,
Duration, ICI; `research_data_and_recording.md` §4). A gradient-boosted-tree model over
those features is therefore the natural ML continuation of the published statistical
analyses — it asks "do the same per-call summary statistics the lab already trusts carry
enough genotype signal for a classifier?"

**(b) It is the honest, reproducible anchor.** It uses the legacy untuned recipe with no
hyperparameter search (`scale_pos_weight=3.12` from n_WT/n_HT), so every other tabular
run is measured as a Δ against it. On the test set it reaches **Test Acc 0.733 (train
0.771), Weighted F1 0.749**, with **WT P/R/F1 0.968 / 0.660 / 0.785** and **HT P/R/F1
0.496 / 0.940 / 0.649** — i.e. a recall-heavy operating point that catches 94 % of
ASD-model pups but at HT precision ~0.50 (roughly half of HT calls are false positives).

> **For the paper.** Position untuned XGBoost as the **reproducible classical baseline**:
> gradient-boosted trees over the same bioacoustic summary statistics as the source
> papers, with deterministic class weighting and no tuning. Its recall-heavy, low-HT-
> precision profile (HT precision 0.496) is the headline limitation that motivates every
> higher rung — class separation, not the operating point, is the wall.

### 2.3 Rung 2 — Tuned XGBoost: does careful hyperparameter search actually help?

XGBoost has many knobs (depth, learning rate, subsampling, regularization). Rung 2 holds
the **model family and features fixed** and changes only the hyperparameters, via a
**200-trial random search**, to isolate the value of tuning. Crucially, tuning is done
**per split** — a recipe tuned for the dependent split and a separate one tuned for the
independent split — because the right amount of regularization depends on whether the
evaluation leaks subjects.

- **Tuned-dependent, on its native dependent split**
  ([`xgboost_tuned_dependent_subject_eval_dependent_baseline/`](../results/tabular_models/xgboost_tuned_dependent_subject_eval_dependent_baseline/)):
  **Test Acc 0.772 (+0.039 vs base), Weighted F1 0.785 (+0.036)**, HT F1 0.661 (+0.012).
  Tuning shifts the operating point — HT recall 0.844 (−0.096) but HT precision 0.543
  (+0.047) — a small net HT gain driven mostly by WT.
- **Tuned-independent, on the leak-free split**
  ([`xgboost_tuned_independent_subject_eval_independent_baseline/`](../results/tabular_models/xgboost_tuned_independent_subject_eval_independent_baseline/)):
  **Test Acc 0.702, Weighted F1 0.719, train 0.714** — a **0.01 train/test gap**. The
  heavily regularized, shallow tuned recipe almost eliminates overfitting and costs only
  ~0.03 vs the optimistic dependent base, far short of the usual 10–15 pt dependent→
  independent drop seen in the untuned independent run (Acc 0.693; HT recall collapses to
  0.637 there).

> **For the paper.** Tuning's verdict is **modest but real, and split-dependent**. On the
> matched split it buys ~+0.03–0.04 accuracy; its larger contribution is *generalization*
> — the regularized independent recipe holds the train/test gap to 0.01 and resists the
> dependent→independent collapse. But HT precision stays ~0.47–0.54 throughout: tuning
> reshapes the operating point, it does not create class-separating signal that the
> features lack.

### 2.4 Rung 3 — TabPFN: a foundation model for small tabular data, no tuning

The cohort is exactly the regime where a **prior-data-fitted transformer** is expected to
shine. **TabPFN** (TabPFN-3, via the `tabpfn` package; `preprocessing_pipeline.md` §2.9)
is a transformer **pre-trained on millions of synthetic tabular tasks**: at inference it
performs in-context Bayesian prediction over the training rows in a single forward pass,
with **no hyperparameter search** and no per-dataset training loop. That makes it a
natural fit for a **few-thousand-row, low-dimensional** problem where there is little data
to tune on, and a clean contrast to the bespoke-tuned trees of Rung 2.

- **Dependent split**
  ([`tabpfn_subject_eval_dependent_baseline/`](../results/tabular_models/tabpfn_subject_eval_dependent_baseline/)):
  beats the XGBoost base on **every aggregate** — **Test Acc 0.781 (+0.048), Weighted F1
  0.794 (+0.045)**, HT F1 0.688 (+0.039), HT precision 0.550 (+0.054) — a model-only win,
  since only the model family changes vs the base.
- **Independent (leak-free) split**
  ([`tabpfn_subject_eval_independent_baseline/`](../results/tabular_models/tabpfn_subject_eval_independent_baseline/)):
  **Test Acc 0.729, Weighted F1 0.743 — within ~0.005 of the optimistic dependent base**,
  largely absorbing the dependent→independent difficulty that costs untuned XGBoost
  ~0.04+ and a −0.303 HT-recall hit. HT recall here is 0.782, HT precision ~0.50.

> **For the paper.** Frame TabPFN as the **modern, tuning-free, data-efficient tabular
> learner** appropriate to a small cohort: it is the strongest tabular model on the leaky
> split (Acc 0.781) and the most robust on the honest one (Acc 0.729, almost no
> dependent→independent drop). It does *not*, however, break the **HT-precision ~0.50
> ceiling** — confirming this is a property of the **aggregated features**, not of any one
> tabular algorithm, which is the bridge to the sequence models.

### 2.5 Rung 4 — Sequence models: preserve the temporal order aggregation discards

Every tabular rung shares one blindness: the per-recording aggregate **averages away the
order of calls** (`preprocessing_pipeline.md` §2.2; `NEURAL_NETWORK_BASELINE.md` §2). Yet
*temporal dynamics of isolation calls* — within- and between-session sequencing, maternal
potentiation across S1→S2 — is precisely the phenomenon **Gal et al. (2023)** studied
(`research_data_and_recording.md` §1, §5.2). If genotype shapes the *syntax* of calling
and not only the average acoustics of each call type, no aggregate feature can see it. The
sequence track is the direct test of that hypothesis: it keeps each isolation **session**
as an **ordered, variable-length sequence of syllables** (median ≈ 236 calls, padded/
truncated to 256), each step carrying 4 continuous acoustics + a learned syllable-type
embedding + Noise/recording-boundary flags (`preprocessing_pipeline.md` §3).

Three architectures probe three different notions of "order," all small and trained from
scratch to suit the tiny corpus (params from
[`results/neural_networks/executive_summaries/sequence_models/master_metrics.md`](../results/neural_networks/executive_summaries/sequence_models/master_metrics.md)):

| Model | Inductive bias on the sequence | Params | Why include it |
|---|---|---|---|
| **BiLSTM** | recurrence — long-range, bidirectional call-to-call dependencies | 148,953 | tests whether genotype lives in the *unfolding* of a calling bout |
| **1D-CNN** | local motifs — short fixed-window syllable n-grams via `Conv1d(k=3)` | 86,041 | tests whether short, position-invariant call patterns carry signal |
| **Transformer** | attention — content-based links between arbitrary positions (CLS readout) | 72,537 | tests whether non-local relations between calls matter |

The baseline sequence runs are weak and dominated by an imbalance-driven **operating-
point collapse** rather than poor ranking (`NEURAL_NETWORK_BASELINE.md` §9): the BiLSTM
collapses to all-HT (Test Acc 23.2 %, HT recall 100 %, WT F1 0.00) while its **AUC is
0.790** — i.e. it *ranks* well but the `pos_weight≈3.2` + fixed 0.5 threshold push the
decision boundary off. The Transformer never collapses (dependent Test Acc 65.9 %, AUC
0.655; independent AUC 0.675). After rebalancing levers, the honest CV estimate for the
best recipe (balanced-sampler BiLSTM) is **balanced accuracy 0.563 ± 0.063 independent /
0.609 ± 0.055 dependent** — above chance and above the collapse, but with subject-
independent generalization genuinely **bounded by the data**, not by configuration.

> **For the paper.** The sequence models are the project's test of the **Gal (2023)
> temporal-dynamics hypothesis** under a predictive frame: do the *order and timing* of
> calls add genotype signal beyond per-type averages? Include all three to separate
> recurrence (BiLSTM), local motifs (1D-CNN) and attention (Transformer). Report **AUC
> and balanced accuracy**, never raw accuracy, and report the **CV** estimate — the
> sequence AUCs (0.60–0.79) sit *at or above* a tuned logistic-regression ceiling
> (ROC-AUC ≈ 0.63 dependent, ≈ 0.50–0.57 by-mouse; `NEURAL_NETWORK_BASELINE.md` §9), so
> the limit is a **weak-signal data ceiling**, the central honest finding.

### 2.6 The ladder as one experiment

Read top to bottom, the rungs vary **two axes deliberately and one at a time** so each
comparison is interpretable (every run's README states which lever moved): the *model
family* (untuned XGB → tuned XGB → TabPFN), the *representation* (aggregate vs ordered
sequence), and — orthogonal to both — the *evaluation split* (dependent vs independent).

| Rung | Model | Representation | Question it answers |
|---|---|---|---|
| 1 | Untuned XGBoost | 48-col aggregate | Reproducible classical baseline over the lab's summary statistics |
| 2 | Tuned XGBoost (per split) | 48-col aggregate | Does careful hyperparameter search help? (and how much is generalization) |
| 3 | TabPFN | 48-col aggregate | Does a data-efficient tabular foundation model help, with no tuning? |
| 4 | BiLSTM / 1D-CNN / Transformer | ordered session sequence | Does temporal call order (Gal 2023) add signal aggregation discards? |

Because rungs 1–3 share the aggregate features, a tabular improvement is a *model* effect;
because rung 4 changes the representation, it is a *representation + model* effect and must
be framed as such (`preprocessing_pipeline.md` §4). Two through-lines hold across the whole
ladder and are the paper's load-bearing conclusions: (i) the **HT-precision ~0.50 wall**
survives every tabular model, so it is a property of the *features*, and (ii) **subject-
independent** generalization stays modest for all families, confirming a **weak-signal,
small-cohort ceiling** rather than a fixable modeling defect. This mirrors the
upstream-stack assessment — a classical, interpretable feature side plus modern,
data-efficient learners (`segmentation_process.md` §10;
`preprocessing_pipeline.md` §6) — and points the clearest future work at **richer
per-call acoustic features** (contours, bandwidth, FM depth) rather than larger models.

---

## 3. Tabular models (XGBoost, TabPFN)

The tabular track consumes the **48-column per-recording feature vector** described in
[`preprocessing_pipeline.md`](preprocessing_pipeline.md) (§0–§2): each recording is reduced
to one row of 46 features (10 syllable types × {start-freq, end-freq, relative-freq, duration}
+ maternal genotype, pup sex, mean ISI, age, session, strain), labeled by offspring genotype
(`pup_gen`; WT = 0, HET/HT = 1). No scaling is applied — both estimators are scale-invariant
(gradient-boosted trees, and a transformer trained on a synthetic prior). Two model families
are evaluated, each under both split regimes defined in
[`preprocessing_pipeline.md`](preprocessing_pipeline.md):

- **Subject-dependent** — rows are split randomly, so the same mouse can land in train and
  test. This leaks per-mouse identity signal and gives an **optimistic** read; it is the regime
  of the reference **base model**.
- **Subject-independent** — the split is grouped by `mouse_idx`, so no mouse appears in two
  sets. This is the honest "generalize to unseen mice" estimate.

The model registry lives in `src/classification/tabular/models.py` (`MODEL_REGISTRY`); each
factory returns an sklearn-compatible estimator. HT (the ASD-model minority, ~24–27% of rows)
is the positive class throughout.

> **For the paper.** All tabular runs share one feature representation and one label encoding;
> the only levers that vary across the six runs are (a) the **model family** (XGBoost vs TabPFN),
> (b) the **hyperparameter recipe** (untuned legacy vs split-matched tuned), and (c) the
> **evaluation split** (dependent vs independent). Each run isolates one or two of these levers
> against the base model, so deltas are directly attributable.

### 3.1 XGBoost — hyperparameters and how the tuned configs were found

Three XGBoost recipes are registered. The **untuned** recipe (`create_xgboost`) is the legacy
production point and defines the base model; the two **tuned** recipes were each selected by a
separate 200-trial random search whose hold-out split *matched* the regime they target.

| Hyperparameter | `xgboost` (untuned) | `xgboost_tuned_dependent` | `xgboost_tuned_independent` |
|---|---:|---:|---:|
| `n_estimators` | 50 | 96 | 20 |
| `max_depth` | 5 | 8 | 3 |
| `learning_rate` | 0.10 | 0.08 | 0.10 |
| `min_child_weight` | 0.1 | 2 | 20 |
| `reg_lambda` (L2) | 1.5 | 3.0 | 3.0 |
| `reg_alpha` (L1) | 0.05 | 1.0 | 0.05 |
| `gamma` | — (0) | 0.0 | 0.0 |
| `subsample` | — (1.0) | 0.6 | 0.6 |
| `colsample_bytree` | 0.6 | 0.7 | 0.6 |
| `scale_pos_weight` | n_WT/n_HT (≈3.1) | n_WT/n_HT (≈3.1) | n_WT/n_HT (≈3.1) |
| `objective` / `booster` | `binary:logistic` / `gbtree` | `binary:logistic` / `gbtree` | `binary:logistic` / `gbtree` |

All three weight the HT minority with `scale_pos_weight = n_WT/n_HT` (≈3.07–3.12 depending on
the split's train fold), set at fit time — corrected **single-weighting**; the legacy
double-weighting (`sample_weight=balanced` *and* `scale_pos_weight`) is applied only under
`--legacy`. Removing the double-weight is what recovered WT recall and lifted accuracy,
especially on the independent split (+0.11), without re-introducing the HT-over-prediction bias
(see `outputs/reports/xgboost_tuning/xgboost_tuning_summary.md` §A).

**Search protocol** (`scripts/tune_xgboost_hyperparams.py`). Each tuned config came from a
**200-trial random search over 8 hyperparameters** with the following selection pipeline:

1. **Hold-out test (20%)** carved off first, using the *same* split logic as
   `train_classifier.py`: group-aware by `mouse_idx` for `--independent`, stratified random for
   `--dependent`. The remaining 80% is the trainval pool.
2. Each sampled config is scored by **5-fold cross-validation** on the 80% — `StratifiedKFold`
   for dependent, `StratifiedGroupKFold` (grouped by `mouse_idx`) for independent — so the CV
   respects the same leakage discipline as the final evaluation.
3. Inside every fold the model trains with **`early_stopping_rounds=25`** against the fold's
   validation set (ceiling `n_estimators=500`), so the tree count is chosen *per config* rather
   than fixed.
4. **Primary objective: mean CV balanced accuracy** — the honest summary on this imbalanced
   task. `scale_pos_weight = n_WT/n_HT` is recomputed on each fitting fold.
5. The **top-5** configs are refit on the full 80% (with `n_estimators = ceil(mean best_iter ×
   1.1)`, clamped to ≤500) and scored on the held-out test; trials and top-K test metrics are
   saved under `outputs/reports/xgboost_tuning/`.

The search space (`SEARCH_SPACE`) deliberately includes the untuned production point so it can
be re-drawn. The two recipes that ship are: **dependent = rank 5** by test accuracy (CV
balanced acc 0.8186, the best-test config among the top-5), and **independent = rank 3** by CV
balanced accuracy. Their separate selection is what produces their opposite character: the
dependent recipe goes **deep** (`max_depth=8`, 96 trees) because the leaky split rewards
capacity, whereas the independent recipe collapses to a **shallow, heavily-regularized** model
(`max_depth=3`, `min_child_weight=20`, only 20 trees) because, as the tuning summary notes (§D),
the independent split is **data-limited, not hyperparameter-limited** — every top-5 independent
config converged on `max_depth=3, n_estimators=20` and CV balanced accuracy saturated at 0.7861.

### 3.2 TabPFN — specifics

TabPFN (`create_tabpfn`, the TabPFN-3 prior-data-fitted transformer via the `tabpfn>=8.0`
package) is treated differently from the XGBoost family in three ways encoded in
`src/classification/tabular/models.py`:

- **No hyperparameter tuning.** TabPFN is a pre-trained transformer that performs in-context
  learning at predict time; there is nothing to fit-search. It carries no entry in the random
  search, no `eval_set`, **no learning curve, and no feature-importance plot** (it is absent
  from `XGBOOST_FAMILY`, so `has_feature_importance`/`has_training_curves` return False).
- **Validation merged into train** (`_MERGES_VAL_INTO_TRAIN = {"tabpfn"}`). Because there is no
  early stopping or fit-time search, the val split would be wasted, so it is folded back into
  train — giving the model **80% of the data instead of 60%** (e.g. 7,393 + 2,465 → **9,858**
  train rows on the dependent split). This is also why TabPFN's *train* accuracy reads inflated
  (0.888 dependent, 0.911 independent) — the figure is computed over the enlarged train pool.
- **Native imbalance handling.** `balance_probabilities=True` performs built-in class-balance
  correction — the conceptual equivalent of `scale_pos_weight` in XGBoost, handled inside the
  model. `ignore_pretraining_limits=True` allows the full training set (TabPFN-3 supports up to
  1M rows; our tables are well within range). Requires `TABPFN_TOKEN` in `.env`.

### 3.3 Results — all six runs (test set)

All metrics are the runs' own test-set numbers from
`results/tabular_models/<run>/README.md` (sourced from `comparison_vs_baseline.txt` run column +
`logs/out.txt`). The **base model** is `xgboost_subject_eval_dependent_baseline`:
**Test Acc 0.733 · Weighted F1 0.749 · WT F1 0.785 · HT F1 0.649 · HT recall 0.940 · HT
precision 0.496** (train 0.771).

| Run | Split | Test Acc | Weighted F1 | WT F1 | HT F1 | HT recall | HT precision |
|---|---|---:|---:|---:|---:|---:|---:|
| **xgboost** (base) | dependent | **0.733** | **0.749** | 0.785 | 0.649 | **0.940** | 0.496 |
| xgboost_tuned_dependent | dependent | 0.772 | 0.785 | 0.829 | **0.661** | 0.844 | 0.543 |
| tabpfn | dependent | **0.781** | **0.794** | **0.832** | **0.688** | 0.918 | **0.550** |
| xgboost | independent | 0.693 | 0.706 | 0.772 | 0.529 | 0.637 | 0.452 |
| xgboost_tuned_independent | independent | 0.702 | 0.719 | 0.758 | 0.612 | 0.869 | 0.473 |
| tabpfn | independent | 0.729 | 0.743 | 0.792 | 0.610 | 0.782 | 0.499 |

**Δ vs base model** (run − base; base row omitted as it is the anchor):

| Run | Split | ΔAcc | ΔWeighted F1 | ΔWT F1 | ΔHT F1 | ΔHT recall | ΔHT precision |
|---|---|---:|---:|---:|---:|---:|---:|
| xgboost_tuned_dependent | dependent | +0.039 | +0.036 | +0.044 | +0.012 | −0.096 | +0.047 |
| tabpfn | dependent | +0.048 | +0.045 | +0.047 | +0.039 | −0.022 | +0.054 |
| xgboost | independent | −0.040 | −0.043 | −0.013 | −0.120 | −0.303 | −0.044 |
| xgboost_tuned_independent | independent | −0.031 | −0.030 | −0.027 | −0.037 | −0.071 | −0.023 |
| tabpfn | independent | −0.004 | −0.006 | +0.007 | −0.039 | −0.158 | +0.003 |

> ⚠️ **Do not read the `baseline:` column inside any `comparison_vs_baseline.txt`** — it is a
> legacy 0.829 reference, **not** the base model. Every delta above is computed against the
> base model's own test metrics (0.733 / 0.749 / 0.785 / 0.649 / 0.940 / 0.496).

### 3.4 Insights

- **Tuning gains are modest on the dependent split.** `xgboost_tuned_dependent` lifts accuracy
  +0.039 (0.733 → 0.772) and weighted F1 +0.036 (0.749 → 0.785), driven mostly by **WT**
  (recall 0.660 → 0.747, WT F1 0.785 → 0.829). On the minority class the gain is marginal: HT
  F1 rises only +0.012 (0.649 → 0.661). What tuning really does is **move the operating point**
  — HT recall drops −0.096 (0.940 → 0.844) while HT precision rises +0.047 (0.496 → 0.543);
  fewer ASD-model pups are caught, but fewer false positives. The independent tuned recipe is
  similar relative to the *untuned* independent run: +0.009 accuracy but a large HT-recovery
  (HT F1 0.529 → 0.612, HT recall 0.637 → 0.869), exactly the recall the regularized recipe was
  selected to restore.

- **Best HT-F1 on the dependent split is TabPFN** (HT F1 **0.688**, vs 0.661 tuned-XGB and 0.649
  base) — and it is the best run on *every* aggregate: accuracy 0.781 (+0.048), weighted F1
  0.794 (+0.045), with HT recall still near-saturated at 0.918. A clean model-only win on the
  same data, attributable to its highest HT precision (0.550) cutting false positives while
  holding recall. On the independent split, however, the tuned XGBoost edges TabPFN on HT F1
  (0.612 vs 0.610) and on HT recall (0.869 vs 0.782).

- **The independent (leak-free) drop is real but uneven.** Untuned XGBoost pays the full toll:
  accuracy −0.040 and a **HT collapse** — HT recall −0.303 (0.940 → 0.637), HT F1 −0.120 — i.e.
  it misses ~1 in 3 ASD-model pups on unseen mice. The split-matched recipes absorb most of the
  cost: `xgboost_tuned_independent` lands only −0.031 accuracy, and **TabPFN independent is −0.004
  accuracy / −0.006 weighted F1** vs the optimistic dependent base — far short of the usual
  10–15 pt dependent→independent drop. Train-vs-test gaps confirm the mechanism: the shallow
  tuned-independent XGBoost shows almost no overfit (train 0.714 / test 0.702, 0.01 gap), while
  TabPFN's large gaps (train 0.888/0.911) are an artifact of merging val into train, not memorization.

- **HT precision is capped around 0.50 everywhere.** Across all six runs HT precision sits in
  **0.45–0.55** (untuned-independent 0.452 → TabPFN-dependent 0.550), so **roughly half of every
  model's HT predictions are false positives** regardless of family, tuning, or split. This is
  the dominant limit on the task: HT recall can be pushed to 0.92–0.94, but class separation in
  the 46-feature space is weak enough that precision will not move much past ~0.55 at the default
  0.5 cut. Lifting it requires moving the decision threshold (see the
  `results/tabular_models/threshold/` and `threshold_objectives/` runs) rather than a better
  estimator, and the per-recording grain itself is part of the ceiling — the
  [`segmentation_process.md`](segmentation_process.md) syllable-type signal is aggregated away
  into means here, whereas the sequence models retain syllable order.

> **For the paper.** The honest headline tabular result is **TabPFN, subject-independent:
> Test Acc 0.729 · Weighted F1 0.743 · HT F1 0.610 · HT recall 0.782 · HT precision 0.499** —
> essentially matching the optimistic XGBoost base model's *accuracy* while being measured on
> entirely unseen mice. Untuned XGBoost is the right *reference* anchor (it defines Δ), but it is
> the *least* representative of true generalization; quote the independent runs for any
> new-mouse claim, and report HT precision ≈ 0.50 as the task's structural ceiling at the
> default operating point.

---

## 4. Sequence models (BiLSTM, 1D-CNN, Transformer)

The sequence models attack the same WT-vs-HET genotype task from the opposite
representation to the tabular base model. Where XGBoost/TabPFN consume a flat
**48-column per-recording** aggregate (`docs/preprocessing_pipeline.md` §2), the
neural networks read each **isolation session** as an *ordered, variable-length list
of syllables* — the "syntax" the aggregation throws away — and learn directly from
the call-to-call dynamics (`docs/preprocessing_pipeline.md` §3). The full data
construction (grouping by `Name × Day × Session`, the 14-d per-step vector, the 8-d
syllable-type embedding, `StandardScaler` fit on train only, padding to
`max_seq_len = 256`) is documented there and in
[`docs/NEURAL_NETWORK_BASELINE.md`](NEURAL_NETWORK_BASELINE.md); this section covers
the **architectures, the shared training protocol, the degenerate-collapse problem,
the six baseline runs, and the A–H imbalance-experiment matrix**.

> ⚠️ **Not a 1:1 comparison to the tabular base.** Every sequence metric below is
> scored at the **session level** (the baseline pool is **408 sessions** from **106
> mice**, HT 97 / WT 311, ≈ 24 % positive), whereas the tabular base model
> (`xgboost_subject_eval_dependent_baseline`: Test Acc **0.733**, Weighted F1
> **0.749**, WT P/R/F1 **0.968/0.660/0.785**, HT P/R/F1 **0.496/0.940/0.649**) is
> scored on **~2,465 recording-level rows**. The per-run `comparison_vs_baseline`
> tables therefore label the Δ-vs-base as **directional, not like-for-like** — a
> different unit (session vs recording), a different split, and a different input
> representation all change at once. Treat the sequence numbers as a within-family
> study, not as a head-to-head against the recording-level anchor.

### 4.1 Architectures

All three share the same front-end and head (`sequence_pipeline.py`): the categorical
`Syllable number` (0–10, **including** Undefined = 10) goes through
`nn.Embedding(11, 8)`; the 4 continuous features, the 8-d embedding, and the `Noise` +
`recording_boundary` flags are concatenated to a **14-dim per-timestep input**; the
pooled sequence representation is concatenated with a **4-dim session-level metadata
vector** `[Mother Genotype (binary), Sex (M=1), Day, Session]` and passed to a
`Linear(… + 4) → 64 → ReLU → Dropout → Linear(64 → 1)` sigmoid head. All models are
**trained from scratch** (no pretraining), and are deliberately small for a
few-hundred-session corpus.

| Model | `--model` | Params | Core block | Sequence → vector |
|-------|-----------|-------:|------------|-------------------|
| **BiLSTM** | `bilstm` | **148,953** | 2-layer **bidirectional LSTM**, hidden 64, dropout 0.3 | concat of final forward + backward hidden states (`h_n[-2]`, `h_n[-1]`); `pack_padded_sequence` masks padding |
| **1D-CNN** | `cnn1d` | **86,041** | 3× `Conv1d(k=3, pad=1)` 64→128→128, each + `BatchNorm1d` + ReLU | length-masked **mean-pool** over time (sum ÷ true length) |
| **Transformer** | `transformer` | **72,537** | learned **CLS token** + sinusoidal positional encoding + **2** `TransformerEncoderLayer` (d_model 64, **4 heads**, ffn 128, dropout 0.3) | the CLS output; `src_key_padding_mask` over `length+1` masks padding |

`d_model` is constrained to be divisible by 4 (the Transformer's `nhead = 4`).
Padding handling differs by family — the LSTM packs, the CNN length-masks before
pooling, and the Transformer masks the padded keys (and the extra CLS position) — so
none of the models read the zero-padding as signal.

### 4.2 Shared training protocol

Identical across all runs (`sequence_pipeline.py → train_model`):

| Knob | Value |
|------|-------|
| Optimizer | **Adam**, lr **1e-3** |
| LR schedule | **`ReduceLROnPlateau` on validation AUC** (mode `max`, patience 5, factor 0.5) |
| Early stopping | **patience 15** on best **validation AUC**; checkpoint saved at best val AUC |
| Max epochs | 100 (early stop almost always fires first — observed 16–48 epochs) |
| Gradient clipping | global-norm **1.0** |
| Batch size | 32 |
| Seed | **100** (Python / NumPy / Torch) → reproducible |
| Sequence length | `max_seq_len = 256` (median session ≈ 236 syllables, P95 ≈ 704) |
| Loss | `BCEWithLogitsLoss` with **`pos_weight = n_WT / n_HT`** on the train split (≈ 3.2) |
| Scaling | `StandardScaler` on the 4 continuous features, **fit on train only** |
| Split | 60/20/20, two modes: **dependent** (random session-level, mice leak) and **independent** (`--independent`, split by mouse, leak-free) |

Model selection is on **validation AUC**, not accuracy — a deliberate choice because
accuracy is uninformative under 76/24 imbalance, and because (as §4.3 shows) the
ranking quality and the operating point diverge sharply on this data.

### 4.3 The degenerate-collapse problem

At the **default 0.5 decision threshold** the sequence models repeatedly **collapse to
predicting a single class for every test session**. The mechanism, diagnosed in
`docs/NEURAL_NETWORK_BASELINE.md` §9, is *operating-point collapse, not loss of
ranking*: the `pos_weight ≈ 3.2` rebalancing term pushes the logit bias so far toward
the HT minority that the 0.5 cut lands on the wrong side of every score.

The signature is unmistakable in the **BiLSTM dependent baseline**
(`bilstm_subject_eval_dependent_baseline`): it predicts **HT for every one of the 82
test sessions** — HT recall **1.000**, WT recall **0.000**, WT F1 **0.000** — so
accuracy collapses to exactly the HT base rate, **0.232**. Yet its **test AUC is
0.790** (best val AUC 0.778): the ranking carries real signal, only the threshold is
broken. Train mirrors test (train acc 0.242), so this is a *stuck operating point*,
not overfitting.

Collapse appears in **both directions** depending on the lever:

- **All-HT collapse** — the default `pos_weight` runs (BiLSTM dependent acc 0.232,
  BiLSTM independent acc 0.456 with 49 of 71 WT sessions misrouted to HT).
- **All-WT collapse** — over-regularization or weak rebalancing tips the *other* way.
  `F_regsmall__transformer__independent` predicts **WT for all 90 test sessions** (HT
  recall **0.000**), and its **0.789 "accuracy" is just the 79 % WT majority** —
  balanced accuracy **0.500**, MCC **0.000**. This run has the matrix's **highest AUC
  (0.815) and PR-AUC (0.616)** while being useless at 0.5: the strongest possible
  proof that collapse is a *thresholding/calibration* failure, not a no-signal
  failure.

This is exactly why every run reports **balanced accuracy, PR-AUC, MCC, and macro-F1**
alongside accuracy, and why threshold tuning is pursued as a separate workstream
(Issue #29; out of scope here but see `results/tabular_models/threshold*`).

### 4.4 The six baseline runs

Three architectures × two split modes, all on the `--baseline` dataset
(`all_data_external_baseline.xlsx`, syllable-level, with the official baseline filters;
`docs/preprocessing_pipeline.md` §2.5). Source:
[`results/neural_networks/executive_summaries/sequence_models/master_metrics.md`](../results/neural_networks/executive_summaries/sequence_models/master_metrics.md)
and the per-run READMEs.

| Model | Split | Test Acc | Test AUC | HT P/R/F1 | WT R | WT F1 | Epochs | Note |
|-------|-------|---------:|---------:|-----------|------:|------:|-------:|------|
| BiLSTM | dependent | **0.232** | 0.790 | 0.232 / **1.000** / 0.376 | 0.000 | 0.000 | 16 | all-HT collapse |
| BiLSTM | independent | 0.456 | 0.749 | 0.279 / **1.000** / 0.437 | 0.310 | 0.473 | 16 | near-all-HT collapse |
| 1D-CNN | dependent | 0.500 | 0.604 | 0.271 / 0.684 / 0.388 | 0.444 | 0.577 | 22 | weak both ways |
| 1D-CNN | independent | 0.633 | 0.609 | 0.231 / 0.316 / 0.267 | 0.718 | 0.756 | 17 | HT fails (6/19 caught) |
| Transformer | dependent | **0.659** | 0.655 | 0.371 / 0.684 / 0.481 | 0.651 | 0.745 | 31 | best baseline; no collapse |
| Transformer | independent | 0.544 | 0.675 | 0.288 / 0.789 / 0.423 | 0.479 | 0.624 | 29 | minority-leaning tilt |

Reading the table:

- **BiLSTM** has the **best ranking** (AUC 0.790 / 0.749) but the **worst operating
  point** — it collapses to all-HT under both splits, so its high AUC never converts to
  usable accuracy at 0.5.
- **1D-CNN** is the weakest by AUC (0.604 / 0.609 — barely above chance). It avoids the
  hard all-one-class collapse but the minority class fails on its own merits
  (independent HT recall **0.316**, catching only 6 of 19 ASD-model test sessions).
- **The Transformer is the only architecture that never collapses.** Both classes are
  predicted under both splits, and the dependent run (acc **0.659**, HT F1 0.481) is the
  strongest of the six. Even so it is **below the dependent tabular base on every
  headline metric** (acc −0.074, weighted F1 −0.065, HT F1 −0.168 vs the 0.733 / 0.749 /
  0.649 anchor), despite the leaky split that should flatter it — the per-syllable
  sequence view does not beat 48 aggregated features here.

The shared cause is **data scarcity at the subject level**: the independent splits
leave only ~238 train / ~80 val / ~90 test sessions across ~63 train mice (56 HT train sessions), and
the test fold carries only ~19 HT sessions — far too few to calibrate a decision head.
Train accuracies (0.24–0.73) are themselves low, so these are **under-fit / mis-calibrated**
models, not over-fit ones.

### 4.5 The A–H imbalance-experiment matrix

The collapse motivated a structured sweep of imbalance-handling levers
(`docs/NEURAL_NETWORK_BASELINE.md` §9). Each lever is run with `--baseline`, both
split modes, under `results/neural_networks/experiments/`; ranked by **balanced
accuracy / MCC / PR-AUC** (never accuracy) in
[`results/neural_networks/experiments/_summary/master_metrics.md`](../results/neural_networks/experiments/_summary/master_metrics.md).

| Lever | Flags | What it targets | Key result / finding |
|-------|-------|-----------------|----------------------|
| **A — control** | (defaults: `pos_weight_beta 1.0`, BCE) | the as-shipped baseline operating point | The Transformer is **already at its best under A** (dependent balAcc **0.668**, independent **0.634**) — rebalancing does not help it. BiLSTM A collapses (dependent balAcc 0.500). |
| **B — milder weight** | `--pos-weight-beta 0.5` | soften the `pos_weight` push that causes all-HT collapse | Mixed: lifts some Transformer independent PR-AUC (0.531) but `B__transformer__dependent` and `B__bilstm__dependent` **collapse to all-WT** (balAcc 0.500, HT recall 0.0). Not a reliable fix. |
| **C — no weight** | `--pos-weight-beta 0` (`pos_weight = 1`) | remove rebalancing entirely | Generally drifts toward the majority — BiLSTM dependent balAcc 0.568, `C__cnn1d__dependent` collapses all-WT (balAcc 0.492, MCC −0.06). |
| **D — balanced sampler** | `--sampler balanced --pos-weight-beta 0` | balanced minibatches → balanced base rate | **The most reliable fix.** Rescues the BiLSTM all-HT collapse (dependent balAcc **0.500 → 0.628**, WT recall 0 % → 73 %) and gives the matrix's **best single result** (`D__bilstm__independent` balAcc **0.704**, AUC 0.767). |
| **E — focal loss** | `--loss focal` (`beta 0`, γ 2.0) | confidence-based, gentler rebalancing | Underwhelming — `E__bilstm__dependent` balAcc 0.523, `E__bilstm__independent` 0.491 (MCC −0.03). Run for BiLSTM only. |
| **F — regularized-small** | `--weight-decay 1e-3 --dropout 0.5 --hidden-size 32 --num-layers 1` (`beta 0.5`) | overfitting on the tiny independent split | Best **1D-CNN independent** config (balAcc 0.607). But `F__transformer__independent` posts the **highest AUC 0.815 / PR-AUC 0.616 with balAcc 0.500** — strong ranking, all-WT collapse at 0.5 (the §4.3 calibration case). |
| **G — augmentation** | `--augment-windows 4 --window-stride 128` (`beta 0.5`) | more (esp. HT) training windows from long sessions | Modest at best — `G__bilstm__dependent` balAcc 0.571, `G__bilstm__independent` 0.582; `G__cnn1d__independent` is the matrix's worst (balAcc 0.475, AUC 0.449). Run for BiLSTM/CNN. |
| **H — 5-fold CV** | `--cv-folds 5` (re-runs the D recipe) | a stable estimate of the D winner given only ~19 test HT | **Deflates the headline.** The independent single-split **0.704 does not hold**: 5-fold balAcc is **0.563 ± 0.063** (per-fold AUC 0.556–0.825). The dependent fix *is* robust (0.609 ± 0.055). |

**Best config per model × split (by balanced accuracy):**

| Model | Split | Best config | Bal Acc | vs control | HT rec / WT rec |
|-------|-------|-------------|--------:|-----------:|-----------------|
| BiLSTM | dependent | `D` balanced sampler | 0.628 | **0.500 → 0.628** (collapse fixed) | 0.53 / 0.73 |
| BiLSTM | independent | `D` balanced sampler | **0.704** | 0.655 → 0.704 | 1.00 / 0.41 |
| 1D-CNN | dependent | `D` balanced sampler | 0.594 | 0.564 → 0.594 | 0.47 / 0.71 |
| 1D-CNN | independent | `F` regularized-small | 0.607 | 0.517 → 0.607 | 0.37 / 0.85 |
| Transformer | dependent | `A` control | 0.668 | (already best) | 0.68 / 0.65 |
| Transformer | independent | `A` control | 0.634 | (already best) | 0.79 / 0.48 |

**Takeaways:**

- **D (balanced sampler) is the most reliable collapse fix.** Pairing a
  `WeightedRandomSampler` for ~50/50 minibatches with `pos_weight_beta = 0` (so the
  imbalance is not corrected twice) is the only lever that consistently rescues the
  all-one-class collapse and tops the dependent-BiLSTM and both-BiLSTM rankings.
- **The Transformer needs no rebalancing.** Control is already its best; the levers
  built to fix collapse can instead *induce* it (the opposite, all-WT collapse) on a
  model that was already calibrated.
- **Ranking ≠ operating point.** The highest-AUC run in the entire matrix
  (`F__transformer__independent`, AUC 0.815) has balanced accuracy 0.500 — the clearest
  motivation for the separate threshold-tuning work (Issue #29).

### 4.6 H: cross-validation shows the independent win is a lucky-fold artifact

Lever H re-runs the winning D recipe (balanced-sampler BiLSTM) as **5-fold CV** —
grouped by mouse for the independent split — so the headline is an out-of-fold estimate
over all 408 sessions rather than one test split. The result is the single most
important methodological finding for the sequence track:

| Split | 5-fold balanced accuracy (mean ± std) | 5-fold AUC | Single-split was |
|-------|---------------------------------------|-----------|------------------|
| dependent | **0.609 ± 0.055** | 0.673 ± 0.067 | 0.628 — **confirmed** (vs 0.500 collapse) |
| independent | **0.563 ± 0.063** | 0.689 ± 0.089 | 0.704 — **optimistic / lucky fold** |

The **dependent fix is real and robust** (0.609 ± 0.055, comfortably above the 0.500
all-HT collapse). But the headline **independent 0.704 does not survive
cross-validation** — with only ~19 HT sessions in any one test fold it was a lucky
draw; the honest out-of-fold estimate is **0.563 ± 0.063**. The per-fold instability is
extreme: in `H_cv_Dsampler__bilstm__independent`, fold accuracy spans **0.284 → 0.753**
and AUC **0.556 → 0.825** across only ~81 test sessions per fold, while OOF AUC sinks to
0.586. The same picture holds dependent (per-fold accuracy 0.354 → 0.765, std 0.144).

The conclusion the doc series should carry forward: **subject-independent generalization
of the sequence models is genuinely limited by the data, not by configuration.** With
408 sessions from 106 mice (only ~24 HT mice), which mice land in a fold dominates the
result more than the recipe does. Report the **CV numbers**, not the best single fold,
and for any honest "new-mouse" estimate prefer the subject-independent **tabular** runs
(`results/tabular_models/`) — the sequence models, in their current data-limited regime,
do not beat the recording-level base model anchor.

> **For the paper.** Frame the sequence models as a **representation study under a hard
> data ceiling**, not as a winning classifier. Three reportable facts: (1) the default
> `pos_weight` configuration **collapses to one class at the 0.5 threshold** while the
> AUC stays at 0.60–0.79 — a calibration failure, not a no-signal failure; (2) a
> **balanced minibatch sampler** is the most reliable training-time fix; (3) **5-fold
> CV deflates the best independent single-split result (0.704 → 0.563 ± 0.063)**,
> demonstrating that the apparent wins are fold artifacts of a 408-session / ~24-HT-mouse
> corpus. All sequence metrics are **session-level** and so are **not directly
> comparable** to the recording-level tabular base (Test Acc 0.733); see
> `docs/preprocessing_pipeline.md` §4 for the methodological note on why head-to-head
> accuracy comparisons across the two tracks compare *representation + model*, not pure
> models.

### 4.7 Code-path index (for citation/verification)

| Component | File | Key symbols |
|-----------|------|-------------|
| Pipeline (data, models, training, CLI) | `src/classification/neural_networks/sequence_pipeline.py` | `load_and_prepare`, `USVSequenceDataset`, `BiLSTMClassifier`, `CNN1DClassifier`, `TransformerClassifier`, `make_criterion`, `SequenceLoss`, `train_model`, `run_cross_validation`, `make_train_loader` |
| Baseline / levers narrative | `docs/NEURAL_NETWORK_BASELINE.md` | split modes, lever table A–H, findings, CV verification |
| Data construction (sequence track) | `docs/preprocessing_pipeline.md` §3–§4 | grain, 14-d step, embedding, scaling, split |
| Six baseline runs | `results/neural_networks/{bilstm,cnn1d,transformer}_subject_eval_{dependent,independent}_baseline/` | `README.md`, `results.json`, `logs/out.txt` |
| Baseline roll-up | `results/neural_networks/executive_summaries/sequence_models/master_metrics.md` | per-run summary table |
| A–H experiments | `results/neural_networks/experiments/{A..H}_*__{bilstm,cnn1d,transformer}__{dependent,independent}/` | per-run `README.md` + `results.json` (`config` block) |
| Experiment roll-up | `results/neural_networks/experiments/_summary/master_metrics.md` | matrix ranked by balanced accuracy |
| Summary generator | `scripts/generate_nn_executive_summary.py` | `--strict`, `--results-root`, `--out-dir` |

---

## 5. Decision-threshold tuning (operating-point selection)

The tabular base model — `xgboost_subject_eval_dependent_baseline` — reports its
test metrics at the hard-coded **0.5** probability cut: Test Acc **0.733**,
Weighted F1 **0.749**, with a lopsided per-class split (WT P/R/F1
**0.968/0.660/0.785**, HT P/R/F1 **0.496/0.940/0.649**). That cut is an *arbitrary*
operating point, not a tuned one. On this task it is also a *poor* one, for two
reasons that compound:

1. **Class imbalance.** HET/HT is a ~24% minority (see
   [`preprocessing_pipeline.md`](preprocessing_pipeline.md) §0). A 0.5
   cut on a model trained with imbalance-aware weighting leaves the decision
   boundary in the wrong place for the prior — typically pulling far too many WT
   recordings across into HT (low HT precision, low WT recall on dependent
   splits) or, conversely, *under*-detecting HT on the harder independent splits.
2. **The probabilities are well-separated, but 0.5 doesn't exploit it.** Test AUC
   is high on the dependent splits (**0.876–0.908**), meaning the model *ranks* WT
   vs HT well; the ranking just isn't being thresholded at the point that
   converts that ranking into the operating point you actually want.

Threshold tuning is therefore the cheapest possible lever: it changes *one
scalar* — where on the probability axis we cut — and leaves the trained model,
its features, and its probabilities completely untouched. Resolves Issues #29 /
#51 (Youden adoption) and #73 (objective comparison).

### 5.1 Method — derive on validation, apply to test, no retraining

The procedure is deliberately leak-free and retrain-free:

1. **Score validation.** Take the trained model's per-recording `P(HT)` on the
   **validation** split — a partition the model never trained on. These are the
   `probabilities_val.csv` files committed under each run.
2. **Derive the threshold** from those validation probabilities, by an explicit
   objective (Youden's *J* = max TPR − FPR for the headline runs; §5.3 covers the
   alternatives).
3. **Apply that fixed threshold to test.** Score the held-out **test** split
   (`probabilities_test.csv`), apply the validation-derived cut, and report
   metrics at **both 0.5 and the tuned cut** side by side.

The test set never participates in choosing the threshold, so the tuned numbers
are an honest estimate of how the chosen operating point generalizes. AUC is
reported as a sanity anchor and is **threshold-independent** — it is identical at
0.5 and at the tuned cut, because it is a property of the ranking, not the cut.

> **For the paper.** Threshold selection is a post-hoc calibration of the
> *operating point*, not a model change. The classifier, its features, and its
> output probabilities are byte-for-byte identical across all thresholds; only
> the scalar decision boundary moves. The cut is chosen on validation
> probabilities the model never trained on and then *frozen* before touching
> test — the standard leak-free protocol. No gradient step, no refit.

One subtlety for **TabPFN**: in normal (non-threshold) mode the project merges
the validation split back into TabPFN's in-context training set (it has no
trainable weights, so val is "free" data). In **threshold** mode TabPFN keeps
its validation split **held out** so the val probabilities are genuinely
leak-free for deriving the cut. This run therefore trains on ~60% of the data
instead of ~80%, so its `@0.5` numbers differ *slightly* from the non-threshold
TabPFN run — a protocol difference, not a regression
(`threshold/tabpfn_subject_eval_dependent_baseline/threshold_report.txt`).

The whole matrix is reproducible (`seed=100`):

```bash
python scripts/run_threshold_matrix.py                  # all 6 runs, Youden
python scripts/run_threshold_matrix.py --objective f1   # any other objective
```

Curated outputs and the regeneration recipe live in
[`results/tabular_models/threshold/README.md`](../results/tabular_models/threshold/README.md).

### 5.2 Results — 0.5 vs tuned (Youden)

Six runs cover the cross-product of {XGBoost (default), XGBoost (tuned), TabPFN}
× {subject-dependent, subject-independent}. The dependent/independent split
distinction is defined in
[`preprocessing_pipeline.md`](preprocessing_pipeline.md) — dependent lets
the same mouse appear across train/test (optimistic), independent groups by
mouse identity (honest new-mouse estimate). Source:
[`threshold/summary_matrix.txt`](../results/tabular_models/threshold/summary_matrix.txt).

| Run | tuned thr | test AUC | acc 0.5 → tuned | bal-acc 0.5 → tuned | HT recall 0.5 → tuned | HT prec 0.5 → tuned | WT recall 0.5 → tuned |
|---|---|---|---|---|---|---|---|
| xgboost / dependent | 0.528 | 0.876 | 0.727 → **0.737** | 0.795 → 0.794 | 0.937 → 0.915 | 0.490 → 0.499 | 0.653 → 0.673 |
| xgboost / independent | 0.128 | 0.770 | 0.692 → 0.705 | 0.678 → **0.797** | 0.646 → 0.998 | 0.452 → 0.478 | 0.710 → 0.596 |
| xgboost_tuned_dep / dependent | 0.366 | 0.885 | **0.771** → 0.731 | 0.798 → 0.800 | 0.856 → 0.947 | 0.540 → 0.493 | 0.740 → 0.653 |
| xgboost_tuned_indep / independent | 0.288 | 0.753 | 0.695 → 0.704 | 0.725 → **0.797** | 0.791 → 1.000 | 0.463 → 0.477 | 0.660 → 0.594 |
| tabpfn / dependent | 0.454 | 0.908 | **0.783** → 0.766 | **0.828** → 0.822 | 0.921 → 0.938 | 0.552 → 0.531 | 0.734 → 0.705 |
| tabpfn / independent | 0.005 | 0.783 | 0.713 → 0.703 | 0.662 → **0.796** | 0.551 → 0.998 | 0.474 → 0.477 | 0.773 → 0.594 |

Two regimes fall out cleanly:

- **Dependent splits (high AUC, already well-balanced at 0.5).** Youden moves the
  cut only modestly and buys little. For TabPFN it actually *lowers* the cut to
  0.454 and trades −0.017 accuracy / −0.029 WT recall for +0.017 HT recall — the
  model was already HT-aggressive at 0.5
  (`threshold/tabpfn_subject_eval_dependent_baseline/README.md`). For
  XGBoost-tuned-dependent, Youden drops the cut to 0.366 and *costs* accuracy
  (0.771 → 0.731) while pushing HT recall 0.856 → 0.947. Balanced accuracy is
  essentially flat across the move (≈0.79–0.83 either way). **Youden is roughly a
  wash on dependent splits.**

- **Independent splits (weak AUC ~0.75–0.78).** Here Youden's effect is dramatic
  and *degenerate*. Because the positive class barely separates, the J-maximizing
  cut collapses to a near-zero threshold (0.128, 0.288, **0.005**) that predicts
  HT for almost everyone: HT recall jumps to **0.998–1.000** while WT recall
  craters to ~**0.59**. Balanced accuracy "improves" to ~0.797 only because it
  averages a recall of ~1.0 against ~0.59 — it is a *book-keeping* gain, not a
  useful classifier. The tabpfn / independent confusion matrix at Youden is the
  clearest tell: `[[926, 634], [1, 578]]` — it lets **1** true HT through and
  misclassifies **634** WT as HT
  (`threshold_objectives/tabpfn_subject_eval_independent_baseline/objective_comparison.txt`).

> **⚠️ Balanced-accuracy trap on independent splits.** A jump from bal-acc 0.662
> to 0.796 (tabpfn / independent) looks like a win but is a degenerate
> "predict-HT-for-everyone" point (HT recall ~1.0, WT recall ~0.59). Always read
> *both* per-class recalls before adopting a Youden cut on a weak-AUC split. This
> is exactly what motivated the objective comparison in §5.3.

> **For the paper.** Best single tabular operating point is **TabPFN /
> dependent**: at its default 0.5 cut it already beats the XGBoost base on every
> headline metric — Test Acc **0.783** vs 0.733, balanced accuracy **0.828**,
> weighted F1 **0.794** — at AUC **0.908**, while *matching* HT recall (0.938 vs
> the base's 0.940) with better HT precision (0.531 vs 0.496) and far fewer WT
> false positives. The limiting factor is HT precision (~0.53 — about half of HT
> calls are false positives), which no threshold move can fix; that is a feature
> ceiling, not an operating-point problem.

### 5.3 Objective comparison — choosing *how* to cut

Youden is one objective; it is not always the right one (§5.2 showed it
degenerates on weak-AUC splits). Because the threshold only selects a point on
already-saved, objective-*independent* probabilities, comparing objectives needs
**no retraining at all** — the comparison reads each run's
`probabilities_{val,test}.csv` and re-derives every cut. A self-check confirms
the recomputed Youden numbers match the stored full-run metrics exactly (delta
0.0) for all 6 runs, and the whole sweep runs instantly instead of ~4h of TabPFN
CPU inference
([`threshold_objectives/README.md`](../results/tabular_models/threshold_objectives/README.md)):

```bash
python scripts/compare_threshold_objectives.py                  # instant, from saved probabilities
python scripts/compare_threshold_objectives.py --target-recall 0.85
```

Five operating points are compared per run — `0.5` (default), `youden`, `f1`
(maximize HT F1), `target_recall` (lowest cut keeping HT recall ≥ **0.80**), and
`balanced`. Source:
[`threshold_objectives/summary_objectives.txt`](../results/tabular_models/threshold_objectives/summary_objectives.txt)
(target_recall floor = 0.80).

**Subject-dependent runs (test set):**

| Run | Objective | thr | acc | bal-acc | HT rec | HT prec | WT rec |
|---|---|---|---|---|---|---|---|
| xgboost / dep | @0.5 | 0.500 | 0.727 | 0.795 | 0.937 | 0.490 | 0.653 |
| | youden | 0.528 | 0.737 | 0.794 | 0.915 | 0.499 | 0.673 |
| | **f1** | 0.617 | 0.767 | 0.774 | 0.788 | 0.538 | 0.759 |
| | target_recall | 0.630 | **0.778** | 0.776 | 0.771 | 0.555 | 0.780 |
| xgboost_tuned_dep / dep | @0.5 | 0.500 | 0.771 | 0.798 | 0.856 | 0.540 | 0.740 |
| | youden | 0.366 | 0.731 | 0.800 | 0.947 | 0.493 | 0.653 |
| | **f1** | 0.568 | **0.789** | 0.787 | 0.784 | 0.572 | 0.791 |
| | target_recall | 0.547 | 0.785 | 0.792 | 0.808 | 0.562 | 0.776 |
| tabpfn / dep | @0.5 | 0.500 | 0.783 | 0.828 | 0.921 | 0.552 | 0.734 |
| | youden | 0.454 | 0.766 | 0.822 | 0.938 | 0.531 | 0.705 |
| | **f1** | 0.617 | **0.819** | 0.817 | 0.811 | 0.619 | 0.822 |
| | target_recall | 0.617 | **0.819** | 0.817 | 0.811 | 0.619 | 0.822 |

On dependent splits `f1` (and the closely-tracking `target_recall`) is the clear
winner: it *raises* the cut into the well-separated region and delivers the best
accuracy of any objective. TabPFN / dependent under `f1` reaches **acc 0.819,
bal-acc 0.817, HT precision 0.619, WT recall 0.822** — i.e. it nearly closes the
HT-precision gap while keeping HT recall a healthy 0.811, the most *balanced*
operating point in the whole matrix (tabpfn dep acc 0.78 → 0.82). Youden, by
contrast, lowers the cut and over-pushes HT recall at the cost of accuracy.

**Subject-independent runs (test set):**

| Run | Objective | thr | acc | bal-acc | HT rec | HT prec | WT rec |
|---|---|---|---|---|---|---|---|
| xgboost / indep | @0.5 | 0.500 | 0.692 | 0.678 | 0.646 | 0.452 | 0.710 |
| | youden | 0.128 | 0.705 | 0.797 | 0.998 | 0.478 | 0.596 |
| | f1 | 0.128 | 0.705 | 0.797 | 0.998 | 0.478 | 0.596 |
| | **target_recall** | 0.439 | 0.704 | 0.728 | 0.779 | 0.472 | 0.676 |
| xgboost_tuned_indep / indep | @0.5 | 0.500 | 0.695 | 0.725 | 0.791 | 0.463 | 0.660 |
| | youden | 0.288 | 0.704 | 0.797 | 1.000 | 0.477 | 0.594 |
| | f1 | 0.288 | 0.704 | 0.797 | 1.000 | 0.477 | 0.594 |
| | **target_recall** | 0.523 | 0.694 | 0.706 | 0.731 | 0.459 | 0.681 |
| tabpfn / indep | @0.5 | 0.500 | 0.713 | 0.662 | 0.551 | 0.474 | 0.773 |
| | youden | 0.005 | 0.703 | 0.796 | 0.998 | 0.477 | 0.594 |
| | f1 | 0.005 | 0.703 | 0.796 | 0.998 | 0.477 | 0.594 |
| | **target_recall** | 0.095 | 0.687 | 0.742 | 0.864 | 0.458 | 0.621 |

On independent splits, `youden`, `f1`, and `balanced` all **collapse to the same
near-degenerate point** (cut ≈ 0.005–0.288, HT recall ≈ 1.0, WT recall ≈ 0.59) —
because the weak AUC means the F1-maximizing and J-maximizing thresholds both sit
at the "predict-HT" extreme. Only `target_recall` resists this: by *floor*-ing HT
recall at 0.80 rather than maximizing it, it selects a meaningfully higher cut
(0.439 / 0.523 / 0.095) that keeps WT recall in the 0.62–0.68 range and HT recall
in the controlled 0.73–0.86 band. It trades a little headline accuracy for an
operating point that is actually deployable.

> **For the paper.** The right objective is split-dependent.
> - **Subject-dependent (high AUC):** adopt **`f1`** — it places the cut in the
>   separated region and maximizes accuracy/balance (e.g. TabPFN dep `f1`: acc
>   **0.819**, bal-acc 0.817, HT prec 0.619). Youden buys nothing here.
> - **Subject-independent (weak AUC ~0.75–0.78):** adopt **`target_recall`
>   (≈0.80 floor)** — it is the *only* objective that avoids the degenerate
>   predict-HT-for-everyone collapse and holds a controlled operating point.
> Full writeup in Issue #73; curated comparison in
> [`results/tabular_models/threshold_objectives/README.md`](../results/tabular_models/threshold_objectives/README.md).

### 5.4 Takeaways

- Threshold tuning is a **free, leak-free lever**: one scalar, no retraining,
  validation-derived, test-frozen. It cannot raise AUC or fix the ~0.53 HT
  precision ceiling — those are feature/model properties — but it *does* let you
  pick the operating point your application needs.
- On the **well-separated dependent** splits, `0.5` is already a decent cut and
  `f1` is a small genuine improvement; **Youden is essentially a wash** and
  sometimes a small loss.
- On the **weak independent** splits, the imbalance-sensitive objectives
  (`youden`/`f1`/`balanced`) degenerate; **`target_recall` is the only safe
  choice**, and the high "balanced accuracy" of the degenerate cuts is a trap, not
  a result.
- The strongest tabular operating point overall is **TabPFN / dependent under
  `f1`** (acc 0.819, bal-acc 0.817, weighted-balanced HT prec 0.619 / WT rec
  0.822) — comfortably above the base model's 0.733 / 0.749, though still on the
  optimistic dependent split.

---

## 6. Strain-cohort experiments

The base model and every full-corpus run pool **all** post-baseline years into one training
set. That is convenient but rests on an unverified assumption: that the lab's two animal
cohorts are acoustically interchangeable. They are not obviously so — they differ in *year*,
in *genetic background*, and in pool size. This section trains the same tabular recipes on
each cohort **alone** to test that assumption, and finds a strong cohort × split interaction
that argues against blind pooling.

> **For the paper.** This is the cohort-generalization experiment. The headline is not a
> single accuracy number but an *interaction*: strain1 generalizes to unseen mice while
> strain2 collapses on the minority class. Report it as evidence the two cohorts are not a
> single homogeneous population — the pooled corpus mixes them.

### 6.1 What the two cohorts are

The official cohort definitions live in [`COHORT_DEFINITIONS.md`](COHORT_DEFINITIONS.md)
(Issue #47 / #42), and the year→strain rule is `STRAIN_1_YEARS = {2022, 2023, 2024}` in
`src/preprocessing/utils/io_utils.py` (`strain_from_year()`), with the text→numeric mapping
applied in `extract_features.py`. The `Strain` column itself is described in
[`segmentation_process.md`](segmentation_process.md) §6 (#17): a text label
(`BALB/C` vs `BALB/C+BLACK/C57`) written by enrichment, then **overwritten** with a numeric
strain id (1/2) at tabular feature-extraction time.

| Cohort | CLI filter | Years | Background | `pup_strain` | Baseline recordings | Mice |
|---|---|---|---|---|---|---|
| **strain1** | `--baseline --strain 1` | 2022, 2023, 2024 | mixed `BALB/C+BLACK/C57` (newer litters) | 1 | 7,572 / 12,323 | 59 |
| **strain2** | `--baseline --strain 2` | 2015, 2018 | pure `BALB/c` (classic published cohort) | 2 | 4,751 / 12,323 | 47 |

Both subsets are drawn from the *same* official baseline (Issue #46 filters + the April-2026
HET→WT genotype correction — [`segmentation_process.md`](segmentation_process.md) §9.7); the
only change is the `--strain` row filter applied at train time. There is no separate
per-cohort CSV — filtering happens at `extract_features.py`. Class balance is similar in both
(HT ≈ 22 % in strain1, ≈ 28 % in strain2), so the imbalance levers differ only slightly
(`scale_pos_weight` ≈ 3.51–3.53 for strain1, ≈ 2.45–2.47 for strain2).

The two cohorts therefore confound **three** things at once — year, genetic background, and
pool size (strain1 is ~1.6× the recordings and 12 more mice). Keep that in mind reading the
deltas below: a "strain effect" here is really a "newer-and-larger-and-mixed-background vs
older-and-smaller-and-pure-BALB/c" effect.

### 6.2 The 12-run matrix

The design is **3 models × 2 strains × 2 evaluation splits** (`results/tabular_models/strain/README.md`):

- **Models:** `xgboost` (untuned legacy recipe), `xgboost_tuned_dependent` (the dependent-tuned
  XGBoost), `tabpfn`.
- **Splits:** *dependent* (default; row-level random split — mice leak across train/val/test,
  optimistic) and *independent* (`--independent`; group split by `mouse_idx` — the honest
  generalize-to-unseen-mice metric). Split semantics are the same as the full-corpus runs
  (see [`preprocessing_pipeline.md`](preprocessing_pipeline.md) on the aggregation unit and
  subject grouping).

All metrics below are **test-set** values read from each run's own
`comparison_vs_baseline.txt` *run column* and `logs/out.txt`. The `baseline: 0.829` figure
inside those files is a stale legacy reference, **not** our base model, and is ignored
throughout — the Δ columns are against the real base model
(`results/tabular_models/xgboost_subject_eval_dependent_baseline`: Test Acc **0.733**,
Weighted F1 **0.749**, HT F1 **0.649**).

| Model | Strain | Split | Test Acc | Train Acc | Weighted F1 | WT F1 | HT P | HT R | HT F1 |
|---|---|---|---|---|---|---|---|---|---|
| xgboost | 1 | dependent | 0.774 | 0.811 | 0.791 | 0.832 | 0.512 | 0.919 | 0.657 |
| xgboost | 1 | **independent** | **0.903** | 0.793 | **0.909** | 0.939 | 0.648 | 0.900 | **0.753** |
| xgboost | 2 | dependent | 0.748 | 0.845 | 0.759 | 0.805 | 0.532 | 0.808 | 0.642 |
| xgboost | 2 | **independent** | 0.657 | 0.916 | 0.609 | 0.787 | 0.194 | 0.089 | **0.122** |
| xgboost_tuned_dep | 1 | dependent | 0.789 | 0.903 | 0.802 | 0.849 | 0.533 | 0.829 | 0.649 |
| xgboost_tuned_dep | 1 | **independent** | 0.899 | 0.903 | 0.903 | 0.938 | 0.655 | 0.821 | **0.729** |
| xgboost_tuned_dep | 2 | dependent | 0.783 | 0.924 | 0.790 | 0.842 | 0.590 | 0.741 | 0.657 |
| xgboost_tuned_dep | 2 | **independent** | 0.653 | 0.950 | 0.597 | 0.786 | 0.140 | 0.057 | **0.081** |
| tabpfn | 1 | dependent | 0.785 | 0.847 | 0.801 | 0.838 | 0.523 | 0.969 | 0.680 |
| tabpfn | 1 | **independent** | 0.897 | 0.859 | 0.905 | 0.935 | 0.629 | 0.925 | **0.749** |
| tabpfn | 2 | dependent | 0.801 | 0.926 | 0.809 | 0.851 | 0.604 | 0.842 | 0.703 |
| tabpfn | 2 | **independent** | 0.654 | 0.941 | 0.659 | 0.759 | 0.369 | 0.410 | **0.388** |

> ⚠️ **Read the train/test gaps.** On strain2-independent the train accuracies are
> *high* (0.916 / 0.950 / 0.941) while test sits at ~0.65 — a 0.26–0.30 generalization gap.
> The models memorize their handful of training mice and fail on the held-out ones. On
> strain1-independent the opposite holds (e.g. untuned XGBoost trains at 0.793, tests at
> 0.903): no overfitting at all.

### 6.3 The cohort × split interaction

Model choice barely moves the needle inside a given cohort/split cell — the **cohort × split
interaction dominates**. Four facts:

**(a) Dependent splits are consistent across both strains.** Acc ≈ 0.75–0.80, HT F1 ≈ 0.64–0.70,
in line with the pooled base model (0.733 / 0.649). Both cohorts look "fine" on the leaky
split. Restricting to a single cohort even slightly *lifts* the headline vs the full base
(strain1 untuned +0.041 acc to 0.774; strain2 untuned +0.015 to 0.748), the cleaner
single-cohort signal more than paying for the smaller pool — but these numbers leak (the logs
warn 59/59/59 and 47/47/47 shared mice) and read optimistically.

**(b) strain1 independent is the standout — and it *inverts* the usual penalty.** Across all
three models the leak-free strain1 split lands at **~0.90 accuracy and 0.73–0.75 HT F1**,
*above* its own dependent split. That is the opposite of the normal dependent→independent
drop. Against the base model the untuned run is **+0.170 accuracy / +0.160 weighted F1**, and
the minority class improves on *both* sides of the trade-off — **HT precision +0.152 (to 0.648)**
with HT recall holding at 0.900 (−0.040). Confusion matrix `[[1276, 137], [28, 252]]`: only 28
of 280 true HT recordings missed. Two levers move together here — cohort narrows to strain1 *and*
the split goes independent — so the gain is "cleaner cohort beats harder split," not a
free generalization win.

**(c) strain2 independent collapses, concentrated in the minority class.** Same recipes, same
split logic, opposite outcome: acc drops to ~0.65 and **HT F1 falls to 0.08–0.39**. The untuned
XGBoost is the worst, HT recall 0.089 / precision 0.194 / F1 0.122 — confusion matrix
`[[745, 116], [287, 28]]`: of 315 true HT recordings, **287 are called WT and only 28 caught**. The
tuned XGBoost is no better (HT F1 0.081, recall 0.057). The classifier simply defaults to the
WT majority on the held-out mice. The 0.65 headline accuracy is an artifact of the ~73 % WT
base rate plus WT recall ~0.87; weighted F1 (0.597–0.659) exposes the real failure.

**(d) The collapse is a small-cohort, leak-free-split problem.** strain2 has only 47 mice;
the by-mouse split leaves ~10 test mice and too few held-out HT animals for a stable
estimate. TabPFN degrades **least** (HT F1 0.388) and the tuned XGBoost **most** (0.081) — the
ordering you expect when the limiting factor is data quantity, not model family: TabPFN's
in-context Bayesian fit tolerates tiny pools better than a gradient-boosted ensemble that can
memorize 27 training mice (train 0.95). At the default 0.5 cut HT is effectively undetected;
threshold tuning (the `threshold/` and `threshold_objectives/` runs) cannot rescue it without
first fixing the collapse, since HT precision is already ~0.19.

| Split | strain1 (mean over 3 models) | strain2 (mean over 3 models) |
|---|---|---|
| dependent — Acc | ~0.78 | ~0.78 |
| dependent — HT F1 | ~0.66 | ~0.67 |
| independent — Acc | **~0.90** | **~0.65** |
| independent — HT F1 | **~0.74** | **~0.20** |

The two cohorts are indistinguishable on the leaky split and **maximally divergent** on the
honest one. That is the whole result.

### 6.4 The background-change caveat — what it implies for pooling

The cohort confound is not cosmetic. strain1 carries a **mixed `BALB/C+BLACK/C57` genetic
background** introduced in the 2022–2024 litters, whereas strain2 is **pure `BALB/c`**. Genetic
background is known to modulate the mouse USV repertoire independent of genotype, so the
acoustic feature distributions of the two cohorts may differ for reasons that have nothing to
do with the WT-vs-HET label this project predicts.

> ⚠️ **Background change is a confound for pooling years.** When the full corpus pools all
> years it silently mixes two genetic backgrounds. A model trained on the pool can exploit
> background-correlated acoustic differences that happen to align with cohort, and — because
> cohort correlates with year, recording rig era, and HT base rate — that signal can
> masquerade as a genotype signal. The pooled base model's metrics cannot, on their own,
> distinguish "learned the ASD phenotype" from "learned which cohort a recording came from."

Three implications worth stating in the methods/limitations section:

1. **Do not read strain1 and strain2 numbers across each other.** They are different
   populations on different rigs; the per-cohort runs are cohort-specific estimates, full stop.
   Use the strain1-independent run for any "new mouse on the 2022–2024 cohort" claim, and treat
   the strain2-independent run as evidence the small pure-BALB/c cohort is *too small for a
   leak-free minority estimate*, not as a generalization number to quote.
2. **The pooled corpus is the right default for raw performance, but the wrong evidence for a
   biological claim.** Pooling maximizes data and is defensible for the engineering metric;
   it is not clean for the scientific question "do Mthfr-ASD pups vocalize differently,"
   because background is not held constant.
3. **The honest test of a genotype signal is cross-cohort.** The strongest future experiment
   is train-on-one-cohort / test-on-the-other (or background as an explicit covariate /
   adversarial control), so a reported genotype effect survives the background switch. The
   current matrix only trains and tests *within* each cohort, so it cannot yet rule the
   confound out — it can only show the cohorts are not interchangeable.

**Bottom line.** The two strains agree on the leaky split and diverge sharply on the leak-free
one — strain1 generalizes (≈0.90 acc, HT F1 ≈0.74), strain2's minority class collapses (HT F1
≈0.08–0.39, a small-pool/leak-free-split artifact). Model family is second-order; the cohort ×
split interaction is first-order. Combined with the unequal genetic background, this is
direct evidence the cohorts should **not** be pooled blindly, and that any genotype claim
needs a cross-cohort, background-controlled test before it can be trusted.

**Regenerate:**
```bash
python src/classification/tabular/train_classifier.py --baseline --strain {1,2} [--independent] \
  --model {xgboost,xgboost_tuned_dependent,tabpfn}
```
Results land under `results/tabular_models/strain/<model>_strain{1,2}_subject_eval_{dependent,independent}_baseline/`.

---

## 7. Cross-model comparison & headline results

This section pulls the six model families onto a single page so they can be read
against each other and against the base model. Every number below is the **default
operating point** (probability threshold 0.5, no post-hoc calibration) on the
**pooled `--baseline` data** (Issue #46 filters; April-2026 HET→WT correction), taken
verbatim from the per-run `README.md` files and the master tables — never re-derived.
Threshold-tuned variants are summarized separately in §[threshold tuning] and are *not*
mixed into these tables.

Two caveats frame the whole comparison:

- **Two grains, not one.** The tabular models (XGBoost, XGBoost-tuned, TabPFN) classify
  **one recording** from a 48-column aggregated feature vector; the sequence models
  (BiLSTM, 1D-CNN, Transformer) classify **one isolation session** from an ordered
  syllable sequence (see [`preprocessing_pipeline.md`](preprocessing_pipeline.md) §0).
  The two families therefore have **different test-set sizes and different supports** —
  tabular test sets are ~2,100–2,500 recordings, sequence test sets are a few dozen
  sessions — so a sequence-model accuracy is *not* directly substitutable for a tabular
  one. Compare *families* and *trends*, not single decimals across the grain boundary.
- **Dependent ≠ honest.** Subject-**dependent** runs split rows randomly, so the same
  mouse leaks across train and test; they are an **optimistic ceiling**. Subject-**independent**
  runs split by mouse (group-aware) and are the honest "generalize to a new mouse" read.
  The base model is a *dependent* run, so it sits on the optimistic side by construction.

### 7.1 Subject-dependent (optimistic) — pooled baseline, threshold 0.5

| Model | Test Acc | Bal Acc / AUC | Weighted F1 | HT F1 | HT Recall |
|---|---|---|---|---|---|
| **xgboost** (base model) | **0.733** | 0.795 bal · 0.876 AUC | **0.749** | 0.649 | 0.940 |
| xgboost_tuned | 0.772 | 0.798 bal · 0.885 AUC | 0.785 | 0.661 | 0.844 |
| **tabpfn** | **0.781** | **0.828 bal · 0.908 AUC** | **0.794** | **0.688** | 0.918 |
| bilstm | 0.232 | 0.500 bal · 0.790 AUC | — | 0.38 | 1.000 |
| cnn1d | 0.500 | 0.564 bal · 0.604 AUC | — | 0.39 | 0.684 |
| transformer | 0.659 | 0.668 bal · 0.655 AUC | — | 0.48 | 0.684 |

> Tabular rows: base model, `xgboost_tuned_dependent`, `tabpfn` dependent READMEs (weighted F1
> and HT F1 reported there; balanced acc / AUC from `../threshold/summary_matrix.txt`, `acc.5`/`bal.5`/`tAUC`).
> Sequence rows: the `A_control` dependent configs in
> `results/neural_networks/executive_summaries/sequence_models/master_metrics.md`
> (BiLSTM 23.2% / AUC 0.790 / HT F1 0.38; 1D-CNN 50.0% / AUC 0.604 / HT F1 0.39;
> Transformer 65.9% / AUC 0.655 / HT F1 0.48). Sequence runs report **WT F1**, not an overall
> **weighted F1**, so that cell is "—"; balanced acc for the control rows is from the
> experiments master (`A_control__*__dependent`).

### 7.2 Subject-independent (honest, leak-free) — pooled baseline, threshold 0.5

| Model | Test Acc | Bal Acc / AUC | Weighted F1 | HT F1 | HT Recall |
|---|---|---|---|---|---|
| xgboost | 0.693 | 0.678 bal · 0.770 AUC | 0.706 | 0.529 | 0.637 |
| xgboost_tuned | 0.702 | 0.725 bal · 0.753 AUC | 0.719 | 0.612 | 0.869 |
| **tabpfn** | **0.729** | 0.662 bal · **0.783 AUC** | **0.743** | 0.610 | 0.782 |
| **bilstm** | 0.456 | **0.655 bal** · 0.749 AUC | — | **0.44** | 1.000 |
| cnn1d | 0.633 | 0.517 bal · 0.609 AUC | — | 0.27 | 0.316 |
| transformer | 0.544 | 0.634 bal · 0.675 AUC | — | 0.42 | 0.789 |

> Tabular rows: `xgboost`/`xgboost_tuned_independent`/`tabpfn` **independent** READMEs (test acc,
> weighted F1, HT F1, HT recall) with bal acc / AUC from `summary_matrix.txt`. Sequence rows:
> the `A_control` independent configs in the sequence master (BiLSTM 45.6% / bal 65.5% / AUC 0.749
> / HT F1 0.44; 1D-CNN 63.3% / bal 51.7% / AUC 0.609 / HT F1 0.27; Transformer 54.4% / bal 63.4%
> / AUC 0.675 / HT F1 0.42).

### 7.3 What the tables say

**Best on the honest (independent) metric: TabPFN.** On the leak-free split it leads accuracy
(0.729), weighted F1 (0.743), and AUC (0.783), and it does so while **almost erasing the
dependent→independent penalty** — its accuracy drops only −0.004 and weighted F1 −0.006 versus the
dependent base model, against the 10–15-point fall that the leak-free split usually exacts. The
honest cost lands on the minority class instead: HT recall falls to 0.782 (it now misses ~1 in 5
ASD-model pups) and HT F1 to 0.610. The tuned XGBoost independent recipe is the runner-up and is
arguably the better *minority-class* operating point on unseen mice — HT recall 0.869 and HT F1
0.612 both beat TabPFN — at the cost of lower overall accuracy (0.702) and a much lower AUC (0.753).
Untuned XGBoost independent is the weakest honest tabular model (acc 0.693, HT F1 0.529, HT recall
0.637), confirming that the leak-free split hits the untuned recipe hardest.

**Best on the dependent (optimistic) metric: also TabPFN.** On the leaky split TabPFN tops every
aggregate — accuracy 0.781, weighted F1 0.794, balanced accuracy 0.828, AUC 0.908, HT F1 0.688 —
beating the tuned XGBoost (acc 0.772, wF1 0.785, AUC 0.885) and the base model on all of them. So
the dependent ranking is **tabpfn > xgboost_tuned > xgboost (base)**, and the independent ranking on
overall metrics is the same: **tabpfn > xgboost_tuned > xgboost**.

**Where the base model sits.** The base model (untuned XGBoost, dependent) is the **floor of the
tabular dependent table** — its 0.733 accuracy and 0.749 weighted F1 are the values every other
tabular run is measured against (Δ vs base). It is an outlier in *operating point*, not in skill: its
HT recall of 0.940 is the highest of any tabular run, but that is bought with HT precision 0.496, so
its HT F1 (0.649) is the **lowest** of the three dependent tabular models. Tuning and TabPFN both
trade some of that saturated recall for precision and come out ahead on F1. Read honestly, the base
model's dependent 0.733 sits **above** its own leak-free counterpart (independent untuned XGBoost,
0.693) — i.e. the headline base number is optimistic, and TabPFN's *honest* 0.729 essentially matches
the base model's *optimistic* 0.733.

> **For the paper.** The single defensible headline is **TabPFN, subject-independent: 0.729 accuracy
> / 0.743 weighted F1 / 0.783 AUC / 0.610 HT F1 (HT recall 0.782)** — the best honest, leak-free
> result in the project, and within ~0.005 of the *optimistic* base model. Report the base model's
> 0.733 explicitly as a dependent (leaky) ceiling, not a generalization estimate.

**Tabular vs. sequence: the tabular family wins — with a grain caveat.** On the honest split the
best sequence model on overall accuracy (1D-CNN, 0.633) trails the best tabular model (TabPFN, 0.729)
by ~10 points, and no sequence model reaches the tabular weighted-F1 or AUC band. The sequence models
are also **operating-point-unstable**: the BiLSTM control collapses to a degenerate "predict HT for
everyone" solution (HT recall 1.000 but accuracy 0.232 dependent / 0.456 independent, balanced
accuracy 0.500), while the 1D-CNN swings the other way on the honest split (HT recall 0.316). Their
*ranking* metric, AUC, is respectable (BiLSTM 0.749–0.790, comparable to untuned XGBoost's 0.770),
which says the sequences carry signal but the default 0.5 threshold is badly miscalibrated for them —
threshold tuning helps the sequence models more than the tabular ones. The grain caveat is decisive
here: the sequence test sets are tiny (a few dozen sessions), so each percentage point is one or two
sessions and the variance is large; the tabular comparison rests on 2,100+ recordings. **Verdict:
for this dataset and at the recording grain, the aggregated tabular models — TabPFN first, tuned
XGBoost second — are both the stronger and the more reliable classifiers; the sequence models are a
promising-but-noisy second track whose value is best read through AUC and through their
threshold-tuned configurations, not raw default-threshold accuracy.**

> ⚠️ **Do not cross the grain in a single sentence.** A sequence-model accuracy (per *session*) and a
> tabular-model accuracy (per *recording*) are computed on different test populations of different
> sizes. The tables above are aligned by *split* and *threshold*, not by sample identity; comparisons
> should be made family-to-family and trend-to-trend.

---

## 8. Is this state of the art? (modeling)

**Honest assessment for the methods/limitations section.** The modeling stack has two
families — **tabular** (XGBoost, TabPFN; [`preprocessing_pipeline.md`](preprocessing_pipeline.md) §2)
and **from-scratch sequence** models (BiLSTM, 1D-CNN, Transformer; *ibid.* §3) — and they sit at
very different points on the SOTA scale. Throughout, the anchor is the **base model**
(`results/tabular_models/xgboost_subject_eval_dependent_baseline`): test accuracy **0.733**,
weighted F1 **0.749**, HT recall **0.940** / precision **0.496**.

### 8.1 Tabular classifiers — strong, appropriate baselines for a small cohort

For a **small tabular cohort** (12,323 recording rows aggregated from 126 pups —
[`research_data_and_recording.md`](research_data_and_recording.md) §6–§8; the 46-feature vector of
[`preprocessing_pipeline.md`](preprocessing_pipeline.md) §2.3), **XGBoost** and **TabPFN** are the
right tools, and they are at or near the practical state of the art for this problem shape:

- **XGBoost** (`src/classification/tabular/models.py → create_xgboost`) is the canonical
  gradient-boosted-tree baseline for low-dimensional tabular biology — interpretable (feature
  importances, learning curves), fast, and natively handling the ~3:1 WT:HET imbalance via
  `scale_pos_weight = n_WT/n_HT` (HET positive). The tuned variants
  (`create_xgboost_tuned_dependent` / `_independent`) are the rank-5/rank-3 configs from a
  **200-trial random search with 5-fold CV** (`scripts/tune_xgboost_hyperparams.py`), i.e. a
  proper, non-overfit-to-test selection.
- **TabPFN** (`create_tabpfn`, TabPFN-3) is a genuinely **modern, near-SOTA** entry: a
  prior-data-fitted transformer that performs in-context Bayesian inference over small tables with
  **no per-dataset training**. It is the **strongest single model in the matrix**: on the
  subject-dependent baseline it beats the XGBoost base on every aggregate — test accuracy **0.781**
  (Δ +0.048), weighted F1 **0.794** (+0.045), HT precision **0.550** (+0.054) at HT recall **0.918**
  (`results/tabular_models/tabpfn_subject_eval_dependent_baseline/README.md`). With threshold tuning
  it reaches its best operating point of **acc 0.819 / balacc 0.817 / HT recall 0.811 / WT recall 0.822** (HT F1 0.702)
  (f1 / target_recall objective; `results/tabular_models/threshold_objectives/summary_objectives.txt`).

> **For the paper.** Position XGBoost as the *interpretable classical baseline* and TabPFN as a
> *modern AutoML/foundation-model-for-tables* comparison. Using both — a tree ensemble and a PFN —
> is exactly the recommended practice for small tabular benchmarks; there is little headroom to
> "be more SOTA" on the tabular *representation* without changing the **features**, not the model.

### 8.2 The honest ceiling is the subject-independent number, and it is data-limited

On the leak-free **subject-independent** split (split by mouse, 22 held-out animals) every model
lands far lower than its optimistic dependent read:

| Model / split | Test acc | Weighted F1 | HT recall | HT prec | Source |
|---|---:|---:|---:|---:|---|
| XGBoost / dependent (**base**) | 0.733 | 0.749 | 0.940 | 0.496 | base README |
| XGBoost / independent | 0.693 | 0.706 | 0.637 | 0.452 | `xgboost_subject_eval_independent_baseline/README.md` |
| TabPFN / dependent | 0.781 | 0.794 | 0.918 | 0.550 | `tabpfn_subject_eval_dependent_baseline/README.md` |
| TabPFN / independent | 0.729 | — | — | — | `tabpfn_subject_eval_independent_baseline/README.md` |

The independent XGBoost run loses **HT recall 0.940 → 0.637** (−0.303) and HT F1 0.649 → 0.529 vs
the base — "on unseen mice this run misses ~1 in 3" ASD pups. The tuned-independent recipe is, by
design, *shallow and heavily regularised* (`n_estimators=20, max_depth=3, min_child_weight=20`;
`models.py`) precisely "because the independent split is data-limited." This gap — not the model
choice — is the real ceiling.

### 8.3 Sequence models — under-powered by the few-hundred-session corpus

The three sequence models (`sequence_pipeline.py`) are **trained from scratch, small by design**
(72k–149k params; `results/neural_networks/executive_summaries/sequence_models/master_metrics.md`)
on only **~408 sessions** (≈19 HT test sessions on the independent split;
`results/neural_networks/experiments/README.md`). This is the stack's weakest link relative to SOTA:

- **No pretraining / self-supervision.** Unlike the **BiT R50×3** syllable classifier *upstream*
  ([`segmentation_process.md`](segmentation_process.md) §5.0), which is ImageNet-21k-pretrained and
  the most modern component of the whole pipeline, the sequence encoders see **only** the few-hundred
  labeled sessions. Modern sequence SOTA for small corpora is *pretrain-then-finetune* (self-supervised
  on the unlabeled syllable stream first); none of that exists here.
- **Frequent class collapse.** At the operating point, several configs default to one class — e.g.
  `A_control__bilstm__dependent` lands at **23.2% accuracy / 100% HT recall / 0.00 WT F1** and
  `B_beta0.5__bilstm__dependent` at **76.8% acc / 0% HT recall**
  (`results/neural_networks/experiments/_summary/master_metrics.md`). The best HT-balanced result is
  the balanced-sampler BiLSTM (`D_sampler__bilstm__independent`: balanced acc **70.4%**, AUC 0.767,
  HT recall 100% but HT precision only 31.1%).
- **The lever sweep confirms the limit, not a fix.** Experiments A–H
  (`experiments/README.md`) try class-weighting, balanced sampling, focal loss, regularisation, and
  augmentation. The balanced sampler (**D**) is "the most reliable lever," rescuing the BiLSTM
  dependent collapse (balacc 0.500 → 0.628). But the 5-fold CV honesty check (**H**) shows the strong
  single-split independent numbers are a **lucky-fold artifact** (5-fold independent ≈ **0.56 ± 0.06**
  vs the dependent ≈ **0.61 ± 0.06**): "independent generalization is **data-limited**, not
  recoverable by these levers alone."

> ⚠️ **Tabular vs sequence is not a clean model comparison.** The two tracks make *different*
> decisions about the same raw data (undefined calls dropped vs embedded; first-syllable rows dropped
> vs kept; duration/ISI handling; strain used vs not) and operate at *different grains* (recording vs
> session) — see [`preprocessing_pipeline.md`](preprocessing_pipeline.md) §4. Frame any head-to-head as
> a *representation + model* comparison, not a pure model comparison.

### 8.4 Threshold tuning — sensible, and correctly leak-free

Decision-threshold tuning (Issue #29; `--threshold auto`) derives the cut from the **held-out
validation split only** (`train_classifier.py → derive_thresholds`, then applied to test), with four
objectives (youden / f1 / target_recall / balanced). For TabPFN in threshold mode the val set is
held **out** (not merged into train) "for leak-free threshold derivation" — the correct,
disclosed protocol. This is a defensible, standard way to pick an operating point on an imbalanced
problem and materially improves the tabular results (TabPFN dependent: acc 0.781 @0.5 → acc
**0.819** at the f1/target_recall cut). It is *not* a SOTA modeling advance in itself; it is good
hygiene applied to an already-trained model.

### 8.5 What a more SOTA approach would add

For the future-work / limitations paragraph:

1. **Pretrained / self-supervised sequence encoders** — pretrain on the full unlabeled syllable
   stream (125,576 syllables) before fine-tuning the few-hundred-session classifier, mirroring how
   the upstream BiT classifier benefits from ImageNet-21k pretraining.
2. **Richer per-call contour features** — the tabular set carries only **4 acoustic descriptors per
   type** (start/end frequency, relative frequency, duration); modern bioacoustics traces the **full
   frequency contour** (mean/min/max/slope, bandwidth, FM depth) per call — the clearest feature-side
   upgrade ([`segmentation_process.md`](segmentation_process.md) §10; not currently emitted, no
   bandwidth column).
3. **More data** — the independent ceiling is set by ~22 test mice / ~19 HT sessions; additional
   litters would do more than any architecture change.
4. **Nested cross-validation** — the tuned XGBoost configs use a single held-out test after CV
   selection; nested CV (outer test folds around the inner CV search) would give honest,
   variance-quantified estimates instead of one split, and is the natural next rigor step for a small
   cohort.

**Bottom line.** TabPFN + tuned XGBoost are appropriate, near-SOTA baselines for a small tabular
cohort; threshold tuning is correct hygiene; the from-scratch sequence models are *under-powered* by
the corpus, not by their design, and are the place where pretraining + more data would move the needle.

---

## 9. Open questions / to verify before publishing

These are modeling-side items specific to the classification stack (the data/feature-side questions
live in [`segmentation_process.md`](segmentation_process.md) §11 and
[`preprocessing_pipeline.md`](preprocessing_pipeline.md) §7).

1. **Independent generalization is data-limited (the H-CV result).** The single-split
   subject-independent sequence numbers are inflated by fold luck: the 5-fold CV estimate is
   **≈0.56 ± 0.06** (independent) vs **≈0.61 ± 0.06** (dependent)
   (`experiments/README.md`; `experiments/_summary/master_metrics.md`). **Report CV mean ± std, not
   single-split point estimates**, for any generalization claim — and consider running the same
   `--cv-folds 5` check for the tabular models before publishing their independent numbers.

2. **The strain-background confound.** From 2022 onward the cohort is labeled
   `BALB/C+BLACK/C57` (a possible Balb/c × C57Bl/6 cross) vs pure `BALB/C` in 2015/2018
   ([`research_data_and_recording.md`](research_data_and_recording.md) §7.2). `pup_strain` (1/2) is a
   **tabular feature** but is **absent from the sequence inputs**
   ([`preprocessing_pipeline.md`](preprocessing_pipeline.md) §3.7). Strain is also confounded with
   *year* and *age coverage* (2022–2024 ≈ P4/P6 only). A model could be reading strain/year rather
   than genotype. Verify with the `--strain {1,2}` cohort runs
   (`results/tabular_models/strain/`) and state whether genotype signal survives within a single
   strain.

3. **Recording-vs-subject grain in the reported metrics.** Tabular models predict per **recording**
   (one row = one recording; `mouse_idx` only groups the split), then evaluate at the **recording**
   level — test accuracy 0.733 is over **2,465 recordings**, not 22 mice. Sequence models predict per
   **session**. State explicitly that headline metrics are recording-/session-level, and decide
   whether a **subject-level** aggregation (vote per mouse) should also be reported
   ([`preprocessing_pipeline.md`](preprocessing_pipeline.md) §2.1, §7.4).

4. **Threshold-objective choice.** The adopted runs use **youden**
   (`summary_matrix.txt`), but f1/target_recall give materially different operating points (e.g.
   TabPFN dependent: youden → acc 0.766/HT recall 0.938 vs f1 → acc 0.819/HT recall 0.811;
   `summary_objectives.txt`). The "right" objective depends on the clinical cost of a missed ASD pup
   vs a false alarm — fix and justify one objective in the paper rather than reporting the best cell
   per row. Note the **degenerate independent thresholds** (e.g. tabpfn/independent youden = **0.005**,
   xgboost/independent youden = **0.128**) that push HT recall to ~1.0 by predicting almost everything
   positive — a sign the val ROC is unstable on the small independent split.

5. **NN collapse sensitivity.** Several sequence configs collapse to a single class
   (HT recall 0% or 100%, WT F1 0.00; `experiments/_summary/master_metrics.md`), and which lever
   avoids collapse is architecture-dependent (sampler **D** rescues the BiLSTM; the Transformer's
   control **A** is often already best). Report the **full lever sweep**, not the single best run, and
   note that results are sensitive to seed/sampler — all runs use **seed 100** (§10), so robustness to
   re-seeding is currently *unmeasured*.

6. **Tabular and sequence models are not trained on identical information.** Different undefined-call
   handling, first-syllable handling, duration/ISI clipping, strain inclusion, and grain
   ([`preprocessing_pipeline.md`](preprocessing_pipeline.md) §4). Any sentence comparing them must
   frame it as *representation + model*, not a controlled model comparison. To make it controlled,
   train both tracks on aligned inputs.

7. **Two TabPFN caveats.** (i) In non-threshold mode TabPFN **merges val into train** (80% vs 60%
   data), so its dependent baseline trains on more data than XGBoost — fair to note when comparing.
   (ii) TabPFN requires an external `TABPFN_TOKEN` and API access (`models.py → create_tabpfn`), which
   affects exact reproducibility (network-dependent).

---

## 10. Reproducibility

Every result in this document is regenerable from the corrected input workbook
(`outputs/external/input/segmentation_classification_all_data.xlsx`) with the commands below. All
training runs use **seed = 100** (`train_classifier.py` `seed = 100`; `sequence_pipeline.py`
`SEED = 100`), and **every run writes its own `results/**/README.md`** plus
`comparison_vs_baseline.txt`, `logs/out.txt`, and (tabular) `model/<model>.pkl` /
(sequence) `results.json` + `model/<model>_best.pt` + `scaler.pkl`. Run all commands from the repo
root; `.venv/bin/python` is the project interpreter.

### 10.1 Step 0 — rebuild the training matrices

```bash
# Tabular aggregates (TensorFlow-free, ~11 min) -> outputs/external/aggregated/{tabular,sequence}/
.venv/bin/python scripts/run_external_aggregation.py
#   -> tabular/all_data_external_main.csv      (13,342 rows)
#   -> tabular/all_data_external_baseline.csv  (12,323 rows; OFFICIAL training set)
#   -> sequence/all_data_external_baseline.xlsx (syllable-level; sequence track input)
```

The sequence track rebuilds its in-memory tensors each run from the baseline xlsx (no persisted
artifact); the tabular CSV is headerless, columns defined positionally by `COL_NAMES`
([`preprocessing_pipeline.md`](preprocessing_pipeline.md) §2.3).

### 10.2 Tabular runs (XGBoost / TabPFN)

```bash
# Base model (the anchor: test acc 0.733 / weighted F1 0.749)
.venv/bin/python src/classification/tabular/train_classifier.py --baseline --model xgboost
# subject-independent (leak-free, by mouse)
.venv/bin/python src/classification/tabular/train_classifier.py --baseline --independent --model xgboost

# Tuned XGBoost (200-trial random-search winners; pair each with its matching split)
.venv/bin/python src/classification/tabular/train_classifier.py --baseline --model xgboost_tuned_dependent
.venv/bin/python src/classification/tabular/train_classifier.py --baseline --independent --model xgboost_tuned_independent

# TabPFN (needs TABPFN_TOKEN in .env)
.venv/bin/python src/classification/tabular/train_classifier.py --baseline --model tabpfn
.venv/bin/python src/classification/tabular/train_classifier.py --baseline --independent --model tabpfn

# Cohort (strain) runs -> results/tabular_models/strain/
.venv/bin/python src/classification/tabular/train_classifier.py --baseline --strain 2 --model xgboost
.venv/bin/python src/classification/tabular/train_classifier.py --baseline --strain 1 --independent --model xgboost
```

`--model` choices: `xgboost`, `xgboost_tuned_dependent`, `xgboost_tuned_independent`, `tabpfn`
(registry in `models.py`). `--independent` is the preferred alias for `--group-split`.
Output dir is auto-named from the data source + split
(`results/tabular_models/<model>_subject_eval_{dependent,independent}_baseline/`).

To re-derive the tuned hyperparameters from scratch (5-fold CV random search):

```bash
.venv/bin/python scripts/tune_xgboost_hyperparams.py --dependent  --n-trials 200
.venv/bin/python scripts/tune_xgboost_hyperparams.py --independent --n-trials 200
#   -> outputs/reports/xgboost_tuning/
```

### 10.3 Sequence runs (BiLSTM / 1D-CNN / Transformer)

```bash
for m in bilstm cnn1d transformer; do
  .venv/bin/python src/classification/neural_networks/sequence_pipeline.py --model $m --baseline
  .venv/bin/python src/classification/neural_networks/sequence_pipeline.py --model $m --baseline --independent
done
.venv/bin/python scripts/generate_nn_executive_summary.py --strict
#   -> results/neural_networks/executive_summaries/sequence_models/{master_metrics.md,.csv,executive_summary.html}
```

The lever sweep (experiments A–H) adds tuning flags on top of `--baseline [--independent]`:

```bash
# Example levers (see experiments/README.md for the full A-H matrix):
#   B: --pos-weight-beta 0.5      C: --pos-weight-beta 0
#   D: --sampler balanced --pos-weight-beta 0     E: --loss focal --focal-gamma 2.0
#   F: --weight-decay ... --dropout ... --hidden-size ...    G: --augment-windows N --window-stride N
#   H: --sampler balanced --pos-weight-beta 0 --cv-folds 5
.venv/bin/python src/classification/neural_networks/sequence_pipeline.py --baseline --model bilstm --sampler balanced --pos-weight-beta 0
.venv/bin/python scripts/generate_nn_executive_summary.py --results-root results/neural_networks/experiments
```

### 10.4 Threshold tuning + objective comparison

```bash
# Run all 6 (model x split) threshold runs -> results/tabular_models/threshold/<run>/ + summary_matrix.txt
.venv/bin/python scripts/run_threshold_matrix.py                  # default objective: youden
.venv/bin/python scripts/run_threshold_matrix.py --objective f1
.venv/bin/python scripts/run_threshold_matrix.py --runs tabpfn    # subset by name/index
.venv/bin/python scripts/run_threshold_matrix.py --dry-run        # print commands only

# Cross-objective comparison WITHOUT retraining (reuses saved per-sample probabilities;
# mathematically identical to re-running each objective; self-checks Youden vs stored JSON)
.venv/bin/python scripts/compare_threshold_objectives.py
#   -> results/tabular_models/threshold_objectives/{summary_objectives.txt,.csv} + per-run dirs
```

A single tabular run can also be threshold-tuned directly:
`train_classifier.py --baseline --threshold auto --threshold-objective {youden,f1,target_recall,balanced}
[--target-recall 0.80]` (or a fixed `--threshold FLOAT`).

### 10.5 Where the numbers live

| Master / summary file | Covers |
|---|---|
| `results/tabular_models/threshold/summary_matrix.txt` | 6 runs, 0.5 vs tuned threshold |
| `results/tabular_models/threshold_objectives/summary_objectives.txt` (+`.csv`) | 6 runs × {@0.5, youden, f1, target_recall, balanced} |
| `results/neural_networks/executive_summaries/sequence_models/master_metrics.md` | the 6 baseline sequence runs |
| `results/neural_networks/experiments/_summary/master_metrics.md` | the full A–H lever sweep, ranked by balanced acc |
| each run's `comparison_vs_baseline.txt` / `results.json` / `README.md` | that run's own metrics (read the **run** column, **ignore** the legacy `baseline: 0.829` column) |

> ⚠️ **Do not read the `baseline:` column inside any `comparison_vs_baseline.txt`** — it is a legacy
> 0.829 reference, **not** the base model. The base model is
> `results/tabular_models/xgboost_subject_eval_dependent_baseline` (test acc 0.733, weighted F1 0.749,
> HT recall 0.940, HT precision 0.496).

---

## 11. Code-path index (modeling)

| Step | File | Key symbols |
|------|------|-------------|
| Tabular aggregation entry | `scripts/run_external_aggregation.py` | `main`; calls `run_external_aggregated_feature_extraction` |
| Tabular training / split / eval | `src/classification/tabular/train_classifier.py` | `main`, `resolve_training_csv_path`, `default_results_subdir`, `random_split`, `group_aware_split`, `COL_NAMES`, `seed = 100`, threshold block (`derive_thresholds`/`select_threshold`/`predict_at_threshold`) |
| Tabular model registry | `src/classification/tabular/models.py` | `MODEL_REGISTRY`, `create_xgboost`, `create_xgboost_tuned_dependent`, `create_xgboost_tuned_independent`, `create_tabpfn`, `XGBOOST_FAMILY`, `merges_val_into_train` |
| Threshold logic | `src/classification/tabular/threshold.py` | `OBJECTIVES`, `DEFAULT_OBJECTIVE`, `derive_thresholds`, `select_threshold`, `evaluate`, `positive_proba`, `predict_at_threshold` |
| Threshold report artifacts | `src/classification/tabular/threshold_report.py` | `save_probabilities`, `plot_roc_with_operating_points`, `plot_confusion_at`, `write_threshold_report`, `write_metrics_json` |
| Hyperparameter search | `scripts/tune_xgboost_hyperparams.py` | random search + 5-fold CV (`StratifiedKFold` / `StratifiedGroupKFold`), `early_stopping_rounds=25` |
| Threshold matrix driver | `scripts/run_threshold_matrix.py` | `RUNS`, `build_cmd`, `consolidated_table`, `load_metrics` |
| Cross-objective comparison | `scripts/compare_threshold_objectives.py` | `OBJECTIVES`, `read_probs`, `per_run_report`, `selfcheck_youden` (no-retrain shortcut) |
| Sequence pipeline | `src/classification/neural_networks/sequence_pipeline.py` | `load_and_prepare`, `USVSequenceDataset`, `random_split_sequences`, `group_split_sequences`, `BiLSTMClassifier`, `CNN1DClassifier`, `TransformerClassifier`, `CONTINUOUS_FEATURES`, `NUM_SYLLABLE_TYPES`, `SYLLABLE_EMBED_DIM`, `SEED = 100`, `set_seed` |
| Sequence summary generator | `scripts/generate_nn_executive_summary.py` | `find_runs`, `load_run` (HT = minority-support class), `write_master_md`, `render_html` |
| CLI flag reference | `docs/CLI_Flags.md` | all training / aggregation / threshold / sequence flags |
| Lever sweep index | `results/neural_networks/experiments/README.md` | A–H lever definitions |

> **For the paper.** Cite the exact symbol + file for every reported number; the per-run
> `README.md` under `results/**/` is the human-readable summary, and `results.json` /
> `threshold_metrics.json` / `comparison_vs_baseline.txt` are the machine-readable sources behind
> the master tables in §10.5.

---

*Reproducibility: every metric in this document comes from a per-run summary under
`results/**/README.md` and the master tables
(`results/neural_networks/executive_summaries/sequence_models/master_metrics.md`,
`results/neural_networks/experiments/_summary/master_metrics.md`,
`results/tabular_models/threshold/summary_matrix.txt`,
`results/tabular_models/threshold_objectives/summary_objectives.txt`). Regenerate every run
with the commands in §10 (tabular and sequence training both use seed 100).*

