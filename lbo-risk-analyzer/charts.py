"""
Chart Generation for IC Reports
Creates professional charts for LBO analysis.
"""
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import io
import base64


# Professional color palette
COLORS = {
    'primary': '#00d4ff',      # Cyan
    'secondary': '#ffb020',    # Amber
    'positive': '#1dd1a1',     # Green
    'negative': '#ff4757',     # Red
    'neutral': '#8b92a8',      # Gray
    'dark': '#0a0e1a',         # Dark background
    'grid': '#1e2433'          # Grid lines
}

# Chart style
plt.style.use('dark_background')


def set_chart_style(ax, title: str):
    """Apply consistent styling to charts."""
    ax.set_title(title, fontsize=14, fontweight='bold', color=COLORS['primary'], pad=20)
    ax.set_facecolor(COLORS['dark'])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(COLORS['grid'])
    ax.spines['bottom'].set_color(COLORS['grid'])
    ax.tick_params(colors=COLORS['neutral'])
    ax.grid(True, alpha=0.2, color=COLORS['grid'], linestyle='--')


def save_fig_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 string."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight', 
                facecolor=COLORS['dark'], edgecolor='none')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)
    return img_base64


def save_fig_to_file(fig, filepath: str):
    """Save matplotlib figure to file."""
    fig.savefig(filepath, format='png', dpi=150, bbox_inches='tight',
                facecolor=COLORS['dark'], edgecolor='none')
    plt.close(fig)


def create_revenue_projection_chart(projection_df: pd.DataFrame) -> str:
    """
    Create revenue projection line chart.
    
    Args:
        projection_df: DataFrame with 'year' and 'revenue' columns
        
    Returns:
        Base64 encoded image string
    """
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=COLORS['dark'])
    
    years = projection_df['year']
    revenue = projection_df['revenue']
    
    ax.plot(years, revenue, marker='o', linewidth=2.5, markersize=8,
            color=COLORS['primary'], label='Revenue')
    ax.fill_between(years, revenue, alpha=0.2, color=COLORS['primary'])
    
    # Annotations
    for i, (year, rev) in enumerate(zip(years, revenue)):
        if i == 0 or i == len(years) - 1:
            ax.annotate(f'€{rev:.0f}M', 
                       xy=(year, rev), 
                       xytext=(0, 10),
                       textcoords='offset points',
                       ha='center',
                       fontsize=10,
                       color=COLORS['primary'])
    
    set_chart_style(ax, 'Revenue Projection')
    ax.set_xlabel('Year', fontsize=11, color=COLORS['neutral'])
    ax.set_ylabel('Revenue (€M)', fontsize=11, color=COLORS['neutral'])
    ax.legend(loc='upper left', framealpha=0.9, facecolor=COLORS['dark'])
    
    return save_fig_to_base64(fig)


def create_ebitda_projection_chart(projection_df: pd.DataFrame) -> str:
    """
    Create EBITDA projection line chart.
    
    Args:
        projection_df: DataFrame with 'year' and 'ebitda' columns
        
    Returns:
        Base64 encoded image string
    """
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=COLORS['dark'])
    
    years = projection_df['year']
    ebitda = projection_df['ebitda']
    
    ax.plot(years, ebitda, marker='s', linewidth=2.5, markersize=8,
            color=COLORS['secondary'], label='EBITDA')
    ax.fill_between(years, ebitda, alpha=0.2, color=COLORS['secondary'])
    
    # Annotations
    for i, (year, ebit) in enumerate(zip(years, ebitda)):
        if i == 0 or i == len(years) - 1:
            ax.annotate(f'€{ebit:.0f}M', 
                       xy=(year, ebit), 
                       xytext=(0, 10),
                       textcoords='offset points',
                       ha='center',
                       fontsize=10,
                       color=COLORS['secondary'])
    
    set_chart_style(ax, 'EBITDA Projection')
    ax.set_xlabel('Year', fontsize=11, color=COLORS['neutral'])
    ax.set_ylabel('EBITDA (€M)', fontsize=11, color=COLORS['neutral'])
    ax.legend(loc='upper left', framealpha=0.9, facecolor=COLORS['dark'])
    
    return save_fig_to_base64(fig)


