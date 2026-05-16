# Cohort encoding verification

**Generated:** 2026-05-16T14:04:12Z
**Input:** `outputs/external/input/segmentation_classification_all_data.xlsx`
**Status:** PASS

## Summary

Classic years [2015, 2018] → pup_strain=2: OK. Mixed years [2022, 2023, 2024] → pup_strain=1: OK. Total strain text mismatches: 0.

## By year (syllable-level input)

| Year | Syllable rows | Recordings | Dominant Strain text | Expected `pup_strain` | Text mismatches |
|------|---------------|------------|----------------------|----------------------|-----------------|
| 2015 | 35,680 | 2,526 | balb/c | 2 | 0 |
| 2018 | 10,730 | 961 | balb/c | 2 | 0 |
| 2022 | 30,894 | 1,815 | balb/c+black/c57 | 1 | 0 |
| 2023 | 21,543 | 1,501 | balb/c+black/c57 | 1 | 0 |
| 2024 | 26,729 | 1,655 | balb/c+black/c57 | 1 | 0 |

## Baseline aggregate (`pup_strain`)

- Recording rows: **11,974**
- `pup_strain=1` (Mixed cohort): **7,323**
- `pup_strain=2` (Classic BALB/C): **4,651**
