"""
Script de migração para adicionar coluna calmar_ratio na tabela backtest_metrics.

Uso:
    python scripts/migrate_add_calmar_ratio.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from sqlalchemy import text
from app.models.database import engine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def add_calmar_ratio_column():
    """
    Adiciona coluna calmar_ratio na tabela backtest_metrics.
    """
    logger.info("=" * 80)
    logger.info("MIGRAÇÃO: ADICIONAR COLUNA CALMAR_RATIO")
    logger.info("=" * 80)
    
    # SQL para adicionar a coluna
    add_column_sql = """
    ALTER TABLE backtest_metrics 
    ADD COLUMN IF NOT EXISTS calmar_ratio FLOAT;
    """
    
    try:
        with engine.connect() as conn:
            # Executar SQL
            conn.execute(text(add_column_sql))
            conn.commit()
        
        logger.info("✓ Coluna calmar_ratio adicionada com sucesso")
        logger.info("")
        return True
        
    except Exception as e:
        logger.error(f"✗ Erro ao adicionar coluna: {e}")
        return False


def main():
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 20 + "MIGRAÇÃO: ADICIONAR CALMAR RATIO" + " " * 26 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("")
    
    success = add_calmar_ratio_column()
    
    if success:
        logger.info("")
        logger.info("╔" + "=" * 78 + "╗")
        logger.info("║" + " " * 25 + "MIGRAÇÃO CONCLUÍDA" + " " * 35 + "║")
        logger.info("╚" + "=" * 78 + "╝")
        logger.info("")
        logger.info("A coluna calmar_ratio foi adicionada à tabela backtest_metrics.")
        logger.info("Novos backtests agora incluirão o Calmar Ratio.")
        logger.info("")
    else:
        logger.error("")
        logger.error("╔" + "=" * 78 + "╗")
        logger.error("║" + " " * 27 + "MIGRAÇÃO FALHOU" + " " * 36 + "║")
        logger.error("╚" + "=" * 78 + "╝")
        logger.error("")
        sys.exit(1)


if __name__ == "__main__":
    main()
