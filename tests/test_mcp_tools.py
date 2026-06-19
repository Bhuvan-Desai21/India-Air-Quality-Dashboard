# tests/test_mcp_tools.py
"""Contract tests for the air-quality MCP tools.

These call the tool functions directly (FastMCP's @tool decorator returns the
original function) and assert structural invariants rather than exact figures, so
they lock the model-facing contract without breaking if the data is reprocessed.
"""

import air_quality_mcp as srv

SEASON_ORDER = ["Winter", "Spring", "Monsoon", "Post-Monsoon"]


# --- list_cities / get_aqi (existing tools, smoke-level guards) ----------------

def test_list_cities_reports_coverage_and_metrics():
    out = srv.list_cities()
    assert out["count"] == len(out["cities"]) == 11
    assert out["date_range"]["start"] == "2015-01-01"
    assert "aqi" in out["metrics"]


def test_get_aqi_unknown_city_errors():
    assert "error" in srv.get_aqi("Gotham")


def test_get_aqi_latest_has_as_of_and_pollutants():
    out = srv.get_aqi("Delhi")
    assert out["city"] == "Delhi"
    assert out["as_of"]  # a date string
    assert set(out["pollutants"]) == {"pm25", "pm10", "no2", "so2", "o3", "co", "nh3"}


# --- seasonal_breakdown -------------------------------------------------------

def test_seasonal_breakdown_orders_seasons_and_picks_extremes():
    out = srv.seasonal_breakdown("Delhi")
    assert out["city"] == "Delhi"
    seasons = list(out["seasons"])
    # Present seasons must appear in canonical order (some may be absent).
    assert seasons == [s for s in SEASON_ORDER if s in out["seasons"]]
    avgs = {k: v["avg"] for k, v in out["seasons"].items()}
    assert out["peak_season"] == max(avgs, key=avgs.get)
    assert out["cleanest_season"] == min(avgs, key=avgs.get)


def test_seasonal_breakdown_rejects_unknown_metric():
    assert "error" in srv.seasonal_breakdown("Delhi", "radon")


# --- yearly_summary -----------------------------------------------------------

def test_yearly_summary_sorted_years_with_direction():
    out = srv.yearly_summary("Delhi", "pm25")
    years = [y["year"] for y in out["years"]]
    assert years == sorted(years)
    assert set(years) <= set(range(2015, 2021))
    assert out["direction"] in ("rising", "falling", "flat")


# --- lockdown_impact ----------------------------------------------------------

def test_lockdown_impact_compares_2019_and_2020():
    out = srv.lockdown_impact("Delhi")
    assert out["window"] == "Mar-Jun"
    assert out["before"]["year"] == 2019
    assert out["after"]["year"] == 2020
    assert out["direction"] in ("fell", "rose", "flat")
    assert isinstance(out["change_pct"], float)


# --- health_advisory ----------------------------------------------------------

def test_health_advisory_returns_category_and_text():
    out = srv.health_advisory("Delhi")
    assert out["category"] in srv.ADVISORY
    assert out["advisory"] and out["sensitive_groups"]


def test_health_advisory_unknown_city_errors():
    assert "error" in srv.health_advisory("Gotham")


# --- compare_to_standard ------------------------------------------------------

def test_compare_to_standard_pm25_over_who_limit():
    out = srv.compare_to_standard("Delhi", "pm25")
    assert out["pollutant"] == "PM2.5"
    assert out["who_limit"] == 5.0
    assert out["who_multiple"] > 1  # Delhi is well over the WHO annual limit
    assert "WHO" in out["verdict"]


def test_compare_to_standard_rejects_aqi():
    assert "error" in srv.compare_to_standard("Delhi", "aqi")


def test_compare_to_standard_unknown_city_errors():
    assert "error" in srv.compare_to_standard("Gotham", "pm25")


# --- station_breakdown --------------------------------------------------------

def test_station_breakdown_desc_is_worst_first():
    out = srv.station_breakdown(order="desc")
    assert out["scope"] == "Bengaluru stations"
    values = [e["value"] for e in out["ranking"]]
    assert values == sorted(values, reverse=True)
    assert all("as_of" in e for e in out["ranking"])


def test_station_breakdown_clamps_n_and_validates_order():
    assert len(srv.station_breakdown(n=999)["ranking"]) <= 10  # 10 stations exist
    assert "error" in srv.station_breakdown(order="sideways")
