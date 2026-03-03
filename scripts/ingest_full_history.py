"""
Script para ingestão completa de histórico de preços e fundamentos.

Expande dados históricos para todos os tickers da B3 já cadastrados,
garantindo base robusta para backtests de 5 anos.

Uso:
    python scripts/ingest_full_history.py --start 2018-01-01
    python scripts/ingest_full_history.py --start 2018-01-01 --mode incremental
    python scripts/ingest_full_history.py --start 2018-01-01 --skip-validation
"""

import sys
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.models.database import SessionLocal
from app.ingestion.historical_expansion import HistoricalExpansion
from app.ingestion.data_validation import DataValidator

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ingest_full_history.log')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Executa ingestão completa de histórico."""
    
    parser = argparse.ArgumentParser(
        description='Ingest full historical data for all B3 tickers'
    )
    parser.add_argument(
        '--start',
        type=str,
        default='2018-01-01',
        help='Start date for price history (YYYY-MM-DD). Default: 2018-01-01'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['full', 'incremental'],
        default='full',
        help='Ingestion mode: full (from start date) or incremental (from last date). Default: full'
    )
    parser.add_argument(
        '--max-workers',
        type=int,
        default=5,
        help='Maximum number of parallel workers. Default: 5'
    )
    parser.add_argument(
        '--skip-prices',
        action='store_true',
        help='Skip price ingestion'
    )
    parser.add_argument(
        '--skip-fundamentals',
        action='store_true',
        help='Skip fundamental ingestion'
    )
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip data validation'
    )
    parser.add_argument(
        '--tickers',
        type=str,
        help='Comma-separated list of specific tickers to process (optional)'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("INGESTÃO COMPLETA DE HISTÓRICO")
    logger.info("=" * 80)
    logger.info(f"Data inicial: {args.start}")
    logger.info(f"Modo: {args.mode}")
    logger.info(f"Workers paralelos: {args.max_workers}")
    logger.info(f"Skip preços: {args.skip_prices}")
    logger.info(f"Skip fundamentos: {args.skip_fundamentals}")
    logger.info(f"Skip validação: {args.skip_validation}")
    logger.info("=" * 80)
    
    db = SessionLocal()
    
    try:
        # ====================================================================
        # ETAPA 1: CARREGAR TICKERS
        # ====================================================================
        logger.info("\n" + "=" * 80)
        logger.info("ETAPA 1: CARREGAR TICKERS DA BASE")
        logger.info("=" * 80)
        
        expander = HistoricalExpansion(db)
        
        if args.tickers:
            # Usar tickers específicos
            tickers = [t.strip() for t in args.tickers.split(',')]
            logger.info(f"Usando tickers específicos: {tickers}")
        else:
            # Buscar todos os tickers do banco
            tickers = expander.get_all_tickers_from_db()
        
        if not tickers:
            logger.error("Nenhum ticker encontrado!")
            return 1
        
        logger.info(f"Total de tickers a processar: {len(tickers)}")
        
        # ====================================================================
        # ETAPA 2: INGESTÃO DE PREÇOS HISTÓRICOS
        # ====================================================================
        if not args.skip_prices:
            logger.info("\n" + "=" * 80)
            logger.info("ETAPA 2: INGESTÃO DE PREÇOS HISTÓRICOS")
            logger.info("=" * 80)
            
            price_results = expander.expand_prices_parallel(
                tickers=tickers,
                start_date=args.start,
                mode=args.mode,
                max_workers=args.max_workers,
                delay_seconds=1.0
            )
            
            logger.info("\nResultado da ingestão de preços:")
            logger.info(f"  Total: {price_results['total_tickers']}")
            logger.info(f"  Sucesso: {price_results['success_count']}")
            logger.info(f"  Falhas: {price_results['failed_count']}")
            logger.info(f"  Registros inseridos: {price_results['total_records']}")
        else:
            logger.info("\n⏭️  Pulando ingestão de preços")
            price_results = None
        
        # ====================================================================
        # ETAPA 3: INGESTÃO DE FUNDAMENTOS HISTÓRICOS
        # ====================================================================
        if not args.skip_fundamentals:
            logger.info("\n" + "=" * 80)
            logger.info("ETAPA 3: INGESTÃO DE FUNDAMENTOS HISTÓRICOS")
            logger.info("=" * 80)
            
            fundamental_results = expander.expand_fundamentals_parallel(
                tickers=tickers,
                max_workers=args.max_workers,
                delay_seconds=2.0
            )
            
            logger.info("\nResultado da ingestão de fundamentos:")
            logger.info(f"  Total: {fundamental_results['total_tickers']}")
            logger.info(f"  Sucesso: {fundamental_results['success_count']}")
            logger.info(f"  Falhas: {fundamental_results['failed_count']}")
            logger.info(f"  Registros inseridos: {fundamental_results['total_records']}")
            logger.info(f"  Tickers com < 3 anos: {len(fundamental_results['insufficient_tickers'])}")
            
            if fundamental_results['insufficient_tickers']:
                logger.info("\nTickers com histórico insuficiente:")
                for item in fundamental_results['insufficient_tickers'][:10]:
                    logger.info(f"  {item['ticker']}: {item['years_available']} anos")
                if len(fundamental_results['insufficient_tickers']) > 10:
                    logger.info(f"  ... e mais {len(fundamental_results['insufficient_tickers']) - 10}")
        else:
            logger.info("\n⏭️  Pulando ingestão de fundamentos")
            fundamental_results = None
        
        # ====================================================================
        # ETAPA 4: VALIDAÇÃO DE DADOS
        # ====================================================================
        if not args.skip_validation:
            logger.info("\n" + "=" * 80)
            logger.info("ETAPA 4: VALIDAÇÃO TÉCNICA DE DADOS")
            logger.info("=" * 80)
            
            validator = DataValidator(db)
            validation_results = validator.validate_all_tickers(tickers)
            
            # Salvar relatório
            report_path = Path('data_quality_report.json')
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(validation_results, f, indent=2, default=str)
            
            logger.info(f"\n✓ Relatório salvo em: {report_path}")
        else:
            logger.info("\n⏭️  Pulando validação de dados")
            validation_results = None
        
        # ====================================================================
        # ETAPA 5: RELATÓRIO FINAL
        # ====================================================================
        logger.info("\n" + "=" * 80)
        logger.info("RELATÓRIO FINAL")
        logger.info("=" * 80)
        
        if price_results:
            logger.info("\n📊 PREÇOS:")
            logger.info(f"  Tickers processados: {price_results['total_tickers']}")
            logger.info(f"  Sucesso: {price_results['success_count']} ({price_results['success_count']/price_results['total_tickers']*100:.1f}%)")
            logger.info(f"  Falhas: {price_results['failed_count']}")
            logger.info(f"  Total de registros: {price_results['total_records']:,}")
        
        if fundamental_results:
            logger.info("\n💼 FUNDAMENTOS:")
            logger.info(f"  Tickers processados: {fundamental_results['total_tickers']}")
            logger.info(f"  Sucesso: {fundamental_results['success_count']} ({fundamental_results['success_count']/fundamental_results['total_tickers']*100:.1f}%)")
            logger.info(f"  Falhas: {fundamental_results['failed_count']}")
            logger.info(f"  Total de registros: {fundamental_results['total_records']:,}")
            logger.info(f"  Tickers com < 3 anos: {len(fundamental_results['insufficient_tickers'])}")
        
        if validation_results:
            logger.info("\n✅ VALIDAÇÃO:")
            summary = validation_results['summary']
            logger.info(f"  Preços válidos: {summary['valid_prices']} ({summary['price_validation_rate']}%)")
            logger.info(f"  Fundamentos válidos: {summary['valid_fundamentals']} ({summary['fundamental_validation_rate']}%)")
            logger.info(f"  Prontos para backtest: {summary['valid_for_backtest']} ({summary['backtest_ready_rate']}%)")
            logger.info(f"  Insuficientes: {summary['insufficient_for_backtest']}")
            logger.info("\n  Estatísticas de anos:")
            logger.info(f"    Mínimo: {summary['years_stats']['min']} anos")
            logger.info(f"    Máximo: {summary['years_stats']['max']} anos")
            logger.info(f"    Média: {summary['years_stats']['avg']} anos")
            logger.info(f"    Mediana: {summary['years_stats']['median']} anos")
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ INGESTÃO COMPLETA FINALIZADA COM SUCESSO")
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"Erro durante execução: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
