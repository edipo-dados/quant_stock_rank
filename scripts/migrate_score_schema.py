"""
Database migration script to add enhanced scoring fields to ScoreDaily table.

This script adds the following columns:
- base_score: Score before risk penalties
- risk_penalty_factor: Combined penalty factor
- passed_eligibility: Whether asset passed eligibility filter
- exclusion_reasons: JSON list of exclusion reasons
- risk_penalties: JSON dict of individual penalties

Valida: Requirements 5.1, 5.2, 5.3, 5.5
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.models.database import engine, SessionLocal
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_score_schema():
    """
    Add new columns to scores_daily table for enhanced scoring.
    
    Handles existing data by setting default values for new columns.
    """
    logger.info("Starting database migration for ScoreDaily schema...")
    
    db = SessionLocal()
    
    try:
        # Check database type
        db_url = str(settings.database_url)
        is_sqlite = 'sqlite' in db_url.lower()
        
        logger.info(f"Database type: {'SQLite' if is_sqlite else 'PostgreSQL'}")
        
        # Check if columns already exist (database-agnostic way)
        if is_sqlite:
            # SQLite: Use PRAGMA table_info
            check_query = text("PRAGMA table_info(scores_daily)")
            result = db.execute(check_query)
            existing_columns = {row[1] for row in result}  # column name is at index 1
        else:
            # PostgreSQL: Use information_schema
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'scores_daily'
            """)
            result = db.execute(check_query)
            existing_columns = {row[0] for row in result}
        
        logger.info(f"Found {len(existing_columns)} existing columns in scores_daily")
        
        # Define migrations (SQLite-compatible)
        migrations = [
            {
                'column': 'base_score',
                'sql': 'ALTER TABLE scores_daily ADD COLUMN base_score FLOAT',
                'description': 'Add base_score column (score before penalties)'
            },
            {
                'column': 'risk_penalty_factor',
                'sql': 'ALTER TABLE scores_daily ADD COLUMN risk_penalty_factor FLOAT',
                'description': 'Add risk_penalty_factor column'
            },
            {
                'column': 'passed_eligibility',
                'sql': 'ALTER TABLE scores_daily ADD COLUMN passed_eligibility BOOLEAN DEFAULT 1' if is_sqlite else 'ALTER TABLE scores_daily ADD COLUMN passed_eligibility BOOLEAN DEFAULT TRUE',
                'description': 'Add passed_eligibility column'
            },
            {
                'column': 'exclusion_reasons',
                'sql': 'ALTER TABLE scores_daily ADD COLUMN exclusion_reasons TEXT' if is_sqlite else 'ALTER TABLE scores_daily ADD COLUMN exclusion_reasons JSON',
                'description': 'Add exclusion_reasons column (JSON/TEXT)'
            },
            {
                'column': 'risk_penalties',
                'sql': 'ALTER TABLE scores_daily ADD COLUMN risk_penalties TEXT' if is_sqlite else 'ALTER TABLE scores_daily ADD COLUMN risk_penalties JSON',
                'description': 'Add risk_penalties column (JSON/TEXT)'
            }
        ]
        
        # Execute migrations
        applied_count = 0
        skipped_count = 0
        
        for migration in migrations:
            column_name = migration['column']
            
            if column_name in existing_columns:
                logger.info(f"Column '{column_name}' already exists, skipping")
                skipped_count += 1
                continue
            
            logger.info(f"Applying migration: {migration['description']}")
            
            try:
                db.execute(text(migration['sql']))
                db.commit()
                logger.info(f"✓ Successfully added column '{column_name}'")
                applied_count += 1
            except Exception as e:
                logger.error(f"✗ Failed to add column '{column_name}': {e}")
                db.rollback()
                raise
        
        # Set default values for existing records
        if applied_count > 0:
            logger.info("Setting default values for existing records...")
            
            # Set passed_eligibility to TRUE for all existing records
            # (they were scored before the filter existed, so assume they passed)
            if is_sqlite:
                update_query = text("""
                    UPDATE scores_daily 
                    SET passed_eligibility = 1 
                    WHERE passed_eligibility IS NULL
                """)
            else:
                update_query = text("""
                    UPDATE scores_daily 
                    SET passed_eligibility = TRUE 
                    WHERE passed_eligibility IS NULL
                """)
            db.execute(update_query)
            db.commit()
            logger.info("✓ Set passed_eligibility=TRUE for existing records")
        
        logger.info(
            f"\nMigration complete: {applied_count} columns added, "
            f"{skipped_count} columns skipped (already exist)"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()


def verify_migration():
    """
    Verify that all new columns exist in the table.
    """
    logger.info("\nVerifying migration...")
    
    db = SessionLocal()
    
    try:
        # Check database type
        db_url = str(settings.database_url)
        is_sqlite = 'sqlite' in db_url.lower()
        
        if is_sqlite:
            # SQLite: Use PRAGMA table_info
            check_query = text("PRAGMA table_info(scores_daily)")
            result = db.execute(check_query)
            
            # Filter for new columns
            new_columns = ['base_score', 'risk_penalty_factor', 'passed_eligibility', 
                          'exclusion_reasons', 'risk_penalties']
            columns = [row for row in result if row[1] in new_columns]
            
            if len(columns) == 5:
                logger.info("✓ All 5 new columns verified:")
                for col in columns:
                    logger.info(f"  - {col[1]}: {col[2]} (nullable={col[3]})")
                return True
            else:
                logger.error(f"✗ Expected 5 columns, found {len(columns)}")
                return False
        else:
            # PostgreSQL: Use information_schema
            check_query = text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'scores_daily'
                AND column_name IN (
                    'base_score', 
                    'risk_penalty_factor', 
                    'passed_eligibility', 
                    'exclusion_reasons', 
                    'risk_penalties'
                )
                ORDER BY column_name
            """)
            
            result = db.execute(check_query)
            columns = list(result)
            
            if len(columns) == 5:
                logger.info("✓ All 5 new columns verified:")
                for col in columns:
                    logger.info(
                        f"  - {col[0]}: {col[1]} "
                        f"(nullable={col[2]}, default={col[3]})"
                    )
                return True
            else:
                logger.error(f"✗ Expected 5 columns, found {len(columns)}")
                return False
            
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("ScoreDaily Schema Migration")
    logger.info("=" * 60)
    
    # Run migration
    success = migrate_score_schema()
    
    if success:
        # Verify migration
        verified = verify_migration()
        
        if verified:
            logger.info("\n✓ Migration completed successfully!")
            sys.exit(0)
        else:
            logger.error("\n✗ Migration verification failed")
            sys.exit(1)
    else:
        logger.error("\n✗ Migration failed")
        sys.exit(1)
