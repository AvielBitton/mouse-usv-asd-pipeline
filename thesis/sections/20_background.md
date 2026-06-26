# 2. Background and Related Work

## 2.1 Autism spectrum disorder and the *Mthfr* model

ASD is a heterogeneous neurodevelopmental disorder with a strong but complex genetic component, interacting with environmental and metabolic factors. One metabolic pathway repeatedly implicated in neurodevelopment is one-carbon (folate) metabolism, of which the enzyme **methylenetetrahydrofolate reductase (*Mthfr*)** is a key component. Reduced *Mthfr* activity perturbs methylation reactions required for normal brain development, and *Mthfr*-deficient mice exhibit ASD-relevant behavioural and physiological alterations. The data analysed in this thesis come from a genetic ASD model based on *Mthfr* haploinsufficiency on a BALB/c background: wild-type (WT) dams crossed with WT sires, or heterozygous (HET) dams crossed with WT sires, producing pups whose individual genotype is WT or HET. The HET pups constitute the ASD-model (positive) class; the WT pups are controls [17], [18].

## 2.2 Ultrasonic vocalizations as a behavioural biomarker

Rodent USVs have become a standard tool for behavioural phenotyping of neurodevelopmental and neuropsychiatric models [1], [2], [5], [6]. Pup isolation calls, emitted when a pup is separated from dam and littermates, are among the earliest measurable communicative behaviours and are sensitive to genotype, sex, and developmental stage. Caruso et al. [2] and Premoli et al. [5] review the use of USVs across ASD rodent models and argue for richer, automated analyses beyond simple call counts.

Two studies from the research lineage of this project are particularly important because they characterise the **specific dataset paradigm** analysed here:

- **Shekel et al. (2021)** [17] applied unsupervised clustering to the spectral properties of isolation syllables in environmental (chlorpyrifos) and genetic (*Mthfr*) ASD models. They reported that **start frequency, bandwidth, and duration** were the most ASD-sensitive syllable features, and documented sex differences and strain (C57Bl/6 vs BALB/c) baseline differences that act as confounds. This single-session isolation paradigm and its feature set directly motivate the acoustic features used in the present tabular pipeline.

- **Gal et al. (2023)** [18] studied the **temporal dynamics** of isolation calls under a two-session (maternal-potentiation) paradigm — an isolation session, a reunion, and a second isolation session. They found dynamic, within- and between-session modulation of call quantity and spectral structure, with both ASD models increasing their use of harmonic calls over time, and interpreted altered dynamics as impaired regulation of vocalization. This finding that *temporal organisation* of calls carries phenotypic information motivates the sequence-modelling track of the present work.

## 2.3 Automated USV analysis and machine learning

Automated USV analysis has progressed from manual spectrogram inspection toward computer-vision and deep-learning pipelines. Tools such as VocalMat [10] and the deep-learning segmentation studies of Baggi et al. [11] detect and classify syllables from spectrograms; TrackUSF [12] and ARBUR [16] integrate detection with downstream behavioural analysis in rats; and Scott et al. [14] and Johnson et al. [13] address training-data scarcity through synthetic data and semi-automated labelling. On the *prediction* side, Qian et al. [8] piloted detection of ASD-model mice from USVs ("the sound of silence"), Wu et al. [15] extended this with empirical mode decomposition, and the INTERSPEECH **MADUV** challenge [3] established a public benchmark for mouse-ASD detection from ultrasound. Beyond rodents, deep-learning vocal biomarkers have also been explored for human infant ASD screening [4]. Yao et al. [7] connect mouse USVs to human speech, reinforcing the translational rationale.

The present project sits within this predictive line but is distinguished by its **engineering and evaluation rigour**: a single, versioned data source; an explicit separation of subject-dependent from subject-independent evaluation; and an honest treatment of minority-class behaviour rather than headline accuracy alone.

## 2.4 The prior project in this lineage

A previous M.Sc. project in the same research line — on the same topic and supervised by the same advisor, Dr. Dror Lederman [19] — approached the problem with pretrained audio neural networks (PANNs) operating on spectrograms and with a majority-voting scheme. That prior project is **prior art and a structural reference only**; none of its methods or results are reused or claimed here. The present work takes a different methodological route — interpretable per-recording acoustic aggregates with tree-based models, and ordered syllable sequences with recurrent/convolutional/attention models — and contributes the reproducible-pipeline and data-integrity work that the earlier iteration lacked. Framing the two together simply reflects the continuity of the advisor's research line.

## 2.5 Where this work fits

In summary, the biological grounding (USVs as an early ASD biomarker; the *Mthfr* model; the isolation paradigm) is well established [1], [2], [5], [17], [18]; automated detection of ASD-model mice from USVs is an active and still-open problem [3], [8], [15]; and the chief gaps this thesis addresses are **reproducibility, data integrity, and an honest, leakage-aware evaluation** of which models and which features actually generalize to unseen animals.
