# Deploy MCP Server to Hugging Face Spaces — Design (Step 2)

**Date:** 2026-06-18
**Status:** Approved
**Scope:** Deploy `air_quality_mcp.py` as a remote, token-protected MCP server on a
Hugging Face Docker Space, reachable over streamable-HTTP. NOT in scope: the LangGraph
chatbot (step 3). Claude Desktop is explicitly **not** a consumer — the only client is
the LangGraph chatbot.

## Decisions

- **Dedicated minimal HF Docker Space** (not the whole project repo, not a Gradio/
  Streamlit SDK space). Holds only the deployable copy: server + parquet + Dockerfile.
- **Bearer-token auth.** `POST /mcp` requires `Authorization: Bearer <token>`; the token
  is an HF Space **secret** (`MCP_AUTH_TOKEN`), never committed. `GET /` is an open
  health page.
- **Transport:** streamable-HTTP via the existing `MCP_TRANSPORT=http` path.

## Code change (additive, verified locally)

`air_quality_mcp.py` gains `_run_http()`:
- Builds the MCP ASGI app via `mcp.streamable_http_app()`.
- Adds an open `GET /` health route.
- If `MCP_AUTH_TOKEN` is set, wraps the app in a **pure-ASGI** middleware that checks the
  bearer header and returns 401 otherwise. Pure ASGI (not Starlette `BaseHTTPMiddleware`)
  so it does not buffer/break the `/mcp` SSE stream. Open paths: `/`, `/health`.
- Runs uvicorn on `HOST:PORT` (defaults `0.0.0.0:7860`).
- Logs a warning if no token is set.

Local stdio path (`mcp.run()`) is unchanged.

## Space contents (`hf-space/`, the Space repo root)

- `air_quality_mcp.py` — deployable copy of the server.
- `data/processed/city_day_clean.parquet` — 0.58 MB, no git-lfs needed.
- `requirements.txt` — minimal: `mcp[cli]>=1.27,<2`, `pandas`, `pyarrow` (no Streamlit;
  uvicorn/starlette ship with mcp[cli]).
- `Dockerfile` — `python:3.13-slim`, install deps, copy server + parquet,
  `ENV MCP_TRANSPORT=http HOST=0.0.0.0 PORT=7860`, `EXPOSE 7860`, `CMD python air_quality_mcp.py`.
- `README.md` — HF YAML front-matter (`sdk: docker`, `app_port: 7860`).
- `.gitattributes` — `*.parquet binary`.

## Endpoint

`https://<hf-username>-india-air-quality.hf.space/mcp` (POST, bearer-protected).

## Verification

Local (done): health 200 open; `/mcp` → 401 without/with-wrong token; a real
`streamablehttp_client` with the correct header initialized, listed all 5 tools, and
called `rank_cities` correctly. Remote: repeat the same checks against the live URL once
deployed.

## Deploy steps (user-credentialed)

1. Create a Docker Space named `india-air-quality`.
2. Add Space secret `MCP_AUTH_TOKEN`.
3. Push `hf-space/` contents to the Space git repo; wait for the build.
4. Verify the live URL (health + 401 + authed client).

## Watch-outs

- Token only in the HF secret, never in git.
- HF free Docker Spaces sleep after inactivity → first request cold-starts.
- Container must listen on the `app_port` (7860); matches our `PORT` default.
