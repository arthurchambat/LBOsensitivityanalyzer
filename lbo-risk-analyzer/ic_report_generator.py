"""
Investment Committee Report Generator
Advanced memo generation with scoring, charts, and structured analysis.
"""
import os
import json
from typing import Dict, Optional, Any
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 4000


class ICReportGenerator:
    """
    Generates comprehensive Investment Committee reports using AI.
    
    Combines:
    - Quantitative financial outputs
    - Qualitative business context
    - IC scoring
    - Return contribution analysis
    - Chart placeholders
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        """
        Initialize the report generator.
        
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
    
    def generate_ic_report(
        self,
        financial_data: Dict[str, Any],
        business_context: Dict[str, str],
        scoring_summary: Dict[str, Any],
        contribution_analysis: Dict[str, float],
        user_instructions: Optional[str] = None
    ) -> str:
        """
        Generate complete IC report in markdown format.
        
        Args:
            financial_data: All financial model outputs
            business_context: Qualitative business information
            scoring_summary: IC scoring results
            contribution_analysis: Return driver breakdown
            user_instructions: Optional custom instructions
            
        Returns:
            Markdown-formatted IC report with chart placeholders
        """
        prompt = self._build_ic_prompt(
            financial_data,
            business_context,
            scoring_summary,
            contribution_analysis,
            user_instructions
        )
        
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
            
            # Add chart placeholders
            memo = self._add_chart_placeholders(memo)
            
            return memo
            
        except Exception as e:
            return f"Error generating IC report: {str(e)}"
    
    def _get_system_prompt(self) -> str:
        """Get system prompt defining AI role and constraints."""
        return """You are a senior investment professional preparing an Investment Committee (IC) report for a Private Equity firm.

CRITICAL RULES:
1. Use ONLY the numerical data provided - never invent or calculate numbers
2. Be professional, concise, and objective
3. Write in markdown format with clear section headers
4. Flag any data quality concerns or uncertainties explicitly
5. Focus on risk assessment and value creation drivers
6. Be conservative - this is real capital allocation
7. Use proper financial terminology
8. Keep each section focused and concise (2-5 paragraphs max)

REQUIRED STRUCTURE:
# Deal Snapshot
# Business Overview
# Historical Performance
# Transaction Structure
# Operating Projections
# Leverage & Risk Analysis
# Return Profile & Value Creation
# Sensitivity Analysis
# Investment Committee Assessment
# Key IC Questions
# Recommendation

Use markdown tables where appropriate.
Include chart placeholder comments where visual data would add value.
Maintain professional IC memo tone throughout."""
    
    def _build_ic_prompt(
        self,
        financial_data: Dict[str, Any],
        business_context: Dict[str, str],
        scoring_summary: Dict[str, Any],
        contribution_analysis: Dict[str, float],
        user_instructions: Optional[str]
    ) -> str:
        """Build comprehensive prompt with all context."""
        
        # Extract key metrics
        company_name = business_context.get('company_name', 'Target Company')
        industry = business_context.get('industry', 'Not specified')
        
        prompt = f"""Generate a comprehensive Investment Committee report for the following LBO opportunity.

=== COMPANY & CONTEXT ===
Company: {company_name}
Industry: {industry}

Business Description:
{business_context.get('business_description', 'Not provided')}

Investment Thesis:
{business_context.get('investment_thesis', 'Not provided')}

Key Risks:
{business_context.get('key_risks', 'Not provided')}

Management Notes:
{business_context.get('management_notes', 'Not provided')}

=== TRANSACTION SNAPSHOT ===
Entry EV: €{financial_data.get('entry_ev', 0):.1f}M
Entry EBITDA: €{financial_data.get('entry_ebitda', 0):.1f}M
Entry Multiple: {financial_data.get('entry_multiple', 0):.1f}x

Debt: €{financial_data.get('debt', 0):.1f}M ({financial_data.get('debt_to_ebitda', 0):.1f}x EBITDA)
Equity Check: €{financial_data.get('equity', 0):.1f}M
Transaction Fees: €{financial_data.get('transaction_fees', 0):.1f}M

Hold Period: {financial_data.get('hold_period', 5)} years

=== BASE CASE RETURNS ===
IRR: {financial_data.get('irr', 0) * 100:.1f}%
MOIC: {financial_data.get('moic', 0):.2f}x

Exit EV: €{financial_data.get('exit_ev', 0):.1f}M
Exit Multiple: {financial_data.get('exit_multiple', 0):.1f}x
Exit Debt: €{financial_data.get('exit_debt', 0):.1f}M
Exit Equity Value: €{financial_data.get('exit_equity_value', 0):.1f}M

=== RETURN DRIVER CONTRIBUTION ===
EBITDA Growth: {contribution_analysis.get('ebitda_growth', 0):.1f}%
Multiple Expansion: {contribution_analysis.get('multiple_expansion', 0):.1f}%
Deleveraging: {contribution_analysis.get('deleveraging', 0):.1f}%

=== OPERATING ASSUMPTIONS ===
Revenue Growth: {financial_data.get('revenue_growth', 0) * 100:.1f}% per year
EBITDA Margin: {financial_data.get('ebitda_margin', 0) * 100:.1f}%

=== LEVERAGE & RISK ===
Entry Debt/EBITDA: {financial_data.get('debt_to_ebitda', 0):.1f}x
"""
        
        # Add leverage evolution if available
        if 'leverage_ratios' in financial_data and financial_data['leverage_ratios']:
            prompt += "\nLeverage Evolution:\n"
            for year_data in financial_data['leverage_ratios']:
                prompt += f"  Year {year_data.get('year')}: {year_data.get('debt_to_ebitda', 0):.1f}x Debt/EBITDA, {year_data.get('interest_coverage', 0):.1f}x Coverage\n"
        
        # Add risk flags
        if 'risk_flags' in financial_data and financial_data['risk_flags']:
            flags = financial_data['risk_flags']
            prompt += f"\nRisk Flags:\n"
            prompt += f"  High Leverage (>6x): {'Yes' if flags.get('high_leverage') else 'No'}\n"
            prompt += f"  Low Coverage (<1.5x): {'Yes' if flags.get('low_coverage') else 'No'}\n"
            prompt += f"  Peak Debt/EBITDA: {flags.get('max_debt_to_ebitda', 0):.1f}x\n"
            prompt += f"  Minimum Coverage: {flags.get('min_interest_coverage', 0):.1f}x\n"
        
        # Add IC Scoring
        prompt += f"""
=== INVESTMENT COMMITTEE SCORE ===
Total Score: {scoring_summary.get('total_score', 0)}/100
Risk Level: {scoring_summary.get('risk_level', 'Unknown')}

Component Scores:
"""
        for component, score in scoring_summary.get('component_scores', {}).items():
            prompt += f"  {component}: {score}/100\n"
        
        prompt += f"\nInterpretation: {scoring_summary.get('interpretation', 'N/A')}\n"
        
        # Add sensitivity data if available
        if 'sensitivity_summary' in financial_data:
            sens = financial_data['sensitivity_summary']
            prompt += f"""
=== SENSITIVITY ANALYSIS ===
IRR Range: {sens.get('min_irr', 0) * 100:.1f}% to {sens.get('max_irr', 0) * 100:.1f}%
MOIC Range: {sens.get('min_moic', 0):.2f}x to {sens.get('max_moic', 0):.2f}x
"""
        
        # Add custom instructions if provided
        if user_instructions:
            prompt += f"""
=== SPECIAL INSTRUCTIONS ===
{user_instructions}
"""
        
        prompt += """
===

Generate a complete, professional IC report using ONLY the data provided above.
Use proper markdown formatting.
Insert comment placeholders for charts: {{chart:revenue}}, {{chart:ebitda}}, {{chart:debt}}, {{chart:leverage}}, {{chart:sensitivity}}, {{chart:contribution}}
Be conservative and flag uncertainties.
Focus on value creation and risk assessment."""
        
        return prompt
    
    def _add_chart_placeholders(self, memo: str) -> str:
        """
        Ensure chart placeholders are present in appropriate sections.
        
        Args:
            memo: Generated markdown memo
            
        Returns:
            Memo with chart placeholders added if missing
        """
        # Check if memo already has placeholders
        if '{{chart:' in memo:
            return memo
        
        # Otherwise, add them in appropriate sections
        # This is a fallback - ideally AI includes them
        
        sections_to_enhance = {
            'Operating Projections': '\n\n{{chart:revenue}}\n\n{{chart:ebitda}}\n',
            'Leverage': '\n\n{{chart:debt}}\n\n{{chart:leverage}}\n',
            'Sensitivity': '\n\n{{chart:sensitivity}}\n',
            'Return Profile': '\n\n{{chart:contribution}}\n'
        }
        
        for section_keyword, charts in sections_to_enhance.items():
            if section_keyword in memo and charts.strip() not in memo:
                # Find the section and add charts after the first paragraph
                section_start = memo.find(section_keyword)
                if section_start != -1:
                    # Find next double newline after section
                    next_break = memo.find('\n\n', section_start + len(section_keyword))
                    if next_break != -1:
                        memo = memo[:next_break] + charts + memo[next_break:]
        
        return memo


