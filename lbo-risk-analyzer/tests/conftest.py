"""
Pytest fixtures for smoke tests.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pandas as pd
from src.data import get_sample_dataframe
from src.models import (
    CapitalStructureInputs,
    OperatingAssumptions,
    DebtAssumptions,
    ExitAssumptions,
    LBOEngine,
)
from src.analysis import ICScoring, ScoringInputs, calculate_contribution_analysis
from src.reporting import charts


@pytest.fixture
def df():
    """Sample dataframe fixture."""
    return get_sample_dataframe()


@pytest.fixture
def results(df):
    """Run LBOEngine and return results dict."""
    entry_ebitda = float(df["ebitda"].iloc[-1])
    base_revenue = float(df["revenue"].iloc[-1])

    capital_inputs = CapitalStructureInputs(
        entry_ebitda=entry_ebitda,
        entry_multiple=10.0,
        debt_to_ebitda=5.0,
        transaction_fee_pct=0.02,
        financing_fee_pct=0.03,
        cash_on_bs=0.0,
    )
    operating_assumptions = OperatingAssumptions(
        base_revenue=base_revenue,
        revenue_growth_rates=[0.05] * 5,
        ebitda_margin=0.20,
        tax_rate=0.25,
        da_pct_revenue=0.03,
        capex_pct_revenue=0.03,
        nwc_pct_revenue=0.10,
    )
    debt_assumptions = DebtAssumptions(
        initial_debt=0.0,
        interest_rate=0.06,
        amortization_pct=0.05,
        cash_sweep_enabled=True,
        cash_sweep_pct=0.50,
    )
    exit_assumptions = ExitAssumptions(
        exit_mode="fixed",
        fixed_exit_multiple=10.0,
        entry_multiple=10.0,
        hold_period=5,
    )

    engine = LBOEngine(
        capital_inputs,
        operating_assumptions,
        debt_assumptions,
        exit_assumptions,
    )
    return engine.get_results()


@pytest.fixture
def score_result(results):
    scoring_inputs = ScoringInputs(
        base_case_irr=results["irr"],
        min_sensitivity_irr=results["irr"] * 0.8,
        max_debt_to_ebitda=results["leverage_ratios"]["debt_to_ebitda"].max(),
        min_interest_coverage=results["leverage_ratios"]["interest_coverage"].min(),
        ebitda_growth_volatility=None,
    )
    return ICScoring(scoring_inputs).get_summary()


@pytest.fixture
def chart_paths(results):
    paths = {}
    revenue_df = results["operating_projection"][["year", "revenue"]].copy()
    paths["revenue"] = charts.create_revenue_projection_chart(revenue_df)

    ebitda_df = results["operating_projection"][["year", "ebitda"]].copy()
    paths["ebitda"] = charts.create_ebitda_projection_chart(ebitda_df)

    debt_df = results["debt_schedule"].reset_index()
    if "Year" not in debt_df.columns and "year" not in debt_df.columns:
        debt_df["year"] = range(1, len(debt_df) + 1)
    paths["debt"] = charts.create_debt_schedule_chart(debt_df[["year", "ending_debt"]])

    return paths


@pytest.fixture
def contribution(results):
    entry_ev = results["sources_uses"]["enterprise_value"]
    entry_multiple = 10.0
    entry_ebitda = entry_ev / entry_multiple

    return calculate_contribution_analysis(
        entry_ev=entry_ev,
        exit_ev=results["exit_results"]["exit_ev"],
        entry_debt=results["sources_uses"]["debt"],
        exit_debt=results["debt_schedule"]["ending_debt"].iloc[-1],
        entry_ebitda=entry_ebitda,
        exit_ebitda=results["operating_projection"]["ebitda"].iloc[-1],
        entry_multiple=entry_multiple,
    )
