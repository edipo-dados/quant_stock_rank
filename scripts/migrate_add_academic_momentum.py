"""
Script de migração para adicionar colunas de momentum acadêmico.

Adiciona as seguintes colunas à tabela features_daily:
- return_1m: Retorno de 1 mês
- momentum_6m_ex_1m: Momentum de 6 meses excluindo último mês
- momentum_12m_ex_1m: Momentum de 12 meses excluindo último mês
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


def migrate_add_academic_momentum():
    """
    Adiciona colunas de momentum acadêmico à tabela features_daily.
    """
    logger.info("Starting migration: add academic momentum columns")
    
    db = SessionLocal()
    
    try:
        # Verificar se as colunas já existem
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'features_daily' 
            AND column_name IN ('return_1m', 'momentum_6m_ex_1m', 'momentum_12m_ex_1m')
        """)
        
        existing_columns = [row[0] for row in db.execute(check_query)]
        logger.info(f"Existing columns: {existing_columns}")
        
        # Adicionar colunas que não existem
        columns_to_add = {
            'return_1m': 'DOUBLE PRECISION',
            'momentum_6m_ex_1m': 'DOUBLE PRECISION',
            'momentum_12m_ex_1m': 'DOUBLE PRECISION'
        }
        
        for column_name, column_type in columns_to_add.items():
            if column_name not in existing_columns:
                logger.info(f"Adding column: {column_name}")
                alter_query = text(f"""
                    ALTER TABLE features_daily 
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
    migrate_add_academic_momentum()
