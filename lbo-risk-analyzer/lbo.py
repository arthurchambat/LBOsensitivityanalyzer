"""
LBO Financial Engine
Calcule les métriques financières d'un LBO (Leveraged Buyout)
"""
import numpy as np
import numpy_financial as npf
import pandas as pd


class LBOModel:
    """Moteur de calcul financier pour un LBO"""
    
    def __init__(self, enterprise_value=None, ebitda=None, debt_percentage=None, 
                 interest_rate=None, ebitda_growth_rate=None, years=5,
                 entry_ebitda=None, entry_multiple=None, debt_to_ebitda=None,
                 growth_rate=None, holding_period_years=None, exit_multiple=None):
        """
        Initialise le modèle LBO - supporte deux interfaces
        
        Old interface:
            enterprise_value, ebitda, debt_percentage, interest_rate, ebitda_growth_rate, years
        
        New interface:
            entry_ebitda, entry_multiple, debt_to_ebitda, interest_rate, growth_rate, 
            holding_period_years, exit_multiple
        """
        # Support new interface (preferred)
        if entry_ebitda is not None:
            self.ebitda = entry_ebitda
            self.entry_multiple = entry_multiple or 10.0
            self.exit_multiple = exit_multiple or 10.0
            self.enterprise_value = entry_ebitda * self.entry_multiple
            
            # Convert debt_to_ebitda to debt_percentage
            if debt_to_ebitda is not None:
                debt_amount = entry_ebitda * debt_to_ebitda
                self.debt_percentage = debt_amount / self.enterprise_value if self.enterprise_value > 0 else 0
                self.debt_to_ebitda_multiple = debt_to_ebitda
            else:
                self.debt_percentage = 0.6
                self.debt_to_ebitda_multiple = 0
            
            self.ebitda_growth_rate = growth_rate if growth_rate is not None else 0.05
            self.years = holding_period_years if holding_period_years is not None else 5
        
        # Support old interface (backward compatibility)
        else:
            self.enterprise_value = enterprise_value
            self.ebitda = ebitda
            self.debt_percentage = debt_percentage
            self.ebitda_growth_rate = ebitda_growth_rate
            self.years = years
            self.entry_multiple = enterprise_value / ebitda if ebitda > 0 else 10.0
            self.exit_multiple = 8.0  # Default
            self.debt_to_ebitda_multiple = 0
        
        self.interest_rate = interest_rate if interest_rate is not None else 0.08
        
        # Calculs initiaux
        self.debt = self.enterprise_value * self.debt_percentage
        self.equity = self.enterprise_value * (1 - self.debt_percentage)
        
    def calculate_cash_flows(self):
        """Calcule les flux de trésorerie sur la période"""
        cash_flows = []
        debt_balance = self.debt
        
        for year in range(1, self.years + 1):
            # EBITDA projeté
            ebitda_year = self.ebitda * ((1 + self.ebitda_growth_rate) ** year)
            
            # Charges d'intérêt
            interest_expense = debt_balance * self.interest_rate
            
            # Cash-flow disponible (simplifié)
            fcf = ebitda_year - interest_expense
            
            # Remboursement de dette (50% du FCF)
            debt_repayment = fcf * 0.5
            debt_balance = max(0, debt_balance - debt_repayment)
            
            cash_flows.append({
                'year': year,
                'ebitda': ebitda_year,
                'interest': interest_expense,
                'fcf': fcf,
                'debt_repayment': debt_repayment,
                'debt_balance': debt_balance
            })
        
        return pd.DataFrame(cash_flows)
    
    def calculate_irr(self, exit_multiple=8.0):
        """
        Calcule le TRI (Taux de Rendement Interne)
        
        Args:
            exit_multiple: Multiple de sortie (EV/EBITDA)
        
        Returns:
            float: TRI en pourcentage
        """
        # Cash flow initial (investissement en equity)
        cash_flows = [-self.equity]
        
        # Cash flows intermédiaires (assumés nuls pour simplicité)
        for year in range(1, self.years):
            cash_flows.append(0)
        
        # Cash flow final (exit)
        df = self.calculate_cash_flows()
        final_ebitda = df.iloc[-1]['ebitda']
        exit_value = final_ebitda * exit_multiple
        final_debt = df.iloc[-1]['debt_balance']
        equity_value = exit_value - final_debt
        
        cash_flows.append(equity_value)
        
        # Calcul du TRI
        try:
            irr = npf.irr(cash_flows)
            return irr * 100  # En pourcentage
        except:
            return None
    
    def calculate_moic(self, exit_multiple=8.0):
        """
        Calcule le MOIC (Multiple on Invested Capital)
        
        Args:
            exit_multiple: Multiple de sortie (EV/EBITDA)
        
        Returns:
            float: MOIC
        """
        df = self.calculate_cash_flows()
        final_ebitda = df.iloc[-1]['ebitda']
        exit_value = final_ebitda * exit_multiple
        final_debt = df.iloc[-1]['debt_balance']
        equity_value = exit_value - final_debt
        
        return equity_value / self.equity
    
    def calculate_debt_ratios(self):
        """Calcule les ratios d'endettement"""
        df = self.calculate_cash_flows()
        
        initial_debt_to_ebitda = self.debt / self.ebitda
        final_debt_to_ebitda = df.iloc[-1]['debt_balance'] / df.iloc[-1]['ebitda']
        
        return {
            'initial_debt_ebitda': initial_debt_to_ebitda,
            'final_debt_ebitda': final_debt_to_ebitda
        }
    
    def get_summary(self, exit_multiple=8.0):
        """Retourne un résumé complet du modèle"""
        irr = self.calculate_irr(exit_multiple)
        moic = self.calculate_moic(exit_multiple)
        debt_ratios = self.calculate_debt_ratios()
        
        return {
            'enterprise_value': self.enterprise_value,
            'equity_invested': self.equity,
            'debt': self.debt,
            'irr': irr,
            'moic': moic,
            'initial_debt_ebitda': debt_ratios['initial_debt_ebitda'],
            'final_debt_ebitda': debt_ratios['final_debt_ebitda']
        }
    
    # Compatibility methods for new interface
    def get_base_case_summary(self):
        """Get base case summary - compatible with new interface"""
        df = self.calculate_cash_flows()
        exit_ebitda = df.iloc[-1]['ebitda']
        exit_ev = exit_ebitda * 8.0  # Default exit multiple
        
        return {
            'entry_ebitda': self.ebitda,
            'entry_ev': self.enterprise_value,
            'entry_multiple': self.enterprise_value / self.ebitda if self.ebitda > 0 else 0,
            'debt': self.debt,
            'debt_to_ebitda': self.debt / self.ebitda if self.ebitda > 0 else 0,
            'equity': self.equity,
            'interest_rate': self.interest_rate,
            'growth_rate': self.ebitda_growth_rate,
            'holding_period': self.years,
            'exit_ebitda': exit_ebitda,
            'exit_ev': exit_ev,
            'exit_multiple': 8.0,
            'exit_equity_value': exit_ev - self.debt,
            'irr': self.calculate_irr(8.0),
            'moic': self.calculate_moic(8.0)
        }


