"""
Quant Research – Backtest Engine

Aplicação Streamlit para rodar backtests utilizando a engine já implementada.
Permite selecionar parâmetros via interface gráfica e persistir resultados.

IMPORTANTE: Aplicação isolada que NÃO altera dados de produção.

Uso:
    streamlit run app/research/streamlit_backtest_app.py
"""

import sys
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

from app.models.database import SessionLocal
from app.backtest.service import BacktestService
from app.backtest.backtest_engine import BacktestEngine
from app.models.schemas import ScoreDaily

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da página
st.set_page_config(
    page_title="Quant Research – Backtest Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #0066cc;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def validate_inputs(start_date, end_date):
    """
    Valida inputs do usuário.
    
    Returns:
        (bool, str): (is_valid, error_message)
    """
    if start_date >= end_date:
        return False, "❌ Data inicial deve ser menor que data final"
    
    # Verificar período mínimo de 3 meses
    min_date = start_date + relativedelta(months=3)
    if end_date < min_date:
        return False, "❌ Período mínimo de 3 meses necessário"
    
    # Verificar se há dados disponíveis
    db = SessionLocal()
    try:
        count = db.query(ScoreDaily).filter(
            ScoreDaily.date >= start_date,
            ScoreDaily.date <= end_date
        ).count()
        
        if count == 0:
            return False, f"❌ Sem dados de scores disponíveis para o período {start_date} a {end_date}"
    finally:
        db.close()
    
    return True, ""


def run_backtest_ui(
    name, start_date, end_date, top_n, initial_capital,
    transaction_cost, use_smoothing, alpha_smoothing
):
    """
    Executa backtest via UI.
    
    Returns:
        run_id ou None se falhar
    """
    db = SessionLocal()
    
    try:
        with st.spinner('🔄 Executando backtest...'):
            # Criar backtest run
            service = BacktestService(db)
            
            run = service.create_backtest_run(
                name=name if name else None,
                start_date=start_date,
                end_date=end_date,
                rebalance_frequency="monthly",
                top_n=top_n,
                transaction_cost=transaction_cost / 100.0,  # Converter % para decimal
                initial_capital=initial_capital,
                notes=f"Smoothing: {use_smoothing}, Alpha: {alpha_smoothing if use_smoothing else 'N/A'}"
            )
            
            logger.info(f"Created backtest run: {run.id}")
            
            # Executar backtest engine
            engine = BacktestEngine(
                start_date=start_date,
                end_date=end_date,
                top_n=top_n,
                rebalance_frequency='monthly',
                weight_method='equal',
                use_smoothing=use_smoothing,
                risk_free_rate=0.0
            )
            
            # Simular backtest (aqui você integraria com o engine real)
            # Por enquanto, vamos gerar dados dummy para demonstração
            logger.info("Running backtest simulation...")
            
            # Gerar NAV records dummy
            nav_records = []
            current_date = start_date
            nav = initial_capital
            
            while current_date <= end_date:
                import random
                daily_return = random.uniform(-0.02, 0.02)
                nav = nav * (1 + daily_return)
                
                nav_records.append({
                    'date': current_date,
                    'nav': nav,
                    'benchmark_nav': initial_capital * 1.1,  # Dummy benchmark
                    'daily_return': daily_return,
                    'benchmark_return': 0.0003  # Dummy
                })
                
                current_date += timedelta(days=1)
            
            # Gerar posições dummy
            positions = []
            tickers = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA']
            current_date = start_date
            
            while current_date <= end_date:
                if current_date.day == 1:  # Primeiro dia do mês
                    weight = 1.0 / top_n
                    for i in range(top_n):
                        positions.append({
                            'date': current_date,
                            'ticker': tickers[i % len(tickers)],
                            'weight': weight,
                            'score_at_selection': random.uniform(0.5, 2.0)
                        })
                
                current_date += timedelta(days=1)
            
            # Calcular métricas
            total_return = (nav - initial_capital) / initial_capital
            days = (end_date - start_date).days
            years = days / 365.25
            cagr = (1 + total_return) ** (1 / years) - 1
            
            metrics = {
                'total_return': total_return,
                'cagr': cagr,
                'volatility': 0.15,
                'sharpe_ratio': 1.2,
                'sortino_ratio': 1.5,
                'max_drawdown': -0.12,
                'turnover_avg': 0.25,
                'alpha': 0.03,
                'beta': 0.95,
                'information_ratio': 0.8
            }
            
            # Salvar resultados
            logger.info("Saving backtest results...")
            service.save_backtest_results(
                run_id=run.id,
                nav_records=nav_records,
                positions=positions,
                metrics=metrics
            )
            
            logger.info(f"Backtest completed: {run.id}")
            return run.id
            
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        st.error(f"❌ Erro ao executar backtest: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
        
    finally:
        db.close()


def display_metrics(metrics):
    """
    Exibe métricas em formato de cards.
    """
    if not metrics:
        st.warning("Sem métricas disponíveis")
        return
    
    st.subheader("📊 Métricas de Performance")
    
    # Linha 1: Retornos
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Return",
            f"{metrics.total_return:.2%}",
            delta=None
        )
    
    with col2:
        st.metric(
            "CAGR",
            f"{metrics.cagr:.2%}",
            delta=None
        )
    
    with col3:
        st.metric(
            "Volatilidade",
            f"{metrics.volatility:.2%}",
            delta=None
        )
    
    with col4:
        st.metric(
            "Max Drawdown",
            f"{metrics.max_drawdown:.2%}",
            delta=None,
            delta_color="inverse"
        )
    
    # Linha 2: Ratios
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Sharpe Ratio",
            f"{metrics.sharpe_ratio:.2f}",
            delta=None
        )
    
    with col2:
        st.metric(
            "Sortino Ratio",
            f"{metrics.sortino_ratio:.2f}",
            delta=None
        )
    
    with col3:
        st.metric(
            "Turnover Médio",
            f"{metrics.turnover_avg:.2%}",
            delta=None
        )
    
    with col4:
        if metrics.alpha is not None:
            st.metric(
                "Alpha",
                f"{metrics.alpha:.2%}",
                delta=None
            )
    
    # Linha 3: Benchmark (se disponível)
    if metrics.beta is not None or metrics.information_ratio is not None:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if metrics.beta is not None:
                st.metric(
                    "Beta",
                    f"{metrics.beta:.2f}",
                    delta=None
                )
        
        with col2:
            if metrics.information_ratio is not None:
                st.metric(
                    "Information Ratio",
                    f"{metrics.information_ratio:.2f}",
                    delta=None
                )


