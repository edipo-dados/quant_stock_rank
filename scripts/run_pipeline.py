"""
Script de pipeline completo para execução diária do sistema de ranking.

Este script orquestra todas as etapas do pipeline:
1. Ingestão de dados (preços e fundamentos)
2. Cálculo de fatores (momentum e fundamentalistas)
3. Normalização cross-sectional
4. Cálculo de scores
5. Geração de ranking

Valida: Requisitos 1.1-1.7, 2.1-2.10, 3.1-3.8, 4.1-4.7, 5.1-5.5
"""

import logging
import sys
from datetime import date, datetime, timedelta
from typing import List, Dict
import pandas as pd
from pathlib import Path

# Adicionar o diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy.orm import Session

from app.config import settings
from app.models.database import SessionLocal, engine
from app.models.schemas import RawPriceDaily, RawFundamental
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
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline.log')
    ]
)

logger = logging.getLogger(__name__)


def run_daily_pipeline(
    tickers: List[str],
    pipeline_date: date = None,
    lookback_days: int = 365
) -> Dict:
    """
    Executa o pipeline completo de ranking diário.
    
    Etapas:
    1. Ingestão de dados de preços e fundamentos
    2. Cálculo de fatores de momentum
    3. Cálculo de fatores fundamentalistas
    4. Normalização cross-sectional
    5. Cálculo de scores
    6. Geração de ranking
    
    Args:
        tickers: Lista de símbolos de ações a processar
        pipeline_date: Data do pipeline (default: hoje)
        lookback_days: Dias históricos de preços a buscar (default: 365)
    
    Returns:
        Dict com estatísticas do pipeline:
        {
            "date": data do pipeline,
            "tickers_processed": número de tickers processados,
            "ingestion": estatísticas de ingestão,
            "features": estatísticas de features,
            "scores": estatísticas de scores,
            "ranking_size": tamanho do ranking final,
            "errors": lista de erros encontrados
        }
    
    Valida: Requisitos 1.1-1.7, 2.1-2.10, 3.1-3.8, 4.1-4.7, 5.1-5.5
    """
    if pipeline_date is None:
        pipeline_date = date.today()
    
    logger.info("=" * 80)
    logger.info(f"Starting daily pipeline for {pipeline_date}")
    logger.info(f"Processing {len(tickers)} tickers")
    logger.info("=" * 80)
    
    # Inicializar estatísticas
    stats = {
        "date": pipeline_date,
        "tickers_processed": 0,
        "ingestion": {},
        "features": {},
        "scores": {},
        "ranking_size": 0,
        "errors": []
    }
    
    # Criar sessão de banco de dados
    db = SessionLocal()
    
    try:
        # ===== ETAPA 1: INGESTÃO DE DADOS =====
        logger.info("\n" + "=" * 80)
        logger.info("ETAPA 1: INGESTÃO DE DADOS")
        logger.info("=" * 80)
        
        ingestion_stats = run_ingestion(db, tickers, lookback_days)
        stats["ingestion"] = ingestion_stats
        
        # ===== ETAPA 1.5: FILTRO DE ELEGIBILIDADE =====
        logger.info("\n" + "=" * 80)
        logger.info("ETAPA 1.5: FILTRO DE ELEGIBILIDADE")
        logger.info("=" * 80)
        
        feature_service = FeatureService(db)
        eligible_tickers, exclusion_reasons = feature_service.filter_eligible_assets(
            tickers,
            pipeline_date
        )
        
        logger.info(
            f"Eligibility filter: {len(eligible_tickers)} eligible, "
            f"{len(exclusion_reasons)} excluded"
        )
        
        # Log exclusion summary
        if exclusion_reasons:
            logger.info("\nExcluded assets:")
            for ticker, reasons in exclusion_reasons.items():
                logger.info(f"  {ticker}: {', '.join(reasons)}")
        
        stats["eligibility"] = {
            "eligible": eligible_tickers,
            "excluded": exclusion_reasons,
            "total_eligible": len(eligible_tickers),
            "total_excluded": len(exclusion_reasons)
        }
        
        # ===== ETAPA 2: CÁLCULO DE FATORES DE MOMENTUM =====
        logger.info("\n" + "=" * 80)
        logger.info("ETAPA 2: CÁLCULO DE FATORES DE MOMENTUM")
        logger.info("=" * 80)
        
        # Calcular apenas para ativos elegíveis
        momentum_stats = calculate_momentum_features(db, eligible_tickers, pipeline_date)
        stats["features"]["momentum"] = momentum_stats
        
        # ===== ETAPA 3: CÁLCULO DE FATORES FUNDAMENTALISTAS =====
        logger.info("\n" + "=" * 80)
        logger.info("ETAPA 3: CÁLCULO DE FATORES FUNDAMENTALISTAS")
        logger.info("=" * 80)
        
        # Calcular apenas para ativos elegíveis
        fundamental_stats = calculate_fundamental_features(db, eligible_tickers, pipeline_date)
        stats["features"]["fundamental"] = fundamental_stats
        
        # ===== ETAPA 4: NORMALIZAÇÃO CROSS-SECTIONAL =====
        logger.info("\n" + "=" * 80)
        logger.info("ETAPA 4: NORMALIZAÇÃO CROSS-SECTIONAL")
        logger.info("=" * 80)
        
        normalize_features(db, pipeline_date)
        
        # ===== ETAPA 5: CÁLCULO DE SCORES =====
        logger.info("\n" + "=" * 80)
        logger.info("ETAPA 5: CÁLCULO DE SCORES")
        logger.info("=" * 80)
        
        # Passar ativos elegíveis e razões de exclusão
        scoring_stats = calculate_scores(db, eligible_tickers, pipeline_date, exclusion_reasons)
        stats["scores"] = scoring_stats
        
        # ===== ETAPA 6: GERAÇÃO DE RANKING =====
        logger.info("\n" + "=" * 80)
        logger.info("ETAPA 6: GERAÇÃO DE RANKING")
        logger.info("=" * 80)
        
        ranking_size = generate_ranking(db, pipeline_date)
        stats["ranking_size"] = ranking_size
        
        # Calcular tickers processados com sucesso
        stats["tickers_processed"] = ranking_size
        
        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE COMPLETO COM SUCESSO")
        logger.info(f"Data: {pipeline_date}")
        logger.info(f"Tickers elegíveis: {len(eligible_tickers)}")
        logger.info(f"Tickers excluídos: {len(exclusion_reasons)}")
        logger.info(f"Tickers processados: {stats['tickers_processed']}")
        logger.info(f"Ranking gerado com {ranking_size} ativos")
        logger.info("=" * 80)
        
        return stats
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        stats["errors"].append(str(e))
        raise
        
    finally:
        db.close()


