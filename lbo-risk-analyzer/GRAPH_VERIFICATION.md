# Graph Issue Checklist

## ✅ Repository Cleanup: COMPLETE

All deprecated files have been removed. Current structure:

```
lbo-risk-analyzer/
├── app.py                      ✅ Main entry point
├── requirements.txt
├── run_app.sh
├── README.md
├── REFACTOR_SUMMARY.md
├── .env / .env.example
│
├── src/                        ✅ Source package
│   ├── __init__.py
│   ├── data/                   ✅ 3 files
│   │   ├── __init__.py
│   │   ├── ingestion.py
│   │   └── historical_analysis.py
│   ├── models/                 ✅ 6 files
│   │   ├── __init__.py
│   │   ├── capital_structure.py
│   │   ├── operating_model.py
│   │   ├── debt_model.py
│   │   ├── exit_model.py
│   │   └── lbo_engine.py
│   ├── analysis/               ✅ 3 files
│   │   ├── __init__.py
│   │   ├── scoring.py
│   │   └── risk_analyzer.py
│   ├── reporting/              ✅ 5 files
│   │   ├── __init__.py
│   │   ├── charts.py
│   │   ├── memo_generator.py
│   │   ├── ic_report_generator.py
│   │   └── pdf_exporter.py
│   └── utils/                  ✅ 2 files
│       ├── __init__.py
│       └── formatters.py
│
└── tests/                      ✅ Test suite
    ├── __init__.py
    ├── smoke_test.py
    └── test_data/
        └── sample_financials.csv
```

**Total**: 23 Python files, all properly organized

---

## 🔍 Graph Issue Troubleshooting

### Expected Behavior
When generating an IC report, 6 chart types should be created:
1. Revenue projection line chart
2. EBITDA projection line chart
3. Debt schedule bar chart
4. Leverage ratio line chart
5. Sensitivity heatmap (if sensitivity analysis run)
6. Contribution waterfall (optional)

### Verification Steps

#### 1. Check App is Running
```bash
# App should be at:
http://localhost:8501
```
✅ **Status**: Running

#### 2. Test Chart Generation Directly
Run the smoke test to verify charts work:
```bash
cd /Users/arthur/Documents/Job\ Research/Entretiens/Athvance/LBOsensitivityanalyzer/lbo-risk-analyzer
/Users/arthur/Documents/Job\ Research/Entretiens/Athvance/LBOsensitivityanalyzer/.venv/bin/python tests/smoke_test.py
```

Look for:
```
🧪 Testing chart generation...
  Generated 3 charts
✅ Chart generation test passed
```

#### 3. Check Chart Module Import
The app should import charts like this:
```python
from src.reporting import charts

# Usage:
chart_paths['revenue'] = charts.create_revenue_projection_chart(revenue_df)
```

#### 4. Verify Chart Functions Exist
```bash
grep -n "def create_" src/reporting/charts.py
```

Should show:
- `create_revenue_projection_chart`
- `create_ebitda_projection_chart`
- `create_debt_schedule_chart`
- `create_leverage_chart`
- `create_sensitivity_heatmap`
- `create_contribution_waterfall`

#### 5. Test in UI

**Step-by-step**:
1. Open http://localhost:8501
2. Click "⬢ LOAD.SAMPLE" button
3. Scroll to "◢ EXECUTE: LBO Analysis"
4. Click "▸ RUN.FULL.MODEL"
5. Wait for results to display
6. Scroll to "◢ SYNTHESIZE: IC Report" section
7. Add some text in Business Information (optional)
8. Click "⬢ GENERATE.REPORT"

**What to look for**:
- "📈 Generating financial charts..." message
- Charts should embed as base64 images in the report
- If no API key: report still generates with placeholder structure
- If API key: full AI-generated report with charts

---

## 🐛 Common Issues & Fixes

