# Summary of Summaries: Strongest Models and Conclusions for the Thesis

A focused synthesis across all model families in the project. The task is binary classification of offspring genotype — wild-type (WT) vs *Mthfr*-HET (HT, the ASD-model minority, ~24% positive) — from isolation ultrasonic-vocalization (USV) acoustics. Every number below traces to the verified per-run READMEs, `results/tabular_models/threshold/summary_matrix.txt`, the neural-network master-metrics tables, and `docs/model_development_and_experiments.md`.

## 1. Headline result

The single defensible, honest result is **TabPFN on the subject-INDEPENDENT split** (split by mouse, 22 held-out animals, test = 2,139 recordings): test accuracy **0.729**, weighted F1 **0.743**, ROC-AUC **0.783**, HT F1 **0.610**, HT recall **0.782** (HT precision 0.499). This is within ~0.005 of the optimistic base model and nearly erases the usual 10–15-point dependent→independent generalization penalty. The frequently cited base number — untuned XGBoost, **acc 0.733 / weighted F1 0.749** — is an OPTIMISTIC, leaky, subject-DEPENDENT ceiling: its random row split shares 105 mice between train and test, so it measures memorization of seen animals, not generalization to new ones. It must be reported as a leaky ceiling, never as a new-mouse estimate.

## 2. Strongest models

- **Best on the HONEST (subject-independent) split:** TabPFN — leads overall accuracy (0.729), weighted F1 (0.743), and AUC (0.783). It is the runner-up on the minority class.
- **Best minority-class operating point on unseen mice:** tuned XGBoost (independent recipe) — HT recall 0.869 and HT F1 0.612 both beat TabPFN, at lower overall accuracy (0.702) and AUC (0.753). The right pick if catching ASD-model pups matters more than overall accuracy.
- **Best on the OPTIMISTIC (dependent) split:** TabPFN — tops every aggregate (acc 0.781, weighted F1 0.794, bal-acc 0.828, AUC 0.908, HT F1 0.688). The dependent and independent rankings are identical: **tabpfn > xgboost_tuned > xgboost(base)**.
- **Tabular vs sequence verdict:** tabular wins. The best honest sequence accuracy (1D-CNN 0.633) trails TabPFN (0.729) by ~10 points, and sequence models are operating-point-unstable. *Grain caveat:* tabular metrics are recording-level (test sets ~2,100–2,500 recordings); sequence metrics are session-level (only ~19 HT test sessions). A sequence accuracy is not substitutable for a tabular one — compare families and trends, not single decimals across the grain.

| Model | Split | Acc | wF1 | AUC | HT recall | HT prec | HT F1 |
|---|---|---|---|---|---|---|---|
| TabPFN | dependent | 0.781 | 0.794 | 0.908 | 0.918 | 0.550 | 0.688 |
| XGBoost tuned (dep) | dependent | 0.772 | 0.785 | 0.885 | 0.844 | 0.543 | 0.661 |
| XGBoost base (untuned) | dependent | 0.733 | 0.749 | 0.876 | 0.940 | 0.496 | 0.649 |
| TabPFN | independent | 0.729 | 0.743 | 0.783 | 0.782 | 0.499 | 0.610 |
| XGBoost tuned (indep) | independent | 0.702 | 0.719 | 0.753 | 0.869 | 0.473 | 0.612 |
| XGBoost base (untuned) | independent | 0.693 | 0.706 | 0.770 | 0.637 | 0.452 | 0.529 |

Sequence models report session-level metrics on a different grain (best A_control runs): Transformer dependent acc 0.659 / AUC 0.655; BiLSTM dependent AUC 0.790 but collapses to all-HT at the 0.5 cut (acc 0.232, bal-acc 0.500); 1D-CNN independent acc 0.633 / AUC 0.609.

A structural ceiling cuts across all six tabular runs: **HT precision is capped ~0.45–0.55** (0.452 untuned-independent to 0.550 TabPFN-dependent) regardless of family, tuning, or split. Roughly half of every model's HT calls are false positives at the default cut — this is a feature/data limit, not a model limit. The best tuned operating point on record is TabPFN dependent under the f1/target_recall objective: acc 0.819 / bal-acc 0.817 / HT recall 0.811 / HT precision 0.619 / WT recall 0.822.

## 3. Per-model one-liners

