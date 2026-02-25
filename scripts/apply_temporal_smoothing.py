"""
Script para aplicar suavização temporal aos scores.

Aplica suavização exponencial aos scores diários:
final_score_smoothed = 0.7 * score_current + 0.3 * score_previous
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import argparse

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.scoring.temporal_smoothing import TemporalSmoothing
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Aplica suavização temporal aos scores."""
    
    parser = argparse.ArgumentParser(description='Apply temporal smoothing to scores')
    parser.add_argument(
        '--date',
        type=str,
        help='Date to process (YYYY-MM-DD). Default: today'
    )
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.7,
        help='Smoothing alpha (0-1). Default: 0.7'
    )
    parser.add_argument(
        '--lookback-days',
        type=int,
        default=30,
        help='Days to look back for previous score. Default: 30'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all dates with scores'
    )
    
    args = parser.parse_args()
    
    # Determinar data
    if args.date:
        target_date = date.fromisoformat(args.date)
    else:
        target_date = date.today()
    
    logger.info("=" * 80)
    logger.info("TEMPORAL SMOOTHING")
    logger.info("=" * 80)
    logger.info(f"Alpha: {args.alpha}")
    logger.info(f"Lookback days: {args.lookback_days}")
    
    db = SessionLocal()
    smoother = TemporalSmoothing(alpha=args.alpha)
    
    try:
        if args.all:
            # Processar todas as datas
            from app.models.schemas import ScoreDaily
            from sqlalchemy import func
            
            # Obter todas as datas com scores
            dates = db.query(func.distinct(ScoreDaily.date)).order_by(ScoreDaily.date).all()
            dates = [d[0] for d in dates]
            
            logger.info(f"Processing {len(dates)} dates...")
            
            total_updated = 0
            for process_date in dates:
                updated = smoother.update_smoothed_scores(
                    db,
                    process_date,
                    args.lookback_days
                )
                total_updated += updated
            
            logger.info(f"Total scores updated: {total_updated}")
        else:
            # Processar data específica
            logger.info(f"Processing date: {target_date}")
            
            updated = smoother.update_smoothed_scores(
                db,
                target_date,
                args.lookback_days
            )
            
            logger.info(f"Scores updated: {updated}")
        
        logger.info("=" * 80)
        logger.info("SMOOTHING COMPLETED")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
