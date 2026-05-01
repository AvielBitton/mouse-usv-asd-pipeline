# Results — External Data, Group-Aware Split

**Data source:** `outputs/aggregated_external/all_data_external.csv` (13,081 rows, 115 mice)
**Split:** Group-aware by mouse (no mouse appears in both train and test)
**Flags:** `--external --group-split`

```bash
python3 src/classification/tabular/train_classifier.py --external --group-split
```

Most rigorous evaluation: correct genotype labels, more data, and no data leakage.
This is the most honest measure of model generalization to unseen mice.
