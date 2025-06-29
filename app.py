import streamlit as st
import pandas as pd
import numpy as np

# --------------------------------------------------------------------------
# FUNÇÕES DE CÁLCULO DE SCORE (PILARES 1, 2, 3, 4)
# --------------------------------------------------------------------------
def calcular_score_governanca(inputs):
    scores = []
    map_ubo = {"Sim": 1, "Parcialmente": 3, "Não": 5}; scores.append(map_ubo[inputs['ubo']])
    map_conselho = {"Independente e atuante": 1, "Majoritariamente independente": 2, "Consultivo/Sem independência": 4, "Inexistente": 5}; scores.append(map_conselho[inputs['conselho']])
    scores.append(1 if inputs['comites'] else 4)
    map_auditoria = {"Big Four": 1, "Outra auditoria de mercado": 2, "Não auditado": 5}; scores.append(map_auditoria[inputs['auditoria']])
    scores.append(5 if inputs['ressalvas'] else 1)
    map_compliance = {"Maduras e implementadas": 1, "Em desenvolvimento": 3, "Inexistentes ou ad-hoc": 5}; scores.append(map_compliance[inputs['compliance']])
    map_litigios = {"Inexistente ou irrelevante": 1, "Baixo impacto financeiro": 2, "Médio impacto potencial": 4, "Alto impacto / Risco para a operação": 5}; scores.append(map_litigios[inputs['litigios']])
    scores.append(5 if inputs['renegociacao'] else 1)
    scores.append(5 if inputs['midia_negativa'] else 1)
    return sum(scores) / len(scores)

def calcular_score_operacional(inputs):
    scores = []
    map_track_record = {"Consistente e previsível": 1, "Desvios esporádicos": 3, "Atrasos e estouros recorrentes": 5}; scores.append(map_track_record[inputs['track_record']])
    map_reputacao = {"Positiva, baixo volume de queixas": 1, "Neutra, volume gerenciável": 3, "Negativa, alto volume de queixas sem resolução": 5}; scores.append(map_reputacao[inputs['reputacao']])
    scores.append(1 if inputs['politica_formalizada'] else 4)
    map_politica_credito = {"Score de crédito, análise de renda (DTI) e garantias": 1, "Apenas análise de renda e garantias": 3, "Análise simplificada ou ad-hoc": 5}; scores.append(map_politica_credito[inputs['analise_credito']])
    return sum(scores) / len(scores)

def calcular_score_financeiro(inputs):
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
    else:
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

def calcular_score_lastro_projeto(inputs):
    map_praca = {"Forte e favorável": 1, "Moderada": 3, "Fraca ou desfavorável": 5}; map_produto = {"Alta aderência, produto competitivo": 1, "Aderência razoável": 3, "Produto ou preço desalinhado com o mercado": 5}
    score_viabilidade = (map_praca[inputs['praca']] + map_produto[inputs['produto']]) / 2
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
    map_cronograma = {"Adiantado ou no prazo": 1, "Atraso leve (< 3 meses)": 2, "Atraso significativo (3-6 meses)": 4, "Atraso severo (> 6 meses)": 5}; map_orcamento = {"Dentro do orçamento": 1, "Estouro leve (<5%)": 2, "Estouro moderado (5-10%)": 4, "Estouro severo (>10%)": 5}; map_fundo_obras = {"Suficiente com margem (>110%)": 1, "Suficiente (100-110%)": 2, "Insuficiente (<100%)": 5}
    score_execucao = (map_cronograma[inputs['cronograma']] + map_orcamento[inputs['orcamento']] + map_fundo_obras[inputs['fundo_obras']]) / 3
    score_final = (score_viabilidade * 0.25) + (score_comercial * 0.40) + (score_execucao * 0.35)
    return score_final, score_viabilidade, score_comercial, score_execucao

