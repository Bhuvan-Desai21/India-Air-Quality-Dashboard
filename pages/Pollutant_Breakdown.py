"""
Page 2: Pollutants — The Chemical Signature
Core Question: Which pollutants drive risk, and how do they compare against safety standards?
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.style import apply_brand_style, configure_plotly_theme, TOKENS
from utils.data_loader import load_city_day, CITIES, POLLUTANTS

st.set_page_config(page_title="Chemical Signatures", layout="wide")
apply_brand_style()

df = load_city_day()

# WHO annual guideline values (µg/m³, 2021)
WHO_LIMITS = {
    "PM2.5": 5.0,
    "PM10":  15.0,
    "NO2":   10.0,
    "SO2":   None,
    "O3":    60.0,
    "CO":    None,
    "NH3":   None,
}

# CPCB annual standard (µg/m³, India)
CPCB_LIMITS = {
    "PM2.5": 40.0,
    "PM10":  60.0,
    "NO2":   40.0,
    "SO2":   50.0,
    "O3":    None,
    "CO":    None,
    "NH3":   None,
}

UNITS = {p: "µg/m³" for p in POLLUTANTS}
UNITS["CO"] = "mg/m³"

POLLUTANT_EXPLAINERS = {
    "PM2.5": "Tiny particles in the air that are smaller than 2.5 micrometers (about 30 times thinner than a human hair). They come from burning fuel, dust, and smoke. Because they are so small, they can go deep into your lungs and blood, making them very dangerous to your health.",
    "PM10":  "Larger particles like dust, pollen, and mold. They can irritate your eyes, nose, and throat, and make it harder to breathe, especially for people with asthma.",
    "NO2":   "Nitrogen dioxide gas, mostly from car exhaust and power plants. Breathing it in can irritate your lungs, cause coughing, and make it easier to catch chest infections.",
    "SO2":   "Sulfur dioxide gas, created when industries burn coal or oil. It can cause coughing, throat irritation, and trigger asthma attacks.",
    "O3":    "Ground-level ozone, which forms when sunlight reacts with pollution from cars and factories. It is a main ingredient in smog and can harm your lungs.",
    "CO":    "Carbon monoxide gas, which has no smell or color. It comes from burning fuels and prevents your body from carrying oxygen properly, causing headaches or dizziness.",
    "NH3":   "Ammonia gas, mostly from farming and animal waste. It reacts with other gases in the air to create fine dust particles (PM2.5).",
}

# Sidebar filters
with st.sidebar:
    st.header("Briefing Filters")
    pollutant = st.selectbox("Select Agent", POLLUTANTS, index=0)
    selected_cities = st.multiselect(
        "Focus Cities (max 6)", CITIES,
        default=["Delhi", "Bengaluru", "Mumbai", "Chennai", "Kolkata", "Hyderabad"]
    )
    year_range = st.slider("Select Timeline", 2015, 2020, (2015, 2020))

if not selected_cities:
    st.warning("Select at least one city to begin the chemical analysis.")
    st.stop()

# Filter data
filtered = df[
    df["City"].isin(selected_cities) &
    df["Year"].between(year_range[0], year_range[1]) &
    df[pollutant].notna()
]

if filtered.empty:
    st.warning(f"No measurements available for {pollutant} in the selected period.")
    st.stop()

# Calculate statistics
city_avgs = (
    filtered.groupby("City")[pollutant]
    .mean()
    .reset_index()
    .rename(columns={pollutant: "avg"})
    .sort_values("avg", ascending=False)
)

who_limit = WHO_LIMITS.get(pollutant)
cpcb_limit = CPCB_LIMITS.get(pollutant)

mean_val = city_avgs["avg"].mean()
if who_limit:
    avg_exceedance = mean_val / who_limit
    insight_text = f"<b>WHO Safety Limit</b>: On average, the amount of <b>{pollutant}</b> in the air is <b>{avg_exceedance:.1f} times higher</b> than the recommended WHO annual safety limit of <b>{who_limit} {UNITS[pollutant]}</b>."
elif cpcb_limit:
    avg_exceedance = mean_val / cpcb_limit
    insight_text = f"<b>CPCB Safety Standard</b>: On average, the amount of <b>{pollutant}</b> in the air is <b>{avg_exceedance:.1f} times higher</b> than the CPCB annual safety standard of <b>{cpcb_limit} {UNITS[pollutant]}</b>."
else:
    insight_text = f"<b>Average Levels</b>: The average amount of <b>{pollutant}</b> in the air across these cities is <b>{mean_val:.1f} {UNITS[pollutant]}</b> during the selected timeframe."

# Header and title
st.markdown(f'<h1 style="font-size: 2.2rem; margin-bottom: 4px;">Specific Pollutants: {pollutant}</h1>', unsafe_allow_html=True)
st.caption(f"See how much of this pollutant is in the air and how it compares to safety limits.")

# Summary/insight banner
st.markdown(
    f"""
    <div class="insight-card">
        <h4 style="margin-top:0; margin-bottom:8px; font-size:1.05rem; color:{TOKENS["amber"]};">
            Pollutant Exposure Assessment
        </h4>
        <p style="margin:0; font-size:0.92rem; line-height:1.6; color:{TOKENS["text_secondary"]};">
            {insight_text}
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('<div style="margin-top: 16px;"></div>', unsafe_allow_html=True)

# Main dashboard layout
col_left, col_right = st.columns([4, 6])

