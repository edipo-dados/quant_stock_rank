"""
Migration para adicionar tabelas de backtesting persistente.

Cria 4 novas tabelas isoladas:
- backtest_runs: Metadados de execuções
- backtest_nav: Equity curve diária
- backtest_positions: Posições por rebalance
- backtest_metrics: Métricas finais

IMPORTANTE: Não altera tabelas de produção.
"""

import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import engine, Base
from app.backtest.models import (
    BacktestRun,
    BacktestNAV,
    BacktestPosition,
    BacktestMetrics
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """
    Executa migration para criar tabelas de backtest.
    """
    logger.info("=" * 80)
    logger.info("MIGRATION: Adicionar Tabelas de Backtesting Persistente")
    logger.info("=" * 80)
    
    try:
        # Criar apenas as tabelas de backtest
        logger.info("Criando tabelas de backtest...")
        
        # Verificar se tabelas já existem
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        tables_to_create = [
            'backtest_runs',
            'backtest_nav',
            'backtest_positions',
            'backtest_metrics'
        ]
        
        for table_name in tables_to_create:
            if table_name in existing_tables:
                logger.warning(f"⚠️  Tabela {table_name} já existe. Pulando...")
            else:
                logger.info(f"Criando tabela {table_name}...")
        
        # Criar tabelas (apenas as que não existem)
        Base.metadata.create_all(
            bind=engine,
            tables=[
                BacktestRun.__table__,
                BacktestNAV.__table__,
                BacktestPosition.__table__,
                BacktestMetrics.__table__
            ],
            checkfirst=True
        )
        
        logger.info("✅ Tabelas de backtest criadas com sucesso!")
        
        # Verificar criação
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        logger.info("\nTabelas criadas:")
        for table_name in tables_to_create:
            if table_name in existing_tables:
                logger.info(f"  ✓ {table_name}")
                
                # Mostrar colunas
                columns = inspector.get_columns(table_name)
                logger.info(f"    Colunas: {', '.join([col['name'] for col in columns])}")
                
                # Mostrar índices
                indexes = inspector.get_indexes(table_name)
                if indexes:
                    logger.info(f"    Índices: {len(indexes)}")
            else:
                logger.error(f"  ✗ {table_name} - FALHOU")
        
        logger.info("\n" + "=" * 80)
        logger.info("MIGRATION CONCLUÍDA COM SUCESSO")
        logger.info("=" * 80)
        logger.info("\nPróximos passos:")
        logger.info("1. Testar criação de backtest run:")
        logger.info("   python scripts/test_backtest_persistence.py")
        logger.info("\n2. Rodar backtest completo:")
        logger.info("   python scripts/run_backtest.py")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Erro durante migration: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
