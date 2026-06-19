"""
Page 1: City Overview — The Geography of Disparity
Core Question: Which cities are worst or improving, and how does geography shape this exposure?
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.style import apply_brand_style, configure_plotly_theme, render_city_fingerprint, TOKENS, AQI_COLORS
from utils.data_loader import load_city_day

st.set_page_config(page_title="Geography of Disparity", layout="wide")
apply_brand_style()

df = load_city_day()

# Sidebar filters
with st.sidebar:
    st.header("Briefing Filters")
    year_range = st.slider("Select Timeline", 2015, 2020, (2015, 2020))

filtered = df[df["Year"].between(year_range[0], year_range[1]) & df["AQI"].notna()]

# Calculate statistics
# Aggregated stats by city
city_stats = (
    filtered.groupby("City")
    .agg(
        avg_aqi=("AQI", "mean"),
        max_aqi=("AQI", "max"),
        avg_pm25=("PM2.5", "mean"),
        total_days=("AQI", "count")
    )
    .reset_index()
)

# Percentage of clean days (AQI <= 100)
clean_days = (
    filtered[filtered["AQI_Bucket"].isin(["Good", "Satisfactory"])]
    .groupby("City").size().reset_index(name="clean_count")
)
city_stats = city_stats.merge(clean_days, on="City", how="left").fillna(0)
city_stats["clean_pct"] = (city_stats["clean_count"] / city_stats["total_days"] * 100).round(1)

# Sort by worst AQI
city_stats = city_stats.sort_values("avg_aqi", ascending=False).reset_index(drop=True)

worst_city = city_stats.iloc[0]
best_city = city_stats.iloc[-1]
india_avg = filtered["AQI"].mean()

# Determine dominant pollutant
city_pollutants = {}
for idx, row in city_stats.iterrows():
    c = row["City"]
    c_df = filtered[filtered["City"] == c]
    pm25_mean = c_df["PM2.5"].mean()
    pm10_mean = c_df["PM10"].mean()
    no2_mean = c_df["NO2"].mean()
    
    if pd.notna(pm25_mean) and (pd.isna(pm10_mean) or pm25_mean * 2 > pm10_mean):
        city_pollutants[c] = "PM2.5"
    elif pd.notna(pm10_mean):
        city_pollutants[c] = "PM10"
    else:
        city_pollutants[c] = "NO2"

def aqi_bucket_label(aqi):
    if aqi <= 50: return "Good"
    if aqi <= 100: return "Satisfactory"
    if aqi <= 200: return "Moderate"
    if aqi <= 300: return "Poor"
    if aqi <= 400: return "Very Poor"
    return "Severe"

worst_pct_exposure = 100 - worst_city['clean_pct']
best_pct_exposure = 100 - best_city['clean_pct']

# Header and title
st.markdown('<h1 style="font-size: 2.2rem; margin-bottom: 4px;">Air Quality by Location</h1>', unsafe_allow_html=True)
st.caption(f"Air quality maps and trends across different cities in India.")

# Summary/insight banner
st.markdown(
    f"""
    <div class="insight-card">
        <h4 style="margin-top:0; margin-bottom:8px; font-size:1.05rem; color:{TOKENS["amber"]};">
            Air Pollution Disparities
        </h4>
        <p style="margin:0; font-size:0.92rem; line-height:1.6; color:{TOKENS["text_secondary"]};">
            How often is the air unsafe? In <b>{worst_city['City']}</b>, the air is unhealthy (AQI over 100) on <b>{worst_pct_exposure:.1f}%</b> of days. On the other hand, <b>{best_city['City']}</b> has clean air on <b>{best_city['clean_pct']:.1f}%</b> of days, thanks to coastal winds that blow pollution away.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('<div style="margin-top: 16px;"></div>', unsafe_allow_html=True)

# Main dashboard layout
col_left, col_right = st.columns([6, 4])

