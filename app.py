import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.graph_objects as go

# ==============================================================================
# INICIALIZAÇÃO E FUNÇÕES AUXILIARES
# ==============================================================================

def inicializar_session_state():
    """Garante que todos os valores de input e scores sejam inicializados no st.session_state apenas uma vez."""
    if 'state_initialized' not in st.session_state:
        st.session_state.state_initialized = True
        st.session_state.scores = {}
        st.session_state.resultados_pilar5 = None

        # Valores padrão para todos os widgets. A chave corresponde ao parâmetro 'key' de cada widget.
        defaults = {
            'pilar_selecionado': 'Pilar 1: Originador/Devedor',
            # Pilar 1
            'hist_emissor': 'Primeira emissão ou histórico negativo', 'exp_socios': 'Experiência moderada', 'ubo': 'Sim',
            'conselho': 'Consultivo/Sem independência', 'comites': False, 'auditoria': 'Outra auditoria de mercado',
            'ressalvas': False, 'compliance': 'Em desenvolvimento', 'litigios': 'Baixo impacto financeiro',
            'renegociacao': False, 'midia_negativa': False, 'exp_similar': 'Experiência relevante em segmentos correlatos',
            'track_record': 'Desvios esporádicos', 'reputacao': 'Neutra, volume gerenciável', 'politica_formalizada': True,
            'analise_credito': 'Apenas análise de renda e garantias', 'modalidade_financeira': 'Análise Corporativa (Holding/Incorporadora)',
            'dl_ebitda': 3.0, 'liq_corrente': 1.2, 'fco_divida': 15.0, 'divida_projeto': 50000000.0, 'vgv_projeto': 100000000.0,
            'custo_remanescente': 30000000.0, 'recursos_obra': 35000000.0, 'vgv_vendido': 60000000.0, 'sd_cri': 50000000.0,
            # Pilar 2
            'tipo_lastro': 'Desenvolvimento Imobiliário (Risco de Projeto)', 'praca': 'Moderada', 'produto': 'Aderência razoável',
            'ivv': 5.0, 'vgv_vendido_perc': 40, 'cronograma': 'Atraso leve (< 3 meses)', 'orcamento': 'Estouro leve (<5%)',
            'fundo_obras': 'Suficiente (100-110%)', 'ltv_medio': 65.0, 'origem': 'Padrão de mercado', 'inadimplencia': 1.2,
            'vintage': 'Com leve deterioração', 'concentracao_top5': 6.0,
            # Pilar 3
            'subordinacao': 10.0, 'waterfall': 'Padrão de mercado com alguma ambiguidade', 'fundo_reserva_pmts': 3.0,
            'fundo_reserva_regra': True, 'sobrecolateralizacao': 110.0, 'spread_excedente': 1.5,
            'tipo_garantia': 'Alienação Fiduciária de Imóveis', 'ltv_garantia': 60.0, 'liquidez_garantia': 'Média (ex: salas comerciais, loteamentos)',
            # Pilar 4
            'independencia': 'Partes relacionadas com mitigação de conflitos', 'retencao_risco': True,
            'historico_decisoes': 'Decisões mistas, alguns waivers aprovados', 'ag_fiduciario': 'Média, cumpre o papel protocolar',
            'securitizadora': 'Média, com histórico misto', 'servicer': 'Padrão de mercado', 'covenants': 'Padrão, com alguma subjetividade',
            'pareceres': 'Padrão, cumprem requisitos formais', 'relatorios': 'Média, cumprem o mínimo regulatório',
            # Pilar 5
            'saldo_lastro': 100000000.0, 'saldo_cri_p5': 80000000.0, 'taxa_lastro': 12.0, 'taxa_cri_p5': 10.0,
            'prazo': 60, 'despesas': 10000.0, 'inad_base': 2.0, 'prep_base': 10.0, 'sev_base': 30, 'lag_base': 12,
            'inad_mod': 5.0, 'prep_mod': 5.0, 'sev_mod': 50, 'lag_mod': 18, 'inad_sev': 10.0, 'prep_sev': 2.0, 'sev_sev': 70,
            'lag_sev': 24,
            # Resultado Final
            'ajuste_final': 0, 'rating_subordinada': 'Não Avaliado', 'justificativa_final': ''
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

def create_gauge_chart(score, title):
    if score is None: score = 0
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        title={'text': title, 'font': {'size': 20}},
        gauge={
            'axis': {'range': [1, 5], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "black", 'thickness': 0.3}, 'bgcolor': "white", 'borderwidth': 1, 'bordercolor': "gray",
            'steps': [
                {'range': [1, 2.75], 'color': '#28a745'},
                {'range': [2.75, 3.5], 'color': '#ffc107'},
                {'range': [3.5, 5], 'color': '#dc3545'}],
        }))
    fig.update_layout(height=250, margin={'t':40, 'b':40, 'l':30, 'r':30})
    return fig

def converter_score_para_rating(score):
    if score is None: return "N/A"
    if score <= 1.25: return 'brAAA(sf)'
    elif score <= 1.75: return 'brAA(sf)'
    elif score <= 2.25: return 'brA(sf)'
    elif score <= 2.75: return 'brBBB(sf)'
    elif score <= 3.25: return 'brBB(sf)'
    elif score <= 4.00: return 'brB(sf)'
    else: return 'brCCC(sf)'

def ajustar_rating(rating_base, notches):
    escala = ['brCCC(sf)', 'brB(sf)', 'brBB(sf)', 'brBBB(sf)', 'brA(sf)', 'brAA(sf)', 'brAAA(sf)']
    try:
        idx_base = escala.index(rating_base)
        idx_final = max(0, min(len(escala) - 1, idx_base + notches))
        return escala[idx_final]
    except (ValueError, TypeError):
        return rating_base

# ==============================================================================
# FUNÇÕES DE CÁLCULO DE SCORE
# ==============================================================================
def calcular_score_governanca():
    scores = []
    map_ubo = {"Sim": 1, "Parcialmente": 3, "Não": 5}
    map_conselho = {"Independente e atuante": 1, "Majoritariamente independente": 2, "Consultivo/Sem independência": 4, "Inexistente": 5}
    map_auditoria = {"Big Four": 1, "Outra auditoria de mercado": 2, "Não auditado": 5}
    map_compliance = {"Maduras e implementadas": 1, "Em desenvolvimento": 3, "Inexistentes ou ad-hoc": 5}
    map_litigios = {"Inexistente ou irrelevante": 1, "Baixo impacto financeiro": 2, "Médio impacto potencial": 4, "Alto impacto / Risco para a operação": 5}
    map_emissor = {"Emissor recorrente com bom histórico": 1, "Poucas emissões ou histórico misto": 3, "Primeira emissão ou histórico negativo": 4}
    map_socios = {"Altamente experiente e com boa reputação": 1, "Experiência moderada": 3, "Inexperiente ou com reputação questionável": 5}
    scores.append(map_ubo[st.session_state.ubo]); scores.append(map_conselho[st.session_state.conselho])
    scores.append(1 if st.session_state.comites else 4); scores.append(map_auditoria[st.session_state.auditoria])
    scores.append(5 if st.session_state.ressalvas else 1); scores.append(map_compliance[st.session_state.compliance])
    scores.append(map_litigios[st.session_state.litigios]); scores.append(5 if st.session_state.renegociacao else 1)
    scores.append(5 if st.session_state.midia_negativa else 1); scores.append(map_emissor[st.session_state.hist_emissor])
    scores.append(map_socios[st.session_state.exp_socios])
    return sum(scores) / len(scores) if scores else 5

