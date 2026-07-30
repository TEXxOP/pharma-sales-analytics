"""
Pharma Sales Analytics Dashboard
==================================
Multi-page Streamlit application with 6 analytical views
styled as a consulting-grade deliverable.

Run: streamlit run dashboard/app.py
"""

import sys
from pathlib import Path
from datetime import datetime
from io import BytesIO

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Add project root to path so we can import analytics
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from analytics.queries import DatabaseManager

# ============================================================
# PAGE CONFIG & CUSTOM CSS
# ============================================================

st.set_page_config(
    page_title="Pharma Sales Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Professional custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Custom font */
    html, body {
        font-family: 'Inter', sans-serif;
    }

    /* Main background gradient */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #e6edf3 !important;
    }

    /* KPI Card styling */
    .kpi-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }

    .kpi-card:hover {
        transform: translateY(-4px);
        border-color: rgba(79, 172, 254, 0.3);
        box-shadow: 0 12px 40px rgba(79, 172, 254, 0.15);
    }

    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 8px 0;
    }

    .kpi-label {
        font-size: 0.85rem;
        font-weight: 500;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }

    .kpi-delta {
        font-size: 0.9rem;
        font-weight: 600;
        margin-top: 4px;
    }

    .kpi-delta.positive { color: #3fb950; }
    .kpi-delta.negative { color: #f85149; }

    /* Section headers */
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #e6edf3;
        margin: 32px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid rgba(79, 172, 254, 0.3);
    }

    /* Spotlight card */
    .spotlight-card {
        background: linear-gradient(135deg, rgba(63, 185, 80, 0.1) 0%, rgba(79, 172, 254, 0.1) 100%);
        border: 1px solid rgba(63, 185, 80, 0.2);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
    }

    .spotlight-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #3fb950;
        margin-bottom: 8px;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Dataframe styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: #0d1117;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 8px 24px;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(79, 172, 254, 0.4);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        padding: 8px 16px;
        color: #8b949e;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(79,172,254,0.2), rgba(0,242,254,0.2));
        color: #4facfe !important;
    }

    /* Page title */
    .page-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #e6edf3;
        margin-bottom: 4px;
    }

    .page-subtitle {
        font-size: 0.95rem;
        color: #8b949e;
        margin-bottom: 24px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# PLOTLY THEME
# ============================================================

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#e6edf3"),
    margin=dict(l=40, r=40, t=50, b=40),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(255,255,255,0.1)",
        borderwidth=1,
        font=dict(size=11),
    ),
)

COLOR_PALETTE = ["#4facfe", "#00f2fe", "#43e97b", "#fa709a", "#fee140", "#a18cd1", "#fbc2eb"]
REGION_COLORS = {"North": "#4facfe", "South": "#fa709a", "East": "#43e97b", "West": "#fee140"}
CATEGORY_COLORS = {"Cardiology": "#fa709a", "Oncology": "#4facfe", "Neurology": "#43e97b"}


# ============================================================
# DATABASE CONNECTION (cached)
# ============================================================

@st.cache_resource
def get_db():
    """Create a cached database connection."""
    return DatabaseManager()


