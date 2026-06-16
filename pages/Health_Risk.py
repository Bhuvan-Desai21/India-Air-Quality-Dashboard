"""
Page 4: Health Risk — The Human Cost
Core Question: What does this exposure mean for public health and daily life?
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.style import apply_brand_style, configure_plotly_theme, render_timeline_ribbon, TOKENS, AQI_COLORS
from utils.data_loader import load_city_day, AQI_BUCKET_ORDER

st.set_page_config(page_title="Human Cost", layout="wide")
apply_brand_style()

df = load_city_day()

# Sidebar filters
with st.sidebar:
    st.header("Briefing Filters")
    year_range = st.slider("Select Timeline", 2015, 2020, (2015, 2020))

filtered = df[df["Year"].between(year_range[0], year_range[1]) & df["AQI"].notna()]

# Calculate statistics
delhi_df = filtered[filtered["City"] == "Delhi"]
blr_df = filtered[filtered["City"] == "Bengaluru"]

def get_days_over_200(city_data):
    if city_data.empty:
        return 0.0
    days_over = len(city_data[city_data["AQI"] > 200])
    total_measured = len(city_data)
    if total_measured == 0:
        return 0.0
    return (days_over / total_measured) * 365

delhi_days = get_days_over_200(delhi_df)
blr_days = get_days_over_200(blr_df)

# Header and title
st.markdown('<h1 style="font-size: 2.2rem; margin-bottom: 4px;">Air Quality and Health Risks</h1>', unsafe_allow_html=True)
st.caption(f"How daily air pollution affects our health over time.")

# Summary/insight banner
st.markdown(
    f"""
    <div class="insight-card">
        <h4 style="margin-top:0; margin-bottom:8px; font-size:1.05rem; color:{TOKENS["amber"]};">
            Yearly Health Impact
        </h4>
        <p style="margin:0; font-size:0.92rem; line-height:1.6; color:{TOKENS["text_secondary"]};">
            <b>Yearly Health Toll</b>: People in Delhi breathe unhealthy air (AQI over 200) for an average of <b>{delhi_days:.0f} days a year</b>. In comparison, people in Bengaluru only experience this for about <b>{blr_days:.0f} days a year</b>. Breathing bad air for many months is a major health risk.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('<div style="margin-top: 16px;"></div>', unsafe_allow_html=True)

# Main dashboard layout
col_left, col_right = st.columns([4, 6])

with col_left:
    st.markdown('<h3 style="font-size: 1.2rem; margin-top: 0; margin-bottom: 16px;">Weekly Air Quality Over Time</h3>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 0.82rem; color: #A6B1BE; margin-bottom: 16px;">Weekly air quality ratings showing how often key cities have safe vs. unsafe air.</p>', unsafe_allow_html=True)
    
    # Render 3 contrasting city ribbons
    ribbon_cities = ["Delhi", "Mumbai", "Bengaluru"]
    for rc in ribbon_cities:
        if rc in filtered["City"].unique():
            rc_df = filtered[filtered["City"] == rc]
            # Calculate clean percentage
            rc_total = len(rc_df)
            rc_clean = len(rc_df[rc_df["AQI_Bucket"].isin(["Good", "Satisfactory"])])
            rc_pct = (rc_clean / rc_total * 100) if rc_total > 0 else 0
            
            render_timeline_ribbon(
                rc_df,
                label=rc,
                status_pct_label=f"{rc_pct:.1f}% Clean Days",
                group_by="Week"
            )

