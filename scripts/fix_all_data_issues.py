"""Script para corrigir todos os problemas de dados"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import RankingHistory, RawPriceDaily, ScoreDaily
from datetime import date

db = SessionLocal()

print("\n" + "="*80)
print("CORREÇÃO DE PROBLEMAS DE DADOS")
print("="*80 + "\n")

# 1. Remover rankings com datas futuras
print("1. Removendo rankings com datas futuras...")
today = date.today()
future_rankings = db.query(RankingHistory).filter(
    RankingHistory.date > today
).delete()
db.commit()
print(f"   ✓ {future_rankings} rankings futuros removidos")

# 2. Remover scores com datas futuras
print("\n2. Removendo scores com datas futuras...")
future_scores = db.query(ScoreDaily).filter(
    ScoreDaily.date > today
).delete()
db.commit()
print(f"   ✓ {future_scores} scores futuros removidos")

# 3. Adicionar sufixo .SA aos tickers em RawPriceDaily (se necessário)
print("\n3. Verificando sufixos .SA em preços...")
prices_without_sa = db.query(RawPriceDaily).filter(
    ~RawPriceDaily.ticker.like('%.SA')
).limit(10).all()

if prices_without_sa:
    print("   Preços já estão sem .SA (correto)")
else:
    print("   Preços já têm .SA")

# 4. Verificar tickers em rankings vs preços
print("\n4. Verificando consistência de tickers...")

ranking_tickers = set([r.ticker for r in db.query(RankingHistory.ticker).distinct()])
price_tickers = set([p.ticker for p in db.query(RawPriceDaily.ticker).distinct()])

print(f"   Tickers em rankings: {len(ranking_tickers)}")
print(f"   Tickers em preços: {len(price_tickers)}")

# Tickers no ranking mas sem preços
missing_prices = ranking_tickers - price_tickers
if missing_prices:
    print(f"\n   ⚠ {len(missing_prices)} tickers no ranking sem preços")
    print(f"   Removendo rankings desses tickers...")
    
    for ticker in missing_prices:
        deleted = db.query(RankingHistory).filter(
            RankingHistory.ticker == ticker
        ).delete()
        print(f"     - {ticker}: {deleted} registros removidos")
    
    db.commit()
    print(f"   ✓ Rankings de tickers sem preços removidos")

# 5. Verificar scores negativos
print("\n5. Verificando scores negativos...")
negative_scores = db.query(RankingHistory).filter(
    RankingHistory.final_score < 0
).count()

if negative_scores > 0:
    print(f"   ⚠ {negative_scores} scores negativos encontrados")
    print("   Isso é normal se os scores foram normalizados com z-score")
    print("   Para backtest, usar apenas scores positivos ou re-normalizar")

# Resumo final
print("\n" + "="*80)
print("RESUMO")
print("="*80 + "\n")

remaining_rankings = db.query(RankingHistory).count()
remaining_dates = db.query(RankingHistory.date).distinct().count()
remaining_tickers = db.query(RankingHistory.ticker).distinct().count()

print(f"Rankings restantes: {remaining_rankings}")
print(f"Datas únicas: {remaining_dates}")
print(f"Tickers únicos: {remaining_tickers}")

if remaining_dates > 0:
    first = db.query(RankingHistory).order_by(RankingHistory.date).first()
    last = db.query(RankingHistory).order_by(RankingHistory.date.desc()).first()
    print(f"Período: {first.date} até {last.date}")

print("\n✓ Correções aplicadas!")
print("\nPróximo passo:")
print("  docker exec -it quant-ranker-backend python scripts/run_optimized_backtest.py")

print("\n" + "="*80 + "\n")

db.close()
