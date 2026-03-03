"""
Script para testar ingestão de preços e identificar problemas.

Testa a ingestão de preços para um ticker específico com logs detalhados.
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import yfinance as yf

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.ingestion.historical_expansion import HistoricalExpansion
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_yfinance_direct(ticker: str, start_date: str):
    """Testa yfinance diretamente."""
    
    logger.info("=" * 80)
    logger.info(f"TESTE DIRETO YFINANCE: {ticker}")
    logger.info("=" * 80)
    
    try:
        ticker_obj = yf.Ticker(ticker)
        logger.info(f"Ticker object criado: {ticker_obj}")
        
        end_date = date.today().strftime('%Y-%m-%d')
        logger.info(f"Buscando dados de {start_date} até {end_date}")
        
        df = ticker_obj.history(start=start_date, end=end_date)
        
        if df.empty:
            logger.error(f"❌ DataFrame vazio para {ticker}")
            return False
        
        logger.info(f"✅ Dados recebidos: {len(df)} registros")
        logger.info(f"Colunas: {df.columns.tolist()}")
        logger.info(f"Primeiras 3 linhas:")
        logger.info(df.head(3))
        logger.info(f"Últimas 3 linhas:")
        logger.info(df.tail(3))
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste direto: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_expansion_module(ticker: str, start_date: str):
    """Testa módulo de expansão."""
    
    logger.info("\n" + "=" * 80)
    logger.info(f"TESTE MÓDULO EXPANSÃO: {ticker}")
    logger.info("=" * 80)
    
    db = SessionLocal()
    
    try:
        expander = HistoricalExpansion(db)
        
        result = expander.fetch_full_price_history(
            ticker=ticker,
            start_date=start_date,
            mode='full'
        )
        
        logger.info(f"Resultado: {result}")
        
        if result['success']:
            logger.info(f"✅ Sucesso: {result['records_inserted']} registros")
            return True
        else:
            logger.error(f"❌ Falha: {result['error']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro no teste de expansão: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def check_existing_data(ticker: str):
    """Verifica dados existentes no banco."""
    
    logger.info("\n" + "=" * 80)
    logger.info(f"VERIFICAR DADOS EXISTENTES: {ticker}")
    logger.info("=" * 80)
    
    from app.models.schemas import RawPriceDaily
    from sqlalchemy import func
    
    db = SessionLocal()
    
    try:
        # Contar registros
        count = db.query(func.count(RawPriceDaily.id)).filter(
            RawPriceDaily.ticker == ticker
        ).scalar()
        
        logger.info(f"Registros existentes: {count}")
        
        if count > 0:
            # Datas
            min_date = db.query(func.min(RawPriceDaily.date)).filter(
                RawPriceDaily.ticker == ticker
            ).scalar()
            
            max_date = db.query(func.max(RawPriceDaily.date)).filter(
                RawPriceDaily.ticker == ticker
            ).scalar()
            
            logger.info(f"Período: {min_date} a {max_date}")
            
            years = (max_date - min_date).days / 365.25
            logger.info(f"Anos de dados: {years:.2f}")
            
            # Primeiros 5 registros
            first_records = db.query(RawPriceDaily).filter(
                RawPriceDaily.ticker == ticker
            ).order_by(RawPriceDaily.date).limit(5).all()
            
            logger.info("\nPrimeiros 5 registros:")
            for r in first_records:
                logger.info(f"  {r.date}: close={r.close}, volume={r.volume}")
        else:
            logger.warning("Nenhum registro existente")
            
    except Exception as e:
        logger.error(f"Erro ao verificar dados: {e}")
    finally:
        db.close()


def main():
    """Executa testes."""
    
    # Ticker para teste
    ticker = "PETR4.SA"
    start_date = "2018-01-01"
    
    logger.info("=" * 80)
    logger.info("DIAGNÓSTICO DE INGESTÃO DE PREÇOS")
    logger.info("=" * 80)
    logger.info(f"Ticker: {ticker}")
    logger.info(f"Data inicial: {start_date}")
    logger.info("")
    
    # 1. Verificar dados existentes
    check_existing_data(ticker)
    
    # 2. Testar yfinance direto
    yf_ok = test_yfinance_direct(ticker, start_date)
    
    # 3. Testar módulo de expansão
    if yf_ok:
        expansion_ok = test_expansion_module(ticker, start_date)
    else:
        logger.error("Pulando teste de expansão pois yfinance falhou")
        expansion_ok = False
    
    # Resumo
    logger.info("\n" + "=" * 80)
    logger.info("RESUMO")
    logger.info("=" * 80)
    logger.info(f"YFinance direto: {'✅ OK' if yf_ok else '❌ FALHOU'}")
    logger.info(f"Módulo expansão: {'✅ OK' if expansion_ok else '❌ FALHOU'}")
    logger.info("=" * 80)
    
    return 0 if (yf_ok and expansion_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
