"""
Script de inicialização do banco de dados.

Cria todas as tabelas definidas nos modelos SQLAlchemy.

Valida: Requisito 13.8

Uso:
    python scripts/init_db.py
"""

import logging
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importar módulos
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.models.database import engine, Base
from app.models.schemas import (
    RawPriceDaily,
    RawFundamental,
    FeatureDaily,
    FeatureMonthly,
    ScoreDaily
)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_database():
    """
    Inicializa o schema do banco de dados.
    
    Cria todas as tabelas definidas nos modelos SQLAlchemy:
    - raw_prices_daily
    - raw_fundamentals
    - features_daily
    - features_monthly
    - scores_daily
    
    Raises:
        Exception: Se houver erro ao criar as tabelas
    """
    try:
        logger.info("Iniciando criação das tabelas do banco de dados...")
        logger.info(f"Database URL: {engine.url}")
        
        # Cria todas as tabelas
        Base.metadata.create_all(bind=engine)
        
        # Lista as tabelas criadas
        tables = Base.metadata.tables.keys()
        logger.info(f"Tabelas criadas com sucesso: {', '.join(tables)}")
        
        # Verifica que todas as tabelas esperadas foram criadas
        expected_tables = {
            'raw_prices_daily',
            'raw_fundamentals',
            'features_daily',
            'features_monthly',
            'scores_daily'
        }
        
        created_tables = set(tables)
        if expected_tables.issubset(created_tables):
            logger.info("✓ Todas as tabelas esperadas foram criadas")
        else:
            missing = expected_tables - created_tables
            logger.warning(f"⚠ Tabelas faltando: {', '.join(missing)}")
        
        logger.info("Inicialização do banco de dados concluída com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao criar tabelas do banco de dados: {e}")
        raise


def drop_all_tables():
    """
    Remove todas as tabelas do banco de dados.
    
    ATENÇÃO: Esta operação é destrutiva e remove todos os dados!
    
    Raises:
        Exception: Se houver erro ao remover as tabelas
    """
    try:
        logger.warning("ATENÇÃO: Removendo todas as tabelas do banco de dados...")
        Base.metadata.drop_all(bind=engine)
        logger.info("Todas as tabelas foram removidas")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao remover tabelas: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Inicializa o schema do banco de dados"
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Remove todas as tabelas antes de criar (DESTRUTIVO!)"
    )
    parser.add_argument(
        "--drop-only",
        action="store_true",
        help="Apenas remove as tabelas sem recriar (DESTRUTIVO!)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.drop_only:
            # Apenas remove as tabelas
            logger.warning("Modo: Remover tabelas apenas")
            response = input("Tem certeza que deseja remover todas as tabelas? (sim/não): ")
            if response.lower() == "sim":
                drop_all_tables()
                logger.info("Operação concluída")
            else:
                logger.info("Operação cancelada")
        
        elif args.drop:
            # Remove e recria as tabelas
            logger.warning("Modo: Remover e recriar tabelas")
            response = input("Tem certeza que deseja remover e recriar todas as tabelas? (sim/não): ")
            if response.lower() == "sim":
                drop_all_tables()
                init_database()
            else:
                logger.info("Operação cancelada")
        
        else:
            # Apenas cria as tabelas (modo padrão)
            logger.info("Modo: Criar tabelas (preserva dados existentes)")
            init_database()
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Falha na inicialização: {e}")
        sys.exit(1)