def calcular_score_operacional():
    scores = []
    map_track_record = {"Consistente e previsível": 1, "Desvios esporádicos": 3, "Atrasos e estouros recorrentes": 5}
    map_reputacao = {"Positiva, baixo volume de queixas": 1, "Neutra, volume gerenciável": 3, "Negativa, alto volume de queixas sem resolução": 5}
    map_politica_credito = {"Score de crédito, análise de renda (DTI) e garantias": 1, "Apenas análise de renda e garantias": 3, "Análise simplificada ou ad-hoc": 5}
    map_exp_similar = {"Extensa e comprovada no segmento específico": 1, "Experiência relevante em segmentos correlatos": 2, "Experiência limitada ou em outros segmentos": 4, "Iniciante/Nenhuma": 5}
    scores.append(map_track_record[st.session_state.track_record]); scores.append(map_reputacao[st.session_state.reputacao])
    scores.append(1 if st.session_state.politica_formalizada else 4); scores.append(map_politica_credito[st.session_state.analise_credito])
    scores.append(map_exp_similar[st.session_state.exp_similar])
    return sum(scores) / len(scores) if scores else 5

def calcular_score_financeiro():
    if st.session_state.modalidade_financeira == 'Análise Corporativa (Holding/Incorporadora)':
        scores = []
        dl_ebitda = st.session_state.dl_ebitda
        if dl_ebitda < 2.0: scores.append(1)
        elif dl_ebitda <= 3.0: scores.append(2)
        elif dl_ebitda <= 4.0: scores.append(3)
        elif dl_ebitda <= 5.0: scores.append(4)
        else: scores.append(5)
        liq_corrente = st.session_state.liq_corrente
        if liq_corrente > 1.5: scores.append(1)
        elif liq_corrente >= 1.2: scores.append(2)
        elif liq_corrente >= 1.0: scores.append(3)
        elif liq_corrente >= 0.8: scores.append(4)
        else: scores.append(5)
        fco_divida = st.session_state.fco_divida
        if fco_divida > 30: scores.append(1)
        elif fco_divida >= 20: scores.append(2)
        elif fco_divida >= 15: scores.append(3)
        elif fco_divida >= 10: scores.append(4)
        else: scores.append(5)
        return sum(scores) / len(scores) if scores else 5
    else: # Análise de Projeto (SPE)
        scores = []
        vgv_projeto = st.session_state.vgv_projeto
        ltv = (st.session_state.divida_projeto / vgv_projeto) * 100 if vgv_projeto > 0 else 999
        if ltv < 40: scores.append(1)
        elif ltv <= 50: scores.append(2)
        elif ltv <= 60: scores.append(3)
        elif ltv <= 70: scores.append(4)
        else: scores.append(5)
        custo_remanescente = st.session_state.custo_remanescente
        cobertura_obra = (st.session_state.recursos_obra / custo_remanescente) * 100 if custo_remanescente > 0 else 0
        if cobertura_obra > 120: scores.append(1)
        elif cobertura_obra >= 110: scores.append(2)
        elif cobertura_obra >= 100: scores.append(3)
        elif cobertura_obra >= 90: scores.append(4)
        else: scores.append(5)
        sd_cri = st.session_state.sd_cri
        cobertura_vendas = (st.session_state.vgv_vendido / sd_cri) * 100 if sd_cri > 0 else 0
        if cobertura_vendas > 150: scores.append(1)
        elif cobertura_vendas >= 120: scores.append(2)
        elif cobertura_vendas >= 100: scores.append(3)
        elif cobertura_vendas >= 70: scores.append(4)
        else: scores.append(5)
        return sum(scores) / len(scores) if scores else 5

def calcular_score_lastro_projeto():
    map_praca = {"Forte e favorável": 1, "Moderada": 3, "Fraca ou desfavorável": 5}
    map_produto = {"Alta aderência, produto competitivo": 1, "Aderência razoável": 3, "Produto ou preço desalinhado com o mercado": 5}
    score_viabilidade = (map_praca[st.session_state.praca] + map_produto[st.session_state.produto]) / 2
    ivv = st.session_state.ivv
    if ivv > 7: score_ivv = 1
    elif ivv >= 5: score_ivv = 2
    elif ivv >= 3: score_ivv = 3
    elif ivv >= 1: score_ivv = 4
    else: score_ivv = 5
    vgv_vendido_perc = st.session_state.vgv_vendido_perc
    if vgv_vendido_perc > 70: score_vgv_vendido = 1
    elif vgv_vendido_perc > 50: score_vgv_vendido = 2
    elif vgv_vendido_perc > 30: score_vgv_vendido = 3
    elif vgv_vendido_perc > 15: score_vgv_vendido = 4
    else: score_vgv_vendido = 5
    score_comercial = (score_ivv + score_vgv_vendido) / 2
    map_cronograma = {"Adiantado ou no prazo": 1, "Atraso leve (< 3 meses)": 2, "Atraso significativo (3-6 meses)": 4, "Atraso severo (> 6 meses)": 5}
    map_orcamento = {"Dentro do orçamento": 1, "Estouro leve (<5%)": 2, "Estouro moderado (5-10%)": 4, "Estouro severo (>10%)": 5}
    map_fundo_obras = {"Suficiente com margem (>110%)": 1, "Suficiente (100-110%)": 2, "Insuficiente (<100%)": 5}
    score_execucao = (map_cronograma[st.session_state.cronograma] + map_orcamento[st.session_state.orcamento] + map_fundo_obras[st.session_state.fundo_obras]) / 3
    score_final = (score_viabilidade * 0.25) + (score_comercial * 0.40) + (score_execucao * 0.35)
    return score_final

