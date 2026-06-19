# Data Pipeline v2 — Phase 1 Design (AQI keystone + cleaner + legacy recompute)

**Date:** 2026-06-19
**Status:** Approved
**Part of:** the "continuous, self-cleaning data pipeline (v2)" vision — see
`docs/superpowers/future-plans.md` for the overall roadmap (Phases 2–4).

## Why (problem)

The dataset is frozen at 2020-07-01 and its cleaning is crude and inconsistent:
- The city pipeline drops `AQI > 500`; the **station pipeline has no cap at all** (its max
  AQI is **727** — physically impossible; CPCB AQI maxes at 500).
- Even "valid" rows are internally inconsistent: the precomputed AQI does not track the
  pollutant columns (e.g. Hyderabad 2016-10-30: PM2.5 = 516 µg/m³ but AQI = 487; 2016-07-12:
  AQI = 495 with PM2.5 = 206). The AQI was computed elsewhere and ships as-is.

Phase 1 makes the **existing** 2015–2020 data internally consistent and properly cleaned,
WITHOUT fetching any new data — purely a transform of the current parquets with additive
columns. It is independently valuable (fixes the 727 + inconsistency) and de-risks every
later phase, because the AQI and cleaning modules it builds are reused by Phase 2+.

## Scope

**In scope (Phase 1):**
- A new testable `pipeline/` package: `aqi.py` (CPCB sub-index AQI), `clean.py` (layered
  cleaning), `report.py` (data-quality report), `build.py` (Phase-1 transform of existing
  parquets).
- Recompute AQI for the existing city AND Bangalore-station parquets from their pollutant
  columns, using one consistent CPCB formula.
- Additive, backward-compatible schema columns (see below). `AQI`/`AQI_Bucket` become the
  recomputed values; the original CPCB AQI is preserved, never destroyed.
- Unit tests for `aqi.py` (vs known CPCB reference values) and `clean.py`.
- A printed/markdown **data-quality report** comparing recomputed vs original AQI (counts,
  distribution shift, how many rows flagged) for human review BEFORE redeploying.
- Regenerate both parquets, sync to `hf-space/`, redeploy + verify (existing flow).

**Out of scope (later phases, see future-plans.md):** OpenAQ ingestion, any NEW data, the
2020→now backfill, GitHub Actions automation, the validation gate, dynamic date framing,
and the freshness badge.

## Data strategy (Phase 1 operates on the cleaned parquets, not raw CSVs)

Phase 1 transforms the EXISTING `data/processed/*.parquet` in place (additively). It does
NOT depend on the raw Kaggle CSVs (which may not be present) and does NOT fetch anything.
The pollutant columns already in the parquets are the inputs to AQI recompute + cleaning.

## Schema (additive, backward-compatible — nothing breaks)

Existing columns are kept. Consumers read `City, Date, PM2.5, PM10, NO2, SO2, O3, CO, NH3,
AQI, AQI_Bucket, Year, Month, MonthName, Season` (+ station fields) — all still present with
the same names. Changes:

- `AQI` — now the **recomputed** CPCB AQI (what the app/MCP read; no consumer change needed).
- `AQI_Bucket` — derived from the new `AQI` (same `classify_aqi` thresholds).
- `AQI_cpcb_original` — **new**: the original CPCB AQI value, preserved for comparison/audit.
- `quality_flag` — **new**: `"ok"` (default), `"imputed_bound"` (a pollutant was nulled by a
  physical bound), or `"flagged_spike"` (statistical outlier flagged but value KEPT). If both
  apply, comma-joined (e.g. `"imputed_bound,flagged_spike"`).
- `dominant_pollutant` — **new**: the pollutant driving the AQI (argmax sub-index); `null`
  when AQI is null.
- `source` — **new**: `"kaggle_cpcb"` for all Phase-1 rows (Phase 2 adds `"openaq"`).

Recomputed AQI is structurally bounded to ≤ 500 (each sub-index caps at 500), so the
station 727 is fixed for free.

## `pipeline/aqi.py` — the CPCB AQI keystone

Implements India's National AQI (CPCB, 2014): per-pollutant sub-index via linear
interpolation within breakpoint buckets, AQI = max of available sub-indices.

**Breakpoint tables** (concentration → sub-index). Units match the dataset: µg/m³ for all
except CO in mg/m³. Our data is daily averages; O3 and CO use the daily value as a proxy for
the 8-hr metric (an accepted approximation, consistent with the original Kaggle AQI). Each
row is `(C_lo, C_hi, I_lo, I_hi)`:

