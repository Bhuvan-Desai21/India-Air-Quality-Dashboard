"""
India Air Quality Intelligence Platform - National Briefing Landing Hub
"""

import streamlit as st
from utils.style import apply_brand_style, render_timeline_ribbon, render_city_fingerprint, TOKENS
from utils.data_loader import load_city_day

st.set_page_config(
    page_title="India Air Quality Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_brand_style()

# Load data for macro briefings
df = load_city_day()

# Calculate statistics
basin_cities = ["Delhi", "Patna", "Lucknow"]
south_cities = ["Bengaluru", "Chennai", "Visakhapatnam"]
basin_avg = df[df["City"].isin(basin_cities)]["AQI"].mean()
south_avg = df[df["City"].isin(south_cities)]["AQI"].mean()
geo_ratio = basin_avg / south_avg if south_avg > 0 else 2.5

# Header and title
st.markdown('<h1 style="font-size: 2.2rem; margin-bottom: 4px;">India Air Quality Overview</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="briefing-subtitle">'
    'Air quality data from 11 major cities in India between 2015 and 2020.'
    '</p>', 
    unsafe_allow_html=True
)

# Summary/insight banner
st.markdown(
    f"""
    <div class="danger-card">
        <h4 style="margin-top:0; margin-bottom:6px; font-size:1.05rem; color:{TOKENS["red"]};">
            North vs. South Air Quality Gap
        </h4>
        <p style="margin:0; font-size:0.92rem; line-height:1.6; color:{TOKENS["text_secondary"]};">
            Northern cities suffer from much worse air pollution than southern cities. The average Air Quality Index (AQI) in northern landlocked cities is <b>{basin_avg:.0f}</b> (Unhealthy), which is <b>{geo_ratio:.1f} times higher</b> than southern coastal cities, where fresh sea breezes keep the average at <b>{south_avg:.0f}</b> (Good/Moderate).
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Key metrics
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        f"""
        <div class="intel-kpi" style="border: 1px dashed {TOKENS['border']};">
            <span class="intel-kpi-label" style="font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: {TOKENS['text_muted']}; margin-bottom: 2px;">Northern Cities</span>
            <span class="intel-kpi-label">Northern Average</span>
            <span class="intel-kpi-value">{basin_avg:.0f} AQI</span>
            <span class="intel-kpi-status" style="color: {TOKENS['red']};">■ Unhealthy</span>
        </div>
        """,
        unsafe_allow_html=True
    )
with c2:
    st.markdown(
        f"""
        <div class="intel-kpi" style="border: 1px dashed {TOKENS['border']};">
            <span class="intel-kpi-label" style="font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: {TOKENS['text_muted']}; margin-bottom: 2px;">Southern Cities</span>
            <span class="intel-kpi-label">Southern Average</span>
            <span class="intel-kpi-value">{south_avg:.0f} AQI</span>
            <span class="intel-kpi-status" style="color: {TOKENS['teal']};">■ Good / Moderate</span>
        </div>
        """,
        unsafe_allow_html=True
    )
with c3:
    st.markdown(
        f"""
        <div class="intel-kpi" style="border: 1px dashed {TOKENS['border']};">
            <span class="intel-kpi-label" style="font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: {TOKENS['text_muted']}; margin-bottom: 2px;">Comparison</span>
            <span class="intel-kpi-label">Difference</span>
            <span class="intel-kpi-value">{geo_ratio:.1f}x higher</span>
            <span class="intel-kpi-status" style="color: {TOKENS['amber']};">■ Landlocked trap</span>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown('<div style="margin-top: 16px;"></div>', unsafe_allow_html=True)

# Timeline ribbons
st.markdown('<h2 style="font-size: 1.4rem; margin-bottom: 8px;">How Air Quality Looks Across Cities</h2>', unsafe_allow_html=True)
st.markdown(
    '<p style="font-size: 0.85rem; color: #A6B1BE; margin-bottom: 20px;">'
    'Weekly air quality ratings from 2015 to 2020. You can clearly see how northern cities have much longer periods of bad air compared to coastal cities.'
    '</p>',
    unsafe_allow_html=True
)

# Compute city order by clean days %
city_list = sorted(df["City"].unique())
city_clean_pct = {}
for city in city_list:
    city_df = df[df["City"] == city]
    total_days = len(city_df[city_df["AQI_Bucket"].notna()])
    clean_days = len(city_df[city_df["AQI_Bucket"].isin(["Good", "Satisfactory"])])
    pct = (clean_days / total_days * 100) if total_days > 0 else 0
    city_clean_pct[city] = pct

sorted_cities = sorted(city_list, key=lambda c: city_clean_pct[c], reverse=True)

# Render timeline ribbons
for city in sorted_cities:
    city_df = df[df["City"] == city]
    pct = city_clean_pct[city]
    render_timeline_ribbon(
        city_df, 
        label=city, 
        status_pct_label=f"{pct:.1f}% Clean Days",
        group_by="Week"
    )

st.markdown('<div style="margin-top: 32px;"></div>', unsafe_allow_html=True)

# City fingerprints
st.markdown('<h2 style="font-size: 1.4rem; margin-bottom: 16px;">Typical City Profiles</h2>', unsafe_allow_html=True)

f1, f2, f3 = st.columns(3)
with f1:
    st.markdown('<p style="font-size:0.75rem; color:#A6B1BE; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">■ Worst Air Quality</p>', unsafe_allow_html=True)
    patna_df = df[df["City"] == "Patna"]
    patna_avg = patna_df["AQI"].mean()
    patna_pm = patna_df["PM2.5"].mean()
    patna_who = patna_pm / 5.0
    render_city_fingerprint("Patna", patna_avg, "PM2.5", patna_who, city_clean_pct["Patna"])
    
    # Cleanest Regional Record
with f2:
    st.markdown('<p style="font-size:0.75rem; color:#A6B1BE; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">■ India Average</p>', unsafe_allow_html=True)
    national_pm = df["PM2.5"].mean()
    national_who = national_pm / 5.0
    national_clean = len(df[df["AQI_Bucket"].isin(["Good", "Satisfactory"])]) / len(df[df["AQI"].notna()]) * 100
    render_city_fingerprint("India Average", df["AQI"].mean(), "PM2.5", national_who, national_clean)
    
with f3:
    st.markdown('<p style="font-size:0.75rem; color:#A6B1BE; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">■ Best Air Quality</p>', unsafe_allow_html=True)
    blr_df = df[df["City"] == "Bengaluru"]
    blr_avg = blr_df["AQI"].mean()
    blr_pm = blr_df["PM2.5"].mean()
    blr_who = blr_pm / 5.0
    render_city_fingerprint("Bengaluru", blr_avg, "PM2.5", blr_who, city_clean_pct["Bengaluru"])

st.markdown('<div style="margin-top: 32px;"></div>', unsafe_allow_html=True)

# Navigation links
st.markdown('<h2 style="font-size: 1.4rem; margin-bottom: 16px;">Explore More Details</h2>', unsafe_allow_html=True)

nav1, nav2 = st.columns(2)

with nav1:
    st.markdown(
        f"""
        <div class="dashboard-card" style="min-height: 180px; border: 1px dashed {TOKENS['border']};">
            <h4 style="margin-top: 0; margin-bottom: 8px; font-size: 1rem; color: {TOKENS["text_primary"]};">
                1. Air Quality by Location
            </h4>
            <p style="margin: 0; font-size: 0.85rem; line-height: 1.5; color: {TOKENS["text_secondary"]};">
                See where air pollution is worst across the country. Check interactive maps, compare different cities, and see which cities are getting cleaner or dirtier over time.
            </p>
            <div style="margin-top: 16px; font-size: 0.85rem; font-weight: 500;">
                👉 Go to <b>City Overview</b> in the sidebar.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown(
        f"""
        <div class="dashboard-card" style="min-height: 180px; border: 1px dashed {TOKENS['border']};">
            <h4 style="margin-top: 0; margin-bottom: 8px; font-size: 1rem; color: {TOKENS["text_primary"]};">
                2. Seasons and Lockdowns
            </h4>
            <p style="margin: 0; font-size: 0.85rem; line-height: 1.5; color: {TOKENS["text_secondary"]};">
                Find out why air quality gets worse in the winter, and see how much cleaner the air got when traffic and factories stopped during the 2020 COVID lockdowns.
            </p>
            <div style="margin-top: 16px; font-size: 0.85rem; font-weight: 500;">
                👉 Go to <b>Seasonal Trends</b> in the sidebar.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with nav2:
    st.markdown(
        f"""
        <div class="dashboard-card" style="min-height: 180px; border: 1px dashed {TOKENS['border']};">
            <h4 style="margin-top: 0; margin-bottom: 8px; font-size: 1rem; color: {TOKENS["text_primary"]};">
                3. Specific Pollutants
            </h4>
            <p style="margin: 0; font-size: 0.85rem; line-height: 1.5; color: {TOKENS["text_secondary"]};">
                See what pollutants make up the air we breathe. Learn about dust, smoke, gases, and how they compare to global safety limits.
            </p>
            <div style="margin-top: 16px; font-size: 0.85rem; font-weight: 500;">
                👉 Go to <b>Pollutant Breakdown</b> in the sidebar.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="dashboard-card" style="min-height: 180px; border: 1px dashed {TOKENS['border']};">
            <h4 style="margin-top: 0; margin-bottom: 8px; font-size: 1rem; color: {TOKENS["text_primary"]};">
                4. Bangalore Street-Level View
            </h4>
            <p style="margin: 0; font-size: 0.85rem; line-height: 1.5; color: {TOKENS["text_secondary"]};">
                Check air quality in different neighborhoods of Bangalore. Compare busy road junctions and industrial zones to quiet residential streets.
            </p>
            <div style="margin-top: 16px; font-size: 0.85rem; font-weight: 500;">
                👉 Go to <b>Bangalore Deep Dive</b> in the sidebar.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown('<div style="margin-top: 24px; border-top: 1px solid #27303A; padding-top: 16px;"></div>', unsafe_allow_html=True)
st.caption(
    "Data source: Central Pollution Control Board (CPCB) via Kaggle."
)


