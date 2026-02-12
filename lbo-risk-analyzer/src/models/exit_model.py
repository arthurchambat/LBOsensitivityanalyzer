"""
Exit Model Module
Calculates exit valuation with multiple methodologies.
"""
from typing import Dict, Literal
from dataclasses import dataclass


ExitMode = Literal['fixed', 'mean_reversion', 'growth_adjusted']


@dataclass
class ExitAssumptions:
    """Exit valuation assumptions."""
    exit_mode: ExitMode = 'fixed'
    fixed_exit_multiple: float = 10.0
    entry_multiple: float = 10.0           # For mean reversion
    industry_multiple: float = 10.0        # Target for mean reversion
    hold_period: int = 5
    revenue_cagr: float = 0.0              # For growth-adjusted
    growth_multiple_factor: float = 0.5    # Multiple change per 1% growth


class ExitModel:
    """
    Calculates exit enterprise value using various methodologies.
    
    Methodologies:
    1. Fixed: Use constant exit multiple
    2. Mean Reversion: Trend from entry multiple toward industry average
    3. Growth-Adjusted: Multiple scales with revenue growth performance
    """
    
    def __init__(self, assumptions: ExitAssumptions):
        self.assumptions = assumptions
        self.exit_multiple = self._calculate_exit_multiple()
    
    def _calculate_exit_multiple(self) -> float:
        """
        Calculate exit multiple based on selected methodology.
        
        Returns:
            Exit multiple to apply to final EBITDA
        """
        if self.assumptions.exit_mode == 'fixed':
            return self.assumptions.fixed_exit_multiple
        
        elif self.assumptions.exit_mode == 'mean_reversion':
            # Linear reversion from entry multiple to industry multiple
            # At Year 0: entry_multiple
            # At Year N: industry_multiple
            entry = self.assumptions.entry_multiple
            target = self.assumptions.industry_multiple
            years = self.assumptions.hold_period
            
            # Linear interpolation
            multiple = entry + (target - entry) * (1.0)  # Full reversion at exit
            return multiple
        
        elif self.assumptions.exit_mode == 'growth_adjusted':
            # Base multiple adjusted by growth performance
            # Higher growth = higher multiple
            base_multiple = self.assumptions.entry_multiple
            growth_pct = self.assumptions.revenue_cagr * 100  # Convert to percentage
            
            # Adjustment: +0.5x multiple per 1% growth above/below 5% baseline
            baseline_growth = 5.0
            growth_delta = growth_pct - baseline_growth
            adjustment = growth_delta * self.assumptions.growth_multiple_factor
            
            return max(5.0, base_multiple + adjustment)  # Floor at 5x
        
        return self.assumptions.fixed_exit_multiple
    
    def calculate_exit_value(self, final_ebitda: float, final_debt: float) -> Dict[str, float]:
        """
        Calculate exit enterprise and equity value.
        
        Args:
            final_ebitda: EBITDA in exit year
            final_debt: Remaining debt at exit
            
        Returns:
            Dictionary with exit metrics
        """
        exit_ev = final_ebitda * self.exit_multiple
        exit_equity = exit_ev - final_debt
        
        return {
            'exit_ebitda': final_ebitda,
            'exit_multiple': self.exit_multiple,
            'exit_ev': exit_ev,
            'exit_debt': final_debt,
            'exit_equity_value': exit_equity,
        }
    
    def get_exit_multiple(self) -> float:
        """Returns the calculated exit multiple."""
        return self.exit_multiple
    
    def get_methodology_description(self) -> str:
        """Returns description of exit methodology used."""
        mode = self.assumptions.exit_mode
        
        if mode == 'fixed':
            return f"Fixed exit multiple of {self.exit_multiple:.1f}x"
        elif mode == 'mean_reversion':
            return f"Mean reversion from {self.assumptions.entry_multiple:.1f}x to {self.assumptions.industry_multiple:.1f}x"
        elif mode == 'growth_adjusted':
            return f"Growth-adjusted multiple (base {self.assumptions.entry_multiple:.1f}x, CAGR {self.assumptions.revenue_cagr:.1%})"
        return "Unknown methodology"
