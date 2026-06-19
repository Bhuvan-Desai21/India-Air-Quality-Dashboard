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