def run_ingestion(
    db: Session,
    tickers: List[str],
    lookback_days: int
) -> Dict:
    """
    Executa ingestão de dados de preços e fundamentos.
    
    Valida: Requisitos 1.1-1.7
    """
    logger.info("Inicializando clientes de dados...")
    
    # Inicializar clientes
    yahoo_client = YahooFinanceClient()
    yahoo_fundamentals_client = YahooFundamentalsClient()
    ingestion_service = IngestionService(yahoo_client, yahoo_fundamentals_client, db)
    
    # Ingerir preços
    logger.info(f"Ingerindo preços para {len(tickers)} tickers...")
    price_results = ingestion_service.ingest_prices(tickers, lookback_days)
    
    logger.info(
        f"Preços: {len(price_results['success'])} sucesso, "
        f"{len(price_results['failed'])} falhas, "
        f"{price_results['total_records']} registros"
    )
    
    # Ingerir fundamentos
    logger.info(f"Ingerindo fundamentos para {len(tickers)} tickers...")
    fundamental_results = ingestion_service.ingest_fundamentals(tickers)
    
    logger.info(
        f"Fundamentos: {len(fundamental_results['success'])} sucesso, "
        f"{len(fundamental_results['failed'])} falhas, "
        f"{fundamental_results['total_records']} registros"
    )
    
    return {
        "prices": price_results,
        "fundamentals": fundamental_results
    }


