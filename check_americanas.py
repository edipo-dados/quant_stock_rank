from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from sqlalchemy import desc

session = SessionLocal()
scores = session.query(ScoreDaily).order_by(desc(ScoreDaily.final_score)).all()

print('Top 10 Assets:')
for i, s in enumerate(scores[:10]):
    print(f'{i+1}. {s.ticker}: {s.final_score:.2f}')

print('\nBottom 10 Assets:')
for i, s in enumerate(scores[-10:]):
    print(f'{len(scores)-9+i}. {s.ticker}: {s.final_score:.2f}')

amer = [s for s in scores if 'AMER' in s.ticker]
if amer:
    rank = scores.index(amer[0]) + 1
    print(f'\nAmericanas (AMER3): Rank #{rank} - Score: {amer[0].final_score:.2f}')
else:
    print('\nAmericanas (AMER3): NOT FOUND IN SCORES')

session.close()
