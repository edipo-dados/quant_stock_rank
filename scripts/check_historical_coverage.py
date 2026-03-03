"""
Script para verificar cobertura histórica de dados.

Mostra estatísticas de cobertura de preços e fundamentos
para todos os tickers no banco.
"""

import sys
from pathlib import Path
from datetime import date
import pandas as pd

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


def check_coverage():
    """Verifica cobertura histórica de dados."""
    
    db = SessionLocal()
    
    try:
        logger.info("=" * 80)
        logger.info("VERIFICAÇÃO DE COBERTURA HISTÓRICA")
        logger.info("=" * 80)
        
        # ====================================================================
        # PREÇOS
        # ====================================================================
        logger.info("\n📊 PREÇOS:")
        
        # Total de tickers com preços
        total_tickers_prices = db.query(
            func.count(func.distinct(RawPriceDaily.ticker))
        ).scalar()
        
        logger.info(f"  Total de tickers: {total_tickers_prices}")
        
        # Total de registros
        total_records_prices = db.query(func.count(RawPriceDaily.id)).scalar()
        logger.info(f"  Total de registros: {total_records_prices:,}")
        
        # Data mais antiga e mais recente
        min_date = db.query(func.min(RawPriceDaily.date)).scalar()
        max_date = db.query(func.max(RawPriceDaily.date)).scalar()
        
        if min_date and max_date:
            years_span = (max_date - min_date).days / 365.25
            logger.info(f"  Período: {min_date} a {max_date} ({years_span:.1f} anos)")
        
        # Cobertura por ticker (top 10 e bottom 10)
        ticker_coverage = db.query(
            RawPriceDaily.ticker,
            func.min(RawPriceDaily.date).label('min_date'),
            func.max(RawPriceDaily.date).label('max_date'),
            func.count(RawPriceDaily.id).label('records')
        ).group_by(RawPriceDaily.ticker).all()
        
        if ticker_coverage:
            # Converter para DataFrame
            df_coverage = pd.DataFrame([{
                'ticker': t.ticker,
                'min_date': t.min_date,
                'max_date': t.max_date,
                'records': t.records,
                'years': (t.max_date - t.min_date).days / 365.25
            } for t in ticker_coverage])
            
            logger.info(f"\n  Top 10 tickers (mais registros):")
            top_10 = df_coverage.nlargest(10, 'records')
            for _, row in top_10.iterrows():
                logger.info(
                    f"    {row['ticker']:10s}: {row['records']:>5} registros, "
                    f"{row['years']:>4.1f} anos ({row['min_date']} a {row['max_date']})"
                )
            
            logger.info(f"\n  Bottom 10 tickers (menos registros):")
            bottom_10 = df_coverage.nsmallest(10, 'records')
            for _, row in bottom_10.iterrows():
                logger.info(
                    f"    {row['ticker']:10s}: {row['records']:>5} registros, "
                    f"{row['years']:>4.1f} anos ({row['min_date']} a {row['max_date']})"
                )
            
            # Estatísticas gerais
            logger.info(f"\n  Estatísticas de cobertura:")
            logger.info(f"    Média de registros por ticker: {df_coverage['records'].mean():.0f}")
            logger.info(f"    Mediana de registros por ticker: {df_coverage['records'].median():.0f}")
            logger.info(f"    Média de anos por ticker: {df_coverage['years'].mean():.1f}")
            logger.info(f"    Mediana de anos por ticker: {df_coverage['years'].median():.1f}")
            
            # Tickers com menos de 3 anos
            insufficient = df_coverage[df_coverage['years'] < 3.0]
            logger.info(f"\n  Tickers com < 3 anos: {len(insufficient)} ({len(insufficient)/len(df_coverage)*100:.1f}%)")
            if len(insufficient) > 0:
                logger.info(f"    Exemplos:")
                for _, row in insufficient.head(5).iterrows():
                    logger.info(f"      {row['ticker']:10s}: {row['years']:.1f} anos")
        
        # ====================================================================
        # FUNDAMENTOS
        # ====================================================================
        logger.info("\n💼 FUNDAMENTOS:")
        
        # Total de tickers com fundamentos
        total_tickers_fundamentals = db.query(
            func.count(func.distinct(RawFundamental.ticker))
        ).scalar()
        
        logger.info(f"  Total de tickers: {total_tickers_fundamentals}")
        
        # Total de registros
        total_records_fundamentals = db.query(func.count(RawFundamental.id)).scalar()
        logger.info(f"  Total de registros: {total_records_fundamentals:,}")
        
        # Cobertura por ticker
        fundamental_coverage = db.query(
            RawFundamental.ticker,
            func.count(RawFundamental.id).label('years')
        ).filter(
            RawFundamental.period_type == 'annual'
        ).group_by(RawFundamental.ticker).all()
        
        if fundamental_coverage:
            df_fund = pd.DataFrame([{
                'ticker': f.ticker,
                'years': f.years
            } for f in fundamental_coverage])
            
            logger.info(f"\n  Top 10 tickers (mais anos):")
            top_10_fund = df_fund.nlargest(10, 'years')
            for _, row in top_10_fund.iterrows():
                logger.info(f"    {row['ticker']:10s}: {row['years']} anos")
            
            logger.info(f"\n  Bottom 10 tickers (menos anos):")
            bottom_10_fund = df_fund.nsmallest(10, 'years')
            for _, row in bottom_10_fund.iterrows():
                logger.info(f"    {row['ticker']:10s}: {row['years']} anos")
            
            logger.info(f"\n  Estatísticas de cobertura:")
            logger.info(f"    Média de anos por ticker: {df_fund['years'].mean():.1f}")
            logger.info(f"    Mediana de anos por ticker: {df_fund['years'].median():.1f}")
            
            # Tickers com menos de 3 anos
            insufficient_fund = df_fund[df_fund['years'] < 3]
            logger.info(f"\n  Tickers com < 3 anos: {len(insufficient_fund)} ({len(insufficient_fund)/len(df_fund)*100:.1f}%)")
            if len(insufficient_fund) > 0:
                logger.info(f"    Exemplos:")
                for _, row in insufficient_fund.head(5).iterrows():
                    logger.info(f"      {row['ticker']:10s}: {row['years']} anos")
        
        # ====================================================================
        # COBERTURA COMBINADA
        # ====================================================================
        logger.info("\n🔗 COBERTURA COMBINADA (Preços + Fundamentos):")
        
        # Tickers com ambos
        tickers_with_prices = set([t.ticker for t in ticker_coverage])
        tickers_with_fundamentals = set([f.ticker for f in fundamental_coverage])
        
        tickers_with_both = tickers_with_prices & tickers_with_fundamentals
        tickers_only_prices = tickers_with_prices - tickers_with_fundamentals
        tickers_only_fundamentals = tickers_with_fundamentals - tickers_with_prices
        
        logger.info(f"  Tickers com preços E fundamentos: {len(tickers_with_both)}")
        logger.info(f"  Tickers apenas com preços: {len(tickers_only_prices)}")
        logger.info(f"  Tickers apenas com fundamentos: {len(tickers_only_fundamentals)}")
        
        if tickers_only_prices:
            logger.info(f"\n  Exemplos de tickers sem fundamentos:")
            for ticker in list(tickers_only_prices)[:5]:
                logger.info(f"    {ticker}")
        
        if tickers_only_fundamentals:
            logger.info(f"\n  Exemplos de tickers sem preços:")
            for ticker in list(tickers_only_fundamentals)[:5]:
                logger.info(f"    {ticker}")
        
        # Tickers prontos para backtest (ambos com >= 3 anos)
        if ticker_coverage and fundamental_coverage:
            df_prices_3y = df_coverage[df_coverage['years'] >= 3.0]
            df_fund_3y = df_fund[df_fund['years'] >= 3]
            
            tickers_ready = set(df_prices_3y['ticker']) & set(df_fund_3y['ticker'])
            
            logger.info(f"\n  ✅ Tickers prontos para backtest (≥3 anos ambos): {len(tickers_ready)}")
            logger.info(f"     Taxa: {len(tickers_ready)/len(tickers_with_both)*100:.1f}%")
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ VERIFICAÇÃO CONCLUÍDA")
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
    sys.exit(check_coverage())
