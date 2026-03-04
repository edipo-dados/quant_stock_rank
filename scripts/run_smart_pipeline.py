"""
Pipeline Inteligente - Decide automaticamente entre FULL e INCREMENTAL.

Analisa o estado do banco de dados e decide:
- FULL: Se não há dados ou dados muito antigos (>7 dias sem atualização)
- INCREMENTAL: Se dados estão atualizados (última execução <7 dias)

Também gerencia:
- Ingestão de dados (preços e fundamentos)
- Cálculo de features
- Cálculo de scores
- Suavização temporal
"""

import sys
from pathlib import Path
from datetime import date, datetime, timedelta
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import PipelineExecution, RawPriceDaily, ScoreDaily
from sqlalchemy import func
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_database_state(db) -> dict:
    """
    Analisa estado do banco de dados para decidir tipo de execução.
    
    Returns:
        Dict com análise e recomendação
    """
    logger.info("Analisando estado do banco de dados...")
    
    # 1. Verificar última execução do pipeline
    last_execution = db.query(PipelineExecution).filter(
        PipelineExecution.status == 'SUCCESS'
    ).order_by(PipelineExecution.execution_date.desc()).first()
    
    # 2. Verificar última data de preços
    last_price_date = db.query(func.max(RawPriceDaily.date)).scalar()
    
    # 3. Verificar última data de scores
    last_score_date = db.query(func.max(ScoreDaily.date)).scalar()
    
    # 4. Contar registros
    price_count = db.query(RawPriceDaily).count()
    score_count = db.query(ScoreDaily).count()
    
    # 5. Verificar tickers únicos
    unique_tickers = db.query(func.count(func.distinct(RawPriceDaily.ticker))).scalar()
    
    today = date.today()
    
    analysis = {
        'last_execution': last_execution.execution_date if last_execution else None,
        'last_execution_type': last_execution.execution_type if last_execution else None,
        'last_price_date': last_price_date,
        'last_score_date': last_score_date,
        'price_count': price_count,
        'score_count': score_count,
        'unique_tickers': unique_tickers,
        'today': today
    }
    
    # Calcular dias desde última execução
    if last_execution:
        days_since_execution = (datetime.now() - last_execution.execution_date).days
    else:
        days_since_execution = 999
    
    # Calcular dias desde último preço
    if last_price_date:
        days_since_price = (today - last_price_date).days
    else:
        days_since_price = 999
    
    analysis['days_since_execution'] = days_since_execution
    analysis['days_since_price'] = days_since_price
    
    # DECISÃO: FULL ou INCREMENTAL
    reasons = []
    
    # Condições para FULL
    if price_count == 0:
        recommendation = 'FULL'
        reasons.append('Banco de dados vazio')
    elif last_execution is None:
        recommendation = 'FULL'
        reasons.append('Primeira execução')
    elif days_since_execution > 7:
        recommendation = 'FULL'
        reasons.append(f'Última execução há {days_since_execution} dias (>7)')
    elif days_since_price > 7:
        recommendation = 'FULL'
        reasons.append(f'Últimos preços há {days_since_price} dias (>7)')
    elif unique_tickers < 50:
        recommendation = 'FULL'
        reasons.append(f'Poucos tickers ({unique_tickers} < 50)')
    else:
        # Condições para INCREMENTAL
        recommendation = 'INCREMENTAL'
        reasons.append(f'Dados atualizados (última execução há {days_since_execution} dias)')
        reasons.append(f'Preços recentes (há {days_since_price} dias)')
        reasons.append(f'{unique_tickers} tickers disponíveis')
    
    analysis['recommendation'] = recommendation
    analysis['reasons'] = reasons
    
    return analysis


def print_analysis(analysis: dict):
    """Imprime análise formatada."""
    
    logger.info("=" * 80)
    logger.info("ANÁLISE DO BANCO DE DADOS")
    logger.info("=" * 80)
    
    logger.info(f"Última execução: {analysis['last_execution'] or 'Nunca'}")
    if analysis['last_execution']:
        logger.info(f"  Tipo: {analysis['last_execution_type']}")
        logger.info(f"  Há {analysis['days_since_execution']} dias")
    
    logger.info(f"\nÚltima data de preços: {analysis['last_price_date'] or 'Nenhum'}")
    if analysis['last_price_date']:
        logger.info(f"  Há {analysis['days_since_price']} dias")
    
    logger.info(f"\nÚltima data de scores: {analysis['last_score_date'] or 'Nenhum'}")
    
    logger.info(f"\nEstatísticas:")
    logger.info(f"  Preços: {analysis['price_count']:,} registros")
    logger.info(f"  Scores: {analysis['score_count']:,} registros")
    logger.info(f"  Tickers: {analysis['unique_tickers']}")
    
    logger.info(f"\n{'=' * 80}")
    logger.info(f"RECOMENDAÇÃO: {analysis['recommendation']}")
    logger.info(f"{'=' * 80}")
    
    for reason in analysis['reasons']:
        logger.info(f"  • {reason}")
    
    logger.info("")


