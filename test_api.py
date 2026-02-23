import asyncio
from app.api.routes import get_ranking
from app.models.database import SessionLocal

async def test():
    db = SessionLocal()
    try:
        print("Calling get_ranking...")
        result = await get_ranking(date=None, db=db)
        print(f'Success! Got {result.total_assets} assets')
        print(f'Top 3: {[r.ticker for r in result.rankings[:3]]}')
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test())
