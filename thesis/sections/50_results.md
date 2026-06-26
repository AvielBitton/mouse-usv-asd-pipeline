# 5. Experiments and Results

All numbers in this chapter are taken from the per-run result reports and the derived master results table; the data sources are listed in the traceability appendix. The positive class is HET throughout, and "dependent"/"independent" denote the subject-dependent and subject-independent split regimes defined in Section 4.5.

## 5.1 Master results — tabular models (pooled)

Table 1 reports the three tabular models on the pooled baseline, in both split regimes. [[REF:F9]] visualises the same numbers as dependent-versus-independent dumbbells for accuracy, weighted F1, and AUC.

[[FIG:F9]]

**Table 1 — Tabular models, pooled baseline (recording level). Best independent row in bold.**

| Model | Split | Accuracy | Weighted F1 | Balanced acc. | ROC-AUC | HT recall | HT precision | HT F1 |
|---|---|---|---|---|---|---|---|---|
| XGBoost (inherited) | dependent | 0.733 | 0.749 | 0.795 | 0.876 | 0.940 | 0.496 | 0.649 |
| XGBoost (inherited) | independent | 0.693 | 0.706 | 0.678 | 0.770 | 0.637 | 0.452 | 0.529 |
| XGBoost-tuned | dependent | 0.772 | 0.785 | 0.798 | 0.885 | 0.844 | 0.543 | 0.661 |
| XGBoost-tuned | independent | 0.702 | 0.719 | 0.725 | 0.753 | 0.869 | 0.473 | 0.612 |
| TabPFN | dependent | 0.781 | 0.794 | 0.828 | 0.908 | 0.918 | 0.550 | 0.688 |
| **TabPFN** | **independent** | **0.729** | **0.743** | **0.662** | **0.783** | **0.782** | **0.499** | **0.610** |

Two findings stand out. First, **TabPFN is the strongest tabular model in both regimes** on overall accuracy and weighted F1, answering RQ1 in the affirmative for the tabular foundation model: it beats the inherited XGBoost on the dependent split (0.781 vs 0.733 accuracy) and, more importantly, on the honest independent split (0.729 vs 0.693). Second, the **dependent→independent drop is real and model-dependent**. The inherited XGBoost loses the most (accuracy 0.733→0.693, HT recall 0.940→0.637); TabPFN absorbs the regime change best, with independent accuracy (0.729) essentially matching the *dependent* accuracy of the inherited model (0.733). Note, however, that on **balanced accuracy** the tuned XGBoost independent model (0.725) exceeds TabPFN independent (0.662), because it keeps HT recall high (0.869); "best" therefore depends on whether overall accuracy or minority-class balance is the objective — a point we return to in Sections 5.5 and 6.

## 5.2 The corrected baseline: a data-integrity result

A previously reported subject-dependent accuracy of **0.829** is *not reproduced* by the corrected, leak-free pipeline. [[REF:F4b]] decomposes the difference into two separable effects:

1. **Data-integrity correction (within the dependent regime): 0.829 → 0.733.** Correcting the genotype mislabelling (Section 3.5) and the class-weighting computation lowers the *subject-dependent* XGBoost accuracy to 0.733. This is not a performance regression; the earlier figure was inflated by mislabelled data.
2. **Leakage removal (regime change): 0.733 → 0.693.** Moving from the subject-dependent to the honest subject-independent split costs a further ~0.04 in accuracy for the inherited XGBoost, exposing the optimism of evaluating on recordings from animals also seen in training.

The best *honest* model, TabPFN on the independent split, recovers much of this: **0.729 accuracy on entirely unseen mice**. The headline of this project is therefore not a single large number but a calibrated one: roughly **0.73 accuracy / 0.74 weighted F1 / 0.78 ROC-AUC for generalization to unseen animals**, with the prior 0.829 understood as an artefact of data errors and leakage.

[[FIG:F4b]]

## 5.3 Generalization, ranking, and minority-class behaviour

