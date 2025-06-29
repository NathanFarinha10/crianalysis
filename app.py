import streamlit as st
import pandas as pd
import numpy as np

# --------------------------------------------------------------------------
# FUNÇÕES DE CÁLCULO DE SCORE (PILARES 1, 2, 3, 4)
# --------------------------------------------------------------------------
# (O código para as funções dos Pilares 1 a 4 permanece o mesmo e está omitido por brevidade)
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
# --------------------------------------------------------------------------
# FUNÇÕES DE CONVERSÃO E AJUSTE DE RATING (NOVO CÓDIGO)
# --------------------------------------------------------------------------
def converter_score_para_rating(score):
    """Converte a pontuação final (1-5) para uma notação de rating."""
    if score <= 1.25: return 'brAAA(sf)'
    elif score <= 1.75: return 'brAA(sf)'
    elif score <= 2.25: return 'brA(sf)'
    elif score <= 2.75: return 'brBBB(sf)'
    elif score <= 3.25: return 'brBB(sf)'
    elif score <= 4.00: return 'brB(sf)'
    else: return 'brCCC(sf)'

def ajustar_rating(rating_base, notches):
    """Ajusta um rating para cima ou para baixo em 'n' notches."""
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

# ... Páginas dos Pilares 1 a 5 omitidas por brevidade ...

# --------------------------------------------------------------------------
# PÁGINA FINAL - RESULTADO (NOVO CÓDIGO)
# --------------------------------------------------------------------------
elif pilar_selecionado == "Resultado Final":
    st.header("Resultado Final e Atribuição de Rating")
    
    # Verifica se todos os pilares foram calculados
    if len(st.session_state.scores) < 4 or not st.session_state.resultados_pilar5:
        st.warning("Por favor, calcule todos os 4 pilares de score e execute a simulação do Pilar 5 antes de prosseguir.")
    else:
        # Ponderações conforme Tabela 8
        pesos = {'pilar1': 0.20, 'pilar2': 0.30, 'pilar3': 0.30, 'pilar4': 0.20}
        
        score_final_ponderado = sum(st.session_state.scores[p] * pesos[p] for p in pesos)
        rating_indicado = converter_score_para_rating(score_final_ponderado)
        
        st.subheader("Scorecard Mestre")
        
        # Usar um dataframe para a tabela de scores
        data = {
            'Componente': [
                'Pilar 1: Análise do Originador/Devedor',
                'Pilar 2: Análise do Lastro',
                'Pilar 3: Análise da Estrutura e Reforços',
                'Pilar 4: Análise Jurídica e de Governança'
            ],
            'Peso': [f"{p*100:.0f}%" for p in pesos.values()],
            'Pontuação do Pilar (1-5)': [f"{st.session_state.scores.get(p, 0):.2f}" for p in pesos.keys()],
            'Score Ponderado': [f"{st.session_state.scores.get(p, 0) * pesos[p]:.2f}" for p in pesos.keys()]
        }
        df_scores = pd.DataFrame(data)
        st.table(df_scores.set_index('Componente'))
        
        st.metric(label="Score Final Ponderado", value=f"{score_final_ponderado:.2f}")
        st.metric(label="Rating Indicado pelo Score", value=rating_indicado)
        
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

            # Campo para o rating da série subordinada
            st.text_input("Rating Final Atribuído (Série Subordinada)", value="Não Avaliado")

        with col2:
            justificativa = st.text_area("Justificativa para o ajuste e comentários finais:", height=250, 
                                         placeholder="Ex: Ajuste de -1 notch devido aos conflitos de interesse identificados, apesar do bom resultado no teste de estresse...")
