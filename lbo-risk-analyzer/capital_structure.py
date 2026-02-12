"""
Capital Structure Module
Handles Sources & Uses calculation with transaction fees.
"""
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class CapitalStructureInputs:
    """Input parameters for capital structure calculation."""
    entry_ebitda: float
    entry_multiple: float
    debt_to_ebitda: float
    transaction_fee_pct: float = 0.02  # % of EV
    financing_fee_pct: float = 0.03    # % of Debt
    cash_on_bs: float = 0.0            # Cash on balance sheet


class CapitalStructure:
    """
    Calculates Sources & Uses for LBO transaction.
    
    Includes transaction fees, financing fees, and cash adjustments.
    """
    
    def __init__(self, inputs: CapitalStructureInputs):
        self.inputs = inputs
        self.results = self._calculate()
    
    def _calculate(self) -> Dict[str, float]:
        """
        Compute Sources & Uses.
        
        Returns:
            Dictionary with EV, debt, equity, fees, and total uses.
        """
        # Enterprise Value
        ev = self.inputs.entry_ebitda * self.inputs.entry_multiple
        
        # Debt
        debt = self.inputs.entry_ebitda * self.inputs.debt_to_ebitda
        
        # Fees
        transaction_fees = ev * self.inputs.transaction_fee_pct
        financing_fees = debt * self.inputs.financing_fee_pct
        
        # Total Uses (what we need to buy the company)
        total_uses = ev + transaction_fees + financing_fees
        
        # Sources (Debt + Equity - Cash)
        # Cash on BS reduces equity check
        equity = total_uses - debt - self.inputs.cash_on_bs
        
        return {
            'enterprise_value': ev,
            'debt': debt,
            'equity': equity,
            'transaction_fees': transaction_fees,
            'financing_fees': financing_fees,
            'cash_on_bs': self.inputs.cash_on_bs,
            'total_uses': total_uses,
            'total_sources': debt + equity + self.inputs.cash_on_bs,
            # Key ratios
            'debt_to_ev': debt / ev if ev > 0 else 0,
            'equity_to_ev': equity / ev if ev > 0 else 0,
        }
    
    def get_sources_uses_table(self) -> Dict[str, Dict[str, float]]:
        """
        Returns formatted Sources & Uses table.
        
        Returns:
            Dictionary with 'uses' and 'sources' sections.
        """
        r = self.results
        
        return {
            'uses': {
                'Enterprise Value': r['enterprise_value'],
                'Transaction Fees': r['transaction_fees'],
                'Financing Fees': r['financing_fees'],
                'Total Uses': r['total_uses'],
            },
            'sources': {
                'Debt': r['debt'],
                'Equity': r['equity'],
                'Cash on Balance Sheet': r['cash_on_bs'],
                'Total Sources': r['total_sources'],
            }
        }
    
    def get_summary(self) -> Dict[str, float]:
        """Returns key capital structure metrics."""
        return self.results
