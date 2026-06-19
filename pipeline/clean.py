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
