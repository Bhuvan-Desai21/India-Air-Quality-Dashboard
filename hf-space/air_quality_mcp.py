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
