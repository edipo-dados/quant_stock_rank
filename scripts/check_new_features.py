#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily, FeatureMonthly
from datetime import date

db = SessionLocal()
today = date.today()
current_month = date(today.year, today.month, 1)

print("=" * 80)
print(f"VERIFICAÇÃO DE FEATURES RECÉM-CRIADAS ({today})")
print("=" * 80)
print()

# Verificar features mensais criadas hoje
features = db.query(FeatureMonthly).filter(
    FeatureMonthly.month == current_month
).order_by(FeatureMonthly.ticker).all()

print(f"📈 Features mensais de {current_month}: {len(features)}")
print()

# Mostrar apenas os 10 primeiros (os que acabamos de processar)
tickers_processed = ['VALE3.SA', 'ITUB4.SA', 'PETR4.SA', 'BBAS3.SA', 'BBDC4.SA', 
                     'B3SA3.SA', 'BPAC11.SA', 'PRIO3.SA', 'PETR3.SA']

for ticker in tickers_processed:
    f = next((feat for feat in features if feat.ticker == ticker), None)
    if f:
        print(f"{f.ticker}:")
        print(f"  roe_mean_3y={f.roe_mean_3y}")
        print(f"  roe_mean_3y_confidence={f.roe_mean_3y_confidence}")
        print(f"  revenue_growth_3y={f.revenue_growth_3y}")
        print(f"  revenue_growth_3y_confidence={f.revenue_growth_3y_confidence}")
        print(f"  roe_volatility_confidence={f.roe_volatility_confidence}")
        print(f"  net_income_volatility_confidence={f.net_income_volatility_confidence}")
        print(f"  overall_confidence={f.overall_confidence}")
        print()

# Verificar scores
scores = db.query(ScoreDaily).filter(
    ScoreDaily.date == today
).order_by(ScoreDaily.ticker).all()

print(f"📊 Scores de hoje ({today}): {len(scores)}")
print()

for ticker in tickers_processed:
    s = next((score for score in scores if score.ticker == ticker), None)
    if s:
        print(f"{s.ticker}:")
        print(f"  final={s.final_score:.3f}")
        print(f"  momentum={s.momentum_score:.3f}")
        print(f"  quality={s.quality_score}")
        print(f"  value={s.value_score}")
        print()

db.close()