def calcular_score_lastro_carteira():
    ltv_medio = st.session_state.ltv_medio
    if ltv_medio < 60: score_ltv = 1
    elif ltv_medio <= 70: score_ltv = 2
    elif ltv_medio <= 80: score_ltv = 3
    elif ltv_medio <= 90: score_ltv = 4
    else: score_ltv = 5
    map_origem = {"Robusta e bem documentada (score, DTI, etc.)": 1, "Padrão de mercado": 3, "Frouxa, ad-hoc ou desconhecida": 5}
    score_qualidade = (score_ltv + map_origem[st.session_state.origem]) / 2
    inadimplencia = st.session_state.inadimplencia
    if inadimplencia < 1.0: score_inadimplencia = 1
    elif inadimplencia <= 2.0: score_inadimplencia = 2
    elif inadimplencia <= 3.5: score_inadimplencia = 3
    elif inadimplencia <= 5.0: score_inadimplencia = 4
    else: score_inadimplencia = 5
    map_vintage = {"Estável ou melhorando": 1, "Com leve deterioração": 3, "Com deterioração clara e preocupante": 5}
    score_performance = (score_inadimplencia + map_vintage[st.session_state.vintage]) / 2
    concentracao_top5 = st.session_state.concentracao_top5
    if concentracao_top5 < 10: score_concentracao = 1
    elif concentracao_top5 <= 20: score_concentracao = 2
    elif concentracao_top5 <= 30: score_concentracao = 3
    elif concentracao_top5 <= 40: score_concentracao = 4
    else: score_concentracao = 5
    score_final = (score_qualidade * 0.40) + (score_performance * 0.40) + (score_concentracao * 0.20)
    return score_final

def calcular_score_estrutura():
    scores_capital = []
    subordinacao = st.session_state.subordinacao
    if subordinacao > 20: scores_capital.append(1)
    elif subordinacao >= 15: scores_capital.append(2)
    elif subordinacao >= 10: scores_capital.append(3)
    elif subordinacao >= 5: scores_capital.append(4)
    else: scores_capital.append(5)
    map_waterfall = {"Clara, protetiva e bem definida": 1, "Padrão de mercado com alguma ambiguidade": 3, "Ambígua, com brechas ou prejudicial à série": 5}
    scores_capital.append(map_waterfall[st.session_state.waterfall])
    score_capital = sum(scores_capital) / len(scores_capital)
    scores_reforco = []
    fundo_reserva_pmts = st.session_state.fundo_reserva_pmts
    if fundo_reserva_pmts > 3: score_fundo = 1
    elif fundo_reserva_pmts >= 2: score_fundo = 2
    elif fundo_reserva_pmts >= 1: score_fundo = 3
    else: score_fundo = 5
    if not st.session_state.fundo_reserva_regra:
        score_fundo = min(5, score_fundo + 1)
    scores_reforco.append(score_fundo)
    oc = st.session_state.sobrecolateralizacao
    if oc > 120: scores_reforco.append(1)
    elif oc >= 110: scores_reforco.append(2)
    elif oc >= 105: scores_reforco.append(3)
    elif oc > 100: scores_reforco.append(4)
    else: scores_reforco.append(5)
    spread = st.session_state.spread_excedente
    if spread > 3: scores_reforco.append(1)
    elif spread >= 2: scores_reforco.append(2)
    elif spread >= 1: scores_reforco.append(3)
    elif spread > 0: scores_reforco.append(4)
    else: scores_reforco.append(5)
    score_reforco = sum(scores_reforco) / len(scores_reforco)
    scores_garantias = []
    map_tipo_garantia = {"Alienação Fiduciária de Imóveis": 1, "Cessão Fiduciária de Recebíveis": 2, "Fiança ou Aval": 4, "Sem garantia real (Fidejussória)": 5}
    scores_garantias.append(map_tipo_garantia[st.session_state.tipo_garantia])
    ltv = st.session_state.ltv_garantia
    if ltv < 50: scores_garantias.append(1)
    elif ltv <= 60: scores_garantias.append(2)
    elif ltv <= 70: scores_garantias.append(3)
    elif ltv <= 80: scores_garantias.append(4)
    else: scores_garantias.append(5)
    map_liquidez_garantia = {"Alta (ex: aptos residenciais em capital)": 1, "Média (ex: salas comerciais, loteamentos)": 3, "Baixa (ex: imóvel de uso específico, rural)": 5}
    scores_garantias.append(map_liquidez_garantia[st.session_state.liquidez_garantia])
    score_garantias = sum(scores_garantias) / len(scores_garantias)
    score_final = (score_capital * 0.40) + (score_reforco * 0.30) + (score_garantias * 0.30)
    return score_final

def calcular_score_juridico():
    scores_conflito = []
    map_independencia = {"Totalmente independentes": 1, "Partes relacionadas com mitigação de conflitos": 3, "Mesmo grupo econômico com alto potencial de conflito": 5}
    scores_conflito.append(map_independencia[st.session_state.independencia])
    scores_conflito.append(1 if st.session_state.retencao_risco else 4)
    map_historico = {"Alinhado aos interesses dos investidores": 1, "Decisões mistas, alguns waivers aprovados": 3, "Histórico de decisões que beneficiam o devedor": 5}
    scores_conflito.append(map_historico[st.session_state.historico_decisoes])
    score_conflito = sum(scores_conflito) / len(scores_conflito)
    scores_prestadores = []
    map_ag_fiduciario = {"Alta, com histórico de proatividade": 1, "Média, cumpre o papel protocolar": 3, "Baixa, passivo ou com histórico negativo": 5}
    scores_prestadores.append(map_ag_fiduciario[st.session_state.ag_fiduciario])
    map_securitizadora = {"Alta, experiente e com bom histórico": 1, "Média, com histórico misto": 3, "Nova ou com histórico negativo": 5}
    scores_prestadores.append(map_securitizadora[st.session_state.securitizadora])
    map_servicer = {"Alta, com processos e tecnologia robustos": 1, "Padrão de mercado": 2, "Fraca ou inadequada": 4, "Não aplicável / Não avaliado": 2}
    scores_prestadores.append(map_servicer[st.session_state.servicer])
    score_prestadores = sum(scores_prestadores) / len(scores_prestadores)
    scores_contratual = []
    map_covenants = {"Fortes, objetivos e com gatilhos claros": 1, "Padrão, com alguma subjetividade": 3, "Fracos, subjetivos ou fáceis de contornar": 5}
    scores_contratual.append(map_covenants[st.session_state.covenants])
    map_pareceres = {"Abrangentes e conclusivos (escritório 1ª linha)": 1, "Padrão, cumprem requisitos formais": 2, "Limitados ou com ressalvas": 4}
    scores_contratual.append(map_pareceres[st.session_state.pareceres])
    map_relatorios = {"Alta, detalhados e frequentes": 1, "Média, cumprem o mínimo regulatório": 3, "Baixa, informações inconsistentes ou atrasadas": 5}
    scores_contratual.append(map_relatorios[st.session_state.relatorios])
    score_contratual = sum(scores_contratual) / len(scores_contratual)
    score_final = (score_conflito * 0.50) + (score_prestadores * 0.30) + (score_contratual * 0.20)
    return score_final