[[REF:F11]] (ROC) and [[REF:F12]] (precision–recall) confirm the ranking and quantify the regime cost from held-out probabilities. ROC-AUC falls from the dependent to the independent split for every model (e.g. TabPFN 0.908→0.783), and the precision–recall curves show that minority-class precision degrades sharply at high recall on the independent split.

[[FIG:F11]]

[[FIG:F12]]

[[REF:F10]] makes the minority-class story explicit. As evaluation moves from dependent to independent, **HT precision stays pinned near 0.50 for every tabular model** (0.452–0.550), regardless of model family, tuning, or regime. We call this the **HT-precision wall** ([[REF:F16]]): at the default threshold, roughly half of all positive (HT) calls are false alarms. The confusion matrices in [[REF:F13]] show the same thing structurally — the dominant error in every panel is WT recordings predicted HT. Because the wall survives every estimator and every split, it is a property of the *features*, not of the classifier (Section 6.2), and answers part of RQ2: the current per-recording acoustic aggregates carry only enough information to rank well (AUC up to 0.78 on unseen mice) but not to achieve high-purity positive calls.

[[FIG:F10]]

[[FIG:F13]]

[[FIG:F16]]

## 5.4 Sequence models and cross-validation deflation

Table 2 reports the three sequence models on the pooled baseline (session level; 82 dependent and 90 independent test sessions, of which 19 are HT). These numbers are **not like-for-like** with the tabular models, which are evaluated at the recording level on far larger test sets.

**Table 2 — Sequence models, pooled baseline (session level).**

| Model | Split | Accuracy | Balanced acc. | ROC-AUC | HT recall | HT precision | HT F1 |
|---|---|---|---|---|---|---|---|
| BiLSTM | dependent | 0.232 | 0.500 | 0.790 | 1.000 | 0.232 | 0.376 |
| BiLSTM | independent | 0.456 | 0.655 | 0.749 | 1.000 | 0.279 | 0.437 |
| 1D-CNN | dependent | 0.500 | 0.564 | 0.604 | 0.684 | 0.271 | 0.388 |
| 1D-CNN | independent | 0.633 | 0.517 | 0.609 | 0.316 | 0.231 | 0.267 |
| Transformer | dependent | 0.659 | 0.668 | 0.655 | 0.684 | 0.371 | 0.481 |
| Transformer | independent | 0.544 | 0.634 | 0.675 | 0.789 | 0.288 | 0.423 |

The sequence models are **markedly weaker and prone to collapse**. The clearest pathology is the BiLSTM on the dependent split: it predicts HT for *all* 82 test sessions (accuracy 0.232 = the HT base rate, WT recall 0; balanced accuracy 0.500), yet its ROC-AUC is 0.790 — the ranking is informative but the operating point is broken, a failure that only the imbalance-robust metrics expose. The Transformer is the most stable baseline (balanced accuracy 0.668 dependent, 0.634 independent) but does not approach the tabular models.

A sweep of eight imbalance-handling levers (A–H) was run across the three architectures ([[REF:F18]], left). The best single-split result was a BiLSTM with a balanced minibatch sampler reaching **independent balanced accuracy 0.704**. However, 5-fold grouped cross-validation of this configuration **deflates the estimate to 0.563 ± 0.063** (independent) and 0.609 ± 0.055 (dependent) ([[REF:F18]], right). The single 0.704 was a lucky fold; the honest sequence-model signal is weak and data-limited (≈19 HT test sessions), and is not recoverable by configuration changes. This answers RQ3 for the sequence track: at the current data scale, temporal call order does **not** yield a reliable gain over the tabular aggregates.

[[FIG:F18]]

## 5.5 Decision-threshold tuning

Threshold tuning derives an operating point on the validation split and freezes it before the test set; it cannot change AUC but can move the precision/recall trade-off. [[REF:F17]] shows the effect on TabPFN. On the **dependent** split, an F1- or target-recall objective lifts HT precision to ~0.62 (from 0.55) while holding HT recall ~0.81, and raises accuracy to ~0.82 — the only operating point that meaningfully exceeds the 0.50 precision wall, and then only in the optimistic regime. On the **independent** split, the Youden and balanced objectives **degenerate** (threshold collapses toward 0, HT recall →1, precision pinned ~0.48); a target-recall objective (recall floor ≈0.80) is the only sensible choice, keeping HT recall ~0.86 at precision ~0.46. Threshold tuning is thus best understood as leak-free operating-point hygiene, not as a way to break the feature-level ceiling.

