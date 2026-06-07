import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Green Energy Access & Resilience Optimizer",
    page_icon="⚡",
    layout="wide"
)

# --- DB Connection ---
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

@st.cache_data(ttl=3600)
def load_deployment_targets():
    conn = get_connection()
    return pd.read_sql("SELECT * FROM mart_deployment_targets ORDER BY deployment_priority_rank", conn)

@st.cache_data(ttl=3600)
def load_resilience_scores():
    conn = get_connection()
    return pd.read_sql("SELECT * FROM mart_resilience_score ORDER BY country_name, year", conn)

@st.cache_data(ttl=3600)
def load_forecast(country_code=None):
    conn = get_connection()
    if country_code:
        return pd.read_sql(f"""
            SELECT * FROM energy_demand_forecast
            WHERE country_code = '{country_code}'
            ORDER BY forecast_date
        """, conn)
    return pd.read_sql("SELECT * FROM energy_demand_forecast ORDER BY country_code, forecast_date", conn)

@st.cache_data(ttl=3600)
def load_recommendations():
    conn = get_connection()
    return pd.read_sql("SELECT * FROM deployment_recommendations ORDER BY deployment_priority_rank", conn)

@st.cache_data(ttl=3600)
def load_climate():
    conn = get_connection()
    return pd.read_sql("""
        SELECT country_code, country_name, date,
               solar_irradiance_wm2, max_temp_c, precipitation_mm
        FROM raw_climate
        ORDER BY country_code, date
    """, conn)

# --- Country coordinates for map ---
COUNTRY_COORDS = {
    "KE": {"lat": 0.0236,  "lon": 37.9062, "name": "Kenya"},
    "UG": {"lat": 1.3733,  "lon": 32.2903, "name": "Uganda"},
    "TZ": {"lat": -6.3690, "lon": 34.8888, "name": "Tanzania"},
    "ET": {"lat": 9.1450,  "lon": 40.4897, "name": "Ethiopia"},
    "RW": {"lat": -1.9403, "lon": 29.8739, "name": "Rwanda"},
    "SO": {"lat": 5.1521,  "lon": 46.1996, "name": "Somalia"},
}

ISO3_MAP = {
    "KE": "KEN", "UG": "UGA", "TZ": "TZA",
    "ET": "ETH", "RW": "RWA", "SO": "SOM"
}

TIER_COLORS = {
    "CRITICAL": "#d62728",
    "HIGH":     "#ff7f0e",
    "MEDIUM":   "#2ca02c",
    "LOW":      "#1f77b4"
}

# ── Header ──────────────────────────────────────────────────────────
st.markdown("""
    <h1 style='text-align:center; color:#2e8b57;'>
        ⚡ Green Energy Access & Resilience Optimizer
    </h1>
    <p style='text-align:center; color:#666; font-size:16px;'>
        East Africa — Kenya · Uganda · Tanzania · Ethiopia · Rwanda · Somalia
    </p>
    <hr>
""", unsafe_allow_html=True)

# ── Load data ────────────────────────────────────────────────────────
targets         = load_deployment_targets()
resilience      = load_resilience_scores()
recommendations = load_recommendations()
climate         = load_climate()

targets["iso3"] = targets["country_code"].map(ISO3_MAP)
targets["lat"]  = targets["country_code"].map(lambda x: COUNTRY_COORDS[x]["lat"])
targets["lon"]  = targets["country_code"].map(lambda x: COUNTRY_COORDS[x]["lon"])

# ── KPI Row ─────────────────────────────────────────────────────────
st.subheader("📊 Regional Overview")
col1, col2, col3, col4 = st.columns(4)

total_pop       = targets["population"].sum()
avg_access      = resilience[resilience["electricity_access_pct"].notna()]["electricity_access_pct"].mean()
total_displaced = targets["total_displaced"].sum()
critical_count  = len(targets[targets["priority_tier"].isin(["CRITICAL", "HIGH"])])

