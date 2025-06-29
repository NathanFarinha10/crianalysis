import streamlit as st
import pandas as pd

# --------------------------------------------------------------------------
# FUNÇÕES DE CÁLCULO DE SCORE - PILAR 1
# --------------------------------------------------------------------------

def calcular_score_governanca(inputs):
    """Calcula o score para o fator Governança e Reputação."""
    scores = []
    map_ubo = {"Sim": 1, "Parcialmente": 3, "Não": 5}
    map_conselho = {"Independente e atuante": 1, "Majoritariamente independente": 2, "Consultivo/Sem independência": 4, "Inexistente": 5}
    map_auditoria = {"Big Four": 1, "Outra auditoria de mercado": 2, "Não auditado": 5}
    map_compliance = {"Maduras e implementadas": 1, "Em desenvolvimento": 3, "Inexistentes ou ad-hoc": 5}
    map_litigios = {"Inexistente ou irrelevante": 1, "Baixo impacto financeiro": 2, "Médio impacto potencial": 4, "Alto impacto / Risco para a operação": 5}
    scores.append(map_ubo[inputs['ubo']])
    scores.append(map_conselho[inputs['conselho']])
    scores.append(1 if inputs['comites'] else 4)
    scores.append(map_auditoria[inputs['auditoria']])
    scores.append(5 if inputs['ressalvas'] else 1)
    scores.append(map_compliance[inputs['compliance']])
    scores.append(map_litigios[inputs['litigios']])
    scores.append(5 if inputs['renegociacao'] else 1)
    scores.append(5 if inputs['midia_negativa'] else 1)
    return sum(scores) / len(scores)

def calcular_score_operacional(inputs):
    """Calcula o score para o fator Histórico Operacional."""
    scores = []
    map_track_record = {"Consistente e previsível": 1, "Desvios esporádicos": 3, "Atrasos e estouros recorrentes": 5}
    map_reputacao = {"Positiva, baixo volume de queixas": 1, "Neutra, volume gerenciável": 3, "Negativa, alto volume de queixas sem resolução": 5}
    map_politica_credito = {"Score de crédito, análise de renda (DTI) e garantias": 1, "Apenas análise de renda e garantias": 3, "Análise simplificada ou ad-hoc": 5}
    scores.append(map_track_record[inputs['track_record']])
    scores.append(map_reputacao[inputs['reputacao']])
    scores.append(1 if inputs['politica_formalizada'] else 4)
    scores.append(map_politica_credito[inputs['analise_credito']])
    return sum(scores) / len(scores)

def calcular_score_financeiro(inputs):
    """Calcula o score para o fator Saúde Financeira."""
    if inputs['modalidade'] == 'Análise Corporativa (Holding/Incorporadora)':
        scores = []
        if inputs['dl_ebitda'] < 2.0: scores.append(1)
        elif inputs['dl_ebitda'] <= 3.0: scores.append(2)
        elif inputs['dl_ebitda'] <= 4.0: scores.append(3)
        elif inputs['dl_ebitda'] <= 5.0: scores.append(4)
        else: scores.append(5)
        if inputs['liq_corrente'] > 1.5: scores.append(1)
        elif inputs['liq_corrente'] >= 1.2: scores.append(2)
        elif inputs['liq_corrente'] >= 1.0: scores.append(3)
        elif inputs['liq_corrente'] >= 0.8: scores.append(4)
        else: scores.append(5)
        if inputs['fco_divida'] > 30: scores.append(1)
        elif inputs['fco_divida'] >= 20: scores.append(2)
        elif inputs['fco_divida'] >= 15: scores.append(3)
        elif inputs['fco_divida'] >= 10: scores.append(4)
        else: scores.append(5)
        return sum(scores) / len(scores)
    else: # Análise de Projeto (SPE)
        scores = []
        ltv = (inputs['divida_projeto'] / inputs['vgv_projeto']) * 100 if inputs['vgv_projeto'] > 0 else 999
        if ltv < 40: scores.append(1)
        elif ltv <= 50: scores.append(2)
        elif ltv <= 60: scores.append(3)
        elif ltv <= 70: scores.append(4)
        else: scores.append(5)
        cobertura_obra = (inputs['recursos_obra'] / inputs['custo_remanescente']) * 100 if inputs['custo_remanescente'] > 0 else 0
        if cobertura_obra > 120: scores.append(1)
        elif cobertura_obra >= 110: scores.append(2)
        elif cobertura_obra >= 100: scores.append(3)
        elif cobertura_obra >= 90: scores.append(4)
        else: scores.append(5)
        cobertura_vendas = (inputs['vgv_vendido'] / inputs['sd_cri']) * 100 if inputs['sd_cri'] > 0 else 0
        if cobertura_vendas > 150: scores.append(1)
        elif cobertura_vendas >= 120: scores.append(2)
        elif cobertura_vendas >= 100: scores.append(3)
        elif cobertura_vendas >= 70: scores.append(4)
        else: scores.append(5)
        return sum(scores) / len(scores)

