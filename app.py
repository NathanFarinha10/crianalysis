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
            'saldo_lastro': 100000000.0, 'saldo_cri': 80000000.0, 'taxa_lastro': 12.0, 'taxa_cri': 10.0,
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
    """Cria um gráfico de medidor (gauge) para um score de 1 a 5."""
    if score is None:
        score = 0
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
    scores.append(map_ubo[st.session_state.ubo])
    scores.append(map_conselho[st.session_state.conselho])
    scores.append(1 if st.session_state.comites else 4)
    scores.append(map_auditoria[st.session_state.auditoria])
    scores.append(5 if st.session_state.ressalvas else 1)
    scores.append(map_compliance[st.session_state.compliance])
    scores.append(map_litigios[st.session_state.litigios])
    scores.append(5 if st.session_state.renegociacao else 1)
    scores.append(5 if st.session_state.midia_negativa else 1)
    scores.append(map_emissor[st.session_state.hist_emissor])
    scores.append(map_socios[st.session_state.exp_socios])
    return sum(scores) / len(scores) if scores else 5

def calcular_score_operacional():
    scores = []
    map_track_record = {"Consistente e previsível": 1, "Desvios esporádicos": 3, "Atrasos e estouros recorrentes": 5}
    map_reputacao = {"Positiva, baixo volume de queixas": 1, "Neutra, volume gerenciável": 3, "Negativa, alto volume de queixas sem resolução": 5}
    map_politica_credito = {"Score de crédito, análise de renda (DTI) e garantias": 1, "Apenas análise de renda e garantias": 3, "Análise simplificada ou ad-hoc": 5}
    map_exp_similar = {"Extensa e comprovada no segmento específico": 1, "Experiência relevante em segmentos correlatos": 2, "Experiência limitada ou em outros segmentos": 4, "Iniciante/Nenhuma": 5}
    scores.append(map_track_record[st.session_state.track_record])
    scores.append(map_reputacao[st.session_state.reputacao])
    scores.append(1 if st.session_state.politica_formalizada else 4)
    scores.append(map_politica_credito[st.session_state.analise_credito])
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
    return score_final, score_viabilidade, score_comercial, score_execucao

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
    return score_final, score_qualidade, score_performance, score_concentracao

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
    return score_final, score_capital, score_reforco, score_garantias

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
    return score_final, score_conflito, score_prestadores, score_contratual

@st.cache_data
def run_cashflow_simulation(inputs, cenario_premissas):
    taxa_inadimplencia_aa = cenario_premissas['inadimplencia'] / 100
    taxa_prepagamento_aa = cenario_premissas['prepagamento'] / 100
    severidade_perda = cenario_premissas['severidade'] / 100
    lag_recuperacao = cenario_premissas['lag']
    taxa_juros_lastro_am = (1 + inputs['taxa_lastro']/100)**(1/12) - 1
    taxa_remuneracao_cri_am = (1 + inputs['taxa_cri']/100)**(1/12) - 1
    taxa_inadimplencia_am = (1 + taxa_inadimplencia_aa)**(1/12) - 1
    taxa_prepagamento_am = (1 + taxa_prepagamento_aa)**(1/12) - 1
    saldo_lastro = inputs['saldo_lastro']
    saldo_cri = inputs['saldo_cri']
    prazo = inputs['prazo']
    historico = []
    defaults_pendentes = {}
    for mes in range(1, prazo + 1):
        if saldo_lastro < 1 or saldo_cri < 1: break
        juros_recebido = saldo_lastro * taxa_juros_lastro_am
        amortizacao_programada_lastro = npf.ppmt(taxa_juros_lastro_am, mes, prazo, -saldo_lastro) if taxa_juros_lastro_am > 0 else saldo_lastro / prazo
        novos_defaults = saldo_lastro * taxa_inadimplencia_am
        defaults_pendentes[mes] = novos_defaults
        prepagamentos = (saldo_lastro - novos_defaults) * taxa_prepagamento_am
        recuperacao_do_mes = 0
        mes_recuperacao = mes - lag_recuperacao
        if mes_recuperacao in defaults_pendentes:
            valor_a_recuperar = defaults_pendentes.pop(mes_recuperacao)
            recuperacao_do_mes = valor_a_recuperar * (1 - severidade_perda)
        caixa_disponivel = juros_recebido + amortizacao_programada_lastro + prepagamentos + recuperacao_do_mes
        caixa_disponivel -= inputs['despesas']
        juros_devido_cri = saldo_cri * taxa_remuneracao_cri_am
        juros_pago_cri = min(juros_devido_cri, caixa_disponivel)
        caixa_disponivel -= juros_pago_cri
        amortizacao_paga_cri = caixa_disponivel
        saldo_lastro -= (amortizacao_programada_lastro + prepagamentos + novos_defaults)
        saldo_cri_anterior = saldo_cri
        saldo_cri -= amortizacao_paga_cri
        servico_divida_programado = juros_devido_cri + npf.ppmt(taxa_remuneracao_cri_am, 1, prazo - mes + 1, -saldo_cri_anterior) if taxa_remuneracao_cri_am > 0 else juros_devido_cri + saldo_cri_anterior / (prazo - mes + 1)
        dscr = (juros_pago_cri + amortizacao_paga_cri) / servico_divida_programado if servico_divida_programado > 0 else 1.0
        historico.append({'Mês': mes, 'Saldo Devedor Lastro': saldo_lastro, 'Saldo Devedor CRI': saldo_cri, 'DSCR': dscr})
    perda_principal = max(0, saldo_cri)
    return perda_principal, pd.DataFrame(historico)

# ... (código da interface principal) ...
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
    # ... (código completo do Pilar 1 com todos os widgets usando 'key' e 'help') ...

elif st.session_state.pilar_selecionado == "Pilar 2: Lastro":
    # ... (código completo do Pilar 2 com todos os widgets usando 'key' e 'help', e a exibição do gauge e expander) ...

elif st.session_state.pilar_selecionado == "Pilar 3: Estrutura":
    # ... (código completo do Pilar 3 com todos os widgets usando 'key' e 'help', e a exibição do gauge e expander) ...

elif st.session_state.pilar_selecionado == "Pilar 4: Jurídico/Governança":
    # ... (código completo do Pilar 4 com todos os widgets usando 'key' e 'help', e a exibição do gauge e expander) ...

elif st.session_state.pilar_selecionado == "Pilar 5: Teste de Estresse":
    # ... (código completo do Pilar 5 com todos os widgets usando 'key' e 'help') ...

elif st.session_state.pilar_selecionado == "Resultado Final":
    # ... (código completo da página de resultado final) ...
