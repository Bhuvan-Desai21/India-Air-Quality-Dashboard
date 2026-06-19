# Data Pipeline v2 — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing 2015–2020 city + Bengaluru-station data internally consistent and properly cleaned by recomputing CPCB AQI from pollutants through a new testable `pipeline/` package, with additive schema columns — backward-compatible, validated, and shipped.

**Architecture:** A new `pipeline/` package — `aqi.py` (CPCB sub-index AQI), `clean.py` (physical bounds + statistical spike flagging), `report.py` (data-quality report), `build.py` (the Phase-1 transform). It transforms the existing `data/processed/*.parquet` in place, additively (no new data, no network). `AQI`/`AQI_Bucket` become the recomputed values; the originals are preserved in `AQI_cpcb_original`.

**Tech Stack:** Python 3.13, pandas, numpy, pyarrow, pytest.

Spec: `docs/superpowers/specs/2026-06-19-data-pipeline-phase1-design.md`
Branch: `feat/data-pipeline-phase1` (already created; spec + roadmap already committed).

**Repo rules:** Use `.venv/Scripts/python.exe` (NOT bare `python`). Commit messages: NO `Co-Authored-By` trailer.

---

### Task 1: `pipeline` package + CPCB AQI module

**Files:**
- Create: `pipeline/__init__.py`
- Create: `pipeline/aqi.py`
- Test: `tests/test_aqi.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_aqi.py`:

```python
from pipeline.aqi import sub_index, compute_aqi, BREAKPOINTS


def test_sub_index_boundaries_are_exact():
    assert sub_index("PM2.5", 0) == 0
    assert sub_index("PM2.5", 90) == 200      # top of the 101-200 band
    assert sub_index("PM2.5", 120) == 300
    assert sub_index("PM10", 100) == 100
    assert sub_index("CO", 1.0) == 50         # CO is mg/m3


def test_sub_index_clamps_above_top_bucket():
    assert sub_index("PM2.5", 600) == 500     # beyond top C_hi -> 500
    assert sub_index("PM10", 99999) == 500


def test_sub_index_rejects_bad_input():
    assert sub_index("PM2.5", None) is None
    assert sub_index("PM2.5", -5) is None
    assert sub_index("radon", 10) is None


def test_compute_aqi_max_of_subindices_with_dominant():
    aqi, dom = compute_aqi({"PM2.5": 90, "PM10": 100, "NO2": 40})
    assert aqi == 200 and dom == "PM2.5"


def test_compute_aqi_requires_three_pollutants():
    # only 2 pollutants -> invalid
    assert compute_aqi({"PM2.5": 90, "NO2": 40}) == (None, None)


def test_compute_aqi_requires_a_pm_pollutant():
    # 3 pollutants but no PM2.5/PM10 -> invalid
    assert compute_aqi({"NO2": 40, "SO2": 40, "O3": 50}) == (None, None)


def test_breakpoints_cover_seven_pollutants():
    assert set(BREAKPOINTS) == {"PM2.5", "PM10", "NO2", "O3", "CO", "SO2", "NH3"}
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_aqi.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline'`.

- [ ] **Step 3: Create the package**

Create `pipeline/__init__.py` (empty file).

- [ ] **Step 4: Implement `pipeline/aqi.py`**

