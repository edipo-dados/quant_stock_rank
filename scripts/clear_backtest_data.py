"""
Script para limpar dados de backtest antigos.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.backtest.models import BacktestRun, BacktestNAV, BacktestPosition, BacktestMetrics
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clear_all_backtests():
    """Limpa todos os dados de backtest."""
    
    db = SessionLocal()
    
    try:
        # Contar registros antes
        runs_count = db.query(BacktestRun).count()
        nav_count = db.query(BacktestNAV).count()
        positions_count = db.query(BacktestPosition).count()
        metrics_count = db.query(BacktestMetrics).count()
        
        logger.info("=" * 80)
        logger.info("LIMPEZA DE DADOS DE BACKTEST")
        logger.info("=" * 80)
        logger.info(f"Registros encontrados:")
        logger.info(f"  Runs: {runs_count}")
        logger.info(f"  NAV: {nav_count}")
        logger.info(f"  Positions: {positions_count}")
        logger.info(f"  Metrics: {metrics_count}")
        logger.info("")
        
        if runs_count == 0:
            logger.info("Nenhum dado de backtest encontrado")
            return 0
        
        # Deletar tudo (cascade vai deletar relacionados)
        db.query(BacktestRun).delete()
        db.commit()
        
        logger.info("✓ Todos os dados de backtest foram removidos")
        logger.info("=" * 80)
        
        return runs_count
        
    except Exception as e:
        logger.error(f"✗ Erro ao limpar dados: {e}")
        db.rollback()
        return 0
    finally:
        db.close()


def clear_backtest_by_name(name: str):
    """Limpa dados de um backtest específico por nome."""
    
    db = SessionLocal()
    
    try:
        # Buscar runs com esse nome
        runs = db.query(BacktestRun).filter(BacktestRun.name == name).all()
        
        if not runs:
            logger.info(f"Nenhum backtest encontrado com nome: {name}")
            return 0
        
        logger.info("=" * 80)
        logger.info(f"LIMPEZA DE BACKTEST: {name}")
        logger.info("=" * 80)
        logger.info(f"Encontrados {len(runs)} run(s)")
        logger.info("")
        
        for run in runs:
            logger.info(f"Removendo run {run.id}:")
            logger.info(f"  Período: {run.start_date} a {run.end_date}")
            logger.info(f"  Criado em: {run.created_at}")
            
            # Deletar (cascade vai deletar relacionados)
            db.delete(run)
        
        db.commit()
        
        logger.info("")
        logger.info(f"✓ {len(runs)} backtest(s) removido(s)")
        logger.info("=" * 80)
        
        return len(runs)
        
    except Exception as e:
        logger.error(f"✗ Erro ao limpar backtest: {e}")
        db.rollback()
        return 0
    finally:
        db.close()


def list_backtests():
    """Lista todos os backtests salvos."""
    
    db = SessionLocal()
    
    try:
        runs = db.query(BacktestRun).order_by(BacktestRun.created_at.desc()).all()
        
        if not runs:
            logger.info("Nenhum backtest encontrado")
            return
        
        logger.info("=" * 80)
        logger.info("BACKTESTS SALVOS")
        logger.info("=" * 80)
        
        for run in runs:
            logger.info(f"\nID: {run.id}")
            logger.info(f"Nome: {run.name or '(sem nome)'}")
            logger.info(f"Período: {run.start_date} a {run.end_date}")
            logger.info(f"Top N: {run.top_n}")
            logger.info(f"Criado em: {run.created_at}")
            
            # Contar registros relacionados
            nav_count = db.query(BacktestNAV).filter(BacktestNAV.run_id == run.id).count()
            pos_count = db.query(BacktestPosition).filter(BacktestPosition.run_id == run.id).count()
            
            logger.info(f"Registros: {nav_count} NAV, {pos_count} posições")
        
        logger.info("")
        logger.info("=" * 80)
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Gerenciar dados de backtest')
    parser.add_argument(
        '--action',
        type=str,
        choices=['list', 'clear-all', 'clear-name'],
        required=True,
        help='Ação a executar'
    )
    parser.add_argument(
        '--name',
        type=str,
        help='Nome do backtest (para clear-name)'
    )
    
    args = parser.parse_args()
    
    if args.action == 'list':
        list_backtests()
    elif args.action == 'clear-all':
        clear_all_backtests()
    elif args.action == 'clear-name':
        if not args.name:
            logger.error("--name é obrigatório para clear-name")
            sys.exit(1)
        clear_backtest_by_name(args.name)