def calcular_score_lastro_carteira(inputs):
    score_ltv = 0
    if inputs['ltv_medio'] < 60: score_ltv = 1
    elif inputs['ltv_medio'] <= 70: score_ltv = 2
    elif inputs['ltv_medio'] <= 80: score_ltv = 3
    elif inputs['ltv_medio'] <= 90: score_ltv = 4
    else: score_ltv = 5
    map_origem = {"Robusta e bem documentada (score, DTI, etc.)": 1, "Padrão de mercado": 3, "Frouxa, ad-hoc ou desconhecida": 5}
    score_qualidade = (score_ltv + map_origem[inputs['origem']]) / 2
    score_inadimplencia = 0
    if inputs['inadimplencia'] < 1.0: score_inadimplencia = 1
    elif inputs['inadimplencia'] <= 2.0: score_inadimplencia = 2
    elif inputs['inadimplencia'] <= 3.5: score_inadimplencia = 3
    elif inputs['inadimplencia'] <= 5.0: score_inadimplencia = 4
    else: score_inadimplencia = 5
    map_vintage = {"Estável ou melhorando": 1, "Com leve deterioração": 3, "Com deterioração clara e preocupante": 5}
    score_performance = (score_inadimplencia + map_vintage[inputs['vintage']]) / 2
    score_concentracao = 0
    if inputs['concentracao_top5'] < 10: score_concentracao = 1
    elif inputs['concentracao_top5'] <= 20: score_concentracao = 2
    elif inputs['concentracao_top5'] <= 30: score_concentracao = 3
    elif inputs['concentracao_top5'] <= 40: score_concentracao = 4
    else: score_concentracao = 5
    score_final = (score_qualidade * 0.40) + (score_performance * 0.40) + (score_concentracao * 0.20)
    return score_final, score_qualidade, score_performance, score_concentracao

def calcular_score_estrutura(inputs):
    scores_capital = []
    subordinacao = inputs['subordinacao']
    if subordinacao > 20: scores_capital.append(1)
    elif subordinacao >= 15: scores_capital.append(2)
    elif subordinacao >= 10: scores_capital.append(3)
    elif subordinacao >= 5: scores_capital.append(4)
    else: scores_capital.append(5)
    map_waterfall = {"Clara, protetiva e bem definida": 1, "Padrão de mercado com alguma ambiguidade": 3, "Ambígua, com brechas ou prejudicial à série": 5}
    scores_capital.append(map_waterfall[inputs['waterfall']])
    score_capital = sum(scores_capital) / len(scores_capital)
    scores_reforco = []
    score_fundo = 0
    if inputs['fundo_reserva_pmts'] > 3: score_fundo = 1
    elif inputs['fundo_reserva_pmts'] >= 2: score_fundo = 2
    elif inputs['fundo_reserva_pmts'] >= 1: score_fundo = 3
    else: score_fundo = 5
    if not inputs['fundo_reserva_regra']:
        score_fundo = min(5, score_fundo + 1)
    scores_reforco.append(score_fundo)
    oc = inputs['sobrecolateralizacao']
    if oc > 120: scores_reforco.append(1)
    elif oc >= 110: scores_reforco.append(2)
    elif oc >= 105: scores_reforco.append(3)
    elif oc > 100: scores_reforco.append(4)
    else: scores_reforco.append(5)
    spread = inputs['spread_excedente']
    if spread > 3: scores_reforco.append(1)
    elif spread >= 2: scores_reforco.append(2)
    elif spread >= 1: scores_reforco.append(3)
    elif spread > 0: scores_reforco.append(4)
    else: scores_reforco.append(5)
    score_reforco = sum(scores_reforco) / len(scores_reforco)
    scores_garantias = []
    map_tipo_garantia = {"Alienação Fiduciária de Imóveis": 1, "Cessão Fiduciária de Recebíveis": 2, "Fiança ou Aval": 4, "Sem garantia real (Fidejussória)": 5}
    scores_garantias.append(map_tipo_garantia[inputs['tipo_garantia']])
    ltv = inputs['ltv_garantia']
    if ltv < 50: scores_garantias.append(1)
    elif ltv <= 60: scores_garantias.append(2)
    elif ltv <= 70: scores_garantias.append(3)
    elif ltv <= 80: scores_garantias.append(4)
    else: scores_garantias.append(5)
    map_liquidez_garantia = {"Alta (ex: aptos residenciais em capital)": 1, "Média (ex: salas comerciais, loteamentos)": 3, "Baixa (ex: imóvel de uso específico, rural)": 5}
    scores_garantias.append(map_liquidez_garantia[inputs['liquidez_garantia']])
    score_garantias = sum(scores_garantias) / len(scores_garantias)
    score_final = (score_capital * 0.40) + (score_reforco * 0.30) + (score_garantias * 0.30)
    return score_final, score_capital, score_reforco, score_garantias

