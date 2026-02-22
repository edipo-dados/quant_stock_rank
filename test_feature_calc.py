import sys
from datetime import date, timedelta
from app.models.database import SessionLocal
from app.factor_engine.feature_service import FeatureService
from app.factor_engine.fundamental_factors import FundamentalFactorCalculator
from app.factor_engine.momentum_factors import MomentumFactorCalculator

# Test feature calculation for one ticker
ticker = "ITUB4.SA"
reference_date = date(2026, 2, 18)

session = SessionLocal()
feature_service = FeatureService(session)
fundamental_calc = FundamentalFactorCalculator()
momentum_calc = MomentumFactorCalculator()

print(f"Testing feature calculation for {ticker}")
print(f"Reference date: {reference_date}")

try:
    # Calculate fundamental factors
    print("\n1. Calculating fundamental factors...")
    fundamentals = feature_service.get_fundamentals_for_ticker(ticker, reference_date)
    print(f"Fundamentals data: {fundamentals}")
    
    if fundamentals:
        print("\n2. Calculating factors...")
        factors = fundamental_calc.calculate_all_factors(ticker, fundamentals, reference_date)
        print(f"Factors calculated: {list(factors.keys())}")
        print(f"ROE Mean 3Y: {factors.get('roe_mean_3y')}")
        print(f"ROE Volatility: {factors.get('roe_volatility')}")
        print(f"Debt/EBITDA Raw: {factors.get('debt_to_ebitda_raw')}")
        print(f"Net Income Last Year: {factors.get('net_income_last_year')}")
        print(f"Net Income History: {factors.get('net_income_history')}")
        
        print("\n3. Saving monthly features...")
        month = date(reference_date.year, reference_date.month, 1)
        result = feature_service.save_monthly_features(ticker, month, factors)
        print(f"Saved: {result}")
    else:
        print("No fundamentals data found!")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