with col_right:
    st.markdown('<h3 style="font-size: 1.2rem; margin-top: 0; margin-bottom: 8px;">Air Quality Breakdown</h3>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 0.82rem; color: #A6B1BE; margin-bottom: 12px;">Percentage of days spent in each air quality category, from best to worst.</p>', unsafe_allow_html=True)
    
    total = filtered.groupby("City").size().reset_index(name="Total")
    bucket_counts = (
        filtered.groupby(["City", "AQI_Bucket"])
        .size()
        .reset_index(name="Days")
    )
    bucket_counts = bucket_counts.merge(total, on="City")
    bucket_counts["Pct"] = (bucket_counts["Days"] / bucket_counts["Total"] * 100).round(1)
    bucket_counts["AQI_Bucket"] = pd.Categorical(
        bucket_counts["AQI_Bucket"], categories=AQI_BUCKET_ORDER, ordered=True
    )
    
    # Sort cities by unhealthy days (Poor + Very Poor + Severe) descending
    unhealthy_order = (
        filtered[filtered["AQI_Bucket"].isin(["Poor", "Very Poor", "Severe"])]
        .groupby("City").size().reset_index(name="n")
        .sort_values("n", ascending=False)["City"].tolist()
    )
    
    # Include cities that might have 0 unhealthy days at the end
    all_cities = sorted(filtered["City"].unique())
    for c in all_cities:
        if c not in unhealthy_order:
            unhealthy_order.append(c)
            
    fig = px.bar(
        bucket_counts.sort_values("AQI_Bucket"),
        x="Pct",
        y="City",
        color="AQI_Bucket",
        color_discrete_map=AQI_COLORS,
        orientation="h",
        category_orders={"AQI_Bucket": AQI_BUCKET_ORDER, "City": unhealthy_order},
        labels={"Pct": "% of measured days", "AQI_Bucket": "Category", "City": ""},
        barmode="stack",
        hover_data={"Days": True, "Pct": True},
    )
    fig = configure_plotly_theme(fig)
    fig.update_layout(
        xaxis=dict(title="% of measured days", range=[0, 100]),
        legend_title="Category",
        height=320,
        margin=dict(l=10, r=20, t=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div style="margin-top: 32px; border-top: 1px solid #27303A; padding-top: 24px;"></div>', unsafe_allow_html=True)

# AQI reference table
st.markdown('<h3 style="font-size: 1.25rem; margin-bottom: 12px;">Air Quality Safety Guide</h3>', unsafe_allow_html=True)

ref_table_html = f"""
<div class="reference-table-container">
    <table class="ref-table">
        <thead>
            <tr>
                <th>AQI Range</th>
                <th>Category</th>
                <th>Health Effects</th>
                <th>What You Should Do</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><span class="ref-band-badge" style="background-color: {AQI_COLORS['Good']};">0 – 50</span></td>
                <td style="font-weight: 600; color: {AQI_COLORS['Good']};">Good</td>
                <td>Safe air with no health risks.</td>
                <td style="color: {TOKENS['text_secondary']};">Safe to go outside.</td>
            </tr>
            <tr>
                <td><span class="ref-band-badge" style="background-color: {AQI_COLORS['Satisfactory']};">51 – 100</span></td>
                <td style="font-weight: 600; color: {AQI_COLORS['Satisfactory']};">Satisfactory</td>
                <td>Sensitive people may feel slight discomfort.</td>
                <td style="color: {TOKENS['text_secondary']};">Fine for everyone.</td>
            </tr>
            <tr>
                <td><span class="ref-band-badge" style="background-color: {AQI_COLORS['Moderate']};">101 – 200</span></td>
                <td style="font-weight: 600; color: {AQI_COLORS['Moderate']};">Moderate</td>
                <td>People with asthma or heart conditions may feel discomfort.</td>
                <td style="color: {TOKENS['text_secondary']};">Sensitive people should avoid heavy outdoor exercise.</td>
            </tr>
            <tr>
                <td><span class="ref-band-badge" style="background-color: {AQI_COLORS['Poor']};">201 – 300</span></td>
                <td style="font-weight: 600; color: {AQI_COLORS['Poor']};">Poor</td>
                <td>Healthy people will start to feel discomfort; triggers asthma attacks.</td>
                <td style="color: {TOKENS['text_secondary']};">Avoid heavy exercise outside.</td>
            </tr>
            <tr>
                <td><span class="ref-band-badge" style="background-color: {AQI_COLORS['Very Poor']};">301 – 400</span></td>
                <td style="font-weight: 600; color: {AQI_COLORS['Very Poor']};">Very Poor</td>
                <td>Can cause breathing problems for everyone.</td>
                <td style="color: {TOKENS['text_secondary']};">Try to stay indoors; wear a mask if you go outside.</td>
            </tr>
            <tr>
                <td><span class="ref-band-badge" style="background-color: {AQI_COLORS['Severe']};">401 – 500</span></td>
                <td style="font-weight: 600; color: {AQI_COLORS['Severe']};">Severe</td>
                <td>Dangerous air. High risk for everyone even during short exposure.</td>
                <td style="color: {TOKENS['text_secondary']};">Stay indoors and keep windows closed.</td>
            </tr>
        </tbody>
    </table>
</div>
"""
st.markdown(ref_table_html, unsafe_allow_html=True)

# Navigation and footer
st.markdown('<div style="margin-top: 24px; border-top: 1px solid #27303A; padding-top: 16px;"></div>', unsafe_allow_html=True)
st.markdown(
    '👉 **Next: How does air quality differ by neighborhood?** '
    'Check local street-level monitors on the **[Local Neighborhoods (Bangalore Deep Dive)](Bangalore_Deep_Dive)** page.'
)