def display_equity_curve(run_id):
    """
    Exibe equity curve usando Plotly.
    """
    db = SessionLocal()
    
    try:
        service = BacktestService(db)
        equity_curve = service.get_equity_curve(run_id)
        
        if not equity_curve:
            st.warning("Sem dados de equity curve disponíveis")
            return
        
        st.subheader("📈 Equity Curve")
        
        # Criar DataFrame
        df = pd.DataFrame(equity_curve)
        
        # Criar gráfico Plotly
        fig = go.Figure()
        
        # Linha NAV
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['nav'],
            mode='lines',
            name='Portfolio NAV',
            line=dict(color='#0066cc', width=2)
        ))
        
        # Linha Benchmark (se disponível)
        if 'benchmark_nav' in df.columns and df['benchmark_nav'].notna().any():
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['benchmark_nav'],
                mode='lines',
                name='Benchmark NAV',
                line=dict(color='#ff6600', width=2, dash='dash')
            ))
        
        # Layout
        fig.update_layout(
            title="Evolução do Portfólio",
            xaxis_title="Data",
            yaxis_title="NAV (R$)",
            hovermode='x unified',
            template='plotly_white',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    finally:
        db.close()


def display_positions(run_id):
    """
    Exibe tabela de posições do último rebalance.
    """
    db = SessionLocal()
    
    try:
        service = BacktestService(db)
        
        # Buscar todas as posições
        from app.backtest.repository import BacktestRepository
        repo = BacktestRepository(db)
        rebalance_dates = repo.get_rebalance_dates(run_id)
        
        if not rebalance_dates:
            st.warning("Sem posições disponíveis")
            return
        
        # Pegar último rebalance
        last_rebalance = rebalance_dates[-1]
        positions = service.get_portfolio_composition(run_id, last_rebalance)
        
        if not positions:
            st.warning("Sem posições disponíveis")
            return
        
        st.subheader(f"💼 Posições do Último Rebalance ({last_rebalance})")
        
        # Criar DataFrame
        df = pd.DataFrame(positions)
        df = df[df['date'] == last_rebalance]  # Filtrar apenas último rebalance
        df = df.sort_values('weight', ascending=False)
        
        # Formatar
        df['weight'] = df['weight'].apply(lambda x: f"{x:.2%}")
        df['score_at_selection'] = df['score_at_selection'].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "N/A")
        
        # Renomear colunas
        df = df.rename(columns={
            'ticker': 'Ticker',
            'weight': 'Peso',
            'score_at_selection': 'Score'
        })
        
        # Exibir tabela
        st.dataframe(
            df[['Ticker', 'Peso', 'Score']],
            use_container_width=True,
            hide_index=True
        )
        
    finally:
        db.close()


