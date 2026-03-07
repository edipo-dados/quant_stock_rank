"""
Script para rodar backtest com configurações otimizadas.

Melhorias implementadas:
1. Score-weighted portfolio (em vez de equal weight)
2. Market regime filter ativado (IBOV MA200)
3. Temporal smoothing dos scores
4. Pesos multifator otimizados (momentum=0.5, value=0.25, quality=0.15, risk=0.10)
5. Filtro de liquidez aumentado (volume > 5M)
6. Rebalanceamento mensal
7. Limite máximo por ativo de 25%
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.backtest.backtest_engine import BacktestEngine
from app.backtest.service import BacktestService
from datetime import date
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def run_optimized_backtest():
    """Executa backtest com configurações otimizadas"""
    
    print("\n" + "="*80)
    print("BACKTEST OTIMIZADO - ESTRATÉGIA QUANTITATIVA")
    print("="*80)
    
    print("\nConfigurações:")
    print("  - Portfolio Weighting: Score-weighted (max 25% por ativo)")
    print("  - Market Regime Filter: Ativado (IBOV MA200)")
    print("  - Temporal Smoothing: Ativado (0.7 atual + 0.3 anterior)")
    print("  - Pesos Multifator: Momentum=0.5, Value=0.25, Quality=0.15, Risk=0.10")
    print("  - Filtro Liquidez: Volume > 5M, Market Cap > 1B")
    print("  - Rebalanceamento: Mensal")
    print("  - Top N: 10 ações")
    print("  - Benchmark: IBOVESPA (^BVSP)")
    
    # Conectar ao banco
    db = SessionLocal()
    
    try:
        # Verificar se há dados no banco
        from app.models.schemas import RankingHistory, RawPriceDaily
        
        print("\n" + "-"*80)
        print("VERIFICANDO DADOS DISPONÍVEIS...")
        print("-"*80)
        
        # Verificar ranking history
        ranking_count = db.query(RankingHistory).count()
        print(f"  Ranking snapshots: {ranking_count}")
        
        if ranking_count == 0:
            print("\n❌ ERRO: Nenhum ranking snapshot encontrado!")
            print("\nVocê precisa executar o pipeline primeiro:")
            print("  docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py")
            print("\nOu gerar snapshots históricos:")
            print("  docker exec -it quant-ranker-backend python scripts/generate_historical_scores.py")
            return
        
        # Verificar datas disponíveis
        first_ranking = db.query(RankingHistory).order_by(RankingHistory.date).first()
        last_ranking = db.query(RankingHistory).order_by(RankingHistory.date.desc()).first()
        
        if first_ranking and last_ranking:
            print(f"  Primeira data: {first_ranking.date}")
            print(f"  Última data: {last_ranking.date}")
        
        # Verificar preços
        price_count = db.query(RawPriceDaily).count()
        print(f"  Preços disponíveis: {price_count}")
        
        if price_count == 0:
            print("\n❌ ERRO: Nenhum preço encontrado!")
            print("\nExecute o pipeline de ingestão:")
            print("  docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py")
            return
        
        # Configurar backtest engine
        engine = BacktestEngine(
            start_date=date(2020, 1, 1),  # 5 anos de backtest
            end_date=date(2024, 12, 31),
            top_n=10,
            rebalance_frequency='monthly',
            weight_method='score',  # Score-weighted
            use_market_regime=True,  # Ativar filtro de regime
            use_smoothing=True,  # Ativar smoothing temporal
            benchmark_symbol='^BVSP'
        )
        
        print("\n" + "-"*80)
        print("EXECUTANDO BACKTEST...")
        print("-"*80 + "\n")
        
        # Executar backtest
        results = engine.run_backtest(db)
        
        # Exibir resultados
        print("\n" + "="*80)
        print("RESULTADOS DO BACKTEST")
        print("="*80 + "\n")
        
        metrics = results.get('metrics', {})
        
        # Verificar se há resultados válidos
        if metrics.get('total_return', 0) == 0 and metrics.get('cagr', 0) == 0:
            print("⚠ AVISO: Backtest retornou métricas zeradas!")
            print("\nPossíveis causas:")
            print("  1. Período sem dados suficientes")
            print("  2. Nenhum ativo passou nos filtros de elegibilidade")
            print("  3. Snapshots não foram criados corretamente")
            print("\nVerifique os logs acima para mais detalhes.")
            return
        
        print("Performance Metrics:")
        print(f"  Total Return:        {metrics.get('total_return', 0)*100:>8.2f}%")
        print(f"  CAGR:                {metrics.get('cagr', 0)*100:>8.2f}%")
        print(f"  Volatility:          {metrics.get('volatility', 0)*100:>8.2f}%")
        print(f"  Max Drawdown:        {metrics.get('max_drawdown', 0)*100:>8.2f}%")
        
        print("\nRisk-Adjusted Metrics:")
        print(f"  Sharpe Ratio:        {metrics.get('sharpe_ratio', 0):>8.2f}")
        print(f"  Sortino Ratio:       {metrics.get('sortino_ratio', 0):>8.2f}")
        print(f"  Calmar Ratio:        {metrics.get('calmar_ratio', 0):>8.2f}")
        
        print("\nBenchmark Comparison:")
        benchmark_return = metrics.get('benchmark_total_return')
        benchmark_cagr = metrics.get('benchmark_cagr')
        alpha = metrics.get('alpha')
        beta = metrics.get('beta')
        info_ratio = metrics.get('information_ratio')
        
        print(f"  Benchmark Return:    {benchmark_return*100 if benchmark_return else 0:>8.2f}%")
        print(f"  Benchmark CAGR:      {benchmark_cagr*100 if benchmark_cagr else 0:>8.2f}%")
        print(f"  Alpha:               {alpha*100 if alpha else 0:>8.2f}%")
        print(f"  Beta:                {beta if beta else 0:>8.2f}")
        print(f"  Information Ratio:   {info_ratio if info_ratio else 0:>8.2f}")
        
        print("\nMarket Regime Analysis:")
        regime_stats = results.get('regime_stats', {})
        if regime_stats:
            print(f"  Bullish Periods:     {regime_stats.get('bullish_count', 0):>8d}")
            print(f"  Bearish Periods:     {regime_stats.get('bearish_count', 0):>8d}")
            print(f"  Avg Return (Bull):   {regime_stats.get('bullish_avg_return', 0)*100:>8.2f}%")
            print(f"  Avg Return (Bear):   {regime_stats.get('bearish_avg_return', 0)*100:>8.2f}%")
        
        # Salvar resultados
        print("\n" + "-"*80)
        print("SALVANDO RESULTADOS...")
        print("-"*80)
        
        service = BacktestService(db)
        backtest_id = service.save_backtest_result(
            config={
                'start_date': '2020-01-01',
                'end_date': '2024-12-31',
                'top_n': 10,
                'rebalance_frequency': 'monthly',
                'weight_method': 'score',
                'use_market_regime': True,
                'use_smoothing': True,
                'benchmark_symbol': '^BVSP',
                'momentum_weight': 0.5,
                'value_weight': 0.25,
                'quality_weight': 0.15,
                'risk_weight': 0.10
            },
            metrics=metrics,
            portfolio_history=results.get('portfolio_history', []),
            monthly_returns=results.get('monthly_returns', [])
        )
        
        print(f"\n✓ Backtest salvo com ID: {backtest_id}")
        
        print("\n" + "="*80)
        print("BACKTEST CONCLUÍDO COM SUCESSO")
        print("="*80 + "\n")
        
        # Comparação com equal weight (se disponível)
        print("\nPara comparar com equal weight, execute:")
        print("  python scripts/run_backtest_pipeline.py --weight-method equal")
        
    except Exception as e:
        logger.error(f"Erro ao executar backtest: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_optimized_backtest()
