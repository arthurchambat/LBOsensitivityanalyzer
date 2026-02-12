"""
AI-Augmented Deal Evaluation Pipeline
Complete Streamlit Application

Full workflow:
1. Upload historical financials (CSV)
2. Analyze historical performance
3. Calibrate forward assumptions
4. Run LBO model
5. Generate IC memo
6. Download memo
"""
import streamlit as st
import pandas as pd
import io
from datetime import datetime

# Import custom modules
from ingestion import FinancialDataIngestion, create_sample_csv
from historical_analysis import HistoricalAnalyzer, format_metric
from lbo import LBOModel, build_sensitivity_grid, summarize_sensitivity
from risk_analyzer import RiskAnalyzer, check_api_key_available
from memo_generator import MemoGenerator, check_memo_api_available
from utils import (
    format_currency,
    format_percentage,
    format_multiple,
    validate_model_inputs,
    safe_percentage_input
)

# Page configuration
st.set_page_config(
    page_title="AI Deal Evaluation Pipeline",
    page_icon="🎯",
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
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
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
        text-shadow: 0 0 30px var(--glow);
        position: relative;
        display: inline-block;
    }
    
    .main-header::after {
        content: '';
        position: absolute;
        bottom: -10px;
        left: 0;
        width: 60%;
        height: 3px;
        background: linear-gradient(90deg, var(--accent-cyan), transparent);
        animation: slideInRight 1s ease-out 0.2s both;
    }
    
    .sub-header {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.95rem;
        color: var(--text-secondary);
        font-weight: 300;
        letter-spacing: 0.05em;
        margin-bottom: 3rem;
        animation: slideInRight 0.8s ease-out 0.1s both;
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
        position: relative;
        animation: slideInRight 0.6s ease-out;
    }
    
    .section-header::before {
        content: '▸';
        position: absolute;
        left: -0.3rem;
        color: var(--accent-cyan);
        animation: pulse 2s ease-in-out infinite;
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: var(--accent-cyan);
        text-shadow: 0 0 10px var(--glow);
    }
    
    [data-testid="stMetricLabel"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
    }
    
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, var(--secondary-dark) 0%, rgba(19, 24, 41, 0.5) 100%);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 212, 255, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.05);
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
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .stButton > button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 212, 255, 0.5);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* DataFrames */
    [data-testid="stDataFrame"] {
        font-family: 'JetBrains Mono', monospace;
        background: var(--secondary-dark);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    
    [data-testid="stDataFrame"] th {
        background: linear-gradient(180deg, #1a1f2e 0%, #131829 100%);
        color: var(--accent-amber);
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        border-bottom: 2px solid var(--accent-cyan);
    }
    
    [data-testid="stDataFrame"] td {
        color: var(--text-primary);
        border-color: var(--border-color);
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        font-family: 'JetBrains Mono', monospace;
        background: var(--secondary-dark);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        color: var(--text-primary);
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-cyan);
        box-shadow: 0 0 0 2px var(--glow);
    }
    
    /* Selectbox & Radio */
    .stSelectbox > div > div > div,
    .stRadio > div {
        font-family: 'JetBrains Mono', monospace;
        background: var(--secondary-dark);
        border-color: var(--border-color);
        color: var(--text-primary);
    }
    
    /* Alerts */
    .stAlert {
        font-family: 'JetBrains Mono', monospace;
        background: var(--secondary-dark);
        border-left: 4px solid var(--accent-cyan);
        border-radius: 6px;
        color: var(--text-primary);
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    }
    
    .stSuccess {
        border-left-color: var(--accent-green);
    }
    
    .stWarning {
        border-left-color: var(--accent-amber);
    }
    
    .stError {
        border-left-color: var(--accent-red);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1321 0%, #0a0e1a 100%);
        border-right: 1px solid var(--border-color);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: var(--text-primary);
    }
    
    /* File Uploader */
    [data-testid="stFileUploader"] {
        background: var(--secondary-dark);
        border: 2px dashed var(--border-color);
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: var(--accent-cyan);
        background: rgba(0, 212, 255, 0.05);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        background: var(--secondary-dark);
        border: 1px solid var(--border-color);
        border-radius: 6px 6px 0 0;
        color: var(--text-secondary);
        padding: 0.75rem 1.5rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(180deg, var(--accent-cyan) 0%, #0099cc 100%);
        color: var(--primary-dark);
        border-color: var(--accent-cyan);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: var(--accent-cyan);
        animation: spin 1s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
    }
    
    /* Download Button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--accent-green) 0%, #10ac84 100%);
        color: white;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 15px rgba(29, 209, 161, 0.3);
    }
    
    .stDownloadButton > button:hover {
        box-shadow: 0 6px 25px rgba(29, 209, 161, 0.5);
    }
    
    /* Markdown Content */
    .stMarkdown {
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-primary);
    }
    
    .stMarkdown code {
        background: var(--secondary-dark);
        color: var(--accent-amber);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        padding: 0.2rem 0.4rem;
        font-size: 0.9rem;
    }
    
    /* Info Box */
    .stInfo {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 153, 204, 0.1) 100%);
        border-left: 4px solid var(--accent-cyan);
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Horizontal Rule */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
        margin: 2rem 0;
        animation: slideInRight 1s ease-out;
    }
    
    /* Chart Containers */
    .js-plotly-plot {
        background: var(--secondary-dark) !important;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Custom Animation Classes */
    .animate-on-load {
        animation: slideInRight 0.8s ease-out;
    }
    
    /* Terminal-like text effect */
    .terminal-text {
        font-family: 'JetBrains Mono', monospace;
        color: var(--accent-cyan);
        text-shadow: 0 0 5px var(--glow);
        letter-spacing: 0.02em;
    }
    </style>
    """, unsafe_allow_html=True)

# Title
st.markdown('<p class="main-header">🎯 AI-Augmented Deal Evaluation Pipeline</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Complete PE workflow: Upload → Analyze → Model → Generate IC Memo</p>', unsafe_allow_html=True)

# Check API availability
api_available = check_api_key_available()

if not api_available:
    st.warning("⚠️ **OpenAI API key not configured.** AI features (risk analysis & IC memo) will be disabled. Add your key to `.env` to enable.")

# Header with terminal aesthetic
st.markdown('''
    <div class="main-header">⬢ DEAL.EVAL v2.1</div>
    <div class="sub-header">
        <span class="terminal-text">→</span> INGEST 
        <span class="terminal-text">→</span> ANALYZE 
        <span class="terminal-text">→</span> CALIBRATE 
        <span class="terminal-text">→</span> MODEL 
        <span class="terminal-text">→</span> SYNTHESIZE
    </div>
    ''', unsafe_allow_html=True)

# Initialize session state
if 'data_uploaded' not in st.session_state:
    st.session_state.data_uploaded = False
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = None
if 'historical_summary' not in st.session_state:
    st.session_state.historical_summary = None
if 'model_ran' not in st.session_state:
    st.session_state.model_ran = False

# Sidebar - Company Info
st.sidebar.markdown('<div class="terminal-text" style="font-size: 1.1rem; margin-bottom: 1rem;">◉ DEAL.CONFIG</div>', unsafe_allow_html=True)
company_name = st.sidebar.text_input(
    "Company Name",
    value="Target Co.",
    help="Name of the target company"
)

st.sidebar.markdown("---")

# ============================================================================
# SECTION 1: UPLOAD & ANALYZE HISTORICAL FINANCIALS
# ============================================================================
st.markdown('<p class="section-header">◢ INGEST: Historical Financials</p>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("**Upload CSV with historical financial data**")
    st.markdown("Required columns: `Year`, `Revenue`, `EBITDA` (Optional: `Capex`, `NetDebt`)")
    
    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type=['csv'],
        help="Upload historical financials (min 3 years recommended)"
    )

with col2:
    st.markdown("**Or use sample data**")
    if st.button("⬢ LOAD.SAMPLE", width="stretch"):
        sample_csv = create_sample_csv()
        uploaded_file = io.StringIO(sample_csv)
        st.session_state.use_sample = True

# Process uploaded file
if uploaded_file is not None:
    with st.spinner("Processing data..."):
        ingestion = FinancialDataIngestion()
        cleaned_data, warnings = ingestion.ingest_csv(uploaded_file)
        
        if cleaned_data is not None:
            st.session_state.data_uploaded = True
            st.session_state.historical_data = cleaned_data
            
            # Show warnings
            if warnings:
                st.warning("**Data Validation Warnings:**")
                for warning in warnings:
                    st.markdown(f"- {warning}")
            else:
                st.success("✅ **[VALIDATED]** Data ingestion complete. Proceeding to analysis phase.")
            
            # Display data
            st.markdown('<div class="terminal-text" style="font-size: 0.9rem; margin-top: 1.5rem; margin-bottom: 0.5rem;">// HISTORICAL.DATA</div>', unsafe_allow_html=True)
            st.dataframe(cleaned_data, width="stretch")
            
            # Run historical analysis
            analyzer = HistoricalAnalyzer(cleaned_data)
            historical_summary = analyzer.get_full_summary()
            st.session_state.historical_summary = historical_summary
            
            # Display historical metrics
            st.markdown('<div class="terminal-text" style="font-size: 0.9rem; margin-top: 2rem; margin-bottom: 1rem;">// PERFORMANCE.METRICS</div>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Revenue CAGR",
                    format_metric(historical_summary.get('revenue_cagr'), 'percentage')
                )
                st.metric(
                    "EBITDA CAGR",
                    format_metric(historical_summary.get('ebitda_cagr'), 'percentage')
                )
            
            with col2:
                st.metric(
                    "Avg EBITDA Margin",
                    format_metric(historical_summary.get('avg_margin', 0) / 100, 'percentage')
                )
                st.metric(
                    "Margin Volatility",
                    format_metric(historical_summary.get('margin_volatility', 0) / 100, 'percentage')
                )
            
            with col3:
                st.metric(
                    "Revenue Growth Range",
                    f"{format_metric(historical_summary.get('revenue_growth_min'), 'percentage')} to {format_metric(historical_summary.get('revenue_growth_max'), 'percentage')}"
                )
                st.metric(
                    "Margin Trend",
                    historical_summary.get('margin_trend', 'N/A').title()
                )
            
            with col4:
                st.metric(
                    "Years of Data",
                    historical_summary.get('years_of_data', 0)
                )
                st.metric(
                    "Data Period",
                    f"{historical_summary.get('start_year', 'N/A')} - {historical_summary.get('end_year', 'N/A')}"
                )
        
        else:
            st.error("❌ Failed to process data. Please check the file format and warnings above.")

# ============================================================================
# SECTION 2: CONFIGURE LBO ASSUMPTIONS
# ============================================================================
if st.session_state.data_uploaded:
    st.markdown("---")
    st.markdown('<p class="section-header">◢ CALIBRATE: LBO Assumptions</p>', unsafe_allow_html=True)
    
    # Get calibrated assumptions
    analyzer = HistoricalAnalyzer(st.session_state.historical_data)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown('<div class="terminal-text" style="font-size: 0.9rem; margin-bottom: 1rem;">// CALIBRATION.MODE</div>', unsafe_allow_html=True)
        growth_mode = st.radio(
            "Select mode:",
            options=['base', 'conservative', 'optimistic', 'manual'],
            format_func=lambda x: {
                'base': '◉ Base (Historical CAGR)',
                'conservative': '◉ Conservative (CAGR - 1σ)',
                'optimistic': '◉ Optimistic (CAGR + 0.5σ)',
                'manual': '◉ Manual Override'
            }[x],
            help="Select how to calibrate forward growth assumptions"
        )
        
        if growth_mode != 'manual':
            calibrated = analyzer.get_calibrated_assumptions(mode=growth_mode)
            st.info(f"**⬢ Suggested Growth:** {format_metric(calibrated['forward_growth_rate'], 'percentage')}")
            st.caption(f"Confidence: {calibrated['confidence'].upper()}")
    
    with col2:
        st.markdown('<div class="terminal-text" style="font-size: 0.9rem; margin-bottom: 1rem;">// MODEL.PARAMETERS</div>', unsafe_allow_html=True)
        
        # Get latest EBITDA for default
        latest_ebitda = st.session_state.historical_data['ebitda'].iloc[-1]
        
        col2a, col2b, col2c = st.columns(3)
        
        with col2a:
            entry_ebitda = st.number_input(
                "Entry EBITDA (€M)",
                min_value=0.1,
                max_value=10000.0,
                value=float(latest_ebitda),
                step=0.5,
                help="Latest or projected LTM EBITDA"
            )
            
            entry_multiple = st.number_input(
                "Entry Multiple (EV/EBITDA)",
                min_value=1.0,
                max_value=30.0,
                value=10.0,
                step=0.5
            )
            
            debt_to_ebitda = st.number_input(
                "Debt-to-EBITDA",
                min_value=0.0,
                max_value=10.0,
                value=3.0,
                step=0.5
            )
        
        with col2b:
            interest_rate_pct = st.number_input(
                "Interest Rate (%)",
                min_value=0.0,
                max_value=20.0,
                value=8.0,
                step=0.5
            )
            
            # Auto-populate growth based on mode
            if growth_mode != 'manual':
                calibrated = analyzer.get_calibrated_assumptions(mode=growth_mode)
                default_growth = calibrated['forward_growth_rate'] * 100
            else:
                default_growth = 5.0
            
            growth_rate_pct = st.number_input(
                "EBITDA Growth Rate (% p.a.)",
                min_value=-20.0,
                max_value=50.0,
                value=float(default_growth),
                step=1.0,
                disabled=(growth_mode != 'manual')
            )
            
            holding_period_years = st.number_input(
                "Holding Period (years)",
                min_value=1,
                max_value=15,
                value=5,
                step=1
            )
        
        with col2c:
            exit_multiple = st.number_input(
                "Exit Multiple (EV/EBITDA)",
                min_value=1.0,
                max_value=30.0,
                value=10.0,
                step=0.5
            )
    
    # Convert percentages
    interest_rate = safe_percentage_input(interest_rate_pct)
    growth_rate = safe_percentage_input(growth_rate_pct)
    
    # Validate inputs
    is_valid, error_message = validate_model_inputs(
        entry_ebitda,
        entry_multiple,
        debt_to_ebitda,
        interest_rate,
        growth_rate,
        holding_period_years,
        exit_multiple
    )
    
    if not is_valid:
        st.error(f"❌ {error_message}")
    
    # ============================================================================
    # SECTION 3: RUN LBO MODEL
    # ============================================================================
    st.markdown("---")
    st.markdown('<p class="section-header">◢ MODEL: LBO Analysis</p>', unsafe_allow_html=True)
    
    run_model = st.button("▸ EXECUTE.MODEL", type="primary", width="stretch")
    
    if run_model and is_valid:
        with st.spinner("Running LBO model..."):
            # Create model
            model = LBOModel(
                entry_ebitda=entry_ebitda,
                entry_multiple=entry_multiple,
                debt_to_ebitda=debt_to_ebitda,
                interest_rate=interest_rate,
                growth_rate=growth_rate,
                holding_period_years=holding_period_years,
                exit_multiple=exit_multiple
            )
            
            # Get results
            base_case = model.get_base_case_summary()
            st.session_state.base_case = base_case
            
            # Sensitivity analysis
            sensitivity_grids = build_sensitivity_grid(
                entry_ebitda=entry_ebitda,
                entry_multiple=entry_multiple,
                debt_to_ebitda=debt_to_ebitda,
                interest_rate=interest_rate,
                holding_period_years=holding_period_years
            )
            st.session_state.sensitivity_grids = sensitivity_grids
            
            sens_summary = summarize_sensitivity(sensitivity_grids)
            st.session_state.sens_summary = sens_summary
            
            # Store inputs
            st.session_state.model_inputs = {
                'entry_ebitda': entry_ebitda,
                'entry_multiple': entry_multiple,
                'debt_to_ebitda': debt_to_ebitda,
                'interest_rate': interest_rate,
                'growth_rate': growth_rate,
                'holding_period_years': holding_period_years,
                'exit_multiple': exit_multiple
            }
            
            st.session_state.model_ran = True
            st.success("✅ LBO model complete!")
    
    # Display results if model has been run
    if st.session_state.model_ran:
        base_case = st.session_state.base_case
        
        st.markdown('<div class="terminal-text" style="font-size: 0.9rem; margin-top: 2rem; margin-bottom: 1rem;">// TRANSACTION.STRUCTURE</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Entry EV", format_currency(base_case['entry_ev']))
        with col2:
            st.metric("Debt", format_currency(base_case['debt']))
        with col3:
            st.metric("Equity", format_currency(base_case['equity']))
        with col4:
            st.metric("Exit EV", format_currency(base_case['exit_ev']))
        with col5:
            st.metric("Exit Equity", format_currency(base_case['exit_equity_value']))
        
        st.markdown("---")
        
        # Returns
        st.markdown('<div class="terminal-text" style="font-size: 0.9rem; margin-top: 2rem; margin-bottom: 1rem;">// BASE.RETURNS</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            irr_val = base_case['irr']
            if irr_val is not None:
                st.metric("Equity IRR", f"{irr_val:.1f}%", delta=None)
            else:
                st.metric("Equity IRR", "N/A")
        
        with col2:
            moic_val = base_case['moic']
            if moic_val is not None:
                st.metric("Equity MOIC", format_multiple(moic_val))
            else:
                st.metric("Equity MOIC", "N/A")
        
        with col3:
            st.metric("Debt/EBITDA", format_multiple(base_case['debt_to_ebitda']))
        
        with col4:
            st.metric("Growth Rate", format_percentage(base_case['growth_rate']))
        
        # Sensitivity tables
        st.subheader("🎯 Sensitivity Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**IRR Sensitivity (Growth vs Exit Multiple)**")
            irr_grid = st.session_state.sensitivity_grids['irr_grid'].copy()
            for col in irr_grid.columns:
                irr_grid[col] = irr_grid[col].apply(
                    lambda x: f"{x:.1f}%" if x is not None and not pd.isna(x) else "N/A"
                )
            st.dataframe(irr_grid, width="stretch")
        
        with col2:
            st.markdown("**MOIC Sensitivity (Growth vs Exit Multiple)**")
            moic_grid = st.session_state.sensitivity_grids['moic_grid'].copy()
            for col in moic_grid.columns:
                moic_grid[col] = moic_grid[col].apply(
                    lambda x: f"{x:.2f}x" if x is not None and not pd.isna(x) else "N/A"
                )
            st.dataframe(moic_grid, width="stretch")
        
        # Sensitivity summary
        sens_summary = st.session_state.sens_summary
        st.info(f"""
        **Sensitivity Summary:**  
        IRR Range: {sens_summary['irr_min']:.1f}% to {sens_summary['irr_max']:.1f}% (spread: {sens_summary['irr_range']:.1f}pp)  
        MOIC Range: {sens_summary['moic_min']:.2f}x to {sens_summary['moic_max']:.2f}x (spread: {sens_summary['moic_range']:.2f}x)
        """)
        
        # ============================================================================
        # SECTION 4: GENERATE IC MEMO
        # ============================================================================
        st.markdown("---")
        st.markdown('<p class="section-header">◢ SYNTHESIZE: IC Memo Generation</p>', unsafe_allow_html=True)
        
        if not api_available:
            st.warning("⚠️ OpenAI API key not configured. IC memo generation is unavailable.")
        else:
            st.markdown("**AI will generate a professional IC memo based on your analysis.**")
            
            memo_focus = st.text_area(
                "Optional: Special instructions for the memo",
                placeholder="e.g., 'emphasize operational risks', 'conservative tone for risk committee', 'highlight margin improvement opportunity'",
                height=100
            )
            
            col1, col2 = st.columns([1, 4])
            
            with col1:
                generate_memo = st.button("⬢ SYNTHESIZE.MEMO", type="primary", width="stretch")
            
            if generate_memo:
                with st.spinner("🤖 AI is generating your Investment Committee memo..."):
                    try:
                        memo_gen = MemoGenerator()
                        
                        memo = memo_gen.generate_ic_memo(
                            company_name=company_name,
                            historical_summary=st.session_state.historical_summary,
                            lbo_inputs=st.session_state.model_inputs,
                            lbo_outputs=st.session_state.base_case,
                            sensitivities=st.session_state.sens_summary,
                            user_focus=memo_focus if memo_focus else None
                        )
                        
                        st.session_state.ic_memo = memo
                        st.success("✅ IC Memo generated successfully!")
                    
                    except Exception as e:
                        st.error(f"❌ Error generating memo: {str(e)}")
            
            # Display memo if available
            if 'ic_memo' in st.session_state:
                st.markdown("---")
                st.subheader("📄 Investment Committee Memo")
                
                # Display the memo
                st.markdown(st.session_state.ic_memo)
                
                # Download button
                st.markdown("---")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{company_name.replace(' ', '_')}_IC_Memo_{timestamp}.md"
                
                st.download_button(
                    label="⬇️ Download Memo (Markdown)",
                    data=st.session_state.ic_memo,
                    file_name=filename,
                    mime="text/markdown",
                    width="stretch"
                )

else:
    st.info("👆 Upload historical financial data to begin the deal evaluation process.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    <p><strong>AI-Augmented Deal Evaluation Pipeline</strong> | Professional PE Workflow Automation</p>
    <p>Historical Analysis → LBO Modeling → IC Memo Generation</p>
</div>
""", unsafe_allow_html=True)
