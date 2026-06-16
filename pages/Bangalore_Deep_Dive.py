"""
Page 5: Bangalore Deep Dive — The Hyperlocal Disparity
Core Question: How does air quality vary across different neighborhoods and micro-environments?
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.style import apply_brand_style, configure_plotly_theme, render_station_monitor, TOKENS, AQI_COLORS
from utils.data_loader import load_station_day, POLLUTANTS

st.set_page_config(page_title="Hyperlocal Disparities", layout="wide")
apply_brand_style()

df = load_station_day()

# Coordinate mappings for Bangalore monitoring stations
STATION_COORDS = {
    "BTM Layout": [12.9166, 77.6101],
    "BWSSB Kadabesanahalli": [12.9367, 77.6974],
    "Bapuji Nagar": [12.9566, 77.5350],
    "City Railway Station": [12.9783, 77.5696],
    "Hebbal": [13.0358, 77.5970],
    "Hombegowda Nagar": [12.9419, 77.5956],
    "Jayanagar 5th Block": [12.9248, 77.5815],
    "Peenya": [13.0322, 77.5250],
    "Sanegurava Halli": [12.9904, 77.5385],
    "Silk Board": [12.9176, 77.6226],
}

# Sidebar filters
with st.sidebar:
    st.header("Briefing Filters")
    year_range = st.slider("Select Timeline", 2015, 2020, (2015, 2020))
    pollutant = st.selectbox("Select Agent", POLLUTANTS, index=0)

filtered = df[df["Year"].between(year_range[0], year_range[1])]
aqi_filtered = filtered[filtered["AQI"].notna()]

# Calculate statistics
station_avg = (
    aqi_filtered.groupby("StationShort")
    .agg(
        avg_aqi=("AQI", "mean"),
        max_aqi=("AQI", "max"),
        total_days=("AQI", "count")
    )
    .reset_index()
    .sort_values("avg_aqi", ascending=False)
    .reset_index(drop=True)
)

worst_station = station_avg.iloc[0]
best_station = station_avg.iloc[-1]
diff_aqi = worst_station["avg_aqi"] - best_station["avg_aqi"]

# Exceedance counts per station (AQI > 100 is Poor/Moderate warning threshold)
exceed_counts = (
    aqi_filtered[aqi_filtered["AQI"] > 100]
    .groupby("StationShort").size().reset_index(name="exceed_days")
)
station_avg = station_avg.merge(exceed_counts, on="StationShort", how="left").fillna(0)
station_avg["exceed_days"] = station_avg["exceed_days"].astype(int)

# Determine primary pollutant per station
station_pollutants = {}
for s in station_avg["StationShort"]:
    s_df = filtered[filtered["StationShort"] == s]
    pm25_mean = s_df["PM2.5"].mean()
    pm10_mean = s_df["PM10"].mean()
    if pd.notna(pm25_mean) and (pd.isna(pm10_mean) or pm25_mean * 1.8 > pm10_mean):
        station_pollutants[s] = "PM2.5"
    else:
        station_pollutants[s] = "PM10"

def get_safety_bucket(aqi):
    if aqi <= 50: return "Good"
    if aqi <= 100: return "Satisfactory"
    if aqi <= 200: return "Moderate"
    if aqi <= 300: return "Poor"
    if aqi <= 400: return "Very Poor"
    return "Severe"

# Header and title
st.markdown('<h1 style="font-size: 2.2rem; margin-bottom: 4px;">Bangalore Neighborhood View</h1>', unsafe_allow_html=True)
st.caption(f"Air quality tracked by different monitors in Bangalore.")

# Summary/insight banner
st.markdown(
    f"""
    <div class="insight-card">
        <h4 style="margin-top:0; margin-bottom:8px; font-size:1.05rem; color:{TOKENS["amber"]};">
            Neighborhood Differences
        </h4>
        <p style="margin:0; font-size:0.92rem; line-height:1.6; color:{TOKENS["text_secondary"]};">
            <b>Neighborhood Differences</b>: There is a difference of <b>{diff_aqi:.0f} AQI points</b> between the most polluted neighborhood (<b>{worst_station['StationShort']}</b>, average AQI: {worst_station['avg_aqi']:.0f}) and the cleanest neighborhood (<b>{best_station['StationShort']}</b>, average AQI: {best_station['avg_aqi']:.0f}). This shows that city-wide averages hide major local air pollution risks.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('<div style="margin-top: 16px;"></div>', unsafe_allow_html=True)

# Main dashboard layout
col_left, col_right = st.columns([6, 4])

