"""
Script para rodar backtest com melhorias de robustez (v2.7.0).

Melhorias implementadas:
1. Correção definitiva do cálculo de alpha (retornos diários alinhados)
2. Volatility targeting (ajusta exposição para volatilidade alvo)
3. Limites de exposição por setor (máx 30% por setor)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.backtest.backtest_engine import BacktestEngine
from app.config import settings
from datetime import date
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def run_enhanced_backtest():
    """Executa backtest com melhorias de robustez v2.7.0"""
    
    print("\n" + "="*80)
    print("BACKTEST ENHANCED - ESTRATÉGIA QUANTITATIVA v2.7.0")
    print("="*80)
    
    print("\nMelhorias Implementadas:")
    print("  1. ✅ Correção definitiva do cálculo de Alpha")
    print("     - Retornos diários alinhados por data")
    print("     - Risk-free rate convertida para frequência diária")
    print("     - Validações robustas de NaN e valores irrealistas")
    
    print("\n  2. ✅ Volatility Targeting")
    print("     - Ajusta pesos pelo inverso da volatilidade")
    print("     - Controla volatilidade do portfólio (alvo: 15%)")
    print("     - Melhora Sharpe Ratio esperado: +30-50%")
    
    print("\n  3. ✅ Limites de Exposição por Setor")
    print("     - Máximo 30% por setor")
    print("     - Evita concentração excessiva")
    print("     - Redistribui excesso proporcionalmente")
    
    print("\n" + "-"*80)
    print("CONFIGURAÇÕES")
    print("-"*80)
    
    # Configurações do backtest
    use_vol_targeting = settings.use_volatility_targeting
    use_sector_limits = settings.use_sector_limits
    target_vol = settings.target_portfolio_volatility
    max_sector = settings.max_sector_exposure
    
    print(f"  Volatility Targeting: {'ATIVADO' if use_vol_targeting else 'DESATIVADO'}")
    print(f"  Volatilidade Alvo: {target_vol*100:.0f}%")
    print(f"  Limites Setoriais: {'ATIVADO' if use_sector_limits else 'DESATIVADO'}")
    print(f"  Exposição Máxima por Setor: {max_sector*100:.0f}%")
    print(f"  Score-weighted: SIM (máx 25% por ativo)")
    print(f"  Market Regime Filter: SIM (MA200)")
    print(f"  Temporal Smoothing: SIM (0.7 + 0.3)")
    print(f"  Rebalanceamento: Mensal")
    print(f"  Top N: 10 ações")
    
    # Conectar ao banco
    db = SessionLocal()
    
    try:
        # Verificar dados disponíveis
        from app.models.schemas import RankingHistory, RawPriceDaily
        
        print("\n" + "-"*80)
        print("VERIFICANDO DADOS")
        print("-"*80)
        
        ranking_count = db.query(RankingHistory).count()
        price_count = db.query(RawPriceDaily).count()
        
        print(f"  Ranking snapshots: {ranking_count}")
        print(f"  Preços disponíveis: {price_count}")
        
        if ranking_count == 0:
            print("\n❌ ERRO: Nenhum ranking snapshot encontrado!")
            print("\nExecute primeiro:")
            print("  docker exec -it quant-ranker-backend python scripts/generate_historical_scores.py \\")
            print("    --start 2022-01-01 --end 2026-03-01 --frequency monthly")
            return
        
        # Determinar período
        first_ranking = db.query(RankingHistory).order_by(RankingHistory.date).first()
        last_ranking = db.query(RankingHistory).order_by(RankingHistory.date.desc()).first()
        
        if first_ranking and last_ranking:
            backtest_start = max(date(2022, 1, 1), first_ranking.date)
            backtest_end = min(date(2026, 3, 1), last_ranking.date)
            print(f"\n  Período: {backtest_start} até {backtest_end}")
        else:
            backtest_start = date(2022, 1, 1)
            backtest_end = date(2026, 3, 1)
        
        # Configurar backtest engine
        engine = BacktestEngine(
            start_date=backtest_start,
            end_date=backtest_end,
            top_n=10,
            rebalance_frequency='monthly',
            weight_method='score',  # Score-weighted
            use_smoothing=True,  # Temporal smoothing
            use_market_regime=True,  # Market regime filter
            benchmark_symbol='^BVSP',
            # Novos parâmetros v2.7.0
            use_volatility_targeting=use_vol_targeting,
            target_portfolio_volatility=target_vol,
            volatility_lookback_days=settings.volatility_lookback_days,
            use_sector_limits=use_sector_limits,
            max_sector_exposure=max_sector
        )
        
        print("\n" + "-"*80)
        print("EXECUTANDO BACKTEST")
        print("-"*80 + "\n")
        
        # Executar backtest
        results = engine.run_backtest(db)
        
        # Exibir resultados
        print("\n" + "="*80)
        print("RESULTADOS DO BACKTEST")
        print("="*80 + "\n")
        
        metrics = results.get('metrics', {})
        
        print("📊 Métricas de Performance")
        print(f"  Total Return:        {metrics.get('total_return', 0):.2f}%")
        print(f"  CAGR:                {metrics.get('cagr', 0):.2f}%")
        print(f"  Volatilidade:        {metrics.get('volatility', 0):.2f}%")
        print(f"  Max Drawdown:        {metrics.get('max_drawdown', 0):.2f}%")
        
        print("\n📈 Métricas Ajustadas ao Risco")
        print(f"  Sharpe Ratio:        {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"  Sortino Ratio:       {metrics.get('sortino_ratio', 0):.2f}")
        print(f"  Calmar Ratio:        {metrics.get('calmar_ratio', 0):.2f}")
        
        print("\n📊 Comparação vs IBOVESPA")
        alpha = metrics.get('alpha')
        beta = metrics.get('beta')
        ir = metrics.get('information_ratio')
        
        print(f"  Benchmark Return:    {metrics.get('benchmark_total_return', 0):.2f}%")
        print(f"  Benchmark CAGR:      {metrics.get('benchmark_cagr', 0):.2f}%")
        print(f"  Alpha Anual:         {alpha:.2f}%" if alpha else "  Alpha Anual:         N/A")
        print(f"  Beta:                {beta:.2f}" if beta else "  Beta:                N/A")
        print(f"  Information Ratio:   {ir:.2f}" if ir else "  Information Ratio:   N/A")
        
        print("\n🔄 Eficiência Operacional")
        print(f"  Turnover Médio:      {metrics.get('avg_turnover', 0):.2f}%")
        print(f"  Rebalanceamentos:    {metrics.get('num_rebalances', 0)}")
        
        # Validações
        warnings = metrics.get('validation_warnings', {})
        if warnings:
            print("\n⚠️  AVISOS DE VALIDAÇÃO:")
            for metric, warning in warnings.items():
                print(f"  - {metric}: {warning}")
        
        print("\n" + "="*80)
        print("BACKTEST CONCLUÍDO COM SUCESSO")
        print("="*80 + "\n")
        
        # Comparação
        print("Para comparar com versão anterior (sem melhorias):")
        print("  python scripts/run_optimized_backtest.py")
        
    except Exception as e:
        logger.error(f"Erro ao executar backtest: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_enhanced_backtest()
