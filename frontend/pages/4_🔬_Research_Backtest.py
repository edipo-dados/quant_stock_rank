"""
Página de Research - Backtest Engine

Permite rodar backtests com interface gráfica e visualizar resultados.
Integrada à aplicação principal do Streamlit.
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
    page_title="Research - Backtest Engine",
    page_icon="🔬",
    layout="wide"
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
    """Valida inputs do usuário."""
    if start_date >= end_date:
        return False, "❌ Data inicial deve ser menor que data final"
    
    min_date = start_date + relativedelta(months=3)
    if end_date < min_date:
        return False, "❌ Período mínimo de 3 meses necessário"
    
    db = SessionLocal()
    try:
        count = db.query(ScoreDaily).filter(
            ScoreDaily.date >= start_date,
            ScoreDaily.date <= end_date
        ).count()
        
        if count == 0:
            return False, f"❌ Sem dados de scores para o período {start_date} a {end_date}"
    finally:
        db.close()
    
    return True, ""


def run_backtest_ui(name, start_date, end_date, top_n, initial_capital,
                    transaction_cost, use_smoothing, alpha_smoothing):
    """Executa backtest via UI usando BacktestEngine real."""
    db = SessionLocal()
    
    try:
        with st.spinner('🔄 Executando backtest...'):
            service = BacktestService(db)
            
            # Criar run
            run = service.create_backtest_run(
                name=name if name else None,
                start_date=start_date,
                end_date=end_date,
                rebalance_frequency="monthly",
                top_n=top_n,
                transaction_cost=transaction_cost / 100.0,
                initial_capital=initial_capital,
                notes=f"Smoothing: {use_smoothing}, Alpha: {alpha_smoothing if use_smoothing else 'N/A'}"
            )
            
            logger.info(f"Created backtest run: {run.id}")
            
            # Executar backtest real usando BacktestEngine
            engine = BacktestEngine(
                start_date=start_date,
                end_date=end_date,
                top_n=top_n,
                rebalance_frequency='monthly',
                weight_method='equal',
                use_smoothing=use_smoothing,
                risk_free_rate=0.0
            )
            
            # Rodar backtest
            result = engine.run_backtest(db)
            
            # Converter resultados para formato do repository
            # Calcular NAV diário a partir dos retornos mensais
            nav_records = []
            nav = initial_capital
            monthly_returns = result['monthly_returns']
            rebalance_dates = engine.get_monthly_dates()[:-1]  # Excluir última data
            
            for i, monthly_return in enumerate(monthly_returns):
                if i < len(rebalance_dates):
                    rebalance_date = rebalance_dates[i]
                    # Calcular NAV após o retorno mensal
                    nav = nav * (1 + monthly_return)
                    
                    nav_records.append({
                        'date': rebalance_date,
                        'nav': nav,
                        'benchmark_nav': None,
                        'daily_return': monthly_return,
                        'benchmark_return': None
                    })
            
            # Converter posições
            positions = []
            portfolio_history = result['portfolio_history']
            portfolio_scores = result.get('portfolio_scores', [])
            
            for i, weights in enumerate(portfolio_history):
                if i < len(rebalance_dates):
                    rebalance_date = rebalance_dates[i]
                    scores = portfolio_scores[i] if i < len(portfolio_scores) else {}
                    
                    for ticker, weight in weights.items():
                        positions.append({
                            'date': rebalance_date,
                            'ticker': ticker,
                            'weight': weight,
                            'score_at_selection': scores.get(ticker)
                        })
            
            # Preparar métricas
            metrics_data = result['metrics']
            metrics = {
                'total_return': metrics_data['total_return'] / 100.0,  # Converter de % para decimal
                'cagr': metrics_data['cagr'] / 100.0,
                'volatility': metrics_data['volatility'] / 100.0,
                'sharpe_ratio': metrics_data['sharpe_ratio'],
                'sortino_ratio': 0.0,  # Não calculado ainda
                'max_drawdown': metrics_data['max_drawdown'] / 100.0,
                'turnover_avg': metrics_data['avg_turnover'] / 100.0,
                'alpha': None,
                'beta': None,
                'information_ratio': None
            }
            
            # Salvar resultados
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
        st.error(traceback.format_exc())
        return None
        
    finally:
        db.close()


def display_metrics(metrics):
    """Exibe métricas em formato de cards."""
    if not metrics:
        st.warning("Sem métricas disponíveis")
        return
    
    st.subheader("📊 Métricas de Performance")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Return", f"{metrics.total_return:.2%}")
    with col2:
        st.metric("CAGR", f"{metrics.cagr:.2%}")
    with col3:
        st.metric("Volatilidade", f"{metrics.volatility:.2%}")
    with col4:
        st.metric("Max Drawdown", f"{metrics.max_drawdown:.2%}", delta_color="inverse")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Sharpe Ratio", f"{metrics.sharpe_ratio:.2f}")
    with col2:
        st.metric("Sortino Ratio", f"{metrics.sortino_ratio:.2f}")
    with col3:
        st.metric("Turnover Médio", f"{metrics.turnover_avg:.2%}")
    with col4:
        if metrics.alpha is not None:
            st.metric("Alpha", f"{metrics.alpha:.2%}")


def display_equity_curve(run_id):
    """Exibe equity curve usando Plotly."""
    db = SessionLocal()
    
    try:
        service = BacktestService(db)
        equity_curve = service.get_equity_curve(run_id)
        
        if not equity_curve:
            st.warning("Sem dados de equity curve disponíveis")
            return
        
        st.subheader("📈 Equity Curve")
        
        df = pd.DataFrame(equity_curve)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['nav'],
            mode='lines',
            name='Portfolio NAV',
            line=dict(color='#0066cc', width=2)
        ))
        
        if 'benchmark_nav' in df.columns and df['benchmark_nav'].notna().any():
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['benchmark_nav'],
                mode='lines',
                name='Benchmark NAV',
                line=dict(color='#ff6600', width=2, dash='dash')
            ))
        
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
    """Exibe tabela de posições do último rebalance."""
    db = SessionLocal()
    
    try:
        service = BacktestService(db)
        from app.backtest.repository import BacktestRepository
        repo = BacktestRepository(db)
        rebalance_dates = repo.get_rebalance_dates(run_id)
        
        if not rebalance_dates:
            st.warning("Sem posições disponíveis")
            return
        
        last_rebalance = rebalance_dates[-1]
        positions = service.get_portfolio_composition(run_id, last_rebalance)
        
        if not positions:
            st.warning("Sem posições disponíveis")
            return
        
        st.subheader(f"💼 Posições do Último Rebalance ({last_rebalance})")
        
        df = pd.DataFrame(positions)
        df = df[df['date'] == last_rebalance]
        df = df.sort_values('weight', ascending=False)
        
        df['weight'] = df['weight'].apply(lambda x: f"{x:.2%}")
        df['score_at_selection'] = df['score_at_selection'].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "N/A")
        
        df = df.rename(columns={
            'ticker': 'Ticker',
            'weight': 'Peso',
            'score_at_selection': 'Score'
        })
        
        st.dataframe(
            df[['Ticker', 'Peso', 'Score']],
            use_container_width=True,
            hide_index=True
        )
        
    finally:
        db.close()


def display_history():
    """Exibe histórico de execuções de backtest."""
    db = SessionLocal()
    
    try:
        service = BacktestService(db)
        runs = service.list_backtests(limit=50)
        
        if not runs:
            st.info("Nenhum backtest executado ainda")
            return
        
        st.subheader("📚 Histórico de Execuções")
        
        data = []
        for run in runs:
            metrics = service.repository.get_metrics(run.id)
            
            data.append({
                'Run ID': run.id[:8] + '...',
                'Nome': run.name or 'Sem nome',
                'Período': f"{run.start_date} a {run.end_date}",
                'Top N': run.top_n,
                'Sharpe': f"{metrics.sharpe_ratio:.2f}" if metrics else "N/A",
                'CAGR': f"{metrics.cagr:.2%}" if metrics else "N/A",
                'Data': run.created_at.strftime('%Y-%m-%d %H:%M'),
                'run_id_full': run.id
            })
        
        df = pd.DataFrame(data)
        
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
    """Função principal da página."""
    st.title("🔬 Research - Backtest Engine")
    st.markdown("Plataforma de research quantitativo para testar estratégias e comparar versões de modelo")
    st.markdown("---")
    
    # Sidebar - Parâmetros
    with st.sidebar:
        st.header("⚙️ Parâmetros do Backtest")
        
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
        
        st.subheader("📝 Identificação")
        test_name = st.text_input(
            "Nome do Teste (opcional)",
            placeholder="Ex: momentum_v1"
        )
        
        st.markdown("---")
        
        run_button = st.button("🚀 Rodar Backtest", type="primary")
        
        # Seção de Gerenciamento
        st.markdown("---")
        st.subheader("🗑️ Gerenciamento")
        
        with st.expander("Limpar Backtests"):
            st.caption("Remove backtests antigos ou com erro")
            
            # Listar backtests existentes
            db = SessionLocal()
            try:
                from app.backtest.models import BacktestRun
                runs = db.query(BacktestRun).order_by(BacktestRun.created_at.desc()).limit(10).all()
                
                if runs:
                    st.write(f"**{len(runs)} backtest(s) recente(s):**")
                    
                    for run in runs:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            name_display = run.name or f"Run {run.id[:8]}"
                            st.text(f"• {name_display}")
                            st.caption(f"  {run.start_date} a {run.end_date}")
                        with col2:
                            if st.button("🗑️", key=f"del_{run.id}", help="Deletar"):
                                try:
                                    db.delete(run)
                                    db.commit()
                                    st.success("✓ Deletado")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro: {e}")
                    
                    st.markdown("---")
                    if st.button("🗑️ Limpar Todos", type="secondary"):
                        try:
                            db.query(BacktestRun).delete()
                            db.commit()
                            st.success("✓ Todos os backtests foram removidos")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
                else:
                    st.info("Nenhum backtest encontrado")
            finally:
                db.close()
    
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
    
    # Exibir resultados
    if 'selected_run_id' in st.session_state:
        run_id = st.session_state['selected_run_id']
        
        db = SessionLocal()
        try:
            service = BacktestService(db)
            summary = service.get_backtest_summary(run_id)
            
            if summary:
                st.markdown("---")
                st.header("📊 Resultados do Backtest")
                
                run = summary['run']
                st.info(f"**Run:** {run.name or run.id[:8]} | **Período:** {run.start_date} a {run.end_date} | **Top N:** {run.top_n}")
                
                display_metrics(summary['metrics'])
                st.markdown("---")
                display_equity_curve(run_id)
                st.markdown("---")
                display_positions(run_id)
                
        finally:
            db.close()
    
    # Histórico
    st.markdown("---")
    display_history()


if __name__ == "__main__":
    main()
else:
    main()
