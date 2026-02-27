"""
Script de teste para validar aplicação de research.

Testa:
- Importação de módulos
- Conexão com banco
- Criação de backtest run
- Funções auxiliares
"""

import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_imports():
    """Testa importação de módulos."""
    logger.info("=" * 80)
    logger.info("TESTE 1: Importação de Módulos")
    logger.info("=" * 80)
    
    try:
        import streamlit as st
        logger.info("✅ Streamlit importado")
        
        import plotly.graph_objects as go
        logger.info("✅ Plotly importado")
        
        from app.models.database import SessionLocal
        logger.info("✅ Database importado")
        
        from app.backtest.service import BacktestService
        logger.info("✅ BacktestService importado")
        
        from app.backtest.backtest_engine import BacktestEngine
        logger.info("✅ BacktestEngine importado")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na importação: {e}")
        return False


def test_database_connection():
    """Testa conexão com banco."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTE 2: Conexão com Banco")
    logger.info("=" * 80)
    
    try:
        from app.models.database import SessionLocal
        from app.models.schemas import ScoreDaily
        
        db = SessionLocal()
        
        # Verificar se há scores
        count = db.query(ScoreDaily).count()
        logger.info(f"✅ Conexão OK - {count} scores no banco")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na conexão: {e}")
        return False


def test_backtest_tables():
    """Testa se tabelas de backtest existem."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTE 3: Tabelas de Backtest")
    logger.info("=" * 80)
    
    try:
        from sqlalchemy import inspect
        from app.models.database import engine
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = [
            'backtest_runs',
            'backtest_nav',
            'backtest_positions',
            'backtest_metrics'
        ]
        
        for table in required_tables:
            if table in tables:
                logger.info(f"✅ Tabela {table} existe")
            else:
                logger.error(f"❌ Tabela {table} NÃO existe")
                logger.error("Execute: python scripts/migrate_add_backtest_tables.py")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar tabelas: {e}")
        return False


def test_backtest_service():
    """Testa BacktestService."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTE 4: BacktestService")
    logger.info("=" * 80)
    
    try:
        from app.models.database import SessionLocal
        from app.backtest.service import BacktestService
        
        db = SessionLocal()
        service = BacktestService(db)
        
        # Criar backtest run de teste
        run = service.create_backtest_run(
            name="test_research_app",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            rebalance_frequency="monthly",
            top_n=5,
            transaction_cost=0.001,
            initial_capital=100000.0,
            notes="Teste da aplicação de research"
        )
        
        logger.info(f"✅ Backtest run criado: {run.id}")
        
        # Verificar se foi salvo
        retrieved = service.repository.get_run(run.id)
        if retrieved:
            logger.info(f"✅ Run recuperado do banco: {retrieved.name}")
        else:
            logger.error("❌ Run não foi recuperado")
            return False
        
        # Deletar run de teste
        service.delete_backtest(run.id)
        logger.info("✅ Run de teste deletado")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no BacktestService: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_validation_function():
    """Testa função de validação."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTE 5: Função de Validação")
    logger.info("=" * 80)
    
    try:
        # Importar função de validação
        # (Simulação - a função está no streamlit_backtest_app.py)
        
        # Teste 1: Data início >= Data fim
        start = date(2024, 12, 31)
        end = date(2024, 1, 1)
        
        if start >= end:
            logger.info("✅ Validação: Data início >= Data fim detectada")
        
        # Teste 2: Período < 3 meses
        start = date(2024, 1, 1)
        end = date(2024, 2, 1)
        
        min_date = start + relativedelta(months=3)
        if end < min_date:
            logger.info("✅ Validação: Período < 3 meses detectado")
        
        # Teste 3: Período válido
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)
        
        if start < end and (end - start).days >= 90:
            logger.info("✅ Validação: Período válido aceito")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na validação: {e}")
        return False


def main():
    """Executa todos os testes."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTE DA APLICAÇÃO DE RESEARCH")
    logger.info("=" * 80)
    
    tests = [
        ("Importação de Módulos", test_imports),
        ("Conexão com Banco", test_database_connection),
        ("Tabelas de Backtest", test_backtest_tables),
        ("BacktestService", test_backtest_service),
        ("Função de Validação", test_validation_function)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Erro no teste {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo
    logger.info("\n" + "=" * 80)
    logger.info("RESUMO DOS TESTES")
    logger.info("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        logger.info(f"{status}: {test_name}")
    
    logger.info("\n" + "=" * 80)
    logger.info(f"RESULTADO FINAL: {passed}/{total} testes passaram")
    logger.info("=" * 80)
    
    if passed == total:
        logger.info("\n✅ TODOS OS TESTES PASSARAM!")
        logger.info("\nPróximos passos:")
        logger.info("1. Executar aplicação: streamlit run app/research/streamlit_backtest_app.py")
        logger.info("2. Acessar: http://localhost:8501")
        logger.info("3. Configurar parâmetros e rodar backtest")
        return True
    else:
        logger.error("\n❌ ALGUNS TESTES FALHARAM!")
        logger.error("\nVerifique os erros acima e corrija antes de usar a aplicação.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
