#!/usr/bin/env python3
"""
Test adaptive history calculation directly.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schemas import RawFundamental
from app.factor_engine.fundamental_factors import FundamentalFactorCalculator

def test_adaptive_history():
    """Test adaptive history calculation for sample tickers."""
    db = next(get_db())
    calculator = FundamentalFactorCalculator()
    
    sample_tickers = ['VALE3.SA', 'TAEE11.SA', 'ITUB4.SA']
    
    for ticker in sample_tickers:
        print(f"\n{'='*80}")
        print(f"📊 Testing {ticker}")
        print(f"{'='*80}")
        
        # Get fundamentals history
        fundamentals_history_raw = db.query(RawFundamental).filter(
            RawFundamental.ticker == ticker
        ).order_by(RawFundamental.period_end_date.asc()).limit(5).all()
        
        print(f"Found {len(fundamentals_history_raw)} historical records")
        
        # Convert to dict format
        fundamentals_history = []
        for f in fundamentals_history_raw:
            fundamentals_history.append({
                'period_end_date': f.period_end_date,
                'revenue': f.revenue,
                'net_income': f.net_income,
                'shareholders_equity': f.shareholders_equity,
                'ebitda': f.ebitda,
                'total_assets': f.total_assets
            })
        
        print(f"\nHistory data:")
        for i, h in enumerate(fundamentals_history):
            print(f"  {i+1}. {h['period_end_date']}: net_income={h['net_income']}, equity={h['shareholders_equity']}")
        
        # Test calculate_roe_mean_3y
        print(f"\n🧪 Testing calculate_roe_mean_3y:")
        roe_mean, roe_conf = calculator.calculate_roe_mean_3y(fundamentals_history)
        print(f"  Result: roe_mean={roe_mean}, confidence={roe_conf}")
        
        # Test calculate_revenue_growth_3y
        print(f"\n🧪 Testing calculate_revenue_growth_3y:")
        rev_growth, rev_conf = calculator.calculate_revenue_growth_3y(fundamentals_history)
        print(f"  Result: revenue_growth={rev_growth}, confidence={rev_conf}")
        
        # Test calculate_roe_volatility
        print(f"\n🧪 Testing calculate_roe_volatility:")
        roe_vol, roe_vol_conf = calculator.calculate_roe_volatility(fundamentals_history)
        print(f"  Result: roe_volatility={roe_vol}, confidence={roe_vol_conf}")

if __name__ == "__main__":
    test_adaptive_history()