def run_pipeline(mode: str, limit: int = 50) -> bool:
    """
    Executa pipeline de ingestão e scoring.
    
    Args:
        mode: 'full' ou 'incremental'
        limit: Número de tickers a processar
        
    Returns:
        True se sucesso, False se erro
    """
    logger.info(f"Executando pipeline {mode.upper()}...")
    
    # Determinar script a executar
    if mode == 'full':
        # Pipeline FULL: clear + run
        script = 'scripts/clear_and_run_full.py'
    else:
        # Pipeline INCREMENTAL: apenas run
        script = 'scripts/run_pipeline_docker.py'
    
    cmd = [
        'python', script,
        '--mode', 'liquid',
        '--limit', str(limit)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutos
        )
        
        if result.returncode == 0:
            logger.info("✓ Pipeline concluído com sucesso")
            
            # Mostrar últimas linhas do output
            lines = result.stdout.split('\n')
            for line in lines[-10:]:
                if line.strip():
                    logger.info(f"  {line}")
            
            return True
        else:
            logger.error("✗ Pipeline falhou")
            logger.error(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("✗ Pipeline timeout (>30 min)")
        return False
    except Exception as e:
        logger.error(f"✗ Erro ao executar pipeline: {e}")
        return False


def run_smoothing() -> bool:
    """
    Executa suavização temporal.
    
    Returns:
        True se sucesso, False se erro
    """
    logger.info("Executando suavização temporal...")
    
    cmd = [
        'python', 'scripts/apply_temporal_smoothing.py',
        '--all'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos
        )
        
        if result.returncode == 0:
            logger.info("✓ Suavização concluída com sucesso")
            return True
        else:
            logger.error("✗ Suavização falhou")
            logger.error(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("✗ Suavização timeout (>5 min)")
        return False
    except Exception as e:
        logger.error(f"✗ Erro ao executar suavização: {e}")
        return False


def main():
    """Pipeline inteligente."""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Pipeline inteligente - decide automaticamente entre FULL e INCREMENTAL'
    )
    parser.add_argument(
        '--force-full',
        action='store_true',
        help='Forçar execução FULL (ignorar análise)'
    )
    parser.add_argument(
        '--force-incremental',
        action='store_true',
        help='Forçar execução INCREMENTAL (ignorar análise)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Número de tickers a processar (default: 50)'
    )
    parser.add_argument(
        '--skip-smoothing',
        action='store_true',
        help='Pular suavização temporal'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Apenas analisar, não executar'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("PIPELINE INTELIGENTE")
    logger.info("=" * 80)
    logger.info("")
    
    db = SessionLocal()
    
    try:
        # ETAPA 1: Análise
        analysis = analyze_database_state(db)
        print_analysis(analysis)
        
        # Decidir modo de execução
        if args.force_full:
            mode = 'full'
            logger.info("⚠ Modo FULL forçado pelo usuário")
        elif args.force_incremental:
            mode = 'incremental'
            logger.info("⚠ Modo INCREMENTAL forçado pelo usuário")
        else:
            mode = analysis['recommendation'].lower()
            logger.info(f"✓ Modo {mode.upper()} recomendado pela análise")
        
        logger.info("")
        
        if args.dry_run:
            logger.info("🔍 DRY RUN - Não executando pipeline")
            logger.info(f"   Seria executado: {mode.upper()}")
            return 0
        
        # ETAPA 2: Executar pipeline
        logger.info("=" * 80)
        logger.info(f"EXECUTANDO PIPELINE {mode.upper()}")
        logger.info("=" * 80)
        logger.info("")
        
        success = run_pipeline(mode, args.limit)
        
        if not success:
            logger.error("✗ Pipeline falhou")
            return 1
        
        logger.info("")
        
        # ETAPA 3: Suavização temporal (opcional)
        if not args.skip_smoothing:
            logger.info("=" * 80)
            logger.info("SUAVIZAÇÃO TEMPORAL")
            logger.info("=" * 80)
            logger.info("")
            
            smoothing_success = run_smoothing()
            
            if not smoothing_success:
                logger.warning("⚠ Suavização falhou, mas pipeline foi concluído")
            
            logger.info("")
        
        # ETAPA 4: Resumo final
        logger.info("=" * 80)
        logger.info("RESUMO")
        logger.info("=" * 80)
        logger.info(f"Modo executado: {mode.upper()}")
        logger.info(f"Pipeline: {'✓ Sucesso' if success else '✗ Falhou'}")
        
        if not args.skip_smoothing:
            logger.info(f"Suavização: {'✓ Sucesso' if smoothing_success else '✗ Falhou'}")
        
        logger.info("")
        logger.info("Próximos passos:")
        logger.info("  1. Verificar scores: python scripts/check_latest_scores.py")
        logger.info("  2. Acessar interface Streamlit")
        logger.info("  3. Verificar ranking atualizado")
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"✗ Erro no pipeline: {e}", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
