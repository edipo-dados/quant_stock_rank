"""Test API route directly with full error trace."""
import sys
import asyncio
from app.models.database import SessionLocal
from app.api.routes import get_ranking

async def test_ranking():
    db = SessionLocal()
    try:
        result = await get_ranking(date=None, db=db)
        print("Success!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_ranking())
