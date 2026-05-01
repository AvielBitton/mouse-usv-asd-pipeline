# Results — Pipeline Data, Group-Aware Split

**Data source:** `outputs/aggregated/all_data.csv` (9,515 rows, 87 mice)
**Split:** Group-aware by mouse (no mouse appears in both train and test)
**Flags:** `--group-split`

```bash
python3 src/classification/train_classifier.py --group-split
```

Fair evaluation of the pipeline data — prevents data leakage by ensuring
all recordings from a given mouse stay in the same split.
