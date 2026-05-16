# Results — Pipeline Data, Subject-Dependent Evaluation

**Data source:** `outputs/aggregated/all_data.csv` (9,515 rows, 87 mice)
**Evaluation:** Subject-dependent — random row-level split (subject overlap between train/test)
**Flags:** none (baseline)

```bash
python3 src/classification/tabular/train_classifier.py
```

Baseline model using pipeline-processed data with corrected genotype labels.
Subject-dependent split allows overlap across sets, which inflates accuracy compared to subject-independent evaluation.
