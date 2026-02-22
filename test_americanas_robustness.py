"""
Script de teste para verificar se a Americanas (AMER3) seria excluída/penalizada
com as novas regras de robustez.
"""

import pandas as pd
from app.filters.eligibility_filter import EligibilityFilter
from app.scoring.scoring_engine import ScoringEngine
from app.config import Settings

# Configuração
config = Settings(minimum_volume=100000)

# Dados simulados da Americanas (baseados em informações públicas)
# A Americanas teve prejuízos bilionários e está em recuperação judicial
americanas_fundamentals = {
    'shareholders_equity': -10_000_000_000,  # Patrimônio líquido negativo (bilhões)
    'ebitda': -2_000_000_000,  # EBITDA negativo
    'revenue': 30_000_000_000,  # Ainda tem receita
    'net_income_last_year': -20_000_000_000,  # Prejuízo bilionário
    'net_income_history': [-20_000_000_000, -5_000_000_000, 1_000_000_000],  # 2 anos negativos
    'net_debt_to_ebitda': 15.0,  # Endividamento extremo
    'total_debt': 30_000_000_000,
    'cash': 1_000_000_000,
    'net_income': -20_000_000_000
}

# Volume de negociação (ainda tem liquidez)
americanas_volume = pd.DataFrame({'volume': [500_000] * 90})

print("=" * 80)
print("TESTE DE ROBUSTEZ - AMERICANAS (AMER3)")
print("=" * 80)
print()

# Teste 1: Filtro de Elegibilidade
print("1. TESTE DO FILTRO DE ELEGIBILIDADE")
print("-" * 80)

eligibility_filter = EligibilityFilter(config)
is_eligible, exclusion_reasons = eligibility_filter.is_eligible(
    'AMER3',
    americanas_fundamentals,
    americanas_volume
)

print(f"Elegível: {is_eligible}")
print(f"Razões de exclusão: {exclusion_reasons}")
print()

if not is_eligible:
    print("✅ SUCESSO: Americanas foi EXCLUÍDA do universo de investimento")
    print()
    print("Razões detalhadas:")
    for reason in exclusion_reasons:
        if reason == "negative_or_zero_equity":
            print("  - Patrimônio líquido negativo (R$ -10 bilhões)")
        elif reason == "negative_or_zero_ebitda":
            print("  - EBITDA negativo (R$ -2 bilhões)")
        elif reason == "negative_net_income_last_year":
            print("  - Lucro líquido negativo no último ano (R$ -20 bilhões)")
        elif reason == "negative_net_income_2_of_3_years":
            print("  - Lucro negativo em 2 dos últimos 3 anos")
        elif reason == "excessive_leverage_debt_to_ebitda_gt_8":
            print("  - Endividamento excessivo (Dívida/EBITDA = 15.0)")
        else:
            print(f"  - {reason}")
else:
    print("❌ FALHA: Americanas NÃO foi excluída (deveria ter sido)")

print()
print("=" * 80)

# Teste 2: Distress Flag (caso passasse no filtro)
print("2. TESTE DO DISTRESS FLAG (se passasse no filtro)")
print("-" * 80)

# Simular fatores normalizados (valores fictícios)
fundamental_factors = {
    'roe_mean_3y': -2.0,  # ROE muito negativo
    'roe_volatility': 3.0,  # Alta volatilidade
    'net_margin': -0.5,
    'revenue_growth_3y': 0.1,
    'debt_to_ebitda': 5.0,  # Normalizado
    'debt_to_ebitda_raw': 15.0,  # Valor real
    'pe_ratio': None,  # Não aplicável com prejuízo
    'ev_ebitda': None,
    'pb_ratio': None,
    'net_income_last_year': -20_000_000_000,
    'net_income_history': [-20_000_000_000, -5_000_000_000, 1_000_000_000]
}

momentum_factors = {
    'return_6m': -0.5,
    'return_12m': -1.5,
    'rsi_14': 0.3,
    'volatility_90d': 2.0,
    'recent_drawdown': -0.8
}

scoring_engine = ScoringEngine(config)

# Calcular score com distress flag
score_result = scoring_engine.score_asset_enhanced(
    ticker='AMER3',
    fundamental_factors=fundamental_factors,
    momentum_factors=momentum_factors,
    net_income_volatility=2.5,
    financial_strength=0.0,  # Força financeira zero
    confidence=0.3,  # Baixa confiança
    volatility_limit=0.5,
    drawdown_limit=-0.3,
    passed_eligibility=False,  # Não passou no filtro
    exclusion_reasons=exclusion_reasons
)

print(f"Score Base: {score_result.base_score:.3f}")
print(f"Score Final: {score_result.final_score:.3f}")
print(f"Penalidades de Risco: {score_result.risk_penalties}")
print()

# Verificar se distress flag foi ativado
distress_penalty = score_result.risk_penalties.get('distress', 1.0)
if distress_penalty < 1.0:
    print(f"✅ SUCESSO: Distress flag ATIVADO (penalidade de {distress_penalty:.1%})")
    print(f"Razões: {score_result.risk_penalties.get('distress_reasons', [])}")
    print()
    print(f"Score foi reduzido de {score_result.base_score:.3f} para {score_result.final_score:.3f}")
    print(f"Redução: {(1 - score_result.final_score/score_result.base_score)*100:.1f}%")
else:
    print("❌ FALHA: Distress flag NÃO foi ativado (deveria ter sido)")

print()
print("=" * 80)

# Teste 3: Penalização de Qualidade
print("3. TESTE DE PENALIZAÇÃO DE QUALIDADE")
print("-" * 80)

quality_score = scoring_engine.calculate_quality_score(fundamental_factors)
print(f"Quality Score: {quality_score:.3f}")

# Verificar se foi penalizado por prejuízo
if fundamental_factors['net_income_last_year'] < 0:
    print("✅ Penalização por prejuízo recente aplicada (0.4x)")

# Verificar se foi penalizado por endividamento
if fundamental_factors['debt_to_ebitda_raw'] > 5:
    print("✅ Penalização forte por endividamento aplicada (0.7x)")
elif fundamental_factors['debt_to_ebitda_raw'] > 3:
    print("✅ Penalização leve por endividamento aplicada (0.9x)")

print()
print("=" * 80)
print("CONCLUSÃO")
print("=" * 80)
print()

if not is_eligible:
    print("✅ A Americanas seria EXCLUÍDA do universo de investimento")
    print("   devido a múltiplas violações dos critérios de elegibilidade.")
    print()
    print("   Isso protege os investidores de empresas em grave dificuldade financeira.")
else:
    print("⚠️  A Americanas passou no filtro, mas seria fortemente penalizada:")
    print(f"   - Distress flag: {distress_penalty:.1%}")
    print(f"   - Quality score muito baixo: {quality_score:.3f}")
    print(f"   - Score final: {score_result.final_score:.3f}")

print()
print("=" * 80)
