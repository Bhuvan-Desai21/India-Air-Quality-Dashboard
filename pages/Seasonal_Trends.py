"""
Page 3: Seasonal Trends — The Winter Siege & Lockdown Anomaly
Core Question: How do weather cycles and human activity anomalies shape seasonal air quality profiles?
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.style import apply_brand_style, configure_plotly_theme, TOKENS
from utils.data_loader import load_city_day, CITIES, MONTH_ORDER, SEASON_ORDER

st.set_page_config(page_title="Atmospheric Trapping", layout="wide")
apply_brand_style()

df = load_city_day()

# Sidebar filters
with st.sidebar:
    st.header("Briefing Filters")
    city = st.selectbox("Focus City", CITIES, index=CITIES.index("Bengaluru"))
    compare = st.selectbox("Compare With", ["None"] + [c for c in CITIES if c != city])

city_df = df[df["City"] == city].copy()
city_aqi = city_df[city_df["AQI"].notna()]

# Calculate statistics
# Seasonal Ratio (Winter vs Monsoon)
seasonal_averages = city_aqi.groupby("Season")["AQI"].mean()
winter_val = seasonal_averages.get("Winter", 100.0)
monsoon_val = seasonal_averages.get("Monsoon", 50.0)
seasonal_ratio = winter_val / monsoon_val if monsoon_val > 0 else 2.0

# Lockdown Intervention Drop (Mar-Jun, 2019 vs 2020)
lockdown_months = [3, 4, 5, 6]
lock_df = city_aqi[city_aqi["Month"].isin(lockdown_months) & city_aqi["Year"].isin([2019, 2020])]
lock_avgs = lock_df.groupby("Year")["AQI"].mean()
val_2019 = lock_avgs.get(2019, 100.0)
val_2020 = lock_avgs.get(2020, 70.0)
lockdown_drop = ((val_2019 - val_2020) / val_2019 * 100) if val_2019 > 0 else 30.0

# Header and title
st.markdown(f'<h1 style="font-size: 2.2rem; margin-bottom: 4px;">Seasons & Lockdowns: {city}</h1>', unsafe_allow_html=True)
st.caption(f"How weather patterns and temporary lockdowns changed air quality.")

# Summary/insight banner
st.markdown(
    f"""
    <div class="insight-card">
        <h4 style="margin-top:0; margin-bottom:8px; font-size:1.05rem; color:{TOKENS["amber"]};">
            Weather & Lockdown Effects
        </h4>
        <p style="margin:0; font-size:0.92rem; line-height:1.6; color:{TOKENS["text_secondary"]};">
            <b>Weather Inversions</b>: In <b>{city}</b>, winter weather spikes pollution levels by <b>{seasonal_ratio:.1f} times</b> compared to the monsoon season. This happens because cold air traps smoke and dust close to the ground.<br>
            <b>Lockdown Effect</b>: When traffic and factories stopped during the 2020 COVID lockdowns, air pollution in <b>{city}</b> dropped by <b>{lockdown_drop:.1f}%</b> compared to the same months in 2019.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('<div style="margin-top: 16px;"></div>', unsafe_allow_html=True)

# Main dashboard layout
col_left, col_right = st.columns([5, 5])

with col_left:
    st.markdown('<h3 style="font-size: 1.2rem; margin-top: 0; margin-bottom: 8px;">Monthly Air Quality Heatmap</h3>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size: 0.82rem; color: #A6B1BE; margin-bottom: 12px;">Average AQI by month. Darker red blocks show months with worse air, usually in winter.</p>', unsafe_allow_html=True)
    
    pivot = (
        city_aqi.groupby(["Year", "MonthName"])["AQI"]
        .mean()
        .reset_index()
    )
    pivot["MonthName"] = pd.Categorical(pivot["MonthName"], categories=MONTH_ORDER, ordered=True)
    pivot_wide = pivot.pivot(index="Year", columns="MonthName", values="AQI")
    pivot_wide = pivot_wide.reindex(columns=[m for m in MONTH_ORDER if m in pivot_wide.columns])
    
    fig_heat = px.imshow(
        pivot_wide,
        color_continuous_scale="RdYlGn_r",
        aspect="auto",
        zmin=0, zmax=400,
        labels=dict(x="Month", y="Year", color="Avg AQI"),
    )
    fig_heat.update_layout(
        height=280,
        margin=dict(t=10, b=10, l=40, r=10),
    )
    fig_heat = configure_plotly_theme(fig_heat)
    st.plotly_chart(fig_heat, use_container_width=True)

