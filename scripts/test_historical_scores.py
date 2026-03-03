"""
Script de teste para verificar cálculo de scores históricos.
Testa uma única data para debug.
"""

import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from scripts.calculate_historical_scores import calculate_scores_for_date
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Testa cálculo de scores para uma data."""
    
    # Testar com data recente
    test_date = date(2024, 12, 31)
    
    logger.info("=" * 80)
    logger.info("TESTE DE CÁLCULO DE SCORES HISTÓRICOS")
    logger.info("=" * 80)
    logger.info(f"Data de teste: {test_date}")
    logger.info("")
    
    db = SessionLocal()
    
    try:
        result = calculate_scores_for_date(test_date, db)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("RESULTADO")
        logger.info("=" * 80)
        logger.info(f"Data: {result['date']}")
        logger.info(f"Scores calculados: {result['scores']}")
        logger.info(f"Pulado: {result.get('skipped', False)}")
        
        if 'error' in result:
            logger.error(f"Erro: {result['error']}")
            return 1
        
        logger.info("")
        logger.info("✓ Teste concluído com sucesso")
        return 0
        
    except Exception as e:
        logger.error(f"✗ Erro no teste: {e}", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