```python
"""CPCB National Air Quality Index (2014) computation.

Sub-index per pollutant via linear interpolation within breakpoint buckets;
AQI = max of available sub-indices. The lower five bands (Good..Very Poor) are
verified against official CPCB documentation. The Severe (401-500) band is
open-ended officially, so its upper concentration bound below is a documented
convention and the sub-index clamps at 500.
"""

from __future__ import annotations

# (C_lo, C_hi, I_lo, I_hi). Units: ug/m3 except CO in mg/m3.
BREAKPOINTS: dict[str, list[tuple[float, float, int, int]]] = {
    "PM2.5": [(0, 30, 0, 50), (30, 60, 51, 100), (60, 90, 101, 200),
              (90, 120, 201, 300), (120, 250, 301, 400), (250, 500, 401, 500)],
    "PM10":  [(0, 50, 0, 50), (50, 100, 51, 100), (100, 250, 101, 200),
              (250, 350, 201, 300), (350, 430, 301, 400), (430, 600, 401, 500)],
    "NO2":   [(0, 40, 0, 50), (40, 80, 51, 100), (80, 180, 101, 200),
              (180, 280, 201, 300), (280, 400, 301, 400), (400, 1000, 401, 500)],
    "O3":    [(0, 50, 0, 50), (50, 100, 51, 100), (100, 168, 101, 200),
              (168, 208, 201, 300), (208, 748, 301, 400), (748, 1000, 401, 500)],
    "CO":    [(0, 1.0, 0, 50), (1.0, 2.0, 51, 100), (2.0, 10, 101, 200),
              (10, 17, 201, 300), (17, 34, 301, 400), (34, 50, 401, 500)],
    "SO2":   [(0, 40, 0, 50), (40, 80, 51, 100), (80, 380, 101, 200),
              (380, 800, 201, 300), (800, 1600, 301, 400), (1600, 2620, 401, 500)],
    "NH3":   [(0, 200, 0, 50), (200, 400, 51, 100), (400, 800, 101, 200),
              (800, 1200, 201, 300), (1200, 1800, 301, 400), (1800, 2400, 401, 500)],
}

MIN_POLLUTANTS = 3
PM_POLLUTANTS = ("PM2.5", "PM10")


def sub_index(pollutant: str, concentration: float | None) -> int | None:
    """Linear-interpolated CPCB sub-index, or None for missing/negative/unknown."""
    if pollutant not in BREAKPOINTS or concentration is None or concentration < 0:
        return None
    table = BREAKPOINTS[pollutant]
    c = float(concentration)
    for c_lo, c_hi, i_lo, i_hi in table:
        if c_lo <= c <= c_hi:
            return round((i_hi - i_lo) / (c_hi - c_lo) * (c - c_lo) + i_lo)
    if c > table[-1][1]:  # beyond the top bucket -> clamp
        return 500
    return None


def compute_aqi(concentrations: dict[str, float | None]) -> tuple[int | None, str | None]:
    """CPCB AQI = max sub-index. Requires >=3 pollutants incl. PM2.5/PM10.

    Returns (aqi, dominant_pollutant) or (None, None) if the validity rule is unmet.
    """
    subs: dict[str, int] = {}
    for pol in BREAKPOINTS:
        si = sub_index(pol, concentrations.get(pol))
        if si is not None:
            subs[pol] = si
    has_pm = any(p in subs for p in PM_POLLUTANTS)
    if len(subs) < MIN_POLLUTANTS or not has_pm:
        return None, None
    dominant = max(subs, key=subs.get)
    return subs[dominant], dominant
```

- [ ] **Step 5: Run to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_aqi.py -q`
Expected: PASS (7 tests).

- [ ] **Step 6: Commit**

```bash
git add pipeline/__init__.py pipeline/aqi.py tests/test_aqi.py
git commit -m "feat(pipeline): CPCB AQI sub-index module with verified breakpoints"
```

---

### Task 2: Cleaning — physical bounds

**Files:**
- Create: `pipeline/clean.py`
- Test: `tests/test_clean.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_clean.py`:

```python
import numpy as np
import pandas as pd
from pipeline.clean import apply_physical_bounds, PHYSICAL_MAX


def _frame(pm25_values):
    n = len(pm25_values)
    return pd.DataFrame({
        "City": ["A"] * n,
        "Date": pd.date_range("2020-01-01", periods=n),
        "PM2.5": pm25_values,
        "PM10": [100.0] * n,
    })


def test_physical_bounds_nulls_impossible_and_flags():
    df = apply_physical_bounds(_frame([90.0, 5000.0, 90.0]))
    assert np.isnan(df.loc[1, "PM2.5"])           # impossible value nulled
    assert df.loc[1, "quality_flag"] == "imputed_bound"
    assert df.loc[0, "quality_flag"] == "ok"      # normal row untouched
    assert df.loc[0, "PM2.5"] == 90.0