def calculate_momentum_features(
    db: Session,
    tickers: List[str],
    feature_date: date
) -> Dict:
    """
    Calcula fatores de momentum para todos os tickers.
    
    Valida: Requisitos 3.1-3.8
    """
    logger.info(f"Calculando fatores de momentum para {feature_date}...")
    
    calculator = MomentumFactorCalculator()
    feature_service = FeatureService(db)
    
    success = []
    failed = []
    
    for ticker in tickers:
        try:
            # Buscar preços históricos
            prices_query = db.query(RawPriceDaily).filter(
                RawPriceDaily.ticker == ticker,
                RawPriceDaily.date <= feature_date
            ).order_by(RawPriceDaily.date.asc()).all()
            
            if not prices_query:
                logger.warning(f"No price data found for {ticker}")
                failed.append({"ticker": ticker, "error": "No price data"})
                continue
            
            # Converter para DataFrame
            prices_df = pd.DataFrame([
                {
                    'date': p.date,
                    'adj_close': p.adj_close
                }
                for p in prices_query
            ])
            
            # Calcular fatores
            factors = calculator.calculate_all_factors(ticker, prices_df)
            
            # Verificar se pelo menos um fator foi calculado
            if all(v is None for v in factors.values()):
                logger.warning(f"Could not calculate any momentum factors for {ticker}")
                failed.append({"ticker": ticker, "error": "No factors calculated"})
                continue
            
            # Salvar features (sem normalização ainda)
            feature_service.save_daily_features(ticker, feature_date, factors)
            
            success.append(ticker)
            logger.debug(f"Calculated momentum factors for {ticker}")
            
        except Exception as e:
            logger.error(f"Error calculating momentum factors for {ticker}: {e}")
            failed.append({"ticker": ticker, "error": str(e)})
            continue
    
    logger.info(
        f"Momentum features: {len(success)} sucesso, {len(failed)} falhas"
    )
    
    return {
        "success": success,
        "failed": failed,
        "total": len(success)
    }


def calculate_fundamental_features(
    db: Session,
    tickers: List[str],
    feature_date: date
) -> Dict:
    """
    Calcula fatores fundamentalistas para todos os tickers.
    
    Valida: Requisitos 2.1-2.10
    """
    logger.info(f"Calculando fatores fundamentalistas para {feature_date}...")
    
    calculator = FundamentalFactorCalculator()
    feature_service = FeatureService(db)
    
    # Primeiro dia do mês para features mensais
    month_start = date(feature_date.year, feature_date.month, 1)
    
    success = []
    failed = []
    
    for ticker in tickers:
        try:
            # Buscar dados fundamentalistas mais recentes
            fundamentals_query = db.query(RawFundamental).filter(
                RawFundamental.ticker == ticker,
                RawFundamental.period_end_date <= feature_date
            ).order_by(RawFundamental.period_end_date.desc()).all()
            
            if not fundamentals_query:
                logger.warning(f"No fundamental data found for {ticker}")
                failed.append({"ticker": ticker, "error": "No fundamental data"})
                continue
            
            # Dados mais recentes
            latest_fundamental = fundamentals_query[0]
            
            # Converter para dict
            fundamentals_data = {
                'net_income': latest_fundamental.net_income,
                'shareholders_equity': latest_fundamental.shareholders_equity,
                'revenue': latest_fundamental.revenue,
                'total_debt': latest_fundamental.total_debt,
                'ebitda': latest_fundamental.ebitda,
                'eps': latest_fundamental.eps,
                'enterprise_value': latest_fundamental.enterprise_value,
                'book_value_per_share': latest_fundamental.book_value_per_share
            }
            
            # Histórico para crescimento de receita e ROE (últimos 3-4 anos)
            fundamentals_history = [
                {
                    'revenue': f.revenue,
                    'net_income': f.net_income,
                    'shareholders_equity': f.shareholders_equity
                }
                for f in fundamentals_query[:4]  # Últimos 4 períodos anuais
            ]
            fundamentals_history.reverse()  # Ordem cronológica
            
            # Buscar preço atual
            latest_price_query = db.query(RawPriceDaily).filter(
                RawPriceDaily.ticker == ticker,
                RawPriceDaily.date <= feature_date
            ).order_by(RawPriceDaily.date.desc()).first()
            
            current_price = latest_price_query.adj_close if latest_price_query else None
            
            # Calcular fatores
            factors = calculator.calculate_all_factors(
                ticker,
                fundamentals_data,
                fundamentals_history,
                current_price,
                db_session=db
            )
            
            # Verificar se pelo menos um fator foi calculado
            if all(v is None for v in factors.values()):
                logger.warning(f"Could not calculate any fundamental factors for {ticker}")
                failed.append({"ticker": ticker, "error": "No factors calculated"})
                continue
            
            # Salvar features (sem normalização ainda)
            feature_service.save_monthly_features(ticker, month_start, factors)
            
            success.append(ticker)
            logger.debug(f"Calculated fundamental factors for {ticker}")
            
        except Exception as e:
            logger.error(f"Error calculating fundamental factors for {ticker}: {e}")
            failed.append({"ticker": ticker, "error": str(e)})
            continue
    
    logger.info(
        f"Fundamental features: {len(success)} sucesso, {len(failed)} falhas"
    )
    
    return {
        "success": success,
        "failed": failed,
        "total": len(success)
    }


