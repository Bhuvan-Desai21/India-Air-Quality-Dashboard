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
