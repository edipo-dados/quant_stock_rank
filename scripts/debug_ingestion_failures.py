"""
Script para debugar falhas na ingestão histórica.

Verifica logs e identifica causas de falhas.
"""

import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import RawPriceDaily, RawFundamental
from sqlalchemy import func
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Debug de falhas na ingestão."""
    
    db = SessionLocal()
    
    try:
        logger.info("=" * 80)
        logger.info("DEBUG DE FALHAS NA INGESTÃO")
        logger.info("=" * 80)
        
        # Verificar tickers no banco
        tickers_prices = db.query(RawPriceDaily.ticker).distinct().all()
        tickers_prices = [t[0] for t in tickers_prices]
        
        tickers_fundamentals = db.query(RawFundamental.ticker).distinct().all()
        tickers_fundamentals = [t[0] for t in tickers_fundamentals]
        
        logger.info(f"\nTickers com preços: {len(tickers_prices)}")
        logger.info(f"Tickers com fundamentos: {len(tickers_fundamentals)}")
        
        # Verificar formato dos tickers
        logger.info("\n" + "=" * 80)
        logger.info("FORMATO DOS TICKERS")
        logger.info("=" * 80)
        
        invalid_format = []
        for ticker in tickers_prices[:10]:
            if not ticker.endswith('.SA'):
                invalid_format.append(ticker)
                logger.warning(f"Ticker sem .SA: {ticker}")
            else:
                logger.info(f"✓ {ticker}")
        
        if invalid_format:
            logger.warning(f"\nTotal de tickers com formato inválido: {len(invalid_format)}")
        
        # Verificar cobertura de dados
        logger.info("\n" + "=" * 80)
        logger.info("COBERTURA DE DADOS (Primeiros 10 tickers)")
        logger.info("=" * 80)
        
        for ticker in tickers_prices[:10]:
            # Contar registros
            count = db.query(func.count(RawPriceDaily.id)).filter(
                RawPriceDaily.ticker == ticker
            ).scalar()
            
            # Datas
            min_date = db.query(func.min(RawPriceDaily.date)).filter(
                RawPriceDaily.ticker == ticker
            ).scalar()
            
            max_date = db.query(func.max(RawPriceDaily.date)).filter(
                RawPriceDaily.ticker == ticker
            ).scalar()
            
            if min_date and max_date:
                years = (max_date - min_date).days / 365.25
                logger.info(
                    f"{ticker:12s}: {count:>5} registros, "
                    f"{years:>4.1f} anos ({min_date} a {max_date})"
                )
            else:
                logger.info(f"{ticker:12s}: {count:>5} registros (sem datas)")
        
        # Ler arquivo de log se existir
        log_file = Path('ingest_full_history.log')
        if log_file.exists():
            logger.info("\n" + "=" * 80)
            logger.info("ÚLTIMOS ERROS DO LOG")
            logger.info("=" * 80)
            
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Buscar linhas com erro
            error_lines = [line for line in lines if 'ERROR' in line or '✗' in line]
            
            if error_lines:
                logger.info(f"\nTotal de linhas com erro: {len(error_lines)}")
                logger.info("\nÚltimos 10 erros:")
                for line in error_lines[-10:]:
                    logger.info(line.strip())
            else:
                logger.info("Nenhum erro encontrado no log")
        
        logger.info("\n" + "=" * 80)
        logger.info("DEBUG CONCLUÍDO")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