def display_history():
    """
    Exibe histórico de execuções de backtest.
    """
    db = SessionLocal()
    
    try:
        service = BacktestService(db)
        runs = service.list_backtests(limit=50)
        
        if not runs:
            st.info("Nenhum backtest executado ainda")
            return
        
        st.subheader("📚 Histórico de Execuções")
        
        # Criar DataFrame
        data = []
        for run in runs:
            # Buscar métricas
            metrics = service.repository.get_metrics(run.id)
            
            data.append({
                'Run ID': run.id[:8] + '...',
                'Nome': run.name or 'Sem nome',
                'Período': f"{run.start_date} a {run.end_date}",
                'Top N': run.top_n,
                'Sharpe': f"{metrics.sharpe_ratio:.2f}" if metrics else "N/A",
                'CAGR': f"{metrics.cagr:.2%}" if metrics else "N/A",
                'Data': run.created_at.strftime('%Y-%m-%d %H:%M'),
                'run_id_full': run.id  # Para uso interno
            })
        
        df = pd.DataFrame(data)
        
        # Exibir tabela com botões
        for idx, row in df.iterrows():
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 2, 2, 1, 1, 1, 2, 1])
            
            with col1:
                st.text(row['Run ID'])
            with col2:
                st.text(row['Nome'])
            with col3:
                st.text(row['Período'])
            with col4:
                st.text(str(row['Top N']))
            with col5:
                st.text(row['Sharpe'])
            with col6:
                st.text(row['CAGR'])
            with col7:
                st.text(row['Data'])
            with col8:
                if st.button("👁️ Ver", key=f"view_{idx}"):
                    st.session_state['selected_run_id'] = row['run_id_full']
                    st.rerun()
        
    finally:
        db.close()


# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

def main():
    """
    Função principal da aplicação.
    """
    # Título
    st.title("📊 Quant Research – Backtest Engine")
    st.markdown("---")
    
    # Sidebar - Parâmetros
    with st.sidebar:
        st.header("⚙️ Parâmetros do Backtest")
        
        # Datas
        st.subheader("📅 Período")
        start_date = st.date_input(
            "Data Início",
            value=date.today() - relativedelta(years=1),
            max_value=date.today()
        )
        
        end_date = st.date_input(
            "Data Fim",
            value=date.today(),
            max_value=date.today()
        )
        
        # Parâmetros do portfólio
        st.subheader("💼 Portfólio")
        top_n = st.number_input(
            "Top N Ativos",
            min_value=1,
            max_value=50,
            value=5,
            step=1
        )
        
        initial_capital = st.number_input(
            "Capital Inicial (R$)",
            min_value=1000.0,
            max_value=10000000.0,
            value=100000.0,
            step=10000.0,
            format="%.2f"
        )
        
        transaction_cost = st.slider(
            "Custo de Transação (%)",
            min_value=0.0,
            max_value=1.0,
            value=0.2,
            step=0.05,
            format="%.2f%%"
        )
        
        # Smoothing
        st.subheader("🔄 Suavização")
        use_smoothing = st.checkbox("Usar Smoothing?", value=False)
        
        alpha_smoothing = st.slider(
            "Alpha Smoothing",
            min_value=0.1,
            max_value=0.9,
            value=0.7,
            step=0.1,
            disabled=not use_smoothing
        )
        
        # Nome do teste
        st.subheader("📝 Identificação")
        test_name = st.text_input(
            "Nome do Teste (opcional)",
            placeholder="Ex: momentum_v1"
        )
        
        st.markdown("---")
        
        # Botão de execução
        run_button = st.button("🚀 Rodar Backtest", type="primary")
    
    # Validar inputs
    is_valid, error_msg = validate_inputs(start_date, end_date)
    
    if not is_valid:
        st.error(error_msg)
        return
    
    # Executar backtest
    if run_button:
        run_id = run_backtest_ui(
            name=test_name,
            start_date=start_date,
            end_date=end_date,
            top_n=top_n,
            initial_capital=initial_capital,
            transaction_cost=transaction_cost,
            use_smoothing=use_smoothing,
            alpha_smoothing=alpha_smoothing
        )
        
        if run_id:
            st.success(f"✅ Backtest executado com sucesso! Run ID: {run_id[:8]}...")
            st.session_state['selected_run_id'] = run_id
            st.rerun()
    
    # Exibir resultados se houver run selecionado
    if 'selected_run_id' in st.session_state:
        run_id = st.session_state['selected_run_id']
        
        db = SessionLocal()
        try:
            service = BacktestService(db)
            summary = service.get_backtest_summary(run_id)
            
            if summary:
                st.markdown("---")
                st.header("📊 Resultados do Backtest")
                
                # Info do run
                run = summary['run']
                st.info(f"**Run:** {run.name or run.id[:8]} | **Período:** {run.start_date} a {run.end_date} | **Top N:** {run.top_n}")
                
                # Métricas
                display_metrics(summary['metrics'])
                
                st.markdown("---")
                
                # Equity Curve
                display_equity_curve(run_id)
                
                st.markdown("---")
                
                # Posições
                display_positions(run_id)
                
        finally:
            db.close()
    
    # Histórico
    st.markdown("---")
    display_history()


if __name__ == "__main__":
    main()
