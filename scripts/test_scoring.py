#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import FeatureMonthly, FeatureDaily
from app.scoring.scoring_engine import ScoringEngine
from datetime import date

db = SessionLocal()
today = date.today()
current_month = date(today.year, today.month, 1)

print("=" * 80)
print("TEST: SCORING ENGINE")
print("=" * 80)
print()

# Buscar features para VALE3
ticker = 'VALE3.SA'

monthly = db.query(FeatureMonthly).filter(
    FeatureMonthly.ticker == ticker,
    FeatureMonthly.month == current_month
).first()

daily = db.query(FeatureDaily).filter(
    FeatureDaily.ticker == ticker,
    FeatureDaily.date == today
).first()

if not monthly or not daily:
    print(f"Features não encontradas para {ticker}")
    db.close()
    sys.exit(1)

print(f"Features encontradas para {ticker}")
print()

# Montar dict de fatores como o scoring engine espera
factors = {}

# Features mensais
for col in ['roe', 'net_margin', 'revenue_growth_3y', 'debt_to_ebitda', 
            'pe_ratio', 'ev_ebitda', 'pb_ratio', 'price_to_book', 'fcf_yield',
            'size_factor', 'roe_mean_3y', 'roe_volatility', 'debt_to_ebitda_raw',
            'net_income_last_year', 'roa', 'efficiency_ratio', 'net_income_volatility',
            'overall_confidence']:
    value = getattr(monthly, col, None)
    factors[col] = value
    print(f"  {col}: {value}")

print()

# Features diárias
for col in ['return_1m', 'return_3m', 'return_6m', 'return_12m', 
            'volatility_90d', 'rsi_14', 'recent_drawdown', 'max_drawdown_3y']:
    value = getattr(daily, col, None)
    factors[col] = value

# Inicializar scoring engine
engine = ScoringEngine()

# Calcular scores
print("\nCalculando scores...")
quality = engine.calculate_quality_score(factors)
value = engine.calculate_value_score(factors)
momentum = engine.calculate_momentum_score(factors)

print(f"\nResultados:")
print(f"  Quality: {quality}")
print(f"  Value: {value}")
print(f"  Momentum: {momentum}")

db.close()
