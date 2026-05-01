# Results — Pipeline Data, Random Split

**Data source:** `outputs/aggregated/all_data.csv` (9,515 rows, 87 mice)
**Split:** Random row-level (mouse overlap between train/test)
**Flags:** none (baseline)

```bash
python3 src/classification/train_classifier.py
```

Baseline model using pipeline-processed data with corrected genotype labels.
Random split allows mouse overlap, which inflates accuracy compared to group-aware split.
