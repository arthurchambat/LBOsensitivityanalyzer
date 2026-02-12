"""
LBO Risk Analyzer - Application Streamlit
Interface utilisateur pour analyser les risques d'un LBO avec l'IA
"""
import streamlit as st
import pandas as pd
import numpy as np
from lbo import LBOModel
from risk_analyzer import RiskAnalyzer


# Configuration de la page
st.set_page_config(
    page_title="LBO Risk Analyzer",
    page_icon="📊",
    layout="wide"
)

# Titre
st.title("📊 LBO Risk Analyzer")
st.markdown("*Analyse de sensibilité et évaluation des risques par IA*")

# Sidebar pour les paramètres
st.sidebar.header("Paramètres du LBO")

# Paramètres de base
enterprise_value = st.sidebar.number_input(
    "Valeur d'entreprise (€M)",
    min_value=10.0,
    max_value=1000.0,
    value=100.0,
    step=10.0
)

ebitda = st.sidebar.number_input(
    "EBITDA initial (€M)",
    min_value=1.0,
    max_value=200.0,
    value=10.0,
    step=1.0
)

debt_percentage = st.sidebar.slider(
    "Pourcentage de dette (%)",
    min_value=30,
    max_value=80,
    value=60,
    step=5
) / 100

interest_rate = st.sidebar.slider(
    "Taux d'intérêt (%)",
    min_value=2.0,
    max_value=10.0,
    value=5.0,
    step=0.5
) / 100

ebitda_growth_rate = st.sidebar.slider(
    "Croissance EBITDA annuelle (%)",
    min_value=-5.0,
    max_value=15.0,
    value=5.0,
    step=1.0
) / 100

exit_multiple = st.sidebar.slider(
    "Multiple de sortie (EV/EBITDA)",
    min_value=5.0,
    max_value=12.0,
    value=8.0,
    step=0.5
)

years = st.sidebar.number_input(
    "Horizon d'investissement (années)",
    min_value=3,
    max_value=10,
    value=5,
    step=1
)

# Création du modèle
lbo = LBOModel(
    enterprise_value=enterprise_value,
    ebitda=ebitda,
    debt_percentage=debt_percentage,
    interest_rate=interest_rate,
    ebitda_growth_rate=ebitda_growth_rate,
    years=years
)

# Tabs principales
tab1, tab2, tab3 = st.tabs(["📈 Résultats", "🎯 Analyse de Sensibilité", "🤖 Analyse IA"])

# Tab 1: Résultats
with tab1:
    st.header("Résultats du LBO")
    
    # Métriques clés
    col1, col2, col3, col4 = st.columns(4)
    
    summary = lbo.get_summary(exit_multiple)
    
    with col1:
        st.metric("TRI", f"{summary['irr']:.1f}%")
    
    with col2:
        st.metric("MOIC", f"{summary['moic']:.2f}x")
    
    with col3:
        st.metric("Dette/EBITDA Initial", f"{summary['initial_debt_ebitda']:.1f}x")
    
    with col4:
        st.metric("Dette/EBITDA Final", f"{summary['final_debt_ebitda']:.1f}x")
    
    # Détails des flux de trésorerie
    st.subheader("Projection des flux de trésorerie")
    cash_flows = lbo.calculate_cash_flows()
    st.dataframe(cash_flows.style.format({
        'ebitda': '{:.1f}',
        'interest': '{:.1f}',
        'fcf': '{:.1f}',
        'debt_repayment': '{:.1f}',
        'debt_balance': '{:.1f}'
    }), width='stretch')
    
    # Graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Évolution de l'EBITDA")
        st.line_chart(cash_flows.set_index('year')['ebitda'])
    
    with col2:
        st.subheader("Évolution de la dette")
        st.line_chart(cash_flows.set_index('year')['debt_balance'])