def calcular_score_juridico(inputs):
    scores_conflito = []
    map_independencia = {"Totalmente independentes": 1, "Partes relacionadas com mitigação de conflitos": 3, "Mesmo grupo econômico com alto potencial de conflito": 5}
    scores_conflito.append(map_independencia[inputs['independencia']])
    scores_conflito.append(1 if inputs['retencao_risco'] else 4)
    map_historico = {"Alinhado aos interesses dos investidores": 1, "Decisões mistas, alguns waivers aprovados": 3, "Histórico de decisões que beneficiam o devedor": 5}
    scores_conflito.append(map_historico[inputs['historico_decisoes']])
    score_conflito = sum(scores_conflito) / len(scores_conflito)
    scores_prestadores = []
    map_ag_fiduciario = {"Alta, com histórico de proatividade": 1, "Média, cumpre o papel protocolar": 3, "Baixa, passivo ou com histórico negativo": 5}
    scores_prestadores.append(map_ag_fiduciario[inputs['ag_fiduciario']])
    map_securitizadora = {"Alta, experiente e com bom histórico": 1, "Média, com histórico misto": 3, "Nova ou com histórico negativo": 5}
    scores_prestadores.append(map_securitizadora[inputs['securitizadora']])
    map_servicer = {"Alta, com processos e tecnologia robustos": 1, "Padrão de mercado": 2, "Fraca ou inadequada": 4, "Não aplicável / Não avaliado": 2}
    scores_prestadores.append(map_servicer[inputs['servicer']])
    score_prestadores = sum(scores_prestadores) / len(scores_prestadores)
    scores_contratual = []
    map_covenants = {"Fortes, objetivos e com gatilhos claros": 1, "Padrão, com alguma subjetividade": 3, "Fracos, subjetivos ou fáceis de contornar": 5}
    scores_contratual.append(map_covenants[inputs['covenants']])
    map_pareceres = {"Abrangentes e conclusivos (escritório 1ª linha)": 1, "Padrão, cumprem requisitos formais": 2, "Limitados ou com ressalvas": 4}
    scores_contratual.append(map_pareceres[inputs['pareceres']])
    map_relatorios = {"Alta, detalhados e frequentes": 1, "Média, cumprem o mínimo regulatório": 3, "Baixa, informações inconsistentes ou atrasadas": 5}
    scores_contratual.append(map_relatorios[inputs['relatorios']])
    score_contratual = sum(scores_contratual) / len(scores_contratual)
    score_final = (score_conflito * 0.50) + (score_prestadores * 0.30) + (score_contratual * 0.20)
    return score_final, score_conflito, score_prestadores, score_contratual

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
        pmt_lastro = np.pmt(taxa_juros_lastro_am, prazo - mes + 1, -saldo_lastro) if taxa_juros_lastro_am > 0 else saldo_lastro / (prazo - mes + 1)
        amortizacao_recebida = pmt_lastro - juros_recebido
        novos_defaults = saldo_lastro * taxa_inadimplencia_am
        defaults_pendentes[mes] = novos_defaults
        prepagamentos = (saldo_lastro - novos_defaults) * taxa_prepagamento_am
        recuperacao_do_mes = 0
        mes_recuperacao = mes - lag_recuperacao
        if mes_recuperacao in defaults_pendentes:
            valor_a_recuperar = defaults_pendentes.pop(mes_recuperacao)
            recuperacao_do_mes = valor_a_recuperar * (1 - severidade_perda)
        caixa_disponivel = juros_recebido + amortizacao_recebida + prepagamentos + recuperacao_do_mes
        caixa_disponivel -= inputs['despesas']
        juros_devido_cri = saldo_cri * taxa_remuneracao_cri_am
        juros_pago_cri = min(juros_devido_cri, caixa_disponivel)
        caixa_disponivel -= juros_pago_cri
        amortizacao_paga_cri = caixa_disponivel
        saldo_lastro -= (amortizacao_recebida + prepagamentos + novos_defaults)
        saldo_cri_anterior = saldo_cri
        saldo_cri -= amortizacao_paga_cri
        servico_divida_programado = juros_devido_cri + (saldo_cri_anterior - juros_devido_cri * (1/taxa_remuneracao_cri_am) * (1-(1+taxa_remuneracao_cri_am)**(-(prazo - mes + 1)))) if taxa_remuneracao_cri_am > 0 else juros_devido_cri + saldo_cri_anterior/(prazo - mes+1)
        dscr = (juros_pago_cri + amortizacao_paga_cri) / servico_divida_programado if servico_divida_programado > 0 else 1.0
        historico.append({'Mês': mes, 'Saldo Devedor Lastro': saldo_lastro, 'Saldo Devedor CRI': saldo_cri, 'DSCR': dscr})
    perda_principal = saldo_cri
    return perda_principal, pd.DataFrame(historico)

