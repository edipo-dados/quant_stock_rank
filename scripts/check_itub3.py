"""Script para verificar status do ITUB3"""
from app.models.database import SessionLocal
from app.models.schemas import AssetInfo, ScoreDaily, RawPriceDaily
from datetime import datetime, timedelta
from sqlalchemy import desc

db = SessionLocal()

# Verificar se ITUB3 existe
itub3 = db.query(AssetInfo).filter(AssetInfo.ticker == 'ITUB3').first()
print(f"\n=== STATUS DO ITUB3 ===")
print(f"ITUB3 encontrado: {itub3 is not None}")

if itub3:
    print(f"ID: {itub3.id}")
    print(f"Ticker: {itub3.ticker}")
    print(f"Nome: {itub3.name}")
    print(f"Ativo: {itub3.is_active}")
    print(f"Elegível: {itub3.is_eligible}")
    
    # Verificar preços recentes
    recent_date = datetime.now() - timedelta(days=30)
    prices = db.query(RawPriceDaily).filter(
        RawPriceDaily.ticker == 'ITUB3',
        RawPriceDaily.date >= recent_date
    ).order_by(desc(RawPriceDaily.date)).limit(5).all()
    
    print(f"\n=== PREÇOS RECENTES (últimos 5) ===")
    if prices:
        for p in prices:
            print(f"Data: {p.date}, Close: {p.close}")
    else:
        print("Nenhum preço encontrado!")
    
    # Verificar scores recentes
    scores = db.query(ScoreDaily).filter(
        ScoreDaily.ticker == 'ITUB3',
        ScoreDaily.date >= recent_date
    ).order_by(desc(ScoreDaily.date)).limit(5).all()
    
    print(f"\n=== SCORES RECENTES (últimos 5) ===")
    if scores:
        for s in scores:
            print(f"Data: {s.date}, Score: {s.composite_score:.4f}, Rank: {s.rank}")
    else:
        print("Nenhum score encontrado!")
else:
    print("ITUB3 não encontrado no banco de dados!")

# Verificar todos os ativos elegíveis
eligible = db.query(AssetInfo).filter(AssetInfo.is_eligible == True).all()
print(f"\n=== TOTAL DE ATIVOS ELEGÍVEIS: {len(eligible)} ===")
if eligible:
    print("Primeiros 10 tickers elegíveis:", [a.ticker for a in eligible[:10]])

# Verificar top 10 do ranking mais recente
latest_scores = db.query(ScoreDaily).order_by(
    desc(ScoreDaily.date),
    ScoreDaily.rank
).limit(10).all()

print(f"\n=== TOP 10 RANKING MAIS RECENTE ===")
if latest_scores:
    print(f"Data: {latest_scores[0].date}")
    for s in latest_scores:
        print(f"Rank {s.rank}: {s.ticker} - Score: {s.composite_score:.4f}")
else:
    print("Nenhum score encontrado!")

db.close()
