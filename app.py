import streamlit as st
import pandas as pd

def render_pilar1_originador():
    """
    Renderiza os inputs e a lógica de cálculo para o Pilar 1.
    """
    st.header("Pilar 1: Análise do Originadorssss/Devedor (Peso: 20%)")

    # Dicionário para armazenar os inputs do usuário
    inputs_pilar1 = {}

    # --- Seção de Inputs ---
    # Título alterado para maior clareza na aplicação
    st.subheader("Coleta de Dados para Análise")

    with st.expander("Clique para inserir os dados de análise do Originador"):
        
        st.info("Para as avaliações qualitativas, utilize a escala de 1 (Risco Mais Baixo) a 5 (Risco Mais Alto).")

        # Fatores Qualitativos
        st.markdown("**Governança e Reputação (Peso: 30%)**")
        inputs_pilar1['gov_score'] = st.slider(
            "Qualidade da Governança (Conselho, Políticas)", 1, 5, 3,
            help="1: Estruturada e independente. 5: Familiar e opaca."
        )
        inputs_pilar1['rep_score'] = st.slider(
            "Risco Reputacional (Litígios, Mídia)", 1, 5, 3,
            help="1: Sem 'red flags'. 5: Múltiplos alertas."
        )
        st.text_area("Comentários sobre Governança e Reputação", key="gov_comments")

        st.markdown("**Histórico Operacional (Peso: 30%)**")
        inputs_pilar1['track_record_score'] = st.slider(
            "Track Record de Entregas", 1, 5, 3,
            help="1: Consistente e no prazo. 5: Atrasos recorrentes."
        )
        inputs_pilar1['politica_credito_score'] = st.slider(
            "Qualidade da Política de Crédito", 1, 5, 3,
            help="1: Robusta e documentada. 5: Ad-hoc/informal."
        )
        st.text_area("Comentários sobre o Histórico Operacional", key="hist_comments")

        st.markdown("**Saúde Financeira (Peso: 40%)**")
        col1, col2 = st.columns(2)
        with col1:
            inputs_pilar1['dl_ebitda'] = st.number_input("Dívida Líquida / EBITDA", value=3.0, format="%.2f")
        with col2:
            inputs_pilar1['liquidez_corrente'] = st.number_input("Índice de Liquidez Corrente", value=1.2, format="%.2f")
        inputs_pilar1['fco_divida_percent'] = st.number_input("FCO / Dívida Total (%)", value=15.0, format="%.2f")
        st.text_area("Comentários sobre a Saúde Financeira", key="fin_comments")

    return inputs_pilar1

def calcular_e_exibir_score_pilar1(inputs):
    """
    Calcula o score do Pilar 1 com base nos inputs e exibe o scorecard.
    """
    # Título alterado para maior clareza na aplicação
    st.subheader("Resultado da Análise: Scorecard do Originador")

    # Funções para mapear métricas financeiras para a pontuação de 1-5
    # Baseado nas faixas de referência da Tabela 2 da metodologia
    def map_dl_ebitda_to_score(value):
        if value < 2.0: return 1
        if value < 3.0: return 2
        if value < 4.0: return 3
        if value <= 5.0: return 4
        return 5

    def map_liquidez_to_score(value):
        if value > 1.5: return 1
        if value > 1.2: return 2
        if value >= 1.0: return 3
        if value > 0.8: return 4
        return 5

    def map_fco_divida_to_score(value):
        if value > 30: return 1
        if value > 20: return 2
        if value > 15: return 3
        if value >= 10: return 4
        return 5

    # Scores qualitativos (já na escala 1-5)
    score_gov = inputs['gov_score']
    score_rep = inputs['rep_score']
    score_track_record = inputs['track_record_score']
    score_politica_credito = inputs['politica_credito_score']
    
    # Scores quantitativos convertidos para a escala de 1-5
    score_dl_ebitda = map_dl_ebitda_to_score(inputs['dl_ebitda'])
    score_liquidez = map_liquidez_to_score(inputs['liquidez_corrente'])
    score_fco_divida = map_fco_divida_to_score(inputs['fco_divida_percent'])

    # Pesos conforme Tabela 2 da metodologia
    pesos = {'gov_rep': 0.30, 'hist_op': 0.30, 'saude_fin': 0.40}

    # Pontuação média por subfator
    pontuacao_media_gov_rep = (score_gov + score_rep) / 2
    pontuacao_media_hist_op = (score_track_record + score_politica_credito) / 2
    pontuacao_media_saude_fin = (score_dl_ebitda + score_liquidez + score_fco_divida) / 3

    # Cálculo dos scores ponderados
    score_ponderado_gov_rep = pontuacao_media_gov_rep * pesos['gov_rep']
    score_ponderado_hist_op = pontuacao_media_hist_op * pesos['hist_op']
    score_ponderado_saude_fin = pontuacao_media_saude_fin * pesos['saude_fin']
    
    score_final_pilar1 = score_ponderado_gov_rep + score_ponderado_hist_op + score_ponderado_saude_fin
    
    # Exibição do Scorecard (simulando a Tabela 2 da metodologia)
    tabela_data = {
        'Fator de Risco': ['Governança e Reputação', 'Histórico Operacional', 'Saúde Financeira'],
        'Peso': [f"{p*100:.0f}%" for p in pesos.values()],
        'Pontuação Média do Fator': [f"{pontuacao_media_gov_rep:.2f}", f"{pontuacao_media_hist_op:.2f}", f"{pontuacao_media_saude_fin:.2f}"],
        'Score Ponderado': [f"{score_ponderado_gov_rep:.2f}", f"{score_ponderado_hist_op:.2f}", f"{score_ponderado_saude_fin:.2f}"]
    }
    df_scorecard = pd.DataFrame(tabela_data)
    st.table(df_scorecard.set_index('Fator de Risco'))

    st.metric(label="**Pontuação Final Ponderada (Pilar 1)**", value=f"{score_final_pilar1:.2f}")
    
    return score_final_pilar1

# --- Layout Principal da Aplicação ---
st.set_page_config(layout="wide")
st.title("Plataforma de Análise e Rating de CRI")

# Dicionário para armazenar todos os scores dos pilares
if 'scores' not in st.session_state:
    st.session_state.scores = {}

# Coleta de Inputs
pilar1_inputs = render_pilar1_originador()

# Botão para processar a análise
if st.button("Calcular Score do Pilar 1"):
    if pilar1_inputs:
        score_pilar1 = calcular_e_exibir_score_pilar1(pilar1_inputs)
        st.session_state.scores['pilar1'] = score_pilar1