def render_kpi_card(label: str, value: str, delta: str = None, delta_positive: bool = True):
    """Render a glassmorphism KPI card."""
    delta_html = ""
    if delta:
        cls = "positive" if delta_positive else "negative"
        icon = "↑" if delta_positive else "↓"
        delta_html = f'<div class="kpi-delta {cls}">{icon} {delta}</div>'

    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:
    st.markdown("## Pharma Sales Analytics")
    st.markdown("---")

    page = st.radio(
        "Navigate",
        [
            "Executive Summary",
            "Territory Performance",
            "Rep Leaderboard",
            "Physician Targeting",
            "Product Analytics",
            "SQL Playground",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        '<p style="color:#8b949e;font-size:0.75rem;">Pharma Sales Analytics Dashboard<br>'
        'Simulating ZS Associates-style consulting deliverable<br><br>'
        f'Last updated: {datetime.now().strftime("%b %d, %Y %H:%M")}</p>',
        unsafe_allow_html=True,
    )

db = get_db()


# ============================================================
# PAGE 1: EXECUTIVE SUMMARY
# ============================================================

if page == "Executive Summary":
    st.markdown('<div class="page-title">Executive Summary</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">High-level KPIs and revenue trends across all territories</div>', unsafe_allow_html=True)

    # KPI Cards
    try:
        kpis = db.get_kpi_summary()
        yoy = db.get_yoy_growth()

        cols = st.columns(4)
        with cols[0]:
            render_kpi_card(
                "Total Revenue",
                f"${kpis.get('total_revenue', 0):,.0f}",
            )
        with cols[1]:
            render_kpi_card(
                "Total Transactions",
                f"{kpis.get('total_transactions', 0):,}",
            )
        with cols[2]:
            render_kpi_card(
                "Avg Deal Size",
                f"${kpis.get('avg_deal_size', 0):,.2f}",
            )
        with cols[3]:
            render_kpi_card(
                "YoY Growth",
                f"{yoy:+.1f}%",
                delta=f"{abs(yoy):.1f}% vs prior year",
                delta_positive=yoy >= 0,
            )

        st.markdown("")

        # Revenue Trend Chart
        col1, col2 = st.columns([3, 2])

        with col1:
            st.markdown('<div class="section-header">Monthly Revenue Trend</div>', unsafe_allow_html=True)
            monthly = db.get_monthly_revenue()
            if not monthly.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=monthly["month"],
                    y=monthly["revenue"],
                    mode="lines+markers",
                    name="Revenue",
                    line=dict(color="#4facfe", width=3),
                    marker=dict(size=6, color="#4facfe"),
                    fill="tozeroy",
                    fillcolor="rgba(79,172,254,0.1)",
                ))
                fig.update_layout(**PLOTLY_LAYOUT, title="", height=400)
                fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
                fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown('<div class="section-header">Revenue by Region</div>', unsafe_allow_html=True)
            region_df = db.get_revenue_by_region()
            if not region_df.empty:
                colors = [REGION_COLORS.get(r, "#4facfe") for r in region_df["region"]]
                fig = go.Figure(go.Bar(
                    x=region_df["region"],
                    y=region_df["revenue"],
                    marker=dict(
                        color=colors,
                        line=dict(width=0),
                        cornerradius=8,
                    ),
                    text=[f"${v:,.0f}" for v in region_df["revenue"]],
                    textposition="outside",
                    textfont=dict(size=11, color="#e6edf3"),
                ))
                fig.update_layout(**PLOTLY_LAYOUT, title="", height=400, showlegend=False)
                fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
                fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
                st.plotly_chart(fig, use_container_width=True)

        # Revenue by Category (monthly stacked)
        st.markdown('<div class="section-header">Revenue by Therapeutic Category</div>', unsafe_allow_html=True)
        cat_df = db.get_monthly_revenue_by_category()
        if not cat_df.empty:
            fig = px.area(
                cat_df, x="month", y="revenue", color="category",
                color_discrete_map=CATEGORY_COLORS,
            )
            fig.update_layout(**PLOTLY_LAYOUT, title="", height=350)
            fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
            fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
            st.plotly_chart(fig, use_container_width=True)

        # PDF Export
        st.markdown("---")
        if st.button("Export Executive Summary to PDF"):
            try:
                from fpdf import FPDF

                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 20)
                pdf.cell(0, 15, "Pharma Sales Analytics - Executive Summary", ln=True, align="C")
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}", ln=True, align="C")
                pdf.ln(10)

                # KPIs
                pdf.set_font("Helvetica", "B", 14)
                pdf.cell(0, 10, "Key Performance Indicators", ln=True)
                pdf.set_font("Helvetica", "", 11)
                pdf.cell(0, 8, f"Total Revenue: ${kpis.get('total_revenue', 0):,.2f}", ln=True)
                pdf.cell(0, 8, f"Total Transactions: {kpis.get('total_transactions', 0):,}", ln=True)
                pdf.cell(0, 8, f"Average Deal Size: ${kpis.get('avg_deal_size', 0):,.2f}", ln=True)
                pdf.cell(0, 8, f"YoY Growth: {yoy:+.1f}%", ln=True)
                pdf.ln(5)

                # Region breakdown
                pdf.set_font("Helvetica", "B", 14)
                pdf.cell(0, 10, "Revenue by Region", ln=True)
                pdf.set_font("Helvetica", "", 11)
                if not region_df.empty:
                    for _, row in region_df.iterrows():
                        pdf.cell(0, 8, f"  {row['region']}: ${row['revenue']:,.2f} ({row['transactions']} transactions)", ln=True)

                pdf_bytes = pdf.output()
                st.download_button(
                    "Download PDF",
                    data=bytes(pdf_bytes),
                    file_name=f"executive_summary_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"PDF generation failed: {e}")

    except Exception as e:
        st.error(f"Failed to load executive summary: {e}")
        st.info("Make sure PostgreSQL is running and data is seeded.")


# ============================================================
# PAGE 2: TERRITORY PERFORMANCE
# ============================================================

elif page == "Territory Performance":
    st.markdown('<div class="page-title">Territory Performance</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Revenue ranking, quota attainment, and quarterly heatmap by territory</div>', unsafe_allow_html=True)

    try:
        # Revenue Analysis Table
        rev_df = db.get_revenue_analysis()
        if not rev_df.empty:
            st.markdown('<div class="section-header">Territory Revenue & YoY Growth</div>', unsafe_allow_html=True)

            # Format for display
            display_df = rev_df.copy()
            display_df["total_revenue"] = display_df["total_revenue"].apply(lambda x: f"${x:,.2f}")
            display_df["prev_year_revenue"] = display_df["prev_year_revenue"].apply(
                lambda x: f"${x:,.2f}" if pd.notna(x) else "—"
            )
            display_df["yoy_growth_pct"] = display_df["yoy_growth_pct"].apply(
                lambda x: f"{x:+.2f}%" if x != 0 else "—"
            )

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "territory_name": "Territory",
                    "region": "Region",
                    "sale_year": "Year",
                    "total_revenue": "Revenue",
                    "total_transactions": "Transactions",
                    "prev_year_revenue": "Prev Year",
                    "yoy_growth_pct": "YoY Growth",
                },
            )

        # Heatmap
        st.markdown('<div class="section-header">Revenue Heatmap (Territory x Quarter)</div>', unsafe_allow_html=True)
        heatmap_df = db.get_territory_quarterly_heatmap()
        if not heatmap_df.empty:
            pivot = heatmap_df.pivot(index="territory", columns="quarter", values="revenue").fillna(0)
            fig = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=pivot.columns.tolist(),
                y=pivot.index.tolist(),
                colorscale=[
                    [0, "#0d1117"],
                    [0.25, "#161b22"],
                    [0.5, "#1a3a5c"],
                    [0.75, "#4facfe"],
                    [1, "#00f2fe"],
                ],
                text=[[f"${v:,.0f}" for v in row] for row in pivot.values],
                texttemplate="%{text}",
                textfont=dict(size=10),
                hovertemplate="Territory: %{y}<br>Quarter: %{x}<br>Revenue: %{text}<extra></extra>",
            ))
            fig.update_layout(**PLOTLY_LAYOUT, title="", height=350)
            st.plotly_chart(fig, use_container_width=True)

        # Gap Analysis
        st.markdown('<div class="section-header">Territories Below 80% Target</div>', unsafe_allow_html=True)
        gap_df = db.get_gap_analysis()
        if not gap_df.empty:
            st.dataframe(
                gap_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "territory_name": "Territory",
                    "region": "Region",
                    "manager": "Manager",
                    "rep_count": "Reps",
                    "territory_quota": st.column_config.NumberColumn("Quota", format="$%,.0f"),
                    "territory_sales": st.column_config.NumberColumn("Sales", format="$%,.0f"),
                    "attainment_pct": st.column_config.NumberColumn("Attainment %", format="%.1f%%"),
                    "revenue_gap": st.column_config.NumberColumn("Gap", format="$%,.0f"),
                    "risk_level": "Risk",
                },
            )
        else:
            st.success("All territories are meeting their 80% target!")

    except Exception as e:
        st.error(f"Failed to load territory data: {e}")


