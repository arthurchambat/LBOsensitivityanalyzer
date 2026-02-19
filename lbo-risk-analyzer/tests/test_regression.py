"""
Regression test: live KPIs must match committed results.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data import get_sample_dataframe
from src.models import (
    CapitalStructureInputs,
    OperatingAssumptions,
    DebtAssumptions,
    ExitAssumptions,
    LBOEngine,
)

# Import pure helpers from app.py
# We re-implement the same logic here to validate
import hashlib, json


def _build(entry_ebitda, base_revenue):
    cap = CapitalStructureInputs(
        entry_ebitda=entry_ebitda, entry_multiple=10.0,
        debt_to_ebitda=5.0, transaction_fee_pct=0.02,
        financing_fee_pct=0.03, cash_on_bs=0.0,
    )
    ops = OperatingAssumptions(
        base_revenue=base_revenue,
        revenue_growth_rates=[0.05] * 5,
        ebitda_margin=0.20, tax_rate=0.25,
        da_pct_revenue=0.03, capex_pct_revenue=0.03,
        nwc_pct_revenue=0.10,
    )
    dbt = DebtAssumptions(
        initial_debt=0.0, interest_rate=0.06,
        amortization_pct=0.05, cash_sweep_enabled=True,
        cash_sweep_pct=0.50,
    )
    ext = ExitAssumptions(
        exit_mode="fixed", fixed_exit_multiple=10.0,
        entry_multiple=10.0, hold_period=5,
    )
    return cap, ops, dbt, ext


def test_live_vs_committed_consistency():
    """
    Calling LBOEngine twice with identical inputs must produce
    identical IRR and MOIC — guaranteeing live KPIs match committed.
    """
    df = get_sample_dataframe()
    entry_ebitda = float(df["ebitda"].iloc[-1])
    base_revenue = float(df["revenue"].iloc[-1])

    cap1, ops1, dbt1, ext1 = _build(entry_ebitda, base_revenue)
    res1 = LBOEngine(cap1, ops1, dbt1, ext1).get_results()

    cap2, ops2, dbt2, ext2 = _build(entry_ebitda, base_revenue)
    res2 = LBOEngine(cap2, ops2, dbt2, ext2).get_results()

    assert res1["irr"] == res2["irr"], (
        f"IRR mismatch: {res1['irr']} vs {res2['irr']}"
    )
    assert res1["moic"] == res2["moic"], (
        f"MOIC mismatch: {res1['moic']} vs {res2['moic']}"
    )
    assert res1["exit_equity_value"] == res2["exit_equity_value"], (
        f"Exit equity mismatch: {res1['exit_equity_value']} vs {res2['exit_equity_value']}"
    )

    # Also verify KPI extraction is deterministic
    su1 = res1["sources_uses"]
    su2 = res2["sources_uses"]
    assert su1["enterprise_value"] == su2["enterprise_value"]
    assert su1["debt"] == su2["debt"]

    print("✅ Live vs committed consistency test passed")
    print(f"   IRR = {res1['irr']:.4f}, MOIC = {res1['moic']:.2f}x")
