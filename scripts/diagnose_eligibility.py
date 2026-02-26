#!/usr/bin/env python3
"""
Script de diagnóstico para entender por que todos os ativos estão sendo excluídos.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.database import SessionLocal
from app.models.schemas import RawFundamental, RawPriceDaily
from app.config import settings
from datetime import date
import pandas as pd

def diagnose():
    db = SessionLocal()
    
    # Tickers de teste
    tickers = ['VALE3.SA', 'ITUB4.SA', 'PETR4.SA', 'BBAS3.SA', 'BBDC4.SA']
    
    print("=" * 80)
    print("DIAGNÓSTICO DE ELEGIBILIDADE")
    print("=" * 80)
    
    for ticker in tickers:
        print(f"\n{ticker}:")
        print("-" * 40)
        
        # Buscar fundamentos
        fundamental = db.query(RawFundamental).filter(
            RawFundamental.ticker == ticker
        ).order_by(RawFundamental.period_end_date.desc()).first()
        
        if not fundamental:
            print("  ❌ Sem fundamentos no banco")
            continue
        
        print(f"  ✓ Fundamentos encontrados (data: {fundamental.period_end_date})")
        print(f"    - shareholders_equity: {fundamental.shareholders_equity}")
        print(f"    - ebitda: {fundamental.ebitda}")
        print(f"    - revenue: {fundamental.revenue}")
        print(f"    - net_income: {fundamental.net_income}")
        print(f"    - total_debt: {fundamental.total_debt}")
        
        # Calcular net_debt_to_ebitda
        if fundamental.total_debt and fundamental.ebitda and fundamental.ebitda != 0:
            net_debt_to_ebitda = fundamental.total_debt / fundamental.ebitda
            print(f"    - net_debt_to_ebitda: {net_debt_to_ebitda:.2f}")
        else:
            print(f"    - net_debt_to_ebitda: N/A")
        
        # Buscar histórico de net_income
        net_income_history = db.query(RawFundamental).filter(
            RawFundamental.ticker == ticker
        ).order_by(RawFundamental.period_end_date.desc()).limit(3).all()
        
        print(f"    - net_income_history: {[f.net_income for f in net_income_history]}")
        
        # Buscar volume
        volume_query = db.query(RawPriceDaily).filter(
            RawPriceDaily.ticker == ticker
        ).order_by(RawPriceDaily.date.desc()).limit(90).all()
        
        if not volume_query:
            print("  ❌ Sem dados de volume")
        else:
            volumes = [p.volume for p in volume_query]
            avg_volume = sum(volumes) / len(volumes)
            print(f"  ✓ Volume médio (90d): {avg_volume:,.0f}")
            print(f"    - Mínimo requerido: {settings.minimum_volume:,.0f}")
            print(f"    - Status: {'✓ OK' if avg_volume >= settings.minimum_volume else '❌ BAIXO'}")
        
        # Verificar critérios de exclusão
        print("\n  Critérios de elegibilidade:")
        
        # 1. Equity
        if fundamental.shareholders_equity and fundamental.shareholders_equity > 0:
            print("    ✓ shareholders_equity > 0")
        else:
            print("    ❌ shareholders_equity <= 0 ou None")
        
        # 2. EBITDA
        if fundamental.ebitda and fundamental.ebitda > 0:
            print("    ✓ ebitda > 0")
        else:
            print("    ❌ ebitda <= 0 ou None (pode ser instituição financeira)")
        
        # 3. Revenue
        if fundamental.revenue and fundamental.revenue > 0:
            print("    ✓ revenue > 0")
        else:
            print("    ❌ revenue <= 0 ou None")
        
        # 4. Net income last year
        if fundamental.net_income and fundamental.net_income >= 0:
            print("    ✓ net_income >= 0")
        else:
            print("    ❌ net_income < 0")
        
        # 5. Net income history
        if len(net_income_history) >= 3:
            negative_years = sum(1 for f in net_income_history if f.net_income and f.net_income < 0)
            if negative_years < 2:
                print(f"    ✓ net_income positivo em pelo menos 2 dos últimos 3 anos ({3-negative_years}/3)")
            else:
                print(f"    ❌ net_income negativo em 2+ dos últimos 3 anos ({negative_years}/3)")
        else:
            print(f"    ⚠️  Histórico incompleto ({len(net_income_history)}/3 anos)")
        
        # 6. Leverage
        if fundamental.total_debt and fundamental.ebitda and fundamental.ebitda != 0:
            net_debt_to_ebitda = fundamental.total_debt / fundamental.ebitda
            if net_debt_to_ebitda <= 8:
                print(f"    ✓ net_debt_to_ebitda <= 8 ({net_debt_to_ebitda:.2f})")
            else:
                print(f"    ❌ net_debt_to_ebitda > 8 ({net_debt_to_ebitda:.2f})")
        else:
            print("    ⚠️  net_debt_to_ebitda não calculável")
        
        # 7. PROBLEMA: Fatores críticos
        print("\n  ⚠️  PROBLEMA IDENTIFICADO:")
        print("    O filtro está verificando se os fatores críticos já existem:")
        print("    - momentum_6m_ex_1m")
        print("    - momentum_12m_ex_1m")
        print("    - roe_mean_3y")
        print("    - net_margin")
        print("    - pe_ratio")
        print("    - price_to_book")
        print("\n    Mas esses fatores são calculados DEPOIS do filtro!")
        print("    Isso causa exclusão de 100% dos ativos.")
    
    db.close()
    
    print("\n" + "=" * 80)
    print("CONCLUSÃO:")
    print("=" * 80)
    print("O filtro de elegibilidade está verificando se os fatores críticos")
    print("já existem no dict 'fundamentals', mas esses fatores são calculados")
    print("DEPOIS do filtro passar. Isso cria um deadlock:")
    print("  - Filtro requer fatores → Exclui todos")
    print("  - Fatores só são calculados para elegíveis → Nenhum elegível")
    print("\nSOLUÇÃO: Remover verificação de fatores críticos do filtro.")
    print("=" * 80)

if __name__ == "__main__":
    diagnose()
