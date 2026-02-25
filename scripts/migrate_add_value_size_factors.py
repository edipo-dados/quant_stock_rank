"""
Script de migração para adicionar colunas de VALUE expandido e SIZE.

Adiciona as seguintes colunas à tabela features_monthly:
- price_to_book: Price-to-Book usando market cap
- fcf_yield: Free Cash Flow Yield
- size_factor: -log(market_cap) para size premium
"""

import sys
import os
import logging
from sqlalchemy import text

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_add_value_size_factors():
    """
    Adiciona colunas de VALUE expandido e SIZE à tabela features_monthly.
    """
    logger.info("Starting migration: add VALUE and SIZE factor columns")
    
    db = SessionLocal()
    
    try:
        # Verificar se as colunas já existem
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'features_monthly' 
            AND column_name IN ('price_to_book', 'fcf_yield', 'size_factor')
        """)
        
        existing_columns = [row[0] for row in db.execute(check_query)]
        logger.info(f"Existing columns: {existing_columns}")
        
        # Adicionar colunas que não existem
        columns_to_add = {
            'price_to_book': 'DOUBLE PRECISION',
            'fcf_yield': 'DOUBLE PRECISION',
            'size_factor': 'DOUBLE PRECISION'
        }
        
        for column_name, column_type in columns_to_add.items():
            if column_name not in existing_columns:
                logger.info(f"Adding column: {column_name}")
                alter_query = text(f"""
                    ALTER TABLE features_monthly 
                    ADD COLUMN {column_name} {column_type}
                """)
                db.execute(alter_query)
                db.commit()
                logger.info(f"Column {column_name} added successfully")
            else:
                logger.info(f"Column {column_name} already exists, skipping")
        
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_add_value_size_factors()
