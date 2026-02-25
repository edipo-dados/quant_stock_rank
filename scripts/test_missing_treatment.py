"""
Script para testar o tratamento de valores ausentes (missing values).

Este script valida que:
1. Fatores críticos ausentes resultam em score = -999.0
2. Fatores secundários ausentes usam apenas fatores disponíveis
3. Imputação setorial funciona corretamente
"""

import sys
import math
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.scoring.scoring_engine import ScoringEngine
from app.factor_engine.normalizer import CrossSectionalNormalizer
from app.config import settings
import pandas as pd


def test_momentum_critical_missing():
    """Testa que fatores críticos ausentes resultam em score = -999.0"""
    print("\n" + "="*80)
    print("TESTE 1: Fatores Críticos de Momentum Ausentes")
    print("="*80)
    
    engine = ScoringEngine(settings)
    
    # Caso 1: momentum_6m_ex_1m ausente
    factors = {
        'momentum_6m_ex_1m': None,
        'momentum_12m_ex_1m': 0.15,
        'volatility_90d': 0.20,
        'recent_drawdown': -0.10
    }
    score = engine.calculate_momentum_score(factors)
    print(f"\nCaso 1: momentum_6m_ex_1m ausente")
    print(f"  Fatores: {factors}")
    print(f"  Score: {score}")
    print(f"  ✓ PASSOU" if score == -999.0 else f"  ✗ FALHOU (esperado -999.0)")
    
    # Caso 2: momentum_12m_ex_1m ausente
    factors = {
        'momentum_6m_ex_1m': 0.10,
        'momentum_12m_ex_1m': None,
        'volatility_90d': 0.20,
        'recent_drawdown': -0.10
    }
    score = engine.calculate_momentum_score(factors)
    print(f"\nCaso 2: momentum_12m_ex_1m ausente")
    print(f"  Fatores: {factors}")
    print(f"  Score: {score}")
    print(f"  ✓ PASSOU" if score == -999.0 else f"  ✗ FALHOU (esperado -999.0)")
    
    # Caso 3: Ambos ausentes
    factors = {
        'momentum_6m_ex_1m': None,
        'momentum_12m_ex_1m': None,
        'volatility_90d': 0.20,
        'recent_drawdown': -0.10
    }
    score = engine.calculate_momentum_score(factors)
    print(f"\nCaso 3: Ambos fatores críticos ausentes")
    print(f"  Fatores: {factors}")
    print(f"  Score: {score}")
    print(f"  ✓ PASSOU" if score == -999.0 else f"  ✗ FALHOU (esperado -999.0)")


def test_momentum_secondary_missing():
    """Testa que fatores secundários ausentes usam apenas disponíveis"""
    print("\n" + "="*80)
    print("TESTE 2: Fatores Secundários de Momentum Ausentes")
    print("="*80)
    
    engine = ScoringEngine(settings)
    
    # Caso 1: Todos os fatores presentes
    factors = {
        'momentum_6m_ex_1m': 0.10,
        'momentum_12m_ex_1m': 0.15,
        'volatility_90d': 0.20,
        'recent_drawdown': -0.10
    }
    score_all = engine.calculate_momentum_score(factors)
    print(f"\nCaso 1: Todos os fatores presentes")
    print(f"  Fatores: {factors}")
    print(f"  Score: {score_all:.4f}")
    
    # Caso 2: Fatores secundários ausentes
    factors = {
        'momentum_6m_ex_1m': 0.10,
        'momentum_12m_ex_1m': 0.15,
        'volatility_90d': None,
        'recent_drawdown': None
    }
    score_no_secondary = engine.calculate_momentum_score(factors)
    print(f"\nCaso 2: Fatores secundários ausentes")
    print(f"  Fatores: {factors}")
    print(f"  Score: {score_no_secondary:.4f}")
    print(f"  Score esperado (média de 0.10 e 0.15): {(0.10 + 0.15) / 2:.4f}")
    expected = (0.10 + 0.15) / 2
    print(f"  ✓ PASSOU" if abs(score_no_secondary - expected) < 0.001 else f"  ✗ FALHOU")


def test_quality_critical_missing():
    """Testa que fatores críticos de quality ausentes resultam em score = -999.0"""
    print("\n" + "="*80)
    print("TESTE 3: Fatores Críticos de Quality Ausentes")
    print("="*80)
    
    engine = ScoringEngine(settings)
    
    # Caso 1: roe_mean_3y ausente
    factors = {
        'roe_mean_3y': None,
        'roe_volatility': 0.05,
        'net_margin': 0.15,
        'revenue_growth_3y': 0.10,
        'debt_to_ebitda': 2.0
    }
    score = engine.calculate_quality_score(factors)
    print(f"\nCaso 1: roe_mean_3y ausente")
    print(f"  Score: {score}")
    print(f"  ✓ PASSOU" if score == -999.0 else f"  ✗ FALHOU (esperado -999.0)")
    
    # Caso 2: net_margin ausente
    factors = {
        'roe_mean_3y': 0.20,
        'roe_volatility': 0.05,
        'net_margin': None,
        'revenue_growth_3y': 0.10,
        'debt_to_ebitda': 2.0
    }
    score = engine.calculate_quality_score(factors)
    print(f"\nCaso 2: net_margin ausente")
    print(f"  Score: {score}")
    print(f"  ✓ PASSOU" if score == -999.0 else f"  ✗ FALHOU (esperado -999.0)")


