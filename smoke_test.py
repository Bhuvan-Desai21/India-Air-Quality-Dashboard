"""Fast, dependency-light check of the MCP tool functions.

This calls the tool functions directly (FastMCP's @tool decorator returns the
original function), so we can verify the data logic without the MCP protocol or
the Inspector. Run with the venv python:

    .venv\\Scripts\\python.exe smoke_test.py
"""

import json

import air_quality_mcp as srv


def show(title: str, result) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    show("list_cities()", srv.list_cities())
    show("rank_cities(metric='aqi', n=3, order='desc')  # worst AQI 'now'",
         srv.rank_cities(metric="aqi", n=3, order="desc"))
    show("get_aqi('delhi')  # case-insensitive, latest valid", srv.get_aqi("delhi"))
    show("get_aqi('Delhi', '2019-11-03')", srv.get_aqi("Delhi", "2019-11-03"))
    show("compare_cities(['Delhi','Mumbai','Atlantis'], 'pm25')",
         srv.compare_cities(["Delhi", "Mumbai", "Atlantis"], "pm25"))
    show("trend('Delhi', 'pm25', 5)", srv.trend("Delhi", "pm25", 5))
    show("seasonal_breakdown('Delhi')", srv.seasonal_breakdown("Delhi"))
    show("yearly_summary('Delhi', 'pm25')", srv.yearly_summary("Delhi", "pm25"))
    show("lockdown_impact('Delhi')", srv.lockdown_impact("Delhi"))
    show("health_advisory('Delhi')", srv.health_advisory("Delhi"))
    show("health_advisory('Gotham')  # unknown city", srv.health_advisory("Gotham"))
    show("compare_to_standard('Delhi', 'pm25')", srv.compare_to_standard("Delhi", "pm25"))
    show("compare_to_standard('Delhi', 'aqi')  # aqi rejected",
         srv.compare_to_standard("Delhi", "aqi"))
    show("station_breakdown(order='desc')  # Bengaluru worst-first",
         srv.station_breakdown(order="desc"))

    # Error handling
    show("get_aqi('Gotham')  # unknown city", srv.get_aqi("Gotham"))
    show("rank_cities(metric='radon')  # unknown metric", srv.rank_cities(metric="radon"))
    show("get_aqi('Delhi', 'not-a-date')  # bad date", srv.get_aqi("Delhi", "not-a-date"))

    print("\nOK: all tool functions returned without raising.")