def converter_score_para_rating(score):
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
    except ValueError:
        return rating_base

# --------------------------------------------------------------------------
# INTERFACE STREAMLIT
# --------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="Análise e Rating de CRI")
st.title("Plataforma de Análise e Rating de CRI")
st.markdown("Desenvolvido em parceria com a IA 'Projeto de Análise e Rating de CRI v2'")

if 'scores' not in st.session_state: st.session_state.scores = {}
if 'resultados_pilar5' not in st.session_state: st.session_state.resultados_pilar5 = None

st.sidebar.header("Pilares da Análise")
pilar_selecionado = st.sidebar.radio("Selecione o pilar para análise:",
    ["Pilar 1: Originador/Devedor", "Pilar 2: Lastro", "Pilar 3: Estrutura", 
     "Pilar 4: Jurídico/Governança", "Pilar 5: Teste de Estresse", "Resultado Final"])

# --- CORPO PRINCIPAL DA APLICAÇÃO ---

if pilar_selecionado == "Pilar 1: Originador/Devedor":
    st.header("Pilar 1: Análise do Risco do Originador/Devedor")
    st.markdown("Peso no Scorecard Mestre: **20%**")
    inputs_pilar1 = {}
    with st.expander("Fator 1: Governança e Reputação (Peso: 30%)", expanded=True):
        inputs_pilar1['ubo'] = st.radio("Os beneficiários finais (UBOs) estão claramente identificados?", ["Sim", "Parcialmente", "Não"])
        inputs_pilar1['conselho'] = st.selectbox("Qual a estrutura do conselho de administração?", ["Independente e atuante", "Majoritariamente independente", "Consultivo/Sem independência", "Inexistente"])
        inputs_pilar1['comites'] = st.checkbox("Possui comitê de auditoria e/ou riscos formalizado?")
        inputs_pilar1['auditoria'] = st.selectbox("As demonstrações financeiras são auditadas por:", ["Big Four", "Outra auditoria de mercado", "Não auditado"])
        inputs_pilar1['ressalvas'] = st.checkbox("Houve ressalvas relevantes na última auditoria?")
        inputs_pilar1['compliance'] = st.selectbox("Maturidade das políticas de compliance e risco:", ["Maduras e implementadas", "Em desenvolvimento", "Inexistentes ou ad-hoc"])
        inputs_pilar1['litigios'] = st.selectbox("Nível de litígios relevantes (cíveis, fiscais, ambientais):", ["Inexistente ou irrelevante", "Baixo impacto financeiro", "Médio impacto potencial", "Alto impacto / Risco para a operação"])
        inputs_pilar1['renegociacao'] = st.checkbox("Há histórico de atraso ou renegociação de dívidas com credores?")
        inputs_pilar1['midia_negativa'] = st.checkbox("Identificado envolvimento em notícias negativas de grande impacto ou investigações?")
    with st.expander("Fator 2: Histórico Operacional (Peso: 30%)"):
        inputs_pilar1['track_record'] = st.selectbox("Histórico de entrega de projetos (prazo e orçamento):", ["Consistente e previsível", "Desvios esporádicos", "Atrasos e estouros recorrentes"])
        inputs_pilar1['reputacao'] = st.selectbox("Reputação e nível de satisfação de clientes (ex: Reclame Aqui):", ["Positiva, baixo volume de queixas", "Neutra, volume gerenciável", "Negativa, alto volume de queixas sem resolução"])
        inputs_pilar1['politica_formalizada'] = st.checkbox("A política de concessão de crédito é formalizada e documentada?")
        inputs_pilar1['analise_credito'] = st.selectbox("A análise de crédito para os recebíveis inclui:", ["Score de crédito, análise de renda (DTI) e garantias", "Apenas análise de renda e garantias", "Análise simplificada ou ad-hoc"])
    with st.expander("Fator 3: Saúde Financeira (Peso: 40%)"):
        inputs_pilar1['modalidade'] = st.radio("Selecione a modalidade de análise financeira:", ('Análise Corporativa (Holding/Incorporadora)', 'Análise de Projeto (SPE)'))
        if inputs_pilar1['modalidade'] == 'Análise Corporativa (Holding/Incorporadora)':
            st.info("Preencha os indicadores financeiros consolidados da empresa.")
            inputs_pilar1['dl_ebitda'] = st.number_input("Dívida Líquida / EBITDA", value=3.0, format="%.2f")
            inputs_pilar1['liq_corrente'] = st.number_input("Liquidez Corrente", value=1.2, format="%.2f")
            inputs_pilar1['fco_divida'] = st.number_input("FCO / Dívida Total (%)", value=15.0, format="%.1f")
        else:
            st.info("Preencha os indicadores financeiros específicos do projeto/SPE.")
            inputs_pilar1['divida_projeto'] = st.number_input("Dívida Total do Projeto (R$)", min_value=1.0, value=50_000_000.0, format="%.2f")
            inputs_pilar1['vgv_projeto'] = st.number_input("VGV Total do Projeto (R$)", min_value=1.0, value=100_000_000.0, format="%.2f")
            inputs_pilar1['custo_remanescente'] = st.number_input("Custo Remanescente da Obra (R$)", min_value=1.0, value=30_000_000.0, format="%.2f")
            inputs_pilar1['recursos_obra'] = st.number_input("Recursos Disponíveis para Obra (Caixa + CRI) (R$)", min_value=1.0, value=35_000_000.0, format="%.2f")
            inputs_pilar1['vgv_vendido'] = st.number_input("VGV já Vendido (R$)", min_value=1.0, value=60_000_000.0, format="%.2f")
            inputs_pilar1['sd_cri'] = st.number_input("Saldo Devedor do CRI (R$)", min_value=1.0, value=50_000_000.0, format="%.2f")
    st.markdown("---")
    if st.button("Calcular Score do Pilar 1"):
        score_gov = calcular_score_governanca(inputs_pilar1); score_op = calcular_score_operacional(inputs_pilar1); score_fin = calcular_score_financeiro(inputs_pilar1)
        score_final_pilar1 = (score_gov * 0.30) + (score_op * 0.30) + (score_fin * 0.40)
        st.subheader("Resultado da Análise - Pilar 1")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Score Governança", f"{score_gov:.2f}"); col2.metric("Score Operacional", f"{score_op:.2f}"); col3.metric("Score Financeiro", f"{score_fin:.2f}"); col4.metric("Score Final Ponderado (Pilar 1)", f"{score_final_pilar1:.2f}")
        st.session_state.scores['pilar1'] = score_final_pilar1
        st.success("Cálculo do Pilar 1 concluído e salvo!")

