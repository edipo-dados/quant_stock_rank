"""
Script para ingerir dados do benchmark (IBOVESPA) do Yahoo Finance.

Uso:
    python scripts/ingest_benchmark.py --start-date 2021-01-01 --end-date 2024-12-31
    python scripts/ingest_benchmark.py --days 365  # Últimos 365 dias
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from datetime import date, datetime, timedelta
import logging
import pandas as pd

from app.models.database import SessionLocal
from app.backtest.benchmark import BenchmarkManager
from app.ingestion.yahoo_client import YahooFinanceClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ingest_benchmark(
    start_date: date,
    end_date: date,
    symbol: str = "^BVSP"
):
    """
    Ingere dados do benchmark do Yahoo Finance.
    
    Args:
        start_date: Data inicial
        end_date: Data final
        symbol: Símbolo do benchmark (padrão: ^BVSP)
    """
    logger.info("=" * 80)
    logger.info("INGESTÃO DE BENCHMARK")
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
            logger.error(f"Nenhum dado encontrado para {symbol}")
            return
        
        logger.info(f"✓ {len(prices_df)} registros obtidos")
        
        # Preparar DataFrame
        prices_df = prices_df.rename(columns={'adj_close': 'close'})
        prices_df = prices_df[['date', 'close']]
        
        # Ingerir no banco
        logger.info("Salvando no banco de dados...")
        records_inserted = benchmark_manager.ingest_benchmark_data(prices_df)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("RESUMO")
        logger.info("=" * 80)
        logger.info(f"Registros inseridos: {records_inserted}")
        logger.info(f"Registros atualizados: {len(prices_df) - records_inserted}")
        logger.info(f"Total de registros: {len(prices_df)}")
        logger.info("")
        
        # Verificar disponibilidade
        availability = benchmark_manager.get_data_availability(start_date, end_date)
        logger.info(f"Cobertura: {availability['coverage']:.1%}")
        logger.info(f"Status: {'✓ Suficiente' if availability['sufficient'] else '✗ Insuficiente'}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Erro ao ingerir benchmark: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='Ingerir dados do benchmark (IBOVESPA)')
    
    parser.add_argument(
        '--start-date',
        type=str,
        help='Data inicial (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='Data final (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--days',
        type=int,
        help='Número de dias retroativos (alternativa a start-date/end-date)'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        default='^BVSP',
        help='Símbolo do benchmark (padrão: ^BVSP)'
    )
    
    args = parser.parse_args()
    
    # Determinar período
    if args.days:
        end_date = date.today()
        start_date = end_date - timedelta(days=args.days)
    elif args.start_date and args.end_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
    else:
        # Padrão: últimos 3 anos
        end_date = date.today()
        start_date = end_date - timedelta(days=3*365)
    
    ingest_benchmark(start_date, end_date, args.symbol)


if __name__ == "__main__":
    main()
