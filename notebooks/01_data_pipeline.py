"""
Data Pipeline - run once after downloading the Kaggle dataset.

Expected inputs (place in data/raw/):
  - city_day.csv
  - station_day.csv
  - stations.csv

Outputs written to data/processed/:
  - city_day_clean.parquet
  - station_day_blr_clean.parquet

Usage:
  python notebooks/01_data_pipeline.py
"""

import pandas as pd
import numpy as np
from pathlib import Path

RAW = Path("data/raw")
PROCESSED = Path("data/processed")
PROCESSED.mkdir(parents=True, exist_ok=True)

YEAR_START = 2015
YEAR_END = 2020

CITIES_OF_INTEREST = [
    "Ahmedabad", "Bengaluru", "Chennai", "Delhi", "Hyderabad",
    "Jaipur", "Kolkata", "Lucknow", "Mumbai", "Patna",
    "Visakhapatnam",
]

POLLUTANTS = ["PM2.5", "PM10", "NO2", "SO2", "O3", "CO", "NH3"]

SEASON_MAP = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Spring", 4: "Spring", 5: "Spring",
    6: "Monsoon", 7: "Monsoon", 8: "Monsoon", 9: "Monsoon",
    10: "Post-Monsoon", 11: "Post-Monsoon",
}


def classify_aqi(aqi):
    if pd.isna(aqi):
        return "Unknown"
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Satisfactory"
    if aqi <= 200:
        return "Moderate"
    if aqi <= 300:
        return "Poor"
    if aqi <= 400:
        return "Very Poor"
    return "Severe"


def process_city_day() -> pd.DataFrame:
    print("Loading city_day.csv ...")
    df = pd.read_csv(RAW / "city_day.csv", parse_dates=["Date"])

    df = df[(df["Date"].dt.year >= YEAR_START) & (df["Date"].dt.year <= YEAR_END)]
    df = df[df["City"].isin(CITIES_OF_INTEREST)].copy()
    df["City"] = df["City"].str.strip()

    pollutant_cols = [c for c in POLLUTANTS if c in df.columns]
    df = df.dropna(subset=["AQI"] + pollutant_cols, how="all")

    # Drop physically impossible AQI values - CPCB scale is 0-500
    bad = df["AQI"] > 500
    if bad.sum() > 0:
        print(f"  Dropping {bad.sum()} rows with AQI > 500 (bad sensor readings)")
    df = df[~bad].copy()

    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["MonthName"] = df["Date"].dt.strftime("%b")
    df["Season"] = df["Month"].map(SEASON_MAP)
    df["AQI_Bucket"] = df["AQI"].apply(classify_aqi)

    df = df.sort_values(["City", "Date"]).reset_index(drop=True)

    out_path = PROCESSED / "city_day_clean.parquet"
    df.to_parquet(out_path, index=False)
    print(f"  Saved {len(df):,} rows to {out_path}")
    print(f"  Cities: {sorted(df['City'].unique())}")
    print(f"  Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
    return df


def process_station_day_blr() -> pd.DataFrame:
    print("\nLoading station_day.csv + stations.csv ...")
    stations = pd.read_csv(RAW / "stations.csv")
    stations.columns = stations.columns.str.lstrip("﻿")

    blr_ids = stations[
        stations["City"].str.contains("Bengaluru|Bangalore", case=False, na=False)
    ]["StationId"].tolist()
    print(f"  Bangalore station IDs: {blr_ids}")

    df = pd.read_csv(RAW / "station_day.csv", parse_dates=["Date"])
    df = df[df["StationId"].isin(blr_ids)].copy()
    df = df[(df["Date"].dt.year >= YEAR_START) & (df["Date"].dt.year <= YEAR_END)]

    df = df.merge(
        stations[["StationId", "StationName", "City"]],
        on="StationId", how="left"
    )

    pollutant_cols = [c for c in POLLUTANTS if c in df.columns]
    df = df.dropna(subset=pollutant_cols, how="all")

    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Season"] = df["Month"].map(SEASON_MAP)
    df["StationShort"] = df["StationName"].str.replace(
        r",\s*Bengaluru\s*-\s*(CPCB|KSPCB)", "", regex=True
    ).str.strip()

    df = df.sort_values(["StationId", "Date"]).reset_index(drop=True)

    out_path = PROCESSED / "station_day_blr_clean.parquet"
    df.to_parquet(out_path, index=False)
    print(f"  Saved {len(df):,} rows to {out_path}")
    print(f"  Stations: {sorted(df['StationShort'].unique())}")
    print(f"  Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
    return df


def main():
    city_df = process_city_day()
    blr_df = process_station_day_blr()
    print("\nPipeline complete.")
    print(f"  city_day_clean:        {len(city_df):,} rows")
    print(f"  station_day_blr_clean: {len(blr_df):,} rows")


if __name__ == "__main__":
    main()