```
PM2.5: (0,30,0,50) (30,60,51,100) (60,90,101,200) (90,120,201,300) (120,250,301,400) (250,500,401,500)
PM10 : (0,50,0,50) (50,100,51,100) (100,250,101,200) (250,350,201,300) (350,430,301,400) (430,600,401,500)
NO2  : (0,40,0,50) (40,80,51,100) (80,180,101,200) (180,280,201,300) (280,400,301,400) (400,1000,401,500)
O3   : (0,50,0,50) (50,100,51,100) (100,168,101,200) (168,208,201,300) (208,748,301,400) (748,1000,401,500)
CO   : (0,1.0,0,50) (1.0,2.0,51,100) (2.0,10,101,200) (10,17,201,300) (17,34,301,400) (34,50,401,500)   # mg/m³
SO2  : (0,40,0,50) (40,80,51,100) (80,380,101,200) (380,800,201,300) (800,1600,301,400) (1600,2620,401,500)
NH3  : (0,200,0,50) (200,400,51,100) (400,800,101,200) (800,1200,201,300) (1200,1800,301,400) (1800,2400,401,500)
```

Sub-index formula within a bucket:
`I = (I_hi - I_lo)/(C_hi - C_lo) * (C - C_lo) + I_lo`, rounded to int. A concentration above
the top bucket caps at 500.

