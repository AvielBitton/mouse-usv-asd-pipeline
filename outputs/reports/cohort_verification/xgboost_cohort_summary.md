# Cohort verification (Phase B — Issue #47)

**Date:** 2026-05-19
**Data:** `outputs/external/aggregated/all_data_external_baseline.csv` (`--baseline`, post-revision `ad0fe57` — Noise==1 retained)
**Encoding:** `WT=0`, `HT/HET=1`. Numeric strain via `STRAIN_1_YEARS={2022,2023,2024}` (`src/preprocessing/utils/io_utils.py`).
**Encoding verification:** `cohort_encoding_report.md` — **PASS** (0 strain-text mismatches).

> **🛠 Revision:** Recording counts were refreshed after commit `ad0fe57` (the `noise` baseline filter was removed). Strain 1 grew 7,323 → 7,572 (+249) and Strain 2 grew 4,651 → 4,751 (+100); +349 total.

---

## A. Cohort counts on current baseline

| Cohort | `pup_strain` | Years | Recordings | Mice | WT | HT | HT % |
|--------|--------------|-------|-----------:|-----:|---:|---:|----:|
| 1 — Full | 1 + 2 | All | 12,323 | 106 | 9,283 | 3,040 | 24.7% |
| 2 — Classic BALB/C | 2 | 2015, 2018 | 4,751 | 47 | 3,392 | 1,359 | 28.6% |
| 3 — Mixed | 1 | 2022, 2023, 2024 | 7,572 | 59 | 5,891 | 1,681 | 22.2% |

(Computed directly from `all_data_external_baseline.csv` after `pup_strain` filtering — same path taken by `train_classifier.py --baseline --strain {1,2}`.)

---

## B. Legacy reference — pre-fix XGBoost cohort runs

The per-strain XGBoost runs that previously populated this report were trained on the **pre-noise-removal** baseline AND used the **legacy double-weighting** class-balance recipe (`sample_weight=balanced` + `scale_pos_weight=n_WT/n_HT`). They have been archived under `results/legacy/tabular_models/strain/` (see commit `7f88433`). Metrics retained here as a historical reference only; **do not compare** against Phase C runs without rerunning under the corrected weighting.

| Scenario | Cohort | Split | Train/Val/Test | SPW | Test acc | HT recall | HT prec | WT recall |
|----------|--------|-------|----------------|-----|---------:|----------:|--------:|----------:|
| C2_classic | Classic BALB/C (2015/2018) | dependent | 2790/930/931 | 2.4108 | 0.67 | 0.93 | 0.46 | 0.57 |
| C2_classic | Classic BALB/C (2015/2018) | independent | 2452/1080/1119 | 2.0688 | 0.70 | 0.58 | 0.40 | 0.74 |
| C3_mixed | Mixed (2022–2024) | dependent | 4393/1465/1465 | 3.5195 | 0.75 | 0.99 | 0.48 | 0.68 |
| C3_mixed | Mixed (2022–2024) | independent | 4068/1433/1822 | 3.3093 | 0.73 | 0.65 | 0.40 | 0.75 |

Legacy result directories:
- `results/legacy/tabular_models/strain/xgboost_strain2_subject_eval_{dependent,independent}_baseline/`
- `results/legacy/tabular_models/strain/xgboost_strain1_subject_eval_{dependent,independent}_baseline/`

---

## C. Phase C entry point

Per-strain training on the corrected baseline lives under Phase C:

- Scenario 2 (Classic BALB/C, strain 2) — **#49**
- Scenario 3 (Mixed, strain 1) — **#50**

Use `train_classifier.py --baseline --strain {1,2}` for the corrected (single-weighting) XGBoost and optionally the new tuned factories (`xgboost_tuned_dependent` / `xgboost_tuned_independent`) — see `outputs/reports/xgboost_tuning/xgboost_tuning_summary.md` for the tuning context. New results will land under `results/tabular_models/strain/`.
