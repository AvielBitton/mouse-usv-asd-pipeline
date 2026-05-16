# External input data

Canonical syllable-level source for all **baseline** training runs (Issue #42 / #46).

| File | Role |
|------|------|
| `segmentation_classification_all_data.xlsx` | Primary input for aggregation |
| `segmentation_classification_all_data.csv` | Synced copy (sequence pipeline cache) |
| `backup/` | Previous input versions |

**Requirements before regenerating aggregates:**

1. Issue #34 corrections (commit `791aa05`)
2. `Session=0` → `1` applied in the workbook (not only at runtime)

**Regenerate outputs:**

```bash
.venv/bin/python scripts/run_external_aggregation.py
```

**Row counts and provenance:** [`docs/BASELINE_DATA_MANIFEST.md`](../../../docs/BASELINE_DATA_MANIFEST.md)
