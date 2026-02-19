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
DEFAULT_MAX_TOKENS = 8000


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
9. ALL financial figures must come from the data - do NOT recalculate or round differently
10. Include the actual numbers in your analysis - don't just describe trends, show the values

REQUIRED STRUCTURE:
# Deal Snapshot
(One-paragraph executive summary with IRR, MOIC, entry EV, hold period)

# Business Overview
(Industry, description, competitive positioning)

# Historical Performance
(Revenue/EBITDA trends if provided)

# Transaction Structure
(Full Sources & Uses breakdown with actual numbers)

# Operating Projections
(Year-by-year revenue, EBITDA, FCF trajectory with actual numbers from the projection data)

# Leverage & Risk Analysis
(Entry leverage, deleveraging path year by year, coverage ratios, risk flags)

# Return Profile & Value Creation
(IRR/MOIC, contribution breakdown: EBITDA growth vs multiple expansion vs deleveraging)

# Sensitivity Analysis
(How returns change under different assumptions)

# Investment Committee Assessment
(IC score breakdown, risk level, key strengths and weaknesses)

# Key IC Questions
(5-7 specific questions the IC should ask)

# Recommendation
(Clear recommendation with conditions/mitigants)

Use markdown tables where appropriate - especially for Sources & Uses, operating projections, and leverage evolution.
Include chart placeholder comments: {{chart:revenue}}, {{chart:ebitda}}, {{chart:debt}}, {{chart:leverage}}, {{chart:sensitivity}}
Maintain professional IC memo tone throughout.
Every section MUST reference specific numbers from the data provided."""
    
    def _build_ic_prompt(
        self,
        financial_data: Dict[str, Any],
        business_context: Dict[str, str],
        scoring_summary: Dict[str, Any],
        contribution_analysis: Dict[str, float],
        user_instructions: Optional[str]
    ) -> str:
        """Build comprehensive prompt with all context."""
        
        company_name = financial_data.get('company_name', 'Target Company')
        industry = financial_data.get('industry', 'Not specified')
        
        # --- Sources & Uses data ---
        su = financial_data.get('sources_uses', {})
        entry_ev = su.get('enterprise_value', financial_data.get('entry_ev', 0))
        debt_amount = su.get('debt', financial_data.get('debt', 0))
        equity_check = su.get('equity', financial_data.get('equity', 0))
        txn_fees = su.get('transaction_fees', financial_data.get('transaction_fees', 0))
        fin_fees = su.get('financing_fees', financial_data.get('financing_fees', 0))
        total_uses = su.get('total_uses', entry_ev + txn_fees + fin_fees)
        total_sources = su.get('total_sources', debt_amount + equity_check)
        cash_on_bs = su.get('cash_on_bs', 0)
        
        # --- Exit data ---
        ex = financial_data.get('exit_results', {})
        exit_ev = ex.get('exit_ev', financial_data.get('exit_ev', 0))
        exit_ebitda = ex.get('exit_ebitda', financial_data.get('exit_ebitda', 0))
        exit_multiple = ex.get('exit_multiple', financial_data.get('exit_multiple', 0))
        exit_debt = ex.get('exit_debt', financial_data.get('exit_debt', 0))
        exit_equity = ex.get('exit_equity_value', financial_data.get('exit_equity_value', 0))
        
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

=== SOURCES & USES ===
USES:
  Enterprise Value: €{entry_ev:.1f}M
  Transaction Fees: €{txn_fees:.1f}M
  Financing Fees: €{fin_fees:.1f}M
  Total Uses: €{total_uses:.1f}M

SOURCES:
  Senior Debt: €{debt_amount:.1f}M ({financial_data.get('debt_to_ebitda', 0):.1f}x EBITDA)
  Equity Check: €{equity_check:.1f}M
  Cash on Balance Sheet: €{cash_on_bs:.1f}M
  Total Sources: €{total_sources:.1f}M

=== TRANSACTION SNAPSHOT ===
Entry EBITDA: €{financial_data.get('entry_ebitda', 0):.1f}M
Entry Multiple: {financial_data.get('entry_multiple', 0):.1f}x
Entry EV: €{entry_ev:.1f}M
Hold Period: {financial_data.get('hold_period', 5)} years

=== OPERATING ASSUMPTIONS ===
Revenue Growth: {financial_data.get('revenue_growth', 0) * 100:.1f}% per year
EBITDA Margin: {financial_data.get('ebitda_margin', 0) * 100:.1f}%
Tax Rate: {financial_data.get('tax_rate', 0.25) * 100:.1f}%
D&A (% Revenue): {financial_data.get('da_pct', 0) * 100:.1f}%
Capex (% Revenue): {financial_data.get('capex_pct', 0) * 100:.1f}%
NWC (% Revenue): {financial_data.get('nwc_pct', 0) * 100:.1f}%

=== DEBT STRUCTURE ===
Interest Rate: {financial_data.get('interest_rate', 0.06) * 100:.1f}%
Annual Amortization: {financial_data.get('amortization_pct', 0) * 100:.1f}% of initial debt
Cash Sweep: {'Enabled at ' + str(round(financial_data.get('cash_sweep_pct', 0) * 100)) + '% of FCF' if financial_data.get('cash_sweep_enabled', False) else 'Disabled'}

=== BASE CASE RETURNS ===
IRR: {financial_data.get('irr', 0) * 100:.1f}%
MOIC: {financial_data.get('moic', 0):.2f}x

=== EXIT SUMMARY ===
Exit EBITDA: €{exit_ebitda:.1f}M
Exit Multiple: {exit_multiple:.1f}x
Exit EV: €{exit_ev:.1f}M
Exit Debt: €{exit_debt:.1f}M
Exit Equity Value: €{exit_equity:.1f}M
Exit Methodology: {financial_data.get('exit_methodology', 'fixed')}

=== RETURN DRIVER CONTRIBUTION ===
EBITDA Growth: {contribution_analysis.get('ebitda_growth', 0):.1f}%
Multiple Expansion: {contribution_analysis.get('multiple_expansion', 0):.1f}%
Deleveraging: {contribution_analysis.get('deleveraging', 0):.1f}%
"""
        
        # Add operating projection year by year
        if 'operating_projection' in financial_data and financial_data['operating_projection']:
            prompt += "\n=== OPERATING PROJECTION (Year by Year) ===\n"
            prompt += f"{'Year':>6} {'Revenue':>10} {'EBITDA':>10} {'FCF':>10}\n"
            for row in financial_data['operating_projection']:
                yr = row.get('year', '?')
                rev = row.get('revenue', 0)
                ebitda = row.get('ebitda', 0)
                fcf = row.get('fcf', 0)
                prompt += f"  {yr:>4}   €{rev:>8.1f}M  €{ebitda:>8.1f}M  €{fcf:>8.1f}M\n"
        
        # Add debt schedule year by year
        if 'debt_schedule' in financial_data and financial_data['debt_schedule']:
            prompt += "\n=== DEBT SCHEDULE (Year by Year) ===\n"
            for row in financial_data['debt_schedule']:
                yr = row.get('year', '?')
                beg = row.get('beginning_debt', 0)
                intr = row.get('interest', 0)
                amort = row.get('scheduled_amort', 0)
                sweep = row.get('cash_sweep', 0)
                end = row.get('ending_debt', 0)
                prompt += f"  Year {yr}: Begin €{beg:.1f}M, Interest €{intr:.1f}M, Amort €{amort:.1f}M, Sweep €{sweep:.1f}M, End €{end:.1f}M\n"

        # Add leverage evolution
        if 'leverage_ratios' in financial_data and financial_data['leverage_ratios']:
            prompt += "\n=== LEVERAGE EVOLUTION ===\n"
            for year_data in financial_data['leverage_ratios']:
                prompt += f"  Year {year_data.get('year')}: {year_data.get('debt_to_ebitda', 0):.1f}x Debt/EBITDA, {year_data.get('interest_coverage', 0):.1f}x Interest Coverage\n"
        
        # Add risk flags
        if 'risk_flags' in financial_data and financial_data['risk_flags']:
            flags = financial_data['risk_flags']
            prompt += f"\n=== RISK FLAGS ===\n"
            prompt += f"  High Leverage (>6x): {'YES - FLAGGED' if flags.get('high_leverage') else 'No'}\n"
            prompt += f"  Low Coverage (<1.5x): {'YES - FLAGGED' if flags.get('low_coverage') else 'No'}\n"
            prompt += f"  Peak Debt/EBITDA: {flags.get('max_debt_to_ebitda', 0):.1f}x\n"
            prompt += f"  Minimum Interest Coverage: {flags.get('min_interest_coverage', 0):.1f}x\n"
        
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
