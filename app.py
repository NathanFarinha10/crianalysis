import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import datetime
import google.generativeai as genai

# ==============================================================================
# INICIALIZAÇÃO E FUNÇÕES AUXILIARES
# ==============================================================================

def inicializar_session_state():
    """Garante que todos os valores de input e scores sejam inicializados no st.session_state apenas uma vez."""
    if 'state_initialized' not in st.session_state:
        st.session_state.state_initialized = True
        st.session_state.scores = {}
        st.session_state.resultados_pilar5 = None
        st.session_state.map_data = None
        st.session_state.fluxo_modelado_df = pd.DataFrame()

        defaults = {
            # --- Chaves para a aba de Cadastro ---
            'op_nome': 'CRI Exemplo Towers', 'op_codigo': 'EXMP11', 'op_securitizadora': 'Exemplo Securitizadora S.A.',
            'op_originador': 'Construtora Exemplo Ltda', 'op_agente_fiduciario': 'Exemplo Trust DTVM',
            'op_volume': 150000000.0, 'op_taxa': 10.5, 'op_indexador': 'IPCA +', 'op_prazo': 120,
            'op_data_emissao': datetime.date(2024, 1, 15), 'op_data_vencimento': datetime.date(2034, 1, 15),
            'op_data_lancamento_projeto': datetime.date(2023, 6, 1),
            
            # Pilar 1
            'hist_emissor': 'Primeira emissão', 'exp_socios': 'Experiência moderada', 'ubo': 'Sim',
            'conselho': 'Consultivo/Sem independência', 'comites': False, 'auditoria': 'Auditoria de Grande Porte (fora do Big Four)',
            'ressalvas': False, 'compliance': 'Em desenvolvimento', 'litigios': 'Baixo impacto financeiro',
            'renegociacao': False, 'midia_negativa': False, 'exp_similar': 'Experiência relevante em segmentos correlatos',
            'track_record': 'Desvios esporádicos', 'reputacao': 'Neutra, volume gerenciável', 'politica_formalizada': True,
            'analise_credito': 'Apenas análise de renda e garantias', 'modalidade_financeira': 'Análise Corporativa (Holding/Incorporadora)',
            'dl_ebitda': 3.0, 'liq_corrente': 1.2, 'fco_divida': 15.0, 'divida_projeto': 50000000.0, 'vgv_projeto': 100000000.0,
            'custo_remanescente': 30000000.0, 'recursos_obra': 35000000.0, 'vgv_vendido': 60000000.0, 'sd_cri': 50000000.0,
            'risco_juridico': 'Baixo / Gerenciado', 'risco_ambiental': 'Baixo / Gerenciado', 'risco_social': 'Baixo / Gerenciado',
            'hist_socios': 'Primeiro empreendimento ou histórico desconhecido',

            # Pilar 2
            'tipo_lastro': 'Desenvolvimento Imobiliário (Risco de Projeto)', 'segmento_projeto': 'Residencial Vertical',
            'qualidade_municipio': 'Capital / Metrópole', 'microlocalizacao': 'Boa', 'cidade_mapa': 'São Paulo, SP',
            'unidades_vendidas_mes': 10, 'unidades_ofertadas_inicio_mes': 150, 'avanco_fisico_obra': 50,
            'cronograma': 'Adiantado ou no prazo', 'orcamento': 'Dentro do orçamento', 'fundo_obras': 'Suficiente (100-110%)',
            'saldo_devedor_carteira': 80_000_000.0, 'valor_garantias_carteira': 120_000_000.0, 'ltv_medio_carteira': 66.7,
            'origem': 'Padrão de mercado', 'inadimplencia': 1.2, 'vintage': 'Com leve deterioração', 'concentracao_top5': 6.0,
            'ivv_calculado': 6.67, 'vgv_vendido_perc': 60,

            # Pilar 3
            'estrutura_tipo': 'Múltiplas Séries (com subordinação)', 'subordinacao': 10.0, 
            'waterfall': 'Padrão de mercado com alguma ambiguidade', 'fundo_reserva_pmts': 3.0, 'fundo_reserva_regra': True,
            'sobrecolateralizacao': 110.0, 'spread_excedente': 1.5, 'tipo_garantia': ['Alienação Fiduciária de Imóveis'], 
            'ltv_garantia': 60.0, 'liquidez_garantia': 'Média (ex: salas comerciais, loteamentos)',
            
            # Pilar 4
            'independencia': 'Partes relacionadas com mitigação de conflitos', 'retencao_risco': True,
            'historico_decisoes': 'Decisões mistas, alguns waivers aprovados', 'ag_fiduciario': 'Média, cumpre o papel protocolar',
            'securitizadora': 'Média, com histórico misto', 'servicer': 'Padrão de mercado', 'covenants': 'Padrão, com alguma subjetividade',
            'pareceres': 'Padrão, cumprem requisitos formais', 'relatorios': 'Média, cumprem o mínimo regulatório',
            
            # Pilar 5
            'tipo_modelagem_p5': 'Projeto (Desenvolvimento Imobiliário)',
            'proj_tipologias': [{'nome': 'Apto Padrão', 'area': 75.0, 'estoque': 50, 'vendidas': 10, 'permutadas': 2, 'preco_m2': 9000.0}],
            'proj_vgv_total': 150000000.0, 'proj_custo_obra': 90000000.0, 'proj_area_total': 10000.0, 'proj_num_unidades': 120,
            'proj_prazo_obra': 36, 'proj_curva_desembolso': 'Curva \'S\' Simplificada', 'proj_ivv_projecao': 5,
            'cart_sd_total': 100000000.0, 'cart_taxa_media': 12.0, 'cart_amortizacao': 'Price', 'cart_prazo_medio': 180,
            'cart_perc_balao': 0, 'cart_ltv_medio': 65.0,
            'saldo_lastro_p5': 100000000.0, 'saldo_cri_p5': 80000000.0, 'taxa_lastro_p5': 12.0, 'taxa_cri_p5': 10.0,
            'prazo_p5': 60, 'despesas_p5': 10000.0, 'inad_base': 2.0, 'prep_base': 10.0, 'sev_base': 30, 'lag_base': 12,
            'inad_mod': 5.0, 'prep_mod': 5.0, 'sev_mod': 50, 'lag_mod': 18, 'inad_sev': 10.0, 'prep_sev': 2.0, 'sev_sev': 70, 'lag_sev': 24,
            
            # Resultado Final
            'ajuste_final': 0, 'justificativa_final': ''
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

@st.cache_data
def get_coords(city):
    if not city: return None
    try:
        geolocator = Nominatim(user_agent="cri_analyzer_app_final")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
        location = geocode(city)
        if location: return pd.DataFrame({'lat': [location.latitude], 'lon': [location.longitude]})
    except Exception: return None

def create_gauge_chart(score, title):
    if score is None: score = 1.0
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=round(score, 2),
        title={'text': title, 'font': {'size': 20}},
        gauge={
            'axis': {'range': [1, 5], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "black", 'thickness': 0.3}, 'bgcolor': "white", 'borderwidth': 1, 'bordercolor': "gray",
            'steps': [
                {'range': [1, 2.5], 'color': '#dc3545'},
                {'range': [2.5, 3.75], 'color': '#ffc107'},
                {'range': [3.75, 5], 'color': '#28a745'}],
        }))
    fig.update_layout(height=250, margin={'t':40, 'b':40, 'l':30, 'r':30})
    return fig

def converter_score_para_rating(score):
    if score is None: return "N/A"
    if score >= 4.75: return 'brAAA(sf)'
    elif score >= 4.25: return 'brAA(sf)'
    elif score >= 3.75: return 'brA(sf)'
    elif score >= 3.25: return 'brBBB(sf)'
    elif score >= 2.75: return 'brBB(sf)'
    elif score >= 2.00: return 'brB(sf)'
    else: return 'brCCC(sf)'

