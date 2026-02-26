#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import RawFundamental
from datetime import date

db = SessionLocal()

print("=" * 80)
print("DEBUG: DADOS FUNDAMENTAIS")
print("=" * 80)
print()

# Verificar dados fundamentais para alguns tickers
tickers = ['VALE3.SA', 'ITUB4.SA', 'BBAS3.SA']

for ticker in tickers:
    fundamentals = db.query(RawFundamental).filter(
        RawFundamental.ticker == ticker
    ).order_by(RawFundamental.period_end_date.desc()).all()
    
    print(f"\n{ticker}: {len(fundamentals)} registros")
    
    for f in fundamentals[:3]:  # Mostrar apenas os 3 mais recentes
        print(f"  Period: {f.period_end_date}")
        print(f"    revenue: {f.revenue}")
        print(f"    net_income: {f.net_income}")
        print(f"    total_assets: {f.total_assets}")
        print(f"    shareholders_equity: {f.shareholders_equity}")
        print(f"    ebitda: {f.ebitda}")

db.close()
