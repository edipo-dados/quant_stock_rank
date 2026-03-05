#!/usr/bin/env python3
"""
Script para validar dados antes de executar backtest.

Uso:
    python scripts/validate_backtest_data.py --start-date 2021-01-01 --end-date 2026-03-05
"""

import sys
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import argparse
from datetime import datetime
import logging

from app.models.database import SessionLocal
from app.backtest.validator import BacktestDataValidator

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Valida dados para backtest."""
    parser = argparse.ArgumentParser(description='Valida dados para backtest')
    parser.add_argument('--start-date', required=True, help='Data inicial (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='Data final (YYYY-MM-DD)')
    parser.add_argument('--top-n', type=int, default=10, help='Número de ativos (default: 10)')
    
    args = parser.parse_args()
    
    # Parse dates
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
    except ValueError as e:
        logger.error(f"Erro ao parsear datas: {e}")
        sys.exit(1)
    
    # Validar
    db = SessionLocal()
    try:
        validator = BacktestDataValidator(db)
        
        logger.info(f"Validando dados para backtest:")
        logger.info(f"  Período: {start_date} a {end_date}")
        logger.info(f"  Top N: {args.top_n}")
        logger.info("")
        
        result = validator.validate_universe(
            start_date=start_date,
            end_date=end_date,
            min_scores_required=args.top_n
        )
        
        validator.log_validation_summary(result)
        
        if not result['valid']:
            logger.error("\n❌ Validação falhou! Corrija os erros antes de executar backtest.")
            sys.exit(1)
        else:
            logger.info("\n✅ Validação passou! Dados suficientes para backtest.")
            sys.exit(0)
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