def ajustar_rating(rating_base, notches):
    escala = ['brCCC(sf)', 'brB(sf)', 'brBB(sf)', 'brBBB(sf)', 'brA(sf)', 'brAA(sf)', 'brAAA(sf)']
    try:
        idx_base = escala.index(rating_base)
        idx_final = max(0, min(len(escala) - 1, idx_base + notches))
        return escala[idx_final]
    except (ValueError, TypeError): return rating_base

# ==============================================================================
# FUNÇÕES DE CÁLCULO DE SCORE (LÓGICA INVERTIDA: 5 = MELHOR, 1 = PIOR)
# ==============================================================================
def calcular_score_governanca():
    scores = []
    map_ubo = {"Sim": 5, "Parcialmente": 3, "Não": 1}
    map_conselho = {"Independente e atuante": 5, "Majoritariamente independente": 4, "Consultivo/Sem independência": 2, "Inexistente": 1}
    map_auditoria = {"Big Four": 5, "Auditoria de Grande Porte (fora do Big Four)": 4, "Auditoria de Pequeno Porte/Contador": 2, "Não auditado": 1}
    map_compliance = {"Maduras e implementadas": 5, "Em desenvolvimento": 3, "Inexistentes ou ad-hoc": 1}
    map_litigios = {"Inexistente ou irrelevante": 5, "Baixo impacto financeiro": 4, "Médio impacto potencial": 2, "Alto impacto / Risco para a operação": 1}
    map_emissor = {"Emissor recorrente com bom histórico": 5, "Poucas emissões ou histórico misto": 3, "Primeira emissão": 2, "Histórico negativo": 1}
    map_socios = {"Altamente experiente e com boa reputação": 5, "Experiência moderada": 3, "Inexperiente ou com reputação questionável": 1}
    map_risco = {"Baixo / Gerenciado": 5, "Moderado / Pontos de Atenção": 3, "Alto / Risco Relevante": 1}
    scores.extend([map_ubo[st.session_state.ubo], map_conselho[st.session_state.conselho], 
                   (5 if st.session_state.comites else 2), map_auditoria[st.session_state.auditoria],
                   (1 if st.session_state.ressalvas else 5), map_compliance[st.session_state.compliance],
                   map_litigios[st.session_state.litigios], (1 if st.session_state.renegociacao else 5),
                   (1 if st.session_state.midia_negativa else 5), map_emissor[st.session_state.hist_emissor],
                   map_socios[st.session_state.exp_socios], map_risco[st.session_state.risco_juridico],
                   map_risco[st.session_state.risco_ambiental], map_risco[st.session_state.risco_social]])
    return sum(scores) / len(scores) if scores else 1

def calcular_score_operacional():
    scores = []
    map_track_record = {"Consistente e previsível": 5, "Desvios esporádicos": 3, "Atrasos e estouros recorrentes": 1}
    map_reputacao = {"Positiva, baixo volume de queixas": 5, "Neutra, volume gerenciável": 3, "Negativa, alto volume de queixas sem resolução": 1}
    map_politica_credito = {"Score de crédito, análise de renda (DTI) e garantias": 5, "Apenas análise de renda e garantias": 3, "Análise simplificada ou ad-hoc": 1}
    map_exp_similar = {"Extensa e comprovada no segmento específico": 5, "Experiência relevante em segmentos correlatos": 4, "Experiência limitada ou em outros segmentos": 2, "Iniciante/Nenhuma": 1}
    map_hist_socios = {"Sócio(s) com múltiplos empreendimentos de sucesso comprovado": 5, "Sócio(s) com algum histórico de sucesso, sem falhas relevantes": 4, "Primeiro empreendimento ou histórico desconhecido": 2, "Sócio(s) com histórico de falências ou recuperações judiciais": 1}
    scores.extend([map_track_record[st.session_state.track_record], map_reputacao[st.session_state.reputacao],
                   (5 if st.session_state.politica_formalizada else 2), map_politica_credito[st.session_state.analise_credito],
                   map_exp_similar[st.session_state.exp_similar], map_hist_socios[st.session_state.hist_socios]])
    return sum(scores) / len(scores) if scores else 1

def calcular_score_financeiro():
    scores = []
    if st.session_state.modalidade_financeira == 'Análise Corporativa (Holding/Incorporadora)':
        dl_ebitda = st.session_state.dl_ebitda
        if dl_ebitda < 2.0: scores.append(5)
        elif dl_ebitda <= 4.0: scores.append(3)
        else: scores.append(1)
        liq_corrente = st.session_state.liq_corrente
        if liq_corrente > 1.5: scores.append(5)
        elif liq_corrente >= 1.0: scores.append(3)
        else: scores.append(1)
        fco_divida = st.session_state.fco_divida
        if fco_divida > 30: scores.append(5)
        elif fco_divida >= 15: scores.append(3)
        else: scores.append(1)
    else:
        vgv_projeto = st.session_state.vgv_projeto
        ltv = (st.session_state.divida_projeto / vgv_projeto) * 100 if vgv_projeto > 0 else 999
        if ltv < 40: scores.append(5)
        elif ltv <= 60: scores.append(3)
        else: scores.append(1)
        custo_remanescente = st.session_state.custo_remanescente
        cobertura_obra = (st.session_state.recursos_obra / custo_remanescente) * 100 if custo_remanescente > 0 else 0
        if cobertura_obra > 120: scores.append(5)
        elif cobertura_obra >= 100: scores.append(3)
        else: scores.append(1)
        sd_cri = st.session_state.sd_cri
        cobertura_vendas = (st.session_state.vgv_vendido / sd_cri) * 100 if sd_cri > 0 else 0
        if cobertura_vendas > 150: scores.append(5)
        elif cobertura_vendas >= 100: scores.append(3)
        else: scores.append(1)
    return sum(scores) / len(scores) if scores else 1

def calcular_score_lastro_projeto():
    map_praca = {"Capital / Metrópole": 5, "Cidade Grande (>500k hab)": 4, "Cidade Média (100-500k hab)": 3, "Cidade Pequena (<100k hab)": 2}
    map_micro = {"Nobre / Premium": 5, "Boa": 4, "Regular": 2, "Periférica / Risco": 1}
    map_segmento = {"Residencial Vertical": 5, "Residencial Horizontal (Condomínio)": 4, "Comercial (Salas/Lajes)": 3, "Loteamento": 2, "Multipropriedade": 1}
    score_localizacao = (map_praca[st.session_state.qualidade_municipio] + map_micro[st.session_state.microlocalizacao]) / 2
    score_viabilidade = (score_localizacao * 0.7) + (map_segmento[st.session_state.segmento_projeto] * 0.3)
    unid_ofertadas = st.session_state.unidades_ofertadas_inicio_mes
    ivv_calculado = (st.session_state.unidades_vendidas_mes / unid_ofertadas) * 100 if unid_ofertadas > 0 else 0
    st.session_state.ivv_calculado = ivv_calculado
    if ivv_calculado > 7: score_ivv = 5
    elif ivv_calculado >= 4: score_ivv = 3
    else: score_ivv = 1
    vgv_vendido_perc = st.session_state.vgv_vendido_perc
    if vgv_vendido_perc > 70: score_vgv_vendido = 5
    elif vgv_vendido_perc > 40: score_vgv_vendido = 3
    else: score_vgv_vendido = 1
    score_comercial = (score_ivv + score_vgv_vendido) / 2
    map_cronograma = {"Adiantado ou no prazo": 5, "Atraso leve (< 3 meses)": 4, "Atraso significativo (3-6 meses)": 2, "Atraso severo (> 6 meses)": 1}
    avanco_obra = st.session_state.avanco_fisico_obra
    if avanco_obra >= 90: score_avanco = 5
    elif avanco_obra >= 50: score_avanco = 3
    else: score_avanco = 1
    score_execucao = (map_cronograma[st.session_state.cronograma] + score_avanco) / 2
    return (score_viabilidade * 0.25) + (score_comercial * 0.40) + (score_execucao * 0.35)

