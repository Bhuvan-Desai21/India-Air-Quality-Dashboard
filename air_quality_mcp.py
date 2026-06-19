"""India Air Quality MCP server.

Exposes the air-quality dashboard's analysis as Model Context Protocol tools.

Transport is chosen at runtime so the SAME file serves every client:
    MCP_TRANSPORT=stdio  (default)  -> mcp.run()                          # Claude Desktop (local), `mcp dev`
    MCP_TRANSPORT=http              -> mcp.run(transport="streamable-http")# Hugging Face Spaces, LangGraph client
For http, the server binds HOST:PORT (defaults 0.0.0.0:7860, the HF Spaces convention).

Data: data/processed/city_day_clean.parquet -- 11 Indian cities, daily, 2015-01-01..2020-07-01.
This is HISTORICAL data, not real-time; every tool reports the as-of date it used.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from mcp.server.fastmcp import FastMCP

# --- Data layer (Streamlit-free) ----------------------------------------------
# The dashboard's utils/data_loader.py is @st.cache_data-decorated; importing it
# would pull Streamlit into the server. We read the same parquet directly instead.
# Resolve the path from this file so the working directory the client launches us
# with does not matter (and so the file containerizes cleanly for HF Spaces).

DATA_PATH = Path(__file__).resolve().parent / "data" / "processed" / "city_day_clean.parquet"

# Friendly, case-insensitive metric aliases -> actual dataframe columns.
METRIC_MAP: dict[str, str] = {
    "aqi": "AQI",
    "pm25": "PM2.5",
    "pm2.5": "PM2.5",
    "pm10": "PM10",
    "no2": "NO2",
    "so2": "SO2",
    "o3": "O3",
    "co": "CO",
    "nh3": "NH3",
}
VALID_METRICS: list[str] = sorted(set(METRIC_MAP))  # advertised to the model

_df = pd.read_parquet(DATA_PATH)
_df["Date"] = pd.to_datetime(_df["Date"])

# lowercase city -> canonical name, for case-insensitive lookups.
_CITY_CANON: dict[str, str] = {c.lower(): c for c in _df["City"].unique()}


def _resolve_city(city: str) -> str | None:
    """Map any-case city name to its canonical spelling, or None if unknown."""
    return _CITY_CANON.get(city.strip().lower())


def _resolve_metric(metric: str) -> str | None:
    """Map a friendly metric alias to its dataframe column, or None if unknown."""
    return METRIC_MAP.get(metric.strip().lower())


def _city_frame(canonical_city: str) -> pd.DataFrame:
    return _df[_df["City"] == canonical_city]


def _latest_valid(frame: pd.DataFrame, column: str) -> tuple[float | None, str | None]:
    """Most recent row where `column` is non-null -> (value, 'YYYY-MM-DD') or (None, None)."""
    valid = frame.dropna(subset=[column]).sort_values("Date")
    if valid.empty:
        return None, None
    row = valid.iloc[-1]
    return round(float(row[column]), 2), row["Date"].strftime("%Y-%m-%d")


def _coverage() -> dict[str, str]:
    return {
        "start": _df["Date"].min().strftime("%Y-%m-%d"),
        "end": _df["Date"].max().strftime("%Y-%m-%d"),
    }


# --- Station (Bengaluru hyperlocal) data layer --------------------------------
# A second cleaned parquet: 10 Bengaluru monitoring stations, same pollutant columns.
# Loaded once at import, path resolved from __file__ like the city frame.
_STATION_PATH = (
    Path(__file__).resolve().parent / "data" / "processed" / "station_day_blr_clean.parquet"
)
_station_df = pd.read_parquet(_STATION_PATH)
_station_df["Date"] = pd.to_datetime(_station_df["Date"])


def _station_frame(station: str) -> pd.DataFrame:
    return _station_df[_station_df["StationShort"] == station]


# --- Constants for the analytical tools ---------------------------------------
SEASON_ORDER: list[str] = ["Winter", "Spring", "Monsoon", "Post-Monsoon"]

# WHO 2021 annual guideline values (µg/m³); None where WHO sets no annual value here.
WHO_LIMITS: dict[str, float | None] = {
    "PM2.5": 5.0, "PM10": 15.0, "NO2": 10.0, "SO2": None, "O3": 60.0, "CO": None, "NH3": None,
}
# CPCB annual standards (India), µg/m³ (CO would be mg/m³ but has no annual std here).
CPCB_LIMITS: dict[str, float | None] = {
    "PM2.5": 40.0, "PM10": 60.0, "NO2": 40.0, "SO2": 50.0, "O3": None, "CO": None, "NH3": None,
}
UNITS: dict[str, str] = {
    "PM2.5": "µg/m³", "PM10": "µg/m³", "NO2": "µg/m³", "SO2": "µg/m³",
    "O3": "µg/m³", "CO": "mg/m³", "NH3": "µg/m³",
}

# CPCB-band health guidance: category -> (advisory, who is most at risk).
ADVISORY: dict[str, tuple[str, str]] = {
    "Good": ("Air quality is good; safe for everyone.", "None."),
    "Satisfactory": (
        "Acceptable air; very sensitive individuals may feel minor discomfort.",
        "Highly sensitive people.",
    ),
    "Moderate": (
        "May cause breathing discomfort to people with lung or heart disease, "
        "children, and older adults.",
        "Asthma/heart patients, children, the elderly.",
    ),
    "Poor": (
        "Breathing discomfort on prolonged exposure; sensitive groups should limit "
        "outdoor exertion.",
        "Most people on prolonged exposure.",
    ),
    "Very Poor": (
        "Respiratory illness on prolonged exposure; avoid outdoor activity.",
        "Everyone, seriously for sensitive groups.",
    ),
    "Severe": (
        "Serious health impact even on light activity; stay indoors.",
        "Everyone.",
    ),
    "Unknown": ("No health category available for this reading.", "Unknown."),
}


def _aqi_category(aqi: float) -> str:
    """Map a numeric AQI to its CPCB band (matches the dashboard buckets)."""
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Satisfactory"
    if aqi <= 200:
        return "Moderate"
    if aqi <= 300:
        return "Poor"
    if aqi <= 400:
        return "Very Poor"
    return "Severe"


# --- MCP server ---------------------------------------------------------------
# host/port are read from the environment now (harmless for stdio) so the http
# transport needs no code change -- only MCP_TRANSPORT=http at launch.

mcp = FastMCP(
    "india-air-quality",
    host=os.environ.get("HOST", "0.0.0.0"),
    port=int(os.environ.get("PORT", "7860")),
)


@mcp.tool()
def list_cities() -> dict:
    """List the Indian cities available in the air-quality dataset.

    Returns the city names plus dataset coverage. The data is HISTORICAL, not
    real-time: any question about "now"/"latest" is answered as of the most
    recent date in `date_range`. Use the names returned here for the other tools.
    """
    cov = _coverage()
    return {
        "cities": sorted(_df["City"].unique().tolist()),
        "count": int(_df["City"].nunique()),
        "date_range": cov,
        "metrics": VALID_METRICS,
        "note": f"Historical data {cov['start']} to {cov['end']}; not real-time.",
    }


@mcp.tool()
def get_aqi(city: str, date: str | None = None) -> dict:
    """Get the AQI and pollutant readings for a city on a single day.

    Args:
        city: City name, e.g. "Delhi" (case-insensitive).
        date: Optional day as "YYYY-MM-DD". If omitted, the latest day for which
            this city has a valid (non-null) AQI reading is used.

    Returns a dict with the city, the `as_of` date actually used, the `aqi` value
    and its `aqi_category` (CPCB bucket), and a `pollutants` map (pm25, pm10, no2,
    so2, o3, co, nh3) in their reported units; missing pollutants are null. On an
    unknown city or a date with no reading, returns {"error": ...}.
    """
    canon = _resolve_city(city)
    if canon is None:
        return {"error": f"Unknown city '{city}'. Call list_cities for valid names."}
    frame = _city_frame(canon)

    if date is not None:
        try:
            target = pd.to_datetime(date)
        except (ValueError, TypeError):
            return {"error": f"Bad date '{date}'. Use YYYY-MM-DD."}
        rows = frame[frame["Date"] == target]
        if rows.empty:
            cov = _coverage()
            # Cleaned data has gaps; point the caller at the closest available day.
            nearest = frame.loc[(frame["Date"] - target).abs().idxmin(), "Date"]
            return {
                "error": f"No reading for {canon} on {date}. "
                f"Data covers {cov['start']} to {cov['end']} with gaps.",
                "nearest_available": nearest.strftime("%Y-%m-%d"),
            }
        row = rows.iloc[0]
        as_of = date
    else:
        valid = frame.dropna(subset=["AQI"]).sort_values("Date")
        if valid.empty:
            return {"error": f"No valid AQI readings for {canon}."}
        row = valid.iloc[-1]
        as_of = row["Date"].strftime("%Y-%m-%d")

    def val(col: str) -> float | None:
        v = row[col]
        return None if pd.isna(v) else round(float(v), 2)

    bucket = row["AQI_Bucket"]
    return {
        "city": canon,
        "as_of": as_of,
        "aqi": val("AQI"),
        "aqi_category": None if pd.isna(bucket) else str(bucket),
        "pollutants": {
            "pm25": val("PM2.5"),
            "pm10": val("PM10"),
            "no2": val("NO2"),
            "so2": val("SO2"),
            "o3": val("O3"),
            "co": val("CO"),
            "nh3": val("NH3"),
        },
    }


@mcp.tool()
def compare_cities(cities: list[str], metric: str = "aqi") -> dict:
    """Compare one metric across several cities, using each city's latest valid reading.

    Args:
        cities: City names to compare (case-insensitive).
        metric: One of aqi, pm25, pm10, no2, so2, o3, co, nh3. Defaults to aqi.

    Returns {"metric", "values": {city: {"value", "as_of"}}}. Each city is dated
    independently (the latest day it has a non-null value). Unknown cities appear
    with a null value and a "note". An unknown metric returns {"error": ...}.
    """
    col = _resolve_metric(metric)
    if col is None:
        return {"error": f"Unknown metric '{metric}'. Valid metrics: {VALID_METRICS}."}
    values: dict[str, dict] = {}
    for city in cities:
        canon = _resolve_city(city)
        if canon is None:
            values[city] = {"value": None, "as_of": None, "note": "unknown city"}
            continue
        v, d = _latest_valid(_city_frame(canon), col)
        values[canon] = {"value": v, "as_of": d}
    return {"metric": metric.lower(), "values": values}


@mcp.tool()
def trend(city: str, metric: str = "aqi", days: int = 30) -> dict:
    """Return a city's recent daily values for a metric, oldest first, newest last.

    Uses the most recent `days` days that have a valid (non-null) value for the
    metric -- good for "how has Delhi's PM2.5 changed lately?".

    Args:
        city: City name (case-insensitive).
        metric: One of aqi, pm25, pm10, no2, so2, o3, co, nh3. Defaults to aqi.
        days: Number of recent valid daily points to return (clamped to 1-365).
            Defaults to 30.

    Returns {"city", "metric", "series": [{"date", "value"}...], "summary": {...}}
    where summary has points/start/end/min/max/mean/change/direction. An unknown
    city or metric returns {"error": ...}.
    """
    canon = _resolve_city(city)
    if canon is None:
        return {"error": f"Unknown city '{city}'. Call list_cities for valid names."}
    col = _resolve_metric(metric)
    if col is None:
        return {"error": f"Unknown metric '{metric}'. Valid metrics: {VALID_METRICS}."}
    days = max(1, min(int(days), 365))
    valid = _city_frame(canon).dropna(subset=[col]).sort_values("Date").tail(days)
    if valid.empty:
        return {"error": f"No valid {metric} readings for {canon}."}

    series = [
        {"date": d.strftime("%Y-%m-%d"), "value": round(float(v), 2)}
        for d, v in zip(valid["Date"], valid[col])
    ]
    vals = [p["value"] for p in series]
    summary = {
        "points": len(series),
        "start": series[0]["date"],
        "end": series[-1]["date"],
        "min": min(vals),
        "max": max(vals),
        "mean": round(sum(vals) / len(vals), 2),
        "change": round(vals[-1] - vals[0], 2),
        "direction": (
            "rising" if vals[-1] > vals[0] else "falling" if vals[-1] < vals[0] else "flat"
        ),
    }
    return {"city": canon, "metric": metric.lower(), "series": series, "summary": summary}


@mcp.tool()
def rank_cities(metric: str = "aqi", n: int = 5, order: str = "desc") -> dict:
    """Rank cities by a metric, using each city's latest valid reading.

    Answers "which cities have the worst/best air quality right now?".

    Args:
        metric: One of aqi, pm25, pm10, no2, so2, o3, co, nh3. Defaults to aqi.
        n: How many cities to return (clamped to 1-50). Defaults to 5.
        order: "desc" for most polluted first (worst), "asc" for cleanest first.

    Returns {"metric", "order", "ranking": [{"city", "value", "as_of"}...]}.
    Cities with no valid reading for the metric are omitted. An unknown metric
    or order returns {"error": ...}.
    """
    col = _resolve_metric(metric)
    if col is None:
        return {"error": f"Unknown metric '{metric}'. Valid metrics: {VALID_METRICS}."}
    order = order.strip().lower()
    if order not in ("desc", "asc"):
        return {"error": f"Unknown order '{order}'. Use 'desc' or 'asc'."}
    n = max(1, min(int(n), 50))

    entries = []
    for canon in _df["City"].unique():
        v, d = _latest_valid(_city_frame(canon), col)
        if v is not None:
            entries.append({"city": canon, "value": v, "as_of": d})
    entries.sort(key=lambda e: e["value"], reverse=(order == "desc"))
    return {"metric": metric.lower(), "order": order, "ranking": entries[:n]}


@mcp.tool()
def seasonal_breakdown(city: str, metric: str = "aqi") -> dict:
    """Average a metric by season for a city: Winter, Spring, Monsoon, Post-Monsoon.

    Good for "is Delhi's pollution worse in winter?". Indian seasons, not calendar
    quarters: Winter (Dec-Feb), Spring (Mar-May), Monsoon (Jun-Sep), Post-Monsoon
    (Oct-Nov), aggregated across all years 2015-2020.

    Args:
        city: City name (case-insensitive).
        metric: One of aqi, pm25, pm10, no2, so2, o3, co, nh3. Defaults to aqi.

    Returns {"city", "metric", "seasons": {season: {avg, min, max, n}}, "peak_season",
    "cleanest_season"}. Seasons with no data are omitted. Unknown city/metric → error.
    """
    canon = _resolve_city(city)
    if canon is None:
        return {"error": f"Unknown city '{city}'. Call list_cities for valid names."}
    col = _resolve_metric(metric)
    if col is None:
        return {"error": f"Unknown metric '{metric}'. Valid metrics: {VALID_METRICS}."}
    frame = _city_frame(canon).dropna(subset=[col])
    if frame.empty:
        return {"error": f"No valid {metric} readings for {canon}."}

    seasons: dict[str, dict] = {}
    for season in SEASON_ORDER:
        s = frame[frame["Season"] == season][col]
        if s.empty:
            continue
        seasons[season] = {
            "avg": round(float(s.mean()), 2),
            "min": round(float(s.min()), 2),
            "max": round(float(s.max()), 2),
            "n": int(s.count()),
        }
    if not seasons:
        return {"error": f"No seasonal data for {canon}."}
    peak = max(seasons, key=lambda k: seasons[k]["avg"])
    cleanest = min(seasons, key=lambda k: seasons[k]["avg"])
    return {
        "city": canon,
        "metric": metric.lower(),
        "seasons": seasons,
        "peak_season": peak,
        "cleanest_season": cleanest,
    }


@mcp.tool()
def yearly_summary(city: str, metric: str = "aqi") -> dict:
    """Year-by-year averages (2015-2020) for a metric in a city.

    Answers "is Delhi's air getting better or worse over the years?".

    Args:
        city: City name (case-insensitive).
        metric: One of aqi, pm25, pm10, no2, so2, o3, co, nh3. Defaults to aqi.

    Returns {"city", "metric", "years": [{year, avg, min, max, n}...], "direction"}
    where direction compares the first vs last year with data. Note 2020 is a partial
    year (data ends 2020-07-01). Unknown city/metric → error.
    """
    canon = _resolve_city(city)
    if canon is None:
        return {"error": f"Unknown city '{city}'. Call list_cities for valid names."}
    col = _resolve_metric(metric)
    if col is None:
        return {"error": f"Unknown metric '{metric}'. Valid metrics: {VALID_METRICS}."}
    frame = _city_frame(canon).dropna(subset=[col])
    if frame.empty:
        return {"error": f"No valid {metric} readings for {canon}."}

    years = []
    for year, g in frame.groupby("Year"):
        years.append({
            "year": int(year),
            "avg": round(float(g[col].mean()), 2),
            "min": round(float(g[col].min()), 2),
            "max": round(float(g[col].max()), 2),
            "n": int(g[col].count()),
        })
    years.sort(key=lambda y: y["year"])
    direction = (
        "rising" if years[-1]["avg"] > years[0]["avg"]
        else "falling" if years[-1]["avg"] < years[0]["avg"] else "flat"
    )
    return {"city": canon, "metric": metric.lower(), "years": years, "direction": direction}


@mcp.tool()
def lockdown_impact(city: str, metric: str = "aqi") -> dict:
    """Compare a city's metric in Mar-Jun 2019 vs Mar-Jun 2020 (the COVID lockdown).

    India's nationwide lockdown began 25 Mar 2020. This compares the same months
    (March-June) one year apart to isolate the lockdown's effect on air quality.

    Args:
        city: City name (case-insensitive).
        metric: One of aqi, pm25, pm10, no2, so2, o3, co, nh3. Defaults to aqi.

    Returns {"city", "metric", "window": "Mar-Jun", "before": {year, avg, n},
    "after": {year, avg, n}, "change_pct", "direction"}. change_pct/direction are null
    (with a note) if either year lacks data in the window. Unknown city/metric → error.
    """
    canon = _resolve_city(city)
    if canon is None:
        return {"error": f"Unknown city '{city}'. Call list_cities for valid names."}
    col = _resolve_metric(metric)
    if col is None:
        return {"error": f"Unknown metric '{metric}'. Valid metrics: {VALID_METRICS}."}
    window = _city_frame(canon)
    window = window[window["Month"].isin([3, 4, 5, 6])].dropna(subset=[col])

    def side(year: int) -> dict | None:
        s = window[window["Year"] == year][col]
        if s.empty:
            return None
        return {"year": year, "avg": round(float(s.mean()), 2), "n": int(s.count())}

    before, after = side(2019), side(2020)
    result: dict = {
        "city": canon, "metric": metric.lower(), "window": "Mar-Jun",
        "before": before, "after": after,
    }
    if before and after and before["avg"] != 0:
        change = (after["avg"] - before["avg"]) / before["avg"] * 100
        result["change_pct"] = round(change, 1)
        result["direction"] = "fell" if change < 0 else "rose" if change > 0 else "flat"
    else:
        result["change_pct"] = None
        result["direction"] = None
        result["note"] = "Need both 2019 and 2020 data in Mar-Jun to compute change."
    return result


@mcp.tool()
def health_advisory(city: str, date: str | None = None) -> dict:
    """Plain-language health guidance for a city's air quality on a day.

    Resolves the AQI exactly like get_aqi (latest valid reading, or a given
    YYYY-MM-DD date), then maps it to its CPCB category and the recommended
    precautions plus who is most at risk.

    Args:
        city: City name (case-insensitive).
        date: Optional "YYYY-MM-DD"; omitted → latest valid AQI day for the city.

    Returns {"city", "as_of", "aqi", "category", "advisory", "sensitive_groups"}.
    Unknown city / no reading → {"error": ...} (same shape as get_aqi).
    """
    reading = get_aqi(city, date)
    if "error" in reading:
        return reading
    aqi = reading["aqi"]
    if aqi is None:
        return {"error": f"No AQI value to advise on for {reading['city']}."}
    category = reading.get("aqi_category") or _aqi_category(aqi)
    advisory, groups = ADVISORY.get(category, ADVISORY["Unknown"])
    return {
        "city": reading["city"],
        "as_of": reading["as_of"],
        "aqi": aqi,
        "category": category,
        "advisory": advisory,
        "sensitive_groups": groups,
    }


@mcp.tool()
def compare_to_standard(city: str, pollutant: str) -> dict:
    """Compare a city's latest pollutant level to WHO and CPCB safe limits.

    Answers "how far over the safe limit is Delhi's PM2.5?". Uses the city's most
    recent non-null reading for the pollutant. AQI is not a pollutant and is rejected.
    Note: this compares a single day's reading against the WHO/CPCB *annual-mean*
    guidelines, so a one-day multiple over the limit is not the same as exceeding the
    annual standard -- treat it as "today's level vs the annual safe average".

    Args:
        city: City name (case-insensitive).
        pollutant: One of pm25, pm10, no2, so2, o3, co, nh3 (NOT aqi).

    Returns {"city", "pollutant", "value", "as_of", "unit", "who_limit",
    "who_multiple", "cpcb_limit", "cpcb_multiple", "verdict"}. A limit that does not
    exist for the pollutant comes back null with a null multiple. Unknown city or a
    non-pollutant input → {"error": ...}.
    """
    canon = _resolve_city(city)
    if canon is None:
        return {"error": f"Unknown city '{city}'. Call list_cities for valid names."}
    col = _resolve_metric(pollutant)
    if col is None or col == "AQI":
        return {
            "error": f"'{pollutant}' is not a pollutant. Choose one of "
            "pm25, pm10, no2, so2, o3, co, nh3."
        }
    value, as_of = _latest_valid(_city_frame(canon), col)
    if value is None:
        return {"error": f"No valid {pollutant} readings for {canon}."}

    who, cpcb = WHO_LIMITS.get(col), CPCB_LIMITS.get(col)
    who_mult = round(value / who, 2) if who else None
    cpcb_mult = round(value / cpcb, 2) if cpcb else None
    if who_mult is not None:
        verdict = (
            f"{who_mult}x the WHO annual limit" if who_mult > 1 else "within the WHO annual limit"
        )
    elif cpcb_mult is not None:
        verdict = (
            f"{cpcb_mult}x the CPCB annual limit" if cpcb_mult > 1 else "within the CPCB annual limit"
        )
    else:
        verdict = "no annual limit defined for this pollutant"
    return {
        "city": canon,
        "pollutant": col,
        "value": value,
        "as_of": as_of,
        "unit": UNITS.get(col),
        "who_limit": who,
        "who_multiple": who_mult,
        "cpcb_limit": cpcb,
        "cpcb_multiple": cpcb_mult,
        "verdict": verdict,
    }


@mcp.tool()
def station_breakdown(metric: str = "aqi", order: str = "desc", n: int = 10) -> dict:
    """Rank Bengaluru's neighbourhood monitoring stations by a metric (hyperlocal).

    Answers "which part of Bengaluru has the worst air?". Uses each station's latest
    valid reading. Stations include Silk Board, Peenya, BTM Layout, Hebbal, etc.

    Args:
        metric: One of aqi, pm25, pm10, no2, so2, o3, co, nh3. Defaults to aqi.
        order: "desc" for most polluted first (worst), "asc" for cleanest first.
        n: How many stations to return (clamped 1-20). Defaults to 10 (all of them).

    Returns {"scope": "Bengaluru stations", "metric", "order",
    "ranking": [{station, value, as_of}...]}. Stations with no valid reading are
    omitted. Unknown metric or order → {"error": ...}.
    """
    col = _resolve_metric(metric)
    if col is None:
        return {"error": f"Unknown metric '{metric}'. Valid metrics: {VALID_METRICS}."}
    order = order.strip().lower()
    if order not in ("desc", "asc"):
        return {"error": f"Unknown order '{order}'. Use 'desc' or 'asc'."}
    n = max(1, min(int(n), 20))

    entries = []
    for station in _station_df["StationShort"].unique():
        v, d = _latest_valid(_station_frame(station), col)
        if v is not None:
            entries.append({"station": station, "value": v, "as_of": d})
    entries.sort(key=lambda e: e["value"], reverse=(order == "desc"))
    return {
        "scope": "Bengaluru stations",
        "metric": metric.lower(),
        "order": order,
        "ranking": entries[:n],
    }


def _run_http() -> None:
    """Serve over streamable-HTTP for remote hosting (e.g. Hugging Face Spaces).

    Environment:
        HOST            bind address (default 0.0.0.0)
        PORT            bind port (default 7860, the HF Spaces convention)
        MCP_AUTH_TOKEN  if set, POST /mcp requires `Authorization: Bearer <token>`.
                        Provide it as a Space secret -- never commit it.

    Auth is a pure-ASGI middleware (NOT Starlette's BaseHTTPMiddleware, which buffers
    and would break the /mcp SSE stream): it only checks the header, then hands the
    untouched stream to the app. "/" stays open as a health page.
    """
    import uvicorn
    from starlette.responses import JSONResponse, PlainTextResponse

    app = mcp.streamable_http_app()

    async def health(_request):
        return PlainTextResponse("india-air-quality MCP server is running. POST /mcp")

    app.router.add_route("/", health, methods=["GET"])

    token = os.environ.get("MCP_AUTH_TOKEN")
    if token:
        inner = app
        open_paths = {"/", "/health"}

        async def auth_app(scope, receive, send):
            if scope["type"] == "http" and scope.get("path") not in open_paths:
                headers = dict(scope.get("headers") or [])
                if headers.get(b"authorization", b"").decode() != f"Bearer {token}":
                    await JSONResponse({"error": "unauthorized"}, status_code=401)(
                        scope, receive, send
                    )
                    return
            await inner(scope, receive, send)

        app = auth_app
    else:
        print("WARNING: MCP_AUTH_TOKEN not set -- /mcp is open to anyone.", flush=True)

    uvicorn.run(
        app,
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "7860")),
    )


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower()
    if transport in ("http", "streamable-http", "streamable_http"):
        _run_http()
    else:
        mcp.run()  # stdio -- local default (MCP Inspector etc.)
