"""
Script simplificado para ingestão sequencial de preços.

Versão sem paralelização para evitar conflitos de sessão SQLAlchemy.
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import time
import yfinance as yf
import pandas as pd

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import RawPriceDaily
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ingest_price_for_ticker(ticker: str, start_date: str = "2018-01-01"):
    """Ingere preços para um ticker específico."""
    
    db = SessionLocal()
    
    try:
        logger.info(f"Processando {ticker}...")
        
        # Buscar dados
        end_date = date.today().strftime('%Y-%m-%d')
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(start=start_date, end=end_date)
        
        if df.empty:
            logger.warning(f"  Sem dados para {ticker}")
            return {"ticker": ticker, "success": False, "records": 0}
        
        # Processar
        df = df.reset_index()
        if 'Date' in df.columns:
            df['date'] = pd.to_datetime(df['Date']).dt.date
        else:
            df['date'] = pd.to_datetime(df.index).date
        
        df = df[df['date'] <= date.today()]
        df = df.drop_duplicates(subset=['date'], keep='last')
        
        # Inserir/atualizar um por um
        inserted = 0
        updated = 0
        
        for _, row in df.iterrows():
            existing = db.query(RawPriceDaily).filter(
                RawPriceDaily.ticker == ticker,
                RawPriceDaily.date == row['date']
            ).first()
            
            if existing:
                existing.open = float(row['Open'])
                existing.high = float(row['High'])
                existing.low = float(row['Low'])
                existing.close = float(row['Close'])
                existing.volume = int(row['Volume'])
                existing.adj_close = float(row['Close'])
                updated += 1
            else:
                price_record = RawPriceDaily(
                    ticker=ticker,
                    date=row['date'],
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']),
                    adj_close=float(row['Close'])
                )
                db.add(price_record)
                inserted += 1
        
        db.commit()
        total = inserted + updated
        logger.info(f"  ✓ {ticker}: {total} registros ({inserted} novos, {updated} atualizados)")
        
        return {"ticker": ticker, "success": True, "records": total}
        
    except Exception as e:
        logger.error(f"  ✗ {ticker}: {e}")
        db.rollback()
        return {"ticker": ticker, "success": False, "records": 0, "error": str(e)}
    finally:
        db.close()


def main():
    """Executa ingestão sequencial."""
    
    logger.info("=" * 80)
    logger.info("INGESTÃO SEQUENCIAL DE PREÇOS")
    logger.info("=" * 80)
    
    # Buscar tickers
    db = SessionLocal()
    tickers = db.query(RawPriceDaily.ticker).distinct().all()
    tickers = [t[0] for t in tickers]
    db.close()
    
    logger.info(f"Total de tickers: {len(tickers)}")
    logger.info("")
    
    # Processar sequencialmente
    results = []
    for i, ticker in enumerate(tickers, 1):
        logger.info(f"[{i}/{len(tickers)}] {ticker}")
        result = ingest_price_for_ticker(ticker)
        results.append(result)
        time.sleep(1)  # Rate limiting
    
    # Resumo
    success = sum(1 for r in results if r['success'])
    failed = len(results) - success
    total_records = sum(r['records'] for r in results if r['success'])
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("RESUMO")
    logger.info("=" * 80)
    logger.info(f"Sucesso: {success}/{len(tickers)} ({success/len(tickers)*100:.1f}%)")
    logger.info(f"Falhas: {failed}")
    logger.info(f"Total de registros: {total_records:,}")
    logger.info("=" * 80)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