def normalize_features(
    db: Session,
    feature_date: date
):
    """
    Normaliza features usando z-score cross-sectional.
    
    Valida: Requisitos 2.8, 3.6
    """
    logger.info("Normalizando features cross-sectionally...")
    
    normalizer = CrossSectionalNormalizer()
    feature_service = FeatureService(db)
    
    # Normalizar features diárias (momentum)
    logger.info("Normalizando features diárias...")
    daily_features = feature_service.get_all_daily_features_for_date(feature_date)
    
    if daily_features:
        # Converter para DataFrame
        daily_df = pd.DataFrame([
            {
                'ticker': f.ticker,
                'return_6m': f.return_6m,
                'return_12m': f.return_12m,
                'rsi_14': f.rsi_14,
                'volatility_90d': f.volatility_90d,
                'recent_drawdown': f.recent_drawdown
            }
            for f in daily_features
        ]).set_index('ticker')
        
        # Normalizar
        factor_columns = ['return_6m', 'return_12m', 'rsi_14', 'volatility_90d', 'recent_drawdown']
        normalized_daily = normalizer.normalize_factors(daily_df, factor_columns)
        
        # Atualizar no banco
        for ticker in normalized_daily.index:
            normalized_factors = normalized_daily.loc[ticker].to_dict()
            feature_service.save_daily_features(ticker, feature_date, normalized_factors)
        
        logger.info(f"Normalized {len(normalized_daily)} daily features")
    else:
        logger.warning("No daily features found to normalize")
    
    # Normalizar features mensais (fundamentalistas)
    logger.info("Normalizando features mensais...")
    month_start = date(feature_date.year, feature_date.month, 1)
    monthly_features = feature_service.get_all_monthly_features_for_month(month_start)
    
    if monthly_features:
        # Converter para DataFrame
        monthly_df = pd.DataFrame([
            {
                'ticker': f.ticker,
                'roe': f.roe,
                'net_margin': f.net_margin,
                'revenue_growth_3y': f.revenue_growth_3y,
                'debt_to_ebitda': f.debt_to_ebitda,
                'pe_ratio': f.pe_ratio,
                'ev_ebitda': f.ev_ebitda,
                'pb_ratio': f.pb_ratio
            }
            for f in monthly_features
        ]).set_index('ticker')
        
        # Normalizar
        factor_columns = ['roe', 'net_margin', 'revenue_growth_3y', 'debt_to_ebitda', 
                         'pe_ratio', 'ev_ebitda', 'pb_ratio']
        normalized_monthly = normalizer.normalize_factors(monthly_df, factor_columns)
        
        # Atualizar no banco
        for ticker in normalized_monthly.index:
            normalized_factors = normalized_monthly.loc[ticker].to_dict()
            feature_service.save_monthly_features(ticker, month_start, normalized_factors)
        
        logger.info(f"Normalized {len(normalized_monthly)} monthly features")
    else:
        logger.warning("No monthly features found to normalize")


