# LBO Risk Analyzer - Deal Evaluation Pipeline

⬢ **DEAL.EVAL v3.0** | Advanced LBO Modeling Engine with IC Report Generation

A professional-grade LBO modeling and analysis platform for private equity deal evaluation, featuring:
- Complete operating model with full P&L projection
- Debt waterfall with amortization and cash sweep
- Multiple exit methodologies (fixed, mean reversion, growth-adjusted)
- Sensitivity analysis for risk assessment
- AI-powered Investment Committee (IC) report generation
- Professional PDF export with embedded charts

---

## 🎯 Features

### Core LBO Model
- **Historical Analysis**: CAGR calculations, margin analysis, volatility assessment
- **Sources & Uses**: Complete transaction structuring with fees
- **Operating Model**: Revenue → EBITDA → NOPAT → FCF projections
- **Debt Schedule**: Interest, amortization, and optional cash sweep
- **Exit Mechanics**: Multiple exit valuation methodologies
- **Returns Calculation**: IRR and MOIC with contribution analysis

### Advanced Analytics
- **Sensitivity Analysis**: 2D grids varying growth rates and exit multiples
- **Risk Scoring**: 0-100 IC score based on returns, leverage, and downside protection
- **Contribution Analysis**: Break down returns by EBITDA growth, multiple expansion, and deleveraging

### Reporting & Export
- **AI Report Generation**: Structured IC memos with OpenAI integration
- **Chart Generation**: 6 chart types (revenue, EBITDA, debt, leverage, sensitivity, contribution)
- **PDF Export**: Professional reports with embedded visualizations
- **Custom Instructions**: User-guided report focus areas

---

## 📁 Project Structure

```
lbo-risk-analyzer/
├── app.py                          # Main Streamlit application (entry point)
├── requirements.txt                 # Python dependencies
├── run_app.sh                      # Launch script with library paths
├── .env.example                    # Environment variable template
├── README.md                       # This file
│
├── src/                            # Source code package
│   ├── __init__.py                 # Package initialization
│   │
│   ├── data/                       # Data ingestion and analysis
│   │   ├── __init__.py
│   │   ├── ingestion.py            # CSV parsing and validation
│   │   └── historical_analysis.py  # Historical metrics calculation
│   │
│   ├── models/                     # Financial modeling components
│   │   ├── __init__.py
│   │   ├── capital_structure.py    # Sources & Uses calculation
│   │   ├── operating_model.py      # P&L projections
│   │   ├── debt_model.py           # Debt schedule and paydown
│   │   ├── exit_model.py           # Exit valuation methodologies
│   │   └── lbo_engine.py           # Main orchestrator
│   │
│   ├── analysis/                   # Analytical tools
│   │   ├── __init__.py
│   │   ├── scoring.py              # IC scoring system
│   │   └── risk_analyzer.py        # Risk assessment and API utilities
│   │
│   ├── reporting/                  # Report generation
│   │   ├── __init__.py
│   │   ├── charts.py               # Chart generation (matplotlib)
│   │   ├── memo_generator.py       # Legacy memo generator
│   │   ├── ic_report_generator.py  # IC report with AI
│   │   └── pdf_exporter.py         # PDF rendering (WeasyPrint)
│   │
│   └── utils/                      # Utilities
│       ├── __init__.py
│       └── formatters.py           # Format helpers and validation
│
└── tests/                          # Test suite
    ├── __init__.py
    ├── smoke_test.py               # End-to-end validation
    └── test_data/
        └── sample_financials.csv   # Test dataset
```

---

## 🚀 Installation

### Prerequisites
- **Python 3.9+**
- **Homebrew** (macOS) for system dependencies
- **OpenAI API Key** (optional, for AI report generation)

### System Dependencies (macOS)
```bash
brew install pango gdk-pixbuf libffi
```

### Python Setup
```bash
# Clone/navigate to project
cd lbo-risk-analyzer

# Create virtual environment
python3 -m venv ../.venv

# Activate virtual environment
source ../.venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key (optional)
# OPENAI_API_KEY=sk-...
```

---

## 💻 Usage

