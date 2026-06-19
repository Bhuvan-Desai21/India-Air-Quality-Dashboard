"""Generate the committed regression fixture. Run once:
   .venv/Scripts/python.exe tests/fixtures/make_fixture.py
"""
import pandas as pd
from pathlib import Path

base = dict(PM10=100.0, NO2=40.0, SO2=40.0, O3=50.0, CO=1.0, NH3=200.0)
rows = []

# City "Norm": deterministic paths.
d = pd.date_range("2020-01-01", periods=6)
rows.append({"City": "Norm", "Date": d[0], "PM2.5": 90.0, "AQI": 195.0, **base})   # normal -> 200
rows.append({"City": "Norm", "Date": d[1], "PM2.5": 5000.0, "AQI": 480.0, **base}) # impossible -> nulled
rows.append({"City": "Norm", "Date": d[2], "PM2.5": 90.0, "NO2": 40.0, "AQI": 160.0})  # <3 pollutants
rows.append({"City": "Norm", "Date": d[3], "PM2.5": 60.0, "AQI": 487.0, **base})   # inconsistent original
rows.append({"City": "Norm", "Date": d[4], "PM2.5": 90.0, "AQI": 200.0, **base})
rows.append({"City": "Norm", "Date": d[5], "PM2.5": 90.0, "AQI": 200.0, **base})

# City "Spike": varied baseline (MAD>0) with one isolated spike at index 7.
ds = pd.date_range("2020-02-01", periods=16)
pm = [80.0, 100.0] * 8
pm[7] = 500.0
for i, dt in enumerate(ds):
    rows.append({"City": "Spike", "Date": dt, "PM2.5": pm[i], "AQI": 150.0, **base})

df = pd.DataFrame(rows)
out = Path(__file__).resolve().parent / "sample_city_day.parquet"
df.to_parquet(out, index=False)
print(f"wrote {len(df)} rows -> {out}")