@st.cache_data
def run_cashflow_simulation(cenario_premissas, saldo_lastro, saldo_cri_p5, taxa_lastro, taxa_cri_p5, prazo, despesas):
    taxa_inadimplencia_aa = cenario_premissas['inadimplencia'] / 100
    taxa_prepagamento_aa = cenario_premissas['prepagamento'] / 100
    severidade_perda = cenario_premissas['severidade'] / 100
    lag_recuperacao = cenario_premissas['lag']
    taxa_juros_lastro_am = (1 + taxa_lastro/100)**(1/12) - 1
    taxa_remuneracao_cri_am = (1 + taxa_cri_p5/100)**(1/12) - 1
    taxa_inadimplencia_am = (1 + taxa_inadimplencia_aa)**(1/12) - 1
    taxa_prepagamento_am = (1 + taxa_prepagamento_aa)**(1/12) - 1

    saldo_lastro_sim = saldo_lastro
    saldo_cri_sim = saldo_cri_p5
    
    historico = []
    defaults_pendentes = {}

    for mes in range(1, prazo + 1):
        if saldo_lastro_sim < 1 or saldo_cri_sim < 1: break

        juros_recebido = saldo_lastro_sim * taxa_juros_lastro_am
        
        prazo_rem = prazo - mes + 1
        amortizacao_programada_lastro = npf.ppmt(taxa_juros_lastro_am, 1, prazo_rem, -saldo_lastro_sim) if taxa_juros_lastro_am > 0 else (saldo_lastro_sim / prazo_rem if prazo_rem > 0 else 0)
        
        novos_defaults = saldo_lastro_sim * taxa_inadimplencia_am
        defaults_pendentes[mes] = novos_defaults
        
        prepagamentos = (saldo_lastro_sim - novos_defaults) * taxa_prepagamento_am
        
        recuperacao_do_mes = 0
        mes_recuperacao = mes - lag_recuperacao
        if mes_recuperacao in defaults_pendentes:
            valor_a_recuperar = defaults_pendentes.pop(mes_recuperacao)
            recuperacao_do_mes = valor_a_recuperar * (1 - severidade_perda)

        caixa_disponivel = juros_recebido + amortizacao_programada_lastro + prepagamentos + recuperacao_do_mes
        caixa_disponivel -= despesas
        
        juros_devido_cri = saldo_cri_sim * taxa_remuneracao_cri_am
        juros_pago_cri = min(juros_devido_cri, caixa_disponivel)
        caixa_disponivel -= juros_pago_cri
        
        amortizacao_paga_cri = min(caixa_disponivel, saldo_cri_sim)
        
        saldo_lastro_sim -= (amortizacao_programada_lastro + prepagamentos + novos_defaults)
        saldo_cri_anterior = saldo_cri_sim
        saldo_cri_sim -= amortizacao_paga_cri
        
        amortizacao_programada_cri = npf.ppmt(taxa_remuneracao_cri_am, 1, prazo_rem, -saldo_cri_anterior) if taxa_remuneracao_cri_am > 0 else (saldo_cri_anterior / prazo_rem if prazo_rem > 0 else 0)
        servico_divida_programado = juros_devido_cri + amortizacao_programada_cri
        
        dscr = (juros_pago_cri + amortizacao_paga_cri) / servico_divida_programado if servico_divida_programado > 0 else 1.0
        
        historico.append({'Mês': mes, 'Saldo Devedor Lastro': saldo_lastro_sim, 'Saldo Devedor CRI': saldo_cri_sim, 'DSCR': dscr})

    perda_principal = max(0, saldo_cri_sim)
    return perda_principal, pd.DataFrame(historico)

# ==============================================================================
# CORPO PRINCIPAL DA APLICAÇÃO
# ==============================================================================
st.set_page_config(layout="wide", page_title="Análise e Rating de CRI")
st.title("Plataforma de Análise e Rating de CRI")
st.markdown("Desenvolvido em parceria com a IA 'Projeto de Análise e Rating de CRI v2'")

inicializar_session_state()

st.sidebar.header("Pilares da Análise")
st.sidebar.radio("Selecione o pilar para análise:",
    ["Pilar 1: Originador/Devedor", "Pilar 2: Lastro", "Pilar 3: Estrutura",
     "Pilar 4: Jurídico/Governança", "Pilar 5: Teste de Estresse", "Resultado Final"],
    key='pilar_selecionado')