# ============================================================
# PAGE 3: REP LEADERBOARD
# ============================================================

elif page == "Rep Leaderboard":
    st.markdown('<div class="page-title">Rep Leaderboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Sales rep ranking by quota attainment with territory filtering</div>', unsafe_allow_html=True)

    try:
        lb_df = db.get_rep_leaderboard()

        if not lb_df.empty:
            # Territory filter
            territories = ["All"] + sorted(lb_df["territory_name"].unique().tolist())
            selected_territory = st.selectbox("Filter by Territory", territories)

            if selected_territory != "All":
                filtered = lb_df[lb_df["territory_name"] == selected_territory]
            else:
                filtered = lb_df

            # Top Performer Spotlight
            if not filtered.empty:
                top = filtered.iloc[0]
                st.markdown(f"""
                <div class="spotlight-card">
                    <div class="spotlight-title">Top Performer: {top['rep_name']}</div>
                    <div style="color:#e6edf3;font-size:0.95rem;">
                        <strong>Territory:</strong> {top['territory_name']} &nbsp;|&nbsp;
                        <strong>Total Sales:</strong> ${top['total_sales']:,.2f} &nbsp;|&nbsp;
                        <strong>Quota Attainment:</strong> {top['quota_attainment_pct']:.1f}% &nbsp;|&nbsp;
                        <strong>Deals:</strong> {top['total_deals']}  &nbsp;|&nbsp;
                        <strong>Rank:</strong> #{int(top['overall_rank'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Leaderboard table
            st.markdown('<div class="section-header">Full Leaderboard</div>', unsafe_allow_html=True)
            st.dataframe(
                filtered,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "rep_name": "Rep Name",
                    "territory_name": "Territory",
                    "region": "Region",
                    "hire_date": "Hire Date",
                    "total_sales": st.column_config.NumberColumn("Total Sales", format="$%,.0f"),
                    "total_deals": "Deals",
                    "target_quota": st.column_config.NumberColumn("Quota", format="$%,.0f"),
                    "quota_attainment_pct": st.column_config.NumberColumn("Attainment %", format="%.1f%%"),
                    "territory_rank": "Territory Rank",
                    "overall_rank": "Overall Rank",
                    "performance_tier": "Status",
                },
            )

            # Performance distribution chart
            st.markdown('<div class="section-header">Performance Distribution</div>', unsafe_allow_html=True)
            tier_counts = filtered["performance_tier"].value_counts().reset_index()
            tier_counts.columns = ["tier", "count"]
            tier_colors = {
                "Star Performer": "#3fb950",
                "On Target": "#4facfe",
                "Near Target": "#fee140",
                "Below Target": "#f85149",
            }
            fig = go.Figure(go.Bar(
                x=tier_counts["tier"],
                y=tier_counts["count"],
                marker=dict(
                    color=[tier_colors.get(t, "#4facfe") for t in tier_counts["tier"]],
                    cornerradius=8,
                ),
                text=tier_counts["count"],
                textposition="outside",
            ))
            fig.update_layout(**PLOTLY_LAYOUT, title="", height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to load leaderboard: {e}")


# ============================================================
# PAGE 4: PHYSICIAN TARGETING
# ============================================================

elif page == "Physician Targeting":
    st.markdown('<div class="page-title">Physician Targeting</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">ABC segmentation, prescribing patterns, and opportunity scoring</div>', unsafe_allow_html=True)

    try:
        abc_df = db.get_physician_abc()

        if not abc_df.empty:
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                specialties = ["All"] + sorted(abc_df["specialty"].unique().tolist())
                selected_spec = st.selectbox("Filter by Specialty", specialties)
            with col2:
                segments = ["All"] + sorted(abc_df["abc_segment"].unique().tolist())
                selected_seg = st.selectbox("Filter by Segment", segments)

            filtered = abc_df.copy()
            if selected_spec != "All":
                filtered = filtered[filtered["specialty"] == selected_spec]
            if selected_seg != "All":
                filtered = filtered[filtered["abc_segment"] == selected_seg]

            # ABC Segmentation Chart
            col1, col2 = st.columns([1, 2])

            with col1:
                st.markdown('<div class="section-header">ABC Segmentation</div>', unsafe_allow_html=True)
                seg_counts = abc_df["abc_segment"].value_counts().reset_index()
                seg_counts.columns = ["segment", "count"]
                seg_colors = {
                    "A - High Value": "#3fb950",
                    "B - Medium Value": "#4facfe",
                    "C - Low Value": "#fee140",
                }
                fig = go.Figure(go.Pie(
                    labels=seg_counts["segment"],
                    values=seg_counts["count"],
                    hole=0.5,
                    marker=dict(colors=[seg_colors.get(s, "#8b949e") for s in seg_counts["segment"]]),
                    textinfo="label+percent",
                    textfont=dict(size=12, color="#e6edf3"),
                ))
                fig.update_layout(**PLOTLY_LAYOUT, title="", height=350, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown('<div class="section-header">Revenue by Segment</div>', unsafe_allow_html=True)
                seg_rev = abc_df.groupby("abc_segment")["total_value"].sum().reset_index()
                seg_rev.columns = ["segment", "revenue"]
                fig = go.Figure(go.Bar(
                    x=seg_rev["segment"],
                    y=seg_rev["revenue"],
                    marker=dict(
                        color=[seg_colors.get(s, "#4facfe") for s in seg_rev["segment"]],
                        cornerradius=8,
                    ),
                    text=[f"${v:,.0f}" for v in seg_rev["revenue"]],
                    textposition="outside",
                ))
                fig.update_layout(**PLOTLY_LAYOUT, title="", height=350, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            # Top Physicians Table
            st.markdown('<div class="section-header">Top 20 Physicians</div>', unsafe_allow_html=True)
            st.dataframe(
                filtered.head(20),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "physician_name": "Physician",
                    "specialty": "Specialty",
                    "current_tier": "Current Tier",
                    "hospital_affiliation": "Hospital",
                    "territory_name": "Territory",
                    "total_value": st.column_config.NumberColumn("Total Value", format="$%,.0f"),
                    "total_transactions": "Transactions",
                    "avg_deal_size": st.column_config.NumberColumn("Avg Deal", format="$%,.0f"),
                    "products_purchased": "Products",
                    "abc_segment": "Segment",
                },
            )

    except Exception as e:
        st.error(f"Failed to load physician data: {e}")


# ============================================================
# PAGE 5: PRODUCT ANALYTICS
# ============================================================

elif page == "Product Analytics":
    st.markdown('<div class="page-title">Product Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Market share, launch trajectories, and seasonality analysis</div>', unsafe_allow_html=True)

    try:
        # Market Share
        st.markdown('<div class="section-header">Market Share by Category</div>', unsafe_allow_html=True)
        share_df = db.get_product_share()

        if not share_df.empty:
            fig = px.bar(
                share_df,
                x="product_name",
                y="market_share_pct",
                color="category",
                color_discrete_map=CATEGORY_COLORS,
                text="market_share_pct",
                barmode="group",
            )
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_layout(**PLOTLY_LAYOUT, title="", height=400, xaxis_tickangle=-45)
            fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
            fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)", title="Market Share (%)")
            st.plotly_chart(fig, use_container_width=True)

            # Category revenue breakdown
            col1, col2 = st.columns(2)

            with col1:
                st.markdown('<div class="section-header">Revenue Split by Category</div>', unsafe_allow_html=True)
                cat_rev = share_df.groupby("category")["product_revenue"].sum().reset_index()
                fig = go.Figure(go.Pie(
                    labels=cat_rev["category"],
                    values=cat_rev["product_revenue"],
                    hole=0.5,
                    marker=dict(colors=[CATEGORY_COLORS.get(c, "#4facfe") for c in cat_rev["category"]]),
                    textinfo="label+percent",
                    textfont=dict(size=12, color="#e6edf3"),
                ))
                fig.update_layout(**PLOTLY_LAYOUT, title="", height=350, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown('<div class="section-header">Seasonality Pattern</div>', unsafe_allow_html=True)
                season_df = db.get_seasonality()
                if not season_df.empty:
                    fig = go.Figure(go.Scatter(
                        x=season_df["month_name"],
                        y=season_df["avg_daily_revenue"],
                        mode="lines+markers",
                        line=dict(color="#43e97b", width=3),
                        marker=dict(size=10, color="#43e97b"),
                        fill="tozeroy",
                        fillcolor="rgba(67,233,123,0.1)",
                    ))
                    fig.update_layout(**PLOTLY_LAYOUT, title="", height=350)
                    fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
                    fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)", title="Avg Daily Revenue ($)")
                    st.plotly_chart(fig, use_container_width=True)

        # Launch Trajectory
        st.markdown('<div class="section-header">Product Launch Trajectories</div>', unsafe_allow_html=True)
        launch_df = db.get_product_launch_trajectory()
        if not launch_df.empty:
            # Filter to products launched in 2023+
            recent = launch_df[launch_df["launch_date"].astype(str) >= "2023-01-01"]
            if not recent.empty:
                fig = px.line(
                    recent, x="month", y="revenue",
                    color="product_name",
                    color_discrete_sequence=COLOR_PALETTE,
                    markers=True,
                )
                fig.update_layout(**PLOTLY_LAYOUT, title="Products launched 2023+", height=400)
                fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
                fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No products launched in 2023 or later found.")

    except Exception as e:
        st.error(f"Failed to load product data: {e}")


# ============================================================
# PAGE 6: SQL PLAYGROUND
# ============================================================

elif page == "SQL Playground":
    st.markdown('<div class="page-title">SQL Playground</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Write and execute custom SQL queries against the pharma database</div>', unsafe_allow_html=True)

    # Pre-loaded queries
    SQL_FILES = {
        "-- Select a pre-built query --": "",
        "1. Revenue by Territory (YoY Growth)": "01_revenue_analysis.sql",
        "2. Rep Leaderboard (Quota Attainment)": "02_rep_leaderboard.sql",
        "3. Physician ABC Segmentation": "03_physician_abc.sql",
        "4. Product Market Share": "04_product_share.sql",
        "5. Running 3-Month Averages": "05_running_averages.sql",
        "6. Cohort Analysis (Hire Quarter)": "06_cohort_analysis.sql",
        "7. Gap Analysis (Below Target)": "07_gap_analysis.sql",
        "8. Cross-Selling Opportunities": "08_cross_sell.sql",
        "9. Churn Risk Detection": "09_churn_risk.sql",
        "10. Trend & Volatility": "10_trend_volatility.sql",
    }

    selected_query = st.selectbox("Pre-Built Business Questions", list(SQL_FILES.keys()))

    # Load SQL from file if selected
    default_sql = "SELECT * FROM sales LIMIT 10;"
    if SQL_FILES.get(selected_query):
        sql_path = PROJECT_ROOT / "sql" / SQL_FILES[selected_query]
        if sql_path.exists():
            default_sql = sql_path.read_text(encoding="utf-8")

    # SQL editor
    sql_input = st.text_area(
        "Write your SQL query:",
        value=default_sql,
        height=300,
        key="sql_editor",
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        execute = st.button("Execute Query", type="primary")
    with col2:
        st.markdown(
            '<span style="color:#8b949e;font-size:0.8rem;">'
            'Read-only mode: DROP, DELETE, INSERT, UPDATE, ALTER, TRUNCATE are blocked</span>',
            unsafe_allow_html=True,
        )

    if execute and sql_input.strip():
        with st.spinner("Executing query..."):
            try:
                result = db.execute_raw(sql_input)
                st.success(f"Query returned {len(result)} rows")
                st.dataframe(result, use_container_width=True, hide_index=True)

                # Show the SQL for learning
                with st.expander("SQL Query Executed"):
                    st.code(sql_input, language="sql")

            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Query failed: {e}")

    # Schema reference
    with st.expander("Database Schema Reference"):
        st.markdown("""
        **Tables:**
        | Table | Key Columns |
        |-------|-------------|
        | `territories` | territory_id, name, region, manager |
        | `reps` | rep_id, name, territory_id, hire_date, target_quota |
        | `products` | product_id, name, category, price_per_unit, launch_date |
        | `physicians` | physician_id, name, specialty, territory_id, tier, hospital_affiliation |
        | `sales` | sale_id, rep_id, physician_id, product_id, quantity, sale_date, amount |

        **Relationships:**
        - `sales.rep_id` → `reps.rep_id`
        - `sales.physician_id` → `physicians.physician_id`
        - `sales.product_id` → `products.product_id`
        - `reps.territory_id` → `territories.territory_id`
        - `physicians.territory_id` → `territories.territory_id`
        """)
