"""
Debt Model Module
Handles debt amortization, interest, and cash sweep mechanics.
"""
import pandas as pd
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class DebtAssumptions:
    """Debt structure assumptions."""
    initial_debt: float
    interest_rate: float              # Annual interest rate
    amortization_pct: float = 0.0     # % of initial debt paid annually
    cash_sweep_enabled: bool = False
    cash_sweep_pct: float = 0.0       # % of FCF used for additional paydown


class DebtModel:
    """
    Models debt paydown with scheduled amortization and optional cash sweep.
    
    Tracks:
    - Beginning debt balance
    - Interest expense
    - Scheduled amortization
    - Optional cash sweep from FCF
    - Ending debt balance
    """
    
    def __init__(self, assumptions: DebtAssumptions, fcf_series: List[float]):
        """
        Initialize debt model.
        
        Args:
            assumptions: Debt structure parameters
            fcf_series: Free cash flow for each year (for sweep calculation)
        """
        self.assumptions = assumptions
        self.fcf_series = fcf_series
        self.schedule = self._build_schedule()
    
    def _build_schedule(self) -> pd.DataFrame:
        """
        Build complete debt schedule.
        
        Returns:
            DataFrame with yearly debt movements.
        """
        years = len(self.fcf_series)
        
        data = {
            'year': list(range(1, years + 1)),
            'beginning_debt': [],
            'interest': [],
            'scheduled_amort': [],
            'cash_sweep': [],
            'total_paydown': [],
            'ending_debt': []
        }
        
        debt_balance = self.assumptions.initial_debt
        scheduled_amort_amount = self.assumptions.initial_debt * self.assumptions.amortization_pct
        
        for i, fcf in enumerate(self.fcf_series):
            # Beginning balance
            data['beginning_debt'].append(debt_balance)
            
            # Interest
            interest = debt_balance * self.assumptions.interest_rate
            data['interest'].append(interest)
            
            # Scheduled amortization (cannot exceed remaining debt)
            scheduled_amort = min(scheduled_amort_amount, debt_balance)
            data['scheduled_amort'].append(scheduled_amort)
            
            # Cash sweep
            cash_sweep = 0.0
            if self.assumptions.cash_sweep_enabled and fcf > 0:
                # Sweep is applied AFTER interest and scheduled amort
                available_fcf = fcf - interest
                cash_sweep = max(0, available_fcf * self.assumptions.cash_sweep_pct)
                # Cannot pay down more than remaining debt after scheduled amort
                cash_sweep = min(cash_sweep, debt_balance - scheduled_amort)
            data['cash_sweep'].append(cash_sweep)
            
            # Total paydown
            total_paydown = scheduled_amort + cash_sweep
            data['total_paydown'].append(total_paydown)
            
            # Ending balance
            debt_balance = max(0, debt_balance - total_paydown)
            data['ending_debt'].append(debt_balance)
        
        return pd.DataFrame(data)
    
    def get_schedule(self) -> pd.DataFrame:
        """Returns complete debt schedule."""
        return self.schedule
    
    def get_final_debt(self) -> float:
        """Returns debt balance at exit."""
        return self.schedule['ending_debt'].iloc[-1]
    
    def get_total_interest(self) -> float:
        """Returns cumulative interest paid over hold period."""
        return self.schedule['interest'].sum()
    
    def get_leverage_ratios(self, ebitda_series: List[float]) -> pd.DataFrame:
        """
        Calculate Debt/EBITDA and Interest Coverage ratios.
        
        Args:
            ebitda_series: EBITDA for each projection year
            
        Returns:
            DataFrame with leverage metrics
        """
        schedule = self.schedule.copy()
        schedule['ebitda'] = ebitda_series
        
        # Use beginning debt for leverage ratio
        schedule['debt_to_ebitda'] = schedule['beginning_debt'] / schedule['ebitda']
        
        # Interest coverage = EBITDA / Interest
        schedule['interest_coverage'] = schedule['ebitda'] / schedule['interest'].replace(0, 1)
        
        return schedule[['year', 'beginning_debt', 'ebitda', 'debt_to_ebitda', 'interest_coverage']]
    
    def get_risk_flags(self, ebitda_series: List[float]) -> Dict[str, bool]:
        """
        Identify covenant or leverage risk flags.
        
        Args:
            ebitda_series: EBITDA for each projection year
            
        Returns:
            Dictionary of risk indicators
        """
        leverage = self.get_leverage_ratios(ebitda_series)
        
        return {
            'high_leverage': (leverage['debt_to_ebitda'] > 6.0).any(),
            'low_coverage': (leverage['interest_coverage'] < 1.5).any(),
            'max_debt_to_ebitda': leverage['debt_to_ebitda'].max(),
            'min_interest_coverage': leverage['interest_coverage'].min(),
        }