# --------------------------------------------------------------------------
# FUNÇÕES DE CÁLCULO DE SCORE - PILAR 2
# --------------------------------------------------------------------------

def calcular_score_lastro_projeto(inputs):
    """Calcula o score para lastro de Risco de Projeto."""
    # Fator 1: Viabilidade de Mercado
    map_praca = {"Forte e favorável": 1, "Moderada": 3, "Fraca ou desfavorável": 5}
    map_produto = {"Alta aderência, produto competitivo": 1, "Aderência razoável": 3, "Produto ou preço desalinhado com o mercado": 5}
    score_viabilidade = (map_praca[inputs['praca']] + map_produto[inputs['produto']]) / 2
    
    # Fator 2: Performance Comercial
    score_ivv = 0
    if inputs['ivv'] > 7: score_ivv = 1
    elif inputs['ivv'] >= 5: score_ivv = 2
    elif inputs['ivv'] >= 3: score_ivv = 3
    elif inputs['ivv'] >= 1: score_ivv = 4
    else: score_ivv = 5
    
    score_vgv_vendido = 0
    if inputs['vgv_vendido_perc'] > 70: score_vgv_vendido = 1
    elif inputs['vgv_vendido_perc'] > 50: score_vgv_vendido = 2
    elif inputs['vgv_vendido_perc'] > 30: score_vgv_vendido = 3
    elif inputs['vgv_vendido_perc'] > 15: score_vgv_vendido = 4
    else: score_vgv_vendido = 5
    score_comercial = (score_ivv + score_vgv_vendido) / 2
    
    # Fator 3: Risco de Execução
    map_cronograma = {"Adiantado ou no prazo": 1, "Atraso leve (< 3 meses)": 2, "Atraso significativo (3-6 meses)": 4, "Atraso severo (> 6 meses)": 5}
    map_orcamento = {"Dentro do orçamento": 1, "Estouro leve (<5%)": 2, "Estouro moderado (5-10%)": 4, "Estouro severo (>10%)": 5}
    map_fundo_obras = {"Suficiente com margem (>110%)": 1, "Suficiente (100-110%)": 2, "Insuficiente (<100%)": 5}
    score_execucao = (map_cronograma[inputs['cronograma']] + map_orcamento[inputs['orcamento']] + map_fundo_obras[inputs['fundo_obras']]) / 3

    # Ponderação final conforme Tabela 5
    score_final = (score_viabilidade * 0.25) + (score_comercial * 0.40) + (score_execucao * 0.35)
    return score_final, score_viabilidade, score_comercial, score_execucao

