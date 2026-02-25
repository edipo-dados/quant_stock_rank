"""
Script para executar backtest de estratégias quantitativas.

Executa backtest mensal com:
- Snapshot mensal do ranking
- Seleção Top N
- Equal weight ou score weighted
- Rebalanceamento mensal
- Cálculo de métricas (CAGR, Sharpe, Max Drawdown, etc.)
"""

import sys
from pathlib import Path
from datetime import date
from dateutil.relativedelta import relativedelta
import argparse

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.backtest.backtest_engine import BacktestEngine
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Executa backtest."""
    
    parser = argparse.ArgumentParser(description='Run backtest')
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date (YYYY-MM-DD). Default: 1 year ago'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date (YYYY-MM-DD). Default: today'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=10,
        help='Number of assets to select. Default: 10'
    )
    parser.add_argument(
        '--weight-method',
        type=str,
        choices=['equal', 'score_weighted'],
        default='equal',
        help='Weighting method. Default: equal'
    )
    parser.add_argument(
        '--use-smoothing',
        action='store_true',
        help='Use smoothed scores'
    )
    parser.add_argument(
        '--risk-free-rate',
        type=float,
        default=0.0,
        help='Risk-free rate (annualized). Default: 0.0'
    )
    parser.add_argument(
        '--name',
        type=str,
        help='Backtest name. Default: auto-generated'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save results to database'
    )
    
    args = parser.parse_args()
    
    # Determinar datas
    if args.end_date:
        end_date = date.fromisoformat(args.end_date)
    else:
        end_date = date.today()
    
    if args.start_date:
        start_date = date.fromisoformat(args.start_date)
    else:
        start_date = end_date - relativedelta(years=1)
    
    # Nome do backtest
    if args.name:
        backtest_name = args.name
    else:
        smoothing_str = "_smoothed" if args.use_smoothing else ""
        backtest_name = f"backtest_top{args.top_n}_{args.weight_method}{smoothing_str}_{start_date}_{end_date}"
    
    logger.info("=" * 80)
    logger.info("BACKTEST")
    logger.info("=" * 80)
    logger.info(f"Name: {backtest_name}")
    logger.info(f"Period: {start_date} to {end_date}")
    logger.info(f"Top N: {args.top_n}")
    logger.info(f"Weight method: {args.weight_method}")
    logger.info(f"Use smoothing: {args.use_smoothing}")
    logger.info(f"Risk-free rate: {args.risk_free_rate * 100:.2f}%")
    logger.info("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Criar engine de backtest
        engine = BacktestEngine(
            start_date=start_date,
            end_date=end_date,
            top_n=args.top_n,
            rebalance_frequency='monthly',
            weight_method=args.weight_method,
            use_smoothing=args.use_smoothing,
            risk_free_rate=args.risk_free_rate
        )
        
        # Executar backtest
        result = engine.run_backtest(db)
        
        # Exibir resultados
        logger.info("\n" + "=" * 80)
        logger.info("RESULTS")
        logger.info("=" * 80)
        
        metrics = result['metrics']
        logger.info(f"Total Return: {metrics['total_return']:.2f}%")
        logger.info(f"CAGR: {metrics['cagr']:.2f}%")
        logger.info(f"Volatility: {metrics['volatility']:.2f}%")
        logger.info(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        logger.info(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
        logger.info(f"Avg Turnover: {metrics['avg_turnover']:.2f}%")
        logger.info(f"Num Rebalances: {metrics['num_rebalances']}")
        logger.info(f"Num Trades: {metrics['num_trades']}")
        
        # Salvar se solicitado
        if args.save:
            logger.info("\nSaving results to database...")
            saved_result = engine.save_backtest_result(backtest_name, result, db)
            logger.info(f"✓ Saved backtest result (ID: {saved_result.id})")
        
        logger.info("=" * 80)
        logger.info("BACKTEST COMPLETED")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