**Breakpoints verified against official CPCB documentation (2026-06-19).** The lower five
bands (Good→Very Poor) for every pollutant above were confirmed to match the official CPCB
National AQI table exactly — see [CPCB About_AQI](https://www.cpcb.nic.in/National-Air-Quality-Index/)
and the [AQI Hub India reference](https://aqihub.info/indices/india). **Caveat:** the
official **Severe (401–500) band is open-ended** in CPCB's documentation (listed as "250+",
"430+", "1600+", etc. with no upper concentration bound). Linear interpolation needs an upper
bound, so the Severe-band `C_hi` values above (PM2.5 500, PM10 600, NO2 1000, O3 1000, CO 50,
SO2 2620, NH3 2400) are an explicit, documented engineering choice; any concentration at or
beyond `C_hi` clamps the sub-index to **500**. This only affects the exact number (e.g. 470
vs 490) of already-Severe days — never the category — and bounds recomputed AQI to ≤500
(fixing the station 727). Implementation must keep these breakpoints in one named constant so
they can be re-verified/adjusted in isolation.

**CPCB validity rule:** AQI requires **at least 3 pollutants** present AND at least one of
PM2.5/PM10. Otherwise AQI is `null` and `dominant_pollutant` is `null` (Bucket "Unknown").

Public API:
- `sub_index(pollutant: str, concentration: float) -> int | None`
- `compute_aqi(concentrations: dict[str, float|None]) -> tuple[int|None, str|None]`
  returns `(aqi, dominant_pollutant)`.

## `pipeline/clean.py` — layered cleaning (flag, don't delete)

Operates on a city/station daily frame. Two layers:

1. **Physical bounds** — null pollutant concentrations that are physically impossible
   (sensor errors), and negative values. Generous caps so real extreme events survive:
   `PM2.5≤1000, PM10≤2000, NO2≤500, SO2≤2000, O3≤800, CO≤50 (mg/m³), NH3≤2000`. A nulled
   value sets `quality_flag` to include `"imputed_bound"`.
2. **Statistical flag** — per `(City|StationShort, pollutant)`, ordered by Date, a centered
   rolling window (default 15 days) median + MAD; robust z = `0.6745*(x-median)/MAD`. Flag a
   point as `"flagged_spike"` when `|z| > 10` (conservative) AND it is **isolated** (its
   immediate neighbors are not themselves extreme) — so sustained real events (Diwali,
   stubble burning) are NOT flagged. **Flagged values are KEPT**, only marked. MAD==0
   windows are skipped (no flag).

Public API:
- `apply_physical_bounds(df) -> df` (nulls impossible values, sets flags)
- `flag_statistical_outliers(df, group_col) -> df` (adds/extends `quality_flag`)
- `clean(df, group_col) -> df` (runs both)

AQI is recomputed AFTER cleaning, so a bad pollutant never inflates AQI.

## `pipeline/build.py` — Phase-1 transform

`rebuild_phase1()`:
1. Load `data/processed/city_day_clean.parquet` and `station_day_blr_clean.parquet`.
2. Stash original AQI into `AQI_cpcb_original`.
3. `clean(df, group_col)` (group by `City` / `StationShort`).
4. Recompute `AQI`, `dominant_pollutant` row-wise from cleaned pollutants via
   `compute_aqi`. Recompute `AQI_Bucket` from new `AQI`.
5. Set `source="kaggle_cpcb"`.
6. Write parquets back (same paths). Build the data-quality report via `pipeline.report`
   (print it AND write `reports/data_quality_phase1.md`).

A `--report-only` flag computes and prints the report WITHOUT writing, for the pre-ship
human review (tread-lightly gate).

### Data-quality report (`pipeline/report.py`)

`build_report(before_df, after_df) -> str` produces a markdown report, printed to the
console AND written to `reports/data_quality_phase1.md` (committed, so the review is
auditable). Computed separately for the city and station parquets. It MUST contain these
explicit metrics:

**Volume & coverage**
- Total rows; date range (must be unchanged); cities/stations covered (must be unchanged).

**AQI change**
- Rows where both old and new AQI are non-null; of those, count & % where AQI changed.
- Absolute AQI delta `|new − old|`: mean, median, p90, p99, and max.
- Rows where AQI flipped null→value and value→null (with counts).
- Confirm `new AQI.max() <= 500` (the 727 fix) — fail the report loudly if not.

**Bucket migration**
- A bucket-migration matrix: counts of `old AQI_Bucket → new AQI_Bucket` (rows that changed
  category), so reviewers see which categories shifted.

**Cleaning actions**
- Per-pollutant count of values nulled by physical bounds (`imputed_bound`).
- Count & % of rows flagged `flagged_spike`, broken down per city/station.

**Largest-change analysis (required)**
- A table of the **top-20 rows by `|ΔAQI|`**, each showing City/Station, Date, old AQI, new
  AQI, Δ, new `dominant_pollutant`, and the contributing pollutant concentrations — so a
  human can judge whether each large change is justified (e.g. an inconsistent original AQI
  being corrected) rather than a new error.
- A per-city/station summary: mean Δ and max Δ AQI.

This report is what the human reads at the deploy gate before anything is shipped.

## Consumers (no breaking changes)

All pages/MCP read `AQI`/`AQI_Bucket`/pollutants, which still exist. Optional tiny
enhancement (YAGNI — note only, not required in Phase 1): `pages/City_Overview.py` and
`pages/Bangalore_Deep_Dive.py` currently derive a dominant pollutant heuristically; they
could later read the new `dominant_pollutant` column. Not done in Phase 1.

## Testing

- `tests/test_aqi.py`: `sub_index`/`compute_aqi` vs hand-computed CPCB reference values
  (e.g. PM2.5=75 → sub-index in the 101–200 band; a multi-pollutant case where PM2.5
  dominates; the <3-pollutant rule returns `(None, None)`; a >top-bucket value caps at 500).
- `tests/test_clean.py`: a 5000 µg/m³ PM2.5 is nulled + flagged `imputed_bound`; a single
  isolated 10× spike is flagged `flagged_spike` (value retained); a sustained multi-day high
  plateau is NOT flagged; MAD==0 window produces no flags.
- **`tests/test_pipeline_regression.py` (end-to-end fixture — required):** a small committed
  fixture `tests/fixtures/sample_city_day.parquet` (~12 hand-crafted rows for 2 cities) that
  deliberately covers every transform path:
  - a normal multi-pollutant row with a **hand-computed expected AQI + dominant_pollutant**,
  - a row with an impossible pollutant (PM2.5 = 5000) → nulled, `quality_flag` contains
    `imputed_bound`,
  - an isolated single-day spike → `flagged_spike`, value retained,
  - a row with <3 pollutants → AQI/`dominant_pollutant` null, Bucket `Unknown`,
  - a row whose original AQI is inconsistent with its pollutants → corrected new AQI.
  The test runs the FULL `rebuild_phase1` transform on the fixture (not the real data) and
  asserts the entire output frame: every expected column present, exact AQI/Bucket/
  `dominant_pollutant`/`quality_flag`/`source` values, `AQI_cpcb_original` equals the input
  AQI, and **idempotency** (running the transform twice yields the same result). This locks
  the whole Phase-1 pipeline against regressions, not just the units.
- Existing `tests/test_mcp_tools.py` must still pass (recompute keeps AQI ∈ [0,500] and the
  schema intact).

## Deploy (careful, human-gated)

1. Run `python -m pipeline.build --report-only`; **human reviews** the data-quality report
   (distribution shift, flagged counts) before proceeding.
2. Run the real rebuild; run full `pytest`.
3. `cp` both parquets to `hf-space/`; redeploy via `HfApi().upload_folder` and verify with
   `scripts/verify_hf_deploy.py`.
4. Commit (git-lfs) and push.

## Verification (Done criteria)

1. `pytest -q` green: the new `test_aqi.py`, `test_clean.py`, the end-to-end
   `test_pipeline_regression.py` (fixture), and the existing suite.
2. Recomputed parquets: `AQI.max() <= 500` for BOTH city and station; every existing column
   still present; new columns populated; `AQI_cpcb_original` retains the old values.
3. `reports/data_quality_phase1.md` exists with all required metrics + the top-20
   largest-change table, and shows the recompute is sane (no mass-nulling of AQI; flagged
   rows a small %; distribution shift explainable).
4. AQI breakpoints in code match the verified CPCB table (lower bands) with the documented
   Severe-band convention; held in one named constant.
5. HF Space verified serving (11 tools, parquets load).

## Watch-outs (tread lightly)

- Recomputing AQI WILL change historical numbers slightly vs the original CPCB values — this
  is expected and the point (consistency). The report quantifies it; a human reviews before
  shipping. `AQI_cpcb_original` keeps the originals for audit.
- Keep the server Streamlit-free and the two server copies byte-identical (unchanged here —
  Phase 1 touches data + `pipeline/`, not `air_quality_mcp.py`).
- `hf-space/.gitattributes` must keep `*.parquet filter=lfs ...` (already fixed).
- Commit messages: NO `Co-Authored-By` trailer.
- Don't over-engineer the statistical flag — conservative threshold; never delete.