[[FIG:F17]]

## 5.6 Per-strain analysis

Splitting the cohort by strain reveals a strong interaction ([[REF:F15]], Table 3, XGBoost). On the **strain1** cohort (2022–2024, mixed background) the models are highly separable *even leak-free*: XGBoost reaches **independent accuracy 0.903, weighted F1 0.909, HT F1 0.753** — higher than the pooled dependent baseline. On the **strain2** cohort (2015/2018, pure BALB/c, only 47 mice) the minority class **collapses** under the independent split: XGBoost independent HT recall falls to 0.089 (HT F1 0.122), and TabPFN independent reaches only 0.654 accuracy with HT F1 0.388.

[[FIG:F15]]

**Table 3 — Per-strain XGBoost results.**

| Cohort | Split | Accuracy | Weighted F1 | HT recall | HT F1 |
|---|---|---|---|---|---|
| strain1 (2022–24) | dependent | 0.774 | 0.791 | 0.919 | 0.657 |
| strain1 (2022–24) | independent | 0.903 | 0.909 | 0.900 | 0.753 |
| strain2 (2015/18) | dependent | 0.748 | 0.759 | 0.808 | 0.642 |
| strain2 (2015/18) | independent | 0.657 | 0.609 | 0.089 | 0.122 |

This is the project's most important cautionary result. The exceptional strain1-independent score should **not** be read as a general headline: strain1 is a more recent, lower-HT-prevalence, more separable cohort, and because strain/background is confounded with genotype, a model trained on it may be reading *cohort membership* rather than the ASD phenotype. The strain2 collapse, despite subject-grouping, reflects both the small cohort and this confound. A genuine cross-cohort test (train on one strain, test on the other) is the honest validation and is left to future work.

## 5.7 Which features matter

[[REF:F14]] shows the top-15 features by XGBoost gain importance, averaged over the dependent and independent models.

[[FIG:F14]]

The classification is driven overwhelmingly by the **per-syllable-type start- and end-frequency aggregates and durations**, with metadata features (age, session, strain) and the average ISI playing secondary roles. This is consistent with Shekel et al. (2021) [17], who identified start frequency, bandwidth, and duration as the most ASD-sensitive syllable features. The result partially answers RQ2: a small set of spectral/temporal feature *families* (boundary frequencies and durations) dominates, rather than any single feature — and the absence of a richer per-call descriptor (e.g. full frequency contour, bandwidth, frequency-modulation depth) is the most plausible explanation for the HT-precision wall (Section 6.2).

## 5.8 Best model per scenario

Table 4 collects the best model for each scenario, which is the practical answer the reader needs. The pattern is consistent: **TabPFN is best on the pooled cohort in both regimes** (by accuracy/weighted F1), **strain1 is highly separable**, **strain2 does not generalize**, and **tabular models dominate sequence models** at this data scale.

**Table 4 — Best model per scenario (by weighted F1 / accuracy).**

| Cohort | Split | Best model | Accuracy | Weighted F1 | HT F1 |
|---|---|---|---|---|---|
| pooled | dependent | TabPFN | 0.781 | 0.794 | 0.688 |
| pooled | independent | TabPFN | 0.729 | 0.743 | 0.610 |
| strain1 | dependent | XGBoost-tuned | 0.789 | 0.802 | 0.649 |
| strain1 | independent | XGBoost | 0.903 | 0.909 | 0.753 |
| strain2 | dependent | TabPFN | 0.801 | 0.809 | 0.703 |
| strain2 | independent | TabPFN | 0.654 | 0.659 | 0.388 |
| pooled (sequence) | dependent | Transformer | 0.659 | — | 0.481 |
| pooled (sequence) | independent | 1D-CNN | 0.633 | — | 0.267 |
