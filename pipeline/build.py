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
    # AQI dtype is int64 if every row is valid, else float64 (None -> NaN). Real data
    # always has "Unknown" rows, so production output is float64 — matching the original
    # AQI column and the numeric MCP consumers. Don't assert int on real data.
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
