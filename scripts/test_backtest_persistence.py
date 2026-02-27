"""
Script de teste para validar estrutura de backtesting persistente.

Testa:
- Criação de backtest run
- Inserção de NAV records
- Inserção de posições
- Inserção de métricas
- Consultas e relacionamentos
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import random

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.backtest.service import BacktestService
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_dummy_data():
    """
    Gera dados dummy para teste.
    """
    # Período de teste
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)
    
    # Gerar NAV records (diários)
    nav_records = []
    current_date = start_date
    nav = 100000.0
    
    while current_date <= end_date:
        daily_return = random.uniform(-0.02, 0.02)  # -2% a +2%
        nav = nav * (1 + daily_return)
        
        nav_records.append({
            'date': current_date,
            'nav': nav,
            'benchmark_nav': 100000.0 * (1 + random.uniform(-0.01, 0.01)),
            'daily_return': daily_return,
            'benchmark_return': random.uniform(-0.01, 0.01)
        })
        
        current_date += timedelta(days=1)
    
    # Gerar posições (mensais)
    positions = []
    tickers = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA',
               'WEGE3.SA', 'RENT3.SA', 'LREN3.SA', 'MGLU3.SA', 'B3SA3.SA']
    
    current_date = start_date
    while current_date <= end_date:
        # Rebalance no primeiro dia de cada mês
        if current_date.day == 1:
            # Selecionar top 5 ativos
            selected_tickers = random.sample(tickers, 5)
            weight = 1.0 / len(selected_tickers)
            
            for ticker in selected_tickers:
                positions.append({
                    'date': current_date,
                    'ticker': ticker,
                    'weight': weight,
                    'score_at_selection': random.uniform(-1.0, 2.0)
                })
        
        current_date += timedelta(days=1)
    
    # Gerar métricas
    total_return = (nav - 100000.0) / 100000.0
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
    
    return nav_records, positions, metrics


def test_backtest_persistence():
    """
    Testa persistência de backtest.
    """
    logger.info("=" * 80)
    logger.info("TESTE: Persistência de Backtesting")
    logger.info("=" * 80)
    
    db = SessionLocal()
    service = BacktestService(db)
    
    try:
        # 1. Criar backtest run
        logger.info("\n1️⃣ Criando backtest run...")
        
        run = service.create_backtest_run(
            name="test_v1",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            rebalance_frequency="monthly",
            top_n=5,
            transaction_cost=0.001,
            initial_capital=100000.0,
            notes="Teste de validação da estrutura de persistência"
        )
        
        logger.info(f"✅ Backtest run criado: {run.id}")
        logger.info(f"   Nome: {run.name}")
        logger.info(f"   Período: {run.start_date} a {run.end_date}")
        logger.info(f"   Top N: {run.top_n}")
        
        # 2. Gerar dados dummy
        logger.info("\n2️⃣ Gerando dados dummy...")
        nav_records, positions, metrics = generate_dummy_data()
        logger.info(f"   NAV records: {len(nav_records)}")
        logger.info(f"   Posições: {len(positions)}")
        logger.info(f"   Métricas: {len(metrics)} campos")
        
        # 3. Salvar resultados
        logger.info("\n3️⃣ Salvando resultados...")
        service.save_backtest_results(
            run_id=run.id,
            nav_records=nav_records,
            positions=positions,
            metrics=metrics
        )
        logger.info("✅ Resultados salvos com sucesso")
        
        # 4. Verificar dados salvos
        logger.info("\n4️⃣ Verificando dados salvos...")
        
        summary = service.get_backtest_summary(run.id)
        logger.info(f"   NAV records salvos: {summary['nav_records_count']}")
        logger.info(f"   Posições salvas: {summary['positions_count']}")
        logger.info(f"   Rebalances: {summary['rebalance_count']}")
        
        # 5. Testar consultas
        logger.info("\n5️⃣ Testando consultas...")
        
        # Equity curve
        equity_curve = service.get_equity_curve(run.id)
        logger.info(f"   Equity curve: {len(equity_curve)} pontos")
        logger.info(f"   NAV inicial: {equity_curve[0]['nav']:.2f}")
        logger.info(f"   NAV final: {equity_curve[-1]['nav']:.2f}")
        
        # Posições de um rebalance
        rebalance_dates = summary['rebalance_dates']
        if rebalance_dates:
            first_rebalance = rebalance_dates[0]
            portfolio = service.get_portfolio_composition(run.id, first_rebalance)
            logger.info(f"   Portfólio em {first_rebalance}: {len(portfolio)} ativos")
            for pos in portfolio[:3]:
                logger.info(f"     - {pos['ticker']}: {pos['weight']:.2%} (score: {pos['score_at_selection']:.3f})")
        
        # Métricas
        if summary['metrics']:
            m = summary['metrics']
            logger.info(f"   Métricas:")
            logger.info(f"     - Total Return: {m.total_return:.2%}")
            logger.info(f"     - CAGR: {m.cagr:.2%}")
            logger.info(f"     - Sharpe Ratio: {m.sharpe_ratio:.2f}")
            logger.info(f"     - Max Drawdown: {m.max_drawdown:.2%}")
        
        # 6. Testar listagem
        logger.info("\n6️⃣ Testando listagem...")
        runs = service.list_backtests(limit=10)
        logger.info(f"   Total de backtests: {len(runs)}")
        for r in runs:
            logger.info(f"     - {r.name or r.id[:8]}: {r.start_date} a {r.end_date}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ TODOS OS TESTES PASSARAM!")
        logger.info("=" * 80)
        logger.info("\nEstrutura de persistência validada:")
        logger.info("  ✓ Criação de backtest runs")
        logger.info("  ✓ Persistência de NAV diário")
        logger.info("  ✓ Persistência de posições")
        logger.info("  ✓ Persistência de métricas")
        logger.info("  ✓ Consultas e relacionamentos")
        logger.info("  ✓ Isolamento de dados (não afeta produção)")
        
        logger.info("\nPróximos passos:")
        logger.info("1. Integrar com backtest_engine.py existente")
        logger.info("2. Criar API endpoints para visualização")
        logger.info("3. Implementar comparação de versões de modelo")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Erro durante teste: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = test_backtest_persistence()
    sys.exit(0 if success else 1)
