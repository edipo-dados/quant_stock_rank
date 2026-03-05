#!/usr/bin/env python3
"""
Script para testar e validar cálculos de métricas de performance.

Uso:
    python scripts/test_metrics_calculation.py
"""

import sys
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import numpy as np
import pandas as pd
import logging

from app.backtest.metrics import PerformanceMetrics

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_alpha_beta_calculation():
    """Testa cálculo de Alpha e Beta com dados sintéticos."""
    logger.info("=" * 60)
    logger.info("TESTE 1: Cálculo de Alpha e Beta")
    logger.info("=" * 60)
    
    # Criar dados sintéticos
    np.random.seed(42)
    n_periods = 36  # 3 anos de dados mensais
    
    # Benchmark: retorno médio de 1% ao mês com volatilidade de 5%
    benchmark_returns = pd.Series(
        np.random.normal(0.01, 0.05, n_periods),
        name='benchmark'
    )
    
    # Estratégia: beta=1.2, alpha=0.5% ao mês
    # Rs = alpha + beta * Rb + erro
    alpha_monthly = 0.005  # 0.5% ao mês = 6% ao ano
    beta = 1.2
    strategy_returns = pd.Series(
        alpha_monthly + beta * benchmark_returns + np.random.normal(0, 0.02, n_periods),
        name='strategy'
    )
    
    logger.info(f"Dados sintéticos criados:")
    logger.info(f"  Períodos: {n_periods}")
    logger.info(f"  Alpha esperado: {alpha_monthly * 12 * 100:.2f}% ao ano")
    logger.info(f"  Beta esperado: {beta:.2f}")
    logger.info(f"  Benchmark retorno médio: {benchmark_returns.mean() * 12 * 100:.2f}% ao ano")
    logger.info(f"  Estratégia retorno médio: {strategy_returns.mean() * 12 * 100:.2f}% ao ano")
    
    # Calcular Alpha e Beta
    alpha_calc, beta_calc = PerformanceMetrics.calculate_alpha_beta(
        strategy_returns,
        benchmark_returns,
        risk_free_rate=0.05,  # 5% ao ano
        periods_per_year=12
    )
    
    logger.info(f"\nResultados:")
    logger.info(f"  Alpha calculado: {alpha_calc:.2f}% ao ano")
    logger.info(f"  Beta calculado: {beta_calc:.2f}")
    logger.info(f"  Erro Alpha: {abs(alpha_calc - alpha_monthly * 12 * 100):.2f}%")
    logger.info(f"  Erro Beta: {abs(beta_calc - beta):.2f}")
    
    # Validar
    assert abs(alpha_calc - alpha_monthly * 12 * 100) < 5, "Alpha muito diferente do esperado"
    assert abs(beta_calc - beta) < 0.3, "Beta muito diferente do esperado"
    
    logger.info("✅ Teste 1 passou!")


def test_information_ratio():
    """Testa cálculo de Information Ratio."""
    logger.info("\n" + "=" * 60)
    logger.info("TESTE 2: Cálculo de Information Ratio")
    logger.info("=" * 60)
    
    # Criar dados sintéticos
    np.random.seed(42)
    n_periods = 36
    
    # Benchmark
    benchmark_returns = pd.Series(
        np.random.normal(0.01, 0.05, n_periods),
        name='benchmark'
    )
    
    # Estratégia com excess return consistente
    excess_return_monthly = 0.003  # 0.3% ao mês
    strategy_returns = benchmark_returns + excess_return_monthly + np.random.normal(0, 0.01, n_periods)
    
    logger.info(f"Dados sintéticos criados:")
    logger.info(f"  Excess return esperado: {excess_return_monthly * 12 * 100:.2f}% ao ano")
    
    # Calcular IR
    ir = PerformanceMetrics.calculate_information_ratio_v2(
        strategy_returns,
        benchmark_returns,
        periods_per_year=12
    )
    
    logger.info(f"\nResultados:")
    logger.info(f"  Information Ratio: {ir:.2f}")
    
    # IR típico está entre 0.5 e 1.5 para estratégias boas
    assert -2 < ir < 3, f"IR fora da faixa razoável: {ir}"
    
    logger.info("✅ Teste 2 passou!")


