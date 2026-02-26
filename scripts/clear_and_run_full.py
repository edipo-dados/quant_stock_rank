"""
Script para limpar dados e rodar pipeline FULL do zero.

ATENÇÃO: Este script DELETA todos os dados de:
- Preços diários (raw_prices_daily)
- Fundamentos (raw_fundamentals)
- Features diárias (features_daily)
- Features mensais (features_monthly)
- Scores diários (scores_daily)

Use com cuidado! Recomenda-se fazer backup antes.
"""

import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Adicionar o diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.models.database import SessionLocal
from app.models.schemas import (
    RawPriceDaily, 
    RawFundamental, 
    FeatureDaily, 
    FeatureMonthly, 
    ScoreDaily
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def clear_all_data(db):
    """
    Limpa todos os dados das tabelas principais.
    
    ATENÇÃO: Esta operação é IRREVERSÍVEL!
    """
    logger.warning("=" * 80)
    logger.warning("⚠️  ATENÇÃO: LIMPANDO TODOS OS DADOS DO BANCO!")
    logger.warning("=" * 80)
    
    tables_to_clear = [
        ("scores_daily", ScoreDaily),
        ("features_monthly", FeatureMonthly),
        ("features_daily", FeatureDaily),
        ("raw_fundamentals", RawFundamental),
        ("raw_prices_daily", RawPriceDaily),
    ]
    
    total_deleted = 0
    
    for table_name, model in tables_to_clear:
        try:
            count = db.query(model).count()
            logger.info(f"Deletando {count} registros de {table_name}...")
            
            db.query(model).delete()
            db.commit()
            
            total_deleted += count
            logger.info(f"✅ {table_name}: {count} registros deletados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar {table_name}: {e}")
            db.rollback()
            raise
    
    logger.info(f"\n✅ Total de registros deletados: {total_deleted}")
    logger.info("Banco de dados limpo com sucesso!")


def run_full_pipeline(mode: str, limit: int):
    """
    Executa o pipeline FULL após limpar os dados.
    """
    logger.info("\n" + "=" * 80)
    logger.info("🚀 INICIANDO PIPELINE FULL")
    logger.info("=" * 80)
    
    # Importar e executar o pipeline
    from scripts.run_pipeline_docker import run_pipeline_docker
    from app.ingestion.b3_liquid_stocks import fetch_most_liquid_stocks
    
    # Buscar tickers
    if mode == 'liquid':
        logger.info(f"Buscando {limit} ativos mais líquidos da B3...")
        tickers = fetch_most_liquid_stocks(limit=limit)
    elif mode == 'test':
        logger.info("Modo teste: usando 5 ativos fixos")
        tickers = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA']
    else:
        raise ValueError(f"Modo inválido: {mode}. Use 'liquid' ou 'test'")
    
    logger.info(f"Tickers selecionados: {tickers}")
    
    # Executar pipeline com force_full=True
    run_pipeline_docker(tickers=tickers, force_full=True)
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ PIPELINE FULL CONCLUÍDO COM SUCESSO!")
    logger.info("=" * 80)


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Limpa dados e roda pipeline FULL do zero',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Limpar e rodar com 10 ativos mais líquidos
  python scripts/clear_and_run_full.py --mode liquid --limit 10

  # Limpar e rodar com 50 ativos (produção)
  python scripts/clear_and_run_full.py --mode liquid --limit 50

  # Limpar e rodar modo teste (5 ativos fixos)
  python scripts/clear_and_run_full.py --mode test

  # Apenas limpar dados (sem rodar pipeline)
  python scripts/clear_and_run_full.py --clear-only

ATENÇÃO: Este script DELETA todos os dados! Use com cuidado!
        """
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['liquid', 'test'],
        default='liquid',
        help='Modo de execução: liquid (B3 líquidos) ou test (5 ativos fixos)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Número de ativos para modo liquid (default: 10)'
    )
    
    parser.add_argument(
        '--clear-only',
        action='store_true',
        help='Apenas limpar dados sem rodar pipeline'
    )
    
    parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='Não pedir confirmação (use com cuidado!)'
    )
    
    args = parser.parse_args()
    
    # Confirmação de segurança
    if not args.no_confirm:
        logger.warning("\n" + "=" * 80)
        logger.warning("⚠️  ATENÇÃO: OPERAÇÃO DESTRUTIVA!")
        logger.warning("=" * 80)
        logger.warning("Este script irá DELETAR TODOS OS DADOS do banco:")
        logger.warning("  - Preços diários")
        logger.warning("  - Fundamentos")
        logger.warning("  - Features")
        logger.warning("  - Scores")
        logger.warning("\nRecomenda-se fazer backup antes de continuar!")
        logger.warning("=" * 80)
        
        confirmation = input("\nDigite 'CONFIRMAR' para continuar: ")
        
        if confirmation != 'CONFIRMAR':
            logger.info("Operação cancelada pelo usuário.")
            return
    
    # Conectar ao banco
    db = SessionLocal()
    
    try:
        # Limpar dados
        clear_all_data(db)
        
        # Rodar pipeline se não for clear-only
        if not args.clear_only:
            run_full_pipeline(args.mode, args.limit)
        else:
            logger.info("\n✅ Dados limpos. Pipeline não foi executado (--clear-only)")
        
    except Exception as e:
        logger.error(f"\n❌ Erro durante execução: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == '__main__':
    main()