### Issue 1: "No module named 'src'"
**Cause**: Python path issue
**Fix**: Run from the lbo-risk-analyzer directory
```bash
cd /Users/arthur/Documents/Job\ Research/Entretiens/Athvance/LBOsensitivityanalyzer/lbo-risk-analyzer
DYLD_LIBRARY_PATH=/opt/homebrew/lib streamlit run app.py
```

### Issue 2: Charts not displaying in report
**Symptoms**: Report generates but no images shown
**Possible causes**:
1. Chart generation failed (check terminal for errors)
2. Chart placeholders not in template
3. Base64 encoding issue

**Debug**:
```python
# In app.py, add after chart generation:
print(f"Chart paths: {list(chart_paths.keys())}")
print(f"Revenue chart length: {len(chart_paths.get('revenue', ''))}")
```

### Issue 3: "ModuleNotFoundError: No module named 'matplotlib'"
**Cause**: Missing dependency
**Fix**:
```bash
/Users/arthur/Documents/Job\ Research/Entretiens/Athvance/LBOsensitivityanalyzer/.venv/bin/pip install matplotlib
```

### Issue 4: Report generates but is very short
**Cause**: OpenAI API key not set or invalid
**Expected**: Report should be >4000 chars with fallback template
**Fix**: Check .env file has valid OPENAI_API_KEY

---

## ✅ Quick Verification Script

Run this to test everything:

```bash
#!/bin/bash
cd /Users/arthur/Documents/Job\ Research/Entretiens/Athvance/LBOsensitivityanalyzer/lbo-risk-analyzer

echo "1. Testing smoke tests..."
/Users/arthur/Documents/Job\ Research/Entretiens/Athvance/LBOsensitivityanalyzer/.venv/bin/python tests/smoke_test.py

if [ $? -eq 0 ]; then
    echo "✅ Smoke tests PASSED"
else
    echo "❌ Smoke tests FAILED"
    exit 1
fi

echo ""
echo "2. Checking chart module..."
python3 -c "from src.reporting import charts; print('✅ Charts module imports correctly')"

echo ""
echo "3. Listing chart functions..."
grep "^def create_" src/reporting/charts.py

echo ""
echo "4. App is running at: http://localhost:8501"
echo ""
echo "Manual test: Generate a report and check for charts"
```

---

## 📊 Expected Chart Output

When you generate an IC report, you should see these in the markdown:

```markdown
## Financial Projections

{{chart:revenue}}

## EBITDA Performance

{{chart:ebitda}}

## Debt Paydown Schedule

{{chart:debt}}

## Leverage Profile

{{chart:leverage}}

## Sensitivity Analysis

{{chart:sensitivity}}
```

These placeholders get replaced with:
```html
<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA..." style="max-width: 100%; height: auto; margin: 20px 0;" />
```

---

## 🔬 Debug Mode

To see detailed chart generation output, add this to `app.py` after chart generation:

```python
# Step 2: Generate Charts
st.info("📈 Generating financial charts...")
chart_paths = {}

# Revenue projection chart
revenue_df = results['operating_projection'][['year', 'revenue']].copy()
chart_paths['revenue'] = charts.create_revenue_projection_chart(revenue_df)
st.write(f"DEBUG: Revenue chart size: {len(chart_paths['revenue'])} bytes")  # ADD THIS

# ... repeat for each chart
```

---

## 🎯 Current Status

✅ Repository cleaned and organized  
✅ All imports updated to src.* pattern  
✅ Smoke tests passing  
✅ App running at http://localhost:8501  
⏳ **Awaiting manual verification**: Generate a report and check charts display

---

## 📝 Next Steps

1. Open the app in browser: http://localhost:8501
2. Load sample data
3. Run the model
4. Generate IC report
5. Verify charts appear in the report
6. If charts missing, check terminal output for errors
7. Report findings

---

**Last Updated**: February 13, 2026  
**App Status**: ✅ Running  
**Repo Status**: ✅ Clean