def test_value_critical_missing():
    """Testa que fatores críticos de value ausentes resultam em score = -999.0"""
    print("\n" + "="*80)
    print("TESTE 4: Fatores Críticos de Value Ausentes")
    print("="*80)
    
    engine = ScoringEngine(settings)
    
    # Caso 1: pe_ratio ausente
    factors = {
        'pe_ratio': None,
        'price_to_book': 1.5,
        'ev_ebitda': 8.0,
        'fcf_yield': 0.05,
        'debt_to_ebitda': 2.0
    }
    score = engine.calculate_value_score(factors)
    print(f"\nCaso 1: pe_ratio ausente")
    print(f"  Score: {score}")
    print(f"  ✓ PASSOU" if score == -999.0 else f"  ✗ FALHOU (esperado -999.0)")
    
    # Caso 2: price_to_book ausente
    factors = {
        'pe_ratio': 12.0,
        'price_to_book': None,
        'ev_ebitda': 8.0,
        'fcf_yield': 0.05,
        'debt_to_ebitda': 2.0
    }
    score = engine.calculate_value_score(factors)
    print(f"\nCaso 2: price_to_book ausente")
    print(f"  Score: {score}")
    print(f"  ✓ PASSOU" if score == -999.0 else f"  ✗ FALHOU (esperado -999.0)")


def test_sector_imputation():
    """Testa imputação setorial de valores ausentes"""
    print("\n" + "="*80)
    print("TESTE 5: Imputação Setorial")
    print("="*80)
    
    normalizer = CrossSectionalNormalizer()
    
    # Criar DataFrame de teste
    df = pd.DataFrame({
        'roe': [0.15, None, 0.10, 0.25, None],
        'pe_ratio': [15.0, 20.0, None, 12.0, 14.0],
        'sector': ['Tech', 'Tech', 'Finance', 'Finance', 'Finance']
    }, index=['AAPL', 'MSFT', 'JPM', 'BAC', 'C'])
    
    print("\nDataFrame original:")
    print(df)
    
    # Imputar valores ausentes
    imputed_df = normalizer.impute_missing_with_sector_mean(
        df,
        factor_columns=['roe', 'pe_ratio'],
        sector_col='sector'
    )
    
    print("\nDataFrame após imputação:")
    print(imputed_df)
    
    # Verificar imputação de ROE
    # MSFT (Tech) deve receber média de Tech (0.15)
    msft_roe = imputed_df.loc['MSFT', 'roe']
    print(f"\nMSFT ROE imputado: {msft_roe:.4f} (esperado: 0.1500)")
    print(f"  ✓ PASSOU" if abs(msft_roe - 0.15) < 0.001 else f"  ✗ FALHOU")
    
    # C (Finance) deve receber média de Finance ((0.10 + 0.25) / 2 = 0.175)
    c_roe = imputed_df.loc['C', 'roe']
    print(f"C ROE imputado: {c_roe:.4f} (esperado: 0.1750)")
    print(f"  ✓ PASSOU" if abs(c_roe - 0.175) < 0.001 else f"  ✗ FALHOU")
    
    # JPM (Finance) deve receber média de Finance ((15 + 20 + 12 + 14) / 4 = 15.25)
    jpm_pe = imputed_df.loc['JPM', 'pe_ratio']
    print(f"JPM P/E imputado: {jpm_pe:.4f} (esperado: 15.2500)")
    print(f"  ✓ PASSOU" if abs(jpm_pe - 15.25) < 0.001 else f"  ✗ FALHOU")


def test_no_fixed_penalties():
    """Testa que penalidades fixas foram removidas"""
    print("\n" + "="*80)
    print("TESTE 6: Remoção de Penalidades Fixas")
    print("="*80)
    
    engine = ScoringEngine(settings)
    
    # Caso 1: debt_to_ebitda alto (antes tinha penalidade de 50%)
    factors = {
        'roe_mean_3y': 0.20,
        'roe_volatility': 0.05,
        'net_margin': 0.15,
        'revenue_growth_3y': 0.10,
        'debt_to_ebitda': 6.0  # > 5 (antes tinha penalidade)
    }
    score_high_debt = engine.calculate_quality_score(factors)
    
    # Caso 2: debt_to_ebitda baixo
    factors_low_debt = {
        'roe_mean_3y': 0.20,
        'roe_volatility': 0.05,
        'net_margin': 0.15,
        'revenue_growth_3y': 0.10,
        'debt_to_ebitda': 2.0  # < 5
    }
    score_low_debt = engine.calculate_quality_score(factors_low_debt)
    
    print(f"\nCaso 1: debt_to_ebitda = 6.0 (alto)")
    print(f"  Score: {score_high_debt:.4f}")
    print(f"\nCaso 2: debt_to_ebitda = 2.0 (baixo)")
    print(f"  Score: {score_low_debt:.4f}")
    
    # Verificar que não há penalidade fixa de 50%
    # Se houvesse penalidade, score_high_debt seria aproximadamente 0.5 * score_low_debt
    # Agora, a diferença deve ser apenas do fator normalizado
    print(f"\nRazão entre scores: {score_high_debt / score_low_debt:.4f}")
    print(f"  ✓ PASSOU (sem penalidade fixa de 50%)" if abs(score_high_debt / score_low_debt - 0.5) > 0.1 else f"  ✗ FALHOU (ainda tem penalidade)")


def main():
    """Executa todos os testes"""
    print("\n" + "="*80)
    print("TESTES DE TRATAMENTO DE VALORES AUSENTES")
    print("="*80)
    
    try:
        test_momentum_critical_missing()
        test_momentum_secondary_missing()
        test_quality_critical_missing()
        test_value_critical_missing()
        test_sector_imputation()
        test_no_fixed_penalties()
        
        print("\n" + "="*80)
        print("TODOS OS TESTES CONCLUÍDOS")
        print("="*80)
        
    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