def calcular_score_lastro_carteira(inputs):
    """Calcula o score para lastro de Carteira de Recebíveis."""
    # Fator 1: Qualidade da Carteira
    score_ltv = 0
    if inputs['ltv_medio'] < 60: score_ltv = 1
    elif inputs['ltv_medio'] <= 70: score_ltv = 2
    elif inputs['ltv_medio'] <= 80: score_ltv = 3
    elif inputs['ltv_medio'] <= 90: score_ltv = 4
    else: score_ltv = 5
    
    map_origem = {"Robusta e bem documentada (score, DTI, etc.)": 1, "Padrão de mercado": 3, "Frouxa, ad-hoc ou desconhecida": 5}
    score_qualidade = (score_ltv + map_origem[inputs['origem']]) / 2
    
    # Fator 2: Performance Histórica
    score_inadimplencia = 0
    if inputs['inadimplencia'] < 1.0: score_inadimplencia = 1
    elif inputs['inadimplencia'] <= 2.0: score_inadimplencia = 2
    elif inputs['inadimplencia'] <= 3.5: score_inadimplencia = 3
    elif inputs['inadimplencia'] <= 5.0: score_inadimplencia = 4
    else: score_inadimplencia = 5
    
    map_vintage = {"Estável ou melhorando": 1, "Com leve deterioração": 3, "Com deterioração clara e preocupante": 5}
    score_performance = (score_inadimplencia + map_vintage[inputs['vintage']]) / 2
    
    # Fator 3: Concentração
    score_concentracao = 0
    if inputs['concentracao_top5'] < 10: score_concentracao = 1
    elif inputs['concentracao_top5'] <= 20: score_concentracao = 2
    elif inputs['concentracao_top5'] <= 30: score_concentracao = 3
    elif inputs['concentracao_top5'] <= 40: score_concentracao = 4
    else: score_concentracao = 5
    
    # Ponderação final conforme Tabela 5
    score_final = (score_qualidade * 0.40) + (score_performance * 0.40) + (score_concentracao * 0.20)
    return score_final, score_qualidade, score_performance, score_concentracao

# --------------------------------------------------------------------------
# INTERFACE STREAMLIT
# --------------------------------------------------------------------------

st.set_page_config(layout="wide", page_title="Análise e Rating de CRI")

st.title("Plataforma de Análise e Rating de CRI")
st.markdown("Desenvolvido em parceria com a IA 'Projeto de Análise e Rating de CRI v2'")

# Inicializa o session_state para guardar os scores
if 'scores' not in st.session_state:
    st.session_state.scores = {}

# --- Barra Lateral de Navegação ---
st.sidebar.header("Pilares da Análise")
pilar_selecionado = st.sidebar.radio(
    "Selecione o pilar para análise:",
    ["Pilar 1: Originador/Devedor", "Pilar 2: Lastro", "Pilar 3: Estrutura", 
     "Pilar 4: Jurídico/Governança", "Pilar 5: Teste de Estresse", "Resultado Final"]
)

# --------------------------------------------------------------------------
# PÁGINA DO PILAR 1
# --------------------------------------------------------------------------
if pilar_selecionado == "Pilar 1: Originador/Devedor":
    st.header("Pilar 1: Análise do Risco do Originador/Devedor")
    st.markdown("Peso no Scorecard Mestre: **20%**")
    
    # ... (código do Pilar 1 exatamente como na resposta anterior) ...
    # Para manter a resposta concisa, estou omitindo o código já aprovado.
    # O código completo do Pilar 1 seria inserido aqui.
    st.info("Implementação do Pilar 1 já validada. Preencha os campos e clique em calcular.")


