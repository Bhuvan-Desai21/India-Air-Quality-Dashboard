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
