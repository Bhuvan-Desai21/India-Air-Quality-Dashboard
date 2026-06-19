---
title: India Air Quality MCP
emoji: 🌫️
colorFrom: indigo
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# India Air Quality MCP Server

A remote [Model Context Protocol](https://modelcontextprotocol.io) server exposing India
air-quality analysis — **11 cities + 10 Bengaluru stations, daily, 2015–2020** — as **11
tools** over streamable-HTTP. Built as the agentic layer for an air-quality dashboard and
consumed by a LangGraph chatbot.

## Endpoint

- `GET /` — health check (open).
- `POST /mcp` — MCP streamable-HTTP endpoint. **Requires** `Authorization: Bearer <token>`
  when the `MCP_AUTH_TOKEN` secret is set (it is, in this Space).

Example (the bearer token is a Space secret, not shown):

```bash
curl -N -H "Authorization: Bearer $MCP_AUTH_TOKEN" \
     -H "Content-Type: application/json" \
     https://Bhuvandesai-india-air-quality.hf.space/mcp
```

## Tools

`list_cities`, `get_aqi`, `compare_cities`, `trend`, `rank_cities`, `seasonal_breakdown`,
`lockdown_impact`, `health_advisory`, `yearly_summary`, `compare_to_standard`,
`station_breakdown`.

The data is historical (2015–2020); every tool reports the as-of date it used.

> Source lives in the project repo; this Space holds the deployable copy
> (`air_quality_mcp.py`, both cleaned parquets, and the Dockerfile).