def test_realistic_scenario():
    """Testa com cenário realista de mercado."""
    logger.info("\n" + "=" * 60)
    logger.info("TESTE 3: Cenário Realista")
    logger.info("=" * 60)
    
    # Simular 5 anos de dados mensais
    np.random.seed(42)
    n_periods = 60
    
    # IBOVESPA: retorno médio de 8% ao ano, volatilidade de 25%
    benchmark_returns = pd.Series(
        np.random.normal(0.08/12, 0.25/np.sqrt(12), n_periods),
        name='IBOVESPA'
    )
    
    # Estratégia: alpha de 3% ao ano, beta de 0.9
    alpha_annual = 0.03
    beta = 0.9
    strategy_returns = pd.Series(
        alpha_annual/12 + beta * benchmark_returns + np.random.normal(0, 0.03/np.sqrt(12), n_periods),
        name='Strategy'
    )
    
    logger.info(f"Cenário realista:")
    logger.info(f"  Períodos: {n_periods} meses (5 anos)")
    logger.info(f"  Alpha esperado: {alpha_annual * 100:.2f}% ao ano")
    logger.info(f"  Beta esperado: {beta:.2f}")
    
    # Calcular métricas
    alpha_calc, beta_calc = PerformanceMetrics.calculate_alpha_beta(
        strategy_returns,
        benchmark_returns,
        risk_free_rate=0.10,  # 10% ao ano (CDI)
        periods_per_year=12
    )
    
    ir = PerformanceMetrics.calculate_information_ratio_v2(
        strategy_returns,
        benchmark_returns,
        periods_per_year=12
    )
    
    logger.info(f"\nResultados:")
    logger.info(f"  Alpha calculado: {alpha_calc:.2f}% ao ano")
    logger.info(f"  Beta calculado: {beta_calc:.2f}")
    logger.info(f"  Information Ratio: {ir:.2f}")
    logger.info(f"  Benchmark CAGR: {PerformanceMetrics.calculate_cagr(benchmark_returns, 12):.2f}%")
    logger.info(f"  Estratégia CAGR: {PerformanceMetrics.calculate_cagr(strategy_returns, 12):.2f}%")
    
    # Validações
    assert -20 < alpha_calc < 20, f"Alpha fora da faixa razoável: {alpha_calc:.2f}%"
    assert 0.5 < beta_calc < 1.5, f"Beta fora da faixa razoável: {beta_calc:.2f}"
    assert -2 < ir < 2, f"IR fora da faixa razoável: {ir:.2f}"
    
    logger.info("✅ Teste 3 passou!")


def test_validation_warnings():
    """Testa sistema de validação de métricas."""
    logger.info("\n" + "=" * 60)
    logger.info("TESTE 4: Sistema de Validação")
    logger.info("=" * 60)
    
    # Métricas normais
    normal_metrics = {
        'alpha': 5.0,
        'beta': 1.1,
        'information_ratio': 0.8,
        'sharpe_ratio': 1.5,
        'volatility': 20.0,
        'max_drawdown': -15.0
    }
    
    warnings = PerformanceMetrics.validate_metrics(normal_metrics)
    logger.info(f"Métricas normais - Warnings: {len(warnings)}")
    assert len(warnings) == 0, "Não deveria ter warnings para métricas normais"
    
    # Métricas anômalas
    anomalous_metrics = {
        'alpha': 290.0,  # Muito alto!
        'beta': 5.0,     # Muito alto!
        'information_ratio': 3.5,  # Muito alto!
        'sharpe_ratio': 8.0,  # Muito alto!
        'volatility': 150.0,  # Muito alta!
        'max_drawdown': -90.0  # Muito baixo!
    }
    
    warnings = PerformanceMetrics.validate_metrics(anomalous_metrics)
    logger.info(f"Métricas anômalas - Warnings: {len(warnings)}")
    for metric, warning in warnings.items():
        logger.info(f"  {metric}: {warning}")
    
    assert len(warnings) > 0, "Deveria ter warnings para métricas anômalas"
    assert 'alpha' in warnings, "Deveria ter warning para alpha"
    
    logger.info("✅ Teste 4 passou!")


def main():
    """Executa todos os testes."""
    logger.info("Iniciando testes de cálculo de métricas...")
    
    try:
        test_alpha_beta_calculation()
        test_information_ratio()
        test_realistic_scenario()
        test_validation_warnings()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ TODOS OS TESTES PASSARAM!")
        logger.info("=" * 60)
        
    except AssertionError as e:
        logger.error(f"\n❌ TESTE FALHOU: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ ERRO: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