elif pilar_selecionado == "Pilar 2: Lastro":
    st.header("Pilar 2: Análise do Lastro"); st.markdown("Peso no Scorecard Mestre: **30%**")
    tipo_lastro = st.radio("Selecione a natureza do lastro do CRI:",('Desenvolvimento Imobiliário (Risco de Projeto)', 'Carteira de Recebíveis (Risco de Crédito)'),key="tipo_lastro_selector")
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
            col1.metric("Score Viabilidade", f"{s_viab:.2f}"); col2.metric("Score Comercial", f"{s_com:.2f}"); col3.metric("Score Execução", f"{s_exec:.2f}"); col4.metric("Score Final Ponderado (Pilar 2)", f"{score_final:.2f}", delta_color="off")
            st.success("Cálculo do Pilar 2 concluído e salvo!")
    else:
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
            col1.metric("Score Qualidade", f"{s_qual:.2f}"); col2.metric("Score Performance", f"{s_perf:.2f}"); col3.metric("Score Concentração", f"{s_conc:.2f}"); col4.metric("Score Final Ponderado (Pilar 2)", f"{score_final:.2f}", delta_color="off")
            st.success("Cálculo do Pilar 2 concluído e salvo!")

elif pilar_selecionado == "Pilar 3: Estrutura":
    st.header("Pilar 3: Análise da Estrutura e Mecanismos de Reforço de Crédito"); st.markdown("Peso no Scorecard Mestre: **30%**")
    inputs_pilar3 = {}
    with st.expander("Fator 1: Estrutura de Capital (Peso: 40%)", expanded=True):
        inputs_pilar3['subordinacao'] = st.number_input("Nível de subordinação (%) para a série em análise", min_value=0.0, max_value=100.0, value=10.0, format="%.2f")
        inputs_pilar3['waterfall'] = st.selectbox("Qualidade da Cascata de Pagamentos (Waterfall)", ["Clara, protetiva e bem definida", "Padrão de mercado com alguma ambiguidade", "Ambígua, com brechas ou prejudicial à série"])
    with st.expander("Fator 2: Mecanismos de Reforço e Liquidez (Peso: 30%)"):
        inputs_pilar3['fundo_reserva_pmts'] = st.number_input("Tamanho do Fundo de Reserva (em nº de pagamentos)", min_value=0.0, value=3.0, step=0.5, format="%.1f")
        inputs_pilar3['fundo_reserva_regra'] = st.checkbox("O Fundo de Reserva possui mecanismo de recomposição obrigatória?")
        inputs_pilar3['sobrecolateralizacao'] = st.number_input("Índice de Sobrecolateralização (%)", min_value=100.0, value=110.0, format="%.2f", help="Ex: 110 para 110%")
        inputs_pilar3['spread_excedente'] = st.number_input("Spread Excedente anualizado (%)", min_value=-5.0, value=1.5, format="%.2f")
    with st.expander("Fator 3: Qualidade das Garantias (Peso: 30%)"):
        inputs_pilar3['tipo_garantia'] = st.selectbox("Tipo de garantia predominante na estrutura", ["Alienação Fiduciária de Imóveis", "Cessão Fiduciária de Recebíveis", "Fiança ou Aval", "Sem garantia real (Fidejussória)"])
        inputs_pilar3['ltv_garantia'] = st.number_input("LTV Médio Ponderado das garantias (%)", min_value=0.0, max_value=200.0, value=60.0, format="%.2f")
        inputs_pilar3['liquidez_garantia'] = st.selectbox("Liquidez estimada da garantia", ["Alta (ex: aptos residenciais em capital)", "Média (ex: salas comerciais, loteamentos)", "Baixa (ex: imóvel de uso específico, rural)"])
    st.markdown("---")
    if st.button("Calcular Score do Pilar 3"):
        score_final, s_cap, s_ref, s_gar = calcular_score_estrutura(inputs_pilar3)
        st.session_state.scores['pilar3'] = score_final
        st.subheader("Resultado da Análise - Pilar 3")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Score Estrutura Capital", f"{s_cap:.2f}"); col2.metric("Score Mecanismos", f"{s_ref:.2f}"); col3.metric("Score Garantias", f"{s_gar:.2f}"); col4.metric("Score Final Ponderado (Pilar 3)", f"{score_final:.2f}")
        st.success("Cálculo do Pilar 3 concluído e salvo!")