# Backward compatibility alias
class MemoGenerator(ICReportGenerator):
    """Alias for backward compatibility."""
    
    def generate_ic_memo(
        self,
        context: Dict,
        user_focus: Optional[str] = None
    ) -> str:
        """
        Legacy interface for memo generation.
        
        Args:
            context: Dictionary with deal context
            user_focus: Optional user instructions
            
        Returns:
            Markdown-formatted memo
        """
        # Convert old context format to new format
        financial_data = context
        
        business_context = {
            'company_name': context.get('company_name', 'Target Company'),
            'industry': context.get('industry', 'Not specified'),
            'business_description': context.get('business_description', ''),
            'investment_thesis': context.get('investment_thesis', ''),
            'key_risks': context.get('key_risks', ''),
            'management_notes': context.get('management_notes', '')
        }
        
        # Create dummy scoring if not provided
        scoring_summary = context.get('scoring_summary', {
            'total_score': 0,
            'risk_level': 'Unknown',
            'component_scores': {},
            'interpretation': 'Scoring not available'
        })
        
        # Create dummy contribution if not provided
        contribution_analysis = context.get('contribution_analysis', {
            'ebitda_growth': 0,
            'multiple_expansion': 0,
            'deleveraging': 0
        })
        
        return self.generate_ic_report(
            financial_data,
            business_context,
            scoring_summary,
            contribution_analysis,
            user_focus
        )
