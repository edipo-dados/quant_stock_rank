#!/usr/bin/env python3
"""
Test quality score calculation directly.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.scoring.scoring_engine import ScoringEngine
from app.models.database import get_db
from app.models.schemas import FeatureMonthly
from datetime import datetime

def test_quality_score():
    """Test quality score calculation."""
    db = next(get_db())
    engine = ScoringEngine()
    
    sample_tickers = ['VALE3.SA', 'ITUB4.SA', 'BBAS3.SA']
    
    for ticker in sample_tickers:
        print(f"\n{'='*80}")
        print(f"📊 Testing {ticker}")
        print(f"{'='*80}")
        
        # Get latest features
        feature = db.query(FeatureMonthly).filter(
            FeatureMonthly.ticker == ticker,
            FeatureMonthly.month == datetime(2026, 2, 1).date()
        ).first()
        
        if not feature:
            print(f"❌ No features found")
            continue
        
        # Prepare factors dict
        factors = {
            'roe_mean_3y': feature.roe_mean_3y,
            'roe_volatility': feature.roe_volatility,
            'net_margin': feature.net_margin,
            'revenue_growth_3y': feature.revenue_growth_3y,
            'debt_to_ebitda': feature.debt_to_ebitda,
            'overall_confidence': feature.overall_confidence
        }
        
        print(f"\nInput factors:")
        for k, v in factors.items():
            print(f"  {k}: {v}")
        
        # Calculate quality score
        quality_score = engine.calculate_quality_score(factors)
        
        print(f"\n✅ Quality score: {quality_score}")

if __name__ == "__main__":
    test_quality_score()