def create_debt_schedule_chart(debt_df: pd.DataFrame) -> str:
    """
    Create debt balance over time chart.
    
    Args:
        debt_df: DataFrame with 'year' and 'ending_debt' columns
        
    Returns:
        Base64 encoded image string
    """
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=COLORS['dark'])
    
    years = debt_df['year']
    debt = debt_df['ending_debt']
    
    ax.plot(years, debt, marker='D', linewidth=2.5, markersize=8,
            color=COLORS['negative'], label='Debt Balance')
    ax.fill_between(years, debt, alpha=0.3, color=COLORS['negative'])
    
    # Annotations for start and end
    ax.annotate(f'€{debt.iloc[0]:.0f}M', 
               xy=(years.iloc[0], debt.iloc[0]), 
               xytext=(0, 15),
               textcoords='offset points',
               ha='center',
               fontsize=10,
               color=COLORS['negative'])
    
    ax.annotate(f'€{debt.iloc[-1]:.0f}M', 
               xy=(years.iloc[-1], debt.iloc[-1]), 
               xytext=(0, 15),
               textcoords='offset points',
               ha='center',
               fontsize=10,
               color=COLORS['positive'])
    
    set_chart_style(ax, 'Debt Paydown Schedule')
    ax.set_xlabel('Year', fontsize=11, color=COLORS['neutral'])
    ax.set_ylabel('Debt Balance (€M)', fontsize=11, color=COLORS['neutral'])
    ax.legend(loc='upper right', framealpha=0.9, facecolor=COLORS['dark'])
    
    return save_fig_to_base64(fig)


def create_leverage_chart(leverage_df: pd.DataFrame) -> str:
    """
    Create leverage ratio chart.
    
    Args:
        leverage_df: DataFrame with 'year' and 'debt_to_ebitda' columns
        
    Returns:
        Base64 encoded image string
    """
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=COLORS['dark'])
    
    years = leverage_df['year']
    leverage = leverage_df['debt_to_ebitda']
    
    # Plot line
    ax.plot(years, leverage, marker='o', linewidth=2.5, markersize=8,
            color=COLORS['primary'], label='Debt/EBITDA', zorder=3)
    
    # Add covenant warning zone (>6x)
    ax.axhline(y=6.0, color=COLORS['negative'], linestyle='--', 
               linewidth=2, alpha=0.5, label='High Risk (>6x)')
    ax.fill_between(years, 6, leverage.max() + 1, alpha=0.1, 
                    color=COLORS['negative'])
    
    # Add safe zone indicator (<4x)
    ax.axhline(y=4.0, color=COLORS['positive'], linestyle='--', 
               linewidth=2, alpha=0.5, label='Low Risk (<4x)')
    
    set_chart_style(ax, 'Leverage Evolution')
    ax.set_xlabel('Year', fontsize=11, color=COLORS['neutral'])
    ax.set_ylabel('Debt / EBITDA (x)', fontsize=11, color=COLORS['neutral'])
    ax.legend(loc='upper right', framealpha=0.9, facecolor=COLORS['dark'])
    ax.set_ylim(0, max(leverage.max() + 1, 7))
    
    return save_fig_to_base64(fig)


