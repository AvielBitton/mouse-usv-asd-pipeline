# 1. Introduction

## 1.1 Motivation

Autism Spectrum Disorder (ASD) is a neurodevelopmental condition defined by difficulties in social communication together with restricted and repetitive behaviour. Diagnosis in humans rests on expert behavioural assessment, which is time-consuming, requires trained clinicians, and is especially hard to apply reliably in early infancy — precisely the window in which early intervention is most valuable. This motivates a search for objective, quantitative, and early biomarkers of atypical neurodevelopment.

Mouse models are a central tool in preclinical ASD research. When isolated from the nest, mouse pups emit **ultrasonic vocalizations (USVs)** — calls in the 35–125 kHz range that are inaudible to humans, produced naturally, and recordable non-invasively. These isolation calls are sensitive to genetic and environmental manipulations relevant to neurodevelopment, and their temporal and spectral structure has been proposed as an early, communication-related biomarker of ASD-like phenotypes [1], [2], [5]. Because mouse USVs share several organisational features with human speech — temporal patterning, frequency modulation, and sensitivity to developmental disruption — they offer a tractable bridge between molecular models and communication phenotypes [7].

Most prior USV studies remain *descriptive*: they report group-level differences in call rate or in a handful of acoustic features. A smaller and more recent body of work asks the harder *predictive* question — whether the differences between an ASD-model group and a wild-type group are large and consistent enough to classify an **individual animal** from its calls [8], [3], [15]. This project belongs to the predictive tradition and inherits a concrete experimental lineage: a long-running collaboration that recorded *Mthfr* (methylenetetrahydrofolate reductase) ASD-model mice and wild-type controls under a standardised isolation paradigm [17], [18].

## 1.2 The starting point: an inherited, non-runnable pipeline

This iteration of the project did not begin from a blank page, nor from a working system. It began from an **inherited code base that did not run**. At handoff, the repository contained a single monolithic prototype with hard-coded paths and a single, basic, *subject-dependent* XGBoost classifier — and nothing else. Reaching a state in which even that one model could be reproduced required rebuilding the whole pipeline: data ingestion, segmentation, feature extraction, training, and evaluation.

This shapes the entire thesis. A central, genuine contribution of this work is therefore not only a set of model results but the **reconstruction of a broken, undocumented pipeline into a versioned, end-to-end-reproducible system with a single source of truth for the data**, accompanied by a graphical tool that lets the biology researcher curate the underlying recordings in parallel. Everything beyond the inherited subject-dependent XGBoost — the tuned XGBoost, the TabPFN tabular model, the three neural-network sequence models, the subject-independent evaluation, and the per-strain analysis — was added by this project. [[REF:F4]] makes this inherited-versus-new distinction explicit.

## 1.3 Research questions

The research questions were not fixed at the outset. The interim proposal framed the project broadly: improve the inherited predictive model, identify which USV characteristics matter most, and assess whether USVs can reliably flag ASD-like traits. As the rebuilt pipeline made systematic experimentation possible, the questions were **refined in consultation with the project advisor, Dr. Dror Lederman**, toward the directions the new infrastructure could actually answer:

- **RQ1 — New models.** Do models that did not previously exist in this project — the TabPFN tabular foundation model and the neural-network sequence models (BiLSTM, 1D-CNN, Transformer) — improve classification of ASD-model (*Mthfr*-HET) versus wild-type pups over the inherited XGBoost baseline?
- **RQ2 — Which features.** Which acoustic characteristics drive the classification, and do a small number (two or three) of consistent features emerge?
- **RQ3 — Evaluation regime and generalization.** How does the data grouping and evaluation regime — *subject-dependent* versus *subject-independent* splits, and per-strain versus pooled cohorts — affect classification performance and, above all, generalization to **unseen mice**?
- **Engineering question.** Can the inherited, broken pipeline be rebuilt into a versioned, reproducible, end-to-end system with a single source of truth, enabling the biology researcher to curate data in parallel?

## 1.4 Contributions

This thesis makes the following contributions:

1. **A reproducible, documented pipeline** that takes raw 250 kHz recordings to trained classifiers and evaluation reports, replacing an inherited prototype that could not be run from a clean checkout (Chapter 7).
2. **A single source of truth for the data**, consolidated through a purpose-built graphical segmentation tool and a versioned baseline manifest, including the discovery and correction of an undocumented genotype-labelling error in the prior data (Chapters 3 and 7).
3. **A systematic model comparison** spanning tree-based tabular models (XGBoost, tuned XGBoost, TabPFN) and neural sequence models (BiLSTM, 1D-CNN, Transformer), under a controlled evaluation protocol (Chapters 4 and 5).
4. **An honest characterisation of generalization**, separating optimistic subject-dependent performance from leak-free subject-independent performance, and exposing a feature-level ceiling on minority-class precision (Chapters 5 and 6).
5. **A faithful account of the data-integrity finding** that the project's clean baseline is *lower* than a previously reported figure, and an analysis decomposing that difference into a data-correction effect and a leakage-removal effect ([[REF:F4b]]).

## 1.5 Thesis structure

Chapter 2 reviews ASD, USVs, and the relevant machine-learning literature, and situates this work within its research lineage. Chapter 3 describes the data: provenance, recording rig, cohorts, composition, and the single-source-of-truth story. Chapter 4 details the methods: segmentation and syllable typing, the two preprocessing representations, the models, and the evaluation protocol. Chapter 5 reports the experiments and results, including the master results table and the best model per scenario. Chapter 6 discusses what the results mean — which features matter, how well the models generalize, and why. Chapter 7 presents the reproducibility and engineering contribution. Chapter 8 states the limitations, and Chapter 9 concludes with future work.
