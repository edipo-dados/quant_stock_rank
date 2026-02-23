"""
Script to recalculate scores using existing features.
"""

from app.models.database import SessionLocal
from app.scoring.scoring_engine import ScoringEngine
from app.scoring.score_service import ScoreService
from app.factor_engine.feature_service import FeatureService
from datetime import date
from app.config import settings
from sqlalchemy import text

def main():
    db = SessionLocal()
    
    try:
        feature_service = FeatureService(db)
        scoring_engine = ScoringEngine(settings)
        score_service = ScoreService(db)
        
        score_date = date.today()
        month_start = date(score_date.year, score_date.month, 1)
        
        # Get all tickers with features
        result = db.execute(text('SELECT DISTINCT ticker FROM features_monthly'))
        tickers = [row[0] for row in result.fetchall()]
        
        print(f'Recalculating scores for {len(tickers)} tickers...')
        
        success = 0
        failed = 0
        
        for ticker in tickers:
            try:
                # Get features
                daily_features = feature_service.get_daily_features(ticker, score_date)
                monthly_features = feature_service.get_monthly_features(ticker, month_start)
                
                if not daily_features or not monthly_features:
                    print(f'[AVISO] Missing features for {ticker}')
                    failed += 1
                    continue
                
                # Prepare factors
                momentum_factors = {
                    'return_6m': daily_features.return_6m,
                    'return_12m': daily_features.return_12m,
                    'rsi_14': daily_features.rsi_14,
                    'volatility_90d': daily_features.volatility_90d,
                    'recent_drawdown': daily_features.recent_drawdown
                }
                
                fundamental_factors = {
                    'roe': monthly_features.roe,
                    'net_margin': monthly_features.net_margin,
                    'revenue_growth_3y': monthly_features.revenue_growth_3y,
                    'debt_to_ebitda': monthly_features.debt_to_ebitda,
                    'pe_ratio': monthly_features.pe_ratio,
                    'ev_ebitda': monthly_features.ev_ebitda,
                    'pb_ratio': monthly_features.pb_ratio
                }
                
                # Calculate score
                score_result = scoring_engine.score_asset(
                    ticker,
                    fundamental_factors,
                    momentum_factors
                )
                
                score_result.passed_eligibility = True
                score_result.exclusion_reasons = []
                score_result.confidence = 0.5
                
                # Save score
                score_service.save_score(score_result, score_date)
                
                success += 1
                print(f'[OK] {ticker}: {score_result.final_score:.4f}')
                
            except Exception as e:
                print(f'[ERRO] {ticker}: {e}')
                failed += 1
                continue
        
        # Update ranks
        print(f'\nUpdating ranks...')
        score_service.update_ranks(score_date)
        
        print(f'\n[OK] Recalculated {success} scores, {failed} failed')
        
    finally:
        db.close()

if __name__ == '__main__':
    main()
