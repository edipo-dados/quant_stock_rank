from app.models.database import SessionLocal
from app.models.schemas import FeatureMonthly, ScoreDaily
from datetime import date

session = SessionLocal()

# Get all scores
scores = session.query(ScoreDaily).filter(ScoreDaily.date == date(2026, 2, 18)).all()

print(f"Total scores: {len(scores)}")
print(f"Passed eligibility: {sum(1 for s in scores if s.passed_eligibility)}")
print(f"Failed eligibility: {sum(1 for s in scores if not s.passed_eligibility)}")

# Check a few examples
print("\nExamples of excluded assets:")
for score in scores[:5]:
    print(f"\n{score.ticker}:")
    print(f"  Passed: {score.passed_eligibility}")
    print(f"  Reasons: {score.exclusion_reasons}")
    
    # Get features
    features = session.query(FeatureMonthly).filter(
        FeatureMonthly.ticker == score.ticker
    ).first()
    
    if features:
        print(f"  ROE Mean 3Y: {features.roe_mean_3y}")
        print(f"  ROE Volatility: {features.roe_volatility}")
        print(f"  Debt/EBITDA Raw: {features.debt_to_ebitda_raw}")
        print(f"  Net Income Last Year: {features.net_income_last_year}")
        print(f"  Net Income History: {features.net_income_history}")

session.close()