def calculate_scores(
    db: Session,
    tickers: List[str],
    score_date: date,
    exclusion_reasons: Dict[str, List[str]] = None
) -> Dict:
    """
    Calcula scores para todos os tickers.
    
    Args:
        db: Sessão do banco de dados
        tickers: Lista de tickers (apenas elegíveis)
        score_date: Data do score
        exclusion_reasons: Dict mapeando tickers excluídos para suas razões
    
    Valida: Requisitos 4.1-4.7, 1.1, 1.6, 5.3, 5.5
    """
    logger.info(f"Calculando scores para {score_date}...")
    
    if exclusion_reasons is None:
        exclusion_reasons = {}
    
    # Inicializar engines
    scoring_engine = ScoringEngine(settings)
    confidence_engine = ConfidenceEngine()
    feature_service = FeatureService(db)
    score_service = ScoreService(db)
    
    month_start = date(score_date.year, score_date.month, 1)
    
    success = []
    failed = []
    score_results = []
    
    # Processar ativos elegíveis
    for ticker in tickers:
        try:
            # Buscar features diárias
            daily_features = feature_service.get_daily_features(ticker, score_date)
            
            if not daily_features:
                logger.warning(f"No daily features found for {ticker}")
                failed.append({"ticker": ticker, "error": "No daily features"})
                continue
            
            # Buscar features mensais
            monthly_features = feature_service.get_monthly_features(ticker, month_start)
            
            if not monthly_features:
                logger.warning(f"No monthly features found for {ticker}")
                failed.append({"ticker": ticker, "error": "No monthly features"})
                continue
            
            # Converter para dicts
            momentum_factors = {
                'return_6m': daily_features.return_6m,
                'return_12m': daily_features.return_12m,
                'rsi_14': daily_features.rsi_14,
                'volatility_90d': daily_features.volatility_90d,
                'recent_drawdown': daily_features.recent_drawdown
            }
            
            fundamental_factors = {
                'roe': monthly_features.roe,
                'net_margin': monthly_features.net_margin,
                'revenue_growth_3y': monthly_features.revenue_growth_3y,
                'debt_to_ebitda': monthly_features.debt_to_ebitda,
                'pe_ratio': monthly_features.pe_ratio,
                'ev_ebitda': monthly_features.ev_ebitda,
                'pb_ratio': monthly_features.pb_ratio
            }
            
            # Calcular score (ativo passou no filtro de elegibilidade)
            score_result = scoring_engine.score_asset(
                ticker,
                fundamental_factors,
                momentum_factors
            )
            
            # Marcar como elegível
            score_result.passed_eligibility = True
            score_result.exclusion_reasons = []
            
            # Calcular confiança
            confidence = confidence_engine.calculate_confidence(ticker, score_result)
            score_result.confidence = confidence
            
            # Salvar score (sem rank ainda)
            score_service.save_score(score_result, score_date)
            
            success.append(ticker)
            score_results.append(score_result)
            logger.debug(f"Calculated score for {ticker}: {score_result.final_score:.3f}")
            
        except Exception as e:
            logger.error(f"Error calculating score for {ticker}: {e}")
            failed.append({"ticker": ticker, "error": str(e)})
            continue
    
    # Processar ativos excluídos (criar ScoreResult com passed_eligibility=False)
    for ticker, reasons in exclusion_reasons.items():
        try:
            # Criar ScoreResult com valores zerados mas com informação de exclusão
            score_result = scoring_engine.score_asset(
                ticker,
                {},  # Fatores vazios
                {}   # Fatores vazios
            )
            
            # Marcar como não elegível
            score_result.passed_eligibility = False
            score_result.exclusion_reasons = reasons
            score_result.final_score = 0.0
            score_result.base_score = 0.0
            score_result.confidence = 0.0
            
            # Salvar score (para manter registro de exclusão)
            score_service.save_score(score_result, score_date)
            
            logger.debug(f"Saved exclusion record for {ticker}: {', '.join(reasons)}")
            
        except Exception as e:
            logger.error(f"Error saving exclusion record for {ticker}: {e}")
            continue
    
    logger.info(
        f"Scores: {len(success)} sucesso, {len(failed)} falhas, "
        f"{len(exclusion_reasons)} excluídos"
    )
    
    return {
        "success": success,
        "failed": failed,
        "excluded": list(exclusion_reasons.keys()),
        "total": len(success),
        "score_results": score_results
    }


