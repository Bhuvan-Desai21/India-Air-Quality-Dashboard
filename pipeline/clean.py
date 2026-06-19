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
        lambda v: label if v == "ok"
        else v if label in v.split(",")
        else f"{v},{label}"
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
