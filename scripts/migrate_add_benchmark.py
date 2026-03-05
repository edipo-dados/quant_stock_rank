"""
Script de migração para adicionar tabela de benchmark e ingerir dados iniciais.

Este script:
1. Cria a tabela benchmark_prices
2. Ingere dados históricos do IBOVESPA (^BVSP)
3. Valida a ingestão

Uso:
    python scripts/migrate_add_benchmark.py
    python scripts/migrate_add_benchmark.py --start-date 2020-01-01
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from datetime import date, datetime, timedelta
import logging

from sqlalchemy import text
from app.models.database import SessionLocal, engine
from app.backtest.benchmark import BenchmarkManager, BenchmarkPrice
from app.ingestion.yahoo_client import YahooFinanceClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_benchmark_table():
    """
    Cria a tabela benchmark_prices no banco de dados.
    """
    logger.info("=" * 80)
    logger.info("CRIANDO TABELA BENCHMARK_PRICES")
    logger.info("=" * 80)
    
    # SQL para criar a tabela
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS benchmark_prices (
        id SERIAL PRIMARY KEY,
        symbol VARCHAR(10) NOT NULL,
        date DATE NOT NULL,
        close FLOAT NOT NULL,
        daily_return FLOAT,
        CONSTRAINT uix_benchmark_symbol_date UNIQUE (symbol, date)
    );
    
    CREATE INDEX IF NOT EXISTS idx_benchmark_date ON benchmark_prices(date);
    CREATE INDEX IF NOT EXISTS idx_benchmark_symbol ON benchmark_prices(symbol);
    """
    
    try:
        with engine.connect() as conn:
            # Executar SQL
            conn.execute(text(create_table_sql))
            conn.commit()
        
        logger.info("✓ Tabela benchmark_prices criada com sucesso")
        logger.info("")
        return True
        
    except Exception as e:
        logger.error(f"✗ Erro ao criar tabela: {e}")
        return False


