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
