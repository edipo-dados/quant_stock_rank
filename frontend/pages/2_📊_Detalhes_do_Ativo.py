"""
Página de detalhes de um ativo específico.

Exibe score completo, breakdown, explicação e gráfico de preços.

Valida: Requisitos 11.4, 11.5, 11.6, 11.7, 11.8
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys

# Adicionar diretório raiz ao path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.config import settings

# Configuração da página
st.set_page_config(
    page_title="Detalhes do Ativo - Quant Stock Ranker",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Detalhes do Ativo")

# URL da API
API_URL = settings.backend_url


def safe_format(value, format_str=".3f", default="N/A"):
    """
    Formata um valor de forma segura, tratando None e NaN.
    
    Args:
        value: Valor a ser formatado
        format_str: String de formatação (ex: ".3f", ".2f", ".0%")
        default: Valor padrão se value for None ou NaN
        
    Returns:
        str: Valor formatado ou default
    """
    if value is None:
        return default
    
    try:
        import math
        if isinstance(value, (int, float)) and math.isnan(value):
            return default
    except (TypeError, ValueError):
        pass
    
    try:
        return f"{value:{format_str}}"
    except (TypeError, ValueError):
        return default


def fetch_asset_detail(ticker, date=None):
    """
    Busca detalhes de um ativo da API.
    
    Args:
        ticker: Símbolo do ativo
        date: Data do score (opcional)
        
    Returns:
        dict: Resposta da API ou None em caso de erro
    """
    try:
        url = f"{API_URL}/api/v1/asset/{ticker}"
        params = {}
        if date:
            params['date'] = date
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 404:
                st.error(f"Ticker '{ticker}' não encontrado.")
            else:
                st.error(f"Erro ao buscar detalhes: {e}")
        else:
            st.error(f"Erro ao conectar com a API: {e}")
        return None


def fetch_price_history(ticker, days=365):
    """
    Busca histórico de preços da API do backend.
    
    Args:
        ticker: Símbolo do ativo
        days: Número de dias de histórico
        
    Returns:
        pd.DataFrame: DataFrame com histórico de preços ou None
    """
    try:
        # Buscar da API do backend
        url = f"{API_URL}/api/v1/prices/{ticker}"
        params = {"days": days}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        data = response.json()
        
        # Converter para DataFrame
        prices = data.get('prices', [])
        if not prices:
            return None
        
        df = pd.DataFrame(prices)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Renomear colunas para match com yfinance format
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
            'adj_close': 'Adj Close'
        }, inplace=True)
        
        return df
        
    except requests.exceptions.RequestException as e:
        # Não mostrar erro, apenas retornar None silenciosamente
        return None
    except Exception as e:
        return None


def plot_price_chart(price_data, ticker):
    """
    Cria gráfico de preços usando Plotly.
    
    Args:
        price_data: DataFrame com histórico de preços
        ticker: Símbolo do ativo
        
    Returns:
        plotly.graph_objects.Figure: Gráfico de preços
    """
    fig = go.Figure()
    
    # Adicionar linha de preço de fechamento
    fig.add_trace(go.Scatter(
        x=price_data.index,
        y=price_data['Close'],
        mode='lines',
        name='Preço de Fechamento',
        line=dict(color='#1f77b4', width=2)
    ))
    
    # Configurar layout
    fig.update_layout(
        title=f"Histórico de Preços - {ticker} (12 meses)",
        xaxis_title="Data",
        yaxis_title="Preço (R$)",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig


# Sidebar com entrada de ticker
st.sidebar.header("Selecionar Ativo")

# Verificar se há ticker no session state (vindo da página de ranking)
default_ticker = st.session_state.get('selected_ticker', '')

ticker_input = st.sidebar.text_input(
    "Digite o ticker",
    value=default_ticker,
    placeholder="Ex: PETR4"
).upper()

# Opção de data
use_latest = st.sidebar.checkbox("Usar data mais recente", value=True)
selected_date = None

if not use_latest:
    selected_date = st.sidebar.date_input(
        "Selecionar data",
        value=datetime.now().date()
    )
    selected_date = selected_date.strftime("%Y-%m-%d")

# Botão para buscar
search_button = st.sidebar.button("🔍 Buscar", use_container_width=True)

# Buscar dados quando houver ticker e botão for clicado (ou ticker no session state)
if ticker_input and (search_button or default_ticker):
    with st.spinner(f"Carregando detalhes de {ticker_input}..."):
        asset_data = fetch_asset_detail(
            ticker_input,
            date=selected_date if not use_latest else None
        )
    
    if asset_data:
        # Extrair informações
        ticker = asset_data['ticker']
        score = asset_data['score']
        explanation = asset_data['explanation']
        raw_factors = asset_data['raw_factors']
        
        # Seção 1: Informações Principais
        st.header(f"{ticker}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Score Final",
                safe_format(score.get('final_score'), ".3f"),
                help="Score final ponderado"
            )
        
        with col2:
            rank = score.get('rank')
            st.metric(
                "Posição no Ranking",
                f"#{rank}" if rank else "N/A",
                help="Posição no ranking diário"
            )
        
        with col3:
            confidence = score.get('confidence')
            st.metric(
                "Confiança",
                safe_format(confidence, ".0%") if confidence is not None else "N/A",
                help="Score de confiança (0-100%)"
            )
        
        with col4:
            st.metric(
                "Data",
                score.get('date', 'N/A'),
                help="Data do score"
            )
        
        st.divider()
        
        # Seção 2: Elegibilidade e Penalidades de Risco
        
        # Verificar elegibilidade
        if not score.get('passed_eligibility', True):
            st.warning("⚠️ Este ativo não passou no filtro de elegibilidade")
            exclusion_reasons = score.get('exclusion_reasons', [])
            if exclusion_reasons:
                st.markdown("**Razões de exclusão:**")
                for reason in exclusion_reasons:
                    st.markdown(f"- {reason}")
            st.divider()
        
        # Mostrar penalidades de risco se houver
        penalty_factor = score.get('penalty_factor', 1.0)
        if penalty_factor < 1.0:
            st.info(f"🛡️ Penalidades de risco aplicadas: {penalty_factor:.1%}")
            risk_penalties = score.get('risk_penalties', {})
            if risk_penalties:
                penalty_cols = st.columns(len(risk_penalties))
                for idx, (penalty_type, penalty_value) in enumerate(risk_penalties.items()):
                    with penalty_cols[idx]:
                        penalty_pct = (1 - penalty_value) * 100
                        if penalty_pct > 0:
                            st.metric(
                                f"{penalty_type.title()}",
                                f"-{penalty_pct:.0f}%",
                                help=f"Penalidade aplicada por {penalty_type}"
                            )
            st.divider()
        
        # Seção 3: Breakdown de Scores
        st.subheader("📊 Breakdown de Scores por Categoria")
        
        # Mostrar base_score se disponível
        base_score = score.get('base_score')
        if base_score is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Score Base",
                    safe_format(base_score, ".3f"),
                    help="Score antes das penalidades de risco"
                )
            with col2:
                final_score = score.get('final_score')
                delta_value = None
                if final_score is not None and base_score is not None:
                    delta_value = final_score - base_score
                st.metric(
                    "Score Final",
                    safe_format(final_score, ".3f"),
                    delta=safe_format(delta_value, ".3f") if delta_value is not None else None,
                    help="Score após aplicação das penalidades de risco"
                )
            st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "🚀 Momentum",
                safe_format(score.get('momentum_score'), ".3f"),
                help="Score de fatores de momentum (retornos, RSI, volatilidade)"
            )
        
        with col2:
            st.metric(
                "⭐ Qualidade",
                safe_format(score.get('quality_score'), ".3f"),
                help="Score de fatores de qualidade (ROE, margens, crescimento)"
            )
        
        with col3:
            st.metric(
                "💰 Valor",
                safe_format(score.get('value_score'), ".3f"),
                help="Score de fatores de valor (P/L, P/VP, EV/EBITDA)"
            )
        
        # Gráfico de barras do breakdown
        momentum_score = score.get('momentum_score', 0) or 0
        quality_score = score.get('quality_score', 0) or 0
        value_score = score.get('value_score', 0) or 0
        
        breakdown_df = pd.DataFrame({
            'Categoria': ['Momentum', 'Qualidade', 'Valor'],
            'Score': [momentum_score, quality_score, value_score]
        })
        
        fig_breakdown = go.Figure(data=[
            go.Bar(
                x=breakdown_df['Categoria'],
                y=breakdown_df['Score'],
                marker_color=['#1f77b4', '#ff7f0e', '#2ca02c'],
                text=breakdown_df['Score'].round(3),
                textposition='auto'
            )
        ])
        
        fig_breakdown.update_layout(
            title="Breakdown de Scores",
            xaxis_title="Categoria",
            yaxis_title="Score",
            template='plotly_white',
            height=300
        )
        
        st.plotly_chart(fig_breakdown, use_container_width=True)
        
        st.divider()
        
        # Seção 4: Explicação Automática
        st.subheader("📝 Análise Automática")
        
        st.markdown(explanation)
        
        st.divider()
        
        # Seção 5: Fatores Brutos
        if raw_factors:
            st.subheader("🔢 Fatores Normalizados")
            
            st.caption(
                "Valores normalizados via z-score cross-sectional. "
                "Valores positivos indicam desempenho acima da média, "
                "valores negativos indicam desempenho abaixo da média."
            )
            
            # Separar fatores por categoria
            momentum_factors = {
                k: v for k, v in raw_factors.items()
                if k in ['return_6m', 'return_12m', 'rsi_14', 'volatility_90d', 'recent_drawdown']
            }
            
            quality_factors = {
                k: v for k, v in raw_factors.items()
                if k in ['roe', 'net_margin', 'revenue_growth_3y', 'debt_to_ebitda']
            }
            
            value_factors = {
                k: v for k, v in raw_factors.items()
                if k in ['pe_ratio', 'ev_ebitda', 'pb_ratio']
            }
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if momentum_factors:
                    st.markdown("**🚀 Momentum**")
                    for factor, value in momentum_factors.items():
                        st.metric(
                            factor.replace('_', ' ').title(),
                            safe_format(value, ".3f")
                        )
            
            with col2:
                if quality_factors:
                    st.markdown("**⭐ Qualidade**")
                    for factor, value in quality_factors.items():
                        st.metric(
                            factor.replace('_', ' ').title(),
                            safe_format(value, ".3f")
                        )
            
            with col3:
                if value_factors:
                    st.markdown("**💰 Valor**")
                    for factor, value in value_factors.items():
                        st.metric(
                            factor.replace('_', ' ').title(),
                            safe_format(value, ".3f")
                        )
        
        st.divider()
        
        # Seção 6: Calculadora de Investimento
        st.subheader("💰 Calculadora de Investimento")
        
        st.markdown("""
        Simule o possível rendimento do seu investimento com base nos retornos históricos da ação.
        
        **⚠️ Aviso:** Esta é apenas uma simulação baseada em dados históricos. 
        Rentabilidade passada não garante rentabilidade futura.
        """)
        
        calc_col1, calc_col2 = st.columns(2)
        
        with calc_col1:
            investment_amount = st.number_input(
                "Valor do Investimento (R$)",
                min_value=100.0,
                max_value=1000000.0,
                value=10000.0,
                step=100.0,
                help="Quanto você pretende investir"
            )
        
        with calc_col2:
            investment_period = st.selectbox(
                "Período de Investimento",
                options=[6, 12, 24, 36],
                format_func=lambda x: f"{x} meses",
                help="Por quanto tempo pretende manter o investimento"
            )
        
        # Buscar retornos históricos do raw_factors
        return_6m = raw_factors.get('return_6m', 0)
        return_12m = raw_factors.get('return_12m', 0)
        
        # Calcular projeções baseadas nos retornos históricos
        if return_6m != 0 or return_12m != 0:
            # Usar o retorno mais apropriado baseado no período
            if investment_period <= 6:
                monthly_return = (return_6m / 6) if return_6m != 0 else 0
                base_return = return_6m
                period_label = "6 meses"
            else:
                monthly_return = (return_12m / 12) if return_12m != 0 else 0
                base_return = return_12m
                period_label = "12 meses"
            
            # Calcular projeção
            projected_return = monthly_return * investment_period
            final_amount = investment_amount * (1 + projected_return)
            profit = final_amount - investment_amount
            
            st.markdown("---")
            st.markdown("### 📊 Projeção de Rendimento")
            
            proj_col1, proj_col2, proj_col3 = st.columns(3)
            
            with proj_col1:
                st.metric(
                    "Valor Final Projetado",
                    f"R$ {final_amount:,.2f}",
                    delta=f"R$ {profit:+,.2f}"
                )
            
            with proj_col2:
                st.metric(
                    "Retorno Projetado",
                    f"{projected_return*100:+.2f}%",
                    help=f"Baseado no retorno histórico de {period_label}"
                )
            
            with proj_col3:
                annual_return = (projected_return / investment_period) * 12
                st.metric(
                    "Retorno Anualizado",
                    f"{annual_return*100:+.2f}%",
                    help="Retorno projetado em base anual"
                )
            
            # Gráfico de evolução do investimento
            months = list(range(investment_period + 1))
            values = [investment_amount * (1 + monthly_return * m) for m in months]
            
            fig_investment = go.Figure()
            
            fig_investment.add_trace(go.Scatter(
                x=months,
                y=values,
                mode='lines+markers',
                name='Valor Projetado',
                line=dict(color='#2ca02c', width=3),
                fill='tonexty'
            ))
            
            fig_investment.add_trace(go.Scatter(
                x=months,
                y=[investment_amount] * len(months),
                mode='lines',
                name='Investimento Inicial',
                line=dict(color='#d62728', width=2, dash='dash')
            ))
            
            fig_investment.update_layout(
                title=f"Evolução do Investimento - {investment_period} meses",
                xaxis_title="Meses",
                yaxis_title="Valor (R$)",
                hovermode='x unified',
                showlegend=True
            )
            
            st.plotly_chart(fig_investment, use_container_width=True)
            
            st.info(f"""
            **Metodologia:** Esta projeção usa o retorno histórico de {period_label} ({base_return*100:+.2f}%) 
            e assume que esse retorno se manterá constante ao longo do período selecionado.
            
            **Importante:** 
            - Rentabilidade passada não garante rentabilidade futura
            - Não considera custos de corretagem, impostos ou dividendos
            - É apenas uma estimativa para fins educacionais
            """)
        else:
            st.warning("Não há dados de retorno histórico suficientes para calcular a projeção.")
        
        st.divider()
        
        # Seção 7: Gráfico de Preços
        st.subheader("📈 Histórico de Preços (12 meses)")
        
        with st.spinner("Carregando histórico de preços..."):
            price_data = fetch_price_history(ticker, days=365)
        
        if price_data is not None and not price_data.empty:
            fig_price = plot_price_chart(price_data, ticker)
            st.plotly_chart(fig_price, use_container_width=True)
            
            # Estatísticas de preço
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                current_price = price_data['Close'].iloc[-1]
                st.metric("Preço Atual", f"R$ {current_price:.2f}")
            
            with col2:
                price_change = (
                    (price_data['Close'].iloc[-1] - price_data['Close'].iloc[0])
                    / price_data['Close'].iloc[0] * 100
                )
                st.metric(
                    "Variação 12M",
                    f"{price_change:+.2f}%",
                    delta=f"{price_change:.2f}%"
                )
            
            with col3:
                max_price = price_data['Close'].max()
                st.metric("Máxima 12M", f"R$ {max_price:.2f}")
            
            with col4:
                min_price = price_data['Close'].min()
                st.metric("Mínima 12M", f"R$ {min_price:.2f}")
        else:
            st.warning(
                "Não foi possível carregar o histórico de preços. "
                "Verifique se o ticker está correto e se o yfinance está instalado."
            )
        
        # Limpar session state após uso
        if 'selected_ticker' in st.session_state:
            del st.session_state['selected_ticker']

else:
    # Instruções quando não há ticker selecionado
    st.info("👈 Digite um ticker na barra lateral para ver os detalhes do ativo.")
    
    st.markdown("""
    ### Como usar esta página:
    
    1. Digite o ticker do ativo na barra lateral (ex: PETR4, VALE3, ITUB4)
    2. Clique em "Buscar" para carregar os detalhes
    3. Visualize:
       - Score final e posição no ranking
       - Breakdown de scores por categoria
       - Análise automática em português
       - Fatores normalizados detalhados
       - Gráfico de preços dos últimos 12 meses
    
    **Dica:** Você também pode navegar para esta página clicando em um ativo na página de Ranking.
    """)
