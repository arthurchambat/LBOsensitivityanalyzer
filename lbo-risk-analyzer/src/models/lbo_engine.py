"""
LBO Engine - Main Orchestrator
Coordinates all LBO model components and calculates returns.
"""
import numpy as np
import numpy_financial as npf
import pandas as pd
from typing import Dict, List, Any

from .capital_structure import CapitalStructure, CapitalStructureInputs
from .operating_model import OperatingModel, OperatingAssumptions
from .debt_model import DebtModel, DebtAssumptions
from .exit_model import ExitModel, ExitAssumptions


class LBOEngine:
    """
    Complete LBO model orchestrator.
    
    Coordinates:
    1. Capital structure (Sources & Uses)
    2. Operating projections (Revenue → FCF)
    3. Debt schedule (Amortization + Sweep)
    4. Exit valuation
    5. Returns calculation (IRR, MOIC)
    """
    
    def __init__(
        self,
        capital_inputs: CapitalStructureInputs,
        operating_assumptions: OperatingAssumptions,
        debt_assumptions: DebtAssumptions,
        exit_assumptions: ExitAssumptions
    ):
        """
        Initialize LBO engine with all input assumptions.
        
        Args:
            capital_inputs: Entry valuation and transaction structure
            operating_assumptions: Operating model parameters
            debt_assumptions: Debt structure and paydown logic
            exit_assumptions: Exit valuation methodology
        """
        self.capital_inputs = capital_inputs
        self.operating_assumptions = operating_assumptions
        self.debt_assumptions = debt_assumptions
        self.exit_assumptions = exit_assumptions
        
        # Run full model
        self.results = self._run_model()
    
    def _run_model(self) -> Dict[str, Any]:
        """
        Execute full LBO model.
        
        Returns:
            Dictionary with all model outputs
        """
        # Step 1: Capital Structure
        cap_structure = CapitalStructure(self.capital_inputs)
        sources_uses = cap_structure.get_summary()
        
        # Step 2: Operating Model
        operating = OperatingModel(self.operating_assumptions)
        operating_projection = operating.get_projection()
        fcf_series = operating.get_fcf_series()
        
        # Step 3: Debt Model (needs FCF for sweep)
        # Update debt_assumptions with actual debt from cap structure
        self.debt_assumptions.initial_debt = sources_uses['debt']
        debt = DebtModel(self.debt_assumptions, fcf_series)
        debt_schedule = debt.get_schedule()
        
        # Get EBITDA series for leverage metrics
        ebitda_series = operating_projection['ebitda'].tolist()
        leverage_ratios = debt.get_leverage_ratios(ebitda_series)
        risk_flags = debt.get_risk_flags(ebitda_series)
        
        # Step 4: Exit Valuation
        final_ebitda = operating.get_final_ebitda()
        final_debt = debt.get_final_debt()
        
        # Add operating metrics to exit assumptions for growth-adjusted
        self.exit_assumptions.revenue_cagr = operating.get_metrics_summary()['revenue_cagr']
        
        exit_model = ExitModel(self.exit_assumptions)
        exit_results = exit_model.calculate_exit_value(final_ebitda, final_debt)
        
        # Step 5: Returns Calculation
        equity_invested = sources_uses['equity']
        exit_equity = exit_results['exit_equity_value']
        
        # Equity cash flows: -Equity at T0, +Exit Equity at TN
        years = len(fcf_series)
        equity_cashflows = [-equity_invested] + [0] * (years - 1) + [exit_equity]
        
        # IRR and MOIC
        try:
            irr = npf.irr(equity_cashflows)
        except:
            irr = None
        
        moic = exit_equity / equity_invested if equity_invested > 0 else 0
        
        return {
            'sources_uses': sources_uses,
            'sources_uses_table': cap_structure.get_sources_uses_table(),
            'operating_projection': operating_projection,
            'operating_summary': operating.get_metrics_summary(),
            'debt_schedule': debt_schedule,
            'leverage_ratios': leverage_ratios,
            'risk_flags': risk_flags,
            'exit_results': exit_results,
            'exit_methodology': exit_model.get_methodology_description(),
            'equity_cashflows': equity_cashflows,
            'irr': irr,
            'moic': moic,
            'equity_invested': equity_invested,
            'exit_equity_value': exit_equity,
            'hold_period': years,
        }
    
    def get_results(self) -> Dict[str, Any]:
        """Returns complete model results."""
        return self.results
    
    def get_summary_metrics(self) -> Dict[str, float]:
        """
        Returns key summary metrics for display.
        
        Returns:
            Dictionary with headline metrics
        """
        r = self.results
        
        return {
            'entry_ev': r['sources_uses']['enterprise_value'],
            'entry_ebitda': self.capital_inputs.entry_ebitda,
            'entry_multiple': self.capital_inputs.entry_multiple,
            'debt': r['sources_uses']['debt'],
            'equity': r['sources_uses']['equity'],
            'exit_ev': r['exit_results']['exit_ev'],
            'exit_ebitda': r['exit_results']['exit_ebitda'],
            'exit_multiple': r['exit_results']['exit_multiple'],
            'exit_debt': r['exit_results']['exit_debt'],
            'exit_equity_value': r['exit_results']['exit_equity_value'],
            'irr': r['irr'],
            'moic': r['moic'],
            'hold_period': r['hold_period'],
        }
    
    def get_base_case_summary(self) -> Dict[str, Any]:
        """
        Returns formatted base case summary (backward compatible).
        
        Returns:
            Dictionary matching legacy LBOModel output format
        """
        r = self.results
        
        return {
            'entry_ev': r['sources_uses']['enterprise_value'],
            'debt': r['sources_uses']['debt'],
            'equity': r['sources_uses']['equity'],
            'exit_ev': r['exit_results']['exit_ev'],
            'exit_equity_value': r['exit_results']['exit_equity_value'],
            'irr': r['irr'],
            'moic': r['moic'],
            'exit_multiple': r['exit_results']['exit_multiple'],
        }


