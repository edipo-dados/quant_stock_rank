"""
Pipeline otimizado para Docker com proteção contra rate limiting.

Características:
- Bulk requests para reduzir número de chamadas
- Sleep entre requisições para evitar bloqueio
- Modo full (primeira execução) e incremental (atualizações)
- Retry automático em caso de falha
"""

import logging
import sys
import time
from datetime import date, datetime, timedelta
from typing import List, Dict
from pathlib import Path

# Adicionar o diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy.orm import Session

from app.config import settings
from app.models.database import SessionLocal
from app.models.schemas import RawPriceDaily, RawFundamental, PipelineExecution
from app.ingestion.yahoo_client import YahooFinanceClient
from app.ingestion.yahoo_finance_client import YahooFinanceClient as YahooFundamentalsClient
from app.ingestion.ingestion_service import IngestionService
from app.ingestion.b3_liquid_stocks import fetch_most_liquid_stocks
from app.factor_engine.fundamental_factors import FundamentalFactorCalculator
from app.factor_engine.momentum_factors import MomentumFactorCalculator
from app.factor_engine.normalizer import CrossSectionalNormalizer
from app.factor_engine.feature_service import FeatureService
from app.scoring.scoring_engine import ScoringEngine
from app.scoring.ranker import Ranker
from app.scoring.score_service import ScoreService
from app.confidence.confidence_engine import ConfidenceEngine

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline_docker.log')
    ]
)

logger = logging.getLogger(__name__)

# Configurações de rate limiting
SLEEP_BETWEEN_TICKERS = 2  # segundos entre cada ticker
SLEEP_BETWEEN_BATCHES = 5  # segundos entre batches
BATCH_SIZE = 5  # número de tickers por batch
MAX_RETRIES = 3  # tentativas máximas por ticker


class PipelineExecutionTracker:
    """Gerencia o rastreamento de execuções do pipeline."""
    
    def __init__(self, db: Session):
        self.db = db
        self.execution = None
    
    def start_execution(
        self,
        execution_type: str,
        mode: str,
        tickers: List[str],
        data_start_date: date,
        data_end_date: date
    ):
        """Inicia uma nova execução do pipeline."""
        self.execution = PipelineExecution(
            execution_date=datetime.utcnow(),
            execution_type=execution_type,
            mode=mode,
            status='RUNNING',
            started_at=datetime.utcnow(),
            tickers_processed=0,
            tickers_success=0,
            tickers_failed=0,
            prices_ingested=0,
            fundamentals_ingested=0,
            features_calculated=0,
            scores_calculated=0,
            data_start_date=data_start_date,
            data_end_date=data_end_date,
            tickers_list=tickers,
            error_log=[],
            config_snapshot={
                'momentum_weight': settings.momentum_weight,
                'quality_weight': settings.quality_weight,
                'value_weight': settings.value_weight,
                'sleep_between_tickers': SLEEP_BETWEEN_TICKERS,
                'sleep_between_batches': SLEEP_BETWEEN_BATCHES,
                'batch_size': BATCH_SIZE
            }
        )
        self.db.add(self.execution)
        self.db.commit()
        logger.info(f"Execucao iniciada: ID={self.execution.id}, Tipo={execution_type}, Modo={mode}")
        return self.execution
    
    def update_stats(
        self,
        tickers_processed: int = None,
        tickers_success: int = None,
        tickers_failed: int = None,
        prices_ingested: int = None,
        fundamentals_ingested: int = None,
        features_calculated: int = None,
        scores_calculated: int = None
    ):
        """Atualiza estatísticas da execução."""
        if not self.execution:
            return
        
        if tickers_processed is not None:
            self.execution.tickers_processed = tickers_processed
        if tickers_success is not None:
            self.execution.tickers_success = tickers_success
        if tickers_failed is not None:
            self.execution.tickers_failed = tickers_failed
        if prices_ingested is not None:
            self.execution.prices_ingested = prices_ingested
        if fundamentals_ingested is not None:
            self.execution.fundamentals_ingested = fundamentals_ingested
        if features_calculated is not None:
            self.execution.features_calculated = features_calculated
        if scores_calculated is not None:
            self.execution.scores_calculated = scores_calculated
        
        self.db.commit()
    
    def complete_execution(self, status: str = 'SUCCESS'):
        """Finaliza a execução."""
        if not self.execution:
            return
        
        self.execution.status = status
        self.execution.completed_at = datetime.utcnow()
        self.db.commit()
        
        duration = (self.execution.completed_at - self.execution.started_at).total_seconds()
        logger.info(f"Execucao finalizada: ID={self.execution.id}, Status={status}, Duracao={duration:.1f}s")


