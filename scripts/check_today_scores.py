#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date

db = SessionLocal()
today = date.today()
scores = db.query(ScoreDaily).filter(ScoreDaily.date == today).all()
print(f'Total scores hoje ({today}): {len(scores)}')
for s in scores:
    print(f'  {s.ticker}: final={s.final_score:.3f}, momentum={s.momentum_score:.3f}, quality={s.quality_score}, value={s.value_score}')
db.close()
