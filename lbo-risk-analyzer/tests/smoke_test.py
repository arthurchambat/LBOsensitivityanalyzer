"""
Smoke Test Suite - Validates core LBO functionality end-to-end
"""
import sys
from pathlib import Path

# Add parent directory to path to import src package
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.data import FinancialDataIngestion, get_sample_dataframe, HistoricalAnalyzer
from src.models import (
    CapitalStructureInputs,
    OperatingAssumptions,
    DebtAssumptions,
    ExitAssumptions,
    LBOEngine
)
from src.analysis import ICScoring, ScoringInputs, calculate_contribution_analysis
from src.reporting import charts, ICReportGenerator, PDFExporter
from src.utils import format_currency, format_percentage, format_multiple


def test_data_ingestion():
    """Test data ingestion and historical analysis"""
    print("🧪 Testing data ingestion...")
    
    # Get sample data
    df = get_sample_dataframe()
    assert df is not None, "Sample data should not be None"
    assert len(df) > 0, "Sample data should have rows"
    assert 'revenue' in df.columns, "Should have revenue column"
    assert 'ebitda' in df.columns, "Should have ebitda column"
    
    # Test historical analyzer
    analyzer = HistoricalAnalyzer(df)
    summary = analyzer.get_full_summary()
    assert 'revenue_cagr' in summary, "Should calculate revenue CAGR"
    assert 'ebitda_cagr' in summary, "Should calculate EBITDA CAGR"
    
    print("✅ Data ingestion test passed")


def test_lbo_model(df):
    """Test full LBO model execution"""
    print("🧪 Testing LBO model...")
    
    # Build inputs
    entry_ebitda = float(df['ebitda'].iloc[-1])
    base_revenue = float(df['revenue'].iloc[-1])
    
    capital_inputs = CapitalStructureInputs(
        entry_ebitda=entry_ebitda,
        entry_multiple=10.0,
        debt_to_ebitda=5.0,
        transaction_fee_pct=0.02,
        financing_fee_pct=0.03,
        cash_on_bs=0.0
    )
    
    operating_assumptions = OperatingAssumptions(
        base_revenue=base_revenue,
        revenue_growth_rates=[0.05] * 5,
        ebitda_margin=0.20,
        tax_rate=0.25,
        da_pct_revenue=0.03,
        capex_pct_revenue=0.03,
        nwc_pct_revenue=0.10
    )
    
    debt_assumptions = DebtAssumptions(
        initial_debt=0.0,
        interest_rate=0.06,
        amortization_pct=0.05,
        cash_sweep_enabled=True,
        cash_sweep_pct=0.50
    )
    
    exit_assumptions = ExitAssumptions(
        exit_mode='fixed',
        fixed_exit_multiple=10.0,
        entry_multiple=10.0,
        hold_period=5
    )
    
    # Run engine
    engine = LBOEngine(
        capital_inputs,
        operating_assumptions,
        debt_assumptions,
        exit_assumptions
    )
    
    results = engine.get_results()
    
    # Validate results
    assert results is not None, "Results should not be None"
    assert 'irr' in results, "Should have IRR"
    assert 'moic' in results, "Should have MOIC"
    assert 'operating_projection' in results, "Should have operating projection"
    assert 'debt_schedule' in results, "Should have debt schedule"
    assert 'leverage_ratios' in results, "Should have leverage ratios"
    
    print(f"  IRR: {format_percentage(results['irr'])}")
    print(f"  MOIC: {results['moic']:.2f}x")
    print("✅ LBO model test passed")
    
    return results


def test_scoring(results):
    """Test IC scoring system"""
    print("🧪 Testing IC scoring...")
    
    scoring_inputs = ScoringInputs(
        base_case_irr=results['irr'],
        min_sensitivity_irr=results['irr'] * 0.8,
        max_debt_to_ebitda=results['leverage_ratios']['debt_to_ebitda'].max(),
        min_interest_coverage=results['leverage_ratios']['interest_coverage'].min(),
        ebitda_growth_volatility=None
    )
    
    scorer = ICScoring(scoring_inputs)
    score_result = scorer.get_summary()
    
    assert 'total_score' in score_result, "Should have total score"
    assert 'risk_level' in score_result, "Should have risk level"
    assert 'component_scores' in score_result, "Should have component scores"
    
    print(f"  IC Score: {score_result['total_score']:.1f}/100")
    print(f"  Risk Level: {score_result['risk_level']}")
    print("✅ IC scoring test passed")
    
    return score_result


def test_charts(results):
    """Test chart generation"""
    print("🧪 Testing chart generation...")
    
    chart_paths = {}
    
    # Revenue chart
    revenue_df = results['operating_projection'][['year', 'revenue']].copy()
    chart_paths['revenue'] = charts.create_revenue_projection_chart(revenue_df)
    assert chart_paths['revenue'] is not None, "Revenue chart should be generated"
    
    # EBITDA chart
    ebitda_df = results['operating_projection'][['year', 'ebitda']].copy()
    chart_paths['ebitda'] = charts.create_ebitda_projection_chart(ebitda_df)
    assert chart_paths['ebitda'] is not None, "EBITDA chart should be generated"
    
    # Debt chart
    debt_df = results['debt_schedule'].reset_index()
    if 'Year' not in debt_df.columns and 'year' not in debt_df.columns:
        debt_df['year'] = range(1, len(debt_df) + 1)
    chart_paths['debt'] = charts.create_debt_schedule_chart(debt_df[['year', 'ending_debt']])
    assert chart_paths['debt'] is not None, "Debt chart should be generated"
    
    print(f"  Generated {len(chart_paths)} charts")
    print("✅ Chart generation test passed")
    
    return chart_paths


