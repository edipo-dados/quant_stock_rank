"""
Página de ranking de ativos.

Exibe tabela ordenável com todos os ativos rankeados por score.

Valida: Requisitos 11.1, 11.2, 11.3, 11.8
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os
import sys

# Adicionar diretório raiz ao path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.config import settings

# Configuração da página
st.set_page_config(
    page_title="Ranking - Quant Stock Ranker",
    page_icon="🏆",
    layout="wide"
)

st.title("🏆 Ranking de Ativos")

# URL da API
API_URL = settings.backend_url


def fetch_ranking(date=None):
    """
    Busca ranking da API.
    
    Args:
        date: Data do ranking (opcional)
        
    Returns:
        dict: Resposta da API ou None em caso de erro
    """
    try:
        url = f"{API_URL}/api/v1/ranking"
        params = {}
        if date:
            params['date'] = date
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao buscar ranking da API: {e}")
        return None


# Sidebar com filtros
st.sidebar.header("Filtros")

# Opção de data (por enquanto usa a mais recente)
use_latest = st.sidebar.checkbox("Usar data mais recente", value=True)
selected_date = None

if not use_latest:
    selected_date = st.sidebar.date_input(
        "Selecionar data",
        value=datetime.now().date()
    )
    selected_date = selected_date.strftime("%Y-%m-%d")

# Buscar dados
with st.spinner("Carregando ranking..."):
    ranking_data = fetch_ranking(date=selected_date if not use_latest else None)

if ranking_data:
    # Extrair informações
    date = ranking_data['date']
    rankings = ranking_data['rankings']
    total_assets = ranking_data['total_assets']
    
    # Exibir informações do ranking
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Data do Ranking", date)
    
    with col2:
        st.metric("Total de Ativos", total_assets)
    
    with col3:
        if rankings:
            top_ticker = rankings[0].get('ticker', 'N/A')
            top_score = rankings[0].get('final_score')
            
            # Formatar o valor do melhor ativo de forma segura
            melhor_ativo_text = str(top_ticker)
            if top_score is not None:
                try:
                    score_value = float(top_score)
                    if not pd.isna(score_value):
                        melhor_ativo_text = melhor_ativo_text + " (" + "{:.3f}".format(score_value) + ")"
                    else:
                        melhor_ativo_text = melhor_ativo_text + " (N/A)"
                except (ValueError, TypeError):
                    melhor_ativo_text = melhor_ativo_text + " (N/A)"
            else:
                melhor_ativo_text = melhor_ativo_text + " (N/A)"
            
            st.metric("Melhor Ativo", melhor_ativo_text)
    
    st.divider()
    
    # Converter para DataFrame para exibição
    if rankings:
        df_data = []
        for asset in rankings:
            # Verificar elegibilidade
            passed_eligibility = asset.get('passed_eligibility', True)
            penalty_factor = asset.get('penalty_factor', 1.0) or 1.0
            
            # Adicionar indicadores visuais
            ticker_display = asset.get('ticker', 'N/A')
            if not passed_eligibility:
                ticker_display = "⚠️ {}".format(ticker_display)
            elif penalty_factor < 1.0:
                ticker_display = "🛡️ {}".format(ticker_display)
            
            # Função auxiliar para tratar valores None/NaN
            def safe_round(value, decimals=3):
                if value is None:
                    return 0.0
                try:
                    # Verificar se é NaN
                    if pd.isna(value):
                        return 0.0
                    return round(float(value), decimals)
                except (ValueError, TypeError):
                    return 0.0
            
            df_data.append({
                'Posição': asset.get('rank', 0) or 0,
                'Ticker': ticker_display,
                'Score Final': safe_round(asset.get('final_score'), 3),
                'Score Base': safe_round(asset.get('base_score', asset.get('final_score')), 3),
                'Penalidade': safe_round(penalty_factor, 3),
                'Momentum': safe_round(asset.get('momentum_score'), 3),
                'Qualidade': safe_round(asset.get('quality_score'), 3),
                'Valor': safe_round(asset.get('value_score'), 3),
                'Confiança': safe_round(asset.get('confidence', 0.0), 2)
            })
        
        df = pd.DataFrame(df_data)
        
        # Opções de visualização
        st.subheader("Ranking Completo")
        
        # Filtro de busca por ticker
        search_ticker = st.text_input("🔍 Buscar ticker", "").upper()
        
        if search_ticker:
            df_filtered = df[df['Ticker'].str.contains(search_ticker, case=False)]
        else:
            df_filtered = df
        
        # Exibir tabela
        st.dataframe(
            df_filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Posição': st.column_config.NumberColumn(
                    'Posição',
                    help="Posição no ranking",
                    format="%d"
                ),
                'Ticker': st.column_config.TextColumn(
                    'Ticker',
                    help="Símbolo do ativo (⚠️ = não elegível, 🛡️ = com penalidades)"
                ),
                'Score Final': st.column_config.NumberColumn(
                    'Score Final',
                    help="Score final após penalidades",
                    format="%.3f"
                ),
                'Score Base': st.column_config.NumberColumn(
                    'Score Base',
                    help="Score base antes das penalidades",
                    format="%.3f"
                ),
                'Penalidade': st.column_config.NumberColumn(
                    'Penalidade',
                    help="Fator de penalidade aplicado (1.0 = sem penalidade)",
                    format="%.3f"
                ),
                'Momentum': st.column_config.NumberColumn(
                    'Momentum',
                    help="Score de momentum",
                    format="%.3f"
                ),
                'Qualidade': st.column_config.NumberColumn(
                    'Qualidade',
                    help="Score de qualidade",
                    format="%.3f"
                ),
                'Valor': st.column_config.NumberColumn(
                    'Valor',
                    help="Score de valor",
                    format="%.3f"
                ),
                'Confiança': st.column_config.ProgressColumn(
                    'Confiança',
                    help="Score de confiança (0-1)",
                    format="%.2f",
                    min_value=0,
                    max_value=1
                )
            }
        )
        
        st.caption(f"Exibindo {len(df_filtered)} de {total_assets} ativos")
        st.caption("⚠️ = Não passou no filtro de elegibilidade | 🛡️ = Penalidades de risco aplicadas")
        
        # Seção de navegação para detalhes
        st.divider()
        st.subheader("Ver Detalhes de um Ativo")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Seletor de ticker
            selected_ticker = st.selectbox(
                "Selecione um ticker para ver detalhes",
                options=df['Ticker'].tolist(),
                index=0
            )
        
        with col2:
            st.write("")  # Espaçamento
            st.write("")  # Espaçamento
            # Botão para navegar para página de detalhes
            if st.button("📊 Ver Detalhes", use_container_width=True):
                # Armazenar ticker selecionado no session state
                st.session_state['selected_ticker'] = selected_ticker
                st.switch_page("pages/3_📊_Detalhes_do_Ativo.py")
        
        # Estatísticas do ranking
        st.divider()
        st.subheader("Estatísticas do Ranking")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_score = df['Score Final'].mean()
            st.metric("Score Médio", f"{avg_score:.3f}" if not pd.isna(avg_score) else "N/A")
        
        with col2:
            max_score = df['Score Final'].max()
            st.metric("Score Máximo", f"{max_score:.3f}" if not pd.isna(max_score) else "N/A")
        
        with col3:
            min_score = df['Score Final'].min()
            st.metric("Score Mínimo", f"{min_score:.3f}" if not pd.isna(min_score) else "N/A")
        
        with col4:
            std_score = df['Score Final'].std()
            st.metric("Desvio Padrão", f"{std_score:.3f}" if not pd.isna(std_score) else "N/A")
        
    else:
        st.warning("Nenhum ativo encontrado no ranking.")

else:
    st.error("Não foi possível carregar o ranking. Verifique se a API está rodando.")
    st.info(f"URL da API: {API_URL}/api/v1/ranking")
