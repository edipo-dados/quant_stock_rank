#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import FeatureMonthly
from datetime import date

db = SessionLocal()
today = date.today()
current_month = date(today.year, today.month, 1)

print("=" * 80)
print("DEBUG: FEATURES PARA SCORING")
print("=" * 80)
print()

# Buscar features mensais dos ativos que processamos
tickers = ['VALE3.SA', 'ITUB4.SA', 'PETR4.SA', 'BBAS3.SA', 'BBDC4.SA']

for ticker in tickers:
    f = db.query(FeatureMonthly).filter(
        FeatureMonthly.ticker == ticker,
        FeatureMonthly.month == current_month
    ).first()
    
    if f:
        print(f"\n{f.ticker}:")
        print(f"  roe_mean_3y: {f.roe_mean_3y}")
        print(f"  roe_volatility: {f.roe_volatility}")
        print(f"  net_margin: {f.net_margin}")
        print(f"  revenue_growth_3y: {f.revenue_growth_3y}")
        print(f"  debt_to_ebitda: {f.debt_to_ebitda}")
        print(f"  roe: {f.roe}")
        print(f"  pe_ratio: {f.pe_ratio}")
        print(f"  pb_ratio: {f.pb_ratio}")
        print(f"  overall_confidence: {f.overall_confidence}")
    else:
        print(f"\n{ticker}: NÃO ENCONTRADO")

db.close()