col1.metric("Total Population Covered",      f"{total_pop/1e6:.1f}M")
col2.metric("Avg Electricity Access",        f"{avg_access:.1f}%" if pd.notna(avg_access) else "N/A")
col3.metric("Total Displaced Persons",       f"{total_displaced/1e6:.2f}M" if pd.notna(total_displaced) else "N/A")
col4.metric("High/Critical Priority Countries", f"{critical_count} / {len(targets)}")

st.markdown("---")

# ── Map + Rankings ───────────────────────────────────────────────────
st.subheader("🗺️ Deployment Priority Map")
col_map, col_rank = st.columns([2, 1])

with col_map:
    fig_map = px.choropleth(
        targets,
        locations="iso3",
        color="resilience_priority_score",
        hover_name="country_name",
        hover_data={
            "electricity_access_pct": ":.1f",
            "priority_tier": True,
            "deployment_priority_rank": True,
            "iso3": False
        },
        color_continuous_scale="RdYlGn_r",
        range_color=[40, 80],
        scope="africa",
        title="Resilience Priority Score (Higher = More Urgent)"
    )
    fig_map.update_layout(
        height=450,
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_colorbar=dict(title="Priority Score")
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col_rank:
    st.markdown("#### 🏆 Deployment Priority Ranking")
    for _, row in targets.iterrows():
        tier  = row["priority_tier"]
        color = TIER_COLORS.get(tier, "#999")
        access_str = f"{row['electricity_access_pct']:.1f}%" if pd.notna(row['electricity_access_pct']) else "N/A"
        st.markdown(f"""
            <div style='background:#f8f9fa; border-left:5px solid {color};
                        padding:10px; margin:6px 0; border-radius:4px;'>
                <b>#{int(row['deployment_priority_rank'])} {row['country_name']}</b>
                <span style='background:{color}; color:white; padding:2px 8px;
                             border-radius:10px; font-size:12px; float:right;'>
                    {tier}
                </span><br>
                <small>Score: {row['resilience_priority_score']} |
                       Access: {access_str}</small>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ── Score Breakdown ──────────────────────────────────────────────────
st.subheader("📈 Resilience Score Components")

score_df = targets[[
    "country_name",
    "energy_vulnerability_score",
    "climate_stress_score",
    "displacement_pressure_score",
    "solar_opportunity_score"
]].melt(id_vars="country_name", var_name="Component", value_name="Score")

score_df["Component"] = (
    score_df["Component"]
    .str.replace("_score", "")
    .str.replace("_", " ")
    .str.title()
)

fig_bar = px.bar(
    score_df,
    x="country_name",
    y="Score",
    color="Component",
    barmode="group",
    color_discrete_sequence=px.colors.qualitative.Set2,
    labels={"country_name": "Country", "Score": "Score (0–100)"},
    title="Score Breakdown by Component"
)
fig_bar.update_layout(height=380, legend_title="Component")
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ── Forecast Section ─────────────────────────────────────────────────
st.subheader("🔮 Energy Demand Forecast (2022–2027)")

selected_countries = st.multiselect(
    "Select countries to compare:",
    options=targets["country_name"].tolist(),
    default=targets["country_name"].tolist()[:3]
)

selected_codes = targets[
    targets["country_name"].isin(selected_countries)
]["country_code"].tolist()

if selected_codes:
    forecast_df = load_forecast()
    forecast_df = forecast_df[forecast_df["country_code"].isin(selected_codes)]
    forecast_df["forecast_date"] = pd.to_datetime(forecast_df["forecast_date"])

    fig_forecast = go.Figure()
    colors = px.colors.qualitative.Set1

    for i, code in enumerate(selected_codes):
        cdf  = forecast_df[forecast_df["country_code"] == code]
        name = cdf["country_name"].iloc[0]
        hist = cdf[cdf["is_historical"] == True]
        fut  = cdf[cdf["is_historical"] == False]
        col  = colors[i % len(colors)]

        fig_forecast.add_trace(go.Scatter(
            x=hist["forecast_date"], y=hist["predicted_demand_index"],
            name=f"{name} (historical)",
            line=dict(color=col, width=1.5),
            mode="lines"
        ))
        fig_forecast.add_trace(go.Scatter(
            x=fut["forecast_date"], y=fut["predicted_demand_index"],
            name=f"{name} (forecast)",
            line=dict(color=col, width=2, dash="dash"),
            mode="lines"
        ))
        fig_forecast.add_trace(go.Scatter(
            x=pd.concat([fut["forecast_date"], fut["forecast_date"][::-1]]),
            y=pd.concat([fut["upper_bound"], fut["lower_bound"][::-1]]),
            fill="toself", fillcolor=col,
            opacity=0.08, line=dict(color="rgba(255,255,255,0)"),
            showlegend=False, name=f"{name} CI"
        ))

    fig_forecast.add_vline(
        x="2026-06-05", line_dash="dot",
        line_color="gray", annotation_text="Today"
    )
    fig_forecast.update_layout(
        height=450,
        title="Energy Demand Index Forecast with 95% Confidence Interval",
        xaxis_title="Date",
        yaxis_title="Demand Index",
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    st.plotly_chart(fig_forecast, use_container_width=True)

st.markdown("---")

# ── Climate Risk Section ─────────────────────────────────────────────
st.subheader("🌡️ Climate Risk Indicators")

climate["date"] = pd.to_datetime(climate["date"])
climate["month"] = climate["date"].dt.to_period("M").dt.to_timestamp()

monthly_avg = climate.groupby(["country_name", "month"]).agg(
    avg_temp=("max_temp_c", "mean"),
    avg_solar=("solar_irradiance_wm2", "mean"),
    total_rain=("precipitation_mm", "sum")
).reset_index()

climate_metric = st.selectbox(
    "Select climate indicator:",
    ["avg_temp", "avg_solar", "total_rain"],
    format_func=lambda x: {
        "avg_temp":   "🌡️ Average Max Temperature (°C)",
        "avg_solar":  "☀️ Solar Irradiance (W/m²)",
        "total_rain": "🌧️ Monthly Precipitation (mm)"
    }[x]
)

fig_climate = px.line(
    monthly_avg,
    x="month",
    y=climate_metric,
    color="country_name",
    title=f"Monthly {climate_metric.replace('_', ' ').title()} by Country",
    labels={"month": "Month", "country_name": "Country"}
)
fig_climate.update_layout(height=380)
st.plotly_chart(fig_climate, use_container_width=True)

st.markdown("---")

# ── Recommendations Table ────────────────────────────────────────────
st.subheader("📋 Deployment Recommendations")

for _, row in recommendations.iterrows():
    tier  = row["priority_tier"]
    color = TIER_COLORS.get(tier, "#999")
    with st.expander(f"#{int(row['deployment_priority_rank'])} {row['country_name']} — {tier}"):
        c1, c2, c3 = st.columns(3)
        c1.metric(
            "Electricity Access",
            f"{row['electricity_access_pct']:.1f}%" if pd.notna(row['electricity_access_pct']) else "N/A"
        )
        c2.metric("Priority Score", f"{row['resilience_priority_score']:.2f}")
        c3.metric(
            "Total Displaced",
            f"{int(row['total_displaced']):,}" if pd.notna(row['total_displaced']) and row['total_displaced'] else "N/A"
        )
        st.info(row["recommendation"])

st.markdown("---")
st.markdown("""
    <p style='text-align:center; color:#aaa; font-size:13px;'>
        Data sources: World Bank API · Open-Meteo API · UNHCR API |
        Built by Kevin Mbugua · github.com/mbuguakevvz
    </p>
""", unsafe_allow_html=True)