def build_sensitivity_grid(
    base_capital_inputs: CapitalStructureInputs,
    base_operating_assumptions: OperatingAssumptions,
    base_debt_assumptions: DebtAssumptions,
    base_exit_assumptions: ExitAssumptions,
    growth_range: List[float],
    exit_multiple_range: List[float]
) -> pd.DataFrame:
    """
    Build sensitivity table varying growth and exit multiple.
    
    Args:
        base_*: Base case assumptions
        growth_range: List of growth rates to test
        exit_multiple_range: List of exit multiples to test
        
    Returns:
        DataFrame with IRR for each scenario
    """
    results = []
    
    for growth in growth_range:
        for exit_mult in exit_multiple_range:
            # Create scenario-specific assumptions
            operating_assumptions = OperatingAssumptions(
                base_revenue=base_operating_assumptions.base_revenue,
                revenue_growth_rates=[growth] * len(base_operating_assumptions.revenue_growth_rates),
                ebitda_margin=base_operating_assumptions.ebitda_margin,
                tax_rate=base_operating_assumptions.tax_rate,
                da_pct_revenue=base_operating_assumptions.da_pct_revenue,
                capex_pct_revenue=base_operating_assumptions.capex_pct_revenue,
                nwc_pct_revenue=base_operating_assumptions.nwc_pct_revenue,
            )
            
            exit_assumptions = ExitAssumptions(
                exit_mode='fixed',
                fixed_exit_multiple=exit_mult,
                entry_multiple=base_exit_assumptions.entry_multiple,
                hold_period=base_exit_assumptions.hold_period,
            )
            
            # Run model
            try:
                engine = LBOEngine(
                    base_capital_inputs,
                    operating_assumptions,
                    base_debt_assumptions,
                    exit_assumptions
                )
                irr = engine.get_results()['irr']
                moic = engine.get_results()['moic']
            except:
                irr = None
                moic = None
            
            results.append({
                'growth_rate': growth,
                'exit_multiple': exit_mult,
                'irr': irr,
                'moic': moic
            })
    
    return pd.DataFrame(results)


def summarize_sensitivity(df: pd.DataFrame, metric: str = 'irr') -> pd.DataFrame:
    """
    Pivot sensitivity results into matrix format.
    
    Args:
        df: Sensitivity results from build_sensitivity_grid
        metric: 'irr' or 'moic'
        
    Returns:
        Pivoted DataFrame (growth x exit_multiple)
    """
    return df.pivot(index='growth_rate', columns='exit_multiple', values=metric)
