# Results — Pipeline Data, Subject-Independent Evaluation

**Data source:** `outputs/aggregated/all_data.csv` (9,515 rows, 87 mice)
**Evaluation:** Subject-independent — group split by subject (no subject in more than one set)
**Flags:** `--group-split` or `--independent`

```bash
python3 src/classification/tabular/train_classifier.py --group-split
```

Fair evaluation of the pipeline data — prevents data leakage by keeping
all recordings from a given subject in the same split.
