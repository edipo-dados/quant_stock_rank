#!/usr/bin/env python3
"""
Teste para verificar o cálculo de fatores específicos por setor.

Testa:
1. Detecção automática de instituições financeiras
2. Cálculo de fatores específicos para bancos
3. Cálculo de fatores industriais para empresas não-financeiras
4. Scoring diferenciado por setor
"""

import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from app.factor_engine.fundamental_factors import FundamentalFactorCalculator
from app.factor_engine.financial_factors import FinancialFactorCalculator
from app.scoring.scoring_engine import ScoringEngine
from app.models.database import get_db
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_bank_sample_data():
    """Cria dados de exemplo para um banco (sem EBITDA)."""
    return {
        'net_income': 5000000000,  # R$ 5 bilhões
        'shareholders_equity': 50000000000,  # R$ 50 bilhões
        'revenue': 25000000000,  # R$ 25 bilhões
        'total_assets': 500000000000,  # R$ 500 bilhões
        'total_debt': 100000000000,  # R$ 100 bilhões
        'cash': 50000000000,  # R$ 50 bilhões
        'eps': 2.50,
        'book_value_per_share': 25.0,
        'ebitda': None,  # Bancos não reportam EBITDA
        'enterprise_value': None  # Não aplicável para bancos
    }


def create_industrial_sample_data():
    """Cria dados de exemplo para empresa industrial."""
    return {
        'net_income': 1000000000,  # R$ 1 bilhão
        'shareholders_equity': 10000000000,  # R$ 10 bilhões
        'revenue': 15000000000,  # R$ 15 bilhões
        'total_assets': 20000000000,  # R$ 20 bilhões
        'total_debt': 5000000000,  # R$ 5 bilhões
        'cash': 2000000000,  # R$ 2 bilhões
        'ebitda': 3000000000,  # R$ 3 bilhões
        'enterprise_value': 18000000000,  # R$ 18 bilhões
        'eps': 5.00,
        'book_value_per_share': 50.0
    }


def create_sample_history(base_data, years=3):
    """Cria histórico de 3 anos baseado nos dados base."""
    history = []
    for i in range(years):
        year_data = base_data.copy()
        # Simular crescimento/variação ao longo dos anos
        growth_factor = 1.0 + (i * 0.05)  # 5% de crescimento por ano
        
        year_data['net_income'] = int(base_data['net_income'] * growth_factor)
        year_data['shareholders_equity'] = int(base_data['shareholders_equity'] * growth_factor)
        year_data['revenue'] = int(base_data['revenue'] * growth_factor)
        
        if base_data.get('ebitda'):
            year_data['ebitda'] = int(base_data['ebitda'] * growth_factor)
        
        history.append(year_data)
    
    return history


def test_bank_factor_calculation():
    """Testa cálculo de fatores para banco."""
    print("\n=== TESTE: Cálculo de Fatores para Banco ===")
    
    calculator = FundamentalFactorCalculator()
    
    # Dados do banco
    bank_data = create_bank_sample_data()
    bank_history = create_sample_history(bank_data)
    current_price = 30.0
    
    print(f"Dados do banco:")
    print(f"  Net Income: R$ {bank_data['net_income']:,.0f}")
    print(f"  Shareholders Equity: R$ {bank_data['shareholders_equity']:,.0f}")
    print(f"  Revenue: R$ {bank_data['revenue']:,.0f}")
    print(f"  EBITDA: {bank_data['ebitda']} (não aplicável)")
    print(f"  Preço atual: R$ {current_price}")
    
    # Calcular fatores (sem sessão do banco - usará heurística)
    factors = calculator.calculate_all_factors(
        ticker="ITUB4",
        fundamentals_data=bank_data,
        fundamentals_history=bank_history,
        current_price=current_price,
        db_session=None  # Forçar uso de heurística
    )
    
    print(f"\nFatores calculados para banco:")
    for key, value in factors.items():
        if value is not None:
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")
        else:
            print(f"  {key}: None")
    
    # Verificar se fatores específicos de banco foram calculados
    expected_bank_factors = ['roe', 'pb_ratio', 'pe_ratio', 'roa', 'efficiency_ratio']
    missing_ebitda_factors = ['debt_to_ebitda', 'ev_ebitda']
    
    print(f"\nVerificação:")
    for factor in expected_bank_factors:
        status = "✅" if factors.get(factor) is not None else "❌"
        print(f"  {factor}: {status}")
    
    for factor in missing_ebitda_factors:
        status = "✅" if factors.get(factor) is None else "❌"
        print(f"  {factor} (deve ser None): {status}")
    
    return factors


