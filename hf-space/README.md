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

A remote [Model Context Protocol](https://modelcontextprotocol.io) server exposing
India air-quality analysis (11 cities, daily, 2015–2020) as tools over
**streamable-HTTP**. Built as the agentic layer for an air-quality dashboard and
consumed by a LangGraph chatbot.

## Endpoint

- `GET /` — health check (open).
- `POST /mcp` — MCP streamable-HTTP endpoint. **Requires** `Authorization: Bearer <token>`
  when the `MCP_AUTH_TOKEN` secret is set (it is, in this Space).

## Tools

`list_cities`, `get_aqi`, `compare_cities`, `trend`, `rank_cities`.

The data is historical (2015–2020); every tool reports the as-of date it used.

> Source lives in the project repo; this Space holds the deployable copy
> (`air_quality_mcp.py`, the cleaned parquet, and the Dockerfile).
