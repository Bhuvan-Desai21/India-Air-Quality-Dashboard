"""
Data loading utilities.
Reads cleaned parquet files from data/processed/ and caches them via st.cache_data.
All page files import from here — never load raw CSVs in page files.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"

CITIES = [
    "Ahmedabad", "Bengaluru", "Chennai", "Delhi", "Hyderabad",
    "Jaipur", "Kolkata", "Lucknow", "Mumbai", "Patna",
    "Visakhapatnam",
]

POLLUTANTS = ["PM2.5", "PM10", "NO2", "SO2", "O3", "CO", "NH3"]

AQI_BUCKET_ORDER = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]

AQI_COLORS = {
    "Good":         "#00B050",
    "Satisfactory": "#92D050",
    "Moderate":     "#FFFF00",
    "Poor":         "#FF7C00",
    "Very Poor":    "#FF0000",
    "Severe":       "#7030A0",
    "Unknown":      "#888888",
}

SEASON_ORDER = ["Winter", "Spring", "Monsoon", "Post-Monsoon"]

MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@st.cache_data
def load_city_day() -> pd.DataFrame:
    """
    City-level daily AQI data, 2015-2020, 11 cities.
    Columns: City, Date, PM2.5, PM10, NO2, SO2, O3, CO, NH3, AQI, AQI_Bucket,
             Year, Month, MonthName, Season
    """
    path = DATA_DIR / "city_day_clean.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Processed data not found at {path}. "
            "Run: python notebooks/01_data_pipeline.py"
        )
    return pd.read_parquet(path)


@st.cache_data
def load_station_day() -> pd.DataFrame:
    """
    Station-level daily data for 10 Bangalore monitoring stations, 2015-2020.
    Columns: StationId, StationShort, StationName, City, Date,
             PM2.5, PM10, NO2, SO2, O3, CO, NH3, AQI, AQI_Bucket,
             Year, Month, Season
    """
    path = DATA_DIR / "station_day_blr_clean.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Processed data not found at {path}. "
            "Run: python notebooks/01_data_pipeline.py"
        )
    return pd.read_parquet(path)
