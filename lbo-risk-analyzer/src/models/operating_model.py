"""
Operating Model Module
Projects Revenue → EBITDA → EBIT → FCF with full P&L.
"""
import pandas as pd
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class OperatingAssumptions:
    """Operating model assumptions for projection period."""
    base_revenue: float
    revenue_growth_rates: List[float]  # Annual growth rates
    ebitda_margin: float               # As % of revenue
    tax_rate: float                     # As % of EBIT
    da_pct_revenue: float              # D&A as % of revenue
    capex_pct_revenue: float           # Capex as % of revenue
    nwc_pct_revenue: float             # NWC as % of revenue


class OperatingModel:
    """
    Projects full operating performance from Revenue to FCF.
    
    Calculates:
    - Revenue projection
    - EBITDA (margin-based)
    - EBIT (EBITDA - D&A)
    - Taxes
    - NOPAT
    - Change in NWC
    - Free Cash Flow
    """
    
    def __init__(self, assumptions: OperatingAssumptions):
        self.assumptions = assumptions
        self.projection = self._build_projection()
    
    def _build_projection(self) -> pd.DataFrame:
        """
        Build full operating projection.
        
        Returns:
            DataFrame with yearly operating metrics.
        """
        years = len(self.assumptions.revenue_growth_rates)
        
        # Initialize storage
        data = {
            'year': list(range(1, years + 1)),
            'revenue': [],
            'ebitda': [],
            'da': [],
            'ebit': [],
            'taxes': [],
            'nopat': [],
            'capex': [],
            'nwc': [],
            'change_in_nwc': [],
            'fcf': []
        }
        
        # Year 0 NWC (for change calculation)
        prev_nwc = self.assumptions.base_revenue * self.assumptions.nwc_pct_revenue
        
        # Project each year
        for i, growth_rate in enumerate(self.assumptions.revenue_growth_rates):
            # Revenue
            if i == 0:
                revenue = self.assumptions.base_revenue * (1 + growth_rate)
            else:
                revenue = data['revenue'][-1] * (1 + growth_rate)
            
            # EBITDA
            ebitda = revenue * self.assumptions.ebitda_margin
            
            # D&A
            da = revenue * self.assumptions.da_pct_revenue
            
            # EBIT
            ebit = ebitda - da
            
            # Taxes
            taxes = max(0, ebit * self.assumptions.tax_rate)
            
            # NOPAT
            nopat = ebit - taxes
            
            # Capex
            capex = revenue * self.assumptions.capex_pct_revenue
            
            # NWC
            nwc = revenue * self.assumptions.nwc_pct_revenue
            change_in_nwc = nwc - prev_nwc
            prev_nwc = nwc
            
            # FCF = NOPAT + D&A - Capex - Change in NWC
            fcf = nopat + da - capex - change_in_nwc
            
            # Store
            data['revenue'].append(revenue)
            data['ebitda'].append(ebitda)
            data['da'].append(da)
            data['ebit'].append(ebit)
            data['taxes'].append(taxes)
            data['nopat'].append(nopat)
            data['capex'].append(capex)
            data['nwc'].append(nwc)
            data['change_in_nwc'].append(change_in_nwc)
            data['fcf'].append(fcf)
        
        return pd.DataFrame(data)
    
    def get_projection(self) -> pd.DataFrame:
        """Returns the full operating projection DataFrame."""
        return self.projection
    
    def get_final_ebitda(self) -> float:
        """Returns final year EBITDA for exit valuation."""
        return self.projection['ebitda'].iloc[-1]
    
    def get_fcf_series(self) -> List[float]:
        """Returns FCF for each projection year."""
        return self.projection['fcf'].tolist()
    
    def get_metrics_summary(self) -> Dict[str, float]:
        """
        Returns summary metrics across projection period.
        
        Returns:
            Dictionary with average margins, growth rates, etc.
        """
        proj = self.projection
        
        return {
            'revenue_cagr': (proj['revenue'].iloc[-1] / proj['revenue'].iloc[0]) ** (1/len(proj)) - 1,
            'avg_ebitda_margin': proj['ebitda'].mean() / proj['revenue'].mean(),
            'avg_fcf_conversion': proj['fcf'].sum() / proj['ebitda'].sum(),
            'total_fcf': proj['fcf'].sum(),
            'final_revenue': proj['revenue'].iloc[-1],
            'final_ebitda': proj['ebitda'].iloc[-1],
        }
