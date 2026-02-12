"""
Investment Committee Scoring System
Quantitative risk/return scoring for LBO opportunities.
"""
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ScoringInputs:
    """Inputs for IC scoring calculation."""
    base_case_irr: float
    min_sensitivity_irr: float
    max_debt_to_ebitda: float
    min_interest_coverage: float
    ebitda_growth_volatility: Optional[float] = None


class ICScoring:
    """
    Investment Committee scoring system.
    
    Scores deals on a 0-100 scale based on:
    - Return attractiveness
    - Downside protection
    - Leverage risk
    - Coverage safety
    - Growth stability
    """
    
    # Scoring weights
    WEIGHTS = {
        'irr_score': 0.30,
        'downside_score': 0.25,
        'leverage_score': 0.20,
        'coverage_score': 0.15,
        'stability_score': 0.10
    }
    
    def __init__(self, inputs: ScoringInputs):
        """
        Initialize scoring engine.
        
        Args:
            inputs: Deal metrics for scoring
        """
        self.inputs = inputs
        self.scores = self._calculate_scores()
        self.total_score = self._calculate_total()
        self.risk_level = self._assess_risk_level()
    
    def _calculate_scores(self) -> Dict[str, float]:
        """
        Calculate individual component scores.
        
        Returns:
            Dictionary with component scores (0-100)
        """
        return {
            'irr_score': self._score_irr(),
            'downside_score': self._score_downside(),
            'leverage_score': self._score_leverage(),
            'coverage_score': self._score_coverage(),
            'stability_score': self._score_stability()
        }
    
    def _score_irr(self) -> float:
        """
        Score base case IRR attractiveness.
        
        Thresholds:
        - < 15%: Poor (0-40)
        - 15-20%: Fair (40-60)
        - 20-25%: Good (60-80)
        - 25-30%: Strong (80-95)
        - > 30%: Exceptional (95-100)
        
        Returns:
            Score 0-100
        """
        irr = self.inputs.base_case_irr * 100  # Convert to percentage
        
        if irr < 15:
            return max(0, (irr / 15) * 40)
        elif irr < 20:
            return 40 + ((irr - 15) / 5) * 20
        elif irr < 25:
            return 60 + ((irr - 20) / 5) * 20
        elif irr < 30:
            return 80 + ((irr - 25) / 5) * 15
        else:
            return min(100, 95 + ((irr - 30) / 10) * 5)
    
    def _score_downside(self) -> float:
        """
        Score downside protection based on worst-case sensitivity IRR.
        
        Thresholds:
        - < 10%: Poor (0-40)
        - 10-15%: Fair (40-70)
        - > 15%: Good (70-100)
        
        Returns:
            Score 0-100
        """
        if self.inputs.min_sensitivity_irr is None:
            return 50  # Neutral if no sensitivity data
        
        min_irr = self.inputs.min_sensitivity_irr * 100
        
        if min_irr < 10:
            return max(0, (min_irr / 10) * 40)
        elif min_irr < 15:
            return 40 + ((min_irr - 10) / 5) * 30
        else:
            return min(100, 70 + ((min_irr - 15) / 10) * 30)
    
    def _score_leverage(self) -> float:
        """
        Score leverage risk based on peak Debt/EBITDA.
        
        Thresholds:
        - < 4x: Low risk (80-100)
        - 4-5x: Moderate (60-80)
        - 5-6x: Elevated (40-60)
        - > 6x: High risk (0-40)
        
        Returns:
            Score 0-100
        """
        leverage = self.inputs.max_debt_to_ebitda
        
        if leverage < 4:
            return 80 + (4 - leverage) / 4 * 20
        elif leverage < 5:
            return 60 + (5 - leverage) * 20
        elif leverage < 6:
            return 40 + (6 - leverage) * 20
        else:
            return max(0, 40 - (leverage - 6) * 10)
    
    def _score_coverage(self) -> float:
        """
        Score interest coverage safety.
        
        Thresholds:
        - < 1.0x: Critical (0-20)
        - 1.0-1.5x: Weak (20-50)
        - 1.5-2.0x: Fair (50-70)
        - 2.0-2.5x: Good (70-85)
        - > 2.5x: Strong (85-100)
        
        Returns:
            Score 0-100
        """
        coverage = self.inputs.min_interest_coverage
        
        if coverage < 1.0:
            return max(0, coverage * 20)
        elif coverage < 1.5:
            return 20 + (coverage - 1.0) / 0.5 * 30
        elif coverage < 2.0:
            return 50 + (coverage - 1.5) / 0.5 * 20
        elif coverage < 2.5:
            return 70 + (coverage - 2.0) / 0.5 * 15
        else:
            return min(100, 85 + (coverage - 2.5) / 1.0 * 15)
    
    def _score_stability(self) -> float:
        """
        Score growth stability based on EBITDA volatility.
        
        Lower volatility = higher score
        
        Returns:
            Score 0-100
        """
        if self.inputs.ebitda_growth_volatility is None:
            return 60  # Neutral if no data
        
        volatility = self.inputs.ebitda_growth_volatility
        
        # Volatility thresholds (standard deviation)
        if volatility < 0.10:  # <10% std dev
            return 90
        elif volatility < 0.20:  # 10-20%
            return 70 + (0.20 - volatility) / 0.10 * 20
        elif volatility < 0.30:  # 20-30%
            return 50 + (0.30 - volatility) / 0.10 * 20
        else:  # >30%
            return max(20, 50 - (volatility - 0.30) / 0.20 * 30)
    
    def _calculate_total(self) -> int:
        """
        Calculate weighted total score.
        
        Returns:
            Total score 0-100
        """
        total = sum(
            self.scores[component] * weight
            for component, weight in self.WEIGHTS.items()
        )
        return int(round(total))
    
    def _assess_risk_level(self) -> str:
        """
        Assess overall risk level based on total score.
        
        Returns:
            'Low', 'Moderate', or 'High'
        """
        if self.total_score >= 70:
            return 'Low'
        elif self.total_score >= 50:
            return 'Moderate'
        else:
            return 'High'
    
    def get_summary(self) -> Dict:
        """
        Get complete scoring summary.
        
        Returns:
            Dictionary with all scoring metrics
        """
        return {
            'total_score': self.total_score,
            'risk_level': self.risk_level,
            'component_scores': {
                'IRR Attractiveness': round(self.scores['irr_score'], 1),
                'Downside Protection': round(self.scores['downside_score'], 1),
                'Leverage Risk': round(self.scores['leverage_score'], 1),
                'Coverage Safety': round(self.scores['coverage_score'], 1),
                'Growth Stability': round(self.scores['stability_score'], 1)
            },
            'interpretation': self._get_interpretation()
        }
    
    def _get_interpretation(self) -> str:
        """Generate text interpretation of score."""
        score = self.total_score
        
        if score >= 80:
            return "Strong deal with attractive returns and manageable risk"
        elif score >= 70:
            return "Good deal with solid returns and acceptable risk profile"
        elif score >= 60:
            return "Fair deal with reasonable returns but notable risks"
        elif score >= 50:
            return "Marginal deal requiring careful consideration"
        else:
            return "Weak deal with concerning risk/return profile"