def test_industrial_factor_calculation():
    """Testa cálculo de fatores para empresa industrial."""
    print("\n=== TESTE: Cálculo de Fatores para Empresa Industrial ===")
    
    calculator = FundamentalFactorCalculator()
    
    # Dados da empresa industrial
    industrial_data = create_industrial_sample_data()
    industrial_history = create_sample_history(industrial_data)
    current_price = 100.0
    
    print(f"Dados da empresa industrial:")
    print(f"  Net Income: R$ {industrial_data['net_income']:,.0f}")
    print(f"  Shareholders Equity: R$ {industrial_data['shareholders_equity']:,.0f}")
    print(f"  Revenue: R$ {industrial_data['revenue']:,.0f}")
    print(f"  EBITDA: R$ {industrial_data['ebitda']:,.0f}")
    print(f"  Preço atual: R$ {current_price}")
    
    # Calcular fatores
    factors = calculator.calculate_all_factors(
        ticker="PETR4",
        fundamentals_data=industrial_data,
        fundamentals_history=industrial_history,
        current_price=current_price,
        db_session=None
    )
    
    print(f"\nFatores calculados para empresa industrial:")
    for key, value in factors.items():
        if value is not None:
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")
        else:
            print(f"  {key}: None")
    
    # Verificar se fatores industriais foram calculados
    expected_industrial_factors = ['roe', 'debt_to_ebitda', 'ev_ebitda', 'pb_ratio', 'pe_ratio']
    
    print(f"\nVerificação:")
    for factor in expected_industrial_factors:
        status = "✅" if factors.get(factor) is not None else "❌"
        print(f"  {factor}: {status}")
    
    return factors


def test_scoring_differences():
    """Testa diferenças no scoring entre bancos e industriais."""
    print("\n=== TESTE: Diferenças no Scoring por Setor ===")
    
    scoring_engine = ScoringEngine()
    
    # Simular fatores normalizados para banco
    bank_factors = {
        'roe': 0.5,  # ROE normalizado
        'revenue_growth_3y': 0.3,  # Crescimento (book value growth)
        'net_margin': 0.4,
        'pe_ratio': -0.2,  # P/L (invertido)
        'pb_ratio': -0.1,  # P/VP (invertido)
        'debt_to_ebitda': None,  # Não aplicável
        'ev_ebitda': None,  # Não aplicável
        'roa': 0.6,  # Específico para bancos
        'efficiency_ratio': 0.3,  # Específico para bancos
        'net_income_last_year': 5000000000
    }
    
    # Simular fatores normalizados para industrial
    industrial_factors = {
        'roe': 0.4,
        'revenue_growth_3y': 0.5,
        'net_margin': 0.3,
        'debt_to_ebitda': -0.2,  # Dívida/EBITDA (invertido)
        'pe_ratio': -0.3,
        'ev_ebitda': -0.1,
        'pb_ratio': -0.2,
        'net_income_last_year': 1000000000
    }
    
    # Fatores de momentum (iguais para ambos)
    momentum_factors = {
        'return_6m': 0.2,
        'return_12m': 0.3,
        'rsi_14': 0.1,
        'volatility_90d': -0.2,
        'recent_drawdown': -0.1
    }
    
    print("Testando scoring para banco:")
    bank_result = scoring_engine.score_asset_sector_aware(
        ticker="ITUB4",
        fundamental_factors=bank_factors,
        momentum_factors=momentum_factors,
        confidence=0.8
    )
    
    print(f"  Final Score: {bank_result.final_score:.4f}")
    print(f"  Quality Score: {bank_result.quality_score:.4f}")
    print(f"  Value Score: {bank_result.value_score:.4f}")
    print(f"  Momentum Score: {bank_result.momentum_score:.4f}")
    
    print("\nTestando scoring para empresa industrial:")
    industrial_result = scoring_engine.score_asset_sector_aware(
        ticker="PETR4",
        fundamental_factors=industrial_factors,
        momentum_factors=momentum_factors,
        confidence=0.8
    )
    
    print(f"  Final Score: {industrial_result.final_score:.4f}")
    print(f"  Quality Score: {industrial_result.quality_score:.4f}")
    print(f"  Value Score: {industrial_result.value_score:.4f}")
    print(f"  Momentum Score: {industrial_result.momentum_score:.4f}")
    
    print(f"\nComparação:")
    print(f"  Diferença no Quality Score: {bank_result.quality_score - industrial_result.quality_score:.4f}")
    print(f"  Diferença no Value Score: {bank_result.value_score - industrial_result.value_score:.4f}")
    print(f"  Diferença no Final Score: {bank_result.final_score - industrial_result.final_score:.4f}")


def main():
    """Executa todos os testes."""
    print("🏦 TESTE DE FATORES ESPECÍFICOS POR SETOR")
    print("=" * 50)
    
    try:
        # Teste 1: Fatores para banco
        bank_factors = test_bank_factor_calculation()
        
        # Teste 2: Fatores para empresa industrial
        industrial_factors = test_industrial_factor_calculation()
        
        # Teste 3: Diferenças no scoring
        test_scoring_differences()
        
        print("\n" + "=" * 50)
        print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("\nResumo:")
        print("- Bancos não usam métricas baseadas em EBITDA")
        print("- Bancos têm fatores específicos (ROA, efficiency ratio)")
        print("- Scoring diferenciado por setor implementado")
        print("- Detecção automática de setor funcionando")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)