def test_contribution_analysis(results):
    """Test contribution analysis"""
    print("🧪 Testing contribution analysis...")
    
    # Calculate entry EBITDA from entry EV and multiple
    entry_ev = results['sources_uses']['enterprise_value']
    entry_multiple = 10.0
    entry_ebitda = entry_ev / entry_multiple
    
    contribution = calculate_contribution_analysis(
        entry_ev=entry_ev,
        exit_ev=results['exit_results']['exit_ev'],
        entry_debt=results['sources_uses']['debt'],
        exit_debt=results['debt_schedule']['ending_debt'].iloc[-1],
        entry_ebitda=entry_ebitda,
        exit_ebitda=results['operating_projection']['ebitda'].iloc[-1],
        entry_multiple=entry_multiple
    )
    
    assert 'ebitda_growth' in contribution, "Should have EBITDA growth contribution"
    assert 'multiple_expansion' in contribution, "Should have multiple expansion contribution"
    assert 'deleveraging' in contribution, "Should have deleveraging contribution"
    
    print(f"  EBITDA Growth: {contribution['ebitda_growth']:.1f}%")
    print(f"  Multiple Expansion: {contribution['multiple_expansion']:.1f}%")
    print(f"  Deleveraging: {contribution['deleveraging']:.1f}%")
    print("✅ Contribution analysis test passed")
    
    return contribution


def test_report_generation(results, score_result, contribution, chart_paths):
    """Test IC report generation"""
    print("🧪 Testing IC report generation...")
    
    # Calculate entry EBITDA from entry EV and multiple
    entry_ev = results['sources_uses']['enterprise_value']
    entry_multiple = 10.0
    entry_ebitda = entry_ev / entry_multiple
    
    financial_data = {
        'company_name': 'Test Co.',
        'industry': 'Business Services',
        'entry_ebitda': entry_ebitda,
        'entry_multiple': entry_multiple,
        'debt_to_ebitda': 5.0,
        'hold_period': 5,
        'revenue_growth': 0.05,
        'ebitda_margin': 0.20,
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
        'business_description': 'Test business description',
        'investment_thesis': 'Test investment thesis',
        'key_risks': 'Test key risks',
        'management_notes': 'Test management notes',
    }
    
    report_gen = ICReportGenerator()
    report_markdown = report_gen.generate_ic_report(
        financial_data=financial_data,
        business_context=business_context,
        scoring_summary=score_result,
        contribution_analysis=contribution,
        user_instructions=None
    )
    
    assert report_markdown is not None, "Report should not be None"
    assert len(report_markdown) > 100, "Report should have content"
    
    # Test chart embedding (if placeholders exist in report)
    chart_placeholders_found = False
    for chart_name in chart_paths.keys():
        placeholder = f"{{{{chart:{chart_name}}}}}"
        if placeholder in report_markdown:
            chart_placeholders_found = True
            break
    
    if chart_placeholders_found:
        for chart_name, chart_base64 in chart_paths.items():
            placeholder = f"{{{{chart:{chart_name}}}}}"
            img_tag = f'<img src="data:image/png;base64,{chart_base64}"'
            report_markdown = report_markdown.replace(placeholder, img_tag)
        
        # Check charts were embedded
        assert '<img src="data:image/png;base64,' in report_markdown, "Charts should be embedded"
        print("  Charts successfully embedded in report")
    else:
        print("  Note: No chart placeholders in report (AI generation may be unavailable)")
    
    print(f"  Report length: {len(report_markdown)} chars")
    print("✅ IC report generation test passed")
    
    return report_markdown


def test_formatters():
    """Test utility formatters"""
    print("🧪 Testing utility formatters...")
    
    assert format_currency(1.0) == "€1.0M", "Should format currency"
    assert format_percentage(0.15) == "15.0%", "Should format percentage"
    assert format_multiple(10.5) == "10.50x", "Should format multiple"
    
    print("✅ Utility formatters test passed")


def run_all_tests():
    """Run complete smoke test suite"""
    print("\n" + "=" * 60)
    print("🚀 Running LBO Engine Smoke Test Suite")
    print("=" * 60 + "\n")
    
    try:
        # Run tests in sequence
        df = test_data_ingestion()
        results = test_lbo_model(df)
        score_result = test_scoring(results)
        chart_paths = test_charts(results)
        contribution = test_contribution_analysis(results)
        report_markdown = test_report_generation(results, score_result, contribution, chart_paths)
        test_formatters()
        
        print("\n" + "=" * 60)
        print("✅ All smoke tests passed successfully!")
        print("=" * 60 + "\n")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Smoke test failed: {e}")
        print("=" * 60 + "\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
