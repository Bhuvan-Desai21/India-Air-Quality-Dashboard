"""
Global brand styling and visual design system for the India AQI Intelligence Platform.
Defines color tokens, typography (Space Grotesk, Inter, IBM Plex Mono), global CSS overrides,
and the custom Plotly theme builder.
"""

import streamlit as st
import pandas as pd
import numpy as np

# Design Token Palette
TOKENS = {
    "bg_primary": "#0E1116",
    "bg_surface": "#151A21",
    "bg_elevated": "#1B222C",
    "border": "#27303A",
    "text_primary": "#F4F7FA",
    "text_secondary": "#A6B1BE",
    "text_muted": "#6F7A88",
    "teal": "#4FD1C5",
    "amber": "#F6C445",
    "orange": "#FB8500",
    "red": "#FF6B6B",
    "green": "#4ADE80",
}

# Semantic AQI Colors (CPCB Categories with refined visual palette)
AQI_COLORS = {
    "Good": "#10B981",          # Emerald / Teal
    "Satisfactory": "#34D399",  # Mint Green
    "Moderate": "#F59E0B",      # Amber / Ochre
    "Poor": "#F97316",          # Warm Orange
    "Very Poor": "#EF4444",     # Coral Red
    "Severe": "#8B5CF6",        # Deep Amethyst / Violet
    "Unknown": "#4B5563",       # Slate Gray
}

AQI_DESC = {
    "Good": "Minimal impact, safe for all activities.",
    "Satisfactory": "Minor discomfort for highly sensitive groups.",
    "Moderate": "Respiratory discomfort for children, elderly, and lung/heart patients.",
    "Poor": "Respiratory discomfort for most people on prolonged exposure.",
    "Very Poor": "Respiratory illness on prolonged exposure; health alert.",
    "Severe": "Serious health risk even on brief exposure; toxic alert.",
}

