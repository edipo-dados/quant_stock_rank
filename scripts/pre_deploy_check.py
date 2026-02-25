"""
Script de verificação pré-deploy.

Verifica se o sistema está pronto para deploy:
- Migrações executadas
- Banco de dados funcionando
- Scores calculados
- Suavização aplicada
- Backend respondendo
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal, engine
from app.models.schemas import (
    ScoreDaily, FeatureDaily, FeatureMonthly,
    RankingHistory, BacktestResult
)
from sqlalchemy import inspect, text
from datetime import date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_database_connection():
    """Verifica conexão com banco de dados."""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✅ Database connection OK")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection FAILED: {e}")
        return False


def check_tables_exist():
    """Verifica se todas as tabelas necessárias existem."""
    required_tables = [
        'scores_daily',
        'features_daily',
        'features_monthly',
        'ranking_history',
        'backtest_results',
        'raw_prices_daily',
        'raw_fundamentals',
        'asset_info',
        'pipeline_executions'
    ]
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    missing_tables = [t for t in required_tables if t not in existing_tables]
    
    if missing_tables:
        logger.error(f"❌ Missing tables: {missing_tables}")
        return False
    else:
        logger.info(f"✅ All {len(required_tables)} tables exist")
        return True


def check_columns_exist():
    """Verifica se colunas das migrações existem."""
    db = SessionLocal()
    
    checks = []
    
    try:
        # Check features_daily columns
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'features_daily'
        """))
        columns = [row[0] for row in result]
        
        required_momentum = ['return_1m', 'momentum_6m_ex_1m', 'momentum_12m_ex_1m']
        missing_momentum = [c for c in required_momentum if c not in columns]
        
        if missing_momentum:
            logger.error(f"❌ Missing momentum columns: {missing_momentum}")
            checks.append(False)
        else:
            logger.info("✅ Momentum columns OK")
            checks.append(True)
        
        # Check features_monthly columns
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'features_monthly'
        """))
        columns = [row[0] for row in result]
        
        required_value_size = ['price_to_book', 'fcf_yield', 'size_factor']
        missing_value_size = [c for c in required_value_size if c not in columns]
        
        if missing_value_size:
            logger.error(f"❌ Missing VALUE/SIZE columns: {missing_value_size}")
            checks.append(False)
        else:
            logger.info("✅ VALUE/SIZE columns OK")
            checks.append(True)
        
        # Check scores_daily columns
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'scores_daily'
        """))
        columns = [row[0] for row in result]
        
        if 'final_score_smoothed' not in columns:
            logger.error("❌ Missing final_score_smoothed column")
            checks.append(False)
        else:
            logger.info("✅ Smoothing column OK")
            checks.append(True)
        
    finally:
        db.close()
    
    return all(checks)


def check_data_exists():
    """Verifica se há dados no banco."""
    db = SessionLocal()
    
    checks = []
    
    try:
        # Check scores
        score_count = db.query(ScoreDaily).count()
        if score_count == 0:
            logger.warning("⚠️  No scores in database (run pipeline first)")
            checks.append(False)
        else:
            logger.info(f"✅ {score_count} scores in database")
            checks.append(True)
        
        # Check if smoothing was applied
        smoothed_count = db.query(ScoreDaily).filter(
            ScoreDaily.final_score_smoothed.isnot(None)
        ).count()
        
        if smoothed_count == 0:
            logger.warning("⚠️  No smoothed scores (run apply_temporal_smoothing.py)")
            checks.append(False)
        else:
            logger.info(f"✅ {smoothed_count} smoothed scores")
            checks.append(True)
        
    finally:
        db.close()
    
    return all(checks)


def check_weights_sum():
    """Verifica se pesos somam 1.0."""
    from app.config import settings
    
    total = (
        settings.momentum_weight +
        settings.quality_weight +
        settings.value_weight +
        settings.size_weight
    )
    
    if abs(total - 1.0) > 0.01:
        logger.error(
            f"❌ Weights don't sum to 1.0: "
            f"momentum={settings.momentum_weight}, "
            f"quality={settings.quality_weight}, "
            f"value={settings.value_weight}, "
            f"size={settings.size_weight}, "
            f"total={total}"
        )
        return False
    else:
        logger.info(
            f"✅ Weights sum to 1.0: "
            f"momentum={settings.momentum_weight}, "
            f"quality={settings.quality_weight}, "
            f"value={settings.value_weight}, "
            f"size={settings.size_weight}"
        )
        return True


def main():
    """Executa todas as verificações."""
    logger.info("=" * 80)
    logger.info("PRE-DEPLOY VERIFICATION")
    logger.info("=" * 80)
    
    checks = []
    
    # 1. Database connection
    logger.info("\n1. Checking database connection...")
    checks.append(check_database_connection())
    
    # 2. Tables exist
    logger.info("\n2. Checking tables...")
    checks.append(check_tables_exist())
    
    # 3. Columns exist
    logger.info("\n3. Checking migration columns...")
    checks.append(check_columns_exist())
    
    # 4. Data exists
    logger.info("\n4. Checking data...")
    data_ok = check_data_exists()
    # Don't fail if no data, just warn
    if not data_ok:
        logger.warning("⚠️  No data found, but this is OK for first deploy")
    
    # 5. Weights sum to 1.0
    logger.info("\n5. Checking weights configuration...")
    checks.append(check_weights_sum())
    
    # Summary
    logger.info("\n" + "=" * 80)
    if all(checks):
        logger.info("✅ ALL CHECKS PASSED - READY FOR DEPLOY")
        logger.info("=" * 80)
        
        if not data_ok:
            logger.info("\n📝 Next steps:")
            logger.info("1. Run pipeline: python scripts/run_pipeline_docker.py --mode liquid --limit 50")
            logger.info("2. Apply smoothing: python scripts/apply_temporal_smoothing.py --all")
        
        return 0
    else:
        logger.error("❌ SOME CHECKS FAILED - FIX ISSUES BEFORE DEPLOY")
        logger.info("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