with col_left:
    limit_briefs = []
    if who_limit:
        limit_briefs.append(f"<li><b>WHO Safety Limit</b>: {who_limit} {UNITS[pollutant]} (Annual)</li>")
    if cpcb_limit:
        limit_briefs.append(f"<li><b>CPCB Safety Limit</b>: {cpcb_limit} {UNITS[pollutant]} (Annual)</li>")
    limit_list_html = "".join(limit_briefs)

    st.markdown(
        f"""
        <div class="dashboard-card" style="border: 1px dashed {TOKENS['border']}; min-height: 340px;">
            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: {TOKENS['text_muted']}; margin-bottom: 4px;">Pollutant Information</div>
            <h4 style="margin-top: 0; margin-bottom: 12px; font-size: 1.1rem; color: {TOKENS["text_primary"]};">
                About {pollutant}
            </h4>
            <p style="font-size: 0.85rem; line-height: 1.5; color: {TOKENS["text_secondary"]}; margin-bottom: 16px;">
                {POLLUTANT_EXPLAINERS.get(pollutant, "Chemical pollutant tracked by air quality sensors.")}
            </p>
            <div style="border-top: 1px dashed {TOKENS['border']}; padding-top: 12px;">
                <span style="font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; color: {TOKENS['text_muted']}; text-transform: uppercase;">Safety Limits</span>
                <ul style="font-size: 0.8rem; color: {TOKENS['text_secondary']}; margin-top: 6px; padding-left: 16px; line-height: 1.4;">
                    {limit_list_html if limit_list_html else "<li>No standard set for this pollutant.</li>"}
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_right:
    # Exceedance multiplier chart
    fig_exceed = go.Figure()
    for _, row in city_avgs.sort_values("avg").iterrows():
        val = row["avg"]
        if who_limit:
            mult = val / who_limit
            x_val = mult
            x_title = f"Times over WHO Limit"
            text_label = f"{mult:.1f}x"
            hovertxt = f"<b>{row['City']}</b><br>Average: {val:.1f} {UNITS[pollutant]} ({mult:.1f}x WHO safety limit)<extra></extra>"
        else:
            x_val = val
            x_title = f"Average Concentration ({UNITS[pollutant]})"
            text_label = f"{val:.1f}"
            hovertxt = f"<b>{row['City']}</b><br>Average: {val:.1f} {UNITS[pollutant]}<extra></extra>"
            
        fig_exceed.add_trace(go.Bar(
            y=[row["City"]],
            x=[x_val],
            orientation="h",
            marker_color=TOKENS["red"] if (who_limit and val > who_limit) else TOKENS["teal"],
            text=text_label,
            textposition="outside",
            showlegend=False,
            hovertemplate=hovertxt,
        ))

    if who_limit:
        fig_exceed.add_vline(
            x=1.0, line_dash="dash", line_color=TOKENS["teal"],
            annotation_text="WHO Safety Limit",
            annotation_position="bottom right",
            annotation_font_color=TOKENS["teal"],
        )
    if cpcb_limit and who_limit:
        cpcb_mult = cpcb_limit / who_limit
        fig_exceed.add_vline(
            x=cpcb_mult, line_dash="dot", line_color=TOKENS["amber"],
            annotation_text=f"CPCB Safety Limit",
            annotation_position="top right",
            annotation_font_color=TOKENS["amber"],
        )

    fig_exceed.update_layout(
        height=340,
        margin=dict(t=20, b=20, l=10, r=60),
        xaxis=dict(title=x_title, range=[0, city_avgs["avg"].max() / (who_limit if who_limit else 1.0) * 1.35]),
        yaxis=dict(title=None),
        bargap=0.3,
    )
    fig_exceed = configure_plotly_theme(fig_exceed)
    st.plotly_chart(fig_exceed, use_container_width=True)

st.markdown('<div style="margin-top: 32px; border-top: 1px solid #38352f; padding-top: 24px;"></div>', unsafe_allow_html=True)

# Detailed comparison tabs
st.markdown('<h3 style="font-size: 1.25rem; margin-bottom: 12px;">Compare Cities</h3>', unsafe_allow_html=True)

tab1, tab2 = st.tabs([
    "■ Daily Spread", 
    "■ Yearly Trends"
])

with tab1:
    fig_box = px.box(
        filtered,
        x="City",
        y=pollutant,
        color="City",
        points=False,
        category_orders={"City": city_avgs["City"].tolist()},
        labels={pollutant: f"{pollutant} ({UNITS[pollutant]})"},
    )
    fig_box = configure_plotly_theme(fig_box)
    fig_box.update_layout(
        showlegend=False,
        xaxis_title=None,
        height=340,
        margin=dict(t=20, b=20, l=40, r=20),
    )
    st.plotly_chart(fig_box, use_container_width=True)

with tab2:
    annual = (
        filtered.groupby(["City", "Year"])[pollutant]
        .mean()
        .reset_index()
        .rename(columns={pollutant: "Value"})
    )
    
    fig_trend = px.line(
        annual, x="Year", y="Value", color="City", markers=True,
        labels={"Value": f"{pollutant} ({UNITS[pollutant]})"},
    )
    if who_limit:
        fig_trend.add_hline(
            y=who_limit, line_dash="dash", line_color=TOKENS["teal"],
            annotation_text=f"WHO Limit",
            annotation_position="top right",
            annotation_font_color=TOKENS["teal"],
        )
    fig_trend = configure_plotly_theme(fig_trend)
    fig_trend.update_layout(
        xaxis=dict(tickmode="linear", dtick=1),
        hovermode="x unified",
        height=340,
        margin=dict(t=20, b=20, l=40, r=20),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# Navigation and footer
st.markdown('<div style="margin-top: 24px; border-top: 1px solid #38352f; padding-top: 16px;"></div>', unsafe_allow_html=True)
st.markdown(
    '👉 **Next: How do seasons and lockdowns affect the air?** '
    'Learn about weather patterns and lockdowns on the **[Seasons & Lockdowns (Seasonal Trends)](Seasonal_Trends)** page.'
)