# Tab 2: Analyse de sensibilité
with tab2:
    st.header("Analyse de Sensibilité")
    
    # Choix du paramètre à analyser
    sensitivity_param = st.selectbox(
        "Paramètre à analyser",
        ["Croissance EBITDA", "Taux d'intérêt", "Multiple de sortie", "% Dette"]
    )
    
    # Génération de la sensibilité
    if st.button("Générer l'analyse"):
        with st.spinner("Calcul en cours..."):
            if sensitivity_param == "Croissance EBITDA":
                param_range = np.linspace(-0.05, 0.15, 11)
                results = []
                
                for growth in param_range:
                    temp_lbo = LBOModel(enterprise_value, ebitda, debt_percentage, 
                                       interest_rate, growth, years)
                    irr = temp_lbo.calculate_irr(exit_multiple)
                    moic = temp_lbo.calculate_moic(exit_multiple)
                    results.append({
                        'Croissance (%)': growth * 100,
                        'TRI (%)': irr,
                        'MOIC': moic
                    })
                
            elif sensitivity_param == "Taux d'intérêt":
                param_range = np.linspace(0.02, 0.10, 9)
                results = []
                
                for rate in param_range:
                    temp_lbo = LBOModel(enterprise_value, ebitda, debt_percentage, 
                                       rate, ebitda_growth_rate, years)
                    irr = temp_lbo.calculate_irr(exit_multiple)
                    moic = temp_lbo.calculate_moic(exit_multiple)
                    results.append({
                        'Taux (%)': rate * 100,
                        'TRI (%)': irr,
                        'MOIC': moic
                    })
            
            elif sensitivity_param == "Multiple de sortie":
                param_range = np.linspace(5, 12, 15)
                results = []
                
                for multiple in param_range:
                    irr = lbo.calculate_irr(multiple)
                    moic = lbo.calculate_moic(multiple)
                    results.append({
                        'Multiple': multiple,
                        'TRI (%)': irr,
                        'MOIC': moic
                    })
            
            else:  # % Dette
                param_range = np.linspace(0.3, 0.8, 11)
                results = []
                
                for debt_pct in param_range:
                    temp_lbo = LBOModel(enterprise_value, ebitda, debt_pct, 
                                       interest_rate, ebitda_growth_rate, years)
                    irr = temp_lbo.calculate_irr(exit_multiple)
                    moic = temp_lbo.calculate_moic(exit_multiple)
                    results.append({
                        'Dette (%)': debt_pct * 100,
                        'TRI (%)': irr,
                        'MOIC': moic
                    })
            
            # Affichage des résultats
            df_sensitivity = pd.DataFrame(results)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("TRI en fonction du paramètre")
                st.line_chart(df_sensitivity.set_index(df_sensitivity.columns[0])['TRI (%)'])
            
            with col2:
                st.subheader("MOIC en fonction du paramètre")
                st.line_chart(df_sensitivity.set_index(df_sensitivity.columns[0])['MOIC'])
            
            st.subheader("Tableau de sensibilité")
            st.dataframe(df_sensitivity.style.format({
                df_sensitivity.columns[0]: '{:.1f}',
                'TRI (%)': '{:.1f}',
                'MOIC': '{:.2f}'
            }), use_container_width=True)

# Tab 3: Analyse IA
with tab3:
    st.header("🤖 Analyse des Risques par IA")
    
    st.info("Cette fonctionnalité utilise GPT-4 pour analyser les risques de votre LBO. Assurez-vous d'avoir configuré votre clé API OpenAI dans le fichier .env")
    
    scenario_description = st.text_area(
        "Description du scénario (optionnel)",
        placeholder="Ex: Secteur technologique, entreprise en croissance rapide, marché concurrentiel...",
        height=100
    )
    
    if st.button("🚀 Analyser les risques", type="primary"):
        try:
            with st.spinner("Analyse en cours... Cela peut prendre quelques secondes."):
                analyzer = RiskAnalyzer()
                analysis = analyzer.analyze_lbo_risk(summary, scenario_description)
                
                st.success("Analyse terminée!")
                st.markdown("---")
                st.markdown(analysis)
        
        except ValueError as e:
            st.error(f"Erreur de configuration: {e}")
            st.info("Veuillez configurer votre clé API OpenAI dans le fichier .env")
        
        except Exception as e:
            st.error(f"Erreur lors de l'analyse: {e}")
    
    # Section de comparaison de scénarios
    st.markdown("---")
    st.subheader("Comparaison de scénarios")
    
    if st.button("Comparer: Base vs Pessimiste vs Optimiste"):
        try:
            with st.spinner("Génération et comparaison des scénarios..."):
                # Scénario de base
                base_summary = summary
                
                # Scénario pessimiste
                lbo_pessimist = LBOModel(
                    enterprise_value, ebitda, debt_percentage,
                    interest_rate * 1.2, ebitda_growth_rate * 0.5, years
                )
                pessimist_summary = lbo_pessimist.get_summary(exit_multiple * 0.8)
                
                # Scénario optimiste
                lbo_optimist = LBOModel(
                    enterprise_value, ebitda, debt_percentage,
                    interest_rate * 0.8, ebitda_growth_rate * 1.5, years
                )
                optimist_summary = lbo_optimist.get_summary(exit_multiple * 1.2)
                
                # Analyse comparative
                analyzer = RiskAnalyzer()
                scenarios = [
                    ("Base", base_summary),
                    ("Pessimiste", pessimist_summary),
                    ("Optimiste", optimist_summary)
                ]
                comparison = analyzer.compare_scenarios(scenarios)
                
                st.success("Comparaison terminée!")
                st.markdown("---")
                st.markdown(comparison)
        
        except ValueError as e:
            st.error(f"Erreur de configuration: {e}")
        
        except Exception as e:
            st.error(f"Erreur lors de la comparaison: {e}")

# Footer
st.markdown("---")
st.markdown("*LBO Risk Analyzer - Powered by AI*")
