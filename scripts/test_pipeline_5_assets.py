"""
Script de teste do pipeline com apenas 5 ativos.

Útil para validar configuração e testar rapidamente.
"""

import sys
from datetime import datetime, timedelta
import logging

from app.models.database import SessionLocal
from app.ingestion.ingestion_service import IngestionService
from app.factor_engine.feature_service import FeatureService
from app.scoring.score_service import ScoreService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 5 ativos para teste (líquidos e conhecidos)
TEST_TICKERS = [
    "ITUB3",   # Itaú
    "PETR4",   # Petrobras
    "VALE3",   # Vale
    "BBDC4",   # Bradesco
    "ABEV3"    # Ambev
]


def main():
    """Executa pipeline de teste com 5 ativos."""
    
    logger.info("=" * 60)
    logger.info("PIPELINE DE TESTE - 5 ATIVOS")
    logger.info("=" * 60)
    logger.info(f"Ativos: {', '.join(TEST_TICKERS)}")
    logger.info("")
    
    db = SessionLocal()
    
    try:
        # Calcular período (últimos 2 anos para ter dados suficientes)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=730)  # 2 anos
        
        logger.info(f"Período: {start_date} a {end_date}")
        logger.info("")
        
        # 1. INGESTÃO DE PREÇOS
        logger.info("=" * 60)
        logger.info("ETAPA 1/3: Ingestão de Preços")
        logger.info("=" * 60)
        
        ingestion_service = IngestionService(db)
        
        for ticker in TEST_TICKERS:
            logger.info(f"Baixando preços de {ticker}...")
            try:
                ingestion_service.ingest_daily_prices(
                    ticker=ticker,
                    start_date=start_date,
                    end_date=end_date
                )
                logger.info(f"✓ {ticker} - Preços baixados")
            except Exception as e:
                logger.error(f"✗ {ticker} - Erro: {e}")
        
        logger.info("")
        
        # 2. CÁLCULO DE FEATURES
        logger.info("=" * 60)
        logger.info("ETAPA 2/3: Cálculo de Features")
        logger.info("=" * 60)
        
        feature_service = FeatureService(db)
        
        for ticker in TEST_TICKERS:
            logger.info(f"Calculando features de {ticker}...")
            try:
                feature_service.calculate_and_store_features(
                    ticker=ticker,
                    start_date=start_date,
                    end_date=end_date
                )
                logger.info(f"✓ {ticker} - Features calculadas")
            except Exception as e:
                logger.error(f"✗ {ticker} - Erro: {e}")
        
        logger.info("")
        
        # 3. CÁLCULO DE SCORES
        logger.info("=" * 60)
        logger.info("ETAPA 3/3: Cálculo de Scores")
        logger.info("=" * 60)
        
        score_service = ScoreService(db)
        
        logger.info(f"Calculando scores para {end_date}...")
        try:
            score_service.calculate_and_store_scores(
                tickers=TEST_TICKERS,
                date=end_date
            )
            logger.info(f"✓ Scores calculados para {len(TEST_TICKERS)} ativos")
        except Exception as e:
            logger.error(f"✗ Erro ao calcular scores: {e}")
            raise
        
        logger.info("")
        
        # 4. VERIFICAÇÃO
        logger.info("=" * 60)
        logger.info("VERIFICAÇÃO DOS RESULTADOS")
        logger.info("=" * 60)
        
        from app.models.schemas import ScoreDaily
        
        scores = db.query(ScoreDaily).filter(
            ScoreDaily.date == end_date
        ).order_by(ScoreDaily.final_score.desc()).all()
        
        if scores:
            logger.info(f"\n✓ {len(scores)} scores gerados para {end_date}\n")
            logger.info("Ranking:")
            for i, score in enumerate(scores, 1):
                logger.info(
                    f"  {i}. {score.ticker:6s} - Score: {score.final_score:.3f} "
                    f"(M:{score.momentum_score:.2f} Q:{score.quality_score:.2f} V:{score.value_score:.2f})"
                )
        else:
            logger.warning("✗ Nenhum score foi gerado!")
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("PIPELINE DE TESTE CONCLUÍDO")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Erro no pipeline: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
