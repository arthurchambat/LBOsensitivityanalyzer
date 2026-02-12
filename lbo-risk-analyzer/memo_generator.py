"""
Investment Committee Memo Generator

Uses AI to generate professional IC memos based on financial analysis.
AI interprets data only - does not compute numbers.
"""
import os
import json
from typing import Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 3000


class MemoGenerator:
    """
    Generates Investment Committee memos using AI.
    
    AI is constrained to interpret provided data only.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        """
        Initialize the memo generator.
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model
        
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. "
                "Set it in .env file or pass as argument."
            )
        
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_ic_memo(
        self,
        context: Dict,
        user_focus: Optional[str] = None
    ) -> str:
        """
        Generate a complete IC memo in markdown format.
        
        Args:
            context: Dictionary with all deal context (company, metrics, results)
            user_focus: Optional user instructions
        
        Returns:
            Markdown-formatted IC memo
        """
        prompt = self._build_memo_prompt(context, user_focus)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=DEFAULT_TEMPERATURE,
                max_tokens=DEFAULT_MAX_TOKENS
            )
            
            memo = response.choices[0].message.content
            return memo
        
        except Exception as e:
            return f"# Error Generating Memo\n\n**Error:** {str(e)}\n\nPlease check your API configuration."
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt defining AI behavior."""
        return """You are a senior private equity investment professional writing an Investment Committee (IC) memo.

CRITICAL RULES:
1. You ONLY interpret the provided numerical data. You NEVER compute or invent numbers.
2. If data is missing or unclear, explicitly state "Data not provided" or "Unable to assess without X".
3. Write in a professional, concise, objective tone suitable for senior decision-makers.
4. Use proper markdown formatting with clear section headers.
5. Focus on: historical performance, transaction structure, returns, risks, and recommendation.
6. All numbers you reference MUST come from the provided data.
7. Be conservative in your assessment. This is real capital allocation.
8. If user provides specific focus instructions, adjust tone/emphasis accordingly without inventing data.

REQUIRED MEMO STRUCTURE:
# Executive Summary
# Company Overview & Historical Performance
# Transaction Structure
# Base Case Returns
# Sensitivity Analysis & Downside Scenarios
# Key Investment Risks
# Investment Thesis & Value Creation
# Open Questions & Due Diligence Items
# Recommendation

Keep each section concise (2-5 bullets or short paragraphs).
Use bullet points where appropriate.
Highlight key numbers.
Flag any data quality concerns."""
    
    def _build_memo_prompt(
        self,
        context: Dict,
        user_focus: Optional[str]
    ) -> str:
        """Build the prompt with all context."""
        
        company_name = context.get('company_name', 'Target Co.')
        
        # Handle both old and new format
        if 'sources_uses' in context:
            # New format
            prompt = f"""Generate an Investment Committee memo for the following LBO opportunity.

=== COMPANY ===
{company_name}

=== TRANSACTION STRUCTURE ===
Entry EBITDA: €{context.get('entry_ebitda', 0):.1f}M
Entry Multiple: {context.get('entry_multiple', 0):.1f}x
Enterprise Value: €{context.get('sources_uses', {}).get('enterprise_value', 0):.1f}M

Debt: €{context.get('sources_uses', {}).get('debt', 0):.1f}M ({context.get('debt_to_ebitda', 0):.1f}x EBITDA)
Equity Check: €{context.get('sources_uses', {}).get('equity', 0):.1f}M
Transaction Fees: €{context.get('sources_uses', {}).get('transaction_fees', 0):.1f}M
Financing Fees: €{context.get('sources_uses', {}).get('financing_fees', 0):.1f}M

=== OPERATING ASSUMPTIONS ===
Hold Period: {context.get('hold_period', 5)} years
Revenue Growth: {context.get('revenue_growth', 0) * 100:.1f}% per year
EBITDA Margin: {context.get('ebitda_margin', 0) * 100:.1f}%

=== EXIT ASSUMPTIONS ===
Exit Multiple: {context.get('exit_multiple', 0):.1f}x
Exit EV: €{context.get('exit_results', {}).get('exit_ev', 0):.1f}M
Exit Debt: €{context.get('exit_results', {}).get('exit_debt', 0):.1f}M
Exit Equity Value: €{context.get('exit_results', {}).get('exit_equity_value', 0):.1f}M