with col_left:
    st.markdown('<h3 style="font-size: 1.2rem; margin-top: 0; margin-bottom: 8px;">Neighborhood Map</h3>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 0.82rem; color: #A6B1BE; margin-bottom: 12px;">Location of air quality monitors in Bangalore. Larger circles show higher pollution levels.</p>', unsafe_allow_html=True)
    
    # Map rendering
    coords_list = []
    for s in station_avg["StationShort"]:
        if s in STATION_COORDS:
            coords_list.append({
                "StationShort": s,
                "lat": STATION_COORDS[s][0],
                "lon": STATION_COORDS[s][1]
            })
    map_coords_df = pd.DataFrame(coords_list)
    map_data = station_avg.merge(map_coords_df, on="StationShort")
    map_data["safety_level"] = map_data["avg_aqi"].apply(get_safety_bucket)
    map_data["color"] = map_data["safety_level"].map(AQI_COLORS) + "99"
    map_data["size"] = map_data["avg_aqi"] * 15
    
    st.map(map_data, latitude="lat", longitude="lon", color="color", size="size")
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # Monthly heatmap
    st.markdown('<h3 style="font-size: 1.2rem; margin-top: 0; margin-bottom: 8px;">Neighborhood Heatmap</h3>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 0.82rem; color: #A6B1BE; margin-bottom: 12px;">Average AQI by month for each neighborhood sensor, ordered from worst to best.</p>', unsafe_allow_html=True)
    
    monthly = (
        aqi_filtered.groupby(["StationShort", "Year", "Month"])["AQI"]
        .mean()
        .reset_index()
    )
    monthly["YearMonth"] = pd.to_datetime(
        monthly["Year"].astype(str) + "-" + monthly["Month"].astype(str).str.zfill(2)
    )
    monthly = monthly.sort_values("YearMonth")
    
    pivot = monthly.pivot_table(index="StationShort", columns="YearMonth", values="AQI")
    pivot.columns = pivot.columns.strftime("%b %Y")
    
    # Sort rows to match station ranking
    station_order = station_avg["StationShort"].tolist()
    pivot = pivot.reindex([s for s in station_order if s in pivot.index])
    
    fig_heat = px.imshow(
        pivot,
        color_continuous_scale="RdYlGn_r",
        aspect="auto",
        zmin=0, zmax=250,
        labels=dict(x="", y="Station", color="Avg AQI"),
    )
    fig_heat = configure_plotly_theme(fig_heat)
    fig_heat.update_layout(
        height=300,
        margin=dict(t=10, b=10, l=40, r=10),
        xaxis=dict(tickangle=45, tickfont=dict(size=9)),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with col_right:
    st.markdown('<h3 style="font-size: 1.2rem; margin-top: 0; margin-bottom: 16px;">Neighborhood Monitors Status</h3>', unsafe_allow_html=True)
    
    # Render all station monitors dynamically in a single scrollable ledger
    for _, row in station_avg.iterrows():
        station_name = row["StationShort"]
        render_station_monitor(
            station_name,
            row["avg_aqi"],
            station_pollutants.get(station_name, "PM2.5"),
            row["exceed_days"],
            get_safety_bucket(row["avg_aqi"])
        )

st.markdown('<div style="margin-top: 32px; border-top: 1px solid #27303A; padding-top: 24px;"></div>', unsafe_allow_html=True)

# Lockdown impact and outliers
st.markdown(f'<h3 style="font-size: 1.25rem; margin-bottom: 16px;">Lockdown Impact and Outliers</h3>', unsafe_allow_html=True)

col_bottom_left, col_bottom_right = st.columns([6, 4])

with col_bottom_left:
    # COVID lockdown comparison: 2019 vs 2020 per station
    lock_df = df[
        df["Month"].isin([3, 4, 5, 6]) &
        df["Year"].isin([2019, 2020]) &
        df["AQI"].notna()
    ]
    lock_avg = (
        lock_df.groupby(["StationShort", "Year"])["AQI"]
        .mean()
        .reset_index()
    )
    
    lock_avg["Year"] = lock_avg["Year"].astype(str)
    fig_lock = px.bar(
        lock_avg,
        x="StationShort",
        y="AQI",
        color="Year",
        barmode="group",
        color_discrete_map={"2019": TOKENS["orange"], "2020": TOKENS["green"]},
        labels={"AQI": "Average AQI (Mar-Jun)", "StationShort": "Neighborhood"},
        text_auto=".0f",
        category_orders={"StationShort": station_avg["StationShort"].tolist()},
    )
    fig_lock = configure_plotly_theme(fig_lock)
    fig_lock.update_layout(
        xaxis_title=None,
        xaxis_tickangle=30,
        height=300,
        margin=dict(t=20, b=20, l=40, r=20),
    )
    st.plotly_chart(fig_lock, use_container_width=True)

with col_bottom_right:
    st.markdown(
        f"""
        <div class="insight-card" style="min-height: 300px;">
            <h5 style="margin-top:0; margin-bottom:8px; font-size:0.85rem; color:{TOKENS["amber"]};">
                Local Outliers
            </h5>
            <p style="font-size:0.82rem; line-height:1.6; color:{TOKENS["text_secondary"]}; margin-bottom:12px;">
                There is a gap of <b>{diff_aqi:.0f} AQI points</b> between <b>{worst_station['StationShort']}</b> and <b>{best_station['StationShort']}</b>. This means that a person living near <b>{worst_station['StationShort']}</b> breathes much more polluted air than someone living near <b>{best_station['StationShort']}</b>, even though they are in the same city.
            </p>
            <div style="border-top: 1px dashed {TOKENS['border']}; padding-top: 10px; font-size:0.75rem; color:{TOKENS['text_muted']}; font-family: 'IBM Plex Mono', monospace;">
                Main Cause: vehicle exhaust and smoke near busy traffic roads.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Footer
st.markdown('<div style="margin-top: 24px; border-top: 1px solid #27303A; padding-top: 16px;"></div>', unsafe_allow_html=True)
st.markdown(
    'You can choose different years or pollutants in the sidebar. '
    'To go back to the national overview, visit the **[National Briefing Landing Hub](/)**.'
)


