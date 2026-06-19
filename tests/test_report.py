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
