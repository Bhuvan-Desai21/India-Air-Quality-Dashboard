# India Air Quality MCP Server — Design (Step 1)

**Date:** 2026-06-18
**Status:** Approved
**Scope:** Build, test, and connect a Model Context Protocol (MCP) server to Claude
Desktop. NOT in scope yet: the LangGraph chatbot, RAG, guardrails, eval harness, or
the actual Hugging Face deployment. Those are later steps — but the server is built
*deploy-ready* so they require no rewrite.

## Goal

Expose the existing India air-quality dashboard's analysis as MCP tools, so an LLM
client can answer data questions like *"which city has the worst AQI right now?"* by
calling tools instead of guessing.

Two future consumers, both kept in mind:
1. **Claude Desktop** — local now (stdio), remote later (Custom Connector → HF Spaces).
2. **A LangGraph chatbot** (step 3) — will connect to the same server over HTTP.

## Dataset (verified against the real repo)

- **Source:** `data/processed/city_day_clean.parquet` (the dashboard's cleaned data),
  resolved by an absolute path from `__file__` so the cwd the client launches us with
  does not matter (a common MCP failure mode), and so the file containerizes cleanly.
- **Shape:** 17,954 rows, 11 cities, daily, **2015-01-01 → 2020-07-01**.
- **This is HISTORICAL data, not real-time.** Tools always report an `as_of` date and
  `list_cities` states the coverage, so the model frames "now/latest" correctly.
- **Columns** (note capitalization): `City`, `Date`, `PM2.5`, `PM10`, `NO`, `NO2`,
  `NOx`, `NH3`, `CO`, `SO2`, `O3`, `Benzene`, `Toluene`, `Xylene`, `AQI`, `AQI_Bucket`,
  `Year`, `Month`, `MonthName`, `Season`.
- **Many NaNs** (2,305 of 17,954 AQI values are null). The most recent *calendar* row
  for a city is often null, so "latest" means **latest non-null** value for the
  requested metric.
- No duplicate `City`+`Date` rows. AQI buckets: Good, Satisfactory, Moderate, Poor,
  Very Poor, Severe, Unknown.

## Architecture

Single file `air_quality_mcp.py` at the repo root:

- **Streamlit-free data layer** (in-file). Loads the parquet once at import. Does NOT
  import `utils/data_loader.py` (which is `@st.cache_data`-decorated and would drag
  Streamlit into the server). Dashboard code is left untouched.
- **`FastMCP("india-air-quality")`** with five tools.
- **Transport selected at runtime by env var:**
  - `MCP_TRANSPORT=stdio` (default) → `mcp.run()` — Claude Desktop local + `mcp dev`.
  - `MCP_TRANSPORT=http` → `mcp.run(transport="streamable-http")` on `0.0.0.0:$PORT`
    — for HF Spaces and the LangGraph client. Same file, one env var, no rewrite.

### Helpers

- `_resolve_city(name)` — case-insensitive → canonical `City`, or `None`.
- `_resolve_metric(name)` — case-insensitive alias → real column, or `None`.
  `METRIC_MAP`: `aqi→AQI, pm25/pm2.5→PM2.5, pm10→PM10, no2→NO2, so2→SO2, o3→O3,
  co→CO, nh3→NH3`.
- `_latest_valid(frame, column)` — most recent non-null row → `(value, as_of_date)`.

## Tools (the docstrings + type hints ARE the model-facing interface)

1. `list_cities() -> dict` — `cities`, `count`, `date_range`, `metrics`, and a `note`
   that data is historical.
2. `get_aqi(city, date?) -> dict` — AQI + bucket + all pollutants for a day. No date →
   latest valid AQI day. Reports `as_of`. Unknown city/date → `{"error": ...}`.
3. `compare_cities(cities, metric="aqi") -> dict` — latest-valid value per city, each
   with its `as_of`. Unknown city → null + note; unknown metric → error.
4. `trend(city, metric="aqi", days=30) -> dict` — last `days` non-null daily points
   `{date, value}` + a `summary` (min/max/mean/change/direction).
5. `rank_cities(metric="aqi", n=5, order="desc") -> dict` — cities ranked by
   latest-valid value. `desc` = worst first. Answers the demo question.

All returns are JSON-able; floats rounded to 2 decimals; bad inputs return a clear
`{"error": ...}` rather than raising.

## Repo / environment

- `.venv` on **Python 3.13** (3.14 wheels for the MCP/pydantic stack are still spotty).
- `requirements.txt` gains `mcp[cli]>=1.27,<2` (pandas/pyarrow already present).
- README gains an "MCP server" section: run, inspect, wire to Claude Desktop.

## Verification (Done criteria)

1. `smoke_test.py` exercises all five tool functions directly; then
   `mcp dev air_quality_mcp.py` works in the MCP Inspector (Node/npx confirmed present).
2. Generate the exact `claude_desktop_config.json` snippet (absolute paths;
   `command = E:\air_quality\.venv\Scripts\python.exe`) + step-by-step for
   Settings → Developer → Edit Config → restart, so Claude answers
   *"which city has the worst AQI right now?"* via `rank_cities`. Debug via
   `C:\Users\<user>\AppData\Roaming\Claude\logs`.

## Watch-outs

- Absolute paths only in the Claude config; no trailing commas (silently disables all
  servers); `command` must be the venv python with `mcp` + `pandas` installed.
- Data is historical: the demo answers as of 2020-07-01 (Ahmedabad 119 worst).
- Python 3.14 wheel risk → venv pinned to 3.13.
