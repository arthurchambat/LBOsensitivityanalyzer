"""
Streamlit App - Advanced LBO Deal Evaluation
Uses new modular LBO engine with full operating model.
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any

from src.data import FinancialDataIngestion, get_sample_dataframe, HistoricalAnalyzer
from src.models import (
    CapitalStructure, CapitalStructureInputs,
    OperatingModel, OperatingAssumptions,
    DebtModel, DebtAssumptions,
    ExitModel, ExitAssumptions,
    LBOEngine, build_sensitivity_grid, summarize_sensitivity
)
from src.analysis import check_api_key_available, RiskAnalyzer, ICScoring, ScoringInputs, calculate_contribution_analysis
from src.reporting import charts, MemoGenerator, ICReportGenerator, PDFExporter
from src.utils import format_currency, format_percentage, format_multiple

# Page config
st.set_page_config(
    page_title="Deal Eval Pipeline",
    page_icon="⬢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Financial Terminal Aesthetic
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Fraunces:wght@300;600;900&display=swap');
    
    :root {
        --primary-dark: #0a0e1a;
        --secondary-dark: #131829;
        --accent-cyan: #00d4ff;
        --accent-amber: #ffb020;
        --accent-red: #ff4757;
        --accent-green: #1dd1a1;
        --text-primary: #e8eaed;
        --text-secondary: #8b92a8;
        --border-color: #1e2433;
        --glow: rgba(0, 212, 255, 0.15);
    }
    
    /* Global Styling */
    .stApp {
        background: linear-gradient(135deg, #0a0e1a 0%, #131829 50%, #0f1321 100%);
        background-attachment: fixed;
    }
    
    .main .block-container {
        padding-top: 3rem;
        max-width: 1400px;
        animation: fadeIn 0.6s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(-30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    /* Typography */
    h1, h2, h3, .main-header {
        font-family: 'Fraunces', serif;
        color: var(--text-primary);
        letter-spacing: -0.02em;
        font-weight: 900;
        text-transform: uppercase;
        animation: slideInRight 0.8s ease-out;
    }
    
    .main-header {
        font-size: 3.5rem;
        background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-amber) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.95rem;
        color: var(--text-secondary);
        font-weight: 300;
        letter-spacing: 0.05em;
        margin-bottom: 3rem;
    }
    
    .section-header {
        font-family: 'Fraunces', serif;
        font-size: 1.8rem;
        font-weight: 600;
        color: var(--accent-cyan);
        margin-top: 3rem;
        margin-bottom: 1.5rem;
        padding-left: 1.5rem;
        border-left: 4px solid var(--accent-cyan);
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    
    .terminal-text {
        font-family: 'JetBrains Mono', monospace;
        color: var(--accent-cyan);
        text-shadow: 0 0 5px var(--glow);
        letter-spacing: 0.02em;
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: var(--accent-cyan);
        text-shadow: 0 0 10px var(--glow);
    }
    
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, var(--secondary-dark) 0%, rgba(19, 24, 41, 0.5) 100%);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        transition: all 0.3s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 212, 255, 0.2);
        border-color: var(--accent-cyan);
    }
    
    /* Buttons */
    .stButton > button {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        background: linear-gradient(135deg, var(--accent-cyan) 0%, #0099cc 100%);
        color: var(--primary-dark);
        border: none;
        border-radius: 6px;
        padding: 0.75rem 2rem;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 212, 255, 0.5);
    }
    
    /* DataFrames */
    [data-testid="stDataFrame"] {
        font-family: 'JetBrains Mono', monospace;
        background: var(--secondary-dark);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    
    [data-testid="stDataFrame"] th {
        background: linear-gradient(180deg, #1a1f2e 0%, #131829 100%);
        color: var(--accent-amber);
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 0.08em;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        font-family: 'JetBrains Mono', monospace;
        background: var(--secondary-dark);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        color: var(--text-primary);
    }
    
    </style>
    """, unsafe_allow_html=True)

# Check API availability
api_available = check_api_key_available()