def calcular_score_lastro_carteira():
    scores_qual = []
    valor_garantias = st.session_state.valor_garantias_carteira
    ltv_calculado = (st.session_state.saldo_devedor_carteira / valor_garantias) * 100 if valor_garantias > 0 else 999
    st.session_state.ltv_medio_carteira = ltv_calculado
    if ltv_calculado < 60: scores_qual.append(5)
    elif ltv_calculado <= 80: scores_qual.append(3)
    else: scores_qual.append(1)
    map_origem = {"Robusta e bem documentada (score, DTI, etc.)": 5, "Padrão de mercado": 3, "Frouxa, ad-hoc ou desconhecida": 1}
    scores_qual.append(map_origem[st.session_state.origem])
    score_qualidade = sum(scores_qual) / len(scores_qual)
    scores_perf = []
    inadimplencia = st.session_state.inadimplencia
    if inadimplencia < 1.0: scores_perf.append(5)
    elif inadimplencia <= 3.5: scores_perf.append(3)
    else: scores_perf.append(1)
    map_vintage = {"Estável ou melhorando": 5, "Com leve deterioração": 3, "Com deterioração clara e preocupante": 1}
    scores_perf.append(map_vintage[st.session_state.vintage])
    score_performance = sum(scores_perf) / len(scores_perf)
    concentracao_top5 = st.session_state.concentracao_top5
    if concentracao_top5 < 10: score_concentracao = 5
    elif concentracao_top5 <= 30: score_concentracao = 3
    else: score_concentracao = 1
    return (score_qualidade * 0.40) + (score_performance * 0.40) + (score_concentracao * 0.20)

def calcular_score_estrutura():
    scores_capital = []
    if st.session_state.estrutura_tipo == "Série Única":
        scores_capital.append(1)
    else:
        subordinacao = st.session_state.subordinacao
        if subordinacao > 20: scores_capital.append(5)
        elif subordinacao >= 10: scores_capital.append(3)
        else: scores_capital.append(1)
    map_waterfall = {"Clara, protetiva e bem definida": 5, "Padrão de mercado com alguma ambiguidade": 3, "Ambígua, com brechas ou prejudicial à série": 1}
    scores_capital.append(map_waterfall[st.session_state.waterfall])
    score_capital = sum(scores_capital) / len(scores_capital)
    scores_reforco = []
    fundo_reserva_pmts = st.session_state.fundo_reserva_pmts
    if fundo_reserva_pmts > 3: score_fundo = 5
    elif fundo_reserva_pmts >= 1: score_fundo = 3
    else: score_fundo = 1
    if not st.session_state.fundo_reserva_regra: score_fundo = max(1, score_fundo - 1)
    scores_reforco.append(score_fundo)
    oc = st.session_state.sobrecolateralizacao
    if oc > 120: scores_reforco.append(5)
    elif oc >= 105: scores_reforco.append(3)
    else: scores_reforco.append(1)
    spread = st.session_state.spread_excedente
    if spread > 3: scores_reforco.append(5)
    elif spread >= 1: scores_reforco.append(3)
    else: scores_reforco.append(1)
    score_reforco = sum(scores_reforco) / len(scores_reforco)
    scores_garantias = []
    map_tipo_garantia = {"Alienação Fiduciária de Imóveis": 5, "Cessão Fiduciária de Recebíveis": 4, "Fiança ou Aval": 2, "Sem garantia real (Fidejussória)": 1}
    garantias_selecionadas = st.session_state.tipo_garantia
    if not garantias_selecionadas: score_tipo = 1
    else:
        scores_das_selecionadas = [map_tipo_garantia.get(g, 1) for g in garantias_selecionadas]
        score_base = max(scores_das_selecionadas)
        bonus = (len(garantias_selecionadas) - 1) * 0.5
        score_tipo = min(5, score_base + bonus)
    scores_garantias.append(score_tipo)
    ltv = st.session_state.ltv_garantia
    if ltv < 50: scores_garantias.append(5)
    elif ltv <= 70: scores_garantias.append(3)
    else: scores_garantias.append(1)
    map_liquidez_garantia = {"Alta (ex: aptos residenciais em capital)": 5, "Média (ex: salas comerciais, loteamentos)": 3, "Baixa (ex: imóvel de uso específico, rural)": 1}
    scores_garantias.append(map_liquidez_garantia[st.session_state.liquidez_garantia])
    score_garantias = sum(scores_garantias) / len(scores_garantias)
    return (score_capital * 0.40) + (score_reforco * 0.30) + (score_garantias * 0.30)

def calcular_score_juridico():
    scores_conflito = []
    map_independencia = {"Totalmente independentes": 5, "Partes relacionadas com mitigação de conflitos": 3, "Mesmo grupo econômico com alto potencial de conflito": 1}
    scores_conflito.append(map_independencia[st.session_state.independencia])
    scores_conflito.append(5 if st.session_state.retencao_risco else 2)
    map_historico = {"Alinhado aos interesses dos investidores": 5, "Decisões mistas, alguns waivers aprovados": 3, "Histórico de decisões que beneficiam o devedor": 1}
    scores_conflito.append(map_historico[st.session_state.historico_decisoes])
    score_conflito = sum(scores_conflito) / len(scores_conflito)
    scores_prestadores = []
    map_ag_fiduciario = {"Alta, com histórico de proatividade": 5, "Média, cumpre o papel protocolar": 3, "Baixa, passivo ou com histórico negativo": 1}
    scores_prestadores.append(map_ag_fiduciario[st.session_state.ag_fiduciario])
    map_securitizadora = {"Alta, experiente e com bom histórico": 5, "Média, com histórico misto": 3, "Nova ou com histórico negativo": 1}
    scores_prestadores.append(map_securitizadora[st.session_state.securitizadora])
    map_servicer = {"Alta, com processos e tecnologia robustos": 5, "Padrão de mercado": 4, "Fraca ou inadequada": 2, "Não aplicável / Não avaliado": 4}
    scores_prestadores.append(map_servicer[st.session_state.servicer])
    score_prestadores = sum(scores_prestadores) / len(scores_prestadores)
    scores_contratual = []
    map_covenants = {"Fortes, objetivos e com gatilhos claros": 5, "Padrão, com alguma subjetividade": 3, "Fracos, subjetivos ou fáceis de contornar": 1}
    scores_contratual.append(map_covenants[st.session_state.covenants])
    map_pareceres = {"Abrangentes e conclusivos (escritório 1ª linha)": 5, "Padrão, cumprem requisitos formais": 4, "Limitados ou com ressalvas": 2}
    scores_contratual.append(map_pareceres[st.session_state.pareceres])
    map_relatorios = {"Alta, detalhados e frequentes": 5, "Média, cumprem o mínimo regulatório": 3, "Baixa, informações inconsistentes ou atrasadas": 1}
    scores_contratual.append(map_relatorios[st.session_state.relatorios])
    score_contratual = sum(scores_contratual) / len(scores_contratual)
    return (score_conflito * 0.50) + (score_prestadores * 0.30) + (score_contratual * 0.20)

# ==============================================================================
# FUNÇÕES DE MODELAGEM FINANCEIRA E IA
# ==============================================================================
@st.cache_data
def gerar_analise_ia(nome_pilar, dados_pilar_str):
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    except Exception:
        return "Erro: A chave da API do Gemini (GEMINI_API_KEY) não foi encontrada. Configure o arquivo `.streamlit/secrets.toml`."
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Aja como um analista de crédito sênior, especialista em operações estruturadas (CRI) no Brasil.
    Sua tarefa é analisar os dados do pilar '{nome_pilar}' de uma operação de CRI e fornecer uma análise qualitativa concisa.
    Estruture sua resposta em três seções obrigatórias, usando markdown:
    1.  **Pontos Positivos**: Destaque os fatores que mitigam o risco.
    2.  **Pontos de Atenção**: Aponte os fatores que representam um risco potencial ou que merecem monitoramento.
    3.  **Possíveis Incongruências**: Se houver, aponte dados que parecem contraditórios entre si.
    Seja direto e foque nos pontos mais relevantes para um investidor.
    **Dados para Análise:**
    ---
    {dados_pilar_str}
    ---
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Ocorreu um erro ao chamar a API do Gemini: {e}"

