# CLAUDE.md

Guidance for working in this repo.

## What this is

India Air Quality Intelligence Platform — a Streamlit dashboard over cleaned CPCB
air-quality data (11 cities + 10 Bengaluru stations, daily, 2015–2020), plus an MCP
server that exposes the same analysis as 11 tools, and an "Ask AI" LangGraph chatbot
that calls those tools.

## Layout

- `app.py` — dashboard landing page; `pages/*.py` — the five analysis pages.
- `utils/data_loader.py` — the ONLY place pages load parquet (cached). `utils/style.py` —
  design tokens, global CSS, the `configure_plotly_theme` helper, and HTML components.
- `air_quality_mcp.py` — the MCP server (Streamlit-free; reads parquet directly). The 11
  tools' docstrings + type hints ARE the model-facing interface.
- `hf-space/` — the deployable copy of the server. `hf-space/air_quality_mcp.py` MUST stay
  byte-identical to the root server (author in root, then `cp` to hf-space).
- `chatbot/` — the LangGraph agent (`agent.py`), background event-loop bridge
  (`runtime.py`), config (`config.py`), and shared chat UI (`ui.py`).
- `data/processed/*.parquet` — cleaned data. Regenerate with
  `python notebooks/01_data_pipeline.py` from raw Kaggle CSVs in `data/raw/`.
- `docs/superpowers/{specs,plans}/` — design specs and implementation plans.

## Environment

Windows + a project venv. Use `.venv/Scripts/python.exe` (NOT bare `python`).

## Commands

```bash
# Run the dashboard
.venv/Scripts/python.exe -m streamlit run app.py        # http://localhost:8501

# Tests (pytest suite + MCP tool smoke script)
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe smoke_test.py

# MCP server locally
.venv/Scripts/python.exe air_quality_mcp.py             # stdio (default)
.venv/Scripts/mcp.exe dev air_quality_mcp.py            # MCP Inspector (needs Node/npx)
```

## MCP server

11 tools: `list_cities`, `get_aqi`, `compare_cities`, `trend`, `rank_cities`,
`seasonal_breakdown`, `lockdown_impact`, `health_advisory`, `yearly_summary`,
`compare_to_standard`, `station_breakdown`. Data is historical; every tool reports an
`as_of` date. Bad input returns `{"error": ...}` rather than raising. Tests:
`tests/test_mcp_tools.py`.

Transport is chosen by env var: `MCP_TRANSPORT=stdio` (default) or `http`
(streamable-HTTP on `0.0.0.0:$PORT`, optional `MCP_AUTH_TOKEN` bearer auth).

## Deploying the Hugging Face Space

The MCP server runs as a Docker Space at `Bhuvandesai/india-air-quality`. To redeploy:

1. Make changes in root `air_quality_mcp.py`, then `cp air_quality_mcp.py hf-space/`.
2. Upload the `hf-space/` folder (a write-scoped HF token must be logged in):
   `HfApi().upload_folder(folder_path="hf-space", repo_id="Bhuvandesai/india-air-quality", repo_type="space")`.
3. Verify the rebuild: `.venv/Scripts/python.exe scripts/verify_hf_deploy.py`.

`hf-space/.gitattributes` MUST keep `*.parquet filter=lfs diff=lfs merge=lfs -text` —
without the `filter=lfs` directive the Docker build checks out LFS pointer files instead
of the real parquets and the server crashes on import ("Parquet magic bytes not found").

## Conventions

- Don't load raw CSVs in page files — go through `utils/data_loader.py`.
- Keep the server Streamlit-free: do not import `utils/` into `air_quality_mcp.py`;
  duplicate small constants instead.
- Dashboard palette is the warm near-black `TOKENS` in `utils/style.py`; don't reintroduce
  cool-gray hex literals.
- Commit messages: do NOT add a `Co-Authored-By` trailer.