- **XGBoost (untuned, base):** the reproducible classical baseline over the lab's own 48-column summary statistics. Strength: highest HT recall of any run (0.940 dependent; misses only 39 of 647 pups). Weakness: that recall is bought with the lowest HT precision (0.496) and lowest dependent HT F1 (0.649); it pays the full generalization toll (acc −0.040, HT recall collapses 0.940→0.637) and is the weakest honest tabular model.
- **XGBoost (tuned):** tests whether hyperparameter search helps. Strength: the best minority operating point on unseen mice (independent HT recall 0.869). Weakness: the gain is modest and split-dependent; dependent (0.772) and independent (0.702) use different split-matched recipes, so it is not one model improving across splits.
- **TabPFN:** a data-efficient tabular foundation model, no tuning required. Strength: best overall on BOTH splits, highest dependent AUC (0.908), and almost no own-family generalization drop (acc 0.781→0.729, −0.052; only −0.004 vs the base). Weakness: the cost lands on the minority class (honest HT recall 0.782, misses ~1 in 5 HT pups); needs an external token/network access, and in non-threshold mode it merges validation into training (~80% vs XGBoost's train-only ~60%; XGBoost also uses the 20% val for early stopping). In THRESHOLD mode TabPFN instead keeps its validation split held out (training on ~60%) so the validation probabilities stay leak-free for deriving the cut.
- **BiLSTM (148,953 params):** best ranking signal of the sequence encoders (AUC 0.790 dep / 0.749 indep). Weakness: worst operating point — collapses to "predict HT for every session" at the 0.5 cut (23.2% acc, bal-acc 0.500, WT F1 0.00) unless rescued by the balanced sampler.
- **1D-CNN (86,041 params):** the convolutional sequence baseline. Strength: gives the best honest sequence accuracy (0.633). Weakness: weakest by AUC (~0.60, near chance) and fails the minority class on unseen mice (HT recall 0.316, 6/19 caught).
- **Transformer (72,537 params):** in its baseline (A_control) configuration the only sequence architecture that never collapses, giving the best baseline sequence run (dependent acc 0.659, bal-acc 0.668, HT F1 0.48) without rebalancing. Note: under other imbalance levers it does collapse (e.g. levers B/C/F drop it to bal-acc 0.500 / HT recall 0%). Weakness: still data-limited; its honest numbers do not beat the recording-level tabular anchor.

## 4. Decision-threshold tuning

Threshold tuning is leak-free, retrain-free hygiene: the cut is derived on the held-out validation split and frozen before touching the test split; AUC is unchanged. In threshold mode TabPFN keeps its validation split held out (training on ~60%, not the ~80% it uses in non-threshold mode) precisely so the validation probabilities are leak-free for deriving the cut. **Impact:** it relocates the operating point but cannot raise AUC or break the ~0.53 HT-precision wall. Best result: TabPFN dependent acc 0.783 @0.5 → 0.819 under the f1/target_recall cut (thr 0.617).

The right objective is split-dependent:
- **Subject-DEPENDENT (high AUC 0.876–0.908):** use **f1** (target_recall tracks it closely). It pushes the cut into the well-separated region and maximizes accuracy/balance. Youden lowers the cut, over-pushes HT recall, and costs accuracy (e.g. tuned XGBoost dep 0.771→0.731).
- **Subject-INDEPENDENT (weak AUC ~0.75–0.78):** use **target_recall** (HT-recall floor ≈0.80). Youden/f1/balanced all degenerate to a near-zero cut and a "predict-HT-for-almost-everyone" point — the inflated balanced accuracy ~0.797 is a book-keeping trap. The clearest tell: TabPFN/independent Youden (cut 0.005) confusion matrix [[926, 634],[1, 578]] — it lets just 1 true HT through and calls 634 WT as HT. Only target_recall holds WT recall ~0.62–0.68 with HT recall in a controlled 0.73–0.86 band — the deployable choice.

## 5. Strain cohorts

The 12-run strain matrix reveals an **interaction, not a single accuracy.** strain1 (2022–2024, mixed BALB/C+BLACK/C57, 7,572 recordings, 59 mice, HT ~22%) and strain2 (2015/2018, pure BALB/c, 4,751 recordings, 47 mice, HT ~28%) are indistinguishable on the leaky dependent split (acc ~0.75–0.80) but maximally divergent on the honest split. **strain1-independent inverts the usual penalty** (untuned XGBoost: acc 0.903, weighted F1 0.909, HT F1 0.753, +0.170 acc vs base; confusion [[1276,137],[28,252]]). **strain2-independent collapses on the minority class** (untuned XGBoost HT F1 0.122, recall 0.089; tuned 0.081; TabPFN degrades least at 0.388) — its 0.65 accuracy is a base-rate artifact. The cause is small-cohort/leak-free-split: strain2's 47 mice leave too few held-out HT animals; trees memorize (train acc up to 0.950). **Pooling caveat:** strain1 vs strain2 confounds background, year, and pool size, so the pooled corpus cannot distinguish "learned the ASD phenotype" from "learned which cohort a recording came from." Do not read the two strains across each other; any biological genotype claim needs a cross-cohort, background-controlled test.

## 6. The honest ceiling

The subject-independent number is the real one because it is the only split that does not share mice train↔test. That ceiling is **data-limited, not model-limited:** it is set by ~22 test mice / ~19 HT sessions, and HT precision is capped ~0.45–0.55 across every tabular configuration. The decisive evidence is the 5-fold CV of the best sequence recipe (balanced-sampler BiLSTM): the single-split independent win (bal-acc 0.704) was a **lucky fold** and does NOT survive — the pooled out-of-fold bal-acc is **0.559** independent (0.611 dependent), with the per-fold mean **0.563 ± 0.063** independent (0.609 ± 0.055 dependent) and per-fold accuracy spanning 0.284–0.753. Which fold a mouse lands in dominates the result more than the recipe. Report the fold mean ± std, never single-split point estimates.

## 7. Key takeaways

- Genotype is **barely separable across unseen mice** with these features — a weak-signal, small-cohort data ceiling, not a fixable modeling defect.
- The defensible honest headline is **TabPFN subject-independent** (acc 0.729 / wF1 0.743 / AUC 0.783 / HT F1 0.610 / HT recall 0.782), within ~0.005 of the optimistic base (0.733 / 0.749).
- The base 0.733 is a **leaky dependent ceiling** (105 mice shared train↔test), not a generalization estimate.
- Model ranking is stable on both splits: **tabpfn > xgboost_tuned > xgboost(base); tabular > sequence.**
- The **HT-precision ~0.50 wall** is a property of the features, not the estimator — it survives every model, tuning, and split.
- Threshold tuning is correct hygiene, not a SOTA advance; use f1 on dependent, target_recall on independent.
- From-scratch sequence models are under-powered **by the corpus, not their design.**

## 8. Suggested figures / tables for the paper

- **(a)** The model-ladder table (rung × model × representation × question answered).
- **(b)** Cross-model comparison tables, dependent vs independent at threshold 0.5 (the table in §2 above).
- **(c)** ROC curves with operating points — the AUC-vs-threshold diagnostic; the Transformer F_regsmall independent run (AUC 0.815 at balanced accuracy 0.500) is the clearest collapse illustration.
- **(d)** The A–H imbalance-lever matrix ranked by balanced accuracy.
- **(e)** The 5-fold CV deflation table (single-split 0.704 → fold mean 0.563 ± 0.063).
- **(f)** The strain × split interaction table (strain1 indep ≈0.90 vs strain2 indep ≈0.65; HT F1 ≈0.74 vs ≈0.20).
- **(g)** Cohort composition tables (genotype group × year, age coverage by year).

## 9. Open questions / limitations to acknowledge

- The honest signal is weak and data-limited — report the fold mean ± std (independent 0.563 ± 0.063), not the lucky-fold 0.704.
- The base 0.733 / 0.749 is optimistic and leaky (105 shared mice).
- Strain/year/background confound: a model could read cohort rather than genotype (strain1 indep ≈0.90 vs strain2 minority collapse HT F1 ≈0.08–0.39); the honest test is cross-cohort, which the within-cohort matrix cannot yet do.
- Tabular and sequence tracks are not trained on identical information (undefined-call handling, first-syllable handling, clipping, strain inclusion, recording vs session grain) — any cross-track comparison is representation+model, not a controlled model comparison.
- Metrics are recording-/session-level, not subject-level (the 0.733 dependent test spans 2,465 recordings; the independent split covers ~22 held-out mice) — consider per-mouse vote aggregation.
- HT precision is capped ~0.45–0.55; threshold tuning cannot fix it.
- NN class-collapse sensitivity: the avoiding lever is architecture-dependent (balanced sampler rescues BiLSTM; Transformer control is already best); all runs use seed 100, so re-seeding robustness is unmeasured — report the full lever sweep, not the best run.
- Threshold-objective choice must be fixed and justified; on weak-AUC independent splits Youden degenerates (TabPFN/indep cut 0.005).
- TabPFN caveats: merges validation into training in non-threshold mode (~80% vs 60% data) and needs an external token / network access, affecting exact reproducibility.

## 10. Future work / research still to do

1. **Pretrained / self-supervised sequence encoders** — pretrain on the full unlabeled syllable stream (125,576 syllables) before fine-tuning the few-hundred-session classifier, mirroring the upstream BiT R50x3 syllable classifier's ImageNet-21k pretraining. This is where pretraining + more data would move the needle.
2. **Richer per-call contour features** — the tabular set carries only 4 acoustic descriptors per type (start/end/relative frequency, duration); modern bioacoustics traces the full contour (mean/min/max/slope, bandwidth, FM depth). The clearest feature-side upgrade, since the HT-precision wall is a feature property.
3. **More data / more litters** — the independent ceiling is set by ~22 test mice / ~19 HT sessions; additional litters help more than any architecture change.
4. **Nested cross-validation** — tuned XGBoost uses a single held-out test after CV selection; nested CV gives honest, variance-quantified estimates. Run the `--cv-folds 5` check for the tabular models before publishing their independent numbers.

## 11. Where the detail lives

- **Master reference:** `docs/model_development_and_experiments.md` (§3 tabular, §4 sequence, §5 threshold, §6 strain, §7 cross-model, §8 SOTA/ceiling, §9 open questions).
- **Tabular runs:** `results/tabular_models/<run>/README.md`; aggregate matrix `results/tabular_models/threshold/summary_matrix.txt`; objectives `results/tabular_models/threshold_objectives/summary_objectives.txt`.
- **Strain matrix:** `results/tabular_models/strain/README.md` and per-run `logs/out.txt`.
- **Sequence runs:** `results/neural_networks/executive_summaries/sequence_models/master_metrics.md` and `results/neural_networks/experiments/_summary/master_metrics.md`.
- **Cohort/data:** `docs/research_data_and_recording.md`; preprocessing `docs/preprocessing_pipeline.md`.
