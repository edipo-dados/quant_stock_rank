"""Script completo para diagnosticar por que ITUB3 não aparece"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import AssetInfo, RawPriceDaily, RawFundamental, FeatureDaily, ScoreDaily
from datetime import datetime, timedelta
from sqlalchemy import desc, func
import pandas as pd

db = SessionLocal()

print("\n" + "="*60)
print("DIAGNÓSTICO COMPLETO - ITUB3")
print("="*60)

# 1. Verificar se existe no banco
itub3 = db.query(AssetInfo).filter(AssetInfo.ticker == 'ITUB3').first()

if not itub3:
    print("\n❌ PROBLEMA: ITUB3 não encontrado na tabela AssetInfo!")
    print("   Solução: Execute o pipeline de ingestão")
    db.close()
    sys.exit(1)

print(f"\n✓ ITUB3 encontrado no banco")
print(f"  ID: {itub3.id}")
print(f"  Nome: {itub3.name}")
print(f"  is_active: {itub3.is_active}")
print(f"  is_eligible: {itub3.is_eligible}")

# 2. Verificar preços recentes
print("\n" + "-"*60)
print("VERIFICANDO PREÇOS")
print("-"*60)

recent_date = datetime.now() - timedelta(days=60)
prices = db.query(RawPriceDaily).filter(
    RawPriceDaily.ticker == 'ITUB3',
    RawPriceDaily.date >= recent_date
).order_by(desc(RawPriceDaily.date)).all()

if not prices:
    print("❌ PROBLEMA: Nenhum preço nos últimos 60 dias!")
    print("   Solução: Execute o pipeline de ingestão de preços")
else:
    print(f"✓ {len(prices)} preços encontrados nos últimos 60 dias")
    latest = prices[0]
    print(f"  Último preço: {latest.date}")
    print(f"  Close: R$ {latest.close:.2f}")
    print(f"  Volume: {latest.volume:,.0f}")
    
    # Calcular volume médio
    avg_volume = sum(p.volume for p in prices) / len(prices)
    print(f"  Volume médio (60d): {avg_volume:,.0f}")
    
    MIN_VOLUME = 100000
    if avg_volume < MIN_VOLUME:
        print(f"  ❌ Volume médio ({avg_volume:,.0f}) < mínimo ({MIN_VOLUME:,.0f})")
    else:
        print(f"  ✓ Volume OK (>= {MIN_VOLUME:,.0f})")

# 3. Verificar fundamentals
print("\n" + "-"*60)
print("VERIFICANDO FUNDAMENTALS")
print("-"*60)

fundamentals = db.query(RawFundamental).filter(
    RawFundamental.ticker == 'ITUB3'
).order_by(desc(RawFundamental.date)).first()

if not fundamentals:
    print("❌ PROBLEMA: Nenhum dado fundamental encontrado!")
    print("   Solução: Execute o pipeline de ingestão de fundamentals")
else:
    print(f"✓ Fundamentals encontrados")
    print(f"  Data: {fundamentals.date}")
    print(f"  Market Cap: R$ {fundamentals.market_cap:,.0f}" if fundamentals.market_cap else "  Market Cap: None")
    print(f"  Revenue: R$ {fundamentals.revenue:,.0f}" if fundamentals.revenue else "  Revenue: None")
    print(f"  EBITDA: R$ {fundamentals.ebitda:,.0f}" if fundamentals.ebitda else "  EBITDA: None")
    print(f"  Shareholders Equity: R$ {fundamentals.shareholders_equity:,.0f}" if fundamentals.shareholders_equity else "  Shareholders Equity: None")
    print(f"  Net Income: R$ {fundamentals.net_income:,.0f}" if fundamentals.net_income else "  Net Income: None")
    
    # Verificar critérios de elegibilidade
    MIN_MARKET_CAP = 1_000_000_000  # 1 bilhão
    
    issues = []
    if fundamentals.market_cap and fundamentals.market_cap < MIN_MARKET_CAP:
        issues.append(f"Market cap ({fundamentals.market_cap:,.0f}) < mínimo ({MIN_MARKET_CAP:,.0f})")
    
    if not fundamentals.shareholders_equity or fundamentals.shareholders_equity <= 0:
        issues.append("Shareholders equity <= 0")
    
    if not fundamentals.revenue or fundamentals.revenue <= 0:
        issues.append("Revenue <= 0")
    
    if fundamentals.net_income and fundamentals.net_income < 0:
        issues.append("Net income negativo")
    
    if issues:
        print("\n  ❌ PROBLEMAS DE ELEGIBILIDADE:")
        for issue in issues:
            print(f"     - {issue}")
    else:
        print("\n  ✓ Todos os critérios de elegibilidade OK")

# 4. Verificar features calculadas
print("\n" + "-"*60)
print("VERIFICANDO FEATURES CALCULADAS")
print("-"*60)

features = db.query(FeatureDaily).filter(
    FeatureDaily.ticker == 'ITUB3',
    FeatureDaily.date >= recent_date
).order_by(desc(FeatureDaily.date)).first()

if not features:
    print("❌ PROBLEMA: Nenhuma feature calculada nos últimos 60 dias!")
    print("   Solução: Execute o pipeline de cálculo de features")
else:
    print(f"✓ Features encontradas")
    print(f"  Data: {features.date}")
    print(f"  momentum_ex_1m: {features.momentum_ex_1m:.4f}" if features.momentum_ex_1m else "  momentum_ex_1m: None")
    print(f"  roe_mean_3y: {features.roe_mean_3y:.4f}" if features.roe_mean_3y else "  roe_mean_3y: None")
    print(f"  ev_ebitda: {features.ev_ebitda:.4f}" if features.ev_ebitda else "  ev_ebitda: None")

# 5. Verificar scores
print("\n" + "-"*60)
print("VERIFICANDO SCORES")
print("-"*60)

scores = db.query(ScoreDaily).filter(
    ScoreDaily.ticker == 'ITUB3',
    ScoreDaily.date >= recent_date
).order_by(desc(ScoreDaily.date)).limit(5).all()

if not scores:
    print("❌ PROBLEMA: Nenhum score calculado nos últimos 60 dias!")
    print("   Solução: Execute o pipeline de scoring")
else:
    print(f"✓ {len(scores)} scores encontrados")
    for s in scores[:3]:
        print(f"  {s.date}: Rank {s.rank} - Score: {s.composite_score:.4f}")

# 6. Verificar top 10 atual
print("\n" + "-"*60)
print("TOP 10 RANKING ATUAL")
print("-"*60)

latest_date = db.query(func.max(ScoreDaily.date)).scalar()
if latest_date:
    top10 = db.query(ScoreDaily).filter(
        ScoreDaily.date == latest_date
    ).order_by(ScoreDaily.rank).limit(10).all()
    
    print(f"Data: {latest_date}")
    for s in top10:
        print(f"  {s.rank}. {s.ticker} - Score: {s.composite_score:.4f}")
    
    # Verificar se ITUB3 está no ranking
    itub3_score = db.query(ScoreDaily).filter(
        ScoreDaily.ticker == 'ITUB3',
        ScoreDaily.date == latest_date
    ).first()
    
    if itub3_score:
        print(f"\n✓ ITUB3 está no ranking na posição {itub3_score.rank}")
    else:
        print(f"\n❌ ITUB3 NÃO está no ranking desta data!")
else:
    print("❌ Nenhum score encontrado no banco!")

print("\n" + "="*60)
print("FIM DO DIAGNÓSTICO")
print("="*60 + "\n")

db.close()
