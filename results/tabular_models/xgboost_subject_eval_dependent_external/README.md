# Results — External Data, Subject-Dependent Evaluation

**Data source:** `outputs/aggregated_external/all_data_external.csv` (13,081 rows, 115 mice)
**Evaluation:** Subject-dependent — random row-level split (subject overlap between train/test)
**Flags:** `--external`

```bash
python3 src/classification/tabular/train_classifier.py --external
```

Uses the external segmentation file which contains correct individual genotyping
and 28 additional mice (including 24 from 2024 that were missing from the pipeline due to absent Sex data).