# Header
st.markdown('''
    <div class="main-header">⬢ DEAL.EVAL v3.0</div>
    <div class="sub-header">
        <span class="terminal-text">→</span> INGEST 
        <span class="terminal-text">→</span> ANALYZE 
        <span class="terminal-text">→</span> STRUCTURE 
        <span class="terminal-text">→</span> MODEL 
        <span class="terminal-text">→</span> SYNTHESIZE
    </div>
    ''', unsafe_allow_html=True)

# Initialize session state
for key in ['data_uploaded', 'historical_data', 'historical_summary', 'model_results']:
    if key not in st.session_state:
        st.session_state[key] = None if key != 'data_uploaded' else False

# Sidebar
st.sidebar.markdown('<div class="terminal-text" style="font-size: 1.1rem; margin-bottom: 1rem;">◉ DEAL.CONFIG</div>', unsafe_allow_html=True)
company_name = st.sidebar.text_input("Company Name", value="Target Co.")
industry = st.sidebar.text_input("Industry", value="Business Services")

st.sidebar.markdown("---")

# Business Information Section
with st.sidebar.expander("📋 Business Information", expanded=False):
    st.markdown("**Qualitative Inputs for IC Report**")
    
    business_description = st.text_area(
        "Business Description",
        placeholder="Brief description of company operations, products/services, market position...",
        height=100,
        help="Used in Business Overview section"
    )
    
    investment_thesis = st.text_area(
        "Investment Thesis",
        placeholder="Key value creation drivers, strategic rationale, competitive advantages...",
        height=100,
        help="Core reasons for pursuing this investment"
    )
    
    key_risks = st.text_area(
        "Key Risks",
        placeholder="Market risks, execution risks, competitive threats, regulatory concerns...",
        height=100,
        help="Main risk factors to highlight"
    )
    
    management_notes = st.text_area(
        "Management Assessment",
        placeholder="Management team experience, track record, key hires needed...",
        height=80,
        help="Assessment of leadership quality"
    )

st.sidebar.markdown("---")

# ============================================================================
# SECTION 1: DATA INGESTION
# ============================================================================
st.markdown('<p class="section-header">◢ INGEST: Historical Financials</p>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Upload CSV with historical financials",
        type=['csv'],
        help="CSV with columns: year, revenue, ebitda",
        key="csv_uploader"
    )

with col2:
    if st.button("⬢ LOAD.SAMPLE", width="stretch"):
        sample_df = get_sample_dataframe()
        st.session_state.historical_data = sample_df
        st.session_state.data_uploaded = True
        st.rerun()

# Process uploaded file (only if not already processed)
if uploaded_file is not None and uploaded_file.name:
    # Check if this is a new file (different from what's already loaded)
    file_already_processed = False
    if 'uploaded_filename' in st.session_state:
        if st.session_state.uploaded_filename == uploaded_file.name and st.session_state.data_uploaded:
            file_already_processed = True
    
    if not file_already_processed:
        try:
            ingestion = FinancialDataIngestion()
            
            # Show progress
            with st.spinner("Processing CSV file..."):
                cleaned_data, warnings = ingestion.ingest_csv(uploaded_file)
            
            # Only proceed if data is valid
            if cleaned_data is not None and len(cleaned_data) > 0:
                st.session_state.historical_data = cleaned_data
                st.session_state.data_uploaded = True
                st.session_state.uploaded_filename = uploaded_file.name
                
                # Show success with details
                st.success(f"✅ **[VALIDATED]** Data ingestion complete - {len(cleaned_data)} years loaded")
                
                # Show what was detected (expandable for debugging)
                with st.expander("📊 Detected Data Structure", expanded=False):
                    st.write(f"**Columns detected:** {', '.join(cleaned_data.columns)}")
                    st.write(f"**Years range:** {cleaned_data['year'].min():.0f} - {cleaned_data['year'].max():.0f}")
                    st.dataframe(cleaned_data.head(), use_container_width=True)
                
                if warnings:
                    st.warning("**Validation Warnings:**\n" + "\n".join(f"- {w}" for w in warnings))
                
                st.rerun()
            else:
                # Data validation failed
                st.error("**❌ Data Validation Failed**")
                if warnings:
                    st.error("**Issues found:**\n" + "\n".join(f"- {w}" for w in warnings))
                st.info("**Required CSV format:**\n- Column 1: `year` (or Year, Date, Period)\n- Column 2: `revenue` (or Revenue, Sales, Turnover)\n- Column 3: `ebitda` (or EBITDA)\n\n**Example:**\n```\nyear,revenue,ebitda\n2019,100,20\n2020,105,21\n2021,112,23\n```")
                st.session_state.data_uploaded = False
                st.session_state.historical_data = None
                
        except Exception as e:
            st.error(f"❌ **Error processing file:** {e}")
            st.info("Please ensure your CSV file:\n- Is properly formatted\n- Contains numeric values\n- Has required columns: year, revenue, ebitda")
            st.session_state.data_uploaded = False
            st.session_state.historical_data = None

