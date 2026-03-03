"""
Script para calcular scores históricos point-in-time para backtest.

Calcula features e scores para cada data histórica usando APENAS
dados disponíveis até aquela data (evita look-ahead bias).
"""

import sys
from pathlib import Path
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import argparse
import pandas as pd
from typing import Dict
from sqlalchemy.orm import Session

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import (
    RawPriceDaily, RawFundamental, ScoreDaily, 
    FeatureDaily, FeatureMonthly, RankingHistory
)
from app.factor_engine.momentum_factors import MomentumFactorCalculator
from app.factor_engine.fundamental_factors import FundamentalFactorCalculator
from app.factor_engine.normalizer import CrossSectionalNormalizer
from app.factor_engine.missing_handler import MissingValueHandler
from app.scoring.scoring_engine import ScoringEngine
from app.scoring.ranker import Ranker
from app.filters.eligibility_filter import EligibilityFilter
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_scores_for_date(target_date: date, db: Session) -> Dict:
    """
    Calcula scores para uma data específica usando apenas dados disponíveis até aquela data.
    
    Args:
        target_date: Data para calcular scores
        db: Sessão do banco
        
    Returns:
        Dict com estatísticas
    """
    try:
        logger.info(f"Calculando scores para {target_date}...")
        
        # Verificar se já existem scores
        existing = db.query(ScoreDaily).filter(
            ScoreDaily.date == target_date
        ).count()
        
        if existing > 0:
            logger.info(f"  Já existem {existing} scores, pulando...")
            return {"date": target_date, "scores": existing, "skipped": True}
        
        # 1. Buscar tickers com dados até esta data
        tickers_query = db.query(RawPriceDaily.ticker).filter(
            RawPriceDaily.date <= target_date
        ).distinct().all()
        all_tickers = [t[0] for t in tickers_query]
        
        if not all_tickers:
            logger.warning(f"  Sem tickers disponíveis")
            return {"date": target_date, "scores": 0, "skipped": False}
        
        logger.info(f"  Total de tickers: {len(all_tickers)}")
        
        # 2. Filtro de elegibilidade estrutural
        from app.config import settings
        eligibility_filter = EligibilityFilter(settings)
        eligible_tickers = []
        
        for ticker in all_tickers:
            try:
                # Buscar fundamentos mais recentes até target_date
                latest_fundamental = db.query(RawFundamental).filter(
                    RawFundamental.ticker == ticker,
                    RawFundamental.period_end_date <= target_date,
                    RawFundamental.period_type == 'annual'
                ).order_by(RawFundamental.period_end_date.desc()).first()
                
                if not latest_fundamental:
                    continue
                
                # Buscar volume dos últimos 90 dias
                volume_data = db.query(RawPriceDaily).filter(
                    RawPriceDaily.ticker == ticker,
                    RawPriceDaily.date <= target_date
                ).order_by(RawPriceDaily.date.desc()).limit(90).all()
                
                if len(volume_data) < 60:  # Mínimo 60 dias
                    continue
                
                volume_df = pd.DataFrame([{
                    'date': v.date,
                    'volume': v.volume
                } for v in volume_data])
                
                # Preparar dados fundamentais
                fundamentals_dict = {
                    'shareholders_equity': latest_fundamental.shareholders_equity,
                    'ebitda': latest_fundamental.ebitda,
                    'revenue': latest_fundamental.revenue,
                    'net_income_last_year': latest_fundamental.net_income,
                    'net_income_history': [latest_fundamental.net_income],
                    'net_debt_to_ebitda': None  # Simplificado
                }
                
                # Verificar elegibilidade
                is_eligible, reasons = eligibility_filter.is_eligible(
                    ticker, fundamentals_dict, volume_df
                )
                
                if is_eligible:
                    eligible_tickers.append(ticker)
                    
            except Exception as e:
                logger.debug(f"  Erro elegibilidade {ticker}: {e}")
                continue
        
        logger.info(f"  Elegíveis: {len(eligible_tickers)}")
        
        if len(eligible_tickers) == 0:
            logger.warning(f"  Nenhum ticker elegível")
            return {"date": target_date, "scores": 0, "skipped": False}
        
        # 3. Calcular features de momentum
        momentum_calculator = MomentumFactorCalculator()
        momentum_factors = {}
        
        for ticker in eligible_tickers:
            try:
                # Buscar preços até target_date
                prices = db.query(RawPriceDaily).filter(
                    RawPriceDaily.ticker == ticker,
                    RawPriceDaily.date <= target_date
                ).order_by(RawPriceDaily.date).all()
                
                if len(prices) < 252:  # Mínimo 1 ano
                    continue
                
                prices_df = pd.DataFrame([{
                    'date': p.date,
                    'close': p.close,
                    'adj_close': p.adj_close
                } for p in prices])
                
                factors = momentum_calculator.calculate_all_factors(ticker, prices_df)
                momentum_factors[ticker] = factors
                
            except Exception as e:
                logger.debug(f"  Erro momentum {ticker}: {e}")
                continue
        
        logger.info(f"  Momentum: {len(momentum_factors)} calculados")
        
        # 4. Calcular features fundamentalistas
        fundamental_calculator = FundamentalFactorCalculator()
        fundamental_factors = {}
        
        for ticker in eligible_tickers:
            try:
                # Buscar fundamentos até target_date
                fundamentals = db.query(RawFundamental).filter(
                    RawFundamental.ticker == ticker,
                    RawFundamental.period_end_date <= target_date,
                    RawFundamental.period_type == 'annual'
                ).order_by(RawFundamental.period_end_date.desc()).limit(5).all()
                
                if not fundamentals:
                    continue
                
                latest = fundamentals[0]
                
                # Buscar preço na data
                latest_price = db.query(RawPriceDaily).filter(
                    RawPriceDaily.ticker == ticker,
                    RawPriceDaily.date <= target_date
                ).order_by(RawPriceDaily.date.desc()).first()
                
                if not latest_price:
                    continue
                
                fundamentals_data = {
                    'net_income': latest.net_income,
                    'shareholders_equity': latest.shareholders_equity,
                    'revenue': latest.revenue,
                    'ebitda': latest.ebitda,
                    'total_debt': latest.total_debt,
                    'cash': 0.0,
                    'eps': latest.eps,
                    'enterprise_value': latest.enterprise_value,
                    'book_value_per_share': latest.book_value_per_share,
                    'total_assets': latest.total_assets
                }
                
                fundamentals_history = [{
                    'period_end_date': f.period_end_date,
                    'revenue': f.revenue,
                    'net_income': f.net_income,
                    'shareholders_equity': f.shareholders_equity,
                    'ebitda': f.ebitda,
                    'total_assets': f.total_assets
                } for f in fundamentals]
                
                factors = fundamental_calculator.calculate_all_factors(
                    ticker=ticker,
                    fundamentals_data=fundamentals_data,
                    fundamentals_history=fundamentals_history,
                    current_price=latest_price.close
                )
                fundamental_factors[ticker] = factors
                
            except Exception as e:
                logger.debug(f"  Erro fundamental {ticker}: {e}")
                continue
        
        logger.info(f"  Fundamentais: {len(fundamental_factors)} calculados")
        
        # 5. Combinar fatores
        all_factors = {}
        for ticker in eligible_tickers:
            combined = {}
            if ticker in momentum_factors:
                combined.update(momentum_factors[ticker])
            if ticker in fundamental_factors:
                combined.update(fundamental_factors[ticker])
            
            if combined:
                all_factors[ticker] = combined
        
        if not all_factors:
            logger.warning(f"  Nenhum fator calculado")
            return {"date": target_date, "scores": 0, "skipped": False}
        
        # 6. Imputar missing values
        missing_handler = MissingValueHandler()
        factors_df = pd.DataFrame(all_factors).T
        factors_df = missing_handler.impute_missing_features(factors_df)
        
        # 7. Normalizar
        normalizer = CrossSectionalNormalizer()
        
        # Separar confidence factors
        confidence_cols = ['roe_mean_3y_confidence', 'roe_volatility_confidence',
                          'revenue_growth_3y_confidence', 'net_income_volatility_confidence',
                          'overall_confidence']
        
        numeric_cols = [col for col in factors_df.columns 
                       if col not in confidence_cols and factors_df[col].dtype in ['float64', 'int64']]
        
        normalized_df = normalizer.normalize_factors(factors_df, numeric_cols)
        
        # Adicionar confidence factors de volta
        for col in confidence_cols:
            if col in factors_df.columns:
                normalized_df[col] = factors_df[col]
        
        # 8. Calcular scores
        scoring_engine = ScoringEngine()
        scores = []
        
        for ticker in normalized_df.index:
            try:
                factors = normalized_df.loc[ticker].to_dict()
                
                # Separar fatores de momentum e fundamentais
                momentum_keys = ['momentum_6m_ex_1m', 'momentum_12m_ex_1m', 'volatility_90d', 'recent_drawdown']
                fundamental_keys = [k for k in factors.keys() if k not in momentum_keys and not k.endswith('_confidence')]
                
                momentum_factors = {k: factors[k] for k in momentum_keys if k in factors}
                fundamental_factors = {k: factors[k] for k in fundamental_keys if k in factors}
                
                # Calcular confidence
                confidence = factors.get('overall_confidence', 1.0)
                
                # Calcular score usando score_asset
                score_result = scoring_engine.score_asset(
                    ticker=ticker,
                    fundamental_factors=fundamental_factors,
                    momentum_factors=momentum_factors,
                    confidence=confidence
                )
                
                scores.append({
                    'ticker': ticker,
                    'final_score': score_result.final_score,
                    'momentum_score': score_result.momentum_score,
                    'quality_score': score_result.quality_score,
                    'value_score': score_result.value_score,
                    'confidence': score_result.confidence
                })
            except Exception as e:
                logger.debug(f"  Erro score {ticker}: {e}")
                continue
        
        if not scores:
            logger.warning(f"  Nenhum score calculado")
            return {"date": target_date, "scores": 0, "skipped": False}
        
        # 9. Ranking
        ranker = Ranker()
        scores_df = pd.DataFrame(scores)
        ranked_df = ranker.rank_assets(scores_df)
        
        # 10. Salvar scores
        for _, row in ranked_df.iterrows():
            score_record = ScoreDaily(
                ticker=row['ticker'],
                date=target_date,
                final_score=row['final_score'],
                momentum_score=row['momentum_score'],
                quality_score=row['quality_score'],
                value_score=row['value_score'],
                confidence=row['confidence'],
                rank=row['rank']
            )
            db.add(score_record)
        
        db.commit()
        
        logger.info(f"  ✓ {len(scores)} scores salvos")
        
        return {"date": target_date, "scores": len(scores), "skipped": False}
        
    except Exception as e:
        logger.error(f"  ✗ Erro: {e}")
        db.rollback()
        return {"date": target_date, "scores": 0, "skipped": False, "error": str(e)}


