"""Script para verificar dados disponíveis para backtest"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import RankingHistory, RawPriceDaily, ScoreDaily, AssetInfo
from sqlalchemy import func
from datetime import date

db = SessionLocal()

print("\n" + "="*80)
print("VERIFICAÇÃO DE DADOS PARA BACKTEST")
print("="*80 + "\n")

# 1. AssetInfo
asset_count = db.query(AssetInfo).count()
print(f"1. AssetInfo:")
print(f"   Total de ativos: {asset_count}")

if asset_count > 0:
    assets = db.query(AssetInfo).limit(10).all()
    print(f"   Primeiros 10: {[a.ticker for a in assets]}")

# 2. RawPriceDaily
price_count = db.query(RawPriceDaily).count()
print(f"\n2. RawPriceDaily:")
print(f"   Total de preços: {price_count}")

if price_count > 0:
    first_price = db.query(RawPriceDaily).order_by(RawPriceDaily.date).first()
    last_price = db.query(RawPriceDaily).order_by(RawPriceDaily.date.desc()).first()
    print(f"   Primeira data: {first_price.date}")
    print(f"   Última data: {last_price.date}")
    
    # Tickers com preços
    tickers_with_prices = db.query(RawPriceDaily.ticker).distinct().count()
    print(f"   Tickers com preços: {tickers_with_prices}")

# 3. ScoreDaily
score_count = db.query(ScoreDaily).count()
print(f"\n3. ScoreDaily:")
print(f"   Total de scores: {score_count}")

if score_count > 0:
    first_score = db.query(ScoreDaily).order_by(ScoreDaily.date).first()
    last_score = db.query(ScoreDaily).order_by(ScoreDaily.date.desc()).first()
    print(f"   Primeira data: {first_score.date}")
    print(f"   Última data: {last_score.date}")
    
    # Tickers com scores
    tickers_with_scores = db.query(ScoreDaily.ticker).distinct().count()
    print(f"   Tickers com scores: {tickers_with_scores}")

# 4. RankingHistory
ranking_count = db.query(RankingHistory).count()
print(f"\n4. RankingHistory:")
print(f"   Total de snapshots: {ranking_count}")

if ranking_count > 0:
    first_ranking = db.query(RankingHistory).order_by(RankingHistory.date).first()
    last_ranking = db.query(RankingHistory).order_by(RankingHistory.date.desc()).first()
    print(f"   Primeira data: {first_ranking.date}")
    print(f"   Última data: {last_ranking.date}")
    
    # Datas únicas
    unique_dates = db.query(RankingHistory.date).distinct().count()
    print(f"   Datas únicas: {unique_dates}")
    
    # Exemplo de um snapshot
    sample_date = last_ranking.date
    sample_rankings = db.query(RankingHistory).filter(
        RankingHistory.date == sample_date
    ).order_by(RankingHistory.rank).limit(5).all()
    
    print(f"\n   Top 5 em {sample_date}:")
    for r in sample_rankings:
        print(f"     {r.rank}. {r.ticker} - Score: {r.final_score:.4f}")

# Diagnóstico
print("\n" + "="*80)
print("DIAGNÓSTICO")
print("="*80 + "\n")

if asset_count == 0:
    print("❌ Nenhum ativo cadastrado!")
    print("   Solução: docker exec -it quant-ranker-backend python scripts/update_liquid_stocks.py")
elif price_count == 0:
    print("❌ Nenhum preço disponível!")
    print("   Solução: docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py")
elif score_count == 0:
    print("❌ Nenhum score calculado!")
    print("   Solução: docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py")
elif ranking_count == 0:
    print("❌ Nenhum ranking snapshot!")
    print("   Solução: docker exec -it quant-ranker-backend python scripts/generate_historical_scores.py")
else:
    print("✓ Dados suficientes para backtest!")
    print(f"\n  Período disponível: {first_ranking.date} até {last_ranking.date}")
    print(f"  Total de snapshots: {unique_dates}")
    print(f"  Ativos por snapshot: ~{ranking_count // unique_dates if unique_dates > 0 else 0}")
    
    # Verificar se há dados para 2020-2024
    target_start = date(2020, 1, 1)
    target_end = date(2024, 12, 31)
    
    if first_ranking.date <= target_start and last_ranking.date >= target_end:
        print(f"\n  ✓ Período 2020-2024 disponível para backtest")
    else:
        print(f"\n  ⚠ Período 2020-2024 não totalmente disponível")
        print(f"    Disponível: {first_ranking.date} até {last_ranking.date}")
        print(f"    Necessário: {target_start} até {target_end}")

print("\n" + "="*80 + "\n")

db.close()
