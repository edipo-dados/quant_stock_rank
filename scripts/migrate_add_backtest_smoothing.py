"""
Migração: Adicionar suporte para backtest e suavização temporal.

Adiciona:
1. Coluna final_score_smoothed em scores_daily
2. Tabela ranking_history para snapshots mensais
3. Tabela backtest_results para resultados de backtests
"""

import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.models.database import engine, SessionLocal
from app.models.schemas import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """Executa migração do banco de dados."""
    
    db = SessionLocal()
    
    try:
        logger.info("Starting migration: backtest and temporal smoothing support")
        
        # 1. Adicionar coluna final_score_smoothed em scores_daily
        logger.info("Adding final_score_smoothed column to scores_daily...")
        try:
            db.execute(text("""
                ALTER TABLE scores_daily 
                ADD COLUMN final_score_smoothed FLOAT
            """))
            db.commit()
            logger.info("✓ Added final_score_smoothed column")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e).lower():
                logger.info("✓ Column final_score_smoothed already exists")
                db.rollback()
            else:
                raise
        
        # 2. Criar tabela ranking_history
        logger.info("Creating ranking_history table...")
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS ranking_history (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    ticker VARCHAR(10) NOT NULL,
                    final_score FLOAT NOT NULL,
                    final_score_smoothed FLOAT,
                    momentum_score FLOAT NOT NULL,
                    quality_score FLOAT NOT NULL,
                    value_score FLOAT NOT NULL,
                    rank INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    CONSTRAINT uix_date_ticker_history UNIQUE (date, ticker)
                )
            """))
            db.commit()
            logger.info("✓ Created ranking_history table")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("✓ Table ranking_history already exists")
                db.rollback()
            else:
                raise
        
        # 3. Criar índices para ranking_history
        logger.info("Creating indexes for ranking_history...")
        try:
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_date_rank_history 
                ON ranking_history (date, rank)
            """))
            db.commit()
            logger.info("✓ Created indexes for ranking_history")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
            db.rollback()
        
        # 4. Criar tabela backtest_results
        logger.info("Creating backtest_results table...")
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS backtest_results (
                    id SERIAL PRIMARY KEY,
                    backtest_name VARCHAR(100) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    top_n INTEGER NOT NULL,
                    rebalance_frequency VARCHAR(20) NOT NULL,
                    weight_method VARCHAR(20) NOT NULL,
                    use_smoothing BOOLEAN DEFAULT FALSE,
                    total_return FLOAT,
                    cagr FLOAT,
                    volatility FLOAT,
                    sharpe_ratio FLOAT,
                    max_drawdown FLOAT,
                    avg_turnover FLOAT,
                    num_rebalances INTEGER,
                    num_trades INTEGER,
                    win_rate FLOAT,
                    monthly_returns JSON,
                    portfolio_history JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    config_snapshot JSON
                )
            """))
            db.commit()
            logger.info("✓ Created backtest_results table")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("✓ Table backtest_results already exists")
                db.rollback()
            else:
                raise
        
        # 5. Criar índices para backtest_results
        logger.info("Creating indexes for backtest_results...")
        try:
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_backtest_name_date 
                ON backtest_results (backtest_name, start_date, end_date)
            """))
            db.commit()
            logger.info("✓ Created indexes for backtest_results")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
            db.rollback()
        
        logger.info("=" * 80)
        logger.info("Migration completed successfully!")
        logger.info("=" * 80)
        logger.info("\nNew features available:")
        logger.info("1. Temporal smoothing: final_score_smoothed column in scores_daily")
        logger.info("2. Ranking history: ranking_history table for monthly snapshots")
        logger.info("3. Backtest results: backtest_results table for performance metrics")
        logger.info("\nNext steps:")
        logger.info("- Run temporal smoothing: python scripts/apply_temporal_smoothing.py")
        logger.info("- Run backtest: python scripts/run_backtest.py")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