elif pilar_selecionado == "Pilar 4: Jurídico/Governança":
    st.header("Pilar 4: Análise Jurídica e de Governança da Operação"); st.markdown("Peso no Scorecard Mestre: **20%**")
    inputs_pilar4 = {}
    with st.expander("Fator 1: Conflitos de Interesse (Peso: 50%)", expanded=True):
        inputs_pilar4['independencia'] = st.selectbox("Nível de independência entre Originador, Securitizadora e Gestor", ["Totalmente independentes", "Partes relacionadas com mitigação de conflitos", "Mesmo grupo econômico com alto potencial de conflito"])
        inputs_pilar4['retencao_risco'] = st.checkbox("O originador/cedente retém a cota subordinada ou outra forma de risco relevante?")
        inputs_pilar4['historico_decisoes'] = st.selectbox("Histórico de decisões em assembleias do estruturador/originador", ["Alinhado aos interesses dos investidores", "Decisões mistas, alguns waivers aprovados", "Histórico de decisões que beneficiam o devedor"])
    with st.expander("Fator 2: Qualidade dos Prestadores de Serviço (Peso: 30%)"):
        inputs_pilar4['ag_fiduciario'] = st.selectbox("Reputação e experiência do Agente Fiduciário", ["Alta, com histórico de proatividade", "Média, cumpre o papel protocolar", "Baixa, passivo ou com histórico negativo"])
        inputs_pilar4['securitizadora'] = st.selectbox("Reputação e experiência da Securitizadora", ["Alta, experiente e com bom histórico", "Média, com histórico misto", "Nova ou com histórico negativo"])
        inputs_pilar4['servicer'] = st.selectbox("Qualidade do Agente de Cobrança (Servicer)", ["Alta, com processos e tecnologia robustos", "Padrão de mercado", "Fraca ou inadequada", "Não aplicável / Não avaliado"])
    with st.expander("Fator 3: Robustez Contratual e Transparência (Peso: 20%)"):
        inputs_pilar4['covenants'] = st.selectbox("Qualidade e rigidez dos Covenants da operação", ["Fortes, objetivos e com gatilhos claros", "Padrão, com alguma subjetividade", "Fracos, subjetivos ou fáceis de contornar"])
        inputs_pilar4['pareceres'] = st.selectbox("Qualidade dos pareceres jurídicos (true sale, etc.)", ["Abrangentes e conclusivos (escritório 1ª linha)", "Padrão, cumprem requisitos formais", "Limitados ou com ressalvas"])
        inputs_pilar4['relatorios'] = st.selectbox("Qualidade e frequência dos relatórios de acompanhamento", ["Alta, detalhados e frequentes", "Média, cumprem o mínimo regulatório", "Baixa, informações inconsistentes ou atrasadas"])
    st.markdown("---")
    if st.button("Calcular Score do Pilar 4"):
        score_final, s_conf, s_prest, s_cont = calcular_score_juridico(inputs_pilar4)
        st.session_state.scores['pilar4'] = score_final
        st.subheader("Resultado da Análise - Pilar 4")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Score Conflitos", f"{s_conf:.2f}"); col2.metric("Score Prestadores", f"{s_prest:.2f}"); col3.metric("Score Contratual", f"{s_cont:.2f}"); col4.metric("Score Final Ponderado (Pilar 4)", f"{score_final:.2f}")
        st.success("Cálculo do Pilar 4 concluído e salvo!")

