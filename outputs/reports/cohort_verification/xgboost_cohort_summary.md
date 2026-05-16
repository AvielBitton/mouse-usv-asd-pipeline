# XGBoost cohort validation (Scenarios 2–3)

**Date:** 2026-05-16  
**Model:** XGBoost, `both_dynamic` balance, threshold 0.5  
**Data:** `all_data_external_baseline.csv` + `--strain` filter

## Results

| Scenario | Cohort | Split | Train/Val/Test | SPW | Test acc | HT recall | HT prec | WT recall |
|----------|--------|-------|----------------|-----|----------|-----------|---------|-----------|
| C2_classic | Classic BALB/C (2015/2018) | dependent | 2790/930/931 | 2.4108 | 0.67 | 0.93 | 0.46 | 0.57 |
| C2_classic | Classic BALB/C (2015/2018) | independent | 2452/1080/1119 | 2.0688 | 0.70 | 0.58 | 0.40 | 0.74 |
| C3_mixed | Mixed (2022–2024) | dependent | 4393/1465/1465 | 3.5195 | 0.75 | 0.99 | 0.48 | 0.68 |
| C3_mixed | Mixed (2022–2024) | independent | 4068/1433/1822 | 3.3093 | 0.73 | 0.65 | 0.40 | 0.75 |

## Insights

- **Classic BALB/C (strain 2)** — ~4,651 recordings. Dependent split shows high HT recall (0.93) but optimistic (mouse overlap). **Independent** is the generalization metric: HT recall **0.58**, WT recall **0.74** — harder cohort than Mixed.
- **Mixed (strain 1)** — ~7,323 recordings. Dependent HT recall **0.99**; independent **0.65** with test acc **0.73** (vs full-baseline independent **0.58** on all strains).
- **Pattern:** `both_dynamic` pushes HT recall up on dependent splits; independent splits trade HT recall for WT precision/recall balance.
- Encoding year↔strain: **PASS** — [`cohort_encoding_report.md`](cohort_encoding_report.md). Training uses `--baseline --strain {1,2}` only (no extra cohort CSV).

## Result directories

- `results/tabular_models/strain/xgboost_strain2_subject_eval_{dependent,independent}_baseline/`
- `results/tabular_models/strain/xgboost_strain1_subject_eval_{dependent,independent}_baseline/`
