"""
DEAL.EVAL v4.0 - Model Studio
Live-updating PE KPIs + committed full-model output.
"""

import hashlib
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Tuple

import streamlit as st
import pandas as pd
import numpy as np

from src.data import FinancialDataIngestion, get_sample_dataframe, HistoricalAnalyzer
from src.models import (
    CapitalStructure, CapitalStructureInputs,
    OperatingModel, OperatingAssumptions,
    DebtModel, DebtAssumptions,
    ExitModel, ExitAssumptions,
    LBOEngine, build_sensitivity_grid, summarize_sensitivity,
)
from src.analysis import (
    check_api_key_available, RiskAnalyzer,
    ICScoring, ScoringInputs, calculate_contribution_analysis,
)
from src.reporting import charts, MemoGenerator, ICReportGenerator, PDFExporter
from src.utils import format_currency, format_percentage, format_multiple

# Page config
st.set_page_config(
    page_title="Deal Eval - Model Studio",
    page_icon="\u2B22",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS — Aesthetic: "Zürich Noir" — Swiss brutalist typography meets commodity desk
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&family=Instrument+Sans:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap');

:root {
    --bg-void: #06080c;
    --bg-surface: #0c1017;
    --bg-elevated: #111720;
    --bg-card: #151c28;
    --accent-gold: #c8a55a;
    --accent-gold-bright: #e4c373;
    --accent-gold-dim: #8b7340;
    --signal-up: #3ecf8e;
    --signal-warn: #d4915e;
    --signal-down: #e05252;
    --text-hero: #f0ece4;
    --text-primary: #d4d0c8;
    --text-muted: #9a9588;
    --text-ghost: #5a554d;
    --border-thin: #1e2530;
    --border-accent: #2a3140;
    --scanline: rgba(200, 165, 90, 0.03);
}

/* ---- Base ---- */
.stApp {
    background: var(--bg-void);
    background-image:
        repeating-linear-gradient(
            0deg,
            transparent,
            transparent 3px,
            var(--scanline) 3px,
            var(--scanline) 4px
        );
    background-attachment: fixed;
}
.main .block-container {
    padding-top: 1.8rem;
    max-width: 1480px;
}

/* ---- Typography ---- */
h1, h2, h3, h4, h5 {
    font-family: 'Playfair Display', Georgia, serif !important;
    color: var(--text-hero) !important;
    letter-spacing: -0.03em;
}
p, label, div {
    font-family: 'Instrument Sans', system-ui, sans-serif;
}
/* Apply Instrument Sans to spans used for text, but protect Material
   Symbols icon spans. Streamlit renders icon glyphs as ligature text
   inside <span data-testid="stIconMaterial"> — overriding their font
   breaks the glyph and leaks raw text like "arr".  We scope the span
   override to known text containers only. */
[data-testid="stMarkdownContainer"] span,
[data-testid="stWidgetLabel"] span,
[data-testid="stMetricValue"] span,
[data-testid="stMetricDelta"] span,
.stSelectbox span,
.stMultiSelect span,
.stRadio span {
    font-family: 'Instrument Sans', system-ui, sans-serif;
}
/* Ensure Material Symbols font on ALL icon spans (expander arrows, etc.) */
[data-testid="stIconMaterial"],
span[class*="material-symbols"],
span[class*="material-icon"] {
    font-family: 'Material Symbols Rounded' !important;
    font-feature-settings: 'liga' !important;
    -webkit-font-feature-settings: 'liga' !important;
    -webkit-font-smoothing: antialiased !important;
    font-weight: normal !important;
    font-style: normal !important;
    text-rendering: optimizeLegibility !important;
}

.main-header {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 2.6rem;
    font-weight: 900;
    color: var(--accent-gold-bright);
    letter-spacing: -0.04em;
    line-height: 1.0;
    margin-bottom: 0;
    text-transform: none;
    position: relative;
}
.main-header::after {
    content: '';
    display: block;
    width: 60px;
    height: 2px;
    background: var(--accent-gold);
    margin-top: 0.6rem;
}
.sub-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--text-muted);
    font-weight: 400;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-top: 0.5rem;
    margin-bottom: 2.2rem;
}

.section-header {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.35rem;
    font-weight: 700;
    font-style: italic;
    color: var(--accent-gold);
    margin-top: 2.8rem;
    margin-bottom: 1rem;
    padding-left: 0;
    border-left: none;
    text-transform: none;
    letter-spacing: -0.01em;
    position: relative;
    padding-bottom: 0.5rem;
}
.section-header::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, var(--accent-gold-dim) 0%, transparent 70%);
}

.terminal-text {
    font-family: 'IBM Plex Mono', monospace;
    color: var(--accent-gold-dim);
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

/* ---- Metrics ---- */
[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.6rem !important;
    font-weight: 600 !important;
    color: var(--text-hero) !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.68rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: var(--text-primary) !important;
}
[data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid var(--border-thin);
    border-radius: 2px;
    padding: 1rem;
    transition: border-color 0.2s ease;
}
[data-testid="stMetric"]:hover {
    border-color: var(--accent-gold-dim);
}

/* ---- Buttons ---- */
.stButton > button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    background: var(--accent-gold);
    color: var(--bg-void);
    border: none;
    border-radius: 1px;
    padding: 0.7rem 2.2rem;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    background: var(--accent-gold-bright);
    transform: none;
    box-shadow: 0 0 20px rgba(200, 165, 90, 0.2);
}
.stButton > button:active {
    background: var(--accent-gold-dim);
}

/* ---- DataFrames ---- */
[data-testid="stDataFrame"] {
    font-family: 'IBM Plex Mono', monospace;
    background: var(--bg-surface);
    border: 1px solid var(--border-thin);
    border-radius: 2px;
}