elif pilar_selecionado == "Pilar 5: Teste de Estresse":
    st.header("Pilar 5: Modelagem de Fluxo de Caixa e Testes de Estresse"); st.markdown("Esta etapa representa a validação quantitativa da resiliência da operação.")
    inputs_pilar5 = {}
    with st.expander("Inputs do Modelo (Dados da Operação)", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            inputs_pilar5['saldo_lastro'] = st.number_input("Saldo Devedor do Lastro (R$)", value=100_000_000.0, format="%.2f")
            inputs_pilar5['saldo_cri'] = st.number_input("Saldo Devedor do CRI (Série Sênior) (R$)", value=80_000_000.0, format="%.2f")
        with c2:
            inputs_pilar5['taxa_lastro'] = st.number_input("Taxa Média do Lastro (% a.a.)", value=12.0)
            inputs_pilar5['taxa_cri'] = st.number_input("Taxa da Série Sênior (% a.a.)", value=10.0)
        with c3:
            inputs_pilar5['prazo'] = st.number_input("Prazo Remanescente (meses)", value=60)
            inputs_pilar5['despesas'] = st.number_input("Despesas Fixas Mensais (R$)", value=10000.0)
    st.markdown("---"); st.subheader("Definição das Premissas dos Cenários")
    cenarios = {}
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### Cenário Base")
        cenarios['base'] = {'inadimplencia': st.slider("Inadimplência (% a.a.)", 0.0, 10.0, 2.0, key="inad_base"),'prepagamento': st.slider("Pré-pagamento (% a.a.)", 0.0, 20.0, 10.0, key="prep_base"),'severidade': st.slider("Severidade da Perda (%)", 0, 100, 30, key="sev_base"),'lag': st.slider("Lag de Recuperação (meses)", 0, 24, 12, key="lag_base")}
    with c2:
        st.markdown("#### Cenário Moderado")
        cenarios['moderado'] = {'inadimplencia': st.slider("Inadimplência (% a.a.)", 0.0, 20.0, 5.0, key="inad_mod"),'prepagamento': st.slider("Pré-pagamento (% a.a.)", 0.0, 20.0, 5.0, key="prep_mod"),'severidade': st.slider("Severidade da Perda (%)", 0, 100, 50, key="sev_mod"),'lag': st.slider("Lag de Recuperação (meses)", 0, 24, 18, key="lag_mod")}
    with c3:
        st.markdown("#### Cenário Severo")
        cenarios['severo'] = {'inadimplencia': st.slider("Inadimplência (% a.a.)", 0.0, 40.0, 10.0, key="inad_sev"),'prepagamento': st.slider("Pré-pagamento (% a.a.)", 0.0, 20.0, 2.0, key="prep_sev"),'severidade': st.slider("Severidade da Perda (%)", 0, 100, 70, key="sev_sev"),'lag': st.slider("Lag de Recuperação (meses)", 0, 24, 24, key="lag_sev")}
    st.markdown("---")
    if st.button("Executar Simulação de Fluxo de Caixa"):
        with st.spinner("Simulando cenários... Por favor, aguarde."):
            perda_base, df_base = run_cashflow_simulation(inputs_pilar5, cenarios['base'])
            perda_mod, df_mod = run_cashflow_simulation(inputs_pilar5, cenarios['moderado'])
            perda_sev, df_sev = run_cashflow_simulation(inputs_pilar5, cenarios['severo'])
            st.session_state.resultados_pilar5 = {'perda_base': perda_base, 'perda_moderado': perda_mod, 'perda_severo': perda_sev}
            st.subheader("Resultados da Simulação")
            rc1, rc2, rc3 = st.columns(3)
            rc1.metric("Perda de Principal (Base)", f"R$ {perda_base:,.2f}")
            rc2.metric("Perda de Principal (Moderado)", f"R$ {perda_mod:,.2f}")
            rc3.metric("Perda de Principal (Severo)", f"R$ {perda_sev:,.2f}")
            st.markdown("---"); st.subheader("Gráficos de Performance")
            df_dscr = pd.DataFrame({'Base': df_base.set_index('Mês')['DSCR'],'Moderado': df_mod.set_index('Mês')['DSCR'],'Severo': df_sev.set_index('Mês')['DSCR']})
            st.line_chart(df_dscr); st.caption("Gráfico 1: DSCR (Cobertura do Serviço da Dívida) ao longo do tempo.")
            df_saldos = pd.DataFrame({'Lastro (Base)': df_base.set_index('Mês')['Saldo Devedor Lastro'],'CRI (Base)': df_base.set_index('Mês')['Saldo Devedor CRI'],'Lastro (Severo)': df_sev.set_index('Mês')['Saldo Devedor Lastro'],'CRI (Severo)': df_sev.set_index('Mês')['Saldo Devedor CRI'],})
            st.area_chart(df_saldos); st.caption("Gráfico 2: Amortização dos Saldos Devedores do Lastro vs. CRI.")

elif pilar_selecionado == "Resultado Final":
    st.header("Resultado Final e Atribuição de Rating")
    if len(st.session_state.get('scores', {})) < 4 or not st.session_state.get('resultados_pilar5'):
        st.warning("Por favor, calcule todos os 4 pilares de score e execute a simulação do Pilar 5 antes de prosseguir.")
    else:
        pesos = {'pilar1': 0.20, 'pilar2': 0.30, 'pilar3': 0.30, 'pilar4': 0.20}
        score_final_ponderado = sum(st.session_state.scores[p] * pesos[p] for p in pesos)
        rating_indicado = converter_score_para_rating(score_final_ponderado)
        st.subheader("Scorecard Mestre")
        data = {'Componente': ['Pilar 1: Análise do Originador/Devedor','Pilar 2: Análise do Lastro','Pilar 3: Análise da Estrutura e Reforços','Pilar 4: Análise Jurídica e de Governança'],'Peso': [f"{p*100:.0f}%" for p in pesos.values()],'Pontuação do Pilar (1-5)': [f"{st.session_state.scores.get(p, 0):.2f}" for p in pesos.keys()],'Score Ponderado': [f"{st.session_state.scores.get(p, 0) * pesos[p]:.2f}" for p in pesos.keys()]}
        df_scores = pd.DataFrame(data)
        st.table(df_scores.set_index('Componente'))
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
            ajuste = st.number_input("Ajuste Qualitativo do Comitê (notches)", min_value=-3, max_value=3, value=0, step=1)
            rating_final = ajustar_rating(rating_indicado, ajuste)
            st.metric(label="Rating Final Atribuído (Série Sênior)", value=rating_final)
            st.text_input("Rating Final Atribuído (Série Subordinada)", value="Não Avaliado")
        with col2:
            justificativa = st.text_area("Justificativa para o ajuste e comentários finais:", height=250, placeholder="Ex: Ajuste de -1 notch devido aos conflitos de interesse identificados, apesar do bom resultado no teste de estresse...")