def check_if_full_run_needed(db: Session) -> bool:
    """
    Verifica se precisa fazer uma execução completa.
    
    Returns:
        True se não há dados ou dados muito antigos (>7 dias)
    """
    try:
        # Verificar se há dados de preços
        latest_price = db.query(RawPriceDaily).order_by(
            RawPriceDaily.date.desc()
        ).first()
        
        if not latest_price:
            logger.info("Nenhum dado encontrado. Executando modo FULL.")
            return True
        
        # Verificar se dados são recentes (últimos 7 dias)
        days_old = (date.today() - latest_price.date).days
        if days_old > 7:
            logger.info(f"Dados com {days_old} dias. Executando modo FULL.")
            return True
        
        logger.info(f"Dados recentes ({days_old} dias). Executando modo INCREMENTAL.")
        return False
        
    except Exception as e:
        logger.warning(f"Erro ao verificar dados: {e}. Executando modo FULL.")
        return True


def ingest_prices_with_rate_limit(
    db: Session,
    tickers: List[str],
    lookback_days: int,
    is_full: bool = True
) -> Dict:
    """
    Ingere preços com rate limiting e retry.
    
    Args:
        db: Sessão do banco
        tickers: Lista de tickers
        lookback_days: Dias históricos (full) ou dias recentes (incremental)
        is_full: Se True, busca histórico completo. Se False, apenas últimos dias.
    """
    logger.info(f"Iniciando ingestão de preços ({'FULL' if is_full else 'INCREMENTAL'})")
    
    yahoo_client = YahooFinanceClient()
    ingestion_service = IngestionService(yahoo_client, YahooFundamentalsClient(), db)
    
    success = []
    failed = []
    total_records = 0
    
    # Processar em batches
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(tickers) + BATCH_SIZE - 1) // BATCH_SIZE
        
        logger.info(f"Processando batch {batch_num}/{total_batches}: {batch}")
        
        for ticker in batch:
            retry_count = 0
            while retry_count < MAX_RETRIES:
                try:
                    # Calcular período
                    if is_full:
                        # Modo full: buscar histórico completo
                        start_date = (date.today() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
                    else:
                        # Modo incremental: buscar apenas últimos dias
                        start_date = (date.today() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
                    
                    end_date = date.today().strftime('%Y-%m-%d')
                    
                    # Buscar dados
                    logger.info(f"Buscando preços para {ticker} ({start_date} a {end_date})")
                    df = yahoo_client.fetch_daily_prices(ticker, start_date, end_date)
                    
                    if df is not None and not df.empty:
                        # Persistir no banco
                        records_added = 0
                        for _, row in df.iterrows():
                            try:
                                # Verificar se já existe (para modo incremental)
                                existing = db.query(RawPriceDaily).filter(
                                    RawPriceDaily.ticker == ticker,
                                    RawPriceDaily.date == row['date']
                                ).first()
                                
                                if existing:
                                    # Atualizar
                                    existing.open = row['open']
                                    existing.high = row['high']
                                    existing.low = row['low']
                                    existing.close = row['close']
                                    existing.volume = row['volume']
                                    existing.adj_close = row['adj_close']
                                else:
                                    # Inserir novo
                                    price_record = RawPriceDaily(
                                        ticker=ticker,
                                        date=row['date'],
                                        open=row['open'],
                                        high=row['high'],
                                        low=row['low'],
                                        close=row['close'],
                                        volume=row['volume'],
                                        adj_close=row['adj_close']
                                    )
                                    db.add(price_record)
                                
                                records_added += 1
                            except Exception as e:
                                logger.warning(f"Erro ao inserir registro para {ticker}: {e}")
                                continue
                        
                        db.commit()
                        total_records += records_added
                        success.append(ticker)
                        logger.info(f"[OK] {ticker}: {records_added} registros")
                        break  # Sucesso, sair do retry loop
                    else:
                        logger.warning(f"Sem dados para {ticker}")
                        failed.append({"ticker": ticker, "error": "No data"})
                        break
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count < MAX_RETRIES:
                        logger.warning(f"Erro em {ticker} (tentativa {retry_count}/{MAX_RETRIES}): {e}")
                        time.sleep(SLEEP_BETWEEN_TICKERS * 2)  # Sleep maior no retry
                    else:
                        logger.error(f"✗ {ticker}: Falhou após {MAX_RETRIES} tentativas")
                        failed.append({"ticker": ticker, "error": str(e)})
            
            # Sleep entre tickers
            time.sleep(SLEEP_BETWEEN_TICKERS)
        
        # Sleep entre batches
        if i + BATCH_SIZE < len(tickers):
            logger.info(f"Aguardando {SLEEP_BETWEEN_BATCHES}s antes do próximo batch...")
            time.sleep(SLEEP_BETWEEN_BATCHES)
    
    logger.info(f"Preços: {len(success)} sucesso, {len(failed)} falhas, {total_records} registros")
    
    return {
        "success": success,
        "failed": failed,
        "total_records": total_records
    }


def ingest_fundamentals_with_rate_limit(
    db: Session,
    tickers: List[str],
    is_full: bool = True
) -> Dict:
    """
    Ingere fundamentos com rate limiting e retry.
    """
    logger.info(f"Iniciando ingestão de fundamentos ({'FULL' if is_full else 'INCREMENTAL'})")
    
    yahoo_fundamentals_client = YahooFundamentalsClient()
    ingestion_service = IngestionService(YahooFinanceClient(), yahoo_fundamentals_client, db)
    
    success = []
    failed = []
    total_records = 0
    
    # Processar em batches
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(tickers) + BATCH_SIZE - 1) // BATCH_SIZE
        
        logger.info(f"Processando batch {batch_num}/{total_batches}: {batch}")
        
        for ticker in batch:
            retry_count = 0
            while retry_count < MAX_RETRIES:
                try:
                    logger.info(f"Buscando fundamentos para {ticker}")
                    
                    # Buscar e salvar fundamentos usando o método correto
                    result = ingestion_service.ingest_fundamentals([ticker], period='annual')
                    
                    if result['success']:
                        total_records += result['total_records']
                        success.append(ticker)
                        logger.info(f"[OK] {ticker}: {result['total_records']} registros")
                        break
                    else:
                        error_msg = result['failed'][0]['error'] if result['failed'] else "No data"
                        logger.warning(f"Sem fundamentos para {ticker}: {error_msg}")
                        failed.append({"ticker": ticker, "error": error_msg})
                        break
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count < MAX_RETRIES:
                        logger.warning(f"Erro em {ticker} (tentativa {retry_count}/{MAX_RETRIES}): {e}")
                        time.sleep(SLEEP_BETWEEN_TICKERS * 2)
                    else:
                        logger.error(f"✗ {ticker}: Falhou após {MAX_RETRIES} tentativas")
                        failed.append({"ticker": ticker, "error": str(e)})
            
            # Sleep entre tickers
            time.sleep(SLEEP_BETWEEN_TICKERS)
        
        # Sleep entre batches
        if i + BATCH_SIZE < len(tickers):
            logger.info(f"Aguardando {SLEEP_BETWEEN_BATCHES}s antes do próximo batch...")
            time.sleep(SLEEP_BETWEEN_BATCHES)
    
    logger.info(f"Fundamentos: {len(success)} sucesso, {len(failed)} falhas, {total_records} registros")
    
    return {
        "success": success,
        "failed": failed,
        "total_records": total_records
    }


def run_pipeline_docker(
    tickers: List[str],
    force_full: bool = False
):
    """
    Executa pipeline otimizado para Docker.
    
    Args:
        tickers: Lista de tickers
        force_full: Forçar execução completa mesmo se houver dados recentes
    """
    logger.info("=" * 80)
    logger.info("PIPELINE DOCKER - OTIMIZADO PARA RATE LIMITING")
    logger.info("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Verificar se precisa executar full ou incremental
        is_full = force_full or check_if_full_run_needed(db)
        
        if is_full:
            logger.info("MODO: FULL (histórico completo)")
            lookback_days = 400  # ~1 ano de dados
        else:
            logger.info("MODO: INCREMENTAL (apenas atualizações)")
            lookback_days = 7  # Última semana
        
        # Calcular datas
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Iniciar rastreamento de execução
        tracker = PipelineExecutionTracker(db)
        tracker.start_execution(
            execution_type='FULL' if is_full else 'INCREMENTAL',
            mode='liquid' if len(tickers) > 10 else 'test',
            tickers=tickers,
            data_start_date=start_date,
            data_end_date=end_date
        )
        
        # ETAPA 1: Ingestão de Preços
        logger.info("\n" + "=" * 80)
        logger.info("ETAPA 1: INGESTÃO DE PREÇOS")
        logger.info("=" * 80)
        
        price_results = ingest_prices_with_rate_limit(db, tickers, lookback_days, is_full)
        
        # Atualizar estatísticas
        tracker.update_stats(
            prices_ingested=price_results['total_records']
        )
        
        # ETAPA 2: Ingestão de Fundamentos (apenas em modo full ou se não existir)
        logger.info("\n" + "=" * 80)
        logger.info("ETAPA 2: INGESTÃO DE FUNDAMENTOS")
        logger.info("=" * 80)
        
        if is_full:
            fundamental_results = ingest_fundamentals_with_rate_limit(db, tickers, is_full)
        else:
            # No modo incremental, verificar quais tickers não têm fundamentos
            tickers_without_fundamentals = []
            for ticker in tickers:
                has_fundamentals = db.query(RawFundamental).filter(
                    RawFundamental.ticker == ticker
                ).first()
                if not has_fundamentals:
                    tickers_without_fundamentals.append(ticker)
            
            if tickers_without_fundamentals:
                logger.info(f"Buscando fundamentos para {len(tickers_without_fundamentals)} tickers sem dados")
                fundamental_results = ingest_fundamentals_with_rate_limit(
                    db, tickers_without_fundamentals, True
                )
            else:
                logger.info("Todos os tickers já possuem fundamentos. Pulando...")
                fundamental_results = {"success": tickers, "failed": [], "total_records": 0}
        
        # Atualizar estatísticas
        tracker.update_stats(
            fundamentals_ingested=fundamental_results['total_records']
        )
        
        # ETAPA 3: Processar features e scores (usar pipeline original)
        logger.info("\n" + "=" * 80)
        logger.info("ETAPA 3: PROCESSAMENTO DE FEATURES E SCORES")
        logger.info("=" * 80)
        
        from scripts.run_pipeline import (
            calculate_momentum_features,
            calculate_fundamental_features,
            normalize_features,
            calculate_scores,
            generate_ranking
        )
        
        # Filtro de elegibilidade
        feature_service = FeatureService(db)
        eligible_tickers, exclusion_reasons = feature_service.filter_eligible_assets(
            tickers, date.today()
        )
        
        logger.info(f"Elegibilidade: {len(eligible_tickers)} elegíveis, {len(exclusion_reasons)} excluídos")
        
        # Calcular features
        momentum_stats = calculate_momentum_features(db, eligible_tickers, date.today())
        fundamental_stats = calculate_fundamental_features(db, eligible_tickers, date.today())
        
        # Normalizar
        normalize_features(db, date.today())
        
        # Calcular scores
        scoring_stats = calculate_scores(db, eligible_tickers, date.today(), exclusion_reasons)
        
        # Gerar ranking
        ranking_size = generate_ranking(db, date.today())
        
        # Atualizar estatísticas finais
        tracker.update_stats(
            tickers_processed=len(tickers),
            tickers_success=len(price_results['success']),
            tickers_failed=len(price_results['failed']),
            features_calculated=len(eligible_tickers),
            scores_calculated=ranking_size
        )
        
        # Finalizar execução com sucesso
        tracker.complete_execution(status='SUCCESS')
        
        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE CONCLUÍDO COM SUCESSO")
        logger.info("=" * 80)
        logger.info(f"Modo: {'FULL' if is_full else 'INCREMENTAL'}")
        logger.info(f"Preços: {len(price_results['success'])} tickers, {price_results['total_records']} registros")
        logger.info(f"Fundamentos: {len(fundamental_results['success'])} tickers, {fundamental_results['total_records']} registros")
        logger.info(f"Elegíveis: {len(eligible_tickers)}")
        logger.info(f"Ranking: {ranking_size} ativos")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Pipeline falhou: {e}", exc_info=True)
        # Finalizar execução com falha
        if 'tracker' in locals():
            tracker.complete_execution(status='FAILED')
        raise
    finally:
        db.close()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Pipeline Docker com rate limiting')
    parser.add_argument(
        '--mode',
        choices=['test', 'liquid', 'manual'],
        default='test',
        help='Modo de seleção de ativos'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Número de ativos líquidos (mode=liquid)'
    )
    parser.add_argument(
        '--tickers',
        nargs='+',
        help='Lista de tickers (mode=manual)'
    )
    parser.add_argument(
        '--force-full',
        action='store_true',
        help='Forçar execução completa mesmo com dados recentes'
    )
    
    args = parser.parse_args()
    
    # Selecionar tickers
    if args.mode == 'test':
        logger.info("Modo TEST: 5 ativos para teste")
        tickers = ["ITUB4.SA", "BBDC4.SA", "PETR4.SA", "VALE3.SA", "MGLU3.SA"]
    
    elif args.mode == 'liquid':
        logger.info(f"Modo LIQUID: Top {args.limit} ativos mais líquidos")
        try:
            tickers = fetch_most_liquid_stocks(limit=args.limit)
            if not tickers:
                logger.error("Nenhum ativo líquido encontrado!")
                return 1
        except Exception as e:
            logger.error(f"Erro ao buscar ativos líquidos: {e}")
            return 1
    
    elif args.mode == 'manual':
        if not args.tickers:
            logger.error("Modo MANUAL requer --tickers")
            return 1
        logger.info(f"Modo MANUAL: {len(args.tickers)} ativos customizados")
        tickers = args.tickers
    
    # Executar pipeline
    try:
        run_pipeline_docker(tickers, force_full=args.force_full)
        return 0
    except Exception as e:
        logger.error(f"Pipeline falhou: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
