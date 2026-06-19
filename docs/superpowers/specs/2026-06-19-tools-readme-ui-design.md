# MCP Tools + README Glowup + UI Touchups — Design

**Date:** 2026-06-19
**Status:** Approved
**Scope:** Three semi-independent workstreams, one spec, one implementation plan:
1. Six new MCP tools (server goes 5 → 11).
2. Dashboard UI touchups (fix the `undefined`-in-charts bug, unify the leftover
   cool-gray palette to the warm tokens, minor chart/map hardening).
3. Full README glowup for both the GitHub root README and the Hugging Face Space card.

NOT in scope: dashboard layout redesign, new dashboard pages, chatbot/agent changes,
RAG/guardrails/eval work, new datasets.

## Context (verified against the repo)

- **MCP server** lives in two byte-identical copies that must stay in sync:
  `air_quality_mcp.py` (source of truth) and `hf-space/air_quality_mcp.py` (deploy copy).
  Streamlit-free: it reads parquet directly and resolves paths from `__file__`.
- Current tools (5): `list_cities`, `get_aqi`, `compare_cities`, `trend`, `rank_cities`.
  Helpers: `_resolve_city`, `_resolve_metric`, `_latest_valid`, `_city_frame`, `_coverage`.
  `METRIC_MAP` covers aqi/pm25/pm10/no2/so2/o3/co/nh3.
- **City data:** `data/processed/city_day_clean.parquet` — 11 cities, daily, 2015-01-01→
  2020-07-01, columns include `Season`, `Year`, `Month`, `MonthName`, many NaNs.
- **Station data:** `data/processed/station_day_blr_clean.parquet` — 10 Bangalore stations
  (`StationShort`), same pollutant columns. The MCP server currently ignores this file.
