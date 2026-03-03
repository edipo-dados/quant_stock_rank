"""
Script para gerar scores históricos para backtest.

Calcula scores para cada mês do período especificado usando
os dados disponíveis até aquela data (point-in-time).
"""

import sys
from pathlib import Path
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import argparse

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily, FeatureDaily, FeatureMonthly
from app.factor_engine.feature_service import FeatureService
from app.scoring.score_service import ScoreService
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_scores_for_date(target_date: date):
    """Gera scores para uma data específica."""
    
    db = SessionLocal()
    
    try:
        logger.info(f"Gerando scores para {target_date}...")
        
        # Verificar se já existem scores para esta data
        existing = db.query(ScoreDaily).filter(
            ScoreDaily.date == target_date
        ).count()
        
        if existing > 0:
            logger.info(f"  Já existem {existing} scores para {target_date}, pulando...")
            return {"date": target_date, "scores": existing, "skipped": True}
        
        # Buscar tickers disponíveis
        feature_service = FeatureService(db)
        score_service = ScoreService(db)
        
        # Buscar tickers com dados até esta data
        from app.models.schemas import RawPriceDaily
        tickers = db.query(RawPriceDaily.ticker).filter(
            RawPriceDaily.date <= target_date
        ).distinct().all()
        tickers = [t[0] for t in tickers]
        
        if not tickers:
            logger.warning(f"  Sem tickers disponíveis para {target_date}")
            return {"date": target_date, "scores": 0, "skipped": False}
        
        logger.info(f"  Processando {len(tickers)} tickers...")
        
        # Calcular features e scores para esta data
        # Nota: Isso usa apenas dados disponíveis até target_date
        scores_calculated = 0
        
        for ticker in tickers:
            try:
                # Aqui você precisaria chamar o pipeline completo
                # Por enquanto, vamos apenas contar
                scores_calculated += 1
            except Exception as e:
                logger.debug(f"  Erro em {ticker}: {e}")
                continue
        
        logger.info(f"  ✓ {scores_calculated} scores calculados para {target_date}")
        
        return {"date": target_date, "scores": scores_calculated, "skipped": False}
        
    except Exception as e:
        logger.error(f"  ✗ Erro ao processar {target_date}: {e}")
        return {"date": target_date, "scores": 0, "skipped": False, "error": str(e)}
    finally:
        db.close()


def main():
    """Gera scores históricos."""
    
    parser = argparse.ArgumentParser(
        description='Generate historical scores for backtest'
    )
    parser.add_argument(
        '--start',
        type=str,
        required=True,
        help='Start date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end',
        type=str,
        required=True,
        help='End date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--frequency',
        type=str,
        default='monthly',
        choices=['daily', 'weekly', 'monthly'],
        help='Frequency of score generation'
    )
    
    args = parser.parse_args()
    
    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)
    
    logger.info("=" * 80)
    logger.info("GERAÇÃO DE SCORES HISTÓRICOS")
    logger.info("=" * 80)
    logger.info(f"Período: {start_date} a {end_date}")
    logger.info(f"Frequência: {args.frequency}")
    logger.info("")
    
    # Gerar lista de datas
    dates = []
    current_date = start_date
    
    if args.frequency == 'monthly':
        # Último dia útil de cada mês
        while current_date <= end_date:
            # Último dia do mês
            next_month = current_date + relativedelta(months=1)
            last_day = next_month - timedelta(days=1)
            
            if last_day <= end_date:
                dates.append(last_day)
            
            current_date = next_month
    
    elif args.frequency == 'weekly':
        # Toda sexta-feira
        while current_date <= end_date:
            if current_date.weekday() == 4:  # Sexta
                dates.append(current_date)
            current_date += timedelta(days=1)
    
    else:  # daily
        # Todos os dias úteis
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Segunda a sexta
                dates.append(current_date)
            current_date += timedelta(days=1)
    
    logger.info(f"Total de datas a processar: {len(dates)}")
    logger.info("")
    
    # Processar cada data
    results = []
    for i, target_date in enumerate(dates, 1):
        logger.info(f"[{i}/{len(dates)}] {target_date}")
        result = generate_scores_for_date(target_date)
        results.append(result)
    
    # Resumo
    total_scores = sum(r['scores'] for r in results)
    skipped = sum(1 for r in results if r.get('skipped', False))
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("RESUMO")
    logger.info("=" * 80)
    logger.info(f"Datas processadas: {len(dates)}")
    logger.info(f"Datas puladas (já existiam): {skipped}")
    logger.info(f"Total de scores gerados: {total_scores}")
    logger.info("=" * 80)
    
    logger.info("")
    logger.info("⚠️  NOTA: Este script ainda não implementa o cálculo completo!")
    logger.info("⚠️  Você precisa rodar o pipeline completo para cada data histórica.")
    logger.info("")
    logger.info("Alternativa: Use a página Research do Streamlit que calcula on-the-fly!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