if st.session_state.pilar_selecionado == "Pilar 1: Originador/Devedor":
    st.header("Pilar 1: Análise do Risco do Originador/Devedor")
    st.markdown("Peso no Scorecard Mestre: **20%**")

    with st.expander("Fator 1: Governança e Reputação (Peso: 30%)", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Histórico de emissões no mercado de capitais:", ["Emissor recorrente com bom histórico", "Poucas emissões ou histórico misto", "Primeira emissão ou histórico negativo"], key='hist_emissor', help="Avalia a maturidade e governança da empresa ao acessar o mercado.")
            st.radio("Os beneficiários finais (UBOs) estão claramente identificados?", ["Sim", "Parcialmente", "Não"], key='ubo', help="Transparência na estrutura societária. Nota 1 para 'Sim', 5 para 'Não'.")
            st.selectbox("Maturidade das políticas de compliance e risco:", ["Maduras e implementadas", "Em desenvolvimento", "Inexistentes ou ad-hoc"], key='compliance', help="Políticas robustas e testadas reduzem o risco operacional e legal.")
            st.checkbox("Houve ressalvas relevantes na última auditoria?", key='ressalvas', help="Marcado significa que houve ressalvas, o que aumenta o risco.")
            st.checkbox("Há histórico de atraso ou renegociação de dívidas com credores?", key='renegociacao', help="Marcado indica maior risco de crédito e reputacional.")
        with c2:
            st.selectbox("Experiência do quadro societário/executivo:", ["Altamente experiente e com boa reputação", "Experiência moderada", "Inexperiente ou com reputação questionável"], key='exp_socios', help="Analisa o histórico e a reputação dos tomadores de decisão.")
            st.selectbox("Qual a estrutura do conselho de administração?", ["Independente e atuante", "Majoritariamente independente", "Consultivo/Sem independência", "Inexistente"], key='conselho', help="Conselhos independentes melhoram a governança.")
            st.selectbox("As demonstrações financeiras são auditadas por:", ["Big Four", "Outra auditoria de mercado", "Não auditado"], key='auditoria', help="Auditoria por empresas de primeira linha aumenta a credibilidade das informações.")
            st.selectbox("Nível de litígios relevantes (cíveis, fiscais, ambientais):", ["Inexistente ou irrelevante", "Baixo impacto financeiro", "Médio impacto potencial", "Alto impacto / Risco para a operação"], key='litigios', help="Processos relevantes podem indicar passivos ocultos.")
            st.checkbox("Possui comitê de auditoria e/ou riscos formalizado?", key='comites', help="Comitês especializados são um sinal de governança madura.")
            st.checkbox("Identificado envolvimento em notícias negativas de grande impacto ou investigações?", key='midia_negativa', help="Marcado indica alto risco reputacional.")

    with st.expander("Fator 2: Histórico Operacional (Peso: 30%)"):
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Experiência em projetos semelhantes:", ["Extensa e comprovada no segmento específico", "Experiência relevante em segmentos correlatos", "Experiência limitada ou em outros segmentos", "Iniciante/Nenhuma"], key='exp_similar', help="Avalia o track record do devedor em projetos com o mesmo perfil de risco.")
            st.selectbox("Reputação e nível de satisfação de clientes (ex: Reclame Aqui):", ["Positiva, baixo volume de queixas", "Neutra, volume gerenciável", "Negativa, alto volume de queixas sem resolução"], key='reputacao', help="A satisfação do cliente final impacta a performance de carteiras e a imagem da empresa.")
        with c2:
            st.selectbox("Histórico de entrega de projetos (prazo e orçamento):", ["Consistente e previsível", "Desvios esporádicos", "Atrasos e estouros recorrentes"], key='track_record', help="Avalia a capacidade de execução da companhia.")
            st.selectbox("A análise de crédito para os recebíveis inclui:", ["Score de crédito, análise de renda (DTI) e garantias", "Apenas análise de renda e garantias", "Análise simplificada ou ad-hoc"], key='analise_credito', help="Reflete a qualidade do processo que origina o lastro.")
            st.checkbox("A política de concessão de crédito é formalizada e documentada?", key='politica_formalizada', help="Processos formalizados reduzem o risco de má originação de crédito.")

    with st.expander("Fator 3: Saúde Financeira (Peso: 40%)"):
        st.radio("Selecione a modalidade de análise financeira:", ('Análise Corporativa (Holding/Incorporadora)', 'Análise de Projeto (SPE)'), key='modalidade_financeira', horizontal=True)
        st.markdown("---")
        if st.session_state.modalidade_financeira == 'Análise Corporativa (Holding/Incorporadora)':
            c1, c2, c3 = st.columns(3)
            with c1: st.number_input("Dívida Líquida / EBITDA", key='dl_ebitda', help="Mede a alavancagem. Idealmente abaixo de 3.0x para o setor.")
            with c2: st.number_input("Liquidez Corrente", key='liq_corrente', help="Mede a capacidade de pagar dívidas de curto prazo. Idealmente acima de 1.2.")
            with c3: st.number_input("FCO / Dívida Total (%)", key='fco_divida', help="Capacidade de pagar a dívida com o caixa gerado. Idealmente acima de 15-20%.")
            
            st.markdown("##### Visualização dos Indicadores Corporativos")
            df_chart = pd.DataFrame({"Valor": [st.session_state.dl_ebitda, st.session_state.liq_corrente], "Benchmark Ruim": [5.0, 0.8], "Benchmark Bom": [2.0, 1.5]}, index=["Dívida/EBITDA", "Liq. Corrente"])
            st.bar_chart(df_chart)

        else: # Análise de Projeto (SPE)
            c1, c2 = st.columns(2)
            with c1:
                st.number_input("Dívida Total do Projeto (R$)", key='divida_projeto')
                st.number_input("Custo Remanescente da Obra (R$)", key='custo_remanescente')
                st.number_input("VGV já Vendido (R$)", key='vgv_vendido')
            with c2:
                st.number_input("VGV Total do Projeto (R$)", key='vgv_projeto')
                st.number_input("Recursos Disponíveis para Obra (Caixa + CRI) (R$)", key='recursos_obra')
                st.number_input("Saldo Devedor do CRI (R$)", key='sd_cri')

            st.markdown("##### Visualização dos Indicadores do Projeto")
            custo_rem = st.session_state.custo_remanescente
            sd_cri = st.session_state.sd_cri
            cobertura_obra_perc = (st.session_state.recursos_obra / custo_rem) if custo_rem > 0 else 0
            cobertura_vendas_perc = (st.session_state.vgv_vendido / sd_cri) if sd_cri > 0 else 0
            st.progress(min(cobertura_obra_perc, 1.0), text=f"Cobertura de Custo da Obra: {cobertura_obra_perc:.1%}")
            st.progress(min(cobertura_vendas_perc, 1.0), text=f"Cobertura da Dívida por Vendas: {cobertura_vendas_perc:.1%}")

    st.markdown("---")
    if st.button("Calcular Score do Pilar 1", use_container_width=True):
        score_final_pilar1 = (calcular_score_governanca() * 0.30) + (calcular_score_operacional() * 0.30) + (calcular_score_financeiro() * 0.40)
        st.session_state.scores['pilar1'] = score_final_pilar1
        
        st.plotly_chart(create_gauge_chart(score_final_pilar1, "Score Final Ponderado (Pilar 1)"), use_container_width=True)
        with st.expander("Entenda o Cálculo do Score"):
            st.markdown("O Score Final deste pilar é uma média ponderada dos scores dos três fatores, com pesos baseados na Tabela 2 da metodologia:")
            st.latex(r'''Score_{P1} = (Score_{Gov} \times 0.3) + (Score_{Op} \times 0.3) + (Score_{Fin} \times 0.4)''')
        st.success("Cálculo do Pilar 1 concluído e salvo na sessão!")


elif st.session_state.pilar_selecionado == "Pilar 2: Lastro":
    st.header("Pilar 2: Análise do Lastro")
    st.markdown("Peso no Scorecard Mestre: **30%**")

    st.radio("Selecione a natureza do lastro do CRI:",('Desenvolvimento Imobiliário (Risco de Projeto)', 'Carteira de Recebíveis (Risco de Crédito)'), key="tipo_lastro", horizontal=True)
    st.markdown("---")

    if st.session_state.tipo_lastro == 'Desenvolvimento Imobiliário (Risco de Projeto)':
        with st.expander("Fator 1: Viabilidade de Mercado (Peso: 25%)", expanded=True):
            st.selectbox("Análise da praça do empreendimento:", ["Forte e favorável", "Moderada", "Fraca ou desfavorável"], key='praca', help="Analisa o potencial de crescimento, renda e infraestrutura da região do projeto.")
            st.selectbox("Adequação do produto/preço ao público-alvo:", ["Alta aderência, produto competitivo", "Aderência razoável", "Produto ou preço desalinhado com o mercado"], key='produto', help="Verifica se o produto imobiliário faz sentido para a demanda e os preços locais.")
        with st.expander("Fator 2: Performance Comercial (Peso: 40%)"):
            st.number_input("IVV médio mensal do projeto (%)", key='ivv', help="Índice de Velocidade de Vendas. Um IVV > 5-7% é forte e reduz o risco de carregamento de estoque.")
            st.slider("Percentual do VGV total já vendido (%)", 0, 100, key='vgv_vendido_perc', help="Percentual de vendas já contratadas. Quanto maior, menor o risco comercial futuro.")
        with st.expander("Fator 3: Risco de Execução (Peso: 35%)"):
            st.selectbox("Aderência ao cronograma físico da obra:", ["Adiantado ou no prazo", "Atraso leve (< 3 meses)", "Atraso significativo (3-6 meses)", "Atraso severo (> 6 meses)"], key='cronograma', help="Atrasos na obra impactam custos e o cronograma de recebimentos.")
            st.selectbox("Aderência ao orçamento da obra:", ["Dentro do orçamento", "Estouro leve (<5%)", "Estouro moderado (5-10%)", "Estouro severo (>10%)"], key='orcamento', help="Estouros no orçamento podem demandar novos aportes ou colocar o projeto em risco.")
            st.selectbox("Suficiência do Fundo de Obras para custo remanescente:", ["Suficiente com margem (>110%)", "Suficiente (100-110%)", "Insuficiente (<100%)"], key='fundo_obras', help="O Fundo de Obras garante a conclusão da construção mesmo com vendas fracas.")

        if st.button("Calcular Score do Pilar 2 (Projeto)", use_container_width=True):
            score_final = calcular_score_lastro_projeto()
            st.session_state.scores['pilar2'] = score_final
            st.plotly_chart(create_gauge_chart(score_final, "Score Final Ponderado (Pilar 2)"), use_container_width=True)
            with st.expander("Entenda o Cálculo do Score"):
                st.markdown("O Score Final é uma média ponderada dos fatores, com pesos baseados na Tabela 5 (Projeto) da metodologia:")
                st.latex(r'''Score_{P2} = (Score_{Viab.} \times 0.25) + (Score_{Comercial} \times 0.40) + (Score_{Exec.} \times 0.35)''')
            st.success("Cálculo do Pilar 2 concluído e salvo!")
    else: # Carteira de Recebíveis
        with st.expander("Fator 1: Qualidade da Carteira (Peso: 40%)", expanded=True):
             st.number_input("LTV médio ponderado da carteira (%)", key='ltv_medio', help="Loan-to-Value. Quanto menor, maior a proteção em caso de execução da garantia.")
             st.selectbox("Qualidade da política de crédito que originou a carteira:", ["Robusta e bem documentada (score, DTI, etc.)", "Padrão de mercado", "Frouxa, ad-hoc ou desconhecida"], key='origem', help="Uma boa política de crédito na origem reduz a chance de inadimplência futura.")
        with st.expander("Fator 2: Performance Histórica (Peso: 40%)"):
            st.number_input("Índice de inadimplência da carteira (> 90 dias) (%)", key='inadimplencia', help="Principal indicador de performance da carteira.")
            st.selectbox("Análise de safras (vintage) mostra um comportamento:", ["Estável ou melhorando", "Com leve deterioração", "Com deterioração clara e preocupante"], key='vintage', help="Analisa se as safras mais novas performam melhor ou pior que as antigas.")
        with st.expander("Fator 3: Concentração (Peso: 20%)"):
            st.number_input("Concentração da carteira nos 5 maiores devedores (%)", key='concentracao_top5', help="Mede o risco de um default individual impactar a operação. Quanto menor, mais pulverizado e melhor.")
        if st.button("Calcular Score do Pilar 2 (Carteira)", use_container_width=True):
            score_final = calcular_score_lastro_carteira()
            st.session_state.scores['pilar2'] = score_final
            st.plotly_chart(create_gauge_chart(score_final, "Score Final Ponderado (Pilar 2)"), use_container_width=True)
            with st.expander("Entenda o Cálculo do Score"):
                st.markdown("O Score Final é uma média ponderada dos fatores, com pesos baseados na Tabela 5 (Carteira) da metodologia:")
                st.latex(r'''Score_{P2} = (Score_{Qualidade} \times 0.40) + (Score_{Perf.} \times 0.40) + (Score_{Conc.} \times 0.20)''')
            st.success("Cálculo do Pilar 2 concluído e salvo!")


elif st.session_state.pilar_selecionado == "Pilar 3: Estrutura":
    st.header("Pilar 3: Análise da Estrutura e Mecanismos de Reforço de Crédito")
    st.markdown("Peso no Scorecard Mestre: **30%**")

    with st.expander("Fator 1: Estrutura de Capital (Peso: 40%)", expanded=True):
        st.number_input("Nível de subordinação (%) para a série em análise", key='subordinacao', help="Principal 'colchão' de proteção da série. Quanto maior, menor o risco.")
        st.selectbox("Qualidade da Cascata de Pagamentos (Waterfall)", ["Clara, protetiva e bem definida", "Padrão de mercado com alguma ambiguidade", "Ambígua, com brechas ou prejudicial à série"], key='waterfall', help="A ordem de pagamentos deve ser clara e proteger a série analisada.")
    with st.expander("Fator 2: Mecanismos de Reforço e Liquidez (Peso: 30%)"):
        st.number_input("Tamanho do Fundo de Reserva (em nº de pagamentos)", key='fundo_reserva_pmts', help="Fundo de liquidez para cobrir insuficiências de caixa. Ideal > 3 PMTs.")
        st.checkbox("O Fundo de Reserva possui mecanismo de recomposição obrigatória?", key='fundo_reserva_regra', help="Se o fundo for usado, ele deve ser recomposto. A ausência de regra é um ponto de risco.")
        st.number_input("Índice de Sobrecolateralização (%)", key='sobrecolateralizacao', help="Ex: 110 para 110%. Ocorre quando o valor do lastro é maior que o da dívida, criando um reforço.")
        st.number_input("Spread Excedente anualizado (%)", key='spread_excedente', help="Diferença positiva entre a taxa do lastro e o custo do CRI. Pode ser usado para cobrir primeiras perdas.")
    with st.expander("Fator 3: Qualidade das Garantias (Peso: 30%)"):
        st.selectbox("Tipo de garantia predominante na estrutura", ["Alienação Fiduciária de Imóveis", "Cessão Fiduciária de Recebíveis", "Fiança ou Aval", "Sem garantia real (Fidejussória)"], key='tipo_garantia', help="Alienação Fiduciária é a garantia mais forte no mercado imobiliário brasileiro.")
        st.number_input("LTV Médio Ponderado das garantias (%)", key='ltv_garantia', help="Loan-to-Value da garantia física. < 60% é considerado forte.")
        st.selectbox("Liquidez estimada da garantia", ["Alta (ex: aptos residenciais em capital)", "Média (ex: salas comerciais, loteamentos)", "Baixa (ex: imóvel de uso específico, rural)"], key='liquidez_garantia', help="Facilidade de transformar a garantia em caixa num cenário de execução.")

    st.markdown("---")
    if st.button("Calcular Score do Pilar 3", use_container_width=True):
        score_final = calcular_score_estrutura()
        st.session_state.scores['pilar3'] = score_final
        st.plotly_chart(create_gauge_chart(score_final, "Score Final Ponderado (Pilar 3)"), use_container_width=True)
        with st.expander("Entenda o Cálculo do Score"):
            st.markdown("O Score Final é uma média ponderada dos fatores, com pesos baseados na Tabela 6 da metodologia:")
            st.latex(r'''Score_{P3} = (Score_{Capital} \times 0.40) + (Score_{Reforços} \times 0.30) + (Score_{Garantias} \times 0.30)''')
        st.success("Cálculo do Pilar 3 concluído e salvo!")


elif st.session_state.pilar_selecionado == "Pilar 4: Jurídico/Governança":
    st.header("Pilar 4: Análise Jurídica e de Governança da Operação")
    st.markdown("Peso no Scorecard Mestre: **20%**")

    with st.expander("Fator 1: Conflitos de Interesse (Peso: 50%)", expanded=True):
        st.selectbox("Nível de independência entre Originador, Securitizadora e Gestor", ["Totalmente independentes", "Partes relacionadas com mitigação de conflitos", "Mesmo grupo econômico com alto potencial de conflito"], key='independencia', help="Operações entre partes do mesmo grupo podem gerar decisões que não priorizam o investidor do CRI.")
        st.checkbox("O originador/cedente retém a cota subordinada ou outra forma de risco relevante?", key='retencao_risco', help="A retenção de risco alinha os interesses do originador aos dos investidores.")
        st.selectbox("Histórico de decisões em assembleias do estruturador/originador", ["Alinhado aos interesses dos investidores", "Decisões mistas, alguns waivers aprovados", "Histórico de decisões que beneficiam o devedor"], key='historico_decisoes', help="Um histórico de perdões (waivers) de covenants pode indicar uma governança fraca.")
    with st.expander("Fator 2: Qualidade dos Prestadores de Serviço (Peso: 30%)"):
        st.selectbox("Reputação e experiência do Agente Fiduciário", ["Alta, com histórico de proatividade", "Média, cumpre o papel protocolar", "Baixa, passivo ou com histórico negativo"], key='ag_fiduciario', help="O Agente Fiduciário é o 'advogado' dos investidores; sua proatividade é fundamental.")
        st.selectbox("Reputação e experiência da Securitizadora", ["Alta, experiente e com bom histórico", "Média, com histórico misto", "Nova ou com histórico negativo"], key='securitizadora', help="A securitizadora é o 'cérebro' da operação.")
        st.selectbox("Qualidade do Agente de Cobrança (Servicer)", ["Alta, com processos e tecnologia robustos", "Padrão de mercado", "Fraca ou inadequada", "Não aplicável / Não avaliado"], key='servicer', help="Essencial para carteiras pulverizadas. Uma cobrança ineficiente aumenta a perda.")
    with st.expander("Fator 3: Robustez Contratual e Transparência (Peso: 20%)"):
        st.selectbox("Qualidade e rigidez dos Covenants da operação", ["Fortes, objetivos e com gatilhos claros", "Padrão, com alguma subjetividade", "Fracos, subjetivos ou fáceis de contornar"], key='covenants', help="Covenants são as 'regras do jogo' que o devedor deve seguir. Regras fracas oferecem pouca proteção.")
        st.selectbox("Qualidade dos pareceres jurídicos (true sale, etc.)", ["Abrangentes e conclusivos (escritório 1ª linha)", "Padrão, cumprem requisitos formais", "Limitados ou com ressalvas"], key='pareceres', help="O parecer de 'true sale' garante que o lastro está legalmente separado do originador.")
        st.selectbox("Qualidade e frequência dos relatórios de acompanhamento", ["Alta, detalhados e frequentes", "Média, cumprem o mínimo regulatório", "Baixa, informações inconsistentes ou atrasadas"], key='relatorios', help="A transparência e qualidade da informação são vitais para o monitoramento do risco.")

    st.markdown("---")
    if st.button("Calcular Score do Pilar 4", use_container_width=True):
        score_final = calcular_score_juridico()
        st.session_state.scores['pilar4'] = score_final
        st.plotly_chart(create_gauge_chart(score_final, "Score Final Ponderado (Pilar 4)"), use_container_width=True)
        with st.expander("Entenda o Cálculo do Score"):
            st.markdown("O Score Final é uma média ponderada dos fatores, com pesos baseados na Tabela 7 da metodologia:")
            st.latex(r'''Score_{P4} = (Score_{Conflitos} \times 0.50) + (Score_{Prestadores} \times 0.30) + (Score_{Contratual} \times 0.20)''')
        st.success("Cálculo do Pilar 4 concluído e salvo!")


elif st.session_state.pilar_selecionado == "Pilar 5: Teste de Estresse":
    st.header("Pilar 5: Modelagem de Fluxo de Caixa e Testes de Estresse")
    st.markdown("Esta etapa representa a validação quantitativa da resiliência da operação.")

    with st.expander("Inputs do Modelo (Dados da Operação)", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.number_input("Saldo Devedor do Lastro (R$)", key='saldo_lastro')
            st.number_input("Saldo Devedor do CRI (Série Sênior) (R$)", key='saldo_cri_p5')
        with c2:
            st.number_input("Taxa Média do Lastro (% a.a.)", key='taxa_lastro')
            st.number_input("Taxa da Série Sênior (% a.a.)", key='taxa_cri_p5')
        with c3:
            st.number_input("Prazo Remanescente (meses)", key='prazo', format="%d")
            st.number_input("Despesas Fixas Mensais (R$)", key='despesas')

    st.markdown("---")
    st.subheader("Definição das Premissas dos Cenários")
    cenarios = {}
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### Cenário Base")
        cenarios['base'] = {'inadimplencia': st.slider("Inadimplência (% a.a.)", 0.0, 10.0, key="inad_base"), 'prepagamento': st.slider("Pré-pagamento (% a.a.)", 0.0, 20.0, key="prep_base"), 'severidade': st.slider("Severidade da Perda (%)", 0, 100, key="sev_base"), 'lag': st.slider("Lag de Recuperação (meses)", 0, 24, key="lag_base", format="%d")}
    with c2:
        st.markdown("#### Cenário Moderado")
        cenarios['moderado'] = {'inadimplencia': st.slider("Inadimplência (% a.a.)", 0.0, 20.0, key="inad_mod"), 'prepagamento': st.slider("Pré-pagamento (% a.a.)", 0.0, 20.0, key="prep_mod"), 'severidade': st.slider("Severidade da Perda (%)", 0, 100, key="sev_mod"), 'lag': st.slider("Lag de Recuperação (meses)", 0, 24, key="lag_mod", format="%d")}
    with c3:
        st.markdown("#### Cenário Severo")
        cenarios['severo'] = {'inadimplencia': st.slider("Inadimplência (% a.a.)", 0.0, 40.0, key="inad_sev"), 'prepagamento': st.slider("Pré-pagamento (% a.a.)", 0.0, 20.0, key="prep_sev"), 'severidade': st.slider("Severidade da Perda (%)", 0, 100, key="sev_sev"), 'lag': st.slider("Lag de Recuperação (meses)", 0, 24, key="lag_sev", format="%d")}

    st.markdown("---")
    if st.button("Executar Simulação de Fluxo de Caixa", use_container_width=True):
        with st.spinner("Simulando cenários... Por favor, aguarde."):
            perda_base, df_base = run_cashflow_simulation(cenarios['base'], st.session_state.saldo_lastro, st.session_state.saldo_cri_p5, st.session_state.taxa_lastro, st.session_state.taxa_cri_p5, st.session_state.prazo, st.session_state.despesas)
            perda_mod, df_mod = run_cashflow_simulation(cenarios['moderado'], st.session_state.saldo_lastro, st.session_state.saldo_cri_p5, st.session_state.taxa_lastro, st.session_state.taxa_cri_p5, st.session_state.prazo, st.session_state.despesas)
            perda_sev, df_sev = run_cashflow_simulation(cenarios['severo'], st.session_state.saldo_lastro, st.session_state.saldo_cri_p5, st.session_state.taxa_lastro, st.session_state.taxa_cri_p5, st.session_state.prazo, st.session_state.despesas)
            st.session_state.resultados_pilar5 = {'perda_base': perda_base, 'perda_moderado': perda_mod, 'perda_severo': perda_sev}
        
        st.subheader("Resultados da Simulação")
        rc1, rc2, rc3 = st.columns(3)
        rc1.metric("Perda de Principal (Base)", f"R$ {st.session_state.resultados_pilar5['perda_base']:,.2f}")
        rc2.metric("Perda de Principal (Moderado)", f"R$ {st.session_state.resultados_pilar5['perda_moderado']:,.2f}")
        rc3.metric("Perda de Principal (Severo)", f"R$ {st.session_state.resultados_pilar5['perda_severo']:,.2f}")
        
        st.markdown("---")
        st.subheader("Gráficos de Performance")
        df_dscr = pd.DataFrame({'Base': df_base.set_index('Mês')['DSCR'],'Moderado': df_mod.set_index('Mês')['DSCR'],'Severo': df_sev.set_index('Mês')['DSCR']})
        st.line_chart(df_dscr, use_container_width=True)
        st.caption("Gráfico 1: DSCR (Cobertura do Serviço da Dívida) ao longo do tempo.")
        df_saldos = pd.DataFrame({'Lastro (Base)': df_base.set_index('Mês')['Saldo Devedor Lastro'],'CRI (Base)': df_base.set_index('Mês')['Saldo Devedor CRI'],'Lastro (Severo)': df_sev.set_index('Mês')['Saldo Devedor Lastro'],'CRI (Severo)': df_sev.set_index('Mês')['Saldo Devedor CRI'],})
        st.area_chart(df_saldos, use_container_width=True)
        st.caption("Gráfico 2: Amortização dos Saldos Devedores do Lastro vs. CRI.")


elif st.session_state.pilar_selecionado == "Resultado Final":
    st.header("Resultado Final e Atribuição de Rating")
    if len(st.session_state.scores) < 4 or st.session_state.resultados_pilar5 is None:
        st.warning("Por favor, calcule todos os 4 pilares de score e execute a simulação do Pilar 5 antes de prosseguir.")
    else:
        pesos = {'pilar1': 0.20, 'pilar2': 0.30, 'pilar3': 0.30, 'pilar4': 0.20}
        score_final_ponderado = sum(st.session_state.scores.get(p, 5) * pesos[p] for p in pesos)
        rating_indicado = converter_score_para_rating(score_final_ponderado)
        
        st.subheader("Scorecard Mestre")
        data = {
            'Componente': ['Pilar 1: Originador/Devedor','Pilar 2: Lastro','Pilar 3: Estrutura e Reforços','Pilar 4: Jurídico/Governança'],
            'Peso': [f"{p*100:.0f}%" for p in pesos.values()],
            'Pontuação (1-5)': [f"{st.session_state.scores.get(p, 'N/A'):.2f}" for p in pesos.keys()],
            'Score Ponderado': [f"{(st.session_state.scores.get(p, 5) * pesos[p]):.2f}" for p in pesos.keys()]
        }
        df_scores = pd.DataFrame(data).set_index('Componente')
        st.table(df_scores)
        
        c1, c2 = st.columns(2)
        c1.metric(label="Score Final Ponderado", value=f"{score_final_ponderado:.2f}")
        c2.metric(label="Rating Indicado pelo Score", value=rating_indicado)
        st.markdown("---")
        
        st.subheader("Validação Quantitativa (Pilar 5)")
        perdas = st.session_state.resultados_pilar5
        perda_moderado = perdas['perda_moderado']
        perda_severo = perdas['perda_severo']
        if perda_moderado < 1:
            st.success("✅ A estrutura suportou o Cenário Moderado sem perdas de principal.")
        else:
            st.error(f"❌ A estrutura NÃO suportou o Cenário Moderado, com perda de R$ {perda_moderado:,.2f}.")
        if perda_severo < 1:
            st.info("ℹ️ A estrutura suportou o Cenário Severo sem perdas de principal.")
        else:
            st.warning(f"⚠️ A estrutura apresentou perda de R$ {perda_severo:,.2f} no Cenário Severo.")
        
        st.markdown("---")
        st.subheader("Deliberação Final do Comitê de Rating")
        col1, col2 = st.columns([1,2])
        with col1:
            st.number_input("Ajuste Qualitativo do Comitê (notches)", min_value=-3, max_value=3, value=0, step=1, key='ajuste_final', help="Permite ao analista ajustar o rating final com base em fatores não capturados pelo modelo. Use valores positivos para subir o rating e negativos para descer.")
            rating_final = ajustar_rating(rating_indicado, st.session_state.ajuste_final)
            st.metric(label="Rating Final Atribuído (Série Sênior)", value=rating_final)
            st.text_input("Rating Final Atribuído (Série Subordinada)", key='rating_subordinada')
        with col2:
            st.text_area("Justificativa para o ajuste e comentários finais:", height=250, placeholder="Ex: Ajuste de -1 notch devido aos conflitos de interesse identificados, apesar do bom resultado no teste de estresse...", key='justificativa_final')