- **hf-space/** ships only `city_day_clean.parquet` (Dockerfile `COPY`s just that one).
- **UI:** 6 page files (`app.py` + `pages/*.py`) share `utils/style.py` `TOKENS` (warm
  near-black palette). 23 leftover **cool-gray** hex literals (`#A6B1BE`, `#27303A`, etc.)
  remain from before the palette unification and clash with the warm tokens.

## Workstream 1 — Six new MCP tools

All six are added to the source server and copied verbatim to the hf-space copy. Each:
reuses existing helpers, returns JSON-able dicts (floats rounded 2dp), reports an `as_of`
date or coverage, validates inputs and returns `{"error": ...}` on bad city/metric/order
rather than raising. Docstrings + type hints are the model-facing interface.

1. **`seasonal_breakdown(city, metric="aqi") -> dict`**
   Average of the metric per `Season`, ordered Winter → Spring → Monsoon → Post-Monsoon.
   Returns `{city, metric, seasons: {Season: {avg, min, max, n}}, peak_season,
   cleanest_season}`. Unknown city/metric → error.

2. **`lockdown_impact(city, metric="aqi") -> dict`**
   Compares the COVID-lockdown window **Mar–Jun 2019 vs Mar–Jun 2020** (months 3–6),
   mirroring the dashboard. Returns `{city, metric, window: "Mar-Jun",
   before: {year: 2019, avg, n}, after: {year: 2020, avg, n}, change_pct, direction}`.
   If either year has no data in the window, that side is null with a note.

3. **`health_advisory(city, date=None) -> dict`**
   Resolves AQI the same way `get_aqi` does (latest valid, or a given date), maps it to the
   CPCB category and a plain-language advisory + at-risk groups. Returns
   `{city, as_of, aqi, category, advisory, sensitive_groups}`. Uses a new in-server
   `ADVISORY` dict (the server must stay Streamlit-free, so it cannot import
   `utils/style.py`). Unknown city / no reading → error (same shape as `get_aqi`).

4. **`yearly_summary(city, metric="aqi") -> dict`**
   Year-by-year (2015–2020) aggregates. Returns `{city, metric,
   years: [{year, avg, min, max, n}], direction}` where `direction` compares the first vs
   last year with data. Unknown city/metric → error.

5. **`compare_to_standard(city, pollutant) -> dict`**
   Latest valid pollutant value vs WHO (2021) and CPCB annual limits, as multiples.
   Returns `{city, pollutant, value, as_of, unit, who_limit, who_multiple, cpcb_limit,
   cpcb_multiple, verdict}`. `pollutant` is required and must be a real pollutant
   (aqi is rejected with an error). WHO/CPCB limit dicts embedded in-server (mirroring
   `pages/Pollutant_Breakdown.py`); limits that are undefined for a pollutant come back
   null with the multiple null.

6. **`station_breakdown(metric="aqi", order="desc", n=10) -> dict`**
   Bangalore hyperlocal: ranks the station-level monitors by each station's latest valid
   value. Returns `{scope: "Bengaluru stations", metric, order,
   ranking: [{station, value, as_of}]}`. `order` desc=worst first / asc=cleanest first
   (clamped, validated like `rank_cities`). `n` clamped 1–20. Unknown metric/order → error.

### Server changes
- Load the station parquet once at import into `_station_df` (path resolved from
  `__file__`, same pattern as the city frame); add `_STATION_PATH`, a `_station_frame`
  helper and station-name handling. Guard so the city tools are unaffected.
- Add `ADVISORY` (category → advisory text + sensitive groups), `WHO_LIMITS`,
  `CPCB_LIMITS`, `UNITS`, and an `_aqi_category(aqi)` helper.
- `smoke_test.py` gains direct calls for all six new tools (happy path + one error path).

### Deploy changes (hf-space/)
- Add `hf-space/data/processed/station_day_blr_clean.parquet`.
- `Dockerfile`: add `COPY data/processed/station_day_blr_clean.parquet
  data/processed/station_day_blr_clean.parquet`.
- Copy the updated server to `hf-space/air_quality_mcp.py` (keep byte-identical).

## Workstream 2 — UI touchups

- **`undefined` bug:** launch the app locally, reproduce the `undefined` text in the
  affected chart(s), fix at the source (likely a Plotly hover/legend or `st.map` field
  hitting a NaN/missing value), and re-verify visually. Driven by evidence, not a guess.
- **Palette unification:** replace the 23 leftover cool-gray hex literals across `app.py`
  and `pages/*.py` with warm `TOKENS` (`#A6B1BE` → `TOKENS["text_secondary"]`; `#27303A`
  dividers → `TOKENS["border"]`; any other cool grays → nearest token). Convert affected
  plain strings to f-strings so they reference tokens, matching surrounding style.
- **Chart/map hardening:** give the Pollutant `px.box` brand colors instead of Plotly
  defaults; make the two `st.map` `color` expressions NaN-safe (fill unmapped buckets
  before appending the alpha suffix).
- No layout redesign; no behavioural change to data logic.

## Workstream 3 — README glowup (full, both)

- **GitHub root `README.md`:** add badges (Python · Streamlit · MCP · HF Space · MIT),
  a Mermaid architecture diagram (data → MCP server → {Claude Desktop, LangGraph chatbot};
  dashboard → data; HF Spaces deploy), restructured sections, the **updated 11-tool table
  with one-line example calls**, a quickstart, and **real screenshots** captured from the
  running app, stored under `assets/screenshots/` and referenced with repo-relative paths.
- **HF Space card (`hf-space/README.md`):** keep the required YAML front-matter (title,
  emoji, sdk: docker, app_port), update the tool list to all 11, tighten the prose, and add
  a short example call. Stays mostly text (HF renders repo-relative images from the Space,
  which doesn't carry these screenshots — so no broken image links there).

## Verification (Done criteria)

1. `.venv/Scripts/python.exe smoke_test.py` runs all 11 tools without raising; spot-check
   the new tools' output shapes (seasonal order, lockdown 2019/2020, advisory text, yearly
   direction, WHO/CPCB multiples, station ranking).
2. `streamlit run app.py` launches clean; every page visually verified — the `undefined`
   text is gone and no cool-gray stragglers remain against the warm background.
3. Both READMEs render correctly (badges resolve, Mermaid diagram parses, screenshots load
   in the GitHub README, HF front-matter intact).

## Watch-outs

- The two server files MUST stay byte-identical — author in the source, copy to hf-space.
- Server stays Streamlit-free: embed advisory/limit constants; do NOT import `utils/`.
- Station parquet must be shipped to hf-space AND its `Dockerfile` `COPY` added, or
  `station_breakdown` will 500 in the deployed Space.
- HF README images: don't reference repo-relative screenshots that won't exist in the Space.
- Keep float rounding / `as_of` reporting consistent with the existing five tools.
