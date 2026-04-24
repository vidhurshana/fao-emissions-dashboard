# Dashboard: FAO Agrifood GHG Emissions | 5DATA004C Coursework
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Agrifood GHG Emissions Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Metric card style */
    div[data-testid="metric-container"] {
        background-color: #f0f4f8;
        border: 1px solid #d1dbe8;
        border-radius: 10px;
        padding: 12px 16px;
    }

    /* Sidebar header */
    .sidebar-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a3c5e;
        margin-bottom: 4px;
    }

    /* Section header */
    .section-header {
        font-size: 1.15rem;
        font-weight: 600;
        color: #1a3c5e;
        border-left: 4px solid #2e7d32;
        padding-left: 10px;
        margin: 16px 0 8px 0;
    }
</style>
""", unsafe_allow_html=True)


# ─── Data Loading ────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("FAO_EMSTOT.csv")
    # Keep only the columns we need
    df = df[["REF_AREA_LABEL", "TIME_PERIOD", "OBS_VALUE"]].copy()
    df.columns = ["Country", "Year", "Emissions_kt"]
    df["Emissions_Mt"] = df["Emissions_kt"] / 1_000  # convert to megatonnes
    # Remove regional/global aggregates — keep only individual countries
    aggregates = ["World", "South Asia", "North America"]
    df = df[~df["Country"].isin(aggregates)]
    return df


df = load_data()
all_countries = sorted(df["Country"].unique().tolist())
year_min, year_max = int(df["Year"].min()), int(df["Year"].max())

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/d/db/FAO_logo.svg", width=90)
    st.markdown("## 🌱 Dashboard Controls")
    st.markdown("---")

    st.markdown('<p class="sidebar-title">📅 Year Range</p>', unsafe_allow_html=True)
    year_range = st.slider(
        "Select year range",
        min_value=year_min,
        max_value=year_max,
        value=(1990, year_max),
        label_visibility="collapsed",
    )

    st.markdown('<p class="sidebar-title">🌍 Country Selection</p>', unsafe_allow_html=True)
    default_countries = ["China", "United States of America", "India", "Brazil", "Russian Federation"]
    default_valid = [c for c in default_countries if c in all_countries]

    selected_countries = st.multiselect(
        "Choose countries to compare",
        options=all_countries,
        default=default_valid,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown('<p class="sidebar-title">🗺️ Choropleth Year</p>', unsafe_allow_html=True)
    map_year = st.select_slider(
        "Year for world map",
        options=sorted(df["Year"].unique().tolist()),
        value=2021,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("**Data:** FAO Emissions Totals via World Bank Data360  \n**Unit:** Megatonnes CO₂eq (AR5)  \n**Coverage:** 1961–2021, 237 countries")


# ─── Filtered Data ───────────────────────────────────────────────────────────
df_filtered = df[
    (df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])
]

df_country = df_filtered[df_filtered["Country"].isin(selected_countries)] if selected_countries else df_filtered


# ─── Header ──────────────────────────────────────────────────────────────────
st.title("🌱 Agrifood GHG Emissions Dashboard")
st.markdown(
    "Exploring **greenhouse gas emissions from agrifood systems** across 237 countries (1961–2021).  "
    "Data source: [FAO Emissions Totals](https://data360.worldbank.org/en/dataset/FAO_EMSTOT) via World Bank Data360."
)
st.markdown("---")


# ─── KPI Metrics ─────────────────────────────────────────────────────────────
latest_year_data = df[df["Year"] == year_max]
prev_year_data = df[df["Year"] == year_max - 1]

total_latest = latest_year_data["Emissions_Mt"].sum()
total_prev = prev_year_data["Emissions_Mt"].sum()
delta_total = total_latest - total_prev

top_emitter = latest_year_data.loc[latest_year_data["Emissions_Mt"].idxmax(), "Country"]
top_emitter_val = latest_year_data["Emissions_Mt"].max()

earliest_data = df[df["Year"] == year_min]["Emissions_Mt"].sum()
pct_change = ((total_latest - earliest_data) / earliest_data) * 100

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(
        f"🌍 Global Total ({year_max})",
        f"{total_latest:,.0f} Mt",
        delta=f"{delta_total:+,.0f} Mt vs {year_max-1}",
    )
with col2:
    st.metric("🏭 Top Emitter (2021)", top_emitter, f"{top_emitter_val:,.0f} Mt")
with col3:
    st.metric("📊 Countries Covered", f"{df['Country'].nunique()}", "237 nations")
with col4:
    st.metric(
        f"📈 Change Since {year_min}",
        f"{pct_change:+.1f}%",
        f"{total_latest - earliest_data:+,.0f} Mt",
    )

st.markdown("---")


# ─── ROW 1: Line Chart + Top 10 Bar ──────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown('<p class="section-header">Emissions Over Time – Country Comparison</p>', unsafe_allow_html=True)

    if not selected_countries:
        st.info("👈 Select at least one country in the sidebar to see the trend chart.")
    else:
        fig_line = px.line(
            df_country,
            x="Year",
            y="Emissions_Mt",
            color="Country",
            labels={"Emissions_Mt": "GHG Emissions (Mt CO₂eq)", "Year": "Year"},
            template="plotly_white",
        )
        fig_line.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=10, r=10, t=30, b=10),
            height=370,
        )
        fig_line.update_traces(line=dict(width=2.5))
        st.plotly_chart(fig_line, use_container_width=True)

with col_right:
    st.markdown('<p class="section-header">Top 10 Emitters in Selected Range</p>', unsafe_allow_html=True)

    top10 = (
        df_filtered.groupby("Country")["Emissions_Mt"]
        .mean()
        .nlargest(10)
        .reset_index()
        .sort_values("Emissions_Mt")
    )

    fig_bar = px.bar(
        top10,
        x="Emissions_Mt",
        y="Country",
        orientation="h",
        color="Emissions_Mt",
        color_continuous_scale="Reds",
        labels={"Emissions_Mt": "Avg Annual GHG (Mt CO₂eq)", "Country": ""},
        template="plotly_white",
    )
    fig_bar.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=30, b=10),
        height=370,
    )
    st.plotly_chart(fig_bar, use_container_width=True)


# ─── ROW 2: World Map ────────────────────────────────────────────────────────
st.markdown('<p class="section-header">🗺️ Global Emissions Map</p>', unsafe_allow_html=True)

df_map = df[df["Year"] == map_year].copy()
fig_map = px.choropleth(
    df_map,
    locations="Country",
    locationmode="country names",
    color="Emissions_Mt",
    color_continuous_scale="YlOrRd",
    labels={"Emissions_Mt": "GHG (Mt CO₂eq)"},
    title=f"Agrifood GHG Emissions by Country — {map_year}",
    template="plotly_white",
)
fig_map.update_layout(
    geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth"),
    coloraxis_colorbar=dict(title="Mt CO₂eq"),
    margin=dict(l=0, r=0, t=40, b=0),
    height=430,
)
st.plotly_chart(fig_map, use_container_width=True)


# ─── ROW 3: Global Trend + Year-on-Year Change ───────────────────────────────
col3a, col3b = st.columns(2)

with col3a:
    st.markdown('<p class="section-header">📈 Global Emissions Trend</p>', unsafe_allow_html=True)

    global_trend = (
        df_filtered.groupby("Year")["Emissions_Mt"]
        .sum()
        .reset_index()
        .rename(columns={"Emissions_Mt": "Total_Mt"})
    )

    fig_area = px.area(
        global_trend,
        x="Year",
        y="Total_Mt",
        labels={"Total_Mt": "Total GHG (Mt CO₂eq)", "Year": "Year"},
        template="plotly_white",
        color_discrete_sequence=["#2e7d32"],
    )
    fig_area.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
    st.plotly_chart(fig_area, use_container_width=True)

with col3b:
    st.markdown('<p class="section-header">📊 Year-on-Year % Change (Global)</p>', unsafe_allow_html=True)

    global_all = df.groupby("Year")["Emissions_Mt"].sum().reset_index()
    global_all["YoY_pct"] = global_all["Emissions_Mt"].pct_change() * 100
    global_all = global_all[
        (global_all["Year"] >= year_range[0]) & (global_all["Year"] <= year_range[1])
    ]

    colors = ["#c62828" if v > 0 else "#1b5e20" for v in global_all["YoY_pct"].fillna(0)]

    fig_yoy = go.Figure(
        go.Bar(
            x=global_all["Year"],
            y=global_all["YoY_pct"],
            marker_color=colors,
            name="YoY Change (%)",
        )
    )
    fig_yoy.update_layout(
        xaxis_title="Year",
        yaxis_title="% Change",
        template="plotly_white",
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
        showlegend=False,
    )
    fig_yoy.add_hline(y=0, line_dash="dot", line_color="black", opacity=0.5)
    st.plotly_chart(fig_yoy, use_container_width=True)


# ─── ROW 4: Data Table ───────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<p class="section-header">📋 Raw Data Explorer</p>', unsafe_allow_html=True)

with st.expander("Click to expand data table", expanded=False):
    search = st.text_input("🔍 Filter by country name", "")
    display_df = df_filtered.copy()
    if search:
        display_df = display_df[display_df["Country"].str.contains(search, case=False)]

    display_df_show = display_df[["Country", "Year", "Emissions_Mt"]].copy()
    display_df_show["Emissions_Mt"] = display_df_show["Emissions_Mt"].round(2)
    display_df_show.columns = ["Country", "Year", "GHG Emissions (Mt CO₂eq)"]
    st.dataframe(display_df_show.sort_values(["Country", "Year"]), use_container_width=True, height=350)
    st.caption(f"Showing {len(display_df_show):,} rows")


# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Dashboard developed for 5DATA004C Data Science Project Lifecycle · "
    "University of Westminster · Dataset: FAO Emissions Totals (World Bank Data360)"
)
# Dashboard: FAO Agrifood GHG Emissions | 5DATA004C Coursework
import streamlit as st
import pandas as pd
