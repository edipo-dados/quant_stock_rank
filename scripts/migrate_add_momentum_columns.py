"""
Script de migração para adicionar novas colunas de momentum acadêmico.

Adiciona as seguintes colunas à tabela features_daily:
- return_1m: Retorno de 1 mês
- momentum_6m_ex_1m: Momentum 6m excluindo último mês
- momentum_12m_ex_1m: Momentum 12m excluindo último mês

Uso:
    python scripts/migrate_add_momentum_columns.py
"""

import sys
import os
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy import text
from app.models.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_add_momentum_columns():
    """
    Adiciona novas colunas de momentum acadêmico à tabela features_daily.
    """
    logger.info("Iniciando migração: Adicionando colunas de momentum acadêmico")
    
    migrations = [
        {
            "name": "return_1m",
            "sql": "ALTER TABLE features_daily ADD COLUMN IF NOT EXISTS return_1m FLOAT"
        },
        {
            "name": "momentum_6m_ex_1m",
            "sql": "ALTER TABLE features_daily ADD COLUMN IF NOT EXISTS momentum_6m_ex_1m FLOAT"
        },
        {
            "name": "momentum_12m_ex_1m",
            "sql": "ALTER TABLE features_daily ADD COLUMN IF NOT EXISTS momentum_12m_ex_1m FLOAT"
        }
    ]
    
    try:
        with engine.connect() as conn:
            for migration in migrations:
                logger.info(f"Adicionando coluna: {migration['name']}")
                conn.execute(text(migration['sql']))
                conn.commit()
                logger.info(f"✅ Coluna {migration['name']} adicionada com sucesso")
        
        logger.info("✅ Migração concluída com sucesso!")
        logger.info("")
        logger.info("PRÓXIMOS PASSOS:")
        logger.info("1. Execute o pipeline para calcular os novos fatores:")
        logger.info("   docker exec -it quant_backend python scripts/run_pipeline_docker.py")
        logger.info("")
        logger.info("2. Os novos fatores serão calculados automaticamente:")
        logger.info("   - return_1m")
        logger.info("   - momentum_6m_ex_1m = return_6m - return_1m")
        logger.info("   - momentum_12m_ex_1m = return_12m - return_1m")
        logger.info("")
        logger.info("3. O score de momentum agora usa:")
        logger.info("   - momentum_6m_ex_1m (novo)")
        logger.info("   - momentum_12m_ex_1m (novo)")
        logger.info("   - -volatility_90d")
        logger.info("   - -recent_drawdown")
        logger.info("   - RSI foi REMOVIDO do score (mantido para compatibilidade)")
        
    except Exception as e:
        logger.error(f"❌ Erro durante migração: {e}")
        raise


if __name__ == "__main__":
    migrate_add_momentum_columns()