def generate_ranking(
    db: Session,
    ranking_date: date
) -> int:
    """
    Gera ranking e atualiza ranks no banco.
    
    Valida: Requisitos 5.1-5.5
    """
    logger.info(f"Gerando ranking para {ranking_date}...")
    
    score_service = ScoreService(db)
    
    # Atualizar ranks
    num_updated = score_service.update_ranks(ranking_date)
    
    logger.info(f"Ranking gerado com {num_updated} ativos")
    
    # Mostrar top 10
    top_10 = score_service.get_top_n_scores(ranking_date, 10)
    
    if top_10:
        logger.info("\nTop 10 Ativos:")
        logger.info("-" * 60)
        for score in top_10:
            logger.info(
                f"{score.rank:2d}. {score.ticker:6s} - Score: {score.final_score:6.3f} "
                f"(M:{score.momentum_score:5.2f} Q:{score.quality_score:5.2f} V:{score.value_score:5.2f})"
            )
        logger.info("-" * 60)
    
    return num_updated


def main():
    """
    Função principal para execução do pipeline.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Executa o pipeline de ranking de ações')
    parser.add_argument(
        '--mode',
        choices=['test', 'liquid', 'manual'],
        default='test',
        help='Modo de seleção de ativos: test (5 ativos), liquid (top líquidos), manual (lista customizada)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Número de ativos mais líquidos a processar (apenas para mode=liquid)'
    )
    parser.add_argument(
        '--tickers',
        nargs='+',
        help='Lista de tickers para processar (apenas para mode=manual)'
    )
    
    args = parser.parse_args()
    
    # Selecionar tickers baseado no modo
    if args.mode == 'test':
        logger.info("Modo TEST: Processando 5 ativos para teste")
        tickers = [
            # Bancos
            "ITUB4.SA", "BBDC4.SA",
            
            # Petróleo
            "PETR4.SA",
            
            # Varejo
            "MGLU3.SA",
            
            # Americanas (para testar exclusão)
            "AMER3.SA"
        ]
    
    elif args.mode == 'liquid':
        logger.info(f"Modo LIQUID: Buscando top {args.limit} ativos mais líquidos da B3")
        try:
            tickers = fetch_most_liquid_stocks(limit=args.limit)
            if not tickers:
                logger.error("Nenhum ativo líquido encontrado!")
                return 1
            logger.info(f"Encontrados {len(tickers)} ativos líquidos para processar")
        except Exception as e:
            logger.error(f"Erro ao buscar ativos líquidos: {e}", exc_info=True)
            return 1
    
    elif args.mode == 'manual':
        if not args.tickers:
            logger.error("Modo MANUAL requer --tickers")
            return 1
        logger.info(f"Modo MANUAL: Processando {len(args.tickers)} ativos customizados")
        tickers = args.tickers
    
    # Executar pipeline com lookback de 400 dias para ter dados suficientes para 12m return
    try:
        stats = run_daily_pipeline(tickers, lookback_days=400)
        
        logger.info("\n" + "=" * 80)
        logger.info("RESUMO DO PIPELINE")
        logger.info("=" * 80)
        logger.info(f"Data: {stats['date']}")
        logger.info(f"Tickers processados: {stats['tickers_processed']}")
        logger.info(f"Ranking gerado: {stats['ranking_size']} ativos")
        
        if stats['errors']:
            logger.warning(f"\nErros encontrados: {len(stats['errors'])}")
            for error in stats['errors']:
                logger.warning(f"  - {error}")
        
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
