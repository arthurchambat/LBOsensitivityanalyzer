"""
Risk Analyzer with AI
Utilise l'IA pour analyser les risques d'un LBO
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


class RiskAnalyzer:
    """Analyseur de risques utilisant l'API OpenAI"""
    
    def __init__(self):
        """Initialise le client OpenAI"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == 'your_api_key_here':
            raise ValueError("Veuillez configurer OPENAI_API_KEY dans le fichier .env")
        
        self.client = OpenAI(api_key=api_key)
    
    def analyze_lbo_risk(self, lbo_summary, scenario_description=""):
        """
        Analyse les risques d'un LBO en utilisant l'IA
        
        Args:
            lbo_summary: Dictionnaire contenant les métriques du LBO
            scenario_description: Description optionnelle du scénario
        
        Returns:
            str: Analyse des risques par l'IA
        """
        prompt = self._build_prompt(lbo_summary, scenario_description)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Tu es un expert en private equity spécialisé dans l'analyse de LBO. Tu fournis des analyses détaillées et objectives des risques financiers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Erreur lors de l'analyse IA: {str(e)}"
    
    def _build_prompt(self, lbo_summary, scenario_description):
        """Construit le prompt pour l'API OpenAI"""
        prompt = f"""Analyse les risques du LBO suivant:

**Paramètres de l'opération:**
- Valeur d'entreprise: {lbo_summary['enterprise_value']:.1f} €M
- Equity investi: {lbo_summary['equity_invested']:.1f} €M
- Dette: {lbo_summary['debt']:.1f} €M
- Dette/EBITDA initial: {lbo_summary['initial_debt_ebitda']:.1f}x
- Dette/EBITDA final: {lbo_summary['final_debt_ebitda']:.1f}x

**Performance projetée:**
- TRI: {lbo_summary['irr']:.1f}%
- MOIC: {lbo_summary['moic']:.2f}x

{f"**Scénario:** {scenario_description}" if scenario_description else ""}

Fournis une analyse structurée incluant:
1. **Risques principaux** (3-4 points clés)
2. **Niveaux de levier** (évaluation du niveau d'endettement)
3. **Sensibilité** (facteurs de risque critiques)
4. **Recommandations** (actions pour atténuer les risques)

Sois concis et factuel."""
        
        return prompt
    
    def compare_scenarios(self, scenarios):
        """
        Compare plusieurs scénarios de LBO
        
        Args:
            scenarios: Liste de tuples (nom_scenario, lbo_summary)
        
        Returns:
            str: Analyse comparative
        """
        if len(scenarios) < 2:
            return "Au moins 2 scénarios sont nécessaires pour une comparaison."
        
        prompt = "Compare les scénarios LBO suivants:\n\n"
        
        for i, (name, summary) in enumerate(scenarios, 1):
            prompt += f"""**Scénario {i}: {name}**
- TRI: {summary['irr']:.1f}%
- MOIC: {summary['moic']:.2f}x
- Dette/EBITDA: {summary['initial_debt_ebitda']:.1f}x → {summary['final_debt_ebitda']:.1f}x

"""
        
        prompt += """Fournis une analyse comparative:
1. Quel scénario présente le meilleur profil risque/rendement?
2. Quels sont les trade-offs principaux?
3. Quelle recommandation ferais-tu?"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Tu es un expert en private equity spécialisé dans l'analyse comparative de LBO."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1200
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Erreur lors de l'analyse comparative: {str(e)}"


def check_api_key_available() -> bool:
    """
    Check if OpenAI API key is available in environment.
    
    Returns:
        True if key is available, False otherwise
    """
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    return api_key is not None and api_key != '' and api_key != 'sk-your-openai-api-key-here'