def gerar_fluxo_carteira(ss):
    try:
        saldo_devedor, taxa_aa, prazo, amortizacao_tipo = ss.cart_sd_total, ss.cart_taxa_media / 100, int(ss.cart_prazo_medio), ss.cart_amortizacao
        taxa_am = (1 + taxa_aa)**(1/12) - 1
        fluxo, saldo_atual = [], saldo_devedor
        for mes in range(1, prazo + 1):
            if saldo_atual < 1: break
            juros = saldo_atual * taxa_am
            if amortizacao_tipo == 'Price': principal = npf.pmt(taxa_am, prazo - mes + 1, -saldo_atual) - juros
            else: principal = saldo_devedor / prazo
            principal = min(principal, saldo_atual)
            fluxo.append({"Mês": mes, "Juros Recebidos": juros, "Amortização Recebida": principal, "Saldo Devedor": saldo_atual - principal})
            saldo_atual -= principal
        return pd.DataFrame(fluxo)
    except Exception as e:
        st.error(f"Erro ao gerar fluxo da carteira: {e}")
        return pd.DataFrame()

def gerar_fluxo_projeto(ss):
    try:
        unidades_data = ss.proj_tipologias
        df_unidades = pd.DataFrame()
        if isinstance(unidades_data, pd.DataFrame):
            df_unidades = unidades_data.copy().dropna(how='all')
        elif isinstance(unidades_data, list):
            unidades_data_limpa = [d for d in unidades_data if isinstance(d, dict) and d]
            if unidades_data_limpa: df_unidades = pd.DataFrame(unidades_data_limpa)
        elif isinstance(unidades_data, dict):
            lista_de_linhas = list(unidades_data.values())
            colunas = ['nome', 'area', 'estoque', 'vendidas', 'permutadas', 'preco_m2']
            df_unidades = pd.DataFrame(lista_de_linhas, columns=colunas).dropna(how='all')
        else:
            st.error(f"Formato de dados da tabela de unidades não reconhecido: {type(unidades_data)}")
            return pd.DataFrame()
        if df_unidades.empty:
            st.warning("Adicione e configure pelo menos uma tipologia de unidade para modelar.")
            return pd.DataFrame()
        colunas_necessarias = ['nome', 'area', 'estoque', 'vendidas', 'permutadas', 'preco_m2']
        if not all(col in df_unidades.columns for col in colunas_necessarias):
            st.error(f"Erro: A tabela de unidades não contém as colunas necessárias.")
            return pd.DataFrame()
        for col in ['estoque', 'area', 'preco_m2', 'vendidas', 'permutadas']: df_unidades[col] = pd.to_numeric(df_unidades[col])
        df_unidades['VGV Estoque'] = df_unidades['estoque'] * df_unidades['area'] * df_unidades['preco_m2']
        estoque_vgv_inicial = df_unidades['VGV Estoque'].sum()
        custo_total_obra, prazo_obra, ivv_projetado = ss.proj_custo_obra, int(ss.proj_prazo_obra), ss.proj_ivv_projecao / 100
        divida_total_cri, taxa_cri_aa, prazo_cri = ss.op_volume, ss.op_taxa / 100, int(ss.op_prazo)
        taxa_cri_am = (1 + taxa_cri_aa)**(1/12) - 1
        fluxo, saldo_obra_a_desembolsar, estoque_vgv_atual, saldo_devedor_cri = [], custo_total_obra, estoque_vgv_inicial, divida_total_cri
        for mes in range(1, prazo_cri + 1):
            desembolso_obra, receita_vendas = 0, 0
            if mes <= prazo_obra and saldo_obra_a_desembolsar > 0:
                desembolso_mensal = custo_total_obra / prazo_obra
                desembolso_obra = min(desembolso_mensal, saldo_obra_a_desembolsar)
                saldo_obra_a_desembolsar -= desembolso_obra
            if estoque_vgv_atual > 0:
                venda_do_mes = estoque_vgv_atual * ivv_projetado
                receita_vendas = min(venda_do_mes, estoque_vgv_atual)
                estoque_vgv_atual -= receita_vendas
            juros_cri = saldo_devedor_cri * taxa_cri_am
            amortizacao_cri = min(npf.pmt(taxa_cri_am, prazo_cri - mes + 1, -saldo_devedor_cri) - juros_cri, saldo_devedor_cri) if saldo_devedor_cri > 0 else 0
            obrigacoes_totais = juros_cri + amortizacao_cri
            caixa_liquido = receita_vendas - desembolso_obra - obrigacoes_totais
            fluxo.append({"Mês": mes, "Receita de Vendas": receita_vendas, "Desembolso da Obra": desembolso_obra, "Obrigações do CRI": obrigacoes_totais, "Fluxo de Caixa Líquido": caixa_liquido, "Saldo Devedor CRI": saldo_devedor_cri - amortizacao_cri, "Estoque Remanescente (VGV)": estoque_vgv_atual})
            saldo_devedor_cri -= amortizacao_cri
            if saldo_devedor_cri < 1 and estoque_vgv_atual < 1 and saldo_obra_a_desembolsar < 1: break
        return pd.DataFrame(fluxo)
    except Exception as e:
        st.error(f"Erro ao gerar fluxo do projeto: {e}")
        return pd.DataFrame()

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
    saldo_lastro_sim, saldo_cri_sim, historico, defaults_pendentes = saldo_lastro, saldo_cri_p5, [], {}
    for mes in range(1, int(prazo) + 1):
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
            recuperacao_do_mes = defaults_pendentes.pop(mes_recuperacao) * (1 - severidade_perda)
        caixa_disponivel = juros_recebido + amortizacao_programada_lastro + prepagamentos + recuperacao_do_mes - despesas
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
    return max(0, saldo_cri_sim), pd.DataFrame(historico)

# ==============================================================================
# CORPO PRINCIPAL DA APLICAÇÃO
# ==============================================================================
st.set_page_config(layout="wide", page_title="Análise e Rating de CRI")
col1, col2 = st.columns([1, 5], gap="medium") # Cria duas colunas, a segunda é 5x mais larga

with col1:
    # Substitua "assets/seu_logo.png" pelo caminho correto do seu arquivo de imagem
    st.image("assets/seu_logo.png", width=120) 

with col2:
    st.title("Plataforma de Análise e Rating de CRI")
    st.markdown("Desenvolvido em parceria com a IA 'Projeto de Análise e Rating de CRI v2'")

st.divider() # Adiciona uma linha divisória para um visual mais limpo

inicializar_session_state()

tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📝 Cadastro", "Pilar 1", "Pilar 2", "Pilar 3", "Pilar 4", "📊 Modelagem", "Resultado"])

with tab0:
    st.header("Informações Gerais da Operação (Folha de Rosto)")
    st.markdown("Dados descritivos para identificação e composição do relatório final. **Não impactam o cálculo do rating.**")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Identificação da Emissão")
        st.text_input("Nome da Operação:", key='op_nome')
        st.text_input("Código de Negociação (CETIP/B3):", key='op_codigo')
        st.number_input("Volume Total Emitido (R$):", key='op_volume', format="%.2f")
        c1_taxa, c2_taxa = st.columns([1,2])
        with c1_taxa: st.selectbox("Indexador:", ["IPCA +", "CDI +", "Pré-fixado"], key='op_indexador')
        with c2_taxa: st.number_input("Taxa (% a.a.):", key='op_taxa', format="%.2f")
        st.number_input("Prazo Total da Emissão (meses):", key='op_prazo', step=1)
    with col2:
        st.subheader("Datas e Participantes")
        st.date_input("Data de Emissão:", key='op_data_emissao')
        st.date_input("Data de Vencimento:", key='op_data_vencimento')
        st.date_input("Data de Lançamento do Empreendimento:", key='op_data_lancamento_projeto')
        st.text_input("Securitizadora:", key='op_securitizadora', help="Responsável por estruturar e emitir o CRI.")
        st.text_input("Originador/Cedente:", key='op_originador', help="A empresa que originou os créditos (ex: a construtora).")
        st.text_input("Agente Fiduciário:", key='op_agente_fiduciario', help="Representante legal dos investidores (os titulares dos CRIs).")