# Global CSS Overrides
GLOBAL_CSS = f"""
<style>
/* Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

/* Base Layout and Backgrounds */
html, body, [data-testid="stAppViewContainer"] {{
    background-color: {TOKENS["bg_primary"]} !important;
    color: {TOKENS["text_primary"]} !important;
    font-family: 'Inter', sans-serif !important;
}}

[data-testid="stHeader"] {{
    background-color: {TOKENS["bg_primary"]} !important;
    border-bottom: 1px solid {TOKENS["border"]} !important;
}}

/* Typography */
h1, h2, h3, h4, h5, h6, [data-testid="stHeadingWithActionElements"] h1, [data-testid="stHeadingWithActionElements"] h2 {{
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    color: {TOKENS["text_primary"]} !important;
    letter-spacing: -0.02em !important;
}}

[data-testid="stSidebar"] {{
    background-color: {TOKENS["bg_surface"]} !important;
    border-right: 1px solid {TOKENS["border"]} !important;
}}

/* Hide standard Streamlit header items for cleaner look */
#MainMenu, footer {{visibility: hidden;}}
[data-testid="stHeader"] {{background: rgba(14, 17, 22, 0.8) !important; backdrop-filter: blur(10px);}}

/* Sidebar Elements Custom Design */
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {{
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.9rem !important;
    color: {TOKENS["text_secondary"]} !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}}

/* Selectbox / Controls Styling */
div[data-baseweb="select"] {{
    background-color: {TOKENS["bg_elevated"]} !important;
    border: 1px solid {TOKENS["border"]} !important;
    border-radius: 6px !important;
}}

div[data-baseweb="select"] div {{
    color: {TOKENS["text_primary"]} !important;
    font-family: 'Inter', sans-serif !important;
}}

div[role="listbox"] {{
    background-color: {TOKENS["bg_elevated"]} !important;
    border: 1px solid {TOKENS["border"]} !important;
}}

/* Custom Scrollbar */
::-webkit-scrollbar {{
    width: 6px;
    height: 6px;
}}
::-webkit-scrollbar-track {{
    background: {TOKENS["bg_primary"]};
}}
::-webkit-scrollbar-thumb {{
    background: {TOKENS["border"]};
    border-radius: 3px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: {TOKENS["text_muted"]};
}}

/* Custom CSS Classes */
.dashboard-card {{
    background-color: {TOKENS["bg_surface"]};
    border: 1px solid {TOKENS["border"]};
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 24px;
}}

.insight-card {{
    background-color: {TOKENS["bg_surface"]};
    border: 1px solid {TOKENS["border"]};
    border-left: 4px solid {TOKENS["amber"]};
    border-radius: 4px 8px 8px 4px;
    padding: 20px;
    margin-bottom: 24px;
}}

.danger-card {{
    background-color: {TOKENS["bg_surface"]};
    border: 1px solid {TOKENS["border"]};
    border-left: 4px solid {TOKENS["red"]};
    border-radius: 4px 8px 8px 4px;
    padding: 20px;
    margin-bottom: 24px;
}}

.teal-card {{
    background-color: {TOKENS["bg_surface"]};
    border: 1px solid {TOKENS["border"]};
    border-left: 4px solid {TOKENS["teal"]};
    border-radius: 4px 8px 8px 4px;
    padding: 20px;
    margin-bottom: 24px;
}}

.briefing-title {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: {TOKENS["text_primary"]};
    margin-bottom: 8px;
    letter-spacing: -0.03em;
}}

.briefing-subtitle {{
    font-family: 'Inter', sans-serif;
    font-size: 1rem;
    color: {TOKENS["text_secondary"]};
    margin-bottom: 24px;
}}

/* Custom Monospace Metric Style */
.intel-kpi {{
    background-color: {TOKENS["bg_elevated"]};
    border: 1px solid {TOKENS["border"]};
    border-radius: 6px;
    padding: 16px 20px;
    margin-bottom: 16px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}}

.intel-kpi-value {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.8rem;
    font-weight: 600;
    color: {TOKENS["text_primary"]};
    line-height: 1.2;
}}

.intel-kpi-label {{
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    color: {TOKENS["text_secondary"]};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}}

.intel-kpi-status {{
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    font-weight: 500;
    margin-top: 4px;
    display: inline-block;
}}

/* AQI Timeline Ribbon Styles */
.ribbon-container {{
    margin-bottom: 16px;
    padding: 12px 16px;
    background-color: #151A21;
    border: 1px dashed #27303A;
    border-radius: 6px;
}}

.ribbon-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}}

.ribbon-label {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    color: #F4F7FA;
}}

.ribbon-stat {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #6F7A88;
}}

.ribbon-bar {{
    display: flex;
    height: 12px;
    border-radius: 3px;
    overflow: hidden;
    background-color: #1a1f26;
}}

.ribbon-block {{
    flex: 1;
    height: 100%;
}}

/* Fingerprint Card Styles */
.fingerprint-card {{
    background-color: #151A21;
    border: 1px dashed #27303A;
    border-radius: 8px;
    padding: 18px;
    margin-bottom: 16px;
    position: relative;
}}

.fingerprint-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px dashed #27303A;
    padding-bottom: 8px;
    margin-bottom: 12px;
}}

.fingerprint-city {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    color: #F4F7FA;
}}

.fingerprint-value {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.1rem;
    font-weight: 600;
}}

.fingerprint-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    margin-bottom: 12px;
}}

.fingerprint-item {{
    display: flex;
    flex-direction: column;
}}

.fingerprint-label {{
    font-size: 0.65rem;
    color: #A6B1BE;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

.fingerprint-data {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: #F4F7FA;
    font-weight: 500;
}}

/* Station Monitor Card Styles */
.station-monitor-card {{
    background-color: #151A21;
    border: 1px dashed #27303A;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}}

.station-monitor-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
}}

.station-monitor-name {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.9rem;
    font-weight: 600;
    color: #F4F7FA;
}}

.station-monitor-badge {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 500;
}}

.station-monitor-details {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: #A6B1BE;
    margin-top: 4px;
}}

/* Custom reference table styles */
.reference-table-container {{
    overflow-x: auto;
    margin-bottom: 24px;
    border: 1px dashed #27303A;
    border-radius: 6px;
}}

.ref-table {{
    width: 100%;
    border-collapse: collapse;
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    color: #F4F7FA;
    background-color: #151A21;
}}

.ref-table th {{
    background-color: #1B222C;
    color: #A6B1BE;
    font-family: 'Space Grotesk', sans-serif;
    text-transform: uppercase;
    font-size: 0.72rem;
    letter-spacing: 0.05em;
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px dashed #27303A;
}}

.ref-table td {{
    padding: 12px 16px;
    border-bottom: 1px dashed #27303A;
    vertical-align: top;
}}

.ref-band-badge {{
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    color: #0E1116;
}}
</style>
"""