/* ---- Expanders ---- */
[data-testid="stExpander"] {
    border: 1px solid var(--border-thin) !important;
    border-radius: 2px !important;
    background: var(--bg-surface) !important;
}

/* ---- Sliders ---- */
[data-testid="stSlider"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
    color: var(--text-primary) !important;
}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {
    background: var(--bg-surface) !important;
    border-right: 1px solid var(--border-thin) !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
    color: var(--text-primary) !important;
}
[data-testid="stSidebar"] .terminal-text {
    color: var(--accent-gold) !important;
}
[data-testid="stSidebar"] summary p {
    color: var(--text-primary) !important;
}

/* ---- KPI Cards ---- */
.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border-thin);
    border-radius: 2px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.5rem;
    transition: border-color 0.2s ease;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 3px;
    height: 100%;
    background: var(--border-accent);
    transition: background 0.2s ease;
}
.kpi-card:hover {
    border-color: var(--border-accent);
}
.kpi-card:hover::before {
    background: var(--accent-gold-dim);
}

.kpi-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: var(--text-primary);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.15rem;
    font-weight: 500;
}
.kpi-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.7rem;
    font-weight: 700;
    line-height: 1.15;
    letter-spacing: -0.02em;
}
.kpi-value-sm {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.25rem;
    font-weight: 600;
    line-height: 1.15;
    letter-spacing: -0.01em;
}

.kpi-green  { color: #3ecf8e; }
.kpi-amber  { color: #d4915e; }
.kpi-red    { color: #e05252; }
.kpi-cyan   { color: var(--text-hero); }

.kpi-panel-header {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.05rem;
    font-weight: 700;
    font-style: italic;
    color: var(--accent-gold);
    margin-bottom: 0.9rem;
    text-transform: none;
    letter-spacing: -0.01em;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid var(--border-thin);
}

/* ---- Horizontal rules ---- */
hr {
    border-color: var(--border-thin) !important;
    opacity: 0.5;
}

/* ---- Number inputs ---- */
[data-testid="stNumberInput"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
    color: var(--text-primary) !important;
}

/* ---- File uploader ---- */
[data-testid="stFileUploader"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    color: var(--text-primary) !important;
}

/* ---- Checkbox ---- */
[data-testid="stCheckbox"] label span {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
    color: var(--text-primary) !important;
}

/* ---- Radio ---- */
[data-testid="stRadio"] label {
    color: var(--text-primary) !important;
}

/* ---- Expander summary text ---- */
[data-testid="stExpander"] summary p {
    color: var(--text-primary) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
}

/* ---- Tab ---- */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid var(--border-thin);
}
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: var(--text-primary) !important;
    border-radius: 0 !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent-gold) !important;
    border-bottom: 2px solid var(--accent-gold) !important;
}

/* ---- Sticky KPI panel ---- */
/* Make the Streamlit column containing .live-kpi-sticky stick while scrolling */
[data-testid="stColumn"]:has(.live-kpi-sticky) {
    position: sticky;
    top: 1rem;
    align-self: flex-start;
    z-index: 50;
}
/* Inner wrapper just groups title + grid — no sticky here */
.live-kpi-sticky {
    background: var(--bg-void);
    padding-bottom: 0.5rem;
}
.live-kpi-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
}

/* ---- Sticky committed results banner ---- */
.results-sticky-banner {
    position: sticky;
    top: 0;
    z-index: 60;
    background: var(--bg-void);
    padding: 0.5rem 0 0.6rem 0;
    border-bottom: 1px solid var(--border-thin);
}
.results-kpi-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.6rem;
}
.results-kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border-thin);
    border-radius: 2px;
    padding: 0.8rem 1rem;
}
.results-kpi-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-primary);
    margin-bottom: 0.3rem;
}
.results-kpi-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--text-hero);
}

/* ---- General label brightness fix ---- */
[data-testid="stWidgetLabel"] label,
[data-testid="stWidgetLabel"] p,
.stSelectbox label,
.stMultiSelect label,
.stTextInput label,
.stTextArea label {
    color: var(--text-primary) !important;
}