def calculate_contribution_analysis(
    entry_ev: float,
    exit_ev: float,
    entry_debt: float,
    exit_debt: float,
    entry_ebitda: float,
    exit_ebitda: float,
    entry_multiple: float
) -> Dict[str, float]:
    """
    Estimate return driver contributions.
    
    Approximates % of value creation from:
    - EBITDA growth
    - Multiple expansion
    - Deleveraging
    
    Args:
        entry_ev: Entry enterprise value
        exit_ev: Exit enterprise value
        entry_debt: Entry debt
        exit_debt: Exit debt
        entry_ebitda: Entry EBITDA
        exit_ebitda: Exit EBITDA
        entry_multiple: Entry valuation multiple
    
    Returns:
        Dictionary with contribution percentages
    """
    # Total equity value creation
    entry_equity = entry_ev - entry_debt
    exit_equity = exit_ev - exit_debt
    total_gain = exit_equity - entry_equity
    
    if total_gain <= 0:
        return {
            'ebitda_growth': 0.0,
            'multiple_expansion': 0.0,
            'deleveraging': 0.0
        }
    
    # 1. EBITDA Growth contribution
    # Hypothetical exit EV if multiple stayed constant
    constant_multiple_ev = exit_ebitda * entry_multiple
    ebitda_growth_value = constant_multiple_ev - entry_ev
    
    # 2. Multiple Expansion contribution
    # Actual exit EV - hypothetical constant multiple EV
    exit_multiple = exit_ev / exit_ebitda if exit_ebitda > 0 else entry_multiple
    multiple_expansion_value = exit_ev - constant_multiple_ev
    
    # 3. Deleveraging contribution
    deleveraging_value = entry_debt - exit_debt
    
    # Convert to percentages
    ebitda_pct = (ebitda_growth_value / total_gain * 100) if total_gain > 0 else 0
    multiple_pct = (multiple_expansion_value / total_gain * 100) if total_gain > 0 else 0
    delev_pct = (deleveraging_value / total_gain * 100) if total_gain > 0 else 0
    
    # Normalize to 100%
    total_pct = ebitda_pct + multiple_pct + delev_pct
    if total_pct != 0:
        ebitda_pct = ebitda_pct / total_pct * 100
        multiple_pct = multiple_pct / total_pct * 100
        delev_pct = delev_pct / total_pct * 100
    
    return {
        'ebitda_growth': round(ebitda_pct, 1),
        'multiple_expansion': round(multiple_pct, 1),
        'deleveraging': round(delev_pct, 1)
    }