def apply_brand_style():
    """Inject the unified design system CSS overrides into the page."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# Custom Plotly Theme Builder
def configure_plotly_theme(fig):
    """
    Format a Plotly figure to fit the premium charcoal technical layout design system.
    """
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=TOKENS["text_secondary"], size=11),
        title=dict(
            font=dict(family="Space Grotesk, sans-serif", size=14, color=TOKENS["text_primary"]),
            x=0,
            y=0.98
        ),
        xaxis=dict(
            gridcolor=TOKENS["border"],
            linecolor=TOKENS["border"],
            zeroline=False,
            tickfont=dict(family="IBM Plex Mono, monospace", size=9)
        ),
        yaxis=dict(
            gridcolor=TOKENS["border"],
            linecolor=TOKENS["border"],
            zeroline=False,
            tickfont=dict(family="IBM Plex Mono, monospace", size=9)
        ),
        legend=dict(
            bgcolor=TOKENS["bg_surface"],
            bordercolor=TOKENS["border"],
            borderwidth=1,
            font=dict(size=10)
        ),
        margin=dict(t=50, b=40, l=45, r=20),
        hoverlabel=dict(
            bgcolor=TOKENS["bg_elevated"],
            bordercolor=TOKENS["border"],
            font=dict(family="IBM Plex Mono, monospace", size=11, color=TOKENS["text_primary"])
        )
    )
    return fig


# Reusable Custom Components in HTML/CSS

def render_kpi(label, value, status=None, status_color=None):
    """
    Render a custom analytical KPI block.
    """
    status_html = ""
    if status:
        color_style = f"color: {status_color};" if status_color else f"color: {TOKENS['text_secondary']};"
        status_html = f'<span class="intel-kpi-status" style="{color_style}">■ {status}</span>'
        
    kpi_html = f"""
    <div class="intel-kpi" style="border: 1px dashed {TOKENS['border']};">
        <span class="intel-kpi-label" style="font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: {TOKENS['text_muted']}; margin-bottom: 2px;">Daily Monitoring</span>
        <span class="intel-kpi-label">{label}</span>
        <span class="intel-kpi-value">{value}</span>
        {status_html}
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)


def generate_timeline_ribbon_html(df, label, status_pct_label="", group_by="Week"):
    """
    Generates HTML string for a high-density timeline ribbon.
    """
    df_valid = df[df["AQI_Bucket"].notna() & (df["AQI_Bucket"] != "Unknown")].copy()
    if df_valid.empty:
        return ""

    if group_by == "Week":
        df_valid["Week"] = df_valid["Date"].dt.isocalendar().week
        grouped = (
            df_valid.groupby(["Year", "Week"])
            .agg(
                aqi_avg=("AQI", "mean"),
                bucket=("AQI_Bucket", lambda x: x.mode()[0] if not x.mode().empty else "Unknown")
            )
            .reset_index()
            .sort_values(["Year", "Week"])
        )
        data_points = grouped["bucket"].tolist()
    else:
        grouped = df_valid.sort_values("Date")
        data_points = grouped["AQI_Bucket"].tolist()
        
    blocks = []
    for bucket in data_points:
        color = AQI_COLORS.get(bucket, TOKENS["text_muted"])
        blocks.append(
            f'<div class="ribbon-block" style="background-color: {color};" title="{bucket}"></div>'
        )
        
    blocks_html = "".join(blocks)
    
    html = f"""
    <div class="ribbon-container">
        <div class="ribbon-header">
            <span class="ribbon-label"><span style="font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; color: {TOKENS['text_muted']}; font-weight: normal; margin-right: 6px;">Weekly Comparison</span>{label}</span>
            <span class="ribbon-stat">{status_pct_label}</span>
        </div>
        <div class="ribbon-bar">
            {blocks_html}
        </div>
    </div>
    """
    return html


