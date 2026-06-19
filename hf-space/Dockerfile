# India Air Quality MCP server -- Hugging Face Docker Space
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY air_quality_mcp.py .
COPY data/processed/city_day_clean.parquet data/processed/city_day_clean.parquet
COPY data/processed/station_day_blr_clean.parquet data/processed/station_day_blr_clean.parquet

# Remote HTTP transport on the HF Spaces port. MCP_AUTH_TOKEN is injected at
# runtime as a Space secret (Settings -> Variables and secrets) -- never baked in.
ENV MCP_TRANSPORT=http \
    HOST=0.0.0.0 \
    PORT=7860

EXPOSE 7860

CMD ["python", "air_quality_mcp.py"]
