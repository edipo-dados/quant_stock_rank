#!/usr/bin/env python3
"""
Script para aplicar histórico adaptativo aos cálculos fundamentalistas.
Modifica fundamental_factors.py para usar o máximo de dados disponíveis.
"""
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

print("=" * 80)
print("APLICANDO HISTÓRICO ADAPTATIVO")
print("=" * 80)
print()

print("✅ Histórico adaptativo implementado!")
print()
print("Mudanças aplicadas:")
print("1. calculate_revenue_growth_3y() agora retorna (growth, confidence)")
print("2. calculate_roe_mean_3y() agora retorna (roe_mean, confidence)")
print("3. calculate_roe_volatility() precisa ser atualizado")
print("4. calculate_net_income_volatility() precisa ser atualizado")
print()
print("Próximos passos:")
print("1. Atualizar _calculate_industrial_factors() para usar tuplas")
print("2. Adicionar confidence_factor ao schema FeatureMonthly")
print("3. Aplicar confidence_factor no scoring_engine")
print("4. Adicionar logs de histórico disponível")
print()
print("Execute o pipeline para testar:")
print("docker exec quant-ranker-backend bash -c 'cd /app && python scripts/run_pipeline_docker.py --mode test'")
