#!/usr/bin/env python3
"""
Check latest scores for specific tickers.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schemas import ScoreDaily, FeatureMonthly
from datetime import datetime

def check_latest_scores():
    """Check latest scores for sample tickers."""
    db = next(get_db())
    
    sample_tickers = ['VALE3.SA', 'ITUB4.SA', 'BBAS3.SA', 'BBDC4.SA', 'BPAC11.SA']
    
    print(f"{'='*80}")
    print(f"📊 LATEST SCORES (2026-02-26)")
    print(f"{'='*80}\n")
    
    for ticker in sample_tickers:
        # Get latest score
        score = db.query(ScoreDaily).filter(
            ScoreDaily.ticker == ticker,
            ScoreDaily.date == datetime(2026, 2, 26).date()
        ).first()
        
        # Get latest features
        feature = db.query(FeatureMonthly).filter(
            FeatureMonthly.ticker == ticker,
            FeatureMonthly.month == datetime(2026, 2, 1).date()
        ).first()
        
        print(f"{ticker}:")
        if feature:
            print(f"  Features:")
            print(f"    roe_mean_3y: {feature.roe_mean_3y}")
            print(f"    roe_mean_3y_confidence: {feature.roe_mean_3y_confidence}")
            print(f"    revenue_growth_3y: {feature.revenue_growth_3y}")
            print(f"    net_margin: {feature.net_margin}")
            print(f"    overall_confidence: {feature.overall_confidence}")
        
        if score:
            print(f"  Scores:")
            print(f"    quality_score: {score.quality_score}")
            print(f"    value_score: {score.value_score}")
            print(f"    momentum_score: {score.momentum_score}")
            print(f"    final_score: {score.final_score}")
            print(f"    rank: {score.rank}")
        else:
            print(f"  ❌ No score found")
        
        print()

if __name__ == "__main__":
    check_latest_scores()