def build_sensitivity_grid(
    entry_ebitda: float,
    entry_multiple: float,
    debt_to_ebitda: float,
    interest_rate: float,
    holding_period_years: int,
    growth_rates: list = None,
    exit_multiples: list = None
):
    """
    Build sensitivity analysis grid for IRR and MOIC.
    """
    import pandas as pd
    
    if growth_rates is None:
        growth_rates = [-0.02, 0.00, 0.03, 0.06, 0.09]
    
    if exit_multiples is None:
        exit_multiples = [
            max(1.0, entry_multiple - 2),
            entry_multiple,
            entry_multiple + 2
        ]
    
    # Ensure minimum exit multiple of 1.0
    exit_multiples = [max(1.0, em) for em in exit_multiples]
    
    # Build grids
    irr_data = []
    moic_data = []
    
    for growth in growth_rates:
        irr_row = []
        moic_row = []
        
        for exit_mult in exit_multiples:
            # Create model using old interface
            entry_ev = entry_ebitda * entry_multiple
            debt_pct = (entry_ebitda * debt_to_ebitda) / entry_ev if entry_ev > 0 else 0
            
            model = LBOModel(
                enterprise_value=entry_ev,
                ebitda=entry_ebitda,
                debt_percentage=debt_pct,
                interest_rate=interest_rate,
                ebitda_growth_rate=growth,
                years=holding_period_years
            )
            
            irr = model.calculate_irr(exit_mult)
            moic = model.calculate_moic(exit_mult)
            
            irr_row.append(irr)
            moic_row.append(moic)
        
        irr_data.append(irr_row)
        moic_data.append(moic_row)
    
    # Create DataFrames with proper labels
    growth_labels = [f"{g*100:+.0f}%" for g in growth_rates]
    exit_labels = [f"{em:.1f}x" for em in exit_multiples]
    
    irr_grid = pd.DataFrame(
        irr_data,
        index=growth_labels,
        columns=exit_labels
    )
    
    moic_grid = pd.DataFrame(
        moic_data,
        index=growth_labels,
        columns=exit_labels
    )
    
    return {
        'irr_grid': irr_grid,
        'moic_grid': moic_grid,
        'growth_rates': growth_rates,
        'exit_multiples': exit_multiples
    }


def summarize_sensitivity(sensitivity_grids: dict):
    """
    Summarize sensitivity analysis with key statistics.
    """
    import numpy as np
    
    irr_grid = sensitivity_grids['irr_grid']
    moic_grid = sensitivity_grids['moic_grid']
    
    # Filter out None values
    irr_values = irr_grid.values.flatten()
    irr_values = [v for v in irr_values if v is not None and not np.isnan(v)]
    
    moic_values = moic_grid.values.flatten()
    moic_values = [v for v in moic_values if v is not None and not np.isnan(v)]
    
    return {
        'irr_min': min(irr_values) if irr_values else None,
        'irr_max': max(irr_values) if irr_values else None,
        'irr_range': max(irr_values) - min(irr_values) if irr_values else None,
        'moic_min': min(moic_values) if moic_values else None,
        'moic_max': max(moic_values) if moic_values else None,
        'moic_range': max(moic_values) - min(moic_values) if moic_values else None
    }