def check_table_exists():
    """
    Verifica se a tabela benchmark_prices já existe.
    """
    check_sql = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'benchmark_prices'
    );
    """
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(check_sql))
            exists = result.scalar()
            return exists
    except Exception as e:
        logger.error(f"Erro ao verificar tabela: {e}")
        return False


def ingest_benchmark_data(start_date: date, end_date: date, symbol: str = "^BVSP"):
    """
    Ingere dados históricos do benchmark.
    
    Args:
        start_date: Data inicial
        end_date: Data final
        symbol: Símbolo do benchmark
    """
    logger.info("=" * 80)
    logger.info("INGESTÃO DE DADOS DO BENCHMARK")
    logger.info("=" * 80)
    logger.info(f"Símbolo: {symbol}")
    logger.info(f"Período: {start_date} a {end_date}")
    logger.info("")
    
    db = SessionLocal()
    
    try:
        # Inicializar clientes
        yahoo_client = YahooFinanceClient()
        benchmark_manager = BenchmarkManager(db, symbol=symbol)
        
        # Buscar dados do Yahoo Finance
        logger.info(f"Buscando dados do Yahoo Finance para {symbol}...")
        prices_df = yahoo_client.fetch_daily_prices(
            ticker=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        if prices_df.empty:
            logger.error(f"✗ Nenhum dado encontrado para {symbol}")
            return False
        
        logger.info(f"✓ {len(prices_df)} registros obtidos do Yahoo Finance")
        
        # Preparar DataFrame
        prices_df = prices_df.rename(columns={'adj_close': 'close'})
        prices_df = prices_df[['date', 'close']]
        
        # Ingerir no banco
        logger.info("Salvando no banco de dados...")
        records_inserted = benchmark_manager.ingest_benchmark_data(prices_df)
        
        logger.info(f"✓ {records_inserted} novos registros inseridos")
        logger.info(f"✓ {len(prices_df) - records_inserted} registros atualizados")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Erro ao ingerir dados: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.close()


def validate_migration(start_date: date, end_date: date):
    """
    Valida se a migração foi bem-sucedida.
    
    Args:
        start_date: Data inicial esperada
        end_date: Data final esperada
    """
    logger.info("=" * 80)
    logger.info("VALIDAÇÃO DA MIGRAÇÃO")
    logger.info("=" * 80)
    
    db = SessionLocal()
    
    try:
        benchmark_manager = BenchmarkManager(db)
        
        # Verificar disponibilidade de dados
        availability = benchmark_manager.get_data_availability(start_date, end_date)
        
        logger.info(f"Símbolo: {availability['symbol']}")
        logger.info(f"Período: {availability['start_date']} a {availability['end_date']}")
        logger.info(f"Registros encontrados: {availability['records_found']}")
        logger.info(f"Dias esperados: {availability['expected_days']}")
        logger.info(f"Cobertura: {availability['coverage']:.1%}")
        logger.info("")
        
        if availability['sufficient']:
            logger.info("✓ MIGRAÇÃO BEM-SUCEDIDA")
            logger.info("✓ Dados suficientes para backtesting")
        else:
            logger.warning("⚠ ATENÇÃO: Cobertura abaixo de 70%")
            logger.warning("⚠ Pode haver problemas em backtests")
        
        logger.info("=" * 80)
        
        return availability['sufficient']
        
    except Exception as e:
        logger.error(f"✗ Erro na validação: {e}")
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Migração: adicionar tabela de benchmark e ingerir dados'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        help='Data inicial (YYYY-MM-DD). Padrão: 2021-01-01'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='Data final (YYYY-MM-DD). Padrão: hoje'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        default='^BVSP',
        help='Símbolo do benchmark. Padrão: ^BVSP (IBOVESPA)'
    )
    parser.add_argument(
        '--skip-ingestion',
        action='store_true',
        help='Apenas criar tabela, não ingerir dados'
    )
    
    args = parser.parse_args()
    
    # Determinar período
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
    else:
        end_date = date.today()
    
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
    else:
        # Padrão: desde 2021-01-01 (início dos dados históricos do sistema)
        start_date = date(2021, 1, 1)
    
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 20 + "MIGRAÇÃO: ADICIONAR BENCHMARK" + " " * 29 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("")
    
    # Passo 1: Verificar se tabela já existe
    logger.info("PASSO 1: Verificando se tabela já existe...")
    table_exists = check_table_exists()
    
    if table_exists:
        logger.info("✓ Tabela benchmark_prices já existe")
        logger.info("")
    else:
        logger.info("✗ Tabela benchmark_prices não existe")
        logger.info("")
        
        # Passo 2: Criar tabela
        logger.info("PASSO 2: Criando tabela...")
        success = create_benchmark_table()
        
        if not success:
            logger.error("✗ MIGRAÇÃO FALHOU: Não foi possível criar a tabela")
            sys.exit(1)
    
    # Passo 3: Ingerir dados (se não for skip)
    if not args.skip_ingestion:
        logger.info("PASSO 3: Ingerindo dados históricos...")
        success = ingest_benchmark_data(start_date, end_date, args.symbol)
        
        if not success:
            logger.error("✗ MIGRAÇÃO FALHOU: Não foi possível ingerir dados")
            sys.exit(1)
        
        # Passo 4: Validar
        logger.info("PASSO 4: Validando migração...")
        success = validate_migration(start_date, end_date)
        
        if not success:
            logger.warning("⚠ MIGRAÇÃO CONCLUÍDA COM AVISOS")
            sys.exit(0)
    else:
        logger.info("PASSO 3: Ingestão de dados pulada (--skip-ingestion)")
        logger.info("")
    
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 25 + "MIGRAÇÃO CONCLUÍDA" + " " * 35 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("")
    logger.info("Próximos passos:")
    logger.info("1. Integrar benchmark no BacktestEngine")
    logger.info("2. Adicionar custos de transação")
    logger.info("3. Calcular Alpha, Beta, Information Ratio")
    logger.info("")
    logger.info("Para atualizar dados do benchmark diariamente:")
    logger.info(f"  python scripts/ingest_benchmark.py --days 7")
    logger.info("")


if __name__ == "__main__":
    main()
