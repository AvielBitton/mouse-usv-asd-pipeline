# Results — External Data, Subject-Independent Evaluation

**Data source:** `outputs/aggregated_external/all_data_external.csv` (13,081 rows, 115 mice)
**Evaluation:** Subject-independent — group split by subject (no subject in more than one set)
**Flags:** `--external --group-split` (or `--external --independent`)

```bash
python3 src/classification/tabular/train_classifier.py --external --group-split
```

Most rigorous setting: correct genotyping and no leakage across subjects.