with col_left:
    st.markdown('<h3 style="font-size: 1.2rem; margin-top: 0; margin-bottom: 8px;">Air Quality Map</h3>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 0.82rem; color: #b3ada1; margin-bottom: 12px;">Larger circles show higher average pollution. Colors show the risk level.</p>', unsafe_allow_html=True)
    
    # Map rendering
    city_coords = pd.DataFrame([
        {"City": "Ahmedabad", "lat": 23.0225, "lon": 72.5714},
        {"City": "Bengaluru", "lat": 12.9716, "lon": 77.5946},
        {"City": "Chennai", "lat": 13.0827, "lon": 80.2707},
        {"City": "Delhi", "lat": 28.6139, "lon": 77.2090},
        {"City": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
        {"City": "Jaipur", "lat": 26.9124, "lon": 75.7873},
        {"City": "Kolkata", "lat": 22.5726, "lon": 88.3639},
        {"City": "Lucknow", "lat": 26.8467, "lon": 80.9462},
        {"City": "Mumbai", "lat": 19.0760, "lon": 72.8777},
        {"City": "Patna", "lat": 25.5941, "lon": 85.1376},
        {"City": "Visakhapatnam", "lat": 17.6868, "lon": 83.2185},
    ])
    
    map_data = city_stats.merge(city_coords, on="City")
    map_data["bucket"] = map_data["avg_aqi"].apply(aqi_bucket_label)
    map_data["color"] = map_data["bucket"].map(AQI_COLORS).fillna(TOKENS["text_muted"]) + "99"
    map_data["size"] = map_data["avg_aqi"] * 80
    
    st.map(map_data, latitude="lat", longitude="lon", color="color", size="size")
    
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # Yearly trends
    st.markdown('<h3 style="font-size: 1.2rem; margin-top: 0; margin-bottom: 8px;">Yearly Trends</h3>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 0.82rem; color: #b3ada1; margin-bottom: 12px;">See how average pollution has changed each year.</p>', unsafe_allow_html=True)
    
    annual = (
        filtered.groupby(["City", "Year"])["AQI"]
        .mean().reset_index()
        .rename(columns={"AQI": "Avg AQI"})
    )
    
    fig_trend = px.line(
        annual, x="Year", y="Avg AQI", color="City",
        markers=True,
        labels={"Avg AQI": "Average AQI"},
    )
    fig_trend = configure_plotly_theme(fig_trend)
    fig_trend.update_layout(
        xaxis=dict(tickmode="linear", dtick=1),
        hovermode="x unified",
        height=320,
        margin=dict(t=20, b=20, l=40, r=20),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
    st.markdown('<h3 style="font-size: 1.2rem; margin-top: 0; margin-bottom: 16px;">Air Quality Profiles by City</h3>', unsafe_allow_html=True)
    
    # Render all fingerprints sorted by worst average AQI
    for _, row in city_stats.iterrows():
        city_name = row["City"]
        pm25 = row["avg_pm25"]
        who_multiplier = pm25 / 5.0
        render_city_fingerprint(
            city_name,
            row["avg_aqi"],
            city_pollutants.get(city_name, "PM2.5"),
            who_multiplier,
            row["clean_pct"]
        )

# Worst day alert
worst_record_overall = filtered.loc[filtered["AQI"].idxmax()]
st.markdown(
    f"""
    <div class="danger-card" style="margin-top: 24px;">
        <h4 style="margin-top: 0; margin-bottom: 6px; font-size: 0.95rem; color: {TOKENS["red"]};">
            Worst Day on Record
        </h4>
        <p style="margin: 0; font-size: 0.88rem; line-height: 1.5; color: {TOKENS["text_secondary"]};">
            The worst pollution event in this data happened in <b>{worst_record_overall['City']}</b> on <b>{worst_record_overall['Date'].strftime('%d %b %Y')}</b>, when the daily AQI hit a dangerous peak of <b>{worst_record_overall['AQI']:.0f}</b> ({aqi_bucket_label(worst_record_overall['AQI'])}). This shows how bad pollution can get when cold weather traps smoke over the city.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('<div style="margin-top: 24px; border-top: 1px solid #38352f; padding-top: 16px;"></div>', unsafe_allow_html=True)
st.markdown(
    '👉 **Next: What pollutants are in the air?** '
    'Go to the **[Specific Pollutants (Pollutant Breakdown)](Pollutant_Breakdown)** page in the sidebar.'
)