if st.session_state.data_uploaded and st.session_state.historical_data is not None:
    df = st.session_state.historical_data
    
    st.markdown('<div class="terminal-text" style="font-size: 0.9rem; margin-top: 1.5rem; margin-bottom: 0.5rem;">// HISTORICAL.DATA</div>', unsafe_allow_html=True)
    st.dataframe(df, width="stretch")
    
    # Run analysis
    analyzer = HistoricalAnalyzer(df)
    st.session_state.historical_summary = analyzer.get_full_summary()
    
    st.markdown('<div class="terminal-text" style="font-size: 0.9rem; margin-top: 2rem; margin-bottom: 1rem;">// PERFORMANCE.METRICS</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    summary = st.session_state.historical_summary
    
    with col1:
        st.metric("Revenue CAGR", format_percentage(summary.get('revenue_cagr', 0)))
    with col2:
        st.metric("EBITDA CAGR", format_percentage(summary.get('ebitda_cagr', 0)))
    with col3:
        st.metric("Avg EBITDA Margin", format_percentage(summary.get('ebitda_avg', 0)))
    with col4:
        st.metric("Latest EBITDA", format_currency(df['ebitda'].iloc[-1]))

# ============================================================================
# SECTION 2: CAPITAL STRUCTURE
# ============================================================================
if st.session_state.data_uploaded:
    st.markdown('<p class="section-header">◢ STRUCTURE: Transaction Setup</p>', unsafe_allow_html=True)
    
    with st.expander("⚙️ Capital Structure Inputs", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            entry_ebitda = st.number_input(
                "Entry EBITDA (€M)",
                min_value=1.0,
                value=float(st.session_state.historical_data['ebitda'].iloc[-1]),
                step=1.0
            )
            entry_multiple = st.number_input(
                "Entry Multiple (x)",
                min_value=1.0,
                max_value=20.0,
                value=10.0,
                step=0.5
            )
        
        with col2:
            debt_to_ebitda = st.number_input(
                "Debt / EBITDA (x)",
                min_value=0.0,
                max_value=10.0,
                value=5.0,
                step=0.5
            )
            cash_on_bs = st.number_input(
                "Cash on BS (€M)",
                min_value=0.0,
                value=0.0,
                step=1.0
            )
        
        with col3:
            transaction_fee_pct = st.slider(
                "Transaction Fees (% of EV)",
                min_value=0.0,
                max_value=5.0,
                value=2.0,
                step=0.5
            ) / 100
            
            financing_fee_pct = st.slider(
                "Financing Fees (% of Debt)",
                min_value=0.0,
                max_value=5.0,
                value=3.0,
                step=0.5
            ) / 100

# ============================================================================
# SECTION 3: OPERATING ASSUMPTIONS
# ============================================================================
if st.session_state.data_uploaded:
    st.markdown('<p class="section-header">◢ OPERATE: Financial Projections</p>', unsafe_allow_html=True)
    
    with st.expander("📈 Operating Model Inputs", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            hold_period = st.slider("Hold Period (Years)", 3, 7, 5)
            
            revenue_growth = st.slider(
                "Revenue Growth (%/year)",
                min_value=-5.0,
                max_value=20.0,
                value=5.0,
                step=0.5
            ) / 100
            
            ebitda_margin = st.slider(
                "EBITDA Margin (% of Revenue)",
                min_value=5.0,
                max_value=50.0,
                value=20.0,
                step=1.0
            ) / 100
            
            tax_rate = st.slider(
                "Tax Rate (%)",
                min_value=0.0,
                max_value=40.0,
                value=25.0,
                step=1.0
            ) / 100
        
        with col2:
            da_pct = st.slider(
                "D&A (% of Revenue)",
                min_value=0.0,
                max_value=10.0,
                value=3.0,
                step=0.5
            ) / 100
            
            capex_pct = st.slider(
                "Capex (% of Revenue)",
                min_value=0.0,
                max_value=15.0,
                value=3.0,
                step=0.5
            ) / 100
            
            nwc_pct = st.slider(
                "NWC (% of Revenue)",
                min_value=0.0,
                max_value=30.0,
                value=10.0,
                step=1.0
            ) / 100

# ============================================================================
# SECTION 4: DEBT STRUCTURE
# ============================================================================
if st.session_state.data_uploaded:
    st.markdown('<p class="section-header">◢ LEVERAGE: Debt Structure</p>', unsafe_allow_html=True)
    
    with st.expander("💰 Debt Model Inputs", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            interest_rate = st.slider(
                "Interest Rate (%)",
                min_value=0.0,
                max_value=15.0,
                value=6.0,
                step=0.5
            ) / 100
            
            amortization_pct = st.slider(
                "Annual Amortization (% of Initial Debt)",
                min_value=0.0,
                max_value=20.0,
                value=5.0,
                step=1.0
            ) / 100
        
        with col2:
            cash_sweep_enabled = st.checkbox("Enable Cash Sweep", value=True)
            
            cash_sweep_pct = st.slider(
                "Cash Sweep (% of FCF)",
                min_value=0.0,
                max_value=100.0,
                value=50.0,
                step=10.0,
                disabled=not cash_sweep_enabled
            ) / 100 if cash_sweep_enabled else 0.0

# ============================================================================
# SECTION 5: EXIT ASSUMPTIONS
# ============================================================================
if st.session_state.data_uploaded:
    st.markdown('<p class="section-header">◢ EXIT: Valuation Methodology</p>', unsafe_allow_html=True)
    
    with st.expander("🎯 Exit Model Inputs", expanded=True):
        exit_mode = st.radio(
            "Exit Valuation Method",
            options=['fixed', 'mean_reversion', 'growth_adjusted'],
            format_func=lambda x: {
                'fixed': '◉ Fixed Multiple',
                'mean_reversion': '◉ Mean Reversion to Industry',
                'growth_adjusted': '◉ Growth-Adjusted Multiple'
            }[x]
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if exit_mode == 'fixed':
                fixed_exit_multiple = st.number_input(
                    "Exit Multiple (x)",
                    min_value=1.0,
                    max_value=20.0,
                    value=10.0,
                    step=0.5
                )
            else:
                fixed_exit_multiple = entry_multiple
        
        with col2:
            if exit_mode == 'mean_reversion':
                industry_multiple = st.number_input(
                    "Industry Multiple (x)",
                    min_value=1.0,
                    max_value=20.0,
                    value=12.0,
                    step=0.5
                )
            else:
                industry_multiple = entry_multiple
        
        with col3:
            if exit_mode == 'growth_adjusted':
                growth_multiple_factor = st.slider(
                    "Growth Sensitivity",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.5,
                    step=0.1,
                    help="Multiple change per 1% growth"
                )
            else:
                growth_multiple_factor = 0.5

# ============================================================================
# SECTION 6: RUN MODEL
# ============================================================================
if st.session_state.data_uploaded:
    st.markdown('<p class="section-header">◢ EXECUTE: LBO Analysis</p>', unsafe_allow_html=True)
    
    if st.button("▸ RUN.FULL.MODEL", type="primary", width="stretch"):
        with st.spinner("Running LBO model..."):
            try:
                # Build assumptions
                capital_inputs = CapitalStructureInputs(
                    entry_ebitda=entry_ebitda,
                    entry_multiple=entry_multiple,
                    debt_to_ebitda=debt_to_ebitda,
                    transaction_fee_pct=transaction_fee_pct,
                    financing_fee_pct=financing_fee_pct,
                    cash_on_bs=cash_on_bs
                )
                
                # Base revenue from historical
                base_revenue = st.session_state.historical_data['revenue'].iloc[-1]
                
                operating_assumptions = OperatingAssumptions(
                    base_revenue=base_revenue,
                    revenue_growth_rates=[revenue_growth] * hold_period,
                    ebitda_margin=ebitda_margin,
                    tax_rate=tax_rate,
                    da_pct_revenue=da_pct,
                    capex_pct_revenue=capex_pct,
                    nwc_pct_revenue=nwc_pct
                )
                
                debt_assumptions = DebtAssumptions(
                    initial_debt=0.0,  # Will be set by engine
                    interest_rate=interest_rate,
                    amortization_pct=amortization_pct,
                    cash_sweep_enabled=cash_sweep_enabled,
                    cash_sweep_pct=cash_sweep_pct
                )
                
                exit_assumptions = ExitAssumptions(
                    exit_mode=exit_mode,
                    fixed_exit_multiple=fixed_exit_multiple,
                    entry_multiple=entry_multiple,
                    industry_multiple=industry_multiple,
                    hold_period=hold_period,
                    growth_multiple_factor=growth_multiple_factor
                )
                
                # Run engine
                engine = LBOEngine(
                    capital_inputs,
                    operating_assumptions,
                    debt_assumptions,
                    exit_assumptions
                )
                
                st.session_state.model_results = engine.get_results()
                st.success("✅ **[COMPLETE]** Model execution successful.")
                
            except Exception as e:
                st.error(f"Model error: {e}")
                import traceback
                st.code(traceback.format_exc())

# ============================================================================
# SECTION 7: RESULTS DISPLAY
# ============================================================================
if st.session_state.model_results:
    results = st.session_state.model_results
    
    st.markdown("---")
    st.markdown('<div class="terminal-text" style="font-size: 0.9rem; margin-top: 2rem; margin-bottom: 1rem;">// RESULTS.OUTPUT</div>', unsafe_allow_html=True)
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        irr_val = results['irr']
        st.metric(
            "IRR",
            format_percentage(irr_val) if irr_val is not None else "N/A",
            delta=None
        )
    
    with col2:
        st.metric("MOIC", f"{results['moic']:.2f}x")
    
    with col3:
        st.metric("Entry EV", format_currency(results['sources_uses']['enterprise_value']))
    
    with col4:
        st.metric("Exit Equity", format_currency(results['exit_equity_value']))
    
    # Sources & Uses
    with st.expander("💼 Sources & Uses", expanded=False):
        su_table = results['sources_uses_table']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Uses**")
            uses_df = pd.DataFrame(su_table['uses'].items(), columns=['Item', 'Amount (€M)'])
            st.dataframe(uses_df, width="stretch", hide_index=True)
        
        with col2:
            st.markdown("**Sources**")
            sources_df = pd.DataFrame(su_table['sources'].items(), columns=['Item', 'Amount (€M)'])
            st.dataframe(sources_df, width="stretch", hide_index=True)
    
    # Operating Projection
    with st.expander("📊 Operating Projection", expanded=False):
        op_proj = results['operating_projection'].copy()
        # Format for display
        for col in ['revenue', 'ebitda', 'ebit', 'taxes', 'nopat', 'capex', 'fcf']:
            if col in op_proj.columns:
                op_proj[col] = op_proj[col].round(1)
        st.dataframe(op_proj, width="stretch")
    
    # Debt Schedule
    with st.expander("💰 Debt Schedule & Leverage", expanded=False):
        debt_sched = results['debt_schedule'].copy()
        for col in ['beginning_debt', 'interest', 'scheduled_amort', 'cash_sweep', 'ending_debt']:
            if col in debt_sched.columns:
                debt_sched[col] = debt_sched[col].round(1)
        
        st.markdown("**Debt Paydown**")
        st.dataframe(debt_sched, width="stretch")
        
        st.markdown("**Leverage Ratios**")
        leverage = results['leverage_ratios'].copy()
        leverage['debt_to_ebitda'] = leverage['debt_to_ebitda'].round(2)
        leverage['interest_coverage'] = leverage['interest_coverage'].round(2)
        st.dataframe(leverage, width="stretch")
        
        # Risk flags
        flags = results['risk_flags']
        if flags['high_leverage']:
            st.warning(f"⚠️ High leverage detected: Max Debt/EBITDA = {flags['max_debt_to_ebitda']:.2f}x")
        if flags['low_coverage']:
            st.warning(f"⚠️ Low interest coverage detected: Min = {flags['min_interest_coverage']:.2f}x")
    
    # Exit Summary
    with st.expander("🎯 Exit Summary", expanded=False):
        exit_res = results['exit_results']
        exit_df = pd.DataFrame({
            'Metric': ['Exit EBITDA', 'Exit Multiple', 'Exit EV', 'Exit Debt', 'Exit Equity Value'],
            'Value': [
                format_currency(exit_res['exit_ebitda']),
                f"{exit_res['exit_multiple']:.2f}x",
                format_currency(exit_res['exit_ev']),
                format_currency(exit_res['exit_debt']),
                format_currency(exit_res['exit_equity_value'])
            ]
        })
        st.dataframe(exit_df, width="stretch", hide_index=True)
        st.caption(f"Methodology: {results['exit_methodology']}")

# ============================================================================
# SECTION 8: SENSITIVITY ANALYSIS
# ============================================================================
if st.session_state.model_results:
    st.markdown('<p class="section-header">◢ SENSITIVITY: Scenario Analysis</p>', unsafe_allow_html=True)
    
    with st.expander("🎲 Run Sensitivity Grid", expanded=False):
        st.markdown("Vary growth and exit multiple to see range of outcomes.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            growth_low = st.number_input("Min Growth (%)", value=0.0, step=1.0) / 100
            growth_high = st.number_input("Max Growth (%)", value=10.0, step=1.0) / 100
            growth_steps = st.slider("Growth Steps", 3, 7, 5)
        
        with col2:
            mult_low = st.number_input("Min Exit Multiple", value=8.0, step=0.5)
            mult_high = st.number_input("Max Exit Multiple", value=12.0, step=0.5)
            mult_steps = st.slider("Multiple Steps", 3, 7, 5)
        
        if st.button("▸ RUN.SENSITIVITY"):
            with st.spinner("Building sensitivity grid..."):
                # Recreate inputs
                capital_inputs = CapitalStructureInputs(
                    entry_ebitda=entry_ebitda,
                    entry_multiple=entry_multiple,
                    debt_to_ebitda=debt_to_ebitda,
                    transaction_fee_pct=transaction_fee_pct,
                    financing_fee_pct=financing_fee_pct,
                    cash_on_bs=cash_on_bs
                )
                
                base_revenue = st.session_state.historical_data['revenue'].iloc[-1]
                
                operating_assumptions = OperatingAssumptions(
                    base_revenue=base_revenue,
                    revenue_growth_rates=[revenue_growth] * hold_period,
                    ebitda_margin=ebitda_margin,
                    tax_rate=tax_rate,
                    da_pct_revenue=da_pct,
                    capex_pct_revenue=capex_pct,
                    nwc_pct_revenue=nwc_pct
                )
                
                debt_assumptions = DebtAssumptions(
                    initial_debt=0.0,
                    interest_rate=interest_rate,
                    amortization_pct=amortization_pct,
                    cash_sweep_enabled=cash_sweep_enabled,
                    cash_sweep_pct=cash_sweep_pct
                )
                
                exit_assumptions = ExitAssumptions(
                    exit_mode='fixed',
                    fixed_exit_multiple=fixed_exit_multiple,
                    entry_multiple=entry_multiple,
                    hold_period=hold_period
                )
                
                # Build ranges
                import numpy as np
                growth_range = np.linspace(growth_low, growth_high, growth_steps)
                mult_range = np.linspace(mult_low, mult_high, mult_steps)
                
                sensitivity_df = build_sensitivity_grid(
                    capital_inputs,
                    operating_assumptions,
                    debt_assumptions,
                    exit_assumptions,
                    growth_range.tolist(),
                    mult_range.tolist()
                )
                
                # Store in session state for IC report
                st.session_state.sensitivity_df = sensitivity_df
                
                # Display IRR grid
                irr_grid = summarize_sensitivity(sensitivity_df, 'irr')
                irr_grid = irr_grid.applymap(lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A")
                
                st.markdown("**IRR Sensitivity Grid**")
                st.dataframe(irr_grid, width="stretch")
                
                # Display MOIC grid
                moic_grid = summarize_sensitivity(sensitivity_df, 'moic')
                moic_grid = moic_grid.applymap(lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A")
                
                st.markdown("**MOIC Sensitivity Grid**")
                st.dataframe(moic_grid, width="stretch")

# ============================================================================
# SECTION 9: IC REPORT GENERATION
# ============================================================================
if st.session_state.model_results and api_available:
    st.markdown('<p class="section-header">◢ SYNTHESIZE: IC Report</p>', unsafe_allow_html=True)
    
    # Add custom instructions section
    with st.expander("✍️ Custom Instructions (Optional)", expanded=False):
        st.markdown("Provide additional context or specific focus areas for the IC report:")
        user_instructions = st.text_area(
            "Custom Instructions",
            placeholder="Example:\n- Focus on competitive dynamics in the market\n- Emphasize management team quality\n- Highlight specific operational improvements planned\n- Note regulatory concerns in the sector",
            height=150,
            help="These instructions will guide the AI to emphasize specific aspects in the report"
        )
    
    col_md, col_pdf = st.columns(2)
    
    with col_md:
        generate_report = st.button("⬢ GENERATE.REPORT", type="primary", use_container_width=True)
    
    if generate_report:
        with st.spinner("Generating comprehensive IC report..."):
            try:
                results = st.session_state.model_results
                
                # Step 1: Calculate IC Score
                st.info("📊 Calculating IC score...")
                
                # Get min sensitivity IRR if available
                min_sensitivity_irr = results['irr']  # Default to base case
                if 'sensitivity_df' in st.session_state:
                    try:
                        min_sensitivity_irr = st.session_state.sensitivity_df['irr'].min()
                    except:
                        pass
                
                # Create scoring inputs
                scoring_inputs = ScoringInputs(
                    base_case_irr=results['irr'],
                    min_sensitivity_irr=min_sensitivity_irr,
                    max_debt_to_ebitda=results['leverage_ratios']['debt_to_ebitda'].max() if 'leverage_ratios' in results else debt_to_ebitda,
                    min_interest_coverage=results['leverage_ratios']['interest_coverage'].min() if 'leverage_ratios' in results else 999,
                    ebitda_growth_volatility=None  # Can add if historical data available
                )
                
                # Calculate score
                scorer = ICScoring(scoring_inputs)
                score_result = scorer.get_summary()
                
                # Step 2: Generate Charts
                st.info("📈 Generating financial charts...")
                chart_paths = {}
                
                # Revenue projection chart
                revenue_df = results['operating_projection'][['year', 'revenue']].copy()
                chart_paths['revenue'] = charts.create_revenue_projection_chart(revenue_df)
                
                # EBITDA projection chart
                ebitda_df = results['operating_projection'][['year', 'ebitda']].copy()
                chart_paths['ebitda'] = charts.create_ebitda_projection_chart(ebitda_df)
                
                # Debt schedule chart
                debt_df = results['debt_schedule'].reset_index()
                if 'Year' not in debt_df.columns and 'year' not in debt_df.columns:
                    debt_df['year'] = range(1, len(debt_df) + 1)
                elif 'Year' in debt_df.columns:
                    debt_df['year'] = debt_df['Year']
                # Column is already 'ending_debt' (lowercase)
                chart_paths['debt'] = charts.create_debt_schedule_chart(debt_df[['year', 'ending_debt']])
                
                # Leverage chart
                leverage_df = results['leverage_ratios'].reset_index()
                if 'Year' not in leverage_df.columns and 'year' not in leverage_df.columns:
                    leverage_df['year'] = range(1, len(leverage_df) + 1)
                elif 'Year' in leverage_df.columns:
                    leverage_df['year'] = leverage_df['Year']
                # Column is already 'debt_to_ebitda' (lowercase)
                chart_paths['leverage'] = charts.create_leverage_chart(leverage_df[['year', 'debt_to_ebitda']])
                
                # Sensitivity heatmap (if available)
                if 'sensitivity_df' in st.session_state:
                    sensitivity_df = st.session_state.sensitivity_df
                    chart_paths['sensitivity'] = charts.create_sensitivity_heatmap(sensitivity_df)
                
                # Step 3: Prepare context
                st.info("🤖 Generating AI-powered report sections...")
                
                # Calculate contribution analysis
                contribution = calculate_contribution_analysis(
                    entry_ev=results['sources_uses']['enterprise_value'],
                    exit_ev=results['exit_results']['exit_ev'],
                    entry_debt=results['sources_uses']['debt'],
                    exit_debt=results['debt_schedule']['ending_debt'].iloc[-1],
                    entry_ebitda=entry_ebitda,
                    exit_ebitda=results['operating_projection']['ebitda'].iloc[-1],
                    entry_multiple=entry_multiple
                )
                
                financial_data = {
                    'company_name': company_name,
                    'industry': industry,
                    'entry_ebitda': entry_ebitda,
                    'entry_multiple': entry_multiple,
                    'debt_to_ebitda': debt_to_ebitda,
                    'hold_period': hold_period,
                    'revenue_growth': revenue_growth,
                    'ebitda_margin': ebitda_margin,
                    'exit_multiple': results['exit_results']['exit_multiple'],
                    'irr': results['irr'],
                    'moic': results['moic'],
                    'sources_uses': results['sources_uses'],
                    'exit_results': results['exit_results'],
                    'leverage_ratios': results['leverage_ratios'].to_dict('records'),
                    'risk_flags': results['risk_flags'],
                    'operating_projection': results['operating_projection'].to_dict('records'),
                    'debt_schedule': results['debt_schedule'].to_dict('records'),
                }
                
                business_context = {
                    'business_description': business_description.strip() if business_description else "Not provided",
                    'investment_thesis': investment_thesis.strip() if investment_thesis else "Not provided",
                    'key_risks': key_risks.strip() if key_risks else "Not provided",
                    'management_notes': management_notes.strip() if management_notes else "Not provided",
                }
                
                # Step 4: Generate Report
                report_gen = ICReportGenerator()
                user_focus = user_instructions.strip() if user_instructions else None
                
                report_markdown = report_gen.generate_ic_report(
                    financial_data=financial_data,
                    business_context=business_context,
                    scoring_summary=score_result,
                    contribution_analysis=contribution,
                    user_instructions=user_focus
                )
                
                # Step 5: Embed charts in report
                st.info("🖼️ Embedding charts...")
                for chart_name, chart_base64 in chart_paths.items():
                    placeholder = f"{{{{chart:{chart_name}}}}}"
                    # Create markdown image with base64 data
                    img_tag = f'<img src="data:image/png;base64,{chart_base64}" style="max-width: 100%; height: auto; margin: 20px 0;" />'
                    report_markdown = report_markdown.replace(placeholder, img_tag)
                
                # Display report
                st.success("✅ Report generated successfully!")
                st.markdown("---")
                st.markdown(report_markdown, unsafe_allow_html=True)
                
                # Save to session state for PDF export
                st.session_state.ic_report = report_markdown
                st.session_state.chart_paths = chart_paths
                
            except Exception as e:
                st.error(f"Report generation failed: {e}")
                import traceback
                st.code(traceback.format_exc())
    
    # Download buttons (show if report exists)
    if 'ic_report' in st.session_state:
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            st.download_button(
                label="⬇ DOWNLOAD MARKDOWN",
                data=st.session_state.ic_report,
                file_name=f"{company_name}_IC_Report.md",
                mime="text/markdown",
                use_container_width=True
            )
        
        with col_dl2:
            if st.button("⬇ EXPORT PDF", use_container_width=True):
                with st.spinner("Generating PDF..."):
                    try:
                        # Set library path before importing WeasyPrint
                        import os
                        os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib:' + os.environ.get('DYLD_LIBRARY_PATH', '')
                        
                        # Create PDF exporter instance
                        exporter = PDFExporter()
                        
                        # Generate PDF bytes
                        pdf_bytes = exporter.export_to_pdf_bytes(
                            markdown_content=st.session_state.ic_report,
                            company_name=company_name,
                            charts=st.session_state.chart_paths
                        )
                        
                        st.download_button(
                            label="📄 Download PDF",
                            data=pdf_bytes,
                            file_name=f"{company_name}_IC_Report.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        st.success("✅ PDF ready for download!")
                    except Exception as e:
                        st.error(f"PDF export failed: {e}")
                        import traceback
                        st.code(traceback.format_exc())

st.markdown("---")
st.caption("⬢ DEAL.EVAL v3.0 | Advanced LBO Modeling Engine")
