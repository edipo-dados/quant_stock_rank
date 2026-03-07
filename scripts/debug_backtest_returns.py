"""Script para debugar cálculo de retornos no backtest"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import RankingHistory, RawPriceDaily
from app.backtest.backtest_engine import BacktestEngine
from datetime import date, timedelta
import pandas as pd

db = SessionLocal()

print("\n" + "="*80)
print("DEBUG: CÁLCULO DE RETORNOS NO BACKTEST")
print("="*80 + "\n")

# 1. Verificar um período específico
print("1. Testando cálculo manual de retornos...")

ticker = 'ITUB3'
start = date(2022, 1, 1)
end = date(2022, 3, 1)

prices = db.query(RawPriceDaily).filter(
    RawPriceDaily.ticker == ticker,
    RawPriceDaily.date >= start,
    RawPriceDaily.date <= end
).order_by(RawPriceDaily.date).all()

if prices:
    print(f"\n{ticker} - Primeiros 10 preços:")
    for p in prices[:10]:
        print(f"  {p.date}: R$ {p.close:.2f}")
    
    # Calcular retorno do período
    if len(prices) >= 2:
        first_price = prices[0].close
        last_price = prices[-1].close
        period_return = (last_price - first_price) / first_price
        
        print(f"\nRetorno do período:")
        print(f"  Preço inicial: R$ {first_price:.2f}")
        print(f"  Preço final: R$ {last_price:.2f}")
        print(f"  Retorno: {period_return*100:.2f}%")
        
        if period_return < -1.0:
            print(f"  ⚠ RETORNO ANORMAL! Menor que -100%")

# 2. Testar método get_monthly_returns do BacktestEngine
print("\n2. Testando método get_monthly_returns...")

engine = BacktestEngine(
    start_date=date(2022, 1, 1),
    end_date=date(2022, 3, 1),
    top_n=5
)

# Pegar um snapshot
snapshot_date = date(2022, 1, 31)
next_date = date(2022, 2, 28)

ranking = db.query(RankingHistory).filter(
    RankingHistory.date == snapshot_date
).order_by(RankingHistory.rank).limit(5).all()

if ranking:
    tickers = [r.ticker for r in ranking]
    print(f"\nTop 5 em {snapshot_date}: {tickers}")
    
    # Calcular retornos
    returns = engine.get_monthly_returns(tickers, snapshot_date, next_date)
    
    print(f"\nRetornos calculados pelo engine:")
    for ticker, ret in returns.items():
        print(f"  {ticker}: {ret*100:.2f}%")
        if ret < -1.0:
            print(f"    ⚠ RETORNO ANORMAL!")

# 3. Verificar se há preços duplicados ou faltantes
print("\n3. Verificando qualidade dos preços...")

for ticker in ['ITUB3', 'VALE3', 'PETR4']:
    prices = db.query(RawPriceDaily).filter(
        RawPriceDaily.ticker == ticker,
        RawPriceDaily.date >= date(2022, 1, 1),
        RawPriceDaily.date <= date(2022, 12, 31)
    ).order_by(RawPriceDaily.date).all()
    
    if prices:
        # Verificar duplicatas
        dates = [p.date for p in prices]
        duplicates = len(dates) - len(set(dates))
        
        # Verificar gaps
        gaps = 0
        for i in range(1, len(prices)):
            days_diff = (prices[i].date - prices[i-1].date).days
            if days_diff > 7:  # Gap maior que 1 semana
                gaps += 1
        
        # Verificar preços zerados
        zero_prices = sum(1 for p in prices if p.close <= 0)
        
        print(f"\n{ticker}:")
        print(f"  Total de preços: {len(prices)}")
        print(f"  Duplicatas: {duplicates}")
        print(f"  Gaps > 7 dias: {gaps}")
        print(f"  Preços <= 0: {zero_prices}")
        
        if duplicates > 0 or gaps > 10 or zero_prices > 0:
            print(f"  ⚠ PROBLEMAS DETECTADOS!")

# 4. Verificar benchmark
print("\n4. Verificando benchmark (^BVSP)...")

benchmark_prices = db.query(RawPriceDaily).filter(
    RawPriceDaily.ticker == '^BVSP',
    RawPriceDaily.date >= date(2022, 1, 1),
    RawPriceDaily.date <= date(2022, 12, 31)
).order_by(RawPriceDaily.date).all()

if benchmark_prices:
    print(f"  Preços do benchmark: {len(benchmark_prices)}")
    print(f"  Primeiros 5:")
    for p in benchmark_prices[:5]:
        print(f"    {p.date}: {p.close:.2f}")
else:
    print("  ❌ BENCHMARK NÃO ENCONTRADO!")
    print("  Isso explica os retornos anormais do benchmark")

print("\n" + "="*80)
print("DIAGNÓSTICO")
print("="*80 + "\n")

if not benchmark_prices:
    print("❌ PROBLEMA CRÍTICO: Benchmark não encontrado!")
    print("\nSolução:")
    print("  1. Ingerir dados do IBOVESPA:")
    print("     docker exec -it quant-ranker-backend python scripts/ingest_benchmark.py")
    print("\n  2. Re-executar backtest")

print("\n" + "="*80 + "\n")

db.close()