def render_timeline_ribbon(df, label, status_pct_label="", group_by="Week"):
    """Render a timeline ribbon component directly in Streamlit."""
    html = generate_timeline_ribbon_html(df, label, status_pct_label, group_by)
    st.markdown(html, unsafe_allow_html=True)


def render_city_fingerprint(city_name, avg_aqi, dominant_pollutant, who_multiplier, healthy_days_pct):
    """
    Render a custom city safety and exposure footprint card.
    """
    def get_bucket(aqi):
        if aqi <= 50: return "Good"
        if aqi <= 100: return "Satisfactory"
        if aqi <= 200: return "Moderate"
        if aqi <= 300: return "Poor"
        if aqi <= 400: return "Very Poor"
        return "Severe"
    
    bucket = get_bucket(avg_aqi)
    color = AQI_COLORS.get(bucket, TOKENS["text_muted"])
    
    html = f"""
    <div class="fingerprint-card">
        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: {TOKENS['text_muted']}; margin-bottom: 4px;">City Profile</div>
        <div class="fingerprint-header">
            <span class="fingerprint-city">{city_name}</span>
            <span class="fingerprint-value" style="color: {color};">{round(avg_aqi)} <span style="font-size: 0.7rem; font-weight: normal; color: {TOKENS['text_secondary']};">AQI</span></span>
        </div>
        <div class="fingerprint-grid">
            <div class="fingerprint-item">
                <span class="fingerprint-label">Main Pollutant</span>
                <span class="fingerprint-data">{dominant_pollutant}</span>
            </div>
            <div class="fingerprint-item">
                <span class="fingerprint-label">WHO Safety Limit</span>
                <span class="fingerprint-data" style="color: {TOKENS['orange']};">{who_multiplier:.1f}x limit</span>
            </div>
            <div class="fingerprint-item">
                <span class="fingerprint-label">Clean Days</span>
                <span class="fingerprint-data" style="color: {TOKENS['teal']};">{healthy_days_pct:.1f}%</span>
            </div>
            <div class="fingerprint-item">
                <span class="fingerprint-label">Health Rating</span>
                <span class="fingerprint-data" style="font-family: sans-serif; font-size: 0.7rem; color: {color};">{bucket}</span>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_station_monitor(station_name, avg_aqi, primary_pollutant, exceedance_days, safety_level):
    """
    Render a telemetry station monitor panel.
    """
    color = AQI_COLORS.get(safety_level, TOKENS["text_muted"])
    bg_style = f"background-color: {color}22; color: {color}; border: 1px dashed {color}44;"
    
    html = f"""
    <div class="station-monitor-card">
        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: {TOKENS['text_muted']}; margin-bottom: 4px;">Neighborhood Monitor</div>
        <div class="station-monitor-header">
            <span class="station-monitor-name">{station_name}</span>
            <span class="station-monitor-badge" style="{bg_style}">{safety_level}</span>
        </div>
        <div class="station-monitor-details">
            Average: {round(avg_aqi)} AQI | Main Pollutant: {primary_pollutant}
        </div>
        <div style="font-size: 0.72rem; color: {TOKENS['text_secondary']}; margin-top: 6px;">
            Polluted air recorded on <b>{exceedance_days}</b> days.
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