def main():
    """Calcula scores históricos."""
    
    parser = argparse.ArgumentParser(
        description='Calculate historical scores for backtest'
    )
    parser.add_argument(
        '--start',
        type=str,
        required=True,
        help='Start date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end',
        type=str,
        required=True,
        help='End date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--frequency',
        type=str,
        default='monthly',
        choices=['monthly'],
        help='Frequency (only monthly supported)'
    )
    
    args = parser.parse_args()
    
    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)
    
    logger.info("=" * 80)
    logger.info("CÁLCULO DE SCORES HISTÓRICOS")
    logger.info("=" * 80)
    logger.info(f"Período: {start_date} a {end_date}")
    logger.info("")
    
    # Gerar datas mensais (último dia útil)
    dates = []
    current = start_date
    
    while current <= end_date:
        # Último dia do mês
        next_month = current + relativedelta(months=1)
        last_day = (next_month - timedelta(days=1))
        
        if last_day <= end_date:
            dates.append(last_day)
        
        current = next_month
    
    logger.info(f"Total de datas: {len(dates)}")
    logger.info("")
    
    # Processar cada data
    db = SessionLocal()
    results = []
    
    try:
        for i, target_date in enumerate(dates, 1):
            logger.info(f"[{i}/{len(dates)}] {target_date}")
            result = calculate_scores_for_date(target_date, db)
            results.append(result)
    finally:
        db.close()
    
    # Resumo
    total_scores = sum(r['scores'] for r in results)
    skipped = sum(1 for r in results if r.get('skipped', False))
    errors = sum(1 for r in results if 'error' in r)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("RESUMO")
    logger.info("=" * 80)
    logger.info(f"Datas processadas: {len(dates)}")
    logger.info(f"Datas puladas: {skipped}")
    logger.info(f"Erros: {errors}")
    logger.info(f"Total de scores: {total_scores}")
    logger.info("=" * 80)
    
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
