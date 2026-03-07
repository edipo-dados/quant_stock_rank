"""
Script para comparar estratégias: Baseline vs Otimizada

Executa dois backtests e compara resultados:
1. Baseline: Equal weight, sem regime filter, sem smoothing
2. Otimizada: Score weight, com regime filter, com smoothing
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.backtest.backtest_engine import BacktestEngine
from datetime import date
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def run_comparison():
    """Compara estratégia baseline vs otimizada"""
    
    print("\n" + "="*80)
    print("COMPARAÇÃO DE ESTRATÉGIAS")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        # Parâmetros comuns
        common_params = {
            'start_date': date(2020, 1, 1),
            'end_date': date(2024, 12, 31),
            'top_n': 10,
            'rebalance_frequency': 'monthly',
            'benchmark_symbol': '^BVSP'
        }
        
        # ========================================
        # ESTRATÉGIA 1: BASELINE
        # ========================================
        print("\n" + "-"*80)
        print("EXECUTANDO ESTRATÉGIA BASELINE")
        print("-"*80)
        print("  - Equal weight")
        print("  - Sem regime filter")
        print("  - Sem smoothing")
        print("  - Pesos originais: M=0.4, V=0.3, Q=0.2, R=0.1")
        
        engine_baseline = BacktestEngine(
            **common_params,
            weight_method='equal',
            use_market_regime=False,
            use_smoothing=False
        )
        
        results_baseline = engine_baseline.run_backtest(db)
        metrics_baseline = results_baseline.get('metrics', {})
        
        # ========================================
        # ESTRATÉGIA 2: OTIMIZADA
        # ========================================
        print("\n" + "-"*80)
        print("EXECUTANDO ESTRATÉGIA OTIMIZADA")
        print("-"*80)
        print("  - Score weight (max 25% por ativo)")
        print("  - Com regime filter (IBOV MA200)")
        print("  - Com smoothing (0.7 atual + 0.3 anterior)")
        print("  - Pesos otimizados: M=0.5, V=0.25, Q=0.15, R=0.1")
        
        engine_optimized = BacktestEngine(
            **common_params,
            weight_method='score',
            use_market_regime=True,
            use_smoothing=True
        )
        
        results_optimized = engine_optimized.run_backtest(db)
        metrics_optimized = results_optimized.get('metrics', {})
        
        # ========================================
        # COMPARAÇÃO DE RESULTADOS
        # ========================================
        print("\n" + "="*80)
        print("COMPARAÇÃO DE RESULTADOS")
        print("="*80 + "\n")
        
        # Função auxiliar para calcular melhoria
        def calc_improvement(baseline, optimized, inverse=False):
            if baseline == 0:
                return 0
            improvement = ((optimized - baseline) / abs(baseline)) * 100
            if inverse:
                improvement = -improvement
            return improvement
        
        # Tabela de comparação
        print(f"{'Métrica':<25} {'Baseline':>12} {'Otimizada':>12} {'Melhoria':>12}")
        print("-" * 65)
        
        # Performance Metrics
        metrics_to_compare = [
            ('Total Return', 'total_return', False, '%'),
            ('CAGR', 'cagr', False, '%'),
            ('Volatility', 'volatility', True, '%'),
            ('Max Drawdown', 'max_drawdown', True, '%'),
            ('Sharpe Ratio', 'sharpe_ratio', False, ''),
            ('Sortino Ratio', 'sortino_ratio', False, ''),
            ('Calmar Ratio', 'calmar_ratio', False, ''),
        ]
        
        for label, key, inverse, unit in metrics_to_compare:
            baseline_val = metrics_baseline.get(key, 0)
            optimized_val = metrics_optimized.get(key, 0)
            improvement = calc_improvement(baseline_val, optimized_val, inverse)
            
            if unit == '%':
                baseline_str = f"{baseline_val*100:>10.2f}%"
                optimized_str = f"{optimized_val*100:>10.2f}%"
            else:
                baseline_str = f"{baseline_val:>12.2f}"
                optimized_str = f"{optimized_val:>12.2f}"
            
            improvement_str = f"{improvement:>+10.1f}%"
            
            print(f"{label:<25} {baseline_str} {optimized_str} {improvement_str}")
        
        print("\n" + "-" * 65)
        print("Benchmark Comparison")
        print("-" * 65)
        
        benchmark_metrics = [
            ('Alpha', 'alpha', False, '%'),
            ('Beta', 'beta', False, ''),
            ('Information Ratio', 'information_ratio', False, ''),
        ]
        
        for label, key, inverse, unit in benchmark_metrics:
            baseline_val = metrics_baseline.get(key, 0)
            optimized_val = metrics_optimized.get(key, 0)
            improvement = calc_improvement(baseline_val, optimized_val, inverse)
            
            if unit == '%':
                baseline_str = f"{baseline_val*100:>10.2f}%"
                optimized_str = f"{optimized_val*100:>10.2f}%"
            else:
                baseline_str = f"{baseline_val:>12.2f}"
                optimized_str = f"{optimized_val:>12.2f}"
            
            improvement_str = f"{improvement:>+10.1f}%"
            
            print(f"{label:<25} {baseline_str} {optimized_str} {improvement_str}")
        
        # Análise de regime (apenas otimizada)
        print("\n" + "-" * 65)
        print("Market Regime Analysis (Otimizada)")
        print("-" * 65)
        
        regime_stats = results_optimized.get('regime_stats', {})
        if regime_stats:
            print(f"Bullish Periods:     {regime_stats.get('bullish_count', 0):>8d}")
            print(f"Bearish Periods:     {regime_stats.get('bearish_count', 0):>8d}")
            print(f"Avg Return (Bull):   {regime_stats.get('bullish_avg_return', 0)*100:>8.2f}%")
            print(f"Avg Return (Bear):   {regime_stats.get('bearish_avg_return', 0)*100:>8.2f}%")
        
        # Resumo executivo
        print("\n" + "="*80)
        print("RESUMO EXECUTIVO")
        print("="*80 + "\n")
        
        sharpe_improvement = calc_improvement(
            metrics_baseline.get('sharpe_ratio', 0),
            metrics_optimized.get('sharpe_ratio', 0)
        )
        
        cagr_improvement = calc_improvement(
            metrics_baseline.get('cagr', 0),
            metrics_optimized.get('cagr', 0)
        )
        
        dd_improvement = calc_improvement(
            metrics_baseline.get('max_drawdown', 0),
            metrics_optimized.get('max_drawdown', 0),
            inverse=True
        )
        
        print(f"Sharpe Ratio:     {sharpe_improvement:>+6.1f}% de melhoria")
        print(f"CAGR:             {cagr_improvement:>+6.1f}% de melhoria")
        print(f"Max Drawdown:     {dd_improvement:>+6.1f}% de melhoria")
        
        if sharpe_improvement > 20 and dd_improvement > 10:
            print("\n✓ ESTRATÉGIA OTIMIZADA SUPERIOR")
            print("  Recomendação: Implementar em produção")
        elif sharpe_improvement > 10:
            print("\n⚠ ESTRATÉGIA OTIMIZADA MELHOR")
            print("  Recomendação: Validar com mais dados")
        else:
            print("\n❌ MELHORIAS INSUFICIENTES")
            print("  Recomendação: Revisar parâmetros")
        
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Erro na comparação: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_comparison()
