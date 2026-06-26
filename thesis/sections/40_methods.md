# 4. Methods

The end-to-end pipeline is summarised in [[REF:F1]]: from the recording rig and raw WAV files, through segmentation and CNN syllable typing, to two parallel preprocessing representations (tabular and sequence), the model families, the evaluation protocol, and interpretation. This chapter describes each stage.

[[FIG:F1]]

## 4.1 Segmentation and syllable typing

**Segmentation** detects syllable boundaries with a classical signal-processing detector operating on a cochlear (gammatone) filterbank of 90 ERB-spaced filters covering 35–125 kHz. Audio is analysed in short overlapping frames; a tonality criterion (energy concentrated in few channels) flags candidate syllables, short silent gaps are bridged so that frequency-modulated sweeps are not split, and calls shorter than 10 ms or closer than 20 ms are merged or discarded. Each detected syllable yields a start time, end time, and duration. The detector is deterministic, fast, and tuned to this laboratory's rig; it is comparable in spirit to MUPET/USVSEG-style detectors and predates fully learned detectors such as DeepSqueak and VocalMat. Its thresholds are fixed constants, and it has not been validated against hand-labelled ground truth — limitations noted in Chapter 8.

For each syllable, two **boundary-frequency features** (start and end frequency) are estimated by Welch power-spectral-density peak-picking in a short window centred on each boundary, restricted to the >40 kHz band, and the **inter-syllable interval (ISI)** is computed as the gap to the previous syllable in the same recording (undefined for the first syllable).

**Syllable typing** assigns each syllable to one of ten classes using a convolutional neural network. The recovered architecture is a Big-Transfer (BiT) ResNet-50×3 backbone, pretrained on ImageNet-21k and fine-tuned on 128×128 spectrogram images of individual syllables, with a 10-way softmax head. Predictions whose maximum probability falls below 0.5 are relabelled "Undefined" (an eleventh, post-hoc class). The ten classes plus Undefined and their corpus counts appear in [[REF:F7]]; the dominant type is "Frequency steps". No published model card accompanies the typing network (training set and per-class accuracy are unknown), a limitation carried to Chapter 8.

## 4.2 Two preprocessing representations

The syllable table feeds **two independent representations**, which differ in what they preserve:

**Tabular (recording-level).** Each recording is reduced to a fixed **48-column vector**: for each of the ten syllable types, the mean start frequency, mean end frequency, relative frequency (the type's share of the recording's syllables), and mean duration (4 × 10 = 40 features), plus the average ISI, the pup's sex, age (postnatal day), session, strain, and the mother's genotype, plus the label (pup genotype) and a mouse index used only for grouping. This representation **averages away temporal order**. The first syllable of each recording (which has an undefined ISI) and Undefined-typed syllables are dropped before aggregation. The baseline tabular matrix has 12,323 rows (Section 3.4). Tabular models are XGBoost and TabPFN.

**Sequence (session-level).** Each isolation session is represented as an **ordered sequence of its syllables**, padded or truncated to 256 time-steps, with a 14-dimensional feature vector per step: four continuous features (start frequency, end frequency, duration, ISI, standard-scaled on the training set), a learned 8-dimensional embedding of the syllable type, a noise flag, and a recording-boundary flag. This representation **preserves temporal order** and keeps the Undefined type (as an embedding index). The baseline yields 408 sessions. Sequence models are BiLSTM, 1D-CNN, and Transformer.

Because the two tracks make different decisions (recording vs session grain; dropping vs keeping first and Undefined syllables), any comparison between them is a comparison of *representation plus model*, not of model alone — a caveat respected throughout Chapter 5.

## 4.3 Models

**XGBoost (inherited baseline).** A gradient-boosted tree ensemble using the legacy untuned recipe inherited with the project, with class imbalance handled by `scale_pos_weight = n_WT / n_HT` (≈3.1). This is the only model that existed at handoff and serves as the reference baseline.

**Tuned XGBoost (new).** A 200-trial randomised hyperparameter search with cross-validation, selecting a recipe per split regime. Because the best recipes differ between the dependent and independent regimes, the tuned results are reported as *separate per-regime models*, not as one model improving across regimes.

**TabPFN (new).** A prior-data-fitted transformer for tabular data that performs in-context Bayesian inference in a single forward pass with no hyperparameter tuning. TabPFN merges its validation split into training, so it sees more data than XGBoost (≈80% vs 60%); this is noted wherever the two are compared.

**Sequence models (new).** Three architectures over the ordered syllable sequences: a two-layer **BiLSTM** (≈149k parameters), a three-block **1D-CNN** (≈86k), and a small **Transformer** encoder with a learned CLS token (≈73k). All use `BCEWithLogitsLoss` with `pos_weight = n_WT / n_HT` (≈3.2), the Adam optimiser, learning-rate reduction and early stopping on validation AUC, gradient clipping, and a fixed seed. A family of imbalance-handling levers (loss weighting, balanced sampling, focal loss, regularisation, augmentation) is explored in Section 5.4.

The model taxonomy and the inherited-versus-new split are shown in [[REF:F4]].

## 4.4 Class imbalance and metrics

Under a ~3:1 class imbalance, raw accuracy is misleading: a constant "predict WT" classifier already scores ~0.75. We therefore report a suite of metrics and foreground imbalance-robust ones:

- **Accuracy** and **weighted F1** for overall performance (comparable to prior reports);
- **Balanced accuracy** (mean of per-class recall) as the primary imbalance-robust score;
- **ROC-AUC** (threshold-free ranking) and **PR-AUC / average precision** (focused on the minority HET class);
- **Per-class precision, recall, and F1** for WT and HT separately — the clinically meaningful breakdown, since HT recall is "catching ASD-model pups" and HT precision is the false-alarm rate.

Throughout, the positive class is HET.

## 4.5 Evaluation protocol: the heart of the study

Two split regimes are used, and the distinction between them is the central methodological point of the thesis:

- **Subject-dependent** (default): a random 60/20/20 split at the row/session level. Because the cohort is longitudinal, the *same animal* appears in training and test. This yields an **optimistic upper bound**, not a generalization estimate.
- **Subject-independent** (`--independent`): a 60/20/20 split **grouped by mouse**, with stratification on the label and explicit disjointness checks, so that no animal appears in two sets. This is the **honest "generalize to unseen mice"** setting.

In addition, models are evaluated **pooled** across all cohorts and **per-strain** (strain1 = 2022–2024; strain2 = 2015/2018), to probe whether a learned signal is genotype or cohort. The full grid of what was run is shown in [[REF:F3]].

[[FIG:F3]]

Tabular models are evaluated at the **recording level** and sequence models at the **session level**; the test sets therefore differ in size and grain, so cross-track numbers are directional rather than like-for-like. For the small sequence test sets, single-split estimates are supplemented by 5-fold grouped cross-validation (Section 5.4).

A separate, leak-free **decision-threshold tuning** step (Section 5.5) derives an operating threshold on the validation split and freezes it before touching the test set; it relocates the operating point but cannot change AUC.
