"""
Script para executar backtest de estratégia quantitativa.
"""

import sys
from pathlib import Path
from datetime import date
import argparse
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.backtest.backtest_engine import BacktestEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Executa backtest."""
    
    parser = argparse.ArgumentParser(
        description='Run backtest of quantitative strategy'
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
        '--top-n',
        type=int,
        default=10,
        help='Number of assets to select (default: 10)'
    )
    parser.add_argument(
        '--weight-method',
        type=str,
        default='equal',
        choices=['equal', 'score_weighted'],
        help='Weight method (default: equal)'
    )
    parser.add_argument(
        '--use-smoothing',
        action='store_true',
        help='Use smoothed scores'
    )
    parser.add_argument(
        '--name',
        type=str,
        default='backtest',
        help='Backtest name (default: backtest)'
    )
    
    args = parser.parse_args()
    
    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)
    
    logger.info("=" * 80)
    logger.info("BACKTEST DE ESTRATÉGIA QUANTITATIVA")
    logger.info("=" * 80)
    logger.info(f"Período: {start_date} a {end_date}")
    logger.info(f"Top N: {args.top_n}")
    logger.info(f"Método de peso: {args.weight_method}")
    logger.info(f"Suavização: {args.use_smoothing}")
    logger.info("")
    
    # Criar engine de backtest
    engine = BacktestEngine(
        start_date=start_date,
        end_date=end_date,
        top_n=args.top_n,
        rebalance_frequency='monthly',
        weight_method=args.weight_method,
        use_smoothing=args.use_smoothing,
        risk_free_rate=0.0
    )
    
    # Executar backtest
    db = SessionLocal()
    
    try:
        logger.info("Executando backtest...")
        result = engine.run_backtest(db)
        
        # Exibir resultados
        metrics = result['metrics']
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("RESULTADOS DO BACKTEST")
        logger.info("=" * 80)
        logger.info(f"Retorno Total: {metrics['total_return']:.2f}%")
        logger.info(f"CAGR: {metrics['cagr']:.2f}%")
        logger.info(f"Volatilidade: {metrics['volatility']:.2f}%")
        logger.info(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        logger.info(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
        logger.info(f"Turnover Médio: {metrics['avg_turnover']:.2f}%")
        logger.info(f"Rebalanceamentos: {metrics['num_rebalances']}")
        logger.info(f"Trades: {metrics['num_trades']}")
        logger.info("=" * 80)
        
        # Salvar resultado
        logger.info("")
        logger.info("Salvando resultado...")
        engine.save_backtest_result(args.name, result, db)
        
        logger.info("")
        logger.info("✓ Backtest concluído com sucesso")
        return 0
        
    except Exception as e:
        logger.error(f"✗ Erro no backtest: {e}", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
