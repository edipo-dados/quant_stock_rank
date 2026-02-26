#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily, FeatureMonthly
from datetime import date
from dateutil.relativedelta import relativedelta

db = SessionLocal()
today = date.today()
current_month = date(today.year, today.month, 1)

print("=" * 80)
print("VERIFICAÇÃO DE CONFIDENCE FACTORS")
print("=" * 80)
print()

# Verificar scores
scores = db.query(ScoreDaily).filter(ScoreDaily.date == today).all()
print(f"📊 Scores de hoje ({today}): {len(scores)}")
print()

for s in scores[:5]:
    print(f"{s.ticker}:")
    print(f"  final={s.final_score:.3f}, momentum={s.momentum_score:.3f}")
    print(f"  quality={s.quality_score}, value={s.value_score}")
    print()

# Verificar features mensais com confidence
features = db.query(FeatureMonthly).filter(FeatureMonthly.month == current_month).all()
print(f"📈 Features mensais ({current_month}): {len(features)}")
print()

for f in features[:5]:
    print(f"{f.ticker}:")
    print(f"  roe_mean_3y={f.roe_mean_3y}, conf={f.roe_mean_3y_confidence}")
    print(f"  revenue_growth_3y={f.revenue_growth_3y}, conf={f.revenue_growth_3y_confidence}")
    print(f"  overall_confidence={f.overall_confidence}")
    print()

# Estatísticas de confidence
confidences = [f.overall_confidence for f in features if f.overall_confidence is not None]
if confidences:
    import numpy as np
    print("📊 Estatísticas de Confidence:")
    print(f"  Média: {np.mean(confidences):.2f}")
    print(f"  Mínimo: {np.min(confidences):.2f}")
    print(f"  Máximo: {np.max(confidences):.2f}")
    
    high = sum(1 for c in confidences if c >= 0.9)
    med = sum(1 for c in confidences if 0.6 <= c < 0.9)
    low = sum(1 for c in confidences if c < 0.6)
    
    print(f"  Alta (≥0.9): {high} ativos")
    print(f"  Média (0.6-0.9): {med} ativos")
    print(f"  Baixa (<0.6): {low} ativos")

db.close()
