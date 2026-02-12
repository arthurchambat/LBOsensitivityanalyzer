"""
Utility functions for formatting, validation, and helpers.
"""
from typing import Optional, Tuple


def format_currency(value: float, decimals: int = 1) -> str:
    """
    Format a number as currency in millions.
    
    Args:
        value: The numeric value to format
        decimals: Number of decimal places
    
    Returns:
        Formatted string like "€10.5M"
    """
    return f"€{value:,.{decimals}f}M"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format a decimal as percentage.
    
    Args:
        value: The decimal value (e.g., 0.15 for 15%)
        decimals: Number of decimal places
    
    Returns:
        Formatted string like "15.0%"
    """
    return f"{value * 100:,.{decimals}f}%"


def format_multiple(value: float, decimals: int = 2) -> str:
    """
    Format a multiple.
    
    Args:
        value: The multiple value
        decimals: Number of decimal places
    
    Returns:
        Formatted string like "2.50x"
    """
    return f"{value:,.{decimals}f}x"


def validate_model_inputs(
    entry_ebitda: float,
    entry_multiple: float,
    debt_to_ebitda: float,
    interest_rate: float,
    growth_rate: float,
    holding_period_years: int,
    exit_multiple: float
) -> Tuple[bool, Optional[str]]:
    """
    Validate all model inputs.
    
    Returns:
        (is_valid, error_message) tuple
    """
    if entry_ebitda <= 0:
        return False, "Entry EBITDA must be positive"
    
    if entry_multiple < 1.0:
        return False, "Entry multiple must be >= 1.0"
    
    if debt_to_ebitda < 0:
        return False, "Debt-to-EBITDA must be non-negative"
    
    if interest_rate < 0 or interest_rate > 100:
        return False, "Interest rate must be between 0% and 100%"
    
    if growth_rate < -50 or growth_rate > 100:
        return False, "Growth rate must be between -50% and 100%"
    
    if holding_period_years < 1 or holding_period_years > 20:
        return False, "Holding period must be between 1 and 20 years"
    
    if exit_multiple < 1.0:
        return False, "Exit multiple must be >= 1.0"
    
    return True, None


def safe_percentage_input(value: float) -> float:
    """
    Convert percentage input (e.g., 5.0) to decimal (0.05).
    
    Args:
        value: Percentage value (e.g., 5.0 for 5%)
    
    Returns:
        Decimal value (e.g., 0.05)
    """
    return value / 100.0


def ensure_min_value(value: float, minimum: float) -> float:
    """
    Ensure a value is at least the minimum.
    
    Args:
        value: The value to check
        minimum: The minimum allowed value
    
    Returns:
        max(value, minimum)
    """
    return max(value, minimum)