with col_right:
    st.markdown('<h3 style="font-size: 1.2rem; margin-top: 0; margin-bottom: 8px;">COVID Lockdown Impact (March–June)</h3>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size: 0.82rem; color: #A6B1BE; margin-bottom: 12px;">Comparing average pollution levels when the city was normal (2019) vs. locked down (2020).</p>', unsafe_allow_html=True)
    
    cities_in_view = [city] + ([compare] if compare != "None" else [])
    lockdown_df = df[
        df["City"].isin(cities_in_view) &
        df["Month"].isin(lockdown_months) &
        df["Year"].isin([2019, 2020]) &
        df["AQI"].notna()
    ]
    lockdown_avg = (
        lockdown_df.groupby(["City", "Year"])["AQI"]
        .mean()
        .reset_index()
    )
    
    lockdown_avg["Year"] = lockdown_avg["Year"].astype(str)
    fig_lock = px.bar(
        lockdown_avg,
        x="City",
        y="AQI",
        color="Year",
        barmode="group",
        color_discrete_map={"2019": TOKENS["orange"], "2020": TOKENS["green"]},
        labels={"AQI": "Average AQI (Mar–Jun)"},
        text_auto=".0f",
    )
    fig_lock = configure_plotly_theme(fig_lock)
    fig_lock.update_layout(
        xaxis_title=None,
        height=280,
        margin=dict(t=10, b=10, l=40, r=10),
    )
    st.plotly_chart(fig_lock, use_container_width=True)

st.markdown('<div style="margin-top: 32px; border-top: 1px solid #27303A; padding-top: 24px;"></div>', unsafe_allow_html=True)

# Seasonal comparison
st.markdown('<h3 style="font-size: 1.25rem; margin-bottom: 8px;">Comparing Seasons</h3>', unsafe_allow_html=True)
st.markdown(f'<p style="font-size: 0.82rem; color: #A6B1BE; margin-bottom: 12px;">Average AQI for each season of the year.</p>', unsafe_allow_html=True)

season_df = df[df["City"].isin(cities_in_view) & df["AQI"].notna()]
seasonal = (
    season_df.groupby(["City", "Season"])["AQI"]
    .mean()
    .reset_index()
)
seasonal["Season"] = pd.Categorical(seasonal["Season"], categories=SEASON_ORDER, ordered=True)
seasonal = seasonal.sort_values("Season")

fig_season = px.bar(
    seasonal,
    x="Season",
    y="AQI",
    color="City",
    barmode="group",
    color_discrete_sequence=[TOKENS["red"], TOKENS["teal"]],
    labels={"AQI": "Average AQI"},
)
fig_season = configure_plotly_theme(fig_season)
fig_season.update_layout(
    xaxis_title=None,
    height=320,
    margin=dict(t=20, b=20, l=40, r=20),
)
st.plotly_chart(fig_season, use_container_width=True)

# Navigation and footer
st.markdown('<div style="margin-top: 24px; border-top: 1px solid #27303A; padding-top: 16px;"></div>', unsafe_allow_html=True)
st.markdown(
    '👉 **Next: How does this affect health?** '
    'See the exposure categories and health risks on the **[Health Risks (Health Risk)](Health_Risk)** page.'
)