with tab1:
    st.header("Pilar 1: Análise do Risco do Originador/Devedor")
    st.markdown("Peso no Scorecard Mestre: **20%**")
    with st.expander("Fator 1: Governança e Reputação (Peso: 30%)", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Histórico de emissões:", ["Emissor recorrente com bom histórico", "Poucas emissões ou histórico misto", "Primeira emissão", "Histórico negativo"], key='hist_emissor')
            st.radio("UBOs identificados?", ["Sim", "Parcialmente", "Não"], key='ubo')
            st.selectbox("Políticas de compliance:", ["Maduras e implementadas", "Em desenvolvimento", "Inexistentes ou ad-hoc"], key='compliance')
            st.checkbox("Ressalvas relevantes na auditoria?", key='ressalvas')
            st.checkbox("Histórico de renegociação de dívidas?", key='renegociacao')
        with c2:
            st.selectbox("Experiência do quadro executivo:", ["Altamente experiente e com boa reputação", "Experiência moderada", "Inexperiente ou com reputação questionável"], key='exp_socios')
            st.selectbox("Estrutura do conselho:", ["Independente e atuante", "Majoritariamente independente", "Consultivo/Sem independência", "Inexistente"], key='conselho')
            st.selectbox("Auditoria por:", ["Big Four", "Auditoria de Grande Porte (fora do Big Four)", "Auditoria de Pequeno Porte/Contador", "Não auditado"], key='auditoria')
            st.selectbox("Nível de litígios:", ["Inexistente ou irrelevante", "Baixo impacto financeiro", "Médio impacto potencial", "Alto impacto / Risco para a operação"], key='litigios')
            st.checkbox("Comitês formais (auditoria/riscos)?", key='comites')
            st.checkbox("Envolvimento em notícias negativas?", key='midia_negativa')
            st.markdown("---"); st.markdown("**Checkpoints de Risco Específico**")
            opcoes_risco = ["Baixo / Gerenciado", "Moderado / Pontos de Atenção", "Alto / Risco Relevante"]
            st.selectbox("Risco Jurídico/Regulatório:", opcoes_risco, key='risco_juridico')
            st.selectbox("Risco Ambiental:", opcoes_risco, key='risco_ambiental')
            st.selectbox("Risco Social/Trabalhista:", opcoes_risco, key='risco_social')
    with st.expander("Fator 2: Histórico Operacional (Peso: 30%)"):
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Experiência em projetos semelhantes:", ["Extensa e comprovada no segmento específico", "Experiência relevante em segmentos correlatos", "Experiência limitada ou em outros segmentos", "Iniciante/Nenhuma"], key='exp_similar')
            st.selectbox("Reputação com clientes:", ["Positiva, baixo volume de queixas", "Neutra, volume gerenciável", "Negativa, alto volume de queixas sem resolução"], key='reputacao')
            st.selectbox("Histórico dos sócios:", ["Sócio(s) com múltiplos empreendimentos de sucesso comprovado", "Sócio(s) com algum histórico de sucesso, sem falhas relevantes", "Primeiro empreendimento ou histórico desconhecido", "Sócio(s) com histórico de falências ou recuperações judiciais"], key='hist_socios')
        with c2:
            st.selectbox("Histórico de entrega de projetos:", ["Consistente e previsível", "Desvios esporádicos", "Atrasos e estouros recorrentes"], key='track_record')
            st.selectbox("Análise de crédito para recebíveis:", ["Score de crédito, análise de renda (DTI) e garantias", "Apenas análise de renda e garantias", "Análise simplificada ou ad-hoc"], key='analise_credito')
            st.checkbox("Política de crédito formalizada?", key='politica_formalizada')
    with st.expander("Fator 3: Saúde Financeira (Peso: 40%)"):
        st.radio("Modalidade de análise:", ('Análise Corporativa (Holding/Incorporadora)', 'Análise de Projeto (SPE)'), key='modalidade_financeira', horizontal=True)
    if st.button("Calcular Score do Pilar 1", use_container_width=True):
        st.session_state.scores['pilar1'] = (calcular_score_governanca() * 0.3) + (calcular_score_operacional() * 0.3) + (calcular_score_financeiro() * 0.4)
        st.plotly_chart(create_gauge_chart(st.session_state.scores['pilar1'], "Score Ponderado (Pilar 1)"), use_container_width=True)
    st.divider()
    st.subheader("🤖 Análise com IA Gemini")
    if st.button("Gerar Análise Qualitativa para o Pilar 1", key="ia_pilar1", use_container_width=True):
        dados_p1_str = f"- Histórico: {st.session_state.hist_emissor}, Experiência Executivos: {st.session_state.exp_socios}\n- Histórico Sócios: {st.session_state.hist_socios}, UBOs: {st.session_state.ubo}\n- Conselho: {st.session_state.conselho}, Comitês: {'Sim' if st.session_state.comites else 'Não'}\n- Auditoria: {st.session_state.auditoria}, Ressalvas: {'Sim' if st.session_state.ressalvas else 'Não'}\n- Riscos Específicos (Jurídico, Ambiental, Social): {st.session_state.risco_juridico}, {st.session_state.risco_ambiental}, {st.session_state.risco_social}"
        with st.spinner("Analisando o Pilar 1..."):
            st.session_state.analise_p1 = gerar_analise_ia("Pilar 1: Originador e Devedor", dados_p1_str)
    if "analise_p1" in st.session_state:
        with st.container(border=True): st.markdown(st.session_state.analise_p1)

with tab2:
    st.header("Pilar 2: Análise do Lastro")
    st.markdown("Peso no Scorecard Mestre: **30%**")
    st.radio("Selecione a natureza do lastro:",('Desenvolvimento Imobiliário (Risco de Projeto)', 'Carteira de Recebíveis (Risco de Crédito)'), key="tipo_lastro", horizontal=True)
    if st.session_state.tipo_lastro == 'Desenvolvimento Imobiliário (Risco de Projeto)':
        with st.expander("Fator 1: Viabilidade de Mercado (Peso: 25%)", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                st.selectbox("Segmento do Projeto:", ["Residencial Vertical", "Residencial Horizontal (Condomínio)", "Comercial (Salas/Lajes)", "Loteamento", "Multipropriedade"], key='segmento_projeto')
                st.selectbox("Qualidade do Município:", ["Capital / Metrópole", "Cidade Grande (>500k hab)", "Cidade Média (100-500k hab)", "Cidade Pequena (<100k hab)"], key='qualidade_municipio')
            with c2:
                st.selectbox("Qualidade da Microlocalização:", ["Nobre / Premium", "Boa", "Regular", "Periférica / Risco"], key='microlocalizacao')
                st.text_input("Cidade/Estado para Mapa:", key='cidade_mapa', help="Ex: 'Rio de Janeiro, RJ'.")
        with st.expander("Fator 2: Performance Comercial (Peso: 40%)"):
            c1, c2, c3 = st.columns(3)
            with c1: st.number_input("Unidades Vendidas no Último Mês:", min_value=0, key='unidades_vendidas_mes')
            with c2: st.number_input("Unidades em Oferta no Início do Mês:", min_value=1, key='unidades_ofertadas_inicio_mes')
            with c3:
                unid_ofertadas = st.session_state.unidades_ofertadas_inicio_mes
                ivv_calculado = (st.session_state.unidades_vendidas_mes / unid_ofertadas) * 100 if unid_ofertadas > 0 else 0
                st.metric("IVV Calculado", f"{ivv_calculado:.2f}%")
            st.slider("Percentual do VGV total já vendido (%)", 0, 100, key='vgv_vendido_perc')
        with st.expander("Fator 3: Risco de Execução (Peso: 35%)"):
            st.slider("Avanço Físico da Obra (%)", 0, 100, key='avanco_fisico_obra')
            st.selectbox("Aderência ao cronograma:", ["Adiantado ou no prazo", "Atraso leve (< 3 meses)", "Atraso significativo (3-6 meses)", "Atraso severo (> 6 meses)"], key='cronograma')
            st.selectbox("Aderência ao orçamento:", ["Dentro do orçamento", "Estouro leve (<5%)", "Estouro moderado (5-10%)", "Estouro severo (>10%)"], key='orcamento')
            st.selectbox("Suficiência do Fundo de Obras:", ["Suficiente com margem (>110%)", "Suficiente (100-110%)", "Insuficiente (<100%)"], key='fundo_obras')
        if st.button("Calcular Score e Mapa do Pilar 2 (Projeto)", use_container_width=True):
            st.session_state.scores['pilar2'] = calcular_score_lastro_projeto()
            st.session_state.map_data = get_coords(st.session_state.cidade_mapa)
            st.plotly_chart(create_gauge_chart(st.session_state.scores['pilar2'], "Score Ponderado (Pilar 2)"), use_container_width=True)
    st.markdown("---")
    st.subheader("Painel de Indicadores-Chave (Projeto)")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("IVV (Velocidade de Vendas)", f"{st.session_state.get('ivv_calculado', 0):.2f}%")
    kpi2.metric("Avanço Físico da Obra", f"{st.session_state.avanco_fisico_obra}%")
    kpi3.metric("Situação do Cronograma", st.session_state.cronograma)
        
    # Bloco para exibir o mapa
    if st.session_state.get('map_data') is not None:
            st.map(st.session_state.map_data, zoom=11)
            st.caption(f"Localização aproximada de {st.session_state.cidade_mapa}")
    else:
        with st.expander("Fator 1: Qualidade da Carteira (Peso: 40%)", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1: st.number_input("Saldo Devedor Total da Carteira (R$)", key='saldo_devedor_carteira')
            with c2: st.number_input("Valor de Avaliação Total das Garantias (R$)", key='valor_garantias_carteira')
            with c3:
                valor_garantias = st.session_state.valor_garantias_carteira
                ltv_calculado = (st.session_state.saldo_devedor_carteira / valor_garantias) * 100 if valor_garantias > 0 else 0
                st.metric("LTV Médio Calculado", f"{ltv_calculado:.2f}%")
            st.selectbox("Qualidade da política de crédito:", ["Robusta e bem documentada (score, DTI, etc.)", "Padrão de mercado", "Frouxa, ad-hoc ou desconhecida"], key='origem')
        with st.expander("Fator 2: Performance Histórica (Peso: 40%)"):
            st.number_input("Inadimplência da carteira (> 90 dias) (%)", key='inadimplencia')
            st.selectbox("Análise de safras (vintage):", ["Estável ou melhorando", "Com leve deterioração", "Com deterioração clara e preocupante"], key='vintage')
        with st.expander("Fator 3: Concentração (Peso: 20%)"):
            st.number_input("Concentração nos 5 maiores devedores (%)", key='concentracao_top5')
        if st.button("Calcular Score do Pilar 2 (Carteira)", use_container_width=True):
            st.session_state.scores['pilar2'] = calcular_score_lastro_carteira()
            st.plotly_chart(create_gauge_chart(st.session_state.scores['pilar2'], "Score Ponderado (Pilar 2)"), use_container_width=True)
    st.divider()
    st.subheader("🤖 Análise com IA Gemini")
    if st.button("Gerar Análise Qualitativa para o Pilar 2", key="ia_pilar2", use_container_width=True):
        dados_p2_str = ""
        if st.session_state.tipo_lastro == 'Desenvolvimento Imobiliário (Risco de Projeto)':
            dados_p2_str = f"- Tipo: Desenvolvimento Imobiliário\n- Segmento: {st.session_state.segmento_projeto}\n- Localização: {st.session_state.microlocalizacao} em {st.session_state.qualidade_municipio}\n- Performance: IVV de {st.session_state.ivv_calculado:.2f}%, VGV vendido: {st.session_state.vgv_vendido_perc}%\n- Execução: {st.session_state.avanco_fisico_obra}% da obra concluída, Cronograma: {st.session_state.cronograma}"
        else:
            dados_p2_str = f"- Tipo: Carteira de Recebíveis\n- Qualidade: LTV Médio de {st.session_state.ltv_medio_carteira:.2f}%, Originação: {st.session_state.origem}\n- Performance: Inadimplência>90d de {st.session_state.inadimplencia}%, Safras: {st.session_state.vintage}\n- Concentração (Top 5): {st.session_state.concentracao_top5}%"
        with st.spinner("Analisando o Pilar 2..."):
            st.session_state.analise_p2 = gerar_analise_ia("Pilar 2: Lastro", dados_p2_str)
    if "analise_p2" in st.session_state:
        with st.container(border=True): st.markdown(st.session_state.analise_p2)

with tab3:
    st.header("Pilar 3: Análise da Estrutura e Mecanismos de Reforço de Crédito")
    st.markdown("Peso no Scorecard Mestre: **30%**")
    with st.expander("Fator 1: Estrutura de Capital (Peso: 40%)", expanded=True):
        st.radio("Tipo de Estrutura de Capital:", options=["Múltiplas Séries (com subordinação)", "Série Única"], key='estrutura_tipo', horizontal=True)
        if st.session_state.estrutura_tipo == "Múltiplas Séries (com subordinação)":
            st.number_input("Nível de subordinação (%) para a série em análise", key='subordinacao', help="Principal 'colchão' de proteção da série. Quanto maior, melhor.")
        st.selectbox("Qualidade da Cascata de Pagamentos (Waterfall)", ["Clara, protetiva e bem definida", "Padrão de mercado com alguma ambiguidade", "Ambígua, com brechas ou prejudicial à série"], key='waterfall')
    with st.expander("Fator 2: Mecanismos de Reforço e Liquidez (Peso: 30%)"):
        st.number_input("Tamanho do Fundo de Reserva (em nº de pagamentos)", key='fundo_reserva_pmts')
        st.checkbox("O Fundo de Reserva possui mecanismo de recomposição obrigatória?", key='fundo_reserva_regra')
        st.number_input("Índice de Sobrecolateralização (%)", key='sobrecolateralizacao')
        st.number_input("Spread Excedente anualizado (%)", key='spread_excedente')
    with st.expander("Fator 3: Qualidade das Garantias (Peso: 30%)"):
        st.multiselect("Selecione todos os tipos de garantia presentes na estrutura:", options=["Alienação Fiduciária de Imóveis", "Cessão Fiduciária de Recebíveis", "Fiança ou Aval", "Sem garantia real (Fidejussória)"], key='tipo_garantia')
        st.number_input("LTV Médio Ponderado das garantias (%)", key='ltv_garantia')
        st.selectbox("Liquidez estimada da garantia", ["Alta (ex: aptos residenciais em capital)", "Média (ex: salas comerciais, loteamentos)", "Baixa (ex: imóvel de uso específico, rural)"], key='liquidez_garantia')
    if st.button("Calcular Score do Pilar 3", use_container_width=True):
        st.session_state.scores['pilar3'] = calcular_score_estrutura()
        st.plotly_chart(create_gauge_chart(st.session_state.scores['pilar3'], "Score Ponderado (Pilar 3)"), use_container_width=True)
    st.divider()
    st.subheader("🤖 Análise com IA Gemini")
    if st.button("Gerar Análise Qualitativa para o Pilar 3", key="ia_pilar3", use_container_width=True):
        dados_p3_str = f"- Estrutura: {st.session_state.estrutura_tipo}\n- Subordinação: {st.session_state.subordinacao if st.session_state.estrutura_tipo != 'Série Única' else 'N/A'}%\n- Waterfall: {st.session_state.waterfall}\n- Reforços: Fundo de Reserva ({st.session_state.fundo_reserva_pmts} PMTs), Sobrecolateralização ({st.session_state.sobrecolateralizacao}%), Spread ({st.session_state.spread_excedente}%)\n- Garantias: {', '.join(st.session_state.tipo_garantia)}, LTV: {st.session_state.ltv_garantia}%"
        with st.spinner("Analisando o Pilar 3..."):
            st.session_state.analise_p3 = gerar_analise_ia("Pilar 3: Estrutura", dados_p3_str)
    if "analise_p3" in st.session_state:
        with st.container(border=True): st.markdown(st.session_state.analise_p3)

with tab4:
    st.header("Pilar 4: Análise Jurídica e de Governança da Operação")
    st.markdown("Peso no Scorecard Mestre: **20%**")
    with st.expander("Fator 1: Conflitos de Interesse (Peso: 50%)", expanded=True):
        st.selectbox("Nível de independência entre as partes:", ["Totalmente independentes", "Partes relacionadas com mitigação de conflitos", "Mesmo grupo econômico com alto potencial de conflito"], key='independencia')
        st.checkbox("Originador retém risco relevante?", key='retencao_risco')
        st.selectbox("Histórico de decisões em assembleias:", ["Alinhado aos interesses dos investidores", "Decisões mistas, alguns waivers aprovados", "Histórico de decisões que beneficiam o devedor"], key='historico_decisoes')
    with st.expander("Fator 2: Qualidade dos Prestadores de Serviço (Peso: 30%)"):
        st.selectbox("Reputação do Agente Fiduciário:", ["Alta, com histórico de proatividade", "Média, cumpre o papel protocolar", "Baixa, passivo ou com histórico negativo"], key='ag_fiduciario')
        st.selectbox("Reputação da Securitizadora:", ["Alta, experiente e com bom histórico", "Média, com histórico misto", "Nova ou com histórico negativo"], key='securitizadora')
        st.selectbox("Qualidade do Agente de Cobrança (Servicer):", ["Alta, com processos e tecnologia robustos", "Padrão de mercado", "Fraca ou inadequada", "Não aplicável / Não avaliado"], key='servicer')
    with st.expander("Fator 3: Robustez Contratual e Transparência (Peso: 20%)"):
        st.selectbox("Qualidade dos Covenants:", ["Fortes, objetivos e com gatilhos claros", "Padrão, com alguma subjetividade", "Fracos, subjetivos ou fáceis de contornar"], key='covenants')
        st.selectbox("Qualidade dos pareceres jurídicos:", ["Abrangentes e conclusivos (escritório 1ª linha)", "Padrão, cumprem requisitos formais", "Limitados ou com ressalvas"], key='pareceres')
        st.selectbox("Qualidade dos relatórios de acompanhamento:", ["Alta, detalhados e frequentes", "Média, cumprem o mínimo regulatório", "Baixa, informações inconsistentes ou atrasadas"], key='relatorios')
    if st.button("Calcular Score do Pilar 4", use_container_width=True):
        st.session_state.scores['pilar4'] = calcular_score_juridico()
        st.plotly_chart(create_gauge_chart(st.session_state.scores['pilar4'], "Score Ponderado (Pilar 4)"), use_container_width=True)
    st.divider()
    st.subheader("🤖 Análise com IA Gemini")
    if st.button("Gerar Análise Qualitativa para o Pilar 4", key="ia_pilar4", use_container_width=True):
        dados_p4_str = f"- Conflitos: {st.session_state.independencia}, Retenção de Risco: {'Sim' if st.session_state.retencao_risco else 'Não'}\n- Prestadores: Agente Fiduciário ({st.session_state.ag_fiduciario}), Securitizadora ({st.session_state.securitizadora})\n- Contratual: Covenants ({st.session_state.covenants}), Pareceres ({st.session_state.pareceres})"
        with st.spinner("Analisando o Pilar 4..."):
            st.session_state.analise_p4 = gerar_analise_ia("Pilar 4: Jurídico e Governança", dados_p4_str)
    if "analise_p4" in st.session_state:
        with st.container(border=True): st.markdown(st.session_state.analise_p4)

with tab5:
    st.header("📊 Pilar 5: Modelagem Financeira e Teste de Estresse")
    st.markdown("Esta seção é o motor quantitativo da análise. Modele o fluxo de caixa do lastro para, em seguida, validar a resiliência da estrutura através de testes de estresse.")
    tipo_modelagem = st.radio("Selecione a natureza do lastro para modelagem:", ('Projeto (Desenvolvimento Imobiliário)', 'Carteira de Recebíveis (Crédito Pulverizado)'), key="tipo_modelagem_p5", horizontal=True)
    st.divider()
    if tipo_modelagem == 'Projeto (Desenvolvimento Imobiliário)':
        st.subheader("Módulo de Modelagem: Risco de Projeto")
        col1, col2 = st.columns(2)
        with col1:
            with st.expander("Parâmetros Gerais do Empreendimento", expanded=True):
                st.number_input("VGV Total do Projeto (R$)", key="proj_vgv_total")
                st.number_input("Custo Total da Obra (R$)", key="proj_custo_obra")
                st.number_input("Área Total Construída (m²)", key="proj_area_total")
                st.number_input("Número Total de Unidades", key="proj_num_unidades", step=1)
                custo_por_m2 = st.session_state.proj_custo_obra / st.session_state.proj_area_total if st.session_state.proj_area_total else 0
                custo_sobre_vgv = (st.session_state.proj_custo_obra / st.session_state.proj_vgv_total) * 100 if st.session_state.proj_vgv_total else 0
                st.metric("Custo de Obra / m²", f"R$ {custo_por_m2:,.2f}")
                st.metric("Custo de Obra / VGV", f"{custo_sobre_vgv:.2f}%")
        with col2:
            with st.expander("Cronograma e Desembolso da Obra", expanded=True):
                st.number_input("Prazo da Obra (meses)", key="proj_prazo_obra", step=1)
                st.selectbox("Curva de Desembolso da Obra", ["Linear", "Curva 'S' Simplificada"], key="proj_curva_desembolso")
                st.info("Modelo atual usa desembolso Linear.", icon="ℹ️")
        with st.expander("Bolsão de Unidades e Status de Vendas", expanded=True):
            st.markdown("Adicione e configure cada tipo de unidade do empreendimento.")
            if st.button("Adicionar Nova Tipologia de Unidade", use_container_width=True):
                nova_tipologia = {'nome': f'Nova Tipologia {len(st.session_state.proj_tipologias) + 1}', 'area': 70.0, 'estoque': 10, 'vendidas': 0, 'permutadas': 0, 'preco_m2': 10000.0}
                st.session_state.proj_tipologias.append(nova_tipologia)
            st.divider()
            for i, tipologia in enumerate(st.session_state.proj_tipologias):
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    st.session_state.proj_tipologias[i]['nome'] = col1.text_input(f"Nome da Tipologia", value=tipologia['nome'], key=f"nome_{i}")
                    st.session_state.proj_tipologias[i]['area'] = col2.number_input(f"Área Média (m²)", value=tipologia['area'], key=f"area_{i}")
                    st.session_state.proj_tipologias[i]['preco_m2'] = col3.number_input(f"Preço/m² (R$)", value=tipologia['preco_m2'], key=f"preco_m2_{i}")
                    col_unid1, col_unid2, col_unid3 = st.columns(3)
                    st.session_state.proj_tipologias[i]['estoque'] = col_unid1.number_input(f"Unidades em Estoque", value=tipologia['estoque'], step=1, key=f"estoque_{i}")
                    st.session_state.proj_tipologias[i]['vendidas'] = col_unid2.number_input(f"Unidades Vendidas", value=tipologia['vendidas'], step=1, key=f"vendidas_{i}")
                    st.session_state.proj_tipologias[i]['permutadas'] = col_unid3.number_input(f"Unidades Permutadas", value=tipologia['permutadas'], step=1, key=f"permutadas_{i}")
        with st.expander("Projeção de Comercialização (Velocidade de Vendas)", expanded=True):
            st.slider("Velocidade de Vendas projetada (% do estoque/mês)", 0, 100, 5, key="proj_ivv_projecao")
        st.divider()
        if st.button("Modelar Cenário Base do Projeto", use_container_width=True):
            with st.spinner("Gerando fluxo de caixa do projeto..."):
                st.session_state.fluxo_modelado_df = gerar_fluxo_projeto(st.session_state)
        if not st.session_state.fluxo_modelado_df.empty:
            st.subheader("Resultados da Modelagem do Projeto")
            df = st.session_state.fluxo_modelado_df
            st.line_chart(df.set_index('Mês')[['Receita de Vendas', 'Desembolso da Obra', 'Obrigações do CRI']])
            st.area_chart(df.set_index('Mês')[['Fluxo de Caixa Líquido']])
            st.line_chart(df.set_index('Mês')[['Saldo Devedor CRI', 'Estoque Remanescente (VGV)']])
    elif tipo_modelagem == 'Carteira de Recebíveis (Crédito Pulverizado)':
        st.subheader("Módulo de Modelagem: Risco de Crédito")
        with st.expander("Características Gerais da Carteira", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.number_input("Saldo Devedor Atual da Carteira (R$)", key="cart_sd_total")
                st.number_input("Taxa de Juros Média Ponderada (% a.a.)", key="cart_taxa_media")
                st.selectbox("Sistema de Amortização Predominante", ["SAC", "Price"], key="cart_amortizacao")
            with col2:
                st.number_input("Prazo Remanescente Médio (meses)", key="cart_prazo_medio", step=1)
                st.slider("Percentual do Saldo com Pagamento 'Balão' (%)", 0, 100, 0, key="cart_perc_balao")
                st.number_input("LTV Médio Ponderado dos Clientes (%)", key="cart_ltv_medio")
        st.divider()
        if st.button("Modelar Cenário Base da Carteira", use_container_width=True):
            with st.spinner("Gerando fluxo de caixa da carteira..."):
                st.session_state.fluxo_modelado_df = gerar_fluxo_carteira(st.session_state)
        if not st.session_state.fluxo_modelado_df.empty:
            st.subheader("Resultados da Modelagem da Carteira")
            df = st.session_state.fluxo_modelado_df
            st.area_chart(df.set_index('Mês')[['Juros Recebidos', 'Amortização Recebida']])
            st.line_chart(df.set_index('Mês')[['Saldo Devedor']])
    st.divider()
    st.subheader("Validação da Estrutura: Teste de Estresse")
    st.markdown("Após modelar o cenário base, utilize esta seção para estressar as premissas e testar a resiliência.")
    with st.expander("Inputs do Modelo (Dados da Operação)", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1: st.number_input("Saldo Devedor do Lastro (R$)", key='saldo_lastro_p5')
        with c2: st.number_input("Taxa Média do Lastro (% a.a.)", key='taxa_lastro_p5')
        with c3: st.number_input("Prazo Remanescente (meses)", key='prazo_p5', step=1)
        c4, c5, c6 = st.columns(3)
        with c4: st.number_input("Saldo Devedor do CRI (Série Sênior) (R$)", key='saldo_cri_p5')
        with c5: st.number_input("Taxa da Série Sênior (% a.a.)", key='taxa_cri_p5')
        with c6: st.number_input("Despesas Fixas Mensais (R$)", key='despesas_p5')
    st.subheader("Definição das Premissas dos Cenários de Estresse")
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
    if st.button("Executar Simulação de Teste de Estresse", use_container_width=True):
        with st.spinner("Simulando cenários de estresse..."):
            perda_base, df_base = run_cashflow_simulation(cenarios['base'], st.session_state.saldo_lastro_p5, st.session_state.saldo_cri_p5, st.session_state.taxa_lastro_p5, st.session_state.taxa_cri_p5, st.session_state.prazo_p5, st.session_state.despesas_p5)
            perda_mod, df_mod = run_cashflow_simulation(cenarios['moderado'], st.session_state.saldo_lastro_p5, st.session_state.saldo_cri_p5, st.session_state.taxa_lastro_p5, st.session_state.taxa_cri_p5, st.session_state.prazo_p5, st.session_state.despesas_p5)
            perda_sev, df_sev = run_cashflow_simulation(cenarios['severo'], st.session_state.saldo_lastro_p5, st.session_state.saldo_cri_p5, st.session_state.taxa_lastro_p5, st.session_state.taxa_cri_p5, st.session_state.prazo_p5, st.session_state.despesas_p5)
            st.session_state.resultados_pilar5 = {'perda_base': perda_base, 'perda_moderado': perda_mod, 'perda_severo': perda_sev}
        st.success("Simulação de estresse concluída!")
    if st.session_state.get('resultados_pilar5') is not None:
        st.subheader("Resultados da Simulação de Estresse")
        rc1, rc2, rc3 = st.columns(3)
        rc1.metric("Perda de Principal (Base)", f"R$ {st.session_state.resultados_pilar5['perda_base']:,.2f}")
        rc2.metric("Perda de Principal (Moderado)", f"R$ {st.session_state.resultados_pilar5['perda_moderado']:,.2f}")
        rc3.metric("Perda de Principal (Severo)", f"R$ {st.session_state.resultados_pilar5['perda_severo']:,.2f}")

with tab6:
    st.header("Resultado Final e Atribuição de Rating")
    if len(st.session_state.scores) < 4:
        st.warning("Calcule todos os 4 pilares de score antes de prosseguir.")
    elif st.session_state.resultados_pilar5 is None:
        st.warning("Execute a simulação de Fluxo de Caixa no Pilar 5 antes de prosseguir.")
    else:
        pesos = {'pilar1': 0.20, 'pilar2': 0.30, 'pilar3': 0.30, 'pilar4': 0.20}
        score_final_ponderado = sum(st.session_state.scores.get(p, 1) * pesos[p] for p in pesos)
        rating_indicado = converter_score_para_rating(score_final_ponderado)
        st.subheader("Scorecard Mestre")
        data = {
            'Componente': ['Pilar 1: Originador/Devedor','Pilar 2: Lastro','Pilar 3: Estrutura e Reforços','Pilar 4: Jurídico/Governança'],
            'Peso': [f"{p*100:.0f}%" for p in pesos.values()],
            'Pontuação (1-5)': [f"{st.session_state.scores.get(p, 'N/A'):.2f}" for p in st.session_state.scores.keys()],
            'Score Ponderado': [f"{(st.session_state.scores.get(p, 1) * pesos[p]):.2f}" for p in pesos.keys()]
        }
        df_scores = pd.DataFrame(data).set_index('Componente')
        st.table(df_scores)
        c1, c2 = st.columns(2)
        c1.metric("Score Final Ponderado", f"{score_final_ponderado:.2f}")
        c2.metric("Rating Indicado (Série Sênior)", rating_indicado)
        st.divider()
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
        st.divider()
        st.subheader("Deliberação Final do Comitê de Rating")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.number_input("Ajuste Qualitativo (notches)", min_value=-3, max_value=3, step=1, key='ajuste_final')
            rating_final_senior = ajustar_rating(rating_indicado, st.session_state.ajuste_final)
            st.metric("Rating Final Atribuído (Sênior)", value=rating_final_senior)
            if st.session_state.estrutura_tipo == "Múltiplas Séries (com subordinação)":
                rating_subordinada_indicado = ajustar_rating(rating_final_senior, -4)
                st.metric("Rating Indicativo (Subordinada)", value=rating_subordinada_indicado)
            else:
                st.metric("Rating Indicativo (Subordinada)", value="Não Aplicável")
        with col2:
            st.text_area("Justificativa e comentários finais:", height=250, key='justificativa_final')