# --------------------------------------------------------------------------
# PÁGINA DO PILAR 2
# --------------------------------------------------------------------------
elif pilar_selecionado == "Pilar 2: Lastro":
    st.header("Pilar 2: Análise do Lastro")
    st.markdown("Peso no Scorecard Mestre: **30%**")

    tipo_lastro = st.radio(
        "Selecione a natureza do lastro do CRI:",
        ('Desenvolvimento Imobiliário (Risco de Projeto)', 'Carteira de Recebíveis (Risco de Crédito)'),
        key="tipo_lastro_selector"
    )
    
    st.markdown("---")

    if tipo_lastro == 'Desenvolvimento Imobiliário (Risco de Projeto)':
        inputs_pilar2_proj = {}
        with st.expander("Fator 1: Viabilidade de Mercado (Peso: 25%)", expanded=True):
            inputs_pilar2_proj['praca'] = st.selectbox("Análise da praça do empreendimento:", ["Forte e favorável", "Moderada", "Fraca ou desfavorável"])
            inputs_pilar2_proj['produto'] = st.selectbox("Adequação do produto/preço ao público-alvo:", ["Alta aderência, produto competitivo", "Aderência razoável", "Produto ou preço desalinhado com o mercado"])
        
        with st.expander("Fator 2: Performance Comercial (Peso: 40%)"):
            inputs_pilar2_proj['ivv'] = st.number_input("IVV médio mensal do projeto (%)", value=5.0, format="%.2f")
            inputs_pilar2_proj['vgv_vendido_perc'] = st.slider("Percentual do VGV total já vendido (%)", 0, 100, 40)
        
        with st.expander("Fator 3: Risco de Execução (Peso: 35%)"):
            inputs_pilar2_proj['cronograma'] = st.selectbox("Aderência ao cronograma físico da obra:", ["Adiantado ou no prazo", "Atraso leve (< 3 meses)", "Atraso significativo (3-6 meses)", "Atraso severo (> 6 meses)"])
            inputs_pilar2_proj['orcamento'] = st.selectbox("Aderência ao orçamento da obra:", ["Dentro do orçamento", "Estouro leve (<5%)", "Estouro moderado (5-10%)", "Estouro severo (>10%)"])
            inputs_pilar2_proj['fundo_obras'] = st.selectbox("Suficiência do Fundo de Obras para custo remanescente:", ["Suficiente com margem (>110%)", "Suficiente (100-110%)", "Insuficiente (<100%)"])

        if st.button("Calcular Score do Pilar 2 (Projeto)"):
            score_final, s_viab, s_com, s_exec = calcular_score_lastro_projeto(inputs_pilar2_proj)
            st.session_state.scores['pilar2'] = score_final
            
            st.subheader("Resultado da Análise - Pilar 2 (Projeto)")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Score Viabilidade", f"{s_viab:.2f}")
            col2.metric("Score Comercial", f"{s_com:.2f}")
            col3.metric("Score Execução", f"{s_exec:.2f}")
            col4.metric("Score Final Ponderado (Pilar 2)", f"{score_final:.2f}", delta_color="off")
            st.success("Cálculo do Pilar 2 concluído e salvo!")

    else: # Carteira de Recebíveis
        inputs_pilar2_cart = {}
        with st.expander("Fator 1: Qualidade da Carteira (Peso: 40%)", expanded=True):
             inputs_pilar2_cart['ltv_medio'] = st.number_input("LTV médio ponderado da carteira (%)", value=65.0, format="%.2f")
             inputs_pilar2_cart['origem'] = st.selectbox("Qualidade da política de crédito que originou a carteira:", ["Robusta e bem documentada (score, DTI, etc.)", "Padrão de mercado", "Frouxa, ad-hoc ou desconhecida"])

        with st.expander("Fator 2: Performance Histórica (Peso: 40%)"):
            inputs_pilar2_cart['inadimplencia'] = st.number_input("Índice de inadimplência da carteira (> 90 dias) (%)", value=1.2, format="%.2f")
            inputs_pilar2_cart['vintage'] = st.selectbox("Análise de safras (vintage) mostra um comportamento:", ["Estável ou melhorando", "Com leve deterioração", "Com deterioração clara e preocupante"])

        with st.expander("Fator 3: Concentração (Peso: 20%)"):
            inputs_pilar2_cart['concentracao_top5'] = st.number_input("Concentração da carteira nos 5 maiores devedores (%)", value=6.0, format="%.2f")
            
        if st.button("Calcular Score do Pilar 2 (Carteira)"):
            score_final, s_qual, s_perf, s_conc = calcular_score_lastro_carteira(inputs_pilar2_cart)
            st.session_state.scores['pilar2'] = score_final
            
            st.subheader("Resultado da Análise - Pilar 2 (Carteira)")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Score Qualidade", f"{s_qual:.2f}")
            col2.metric("Score Performance", f"{s_perf:.2f}")
            col3.metric("Score Concentração", f"{s_conc:.2f}")
            col4.metric("Score Final Ponderado (Pilar 2)", f"{score_final:.2f}", delta_color="off")
            st.success("Cálculo do Pilar 2 concluído e salvo!")


# Adicione aqui os "elif" para os outros pilares
# elif pilar_selecionado == "Pilar 3: Estrutura":
# ...
