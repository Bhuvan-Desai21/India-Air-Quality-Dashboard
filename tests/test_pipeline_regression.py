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