def test_physical_bounds_nulls_negative():
    df = apply_physical_bounds(_frame([-3.0, 90.0]))
    assert np.isnan(df.loc[0, "PM2.5"])
    assert "imputed_bound" in df.loc[0, "quality_flag"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_clean.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline.clean'`.

- [ ] **Step 3: Implement `pipeline/clean.py` (physical bounds first)**

```python
"""Layered cleaning: physical bounds (null impossible values) then statistical
spike flagging. Both record provenance in a `quality_flag` column. Physical
bounds NULL the value; spike flagging KEEPS the value and only marks it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Generous per-pollutant plausible maxima (above real extreme events) so only
# sensor errors are nulled. Units match the data: ug/m3 except CO in mg/m3.
PHYSICAL_MAX: dict[str, float] = {
    "PM2.5": 1000.0, "PM10": 2000.0, "NO2": 500.0,
    "SO2": 2000.0, "O3": 800.0, "CO": 50.0, "NH3": 2000.0,
}
POLLUTANTS = list(PHYSICAL_MAX)

SPIKE_WINDOW = 15
SPIKE_Z = 10.0


def _ensure_flag(df: pd.DataFrame) -> pd.DataFrame:
    if "quality_flag" not in df.columns:
        df["quality_flag"] = "ok"
    return df


def _add_flag(df: pd.DataFrame, mask: pd.Series, label: str) -> None:
    sel = df.loc[mask, "quality_flag"]
    df.loc[mask, "quality_flag"] = sel.apply(
        lambda v: label if v == "ok" else f"{v},{label}"
    )


def apply_physical_bounds(df: pd.DataFrame) -> pd.DataFrame:
    """Null physically impossible / negative pollutant values; flag those rows."""
    df = _ensure_flag(df.copy())
    for pol, hi in PHYSICAL_MAX.items():
        if pol not in df.columns:
            continue
        bad = df[pol].notna() & ((df[pol] < 0) | (df[pol] > hi))
        if bad.any():
            _add_flag(df, bad, "imputed_bound")
            df.loc[bad, pol] = np.nan
    return df
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_clean.py -q`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add pipeline/clean.py tests/test_clean.py
git commit -m "feat(pipeline): physical-bounds cleaning (null impossible values, flag rows)"
```

---

### Task 3: Cleaning — statistical spike flagging

**Files:**
- Modify: `pipeline/clean.py` (add `flag_statistical_outliers` + `clean`)
- Test: `tests/test_clean.py` (add cases)

- [ ] **Step 1: Add failing tests**

Append to `tests/test_clean.py`:

```python
from pipeline.clean import flag_statistical_outliers, clean


def _series_frame(values):
    n = len(values)
    return pd.DataFrame({
        "City": ["A"] * n,
        "Date": pd.date_range("2020-01-01", periods=n),
        "PM2.5": [float(v) for v in values],
        "PM10": [100.0] * n,
    })


def test_isolated_spike_is_flagged_and_value_kept():
    vals = [80, 100] * 7         # 14 rows, varied baseline (MAD>0)
    vals.insert(7, 500)          # one isolated spike
    df = flag_statistical_outliers(_series_frame(vals), "City")
    spike_row = df[df["PM2.5"] == 500].iloc[0]
    assert "flagged_spike" in spike_row["quality_flag"]
    assert spike_row["PM2.5"] == 500.0       # value retained, not deleted


def test_sustained_plateau_is_not_flagged():
    # a real multi-day high plateau must NOT be flagged
    vals = [80, 100] * 5 + [500] * 6 + [80, 100] * 5
    df = flag_statistical_outliers(_series_frame(vals), "City")
    assert (df["quality_flag"] == "ok").all()


def test_zero_mad_window_produces_no_flag():
    df = flag_statistical_outliers(_series_frame([90] * 20), "City")
    assert (df["quality_flag"] == "ok").all()


def test_clean_runs_both_layers():
    df = clean(_series_frame([90, 5000, 90, 90, 90]), "City")
    assert "imputed_bound" in df.loc[df["PM2.5"].isna(), "quality_flag"].iloc[0]
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_clean.py -q`
Expected: FAIL with `ImportError: cannot import name 'flag_statistical_outliers'`.

- [ ] **Step 3: Implement the statistical layer + `clean`**

Append to `pipeline/clean.py`:

```python
def flag_statistical_outliers(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Flag isolated, robust-z spikes per (group, pollutant). Values are KEPT.

    A point is flagged when |robust z| > SPIKE_Z within a centered rolling
    window AND neither neighbour is itself extreme (so sustained real events are
    preserved). MAD==0 windows yield no flags.
    """
    df = _ensure_flag(df.copy()).sort_values([group_col, "Date"]).reset_index(drop=True)
    grp = df[group_col]
    for pol in POLLUTANTS:
        if pol not in df.columns:
            continue
        med = df.groupby(grp)[pol].transform(
            lambda x: x.rolling(SPIKE_WINDOW, center=True, min_periods=5).median()
        )
        abs_dev = (df[pol] - med).abs()
        mad = abs_dev.groupby(grp).transform(
            lambda x: x.rolling(SPIKE_WINDOW, center=True, min_periods=5).median()
        )
        z = 0.6745 * (df[pol] - med) / mad.replace(0, np.nan)
        spike = (z.abs() > SPIKE_Z).fillna(False)
        prev_ext = spike.groupby(grp).shift(1, fill_value=False)
        next_ext = spike.groupby(grp).shift(-1, fill_value=False)
        isolated = spike & ~(prev_ext | next_ext)
        if isolated.any():
            _add_flag(df, isolated, "flagged_spike")
    return df


def clean(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Run physical bounds then statistical spike flagging."""
    return flag_statistical_outliers(apply_physical_bounds(df), group_col)
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_clean.py -q`
Expected: PASS (6 tests total).

- [ ] **Step 5: Commit**

```bash
git add pipeline/clean.py tests/test_clean.py
git commit -m "feat(pipeline): statistical spike flagging (isolated, keep value)"
```

---

### Task 4: Phase-1 transform (`build.py`)

**Files:**
- Create: `pipeline/build.py`
- Test: `tests/test_build.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_build.py`:

```python
import numpy as np
import pandas as pd
from pipeline.build import rebuild_frame, classify_aqi


def _frame():
    base = dict(PM10=100.0, NO2=40.0, SO2=40.0, O3=50.0, CO=1.0, NH3=200.0)
    rows = [
        {"City": "A", "Date": pd.Timestamp("2020-01-01"), "PM2.5": 90.0, "AQI": 195.0, **base},
        {"City": "A", "Date": pd.Timestamp("2020-01-02"), "PM2.5": 5000.0, "AQI": 480.0, **base},
        {"City": "A", "Date": pd.Timestamp("2020-01-03"), "PM2.5": 90.0, "NO2": 40.0, "AQI": 160.0},
    ]
    return pd.DataFrame(rows)


def test_rebuild_recomputes_aqi_and_preserves_original():
    out = rebuild_frame(_frame(), "City")
    r0 = out.iloc[0]
    assert r0["AQI"] == 200 and r0["dominant_pollutant"] == "PM2.5"
    assert r0["AQI_Bucket"] == "Moderate"
    assert r0["AQI_cpcb_original"] == 195.0      # original preserved
    assert r0["source"] == "kaggle_cpcb"


def test_rebuild_nulls_impossible_then_lowers_aqi():
    out = rebuild_frame(_frame(), "City")
    r1 = out.iloc[1]
    assert np.isnan(r1["PM2.5"])
    assert "imputed_bound" in r1["quality_flag"]
    assert r1["AQI"] == 100 and r1["dominant_pollutant"] == "PM10"


def test_rebuild_under_three_pollutants_is_unknown():
    out = rebuild_frame(_frame(), "City")
    r2 = out.iloc[2]
    assert pd.isna(r2["AQI"]) and r2["AQI_Bucket"] == "Unknown"


def test_classify_aqi_thresholds():
    assert classify_aqi(None) == "Unknown"
    assert classify_aqi(50) == "Good"
    assert classify_aqi(200) == "Moderate"
    assert classify_aqi(500) == "Severe"
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_build.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline.build'`.

- [ ] **Step 3: Implement `pipeline/build.py`**

```python
"""Phase-1 transform: recompute CPCB AQI for the existing cleaned parquets,
additively. No new data, no network. Writes the parquets back in place and a
data-quality report for the human deploy gate.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from pipeline import aqi
from pipeline.clean import clean
# NOTE: pipeline.report is imported lazily inside rebuild_phase1 to avoid an
# import cycle (report imports classify_aqi from this module).

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
CITY = PROCESSED / "city_day_clean.parquet"
STATION = PROCESSED / "station_day_blr_clean.parquet"


def classify_aqi(value) -> str:
    if value is None or pd.isna(value):
        return "Unknown"
    if value <= 50:
        return "Good"
    if value <= 100:
        return "Satisfactory"
    if value <= 200:
        return "Moderate"
    if value <= 300:
        return "Poor"
    if value <= 400:
        return "Very Poor"
    return "Severe"


def rebuild_frame(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Stash original AQI, clean, recompute AQI/bucket/dominant, tag source."""
    df = df.copy()
    df["AQI_cpcb_original"] = df["AQI"]
    df = clean(df, group_col)

    def _aqi(row):
        return aqi.compute_aqi({p: row.get(p) for p in aqi.BREAKPOINTS})

    results = df.apply(_aqi, axis=1)
    df["AQI"] = [r[0] for r in results]
    df["dominant_pollutant"] = [r[1] for r in results]
    df["AQI_Bucket"] = df["AQI"].apply(classify_aqi)
    df["source"] = "kaggle_cpcb"
    return df


def rebuild_phase1(write: bool = True) -> None:
    from pipeline.report import build_report  # lazy: avoids import cycle
    for path, group_col, name in [(CITY, "City", "city"), (STATION, "StationShort", "station")]:
        before = pd.read_parquet(path)
        after = rebuild_frame(before, group_col)
        report = build_report(before, after, group_col, name)
        out = PROCESSED.parent.parent / "reports" / f"data_quality_phase1_{name}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(report)
        if write:
            after.to_parquet(path, index=False)
            print(f"  wrote {len(after):,} rows -> {path}")
        else:
            print(f"  (report-only) did NOT write {path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true",
                    help="compute + print the report without writing parquets")
    args = ap.parse_args()
    rebuild_phase1(write=not args.report_only)
```

Note: the `pipeline.report` import is lazy (inside `rebuild_phase1`), so `test_build.py` —
which only exercises `rebuild_frame`/`classify_aqi` — imports cleanly even before `report.py`
exists (Task 5).

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_build.py -q`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add pipeline/build.py tests/test_build.py
git commit -m "feat(pipeline): Phase-1 rebuild_frame (recompute AQI, preserve original)"
```

---

### Task 5: Data-quality report (`report.py`)

**Files:**
- Create: `pipeline/report.py`
- Test: `tests/test_report.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_report.py`:

```python
import pandas as pd
from pipeline.build import rebuild_frame
from pipeline.report import build_report


def _frames():
    base = dict(PM10=100.0, NO2=40.0, SO2=40.0, O3=50.0, CO=1.0, NH3=200.0)
    before = pd.DataFrame([
        {"City": "A", "Date": pd.Timestamp("2020-01-01"), "PM2.5": 90.0, "AQI": 195.0, **base},
        {"City": "A", "Date": pd.Timestamp("2020-01-02"), "PM2.5": 5000.0, "AQI": 480.0, **base},
    ])
    after = rebuild_frame(before, "City")
    return before, after


def test_report_contains_required_sections():
    before, after = _frames()
    md = build_report(before, after, "City", "city")
    for heading in ["Volume", "AQI change", "Bucket migration",
                    "Cleaning actions", "Largest-change"]:
        assert heading in md
    assert "max <= 500" in md or "max=" in md


def test_report_flags_aqi_over_500_loudly():
    before, after = _frames()
    after.loc[0, "AQI"] = 727        # inject an impossible value
    md = build_report(before, after, "City", "city")
    assert "FAIL" in md
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_report.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline.report'`.

- [ ] **Step 3: Implement `pipeline/report.py`**

```python
"""Phase-1 data-quality report: explicit metrics + largest-change analysis,
rendered as markdown for the human deploy gate.

Order-safe: AQI deltas come from `after`'s own AQI_cpcb_original (so they don't
depend on `before`/`after` being row-aligned, which they are not — clean()
re-sorts). `before` is only used, via a key-merge, for the per-pollutant
null counts.
"""

from __future__ import annotations

import pandas as pd

from pipeline.build import classify_aqi
from pipeline.clean import POLLUTANTS

_TOP_N = 20


def build_report(before: pd.DataFrame, after: pd.DataFrame, group_col: str, name: str) -> str:
    lines: list[str] = [f"# Data-quality report — {name}", ""]

    # --- Volume & coverage ---
    lines += ["## Volume & coverage",
              f"- rows: {len(before):,} -> {len(after):,}",
              f"- date range: {after['Date'].min().date()} .. {after['Date'].max().date()}",
              f"- groups ({group_col}): {after[group_col].nunique()}", ""]

    old, new = after["AQI_cpcb_original"], after["AQI"]   # both from `after` (aligned)
    both = old.notna() & new.notna()
    delta = (new[both] - old[both]).abs()

    # --- AQI change ---
    new_max = float(new.max())
    gate = "max <= 500 OK" if new_max <= 500 else f"FAIL: AQI max={new_max} > 500"
    lines += ["## AQI change",
              f"- rows with old & new AQI: {int(both.sum()):,}",
              f"- changed: {int((delta > 0).sum()):,} "
              f"({100 * (delta > 0).mean():.1f}% of comparable rows)",
              f"- |delta| mean={delta.mean():.1f} median={delta.median():.1f} "
              f"p90={delta.quantile(0.9):.1f} p99={delta.quantile(0.99):.1f} max={delta.max():.1f}",
              f"- null->value: {int((old.isna() & new.notna()).sum()):,} | "
              f"value->null: {int((old.notna() & new.isna()).sum()):,}",
              f"- recomputed AQI {gate}", ""]

    # --- Bucket migration (old bucket derived from the preserved original AQI) ---
    old_bucket = old.apply(classify_aqi)
    lines += ["## Bucket migration", "", "| old -> new | count |", "| --- | --- |"]
    mig = (pd.crosstab(old_bucket, after["AQI_Bucket"]).stack().reset_index(name="n"))
    mig = mig[(mig["n"] > 0) & (mig.iloc[:, 0] != mig.iloc[:, 1])]
    for _, r in mig.iterrows():
        lines.append(f"| {r.iloc[0]} -> {r.iloc[1]} | {int(r['n'])} |")
    lines.append("")

    # --- Cleaning actions (per-pollutant nulls via key-merge; flags from `after`) ---
    key = [group_col, "Date"]
    cols = [p for p in POLLUTANTS if p in before.columns and p in after.columns]
    merged = before[key + cols].merge(after[key + cols], on=key, suffixes=("_old", "_new"))
    lines.append("## Cleaning actions")
    for pol in cols:
        nulled = (merged[f"{pol}_old"].notna() & merged[f"{pol}_new"].isna()).sum()
        lines.append(f"- {pol} nulled by physical bounds: {int(nulled):,}")
    flag = after["quality_flag"].fillna("ok")
    lines += [f"- rows flagged imputed_bound: {int(flag.str.contains('imputed_bound').sum()):,}",
              f"- rows flagged flagged_spike: {int(flag.str.contains('flagged_spike').sum()):,}", ""]

    # --- Largest-change analysis ---
    lines += ["## Largest-change analysis (top 20 by |delta AQI|)", "",
              "| group | date | old AQI | new AQI | delta | dominant | PM2.5 | PM10 |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    tmp = after.copy()
    tmp["_delta"] = (tmp["AQI"] - tmp["AQI_cpcb_original"]).abs()
    for _, r in tmp.sort_values("_delta", ascending=False).head(_TOP_N).iterrows():
        lines.append(
            f"| {r[group_col]} | {pd.Timestamp(r['Date']).date()} | "
            f"{r['AQI_cpcb_original']} | {r['AQI']} | {r['_delta']:.0f} | "
            f"{r['dominant_pollutant']} | {r.get('PM2.5')} | {r.get('PM10')} |"
        )
    lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_report.py tests/test_build.py -q`
Expected: PASS (test_report 2 + test_build 4).

- [ ] **Step 5: Commit**

```bash
git add pipeline/report.py tests/test_report.py
git commit -m "feat(pipeline): data-quality report with largest-change analysis"
```

---

### Task 6: End-to-end regression fixture + test

**Files:**
- Create: `tests/fixtures/make_fixture.py`
- Create: `tests/fixtures/sample_city_day.parquet` (generated, committed)
- Test: `tests/test_pipeline_regression.py`

- [ ] **Step 1: Write the fixture generator**

Create `tests/fixtures/make_fixture.py`:

```python
"""Generate the committed regression fixture. Run once:
   .venv/Scripts/python.exe tests/fixtures/make_fixture.py
"""
import pandas as pd
from pathlib import Path

base = dict(PM10=100.0, NO2=40.0, SO2=40.0, O3=50.0, CO=1.0, NH3=200.0)
rows = []

# City "Norm": deterministic paths.
d = pd.date_range("2020-01-01", periods=6)
rows.append({"City": "Norm", "Date": d[0], "PM2.5": 90.0, "AQI": 195.0, **base})   # normal -> 200
rows.append({"City": "Norm", "Date": d[1], "PM2.5": 5000.0, "AQI": 480.0, **base}) # impossible -> nulled
rows.append({"City": "Norm", "Date": d[2], "PM2.5": 90.0, "NO2": 40.0, "AQI": 160.0})  # <3 pollutants
rows.append({"City": "Norm", "Date": d[3], "PM2.5": 60.0, "AQI": 487.0, **base})   # inconsistent original
rows.append({"City": "Norm", "Date": d[4], "PM2.5": 90.0, "AQI": 200.0, **base})
rows.append({"City": "Norm", "Date": d[5], "PM2.5": 90.0, "AQI": 200.0, **base})

# City "Spike": varied baseline (MAD>0) with one isolated spike at index 7.
ds = pd.date_range("2020-02-01", periods=16)
pm = [80.0, 100.0] * 8
pm[7] = 500.0
for i, dt in enumerate(ds):
    rows.append({"City": "Spike", "Date": dt, "PM2.5": pm[i], "AQI": 150.0, **base})

df = pd.DataFrame(rows)
out = Path(__file__).resolve().parent / "sample_city_day.parquet"
df.to_parquet(out, index=False)
print(f"wrote {len(df)} rows -> {out}")
```

- [ ] **Step 2: Generate and commit the fixture parquet**

Run: `.venv/Scripts/python.exe tests/fixtures/make_fixture.py`
Expected: `wrote 22 rows -> .../sample_city_day.parquet`

- [ ] **Step 3: Write the regression test**

Create `tests/test_pipeline_regression.py`:

```python
from pathlib import Path

import numpy as np
import pandas as pd
from pipeline.build import rebuild_frame

FIXTURE = Path(__file__).parent / "fixtures" / "sample_city_day.parquet"
EXPECTED_COLS = {"AQI", "AQI_Bucket", "AQI_cpcb_original", "quality_flag",
                 "dominant_pollutant", "source"}


def _out():
    return rebuild_frame(pd.read_parquet(FIXTURE), "City")


def test_schema_and_global_invariants():
    out = _out()
    assert EXPECTED_COLS.issubset(out.columns)
    assert out["AQI"].max() <= 500
    assert (out["source"] == "kaggle_cpcb").all()


def test_normal_row():
    out = _out()
    r = out[(out["City"] == "Norm") & (out["Date"] == "2020-01-01")].iloc[0]
    assert r["AQI"] == 200 and r["dominant_pollutant"] == "PM2.5"
    assert r["AQI_Bucket"] == "Moderate"
    assert r["AQI_cpcb_original"] == 195.0
    assert r["quality_flag"] == "ok"


def test_impossible_value_path():
    out = _out()
    r = out[(out["City"] == "Norm") & (out["Date"] == "2020-01-02")].iloc[0]
    assert np.isnan(r["PM2.5"])
    assert "imputed_bound" in r["quality_flag"]
    assert r["AQI"] == 100 and r["dominant_pollutant"] == "PM10"


def test_under_three_pollutants_is_unknown():
    out = _out()
    r = out[(out["City"] == "Norm") & (out["Date"] == "2020-01-03")].iloc[0]
    assert pd.isna(r["AQI"]) and r["AQI_Bucket"] == "Unknown"


def test_inconsistent_original_is_corrected():
    out = _out()
    r = out[(out["City"] == "Norm") & (out["Date"] == "2020-01-04")].iloc[0]
    assert r["AQI_cpcb_original"] == 487.0
    assert r["AQI"] == 100            # PM2.5=60 & PM10=100 -> 100, not 487


def test_isolated_spike_flagged_value_kept():
    out = _out()
    r = out[(out["City"] == "Spike") & (out["PM2.5"] == 500.0)].iloc[0]
    assert "flagged_spike" in r["quality_flag"]
    assert r["PM2.5"] == 500.0


def test_idempotent_on_stable_columns():
    once = _out()
    twice = rebuild_frame(once, "City")
    cols = ["AQI", "AQI_Bucket", "dominant_pollutant", "quality_flag", "source"]
    pd.testing.assert_frame_equal(
        once.sort_values(["City", "Date"])[cols].reset_index(drop=True),
        twice.sort_values(["City", "Date"])[cols].reset_index(drop=True),
    )
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_pipeline_regression.py -q`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/make_fixture.py tests/fixtures/sample_city_day.parquet tests/test_pipeline_regression.py
git commit -m "test(pipeline): end-to-end regression fixture covering all transform paths"
```

---

### Task 7: Run the real rebuild (report-only), human review, then write

**Files:**
- Modify (data): `data/processed/city_day_clean.parquet`, `data/processed/station_day_blr_clean.parquet`
- Create: `reports/data_quality_phase1_city.md`, `reports/data_quality_phase1_station.md`

- [ ] **Step 1: Full test suite green first**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: all pass (new pipeline tests + existing suite including `test_mcp_tools.py`).

- [ ] **Step 2: Report-only run (no writes)**

Run: `.venv/Scripts/python.exe -m pipeline.build --report-only`
Expected: prints both reports; writes `reports/data_quality_phase1_{city,station}.md`; says it did NOT write the parquets.

- [ ] **Step 3: HUMAN REVIEW GATE**

Read both reports. Confirm: recomputed `AQI max <= 500` for city AND station (the 727 fix); changed-row % and |delta| are explainable (the largest-change rows are corrections of inconsistent originals, not new errors); flagged-spike rows are a small %; no mass null->value or value->null. **Sanity-check CO units:** if CO-dominant rows dominate implausibly, CO may not be mg/m3 — STOP and report. Do not proceed until the report looks sane.

- [ ] **Step 4: Real rebuild (writes parquets)**

Run: `.venv/Scripts/python.exe -m pipeline.build`
Expected: writes both parquets; prints row counts.

- [ ] **Step 5: Verify the written parquets**

Run:
```bash
.venv/Scripts/python.exe -c "import pandas as pd; \
c=pd.read_parquet('data/processed/city_day_clean.parquet'); \
s=pd.read_parquet('data/processed/station_day_blr_clean.parquet'); \
print('city AQI max', c['AQI'].max(), '| station AQI max', s['AQI'].max()); \
print('new cols', [x for x in ['AQI_cpcb_original','quality_flag','dominant_pollutant','source'] if x in c.columns]); \
print('station rows', len(s))"
```
Expected: both AQI maxes `<= 500` (station no longer 727); all four new columns present.

- [ ] **Step 6: Re-run the full suite against the rebuilt data**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: all pass (the MCP tool tests now read the recomputed parquets).

- [ ] **Step 7: Commit**

```bash
git add data/processed/city_day_clean.parquet data/processed/station_day_blr_clean.parquet reports/
git commit -m "data: recompute CPCB AQI + clean existing parquets (Phase 1)"
```

---

### Task 8: Sync to hf-space + redeploy + verify

**Files:**
- Overwrite: `hf-space/data/processed/city_day_clean.parquet`, `hf-space/data/processed/station_day_blr_clean.parquet`

- [ ] **Step 1: Copy the rebuilt parquets to the deploy folder**

Run (Git Bash):
```bash
cp data/processed/city_day_clean.parquet hf-space/data/processed/city_day_clean.parquet
cp data/processed/station_day_blr_clean.parquet hf-space/data/processed/station_day_blr_clean.parquet
```

- [ ] **Step 2: Confirm the deploy copy still loads and AQI is bounded**

Run: `cd hf-space && ../.venv/Scripts/python.exe -c "import air_quality_mcp as s; print('city max', s._df['AQI'].max(), '| station max', s._station_df['AQI'].max())" && cd ..`
Expected: both `<= 500`.

- [ ] **Step 3: Commit (git-lfs stores the parquets)**

```bash
git add hf-space/data/processed/city_day_clean.parquet hf-space/data/processed/station_day_blr_clean.parquet
git commit -m "chore(hf-space): ship Phase-1 recomputed parquets"
```

- [ ] **Step 4: Deploy to the HF Space**

Run:
```bash
.venv/Scripts/python.exe -c "from huggingface_hub import HfApi; \
print(HfApi().upload_folder(folder_path='hf-space', repo_id='Bhuvandesai/india-air-quality', repo_type='space', \
commit_message='Phase 1: recomputed CPCB AQI + cleaned parquets').commit_url)"
```
Expected: prints a commit URL; the Space rebuilds.

- [ ] **Step 5: Verify the live Space**

Run: `.venv/Scripts/python.exe scripts/verify_hf_deploy.py`
Expected: ends with `DEPLOY VERIFIED: 11 tools live.`

---

### Task 9: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Full suite**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: all pass.

- [ ] **Step 2: Confirm Done criteria from the spec**

- `AQI.max() <= 500` for both parquets (Task 7 Step 5). ✓
- `reports/data_quality_phase1_*.md` exist with metrics + top-20 table. ✓
- New columns populated; `AQI_cpcb_original` retains originals. ✓
- HF Space verified (Task 8 Step 5). ✓

- [ ] **Step 3: Confirm branch is clean**

Run: `git status -sb`
Expected: clean working tree on `feat/data-pipeline-phase1`.

---

## Final notes

- This plan is Phase 1 of the v2 data pipeline (see `docs/superpowers/future-plans.md`).
  Phases 2–4 (OpenAQ ingestion, automation, dynamic framing) are separate future specs.
- `git push` + merge are the user's to do unless they ask otherwise.
- The `pipeline/aqi.py` and `pipeline/clean.py` modules are reused by Phase 2 — keep their
  interfaces stable.
