"""Script para investigar anomalias no backtest"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import RankingHistory, RawPriceDaily
from datetime import date
import pandas as pd

db = SessionLocal()

print("\n" + "="*80)
print("INVESTIGAÇÃO DE ANOMALIAS NO BACKTEST")
print("="*80 + "\n")

# 1. Verificar rankings com scores anormais
print("1. Verificando scores anormais...")

rankings = db.query(RankingHistory).all()
scores = [r.final_score for r in rankings if r.final_score is not None]

if scores:
    print(f"   Total de scores: {len(scores)}")
    print(f"   Mínimo: {min(scores):.4f}")
    print(f"   Máximo: {max(scores):.4f}")
    print(f"   Média: {sum(scores)/len(scores):.4f}")
    
    # Scores negativos
    negative = [s for s in scores if s < 0]
    if negative:
        print(f"   ⚠ {len(negative)} scores negativos encontrados!")
    
    # Scores muito altos
    very_high = [s for s in scores if s > 1.0]
    if very_high:
        print(f"   ⚠ {len(very_high)} scores > 1.0 encontrados!")

# 2. Verificar preços anormais
print("\n2. Verificando preços anormais...")

# Pegar amostra de preços recentes
recent_prices = db.query(RawPriceDaily).filter(
    RawPriceDaily.date >= date(2026, 1, 1)
).limit(1000).all()

if recent_prices:
    closes = [p.close for p in recent_prices if p.close is not None]
    print(f"   Total de preços: {len(closes)}")
    print(f"   Mínimo: R$ {min(closes):.2f}")
    print(f"   Máximo: R$ {max(closes):.2f}")
    print(f"   Média: R$ {sum(closes)/len(closes):.2f}")
    
    # Preços zerados ou negativos
    zero_or_neg = [p for p in closes if p <= 0]
    if zero_or_neg:
        print(f"   ⚠ {len(zero_or_neg)} preços <= 0 encontrados!")
    
    # Preços muito altos (possível erro)
    very_high_prices = [p for p in closes if p > 10000]
    if very_high_prices:
        print(f"   ⚠ {len(very_high_prices)} preços > R$ 10.000 encontrados!")

# 3. Verificar retornos mensais calculados
print("\n3. Verificando retornos mensais...")

# Pegar alguns tickers para análise
sample_tickers = ['ITUB3', 'VALE3', 'PETR4']

for ticker in sample_tickers:
    prices = db.query(RawPriceDaily).filter(
        RawPriceDaily.ticker == ticker,
        RawPriceDaily.date >= date(2022, 1, 1),
        RawPriceDaily.date <= date(2026, 3, 1)
    ).order_by(RawPriceDaily.date).all()
    
    if len(prices) > 1:
        # Calcular retornos
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1].close > 0:
                ret = (prices[i].close - prices[i-1].close) / prices[i-1].close
                returns.append(ret)
        
        if returns:
            print(f"\n   {ticker}:")
            print(f"     Preços disponíveis: {len(prices)}")
            print(f"     Retorno médio diário: {sum(returns)/len(returns)*100:.2f}%")
            print(f"     Retorno mínimo: {min(returns)*100:.2f}%")
            print(f"     Retorno máximo: {max(returns)*100:.2f}%")
            
            # Retornos anormais (> 50% em um dia)
            extreme = [r for r in returns if abs(r) > 0.5]
            if extreme:
                print(f"     ⚠ {len(extreme)} retornos extremos (>50% em 1 dia)!")

# 4. Verificar datas futuras
print("\n4. Verificando datas futuras...")

today = date.today()
future_rankings = db.query(RankingHistory).filter(
    RankingHistory.date > today
).count()

future_prices = db.query(RawPriceDaily).filter(
    RawPriceDaily.date > today
).count()

if future_rankings > 0:
    print(f"   ⚠ {future_rankings} rankings com datas futuras!")
    
if future_prices > 0:
    print(f"   ⚠ {future_prices} preços com datas futuras!")

# 5. Verificar consistência de tickers
print("\n5. Verificando consistência de tickers...")

ranking_tickers = set([r.ticker for r in db.query(RankingHistory.ticker).distinct()])
price_tickers = set([p.ticker for p in db.query(RawPriceDaily.ticker).distinct()])

print(f"   Tickers em RankingHistory: {len(ranking_tickers)}")
print(f"   Tickers em RawPriceDaily: {len(price_tickers)}")

# Tickers no ranking mas sem preços
missing_prices = ranking_tickers - price_tickers
if missing_prices:
    print(f"   ⚠ {len(missing_prices)} tickers no ranking sem preços:")
    print(f"     {list(missing_prices)[:10]}")

print("\n" + "="*80)
print("RECOMENDAÇÕES")
print("="*80 + "\n")

issues = []

if negative or very_high:
    issues.append("Scores anormais detectados")
    
if zero_or_neg or very_high_prices:
    issues.append("Preços anormais detectados")
    
if future_rankings or future_prices:
    issues.append("Datas futuras detectadas")
    
if missing_prices:
    issues.append("Tickers sem preços")

if issues:
    print("Problemas encontrados:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
    
    print("\nSoluções:")
    print("  1. Limpar dados anormais:")
    print("     docker exec -it quant-ranker-backend python scripts/clear_backtest_data.py")
    print("\n  2. Re-executar pipeline completo:")
    print("     docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py")
    print("\n  3. Regenerar snapshots:")
    print("     docker exec -it quant-ranker-backend python scripts/generate_historical_scores.py")
else:
    print("✓ Nenhum problema crítico detectado")

print("\n" + "="*80 + "\n")

db.close()