=== BASE CASE RETURNS ===
IRR: {context.get('irr', 0) * 100:.1f}%
MOIC: {context.get('moic', 0):.2f}x

=== LEVERAGE & RISK ===
Entry Debt/EBITDA: {context.get('debt_to_ebitda', 0):.1f}x
"""
            
            # Add leverage evolution if available
            if 'leverage_ratios' in context:
                leverage = context['leverage_ratios']
                if isinstance(leverage, list) and len(leverage) > 0:
                    prompt += "\nLeverage Evolution:\n"
                    for year in leverage:
                        prompt += f"Year {year.get('year')}: {year.get('debt_to_ebitda', 0):.1f}x Debt/EBITDA, {year.get('interest_coverage', 0):.1f}x Coverage\n"
            
            # Add risk flags
            if 'risk_flags' in context:
                flags = context['risk_flags']
                prompt += f"\nRisk Flags:\n"
                prompt += f"- High Leverage: {'Yes' if flags.get('high_leverage') else 'No'}\n"
                prompt += f"- Low Coverage: {'Yes' if flags.get('low_coverage') else 'No'}\n"
                prompt += f"- Max Debt/EBITDA: {flags.get('max_debt_to_ebitda', 0):.1f}x\n"
                prompt += f"- Min Interest Coverage: {flags.get('min_interest_coverage', 0):.1f}x\n"
        
        else:
            # Old format (backward compatibility)
            historical_summary = context.get('historical_summary', {})
            lbo_inputs = context.get('lbo_inputs', {})
            lbo_outputs = context.get('lbo_outputs', {})
            
            prompt = f"""Generate an Investment Committee memo for the following LBO opportunity.

=== COMPANY ===
{company_name}

=== HISTORICAL PERFORMANCE ===
Period: {historical_summary.get('start_year', 'N/A')} - {historical_summary.get('end_year', 'N/A')}
Revenue CAGR: {self._format_pct(historical_summary.get('revenue_cagr'))}
EBITDA CAGR: {self._format_pct(historical_summary.get('ebitda_cagr'))}

=== TRANSACTION STRUCTURE ===
Entry EBITDA: €{lbo_inputs.get('entry_ebitda', 0):.1f}M
Entry Multiple: {lbo_inputs.get('entry_multiple', 0):.1f}x
Entry EV: €{lbo_outputs.get('entry_ev', 0):.1f}M

Debt: €{lbo_outputs.get('debt', 0):.1f}M
Debt/EBITDA: {lbo_inputs.get('debt_to_ebitda', 0):.1f}x
Interest Rate: {self._format_pct(lbo_inputs.get('interest_rate'))}

Equity Check: €{lbo_outputs.get('equity', 0):.1f}M

=== BASE CASE ASSUMPTIONS ===
EBITDA Growth Rate: {self._format_pct(lbo_inputs.get('growth_rate'))} p.a.
Holding Period: {lbo_inputs.get('holding_period_years', 0)} years
Exit Multiple: {lbo_inputs.get('exit_multiple', 0):.1f}x

Exit EBITDA: €{lbo_outputs.get('exit_ebitda', 0):.1f}M
Exit EV: €{lbo_outputs.get('exit_ev', 0):.1f}M
Exit Equity Value: €{lbo_outputs.get('exit_equity_value', 0):.1f}M

=== BASE CASE RETURNS ===
Equity IRR: {self._format_pct(lbo_outputs.get('irr', 0) / 100)}
Equity MOIC: {lbo_outputs.get('moic', 0):.2f}x
"""
        
        if user_focus:
            prompt += f"\n=== SPECIAL INSTRUCTIONS ===\n{user_focus}\n"
        
        prompt += """
Generate a complete IC memo using ONLY the data provided above.
Use proper markdown formatting.
Be professional, concise, and objective.
Do not invent any numbers or data points not explicitly provided."""
        
        return prompt
    
    def _format_pct(self, value: Optional[float]) -> str:
        """Format percentage for display."""
        if value is None:
            return "N/A"
        return f"{value * 100:.1f}%"


def check_memo_api_available() -> bool:
    """
    Check if OpenAI API is available for memo generation.
    
    Returns:
        True if available, False otherwise
    """
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    return api_key is not None and api_key != '' and api_key != 'sk-your-openai-api-key-here'