def create_sensitivity_heatmap(sensitivity_df: pd.DataFrame) -> str:
    """
    Create IRR sensitivity heatmap.
    
    Args:
        sensitivity_df: DataFrame with growth_rate, exit_multiple, irr columns
        
    Returns:
        Base64 encoded image string
    """
    # Pivot data for heatmap
    pivot_irr = sensitivity_df.pivot(
        index='growth_rate', 
        columns='exit_multiple', 
        values='irr'
    )
    
    # Convert to percentage
    pivot_irr = pivot_irr * 100
    
    fig, ax = plt.subplots(figsize=(10, 8), facecolor=COLORS['dark'])
    
    # Create heatmap
    im = ax.imshow(pivot_irr.values, cmap='RdYlGn', aspect='auto',
                   vmin=0, vmax=40, interpolation='nearest')
    
    # Set ticks
    ax.set_xticks(np.arange(len(pivot_irr.columns)))
    ax.set_yticks(np.arange(len(pivot_irr.index)))
    ax.set_xticklabels([f'{x:.1f}x' for x in pivot_irr.columns])
    ax.set_yticklabels([f'{y:.1%}' for y in pivot_irr.index])
    
    # Rotate x labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # Add values to cells
    for i in range(len(pivot_irr.index)):
        for j in range(len(pivot_irr.columns)):
            value = pivot_irr.values[i, j]
            if not np.isnan(value):
                text = ax.text(j, i, f'{value:.1f}%',
                             ha="center", va="center", 
                             color="white" if value < 20 else "black",
                             fontsize=9, fontweight='bold')
    
    # Labels
    ax.set_xlabel('Exit Multiple', fontsize=12, color=COLORS['neutral'])
    ax.set_ylabel('Revenue Growth Rate', fontsize=12, color=COLORS['neutral'])
    ax.set_title('IRR Sensitivity Analysis', fontsize=14, fontweight='bold', 
                color=COLORS['primary'], pad=20)
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('IRR (%)', rotation=270, labelpad=20, color=COLORS['neutral'])
    cbar.ax.tick_params(colors=COLORS['neutral'])
    
    ax.set_facecolor(COLORS['dark'])
    
    return save_fig_to_base64(fig)


def create_contribution_chart(contribution: Dict[str, float]) -> str:
    """
    Create return contribution pie chart.
    
    Args:
        contribution: Dict with 'ebitda_growth', 'multiple_expansion', 'deleveraging'
        
    Returns:
        Base64 encoded image string
    """
    fig, ax = plt.subplots(figsize=(8, 8), facecolor=COLORS['dark'])
    
    labels = ['EBITDA Growth', 'Multiple Expansion', 'Deleveraging']
    sizes = [
        contribution['ebitda_growth'],
        contribution['multiple_expansion'],
        contribution['deleveraging']
    ]
    colors = [COLORS['primary'], COLORS['secondary'], COLORS['positive']]
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        sizes, 
        labels=labels, 
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'color': 'white', 'fontsize': 12}
    )
    
    # Make percentage text bold
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(14)
    
    ax.set_title('Return Driver Contribution', fontsize=14, fontweight='bold',
                color=COLORS['primary'], pad=20)
    
    return save_fig_to_base64(fig)


def create_all_charts(
    operating_projection: pd.DataFrame,
    debt_schedule: pd.DataFrame,
    leverage_ratios: pd.DataFrame,
    sensitivity_df: Optional[pd.DataFrame] = None,
    contribution: Optional[Dict[str, float]] = None
) -> Dict[str, str]:
    """
    Generate all IC report charts.
    
    Args:
        operating_projection: Operating model projection
        debt_schedule: Debt schedule
        leverage_ratios: Leverage ratios over time
        sensitivity_df: Sensitivity analysis results
        contribution: Return driver contribution
        
    Returns:
        Dictionary of chart names to base64 encoded images
    """
    charts = {}
    
    charts['revenue'] = create_revenue_projection_chart(operating_projection)
    charts['ebitda'] = create_ebitda_projection_chart(operating_projection)
    charts['debt'] = create_debt_schedule_chart(debt_schedule)
    charts['leverage'] = create_leverage_chart(leverage_ratios)
    
    if sensitivity_df is not None:
        charts['sensitivity'] = create_sensitivity_heatmap(sensitivity_df)
    
    if contribution is not None:
        charts['contribution'] = create_contribution_chart(contribution)
    
    return charts