/* ---- Markdown h5 (section sub-headers like "Capital Structure") ---- */
.main h5 {
    color: var(--accent-gold-bright) !important;
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.8rem !important;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# PURE HELPERS
# ---------------------------------------------------------------------------

def _build_assumptions(
    entry_ebitda, entry_multiple, debt_to_ebitda,
    transaction_fee_pct, financing_fee_pct, cash_on_bs,
    base_revenue, revenue_growth, hold_period,
    ebitda_margin, tax_rate, da_pct,
    capex_pct, nwc_pct,
    interest_rate, amortization_pct,
    cash_sweep_enabled, cash_sweep_pct,
    exit_mode, fixed_exit_multiple,
    industry_multiple, growth_multiple_factor,
):
    """Pure helper: build dataclass inputs from UI scalars."""
    capital = CapitalStructureInputs(
        entry_ebitda=entry_ebitda, entry_multiple=entry_multiple,
        debt_to_ebitda=debt_to_ebitda, transaction_fee_pct=transaction_fee_pct,
        financing_fee_pct=financing_fee_pct, cash_on_bs=cash_on_bs,
    )
    operating = OperatingAssumptions(
        base_revenue=base_revenue,
        revenue_growth_rates=[revenue_growth] * hold_period,
        ebitda_margin=ebitda_margin, tax_rate=tax_rate,
        da_pct_revenue=da_pct, capex_pct_revenue=capex_pct,
        nwc_pct_revenue=nwc_pct,
    )
    debt = DebtAssumptions(
        initial_debt=0.0,
        interest_rate=interest_rate, amortization_pct=amortization_pct,
        cash_sweep_enabled=cash_sweep_enabled, cash_sweep_pct=cash_sweep_pct,
    )
    exit_a = ExitAssumptions(
        exit_mode=exit_mode, fixed_exit_multiple=fixed_exit_multiple,
        entry_multiple=entry_multiple, industry_multiple=industry_multiple,
        hold_period=hold_period, growth_multiple_factor=growth_multiple_factor,
    )
    return capital, operating, debt, exit_a


def _run_engine(cap, ops, dbt, ext):
    """Pure helper: instantiate LBOEngine and return results dict."""
    return LBOEngine(cap, ops, dbt, ext).get_results()


def _extract_live_kpis(results):
    """Extract the compact set of KPIs we show live."""
    risk = results.get("risk_flags", {})
    su = results["sources_uses"]
    initial_debt = su["debt"]
    final_debt = results["exit_results"]["exit_debt"]
    debt_paydown_pct = (initial_debt - final_debt) / initial_debt if initial_debt > 0 else 0.0

    op = results.get("operating_projection")
    if op is not None and len(op) >= 2:
        ebitda_cagr = (op["ebitda"].iloc[-1] / op["ebitda"].iloc[0]) ** (1 / len(op)) - 1
    else:
        ebitda_cagr = 0.0

    return {
        "irr": results.get("irr"),
        "moic": results.get("moic", 0),
        "exit_equity_value": results.get("exit_equity_value", 0),
        "entry_ev": su["enterprise_value"],
        "max_debt_to_ebitda": risk.get("max_debt_to_ebitda", 0),
        "min_interest_coverage": risk.get("min_interest_coverage", 0),
        "debt_paydown_pct": debt_paydown_pct,
        "ebitda_cagr": ebitda_cagr,
    }


def _input_hash(**kw):
    """Deterministic hash of all model inputs."""
    return hashlib.md5(json.dumps(kw, sort_keys=True, default=str).encode()).hexdigest()


def _kpi_color(value, thresholds, invert=False):
    """Return CSS class suffix: green / amber / red."""
    lo, hi = thresholds
    if invert:
        return "green" if value <= hi else ("amber" if value <= lo else "red")
    else:
        return "green" if value >= hi else ("amber" if value >= lo else "red")


def _kpi_html(label, value_str, css_class="kpi-cyan", small=False):
    """Render one KPI card as HTML."""
    vcls = "kpi-value-sm" if small else "kpi-value"
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="{vcls} {css_class}">{value_str}</div>'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------
for k, v in {
    "data_uploaded": False,
    "historical_data": None,
    "historical_summary": None,
    "uploaded_filename": None,
    "live_results": None,
    "live_kpis": None,
    "last_input_hash": None,
    "committed_results": None,
    "committed_timestamp": None,
    "model_results": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

api_available = check_api_key_available()


# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="main-header">Deal.Eval</div>'
    '<div class="sub-header">'
    'Ingest &middot; Configure &middot; Model &middot; Synthesize'
    '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
st.sidebar.markdown(
    '<div class="terminal-text" style="font-size:0.82rem;margin-bottom:1.2rem;">'
    'Deal Configuration</div>',
    unsafe_allow_html=True,
)
company_name = st.sidebar.text_input("Company Name", value="Target Co.")
industry = st.sidebar.text_input("Industry", value="Business Services")
st.sidebar.markdown("---")

with st.sidebar.expander("Business Information", expanded=False):
    st.markdown("**Qualitative Inputs for IC Report**")
    business_description = st.text_area(
        "Business Description", placeholder="Brief description...", height=100,
    )
    investment_thesis = st.text_area(
        "Investment Thesis", placeholder="Key value creation drivers...", height=100,
    )
    key_risks = st.text_area(
        "Key Risks", placeholder="Market risks, execution risks...", height=100,
    )
    management_notes = st.text_area(
        "Management Assessment", placeholder="Management quality...", height=80,
    )
st.sidebar.markdown("---")


# ===========================================================================
# SECTION 1: DATA INGESTION
# ===========================================================================
st.markdown(
    '<p class="section-header">Historical Financials</p>',
    unsafe_allow_html=True,
)

col_up, col_sample = st.columns([2, 1])
with col_up:
    uploaded_file = st.file_uploader(
        "Upload CSV with historical financials",
        type=["csv"],
        help="CSV with columns: year, revenue, ebitda",
        key="csv_uploader",
    )
with col_sample:
    if st.button("LOAD SAMPLE", width="stretch"):
        st.session_state.historical_data = get_sample_dataframe()
        st.session_state.data_uploaded = True
        st.session_state.uploaded_filename = "__sample__"
        st.session_state.committed_results = None
        st.session_state.committed_timestamp = None
        st.session_state.live_results = None
        st.session_state.live_kpis = None
        st.session_state.last_input_hash = None
        st.rerun()

# Process uploaded CSV
if uploaded_file is not None and uploaded_file.name:
    already = (
        st.session_state.get("uploaded_filename") == uploaded_file.name
        and st.session_state.data_uploaded
    )
    if not already:
        try:
            ingestion = FinancialDataIngestion()
            with st.spinner("Processing CSV..."):
                cleaned, warnings = ingestion.ingest_csv(uploaded_file)
            if cleaned is not None and len(cleaned) > 0:
                st.session_state.historical_data = cleaned
                st.session_state.data_uploaded = True
                st.session_state.uploaded_filename = uploaded_file.name
                st.session_state.committed_results = None
                st.session_state.committed_timestamp = None
                st.session_state.live_results = None
                st.session_state.live_kpis = None
                st.session_state.last_input_hash = None
                st.success(f"Data ingestion complete - {len(cleaned)} years loaded")
                if warnings:
                    st.warning("**Warnings:**\n" + "\n".join(f"- {w}" for w in warnings))
                st.rerun()
            else:
                st.error("Validation failed")
                if warnings:
                    st.error("\n".join(f"- {w}" for w in warnings))
                st.info("Required columns: year, revenue, ebitda")
                st.session_state.data_uploaded = False
                st.session_state.historical_data = None
        except Exception as e:
            st.error(f"Error: {e}")
            st.session_state.data_uploaded = False
            st.session_state.historical_data = None

# Show historical data + metrics
if st.session_state.data_uploaded and st.session_state.historical_data is not None:
    df_hist = st.session_state.historical_data

    st.markdown(
        '<div class="terminal-text" style="margin-top:1rem;'
        'margin-bottom:0.4rem;">Historical Data</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(df_hist, width="stretch")

    analyzer = HistoricalAnalyzer(df_hist)
    st.session_state.historical_summary = analyzer.get_full_summary()
    summary = st.session_state.historical_summary

    st.markdown(
        '<div class="terminal-text" style="margin-top:1.5rem;'
        'margin-bottom:0.5rem;">Performance Metrics</div>',
        unsafe_allow_html=True,
    )
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Revenue CAGR", format_percentage(summary.get("revenue_cagr", 0)))
    with m2:
        st.metric("EBITDA CAGR", format_percentage(summary.get("ebitda_cagr", 0)))
    with m3:
        avg_margin = summary.get("avg_margin", 0)
        st.metric("Avg EBITDA Margin", f"{avg_margin:.1f}%")
    with m4:
        st.metric("Latest EBITDA", format_currency(df_hist["ebitda"].iloc[-1]))


# ===========================================================================
# SECTION 2: MODEL STUDIO (inputs left, live KPIs right)
# ===========================================================================
if st.session_state.data_uploaded:
    st.markdown(
        '<p class="section-header">Model Studio</p>',
        unsafe_allow_html=True,
    )

    col_inputs, col_kpis = st.columns([3, 2], gap="large")

    # -- LEFT: all inputs --------------------------------------------------
    with col_inputs:

        # Capital Structure
        st.markdown("##### Capital Structure")
        c1, c2, c3 = st.columns(3)
        with c1:
            entry_ebitda = st.number_input(
                "Entry EBITDA (M)",
                min_value=1.0,
                value=float(st.session_state.historical_data["ebitda"].iloc[-1]),
                step=1.0,
            )
            entry_multiple = st.number_input(
                "Entry Multiple (x)", min_value=1.0, max_value=25.0, value=10.0, step=0.5,
            )
        with c2:
            debt_to_ebitda = st.number_input(
                "Debt / EBITDA (x)", min_value=0.0, max_value=10.0, value=5.0, step=0.5,
            )
            cash_on_bs = st.number_input(
                "Cash on BS (M)", min_value=0.0, value=0.0, step=1.0,
            )
        with c3:
            transaction_fee_pct = st.slider(
                "Transaction Fees (% EV)", 0.0, 5.0, 2.0, 0.5,
            ) / 100
            financing_fee_pct = st.slider(
                "Financing Fees (% Debt)", 0.0, 5.0, 3.0, 0.5,
            ) / 100

        st.markdown("---")

        # Operating Assumptions
        st.markdown("##### Operating Assumptions")
        o1, o2 = st.columns(2)
        with o1:
            hold_period = st.slider("Hold Period (Years)", 3, 7, 5)
            revenue_growth = st.slider("Revenue Growth (%/yr)", -5.0, 20.0, 5.0, 0.5) / 100
            ebitda_margin = st.slider("EBITDA Margin (% Rev)", 5.0, 50.0, 20.0, 1.0) / 100
            tax_rate = st.slider("Tax Rate (%)", 0.0, 40.0, 25.0, 1.0) / 100
        with o2:
            da_pct = st.slider("D&A (% Rev)", 0.0, 10.0, 3.0, 0.5) / 100
            capex_pct = st.slider("Capex (% Rev)", 0.0, 15.0, 3.0, 0.5) / 100
            nwc_pct = st.slider("NWC (% Rev)", 0.0, 30.0, 10.0, 1.0) / 100

        st.markdown("---")

        # Debt Structure
        st.markdown("##### Debt Structure")
        d1, d2 = st.columns(2)
        with d1:
            interest_rate = st.slider("Interest Rate (%)", 0.0, 15.0, 6.0, 0.5) / 100
            amortization_pct = st.slider(
                "Annual Amort (% Init Debt)", 0.0, 20.0, 5.0, 1.0,
            ) / 100
        with d2:
            cash_sweep_enabled = st.checkbox("Enable Cash Sweep", value=True)
            cash_sweep_pct = (
                st.slider(
                    "Cash Sweep (% FCF)", 0.0, 100.0, 50.0, 10.0,
                    disabled=not cash_sweep_enabled,
                ) / 100
                if cash_sweep_enabled
                else 0.0
            )

        st.markdown("---")

        # Exit Assumptions
        st.markdown("##### Exit Assumptions")
        exit_mode = st.radio(
            "Exit Valuation Method",
            options=["fixed", "mean_reversion", "growth_adjusted"],
            format_func=lambda x: {
                "fixed": "Fixed Multiple",
                "mean_reversion": "Mean Reversion",
                "growth_adjusted": "Growth-Adjusted",
            }[x],
        )
        e1, e2, e3 = st.columns(3)
        with e1:
            fixed_exit_multiple = (
                st.number_input("Exit Multiple (x)", 1.0, 25.0, 10.0, 0.5)
                if exit_mode == "fixed"
                else entry_multiple
            )
        with e2:
            industry_multiple = (
                st.number_input("Industry Multiple (x)", 1.0, 25.0, 12.0, 0.5)
                if exit_mode == "mean_reversion"
                else entry_multiple
            )
        with e3:
            growth_multiple_factor = (
                st.slider("Growth Sensitivity", 0.0, 2.0, 0.5, 0.1)
                if exit_mode == "growth_adjusted"
                else 0.5
            )

    # -- LIVE ENGINE RUN ----------------------------------------------------
    base_revenue = float(st.session_state.historical_data["revenue"].iloc[-1])

    current_hash = _input_hash(
        entry_ebitda=entry_ebitda, entry_multiple=entry_multiple,
        debt_to_ebitda=debt_to_ebitda, cash_on_bs=cash_on_bs,
        transaction_fee_pct=transaction_fee_pct,
        financing_fee_pct=financing_fee_pct,
        base_revenue=base_revenue, revenue_growth=revenue_growth,
        hold_period=hold_period, ebitda_margin=ebitda_margin,
        tax_rate=tax_rate, da_pct=da_pct,
        capex_pct=capex_pct, nwc_pct=nwc_pct,
        interest_rate=interest_rate, amortization_pct=amortization_pct,
        cash_sweep_enabled=cash_sweep_enabled, cash_sweep_pct=cash_sweep_pct,
        exit_mode=exit_mode, fixed_exit_multiple=fixed_exit_multiple,
        industry_multiple=industry_multiple,
        growth_multiple_factor=growth_multiple_factor,
    )

    live_error = None
    if current_hash != st.session_state.last_input_hash:
        try:
            cap, ops, dbt, ext = _build_assumptions(
                entry_ebitda=entry_ebitda, entry_multiple=entry_multiple,
                debt_to_ebitda=debt_to_ebitda,
                transaction_fee_pct=transaction_fee_pct,
                financing_fee_pct=financing_fee_pct, cash_on_bs=cash_on_bs,
                base_revenue=base_revenue, revenue_growth=revenue_growth,
                hold_period=hold_period, ebitda_margin=ebitda_margin,
                tax_rate=tax_rate, da_pct=da_pct,
                capex_pct=capex_pct, nwc_pct=nwc_pct,
                interest_rate=interest_rate, amortization_pct=amortization_pct,
                cash_sweep_enabled=cash_sweep_enabled,
                cash_sweep_pct=cash_sweep_pct,
                exit_mode=exit_mode,
                fixed_exit_multiple=fixed_exit_multiple,
                industry_multiple=industry_multiple,
                growth_multiple_factor=growth_multiple_factor,
            )
            live_res = _run_engine(cap, ops, dbt, ext)
            st.session_state.live_results = live_res
            st.session_state.live_kpis = _extract_live_kpis(live_res)
            st.session_state.last_input_hash = current_hash
        except Exception as exc:
            live_error = str(exc)
            st.session_state.live_results = None
            st.session_state.live_kpis = None

    # -- RIGHT: Live KPI panel ----------------------------------------------
    with col_kpis:
        if live_error:
            st.error(f"Engine error: {live_error}")

        kpis = st.session_state.live_kpis
        if kpis is None:
            st.markdown(
                '<div class="live-kpi-sticky">'
                '<div class="kpi-panel-header">Live Preview</div>'
                '<p style="color:var(--text-primary);font-size:0.85rem;">Adjust inputs to see live KPI preview.</p>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            # Compute values
            irr_val = kpis["irr"]
            if irr_val is not None:
                irr_color = _kpi_color(irr_val * 100, (15, 20))
                irr_str = f"{irr_val * 100:.1f}%"
            else:
                irr_color = "red"
                irr_str = "N/A"
            moic_val = kpis["moic"]
            moic_color = _kpi_color(moic_val, (1.5, 2.0))
            max_lev = kpis["max_debt_to_ebitda"]
            lev_color = _kpi_color(max_lev, (6.0, 5.0), invert=True)
            min_cov = kpis["min_interest_coverage"]
            cov_color = _kpi_color(min_cov, (1.5, 2.0))

            # Render entire panel as one HTML block so sticky works
            st.markdown(
                '<div class="live-kpi-sticky">'
                '<div class="kpi-panel-header">Live Preview</div>'
                '<div class="live-kpi-grid">'
                + _kpi_html("IRR", irr_str, f"kpi-{irr_color}")
                + _kpi_html("MOIC", f"{moic_val:.2f}x", f"kpi-{moic_color}")
                + _kpi_html("Exit Equity", format_currency(kpis["exit_equity_value"]), "kpi-cyan", small=True)
                + _kpi_html("Entry EV", format_currency(kpis["entry_ev"]), "kpi-cyan", small=True)
                + _kpi_html("Max Debt/EBITDA", f"{max_lev:.1f}x", f"kpi-{lev_color}", small=True)
                + _kpi_html("Min Int. Coverage", f"{min_cov:.1f}x", f"kpi-{cov_color}", small=True)
                + _kpi_html("Debt Paydown", f"{kpis['debt_paydown_pct']:.0%}", "kpi-green", small=True)
                + _kpi_html("EBITDA CAGR", f"{kpis['ebitda_cagr']:.1%}", "kpi-cyan", small=True)
                + '</div></div>',
                unsafe_allow_html=True,
            )

    # =======================================================================
    # RUN FULL MODEL button
    # =======================================================================
    st.markdown("---")
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        run_clicked = st.button(
            "RUN FULL MODEL", type="primary", width="stretch",
        )

    if run_clicked:
        with st.spinner("Running full model..."):
            try:
                cap, ops, dbt, ext = _build_assumptions(
                    entry_ebitda=entry_ebitda, entry_multiple=entry_multiple,
                    debt_to_ebitda=debt_to_ebitda,
                    transaction_fee_pct=transaction_fee_pct,
                    financing_fee_pct=financing_fee_pct, cash_on_bs=cash_on_bs,
                    base_revenue=base_revenue, revenue_growth=revenue_growth,
                    hold_period=hold_period, ebitda_margin=ebitda_margin,
                    tax_rate=tax_rate, da_pct=da_pct,
                    capex_pct=capex_pct, nwc_pct=nwc_pct,
                    interest_rate=interest_rate, amortization_pct=amortization_pct,
                    cash_sweep_enabled=cash_sweep_enabled,
                    cash_sweep_pct=cash_sweep_pct,
                    exit_mode=exit_mode,
                    fixed_exit_multiple=fixed_exit_multiple,
                    industry_multiple=industry_multiple,
                    growth_multiple_factor=growth_multiple_factor,
                )
                committed = _run_engine(cap, ops, dbt, ext)
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.committed_results = committed
                st.session_state.committed_timestamp = ts
                st.session_state.model_results = committed
                st.success(f"Full model committed at {ts}")
            except Exception as exc:
                st.error(f"Model error: {exc}")
                st.code(traceback.format_exc())

    # =======================================================================
    # COMMITTED RESULTS (detailed output)
    # =======================================================================
    if st.session_state.committed_results is not None:
        results = st.session_state.committed_results

        st.markdown("---")
        # Sticky results banner: title + KPI cards as pure HTML so sticky works
        irr_display = format_percentage(results["irr"]) if results["irr"] else "N/A"
        moic_display = f"{results['moic']:.2f}x"
        entry_ev_display = format_currency(results["sources_uses"]["enterprise_value"])
        exit_eq_display = format_currency(results["exit_equity_value"])

        st.markdown(
            f'''<div class="results-sticky-banner">
  <div class="terminal-text" style="margin-bottom:0.3rem;">
    Committed &mdash; {st.session_state.committed_timestamp}
  </div>
  <p class="section-header" style="margin-bottom:0.6rem;">Results</p>
  <div class="results-kpi-row">
    <div class="results-kpi-card">
      <div class="results-kpi-label">IRR</div>
      <div class="results-kpi-value">{irr_display}</div>
    </div>
    <div class="results-kpi-card">
      <div class="results-kpi-label">MOIC</div>
      <div class="results-kpi-value">{moic_display}</div>
    </div>
    <div class="results-kpi-card">
      <div class="results-kpi-label">Entry EV</div>
      <div class="results-kpi-value">{entry_ev_display}</div>
    </div>
    <div class="results-kpi-card">
      <div class="results-kpi-label">Exit Equity</div>
      <div class="results-kpi-value">{exit_eq_display}</div>
    </div>
  </div>
</div>''',
            unsafe_allow_html=True,
        )

        # Sources & Uses
        with st.expander("Sources & Uses", expanded=False):
            su = results["sources_uses_table"]
            s1, s2 = st.columns(2)
            with s1:
                st.markdown("**Uses**")
                st.dataframe(
                    pd.DataFrame(su["uses"].items(), columns=["Item", "Amount (M)"]),
                    width="stretch", hide_index=True,
                )
            with s2:
                st.markdown("**Sources**")
                st.dataframe(
                    pd.DataFrame(su["sources"].items(), columns=["Item", "Amount (M)"]),
                    width="stretch", hide_index=True,
                )

        # Operating Projection
        with st.expander("Operating Projection", expanded=False):
            op_proj = results["operating_projection"].copy()
            for c in ["revenue", "ebitda", "ebit", "taxes", "nopat", "capex", "fcf"]:
                if c in op_proj.columns:
                    op_proj[c] = op_proj[c].round(1)
            st.dataframe(op_proj, width="stretch")

        # Debt Schedule
        with st.expander("Debt Schedule & Leverage", expanded=False):
            ds = results["debt_schedule"].copy()
            for c in ["beginning_debt", "interest", "scheduled_amort", "cash_sweep", "ending_debt"]:
                if c in ds.columns:
                    ds[c] = ds[c].round(1)
            st.markdown("**Debt Paydown**")
            st.dataframe(ds, width="stretch")

            st.markdown("**Leverage Ratios**")
            lev = results["leverage_ratios"].copy()
            lev["debt_to_ebitda"] = lev["debt_to_ebitda"].round(2)
            lev["interest_coverage"] = lev["interest_coverage"].round(2)
            st.dataframe(lev, width="stretch")

            flags = results["risk_flags"]
            if flags["high_leverage"]:
                st.warning(
                    f"High leverage: Max Debt/EBITDA = {flags['max_debt_to_ebitda']:.2f}x"
                )
            if flags["low_coverage"]:
                st.warning(
                    f"Low coverage: Min = {flags['min_interest_coverage']:.2f}x"
                )

        # Exit Summary
        with st.expander("Exit Summary", expanded=False):
            ex = results["exit_results"]
            exit_df = pd.DataFrame({
                "Metric": [
                    "Exit EBITDA", "Exit Multiple", "Exit EV",
                    "Exit Debt", "Exit Equity Value",
                ],
                "Value": [
                    format_currency(ex["exit_ebitda"]),
                    f"{ex['exit_multiple']:.2f}x",
                    format_currency(ex["exit_ev"]),
                    format_currency(ex["exit_debt"]),
                    format_currency(ex["exit_equity_value"]),
                ],
            })
            st.dataframe(exit_df, width="stretch", hide_index=True)
            st.caption(f"Methodology: {results['exit_methodology']}")

        # -------------------------------------------------------------------
        # SENSITIVITY
        # -------------------------------------------------------------------
        st.markdown(
            '<p class="section-header">Sensitivity</p>',
            unsafe_allow_html=True,
        )
        with st.expander("Run Sensitivity Grid", expanded=False):
            st.markdown("Vary growth and exit multiple to see range of outcomes.")
            sg1, sg2 = st.columns(2)
            with sg1:
                growth_low = st.number_input("Min Growth (%)", value=0.0, step=1.0) / 100
                growth_high = st.number_input("Max Growth (%)", value=10.0, step=1.0) / 100
                growth_steps = st.slider("Growth Steps", 3, 7, 5, key="gs")
            with sg2:
                mult_low = st.number_input("Min Exit Multiple", value=8.0, step=0.5)
                mult_high = st.number_input("Max Exit Multiple", value=12.0, step=0.5)
                mult_steps = st.slider("Multiple Steps", 3, 7, 5, key="ms")

            if st.button("RUN SENSITIVITY"):
                with st.spinner("Building sensitivity grid..."):
                    cap, ops, dbt, ext = _build_assumptions(
                        entry_ebitda=entry_ebitda, entry_multiple=entry_multiple,
                        debt_to_ebitda=debt_to_ebitda,
                        transaction_fee_pct=transaction_fee_pct,
                        financing_fee_pct=financing_fee_pct, cash_on_bs=cash_on_bs,
                        base_revenue=base_revenue, revenue_growth=revenue_growth,
                        hold_period=hold_period, ebitda_margin=ebitda_margin,
                        tax_rate=tax_rate, da_pct=da_pct,
                        capex_pct=capex_pct, nwc_pct=nwc_pct,
                        interest_rate=interest_rate, amortization_pct=amortization_pct,
                        cash_sweep_enabled=cash_sweep_enabled,
                        cash_sweep_pct=cash_sweep_pct,
                        exit_mode="fixed",
                        fixed_exit_multiple=fixed_exit_multiple,
                        industry_multiple=industry_multiple,
                        growth_multiple_factor=growth_multiple_factor,
                    )
                    gr = np.linspace(growth_low, growth_high, growth_steps)
                    mr = np.linspace(mult_low, mult_high, mult_steps)
                    sens_df = build_sensitivity_grid(
                        cap, ops, dbt, ext, gr.tolist(), mr.tolist(),
                    )
                    st.session_state.sensitivity_df = sens_df

                    st.markdown("**IRR Sensitivity Grid**")
                    irr_grid = summarize_sensitivity(sens_df, "irr")
                    st.dataframe(
                        irr_grid.map(
                            lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A"
                        ),
                        width="stretch",
                    )
                    st.markdown("**MOIC Sensitivity Grid**")
                    moic_grid = summarize_sensitivity(sens_df, "moic")
                    st.dataframe(
                        moic_grid.map(
                            lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A"
                        ),
                        width="stretch",
                    )

        # -------------------------------------------------------------------
        # IC REPORT
        # -------------------------------------------------------------------
        if api_available:
            st.markdown(
                '<p class="section-header">IC Report</p>',
                unsafe_allow_html=True,
            )

            with st.expander("Custom Instructions (Optional)", expanded=False):
                user_instructions = st.text_area(
                    "Custom Instructions",
                    placeholder="Focus areas, risks to highlight...",
                    height=150,
                )

            if st.button("GENERATE REPORT", type="primary", width="stretch"):
                with st.spinner("Generating IC report..."):
                    try:
                        min_sens_irr = results["irr"]
                        if "sensitivity_df" in st.session_state:
                            try:
                                min_sens_irr = st.session_state.sensitivity_df["irr"].min()
                            except Exception:
                                pass

                        scoring_inputs = ScoringInputs(
                            base_case_irr=results["irr"],
                            min_sensitivity_irr=min_sens_irr,
                            max_debt_to_ebitda=results["leverage_ratios"][
                                "debt_to_ebitda"
                            ].max(),
                            min_interest_coverage=results["leverage_ratios"][
                                "interest_coverage"
                            ].min(),
                        )
                        score_result = ICScoring(scoring_inputs).get_summary()

                        chart_paths = {}
                        chart_paths["revenue"] = charts.create_revenue_projection_chart(
                            results["operating_projection"][["year", "revenue"]].copy()
                        )
                        chart_paths["ebitda"] = charts.create_ebitda_projection_chart(
                            results["operating_projection"][["year", "ebitda"]].copy()
                        )
                        debt_df = results["debt_schedule"].reset_index()
                        if "year" not in debt_df.columns and "Year" not in debt_df.columns:
                            debt_df["year"] = range(1, len(debt_df) + 1)
                        elif "Year" in debt_df.columns:
                            debt_df["year"] = debt_df["Year"]
                        chart_paths["debt"] = charts.create_debt_schedule_chart(
                            debt_df[["year", "ending_debt"]]
                        )
                        lev_df = results["leverage_ratios"].reset_index()
                        if "year" not in lev_df.columns and "Year" not in lev_df.columns:
                            lev_df["year"] = range(1, len(lev_df) + 1)
                        elif "Year" in lev_df.columns:
                            lev_df["year"] = lev_df["Year"]
                        chart_paths["leverage"] = charts.create_leverage_chart(
                            lev_df[["year", "debt_to_ebitda"]]
                        )
                        if "sensitivity_df" in st.session_state:
                            chart_paths["sensitivity"] = charts.create_sensitivity_heatmap(
                                st.session_state.sensitivity_df
                            )

                        contribution = calculate_contribution_analysis(
                            entry_ev=results["sources_uses"]["enterprise_value"],
                            exit_ev=results["exit_results"]["exit_ev"],
                            entry_debt=results["sources_uses"]["debt"],
                            exit_debt=results["debt_schedule"]["ending_debt"].iloc[-1],
                            entry_ebitda=entry_ebitda,
                            exit_ebitda=results["operating_projection"]["ebitda"].iloc[-1],
                            entry_multiple=entry_multiple,
                        )

                        su_data = results["sources_uses"]
                        ex_data = results["exit_results"]
                        financial_data = {
                            "company_name": company_name,
                            "industry": industry,
                            # Flat keys for prompt template
                            "entry_ebitda": entry_ebitda,
                            "entry_multiple": entry_multiple,
                            "entry_ev": su_data["enterprise_value"],
                            "debt": su_data["debt"],
                            "equity": su_data["equity"],
                            "transaction_fees": su_data["transaction_fees"],
                            "financing_fees": su_data["financing_fees"],
                            "debt_to_ebitda": debt_to_ebitda,
                            "hold_period": hold_period,
                            "revenue_growth": revenue_growth,
                            "ebitda_margin": ebitda_margin,
                            "tax_rate": tax_rate,
                            "interest_rate": interest_rate,
                            "amortization_pct": amortization_pct,
                            "cash_sweep_enabled": cash_sweep_enabled,
                            "cash_sweep_pct": cash_sweep_pct,
                            "da_pct": da_pct,
                            "capex_pct": capex_pct,
                            "nwc_pct": nwc_pct,
                            # Returns
                            "irr": results["irr"],
                            "moic": results["moic"],
                            "exit_equity_value": results["exit_equity_value"],
                            # Exit details (flat)
                            "exit_multiple": ex_data["exit_multiple"],
                            "exit_ev": ex_data["exit_ev"],
                            "exit_ebitda": ex_data["exit_ebitda"],
                            "exit_debt": ex_data["exit_debt"],
                            "exit_methodology": results.get("exit_methodology", "fixed"),
                            # Nested (for leverage evolution, risk flags, projections)
                            "sources_uses": su_data,
                            "exit_results": ex_data,
                            "leverage_ratios": results["leverage_ratios"].to_dict("records"),
                            "risk_flags": results["risk_flags"],
                            "operating_projection": results["operating_projection"].to_dict(
                                "records"
                            ),
                            "debt_schedule": results["debt_schedule"].to_dict("records"),
                        }

                        # Add sensitivity summary if available
                        if "sensitivity_df" in st.session_state:
                            try:
                                sdf = st.session_state.sensitivity_df
                                financial_data["sensitivity_summary"] = {
                                    "min_irr": float(sdf["irr"].min()),
                                    "max_irr": float(sdf["irr"].max()),
                                    "min_moic": float(sdf["moic"].min()),
                                    "max_moic": float(sdf["moic"].max()),
                                }
                            except Exception:
                                pass

                        business_context = {
                            "business_description": (business_description or "").strip()
                            or "Not provided",
                            "investment_thesis": (investment_thesis or "").strip()
                            or "Not provided",
                            "key_risks": (key_risks or "").strip() or "Not provided",
                            "management_notes": (management_notes or "").strip()
                            or "Not provided",
                        }

                        report_gen = ICReportGenerator()
                        user_focus = (user_instructions or "").strip() or None
                        report_md = report_gen.generate_ic_report(
                            financial_data=financial_data,
                            business_context=business_context,
                            scoring_summary=score_result,
                            contribution_analysis=contribution,
                            user_instructions=user_focus,
                        )

                        for name, b64 in chart_paths.items():
                            tag = (
                                f'<img src="data:image/png;base64,{b64}" '
                                f'style="max-width:100%;height:auto;margin:20px 0;" />'
                            )
                            report_md = report_md.replace(
                                "{{chart:" + name + "}}", tag,
                            )

                        st.success("Report generated!")
                        st.markdown("---")
                        st.markdown(report_md, unsafe_allow_html=True)
                        st.session_state.ic_report = report_md
                        st.session_state.chart_paths = chart_paths

                    except Exception as exc:
                        st.error(f"Report failed: {exc}")
                        st.code(traceback.format_exc())

            if "ic_report" in st.session_state:
                dl1, dl2 = st.columns(2)
                with dl1:
                    st.download_button(
                        "DOWNLOAD MARKDOWN",
                        data=st.session_state.ic_report,
                        file_name=f"{company_name}_IC_Report.md",
                        mime="text/markdown",
                        width="stretch",
                    )
                with dl2:
                    if st.button("EXPORT PDF", width="stretch"):
                        with st.spinner("Generating PDF..."):
                            try:
                                import os

                                os.environ["DYLD_LIBRARY_PATH"] = (
                                    "/opt/homebrew/lib:"
                                    + os.environ.get("DYLD_LIBRARY_PATH", "")
                                )
                                pdf_bytes = PDFExporter().export_to_pdf_bytes(
                                    markdown_content=st.session_state.ic_report,
                                    company_name=company_name,
                                    charts=st.session_state.chart_paths,
                                )
                                st.download_button(
                                    "Download PDF",
                                    data=pdf_bytes,
                                    file_name=f"{company_name}_IC_Report.pdf",
                                    mime="application/pdf",
                                    width="stretch",
                                )
                                st.success("PDF ready!")
                            except Exception as exc:
                                st.error(f"PDF export failed: {exc}")
                                st.code(traceback.format_exc())

    else:
        if st.session_state.committed_results is None:
            st.markdown("---")
            st.info(
                "Adjust assumptions above and click **RUN FULL MODEL** "
                "to generate detailed outputs."
            )

# Footer
st.markdown("---")
st.caption("Deal.Eval — Advanced LBO Modeling Engine")
