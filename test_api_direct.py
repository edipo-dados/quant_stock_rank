"""Test API endpoint directly."""
import sys
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from app.api.routes import _get_latest_date, _score_daily_to_score_breakdown
from sqlalchemy import desc

# Test database query
db = SessionLocal()

try:
    # Get latest date
    latest_date = _get_latest_date(db)
    print(f"Latest date: {latest_date}")
    
    # Get scores
    scores = db.query(ScoreDaily).filter(
        ScoreDaily.date == latest_date
    ).order_by(
        desc(ScoreDaily.final_score)
    ).all()
    
    print(f"Found {len(scores)} scores")
    
    # Try to convert first score
    if scores:
        score = scores[0]
        print(f"\nFirst score: {score.ticker}")
        print(f"  final_score: {score.final_score}")
        print(f"  base_score: {score.base_score}")
        print(f"  risk_penalty_factor: {score.risk_penalty_factor}")
        print(f"  risk_penalties: {score.risk_penalties}")
        print(f"  exclusion_reasons: {score.exclusion_reasons}")
        
        # Try conversion
        try:
            breakdown = _score_daily_to_score_breakdown(score)
            print(f"\nConversion successful!")
            print(f"  ScoreBreakdown: {breakdown}")
        except Exception as e:
            print(f"\nConversion failed: {e}")
            import traceback
            traceback.print_exc()
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
