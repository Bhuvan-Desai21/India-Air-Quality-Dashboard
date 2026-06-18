# India Air Quality Intelligence Platform

An analytical environmental intelligence platform that tracks and visualizes air quality trends in major Indian cities from 2015 to 2020. This platform is designed to make complex air pollution data accessible, offering insights into geographic disparities, seasonal trends, and hyperlocal differences.

## Live Application

An interactive version of this platform is deployed here:
👉 **[Streamlit Cloud Demo Link](https://share.streamlit.io/your-username/your-repo-name)** *(Placeholder - replace with your actual deployment URL)*

## Features

- **National Overview**: National air quality briefing demonstrating comparative exposure across major cities.
- **Geographic Disparities**: Interactive location maps and multi-year trend trackers.
- **Specific Pollutant Profiles**: Detailed breakdown of chemical agents (PM2.5, PM10, NO2, etc.) compared against WHO and CPCB safety standards.
- **Seasonal & Lockdown Dynamics**: Interactive tools showing winter weather inversions and the drop in pollution during the 2020 COVID lockdowns.
- **Health Risk Assessments**: Data-dense exposure metrics showing the yearly impact of air pollution on daily life.
- **Hyperlocal Analysis (Bangalore)**: Deep dive into street-level neighborhood sensors (Silk Board, Peenya, BTM Layout, etc.) to highlight local outliers.

## Getting Started

### Prerequisites

You need Python 3.8 or higher installed on your system.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

Start the Streamlit dashboard locally:
```bash
streamlit run app.py
```

Open your browser and navigate to `http://localhost:8501`.

## Data Pipeline

If you need to reprocess the datasets, place the raw CSV files (`city_day.csv`, `station_day.csv`, and `stations.csv`) from the Kaggle dataset in `data/raw/` and run:

```bash
python notebooks/01_data_pipeline.py
```

This cleans and converts the raw data to compressed Parquet files under `data/processed/` for faster loading times.

## MCP Server (Agentic Layer)

The same analysis is exposed as an **MCP (Model Context Protocol) server**
(`air_quality_mcp.py`), so LLM clients — Claude Desktop today, a LangGraph chatbot
later — can answer data questions by *calling tools* instead of guessing. It reads the
cleaned parquet directly (no Streamlit dependency) and resolves the data path from the
script location, so it runs from any working directory.

### Tools

| Tool | Purpose |
| --- | --- |
| `list_cities()` | Cities + dataset coverage (2015–2020, historical). |
| `get_aqi(city, date?)` | AQI, category, and all pollutants for a day (latest valid if no date). |
| `compare_cities(cities, metric)` | One metric across cities, each at its latest valid reading. |
| `trend(city, metric, days)` | Recent daily series + a min/max/mean/direction summary. |
| `rank_cities(metric, n, order)` | Cities ranked best/worst — e.g. *"worst AQI right now?"*. |

### Setup

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt   # includes mcp[cli]
```

### Run / test

```bash
# Smoke-test the tool logic (no protocol needed):
.venv\Scripts\python.exe smoke_test.py

# Inspect interactively in the MCP Inspector (requires Node.js / npx):
.venv\Scripts\mcp.exe dev air_quality_mcp.py
```

### Transports

The same file serves every client; the transport is chosen by environment variable:

| `MCP_TRANSPORT` | Behaviour | Used by |
| --- | --- | --- |
| `stdio` (default) | `mcp.run()` | Claude Desktop (local), MCP Inspector |
| `http` | `mcp.run(transport="streamable-http")` on `0.0.0.0:$PORT` | Hugging Face Spaces, LangGraph client |

### Connect to Claude Desktop (local, stdio)

Add this server to Claude Desktop via **Settings → Developer → Edit Config**, then
restart Claude Desktop. Merge the `mcpServers` block from
[`claude_desktop_config.snippet.json`](claude_desktop_config.snippet.json) into your
existing config — use **absolute paths** and the **venv python**. After restarting,
ask: *"which city has the worst AQI right now?"* and Claude will call `rank_cities`.

## License

This project is open-source and available under the MIT License.
