"""
Historical Financial Analysis Module

Computes key metrics from historical financial data.
Pure Python - no AI, deterministic only.
"""
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from scipy import stats


class HistoricalAnalyzer:
    """
    Analyzes historical financial data to compute key metrics.
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize analyzer with financial data.
        
        Args:
            data: DataFrame with columns: year, revenue, ebitda
        """
        self.data = data.copy()
        self.data = self.data.sort_values('year').reset_index(drop=True)
    
    def calculate_cagr(self, values: pd.Series) -> Optional[float]:
        """
        Calculate Compound Annual Growth Rate.
        
        Args:
            values: Series of values over time
        
        Returns:
            CAGR as decimal (e.g., 0.05 for 5%)
        """
        if len(values) < 2:
            return None
        
        start_value = values.iloc[0]
        end_value = values.iloc[-1]
        periods = len(values) - 1
        
        if start_value <= 0 or end_value <= 0:
            return None
        
        cagr = (end_value / start_value) ** (1 / periods) - 1
        return cagr
    
    def calculate_growth_rates(self, values: pd.Series) -> pd.Series:
        """
        Calculate year-over-year growth rates.
        
        Args:
            values: Series of values
        
        Returns:
            Series of growth rates
        """
        return values.pct_change()
    
    def calculate_volatility(self, values: pd.Series) -> float:
        """
        Calculate standard deviation (volatility).
        
        Args:
            values: Series of values
        
        Returns:
            Standard deviation
        """
        return values.std()
    
    def calculate_trend_slope(self, values: pd.Series) -> Optional[float]:
        """
        Calculate linear regression slope (trend).
        
        Args:
            values: Series of values over time
        
        Returns:
            Slope of linear trend
        """
        if len(values) < 2:
            return None
        
        x = np.arange(len(values))
        y = values.values
        
        # Remove NaN values
        mask = ~np.isnan(y)
        if mask.sum() < 2:
            return None
        
        slope, _, _, _, _ = stats.linregress(x[mask], y[mask])
        return slope
    
    def analyze_revenue(self) -> Dict[str, float]:
        """
        Analyze revenue metrics.
        
        Returns:
            Dictionary with revenue metrics
        """
        revenue = self.data['revenue']
        growth_rates = self.calculate_growth_rates(revenue).dropna()
        
        return {
            'revenue_cagr': self.calculate_cagr(revenue),
            'revenue_growth_avg': growth_rates.mean() if len(growth_rates) > 0 else None,
            'revenue_growth_volatility': self.calculate_volatility(growth_rates) if len(growth_rates) > 0 else None,
            'revenue_growth_min': growth_rates.min() if len(growth_rates) > 0 else None,
            'revenue_growth_max': growth_rates.max() if len(growth_rates) > 0 else None,
            'revenue_trend_slope': self.calculate_trend_slope(revenue)
        }
    
    def analyze_ebitda(self) -> Dict[str, float]:
        """
        Analyze EBITDA metrics.
        
        Returns:
            Dictionary with EBITDA metrics
        """
        ebitda = self.data['ebitda']
        growth_rates = self.calculate_growth_rates(ebitda).dropna()
        
        return {
            'ebitda_cagr': self.calculate_cagr(ebitda),
            'ebitda_growth_avg': growth_rates.mean() if len(growth_rates) > 0 else None,
            'ebitda_growth_volatility': self.calculate_volatility(growth_rates) if len(growth_rates) > 0 else None,
            'ebitda_growth_min': growth_rates.min() if len(growth_rates) > 0 else None,
            'ebitda_growth_max': growth_rates.max() if len(growth_rates) > 0 else None,
            'ebitda_trend_slope': self.calculate_trend_slope(ebitda)
        }
    
    def analyze_margins(self) -> Dict[str, float]:
        """
        Analyze EBITDA margin metrics.
        
        Returns:
            Dictionary with margin metrics
        """
        margins = (self.data['ebitda'] / self.data['revenue'] * 100).replace([np.inf, -np.inf], np.nan)
        
        return {
            'avg_margin': margins.mean(),
            'margin_volatility': self.calculate_volatility(margins),
            'margin_min': margins.min(),
            'margin_max': margins.max(),
            'margin_trend': 'improving' if self.calculate_trend_slope(margins) > 0 else 'declining'
        }
    
    def get_full_summary(self) -> Dict[str, any]:
        """
        Get comprehensive historical analysis summary.
        
        Returns:
            Dictionary with all metrics
        """
        revenue_metrics = self.analyze_revenue()
        ebitda_metrics = self.analyze_ebitda()
        margin_metrics = self.analyze_margins()
        
        # Combine all metrics
        summary = {
            **revenue_metrics,
            **ebitda_metrics,
            **margin_metrics,
            'years_of_data': len(self.data),
            'start_year': int(self.data['year'].iloc[0]),
            'end_year': int(self.data['year'].iloc[-1])
        }
        
        return summary
    
    def get_calibrated_assumptions(self, mode: str = 'base') -> Dict[str, float]:
        """
        Get calibrated forward-looking assumptions based on historical data.
        
        Args:
            mode: 'base', 'conservative', or 'optimistic'
        
        Returns:
            Dictionary with suggested assumptions
        """
        summary = self.get_full_summary()
        
        ebitda_cagr = summary.get('ebitda_cagr', 0)
        ebitda_volatility = summary.get('ebitda_growth_volatility', 0)
        
        if mode == 'base':
            # Use historical CAGR
            forward_growth = ebitda_cagr
        
        elif mode == 'conservative':
            # Historical CAGR minus 1 standard deviation
            if ebitda_cagr is not None and ebitda_volatility is not None:
                forward_growth = max(0, ebitda_cagr - ebitda_volatility)
            else:
                forward_growth = 0.03  # Default 3%
        
        elif mode == 'optimistic':
            # Historical CAGR plus 0.5 standard deviation
            if ebitda_cagr is not None and ebitda_volatility is not None:
                forward_growth = ebitda_cagr + (0.5 * ebitda_volatility)
            else:
                forward_growth = 0.07  # Default 7%
        
        else:
            forward_growth = 0.05  # Default 5%
        
        # Get latest metrics for entry assumptions
        latest_ebitda = self.data['ebitda'].iloc[-1]
        latest_margin = (self.data['ebitda'].iloc[-1] / self.data['revenue'].iloc[-1] * 100)
        
        return {
            'forward_growth_rate': forward_growth,
            'entry_ebitda': latest_ebitda,
            'assumed_margin': latest_margin,
            'confidence': self._assess_confidence(summary)
        }
    
    def _assess_confidence(self, summary: Dict) -> str:
        """
        Assess confidence in historical data quality.
        
        Args:
            summary: Historical summary dictionary
        
        Returns:
            'high', 'medium', or 'low'
        """
        years = summary.get('years_of_data', 0)
        volatility = summary.get('ebitda_growth_volatility', 1.0)
        
        if years >= 5 and (volatility is None or volatility < 0.15):
            return 'high'
        elif years >= 3 and (volatility is None or volatility < 0.30):
            return 'medium'
        else:
            return 'low'


def format_metric(value: Optional[float], metric_type: str = 'percentage') -> str:
    """
    Format a metric for display.
    
    Args:
        value: Numeric value
        metric_type: 'percentage', 'multiple', or 'currency'
    
    Returns:
        Formatted string
    """
    if value is None or pd.isna(value):
        return "N/A"
    
    if metric_type == 'percentage':
        return f"{value * 100:.1f}%"
    elif metric_type == 'multiple':
        return f"{value:.2f}x"
    elif metric_type == 'currency':
        return f"€{value:,.1f}M"
    else:
        return f"{value:.2f}"