### Quick Start
```bash
# Using the launch script (recommended)
chmod +x run_app.sh
./run_app.sh

# Or manually
DYLD_LIBRARY_PATH=/opt/homebrew/lib streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

### Workflow

1. **INGEST**: Upload historical financials CSV or load sample data
   - Required columns: `year`, `revenue`, `ebitda`
   - System calculates CAGRs and margins

2. **STRUCTURE**: Configure transaction parameters
   - Entry EBITDA and multiple
   - Debt/EBITDA ratio
   - Transaction and financing fees

3. **OPERATE**: Set operating assumptions
   - Hold period (3-7 years)
   - Revenue growth rate
   - EBITDA margin, tax rate, capex, etc.

4. **LEVERAGE**: Define debt structure
   - Interest rate
   - Amortization schedule
   - Cash sweep (optional)

5. **EXIT**: Choose exit methodology
   - Fixed multiple
   - Mean reversion to industry
   - Growth-adjusted

6. **EXECUTE**: Run LBO model
   - View Sources & Uses
   - Operating projections
   - Debt schedule
   - Exit summary

7. **SENSITIVITY**: Run scenario analysis
   - Vary growth and exit multiple
   - Generate IRR and MOIC grids

8. **SYNTHESIZE**: Generate IC report (requires API key)
   - Add business context and thesis
   - Optional custom instructions
   - Export as Markdown or PDF

---

## 🧪 Testing

### Run Smoke Tests
```bash
python tests/smoke_test.py
```

Tests validate:
- ✅ Data ingestion and historical analysis
- ✅ Full LBO model execution
- ✅ IC scoring calculation
- ✅ Chart generation
- ✅ Contribution analysis
- ✅ Report generation
- ✅ Utility formatters

---

## 🔧 Configuration

### PDF Export
PDF generation requires system libraries. On macOS:
```bash
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH
```

This is automatically set by `run_app.sh`.

### AI Report Generation
Set `OPENAI_API_KEY` in `.env` file. Without API key:
- Base model calculations still work
- Manual report export available
- AI synthesis features disabled with warning

---

## 📊 Model Details

### Capital Structure
- Enterprise Value = Entry EBITDA × Entry Multiple
- Debt = Entry EBITDA × Debt/EBITDA ratio
- Equity = EV - Debt + Fees + Cash

### Operating Model
```
Revenue (t) = Revenue (t-1) × (1 + Growth Rate)
EBITDA = Revenue × EBITDA Margin
EBIT = EBITDA - D&A
NOPAT = EBIT × (1 - Tax Rate)
FCF = NOPAT + D&A - Capex - ΔNW C
```

### Debt Waterfall
```
Beginning Debt (t) = Ending Debt (t-1)
Interest = Beginning Debt × Interest Rate
Scheduled Amortization = Initial Debt × Amortization %
Cash Sweep = max(0, FCF × Sweep %) if enabled
Ending Debt = Beginning Debt - Scheduled Amort - Cash Sweep
```

### Exit Valuation
- **Fixed**: Exit Multiple = User Input
- **Mean Reversion**: Weighted avg of entry and industry multiples
- **Growth-Adjusted**: Multiple adjusted by revenue growth rate

### IC Scoring (0-100 scale)
- **IRR Performance** (30%): Base case and downside IRR
- **Downside Protection** (25%): Minimum sensitivity IRR
- **Leverage Profile** (20%): Peak Debt/EBITDA
- **Coverage Ratios** (15%): Minimum interest coverage
- **EBITDA Stability** (10%): Historical volatility

---

## 🎨 UI Design

**Bloomberg Terminal Aesthetic**
- Dark gradient background (#0a0e1a → #131829)
- Cyan/Amber accent colors
- JetBrains Mono (monospace) + Fraunces (serif) fonts
- Animated transitions and hover effects
- Terminal-inspired section headers

---

## 🔒 Safety & Constraints

- **No breaking changes**: All computations remain deterministic
- **API optional**: App runs without OpenAI key (reporting disabled)
- **Error handling**: Graceful degradation for missing inputs
- **Validation**: Input bounds and data quality checks
- **Type safety**: Dataclasses for structured inputs

---

## 📝 File Actions (Refactor Summary)

### Created
- `src/` package structure with 5 subdirectories
- `src/__init__.py` - Package version 2.0.0
- `src/data/__init__.py` - Data module exports
- `src/models/__init__.py` - Model exports
- `src/analysis/__init__.py` - Analysis exports
- `src/reporting/__init__.py` - Reporting exports
- `src/utils/__init__.py` - Utility exports
- `tests/smoke_test.py` - Comprehensive test suite
- `tests/test_data/sample_financials.csv` - Test dataset
- `README.md` - This documentation

### Modified
- `app.py` - Consolidated from app_advanced.py with updated imports
- `run_app.sh` - Updated to run new app.py
- `src/models/lbo_engine.py` - Relative imports within package

### Moved
- All business logic modules → `src/` subdirectories:
  - `ingestion.py` → `src/data/`
  - `historical_analysis.py` → `src/data/`
  - `capital_structure.py` → `src/models/`
  - `operating_model.py` → `src/models/`
  - `debt_model.py` → `src/models/`
  - `exit_model.py` → `src/models/`
  - `lbo_engine.py` → `src/models/`
  - `scoring.py` → `src/analysis/`
  - `risk_analyzer.py` → `src/analysis/`
  - `charts.py` → `src/reporting/`
  - `memo_generator.py` → `src/reporting/`
  - `ic_report_generator.py` → `src/reporting/`
  - `pdf_exporter.py` → `src/reporting/`
  - `utils.py` → `src/utils/formatters.py`

### To Delete (after verification)
- `app_old.py` - Old version
- `app_advanced.py` - Consolidated into app.py
- `app_full.py` - Deprecated version
- `lbo.py` - Old monolithic model
- Root-level module files (after src/ is confirmed working)

---

## 🚧 Future Enhancements

- [ ] Add unit tests for individual components
- [ ] Support multiple debt tranches (senior, mezzanine)
- [ ] Add working capital bridge analysis
- [ ] Implement Monte Carlo simulation for risk analysis
- [ ] Add comp table scraping and benchmarking
- [ ] Export to Excel with live formulas
- [ ] Multi-currency support

---

## 📄 License

Proprietary - For demonstration and interview purposes.

---

## 👤 Author

**Arthur** - Athvance Interview Project
- Private Equity LBO Modeling Platform
- Built with Streamlit, Python 3.13, OpenAI GPT-4

---

## 📞 Support

For questions or issues:
1. Check the smoke test: `python tests/smoke_test.py`
2. Verify library paths: `echo $DYLD_LIBRARY_PATH`
3. Check API key: `cat .env | grep OPENAI_API_KEY`
4. Review logs in terminal output

---

**Last Updated**: February 2026  
**Version**: 3.0.0 (Post-Refactor)
