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
