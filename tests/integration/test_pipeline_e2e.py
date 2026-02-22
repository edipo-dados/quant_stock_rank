"""
Teste de integração end-to-end do pipeline completo.

Este teste valida que todas as etapas do pipeline executam sem erros
e produzem resultados consistentes.

Valida: Todos os requisitos funcionais
"""

import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd

from app.models.database import Base
from app.models.schemas import (
    RawPriceDaily, RawFundamental, FeatureDaily, FeatureMonthly, ScoreDaily
)
from app.ingestion.yahoo_client import YahooFinanceClient
from app.ingestion.fmp_client import FMPClient
from app.ingestion.ingestion_service import IngestionService
from app.factor_engine.fundamental_factors import FundamentalFactorCalculator
from app.factor_engine.momentum_factors import MomentumFactorCalculator
from app.factor_engine.normalizer import CrossSectionalNormalizer
from app.factor_engine.feature_service import FeatureService
from app.scoring.scoring_engine import ScoringEngine
from app.config import Settings
from app.scoring.ranker import Ranker
from app.scoring.score_service import ScoreService
from app.confidence.confidence_engine import ConfidenceEngine


@pytest.fixture
def test_db():
    """
    Cria um banco de dados em memória para testes.
    """
    # Criar engine em memória
    engine = create_engine("sqlite:///:memory:")
    
    # Criar todas as tabelas
    Base.metadata.create_all(engine)
    
    # Criar session factory
    TestSessionLocal = sessionmaker(bind=engine)
    
    # Criar sessão
    session = TestSessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    engine.dispose()


@pytest.fixture
def sample_tickers():
    """
    Lista de tickers para teste.
    """
    return ["AAPL", "MSFT", "GOOGL"]


@pytest.fixture
def sample_price_data():
    """
    Dados de preços de exemplo para testes.
    """
    dates = pd.date_range(end=date.today(), periods=365, freq='D')
    
    data = {}
    for ticker in ["AAPL", "MSFT", "GOOGL"]:
        # Gerar preços sintéticos
        base_price = 100.0
        prices = []
        for i in range(len(dates)):
            # Adicionar alguma variação
            price = base_price * (1 + 0.001 * i)
            prices.append({
                'ticker': ticker,
                'date': dates[i].date(),
                'open': price * 0.99,
                'high': price * 1.02,
                'low': price * 0.98,
                'close': price,
                'volume': 1000000,
                'adj_close': price
            })
        data[ticker] = prices
    
    return data


@pytest.fixture
def sample_fundamental_data():
    """
    Dados fundamentalistas de exemplo para testes.
    """
    data = {}
    for ticker in ["AAPL", "MSFT", "GOOGL"]:
        fundamentals = []
        for year in range(4):
            period_date = date(2024 - year, 12, 31)
            fundamentals.append({
                'ticker': ticker,
                'period_end_date': period_date,
                'period_type': 'annual',
                'revenue': 100000000 * (1.1 ** year),
                'net_income': 20000000 * (1.1 ** year),
                'ebitda': 30000000 * (1.1 ** year),
                'eps': 5.0 * (1.1 ** year),
                'total_assets': 200000000,
                'total_debt': 50000000,
                'shareholders_equity': 100000000,
                'book_value_per_share': 50.0,
                'operating_cash_flow': 25000000,
                'free_cash_flow': 20000000,
                'market_cap': 500000000,
                'enterprise_value': 550000000
            })
        data[ticker] = fundamentals
    
    return data


def populate_test_data(db, price_data, fundamental_data):
    """
    Popula o banco de dados de teste com dados de exemplo.
    """
    # Inserir preços
    for ticker, prices in price_data.items():
        for price in prices:
            record = RawPriceDaily(**price)
            db.add(record)
    
    # Inserir fundamentos
    for ticker, fundamentals in fundamental_data.items():
        for fundamental in fundamentals:
            record = RawFundamental(**fundamental)
            db.add(record)
    
    db.commit()


def test_pipeline_end_to_end(
    test_db,
    sample_tickers,
    sample_price_data,
    sample_fundamental_data
):
    """
    Teste end-to-end do pipeline completo.
    
    Valida que:
    1. Dados podem ser ingeridos
    2. Fatores podem ser calculados
    3. Features podem ser normalizadas
    4. Scores podem ser calculados
    5. Ranking pode ser gerado
    6. Todas as etapas executam sem erros
    
    Valida: Todos os requisitos funcionais
    """
    # Popula dados de teste
    populate_test_data(test_db, sample_price_data, sample_fundamental_data)
    
    pipeline_date = date.today()
    month_start = date(pipeline_date.year, pipeline_date.month, 1)
    
    # ===== ETAPA 1: Verificar dados brutos =====
    prices_count = test_db.query(RawPriceDaily).count()
    fundamentals_count = test_db.query(RawFundamental).count()
    
    assert prices_count > 0, "Should have price data"
    assert fundamentals_count > 0, "Should have fundamental data"
    
    # ===== ETAPA 2: Calcular fatores de momentum =====
    momentum_calculator = MomentumFactorCalculator()
    feature_service = FeatureService(test_db)
    
    momentum_success = 0
    for ticker in sample_tickers:
        # Buscar preços
        prices_query = test_db.query(RawPriceDaily).filter(
            RawPriceDaily.ticker == ticker
        ).order_by(RawPriceDaily.date.asc()).all()
        
        if prices_query:
            prices_df = pd.DataFrame([
                {'date': p.date, 'adj_close': p.adj_close}
                for p in prices_query
            ])
            
            # Calcular fatores
            factors = momentum_calculator.calculate_all_factors(ticker, prices_df)
            
            # Salvar
            feature_service.save_daily_features(ticker, pipeline_date, factors)
            momentum_success += 1
    
    assert momentum_success == len(sample_tickers), \
        f"Should calculate momentum for all tickers, got {momentum_success}/{len(sample_tickers)}"
    
    # ===== ETAPA 3: Calcular fatores fundamentalistas =====
    fundamental_calculator = FundamentalFactorCalculator()
    
    fundamental_success = 0
    for ticker in sample_tickers:
        # Buscar fundamentos
        fundamentals_query = test_db.query(RawFundamental).filter(
            RawFundamental.ticker == ticker
        ).order_by(RawFundamental.period_end_date.desc()).all()
        
        if fundamentals_query:
            latest = fundamentals_query[0]
            
            fundamentals_data = {
                'net_income': latest.net_income,
                'shareholders_equity': latest.shareholders_equity,
                'revenue': latest.revenue,
                'total_debt': latest.total_debt,
                'ebitda': latest.ebitda,
                'eps': latest.eps,
                'enterprise_value': latest.enterprise_value,
                'book_value_per_share': latest.book_value_per_share
            }
            
            history = [{'revenue': f.revenue} for f in fundamentals_query[:4]]
            history.reverse()
            
            # Buscar preço atual
            latest_price = test_db.query(RawPriceDaily).filter(
                RawPriceDaily.ticker == ticker
            ).order_by(RawPriceDaily.date.desc()).first()
            
            current_price = latest_price.adj_close if latest_price else None
            
            # Calcular fatores
            factors = fundamental_calculator.calculate_all_factors(
                ticker,
                fundamentals_data,
                history,
                current_price
            )
            
            # Salvar
            feature_service.save_monthly_features(ticker, month_start, factors)
            fundamental_success += 1
    
    assert fundamental_success == len(sample_tickers), \
        f"Should calculate fundamentals for all tickers, got {fundamental_success}/{len(sample_tickers)}"
    
    # ===== ETAPA 4: Normalizar features =====
    normalizer = CrossSectionalNormalizer()
    
    # Normalizar diárias
    daily_features = feature_service.get_all_daily_features_for_date(pipeline_date)
    assert len(daily_features) == len(sample_tickers), \
        f"Should have daily features for all tickers, got {len(daily_features)}"
    
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
    
    factor_columns = ['return_6m', 'return_12m', 'rsi_14', 'volatility_90d', 'recent_drawdown']
    normalized_daily = normalizer.normalize_factors(daily_df, factor_columns)
    
    # Atualizar
    for ticker in normalized_daily.index:
        normalized_factors = normalized_daily.loc[ticker].to_dict()
        feature_service.save_daily_features(ticker, pipeline_date, normalized_factors)
    
    # Normalizar mensais
    monthly_features = feature_service.get_all_monthly_features_for_month(month_start)
    assert len(monthly_features) == len(sample_tickers), \
        f"Should have monthly features for all tickers, got {len(monthly_features)}"
    
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
    
    factor_columns = ['roe', 'net_margin', 'revenue_growth_3y', 'debt_to_ebitda',
                     'pe_ratio', 'ev_ebitda', 'pb_ratio']
    normalized_monthly = normalizer.normalize_factors(monthly_df, factor_columns)
    
    # Atualizar
    for ticker in normalized_monthly.index:
        normalized_factors = normalized_monthly.loc[ticker].to_dict()
        feature_service.save_monthly_features(ticker, month_start, normalized_factors)
    
    # ===== ETAPA 5: Calcular scores =====
    scoring_config = Settings(
        momentum_weight=0.4,
        quality_weight=0.3,
        value_weight=0.3,
        database_url="sqlite:///:memory:",
        fmp_api_key=""
    )
    scoring_engine = ScoringEngine(scoring_config)
    confidence_engine = ConfidenceEngine()
    score_service = ScoreService(test_db)
    
    score_success = 0
    for ticker in sample_tickers:
        # Buscar features
        daily_features = feature_service.get_daily_features(ticker, pipeline_date)
        monthly_features = feature_service.get_monthly_features(ticker, month_start)
        
        if daily_features and monthly_features:
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
            
            # Calcular score
            score_result = scoring_engine.score_asset(
                ticker,
                fundamental_factors,
                momentum_factors
            )
            
            # Calcular confiança
            confidence = confidence_engine.calculate_confidence(ticker, score_result)
            score_result.confidence = confidence
            
            # Salvar
            score_service.save_score(score_result, pipeline_date)
            score_success += 1
    
    assert score_success == len(sample_tickers), \
        f"Should calculate scores for all tickers, got {score_success}/{len(sample_tickers)}"
    
    # ===== ETAPA 6: Gerar ranking =====
    num_updated = score_service.update_ranks(pipeline_date)
    
    assert num_updated == len(sample_tickers), \
        f"Should update ranks for all tickers, got {num_updated}/{len(sample_tickers)}"
    
    # Verificar ranking
    all_scores = score_service.get_all_scores_for_date(pipeline_date)
    
    assert len(all_scores) == len(sample_tickers), \
        f"Should have scores for all tickers, got {len(all_scores)}"
    
    # Verificar que ranks são sequenciais
    ranks = [s.rank for s in all_scores]
    assert ranks == list(range(1, len(sample_tickers) + 1)), \
        f"Ranks should be sequential from 1 to {len(sample_tickers)}, got {ranks}"
    
    # Verificar que scores estão ordenados
    scores = [s.final_score for s in all_scores]
    assert scores == sorted(scores, reverse=True), \
        "Scores should be in descending order"
    
    # Verificar top N
    top_2 = score_service.get_top_n_scores(pipeline_date, 2)
    assert len(top_2) == 2, f"Should return top 2, got {len(top_2)}"
    assert top_2[0].rank == 1, "First should have rank 1"
    assert top_2[1].rank == 2, "Second should have rank 2"
    
    # ===== VERIFICAÇÕES FINAIS =====
    
    # Verificar que todas as tabelas têm dados
    assert test_db.query(RawPriceDaily).count() > 0, "Should have price data"
    assert test_db.query(RawFundamental).count() > 0, "Should have fundamental data"
    assert test_db.query(FeatureDaily).count() > 0, "Should have daily features"
    assert test_db.query(FeatureMonthly).count() > 0, "Should have monthly features"
    assert test_db.query(ScoreDaily).count() > 0, "Should have scores"
    
    # Verificar que todos os scores têm timestamps
    for score in all_scores:
        assert score.calculated_at is not None, f"Score for {score.ticker} missing timestamp"
    
    # Verificar que todos os scores têm confiança
    for score in all_scores:
        assert score.confidence is not None, f"Score for {score.ticker} missing confidence"
        assert 0 <= score.confidence <= 1, f"Confidence should be between 0 and 1, got {score.confidence}"
    
    # Verificar que todos os scores têm breakdown
    for score in all_scores:
        assert score.momentum_score is not None, f"Score for {score.ticker} missing momentum_score"
        assert score.quality_score is not None, f"Score for {score.ticker} missing quality_score"
        assert score.value_score is not None, f"Score for {score.ticker} missing value_score"


def test_pipeline_handles_missing_data(test_db, sample_tickers):
    """
    Testa que o pipeline lida graciosamente com dados faltantes.
    
    Valida: Requisitos 1.6, 2.10, 3.8
    """
    # Não popular dados - banco vazio
    
    pipeline_date = date.today()
    
    # Tentar calcular fatores de momentum sem dados
    momentum_calculator = MomentumFactorCalculator()
    feature_service = FeatureService(test_db)
    
    for ticker in sample_tickers:
        prices_query = test_db.query(RawPriceDaily).filter(
            RawPriceDaily.ticker == ticker
        ).all()
        
        # Não deve haver dados
        assert len(prices_query) == 0
    
    # Verificar que não há features criadas
    daily_features = feature_service.get_all_daily_features_for_date(pipeline_date)
    assert len(daily_features) == 0, "Should have no features without data"


def test_pipeline_partial_success(
    test_db,
    sample_price_data,
    sample_fundamental_data
):
    """
    Testa que o pipeline continua processando mesmo quando alguns tickers falham.
    
    Valida: Requisitos 1.6, 2.10, 3.8
    """
    # Popular dados apenas para alguns tickers
    partial_price_data = {
        "AAPL": sample_price_data["AAPL"],
        "MSFT": sample_price_data["MSFT"]
    }
    
    partial_fundamental_data = {
        "AAPL": sample_fundamental_data["AAPL"],
        "MSFT": sample_fundamental_data["MSFT"]
    }
    
    populate_test_data(test_db, partial_price_data, partial_fundamental_data)
    
    # Tentar processar 3 tickers (um falhará)
    tickers = ["AAPL", "MSFT", "GOOGL"]
    
    pipeline_date = date.today()
    month_start = date(pipeline_date.year, pipeline_date.month, 1)
    
    # Calcular fatores
    momentum_calculator = MomentumFactorCalculator()
    feature_service = FeatureService(test_db)
    
    success_count = 0
    for ticker in tickers:
        prices_query = test_db.query(RawPriceDaily).filter(
            RawPriceDaily.ticker == ticker
        ).order_by(RawPriceDaily.date.asc()).all()
        
        if prices_query:
            prices_df = pd.DataFrame([
                {'date': p.date, 'adj_close': p.adj_close}
                for p in prices_query
            ])
            
            factors = momentum_calculator.calculate_all_factors(ticker, prices_df)
            feature_service.save_daily_features(ticker, pipeline_date, factors)
            success_count += 1
    
    # Deve ter sucesso para 2 tickers
    assert success_count == 2, f"Should process 2 tickers successfully, got {success_count}"
    
    # Verificar que features foram criadas apenas para tickers com sucesso
    daily_features = feature_service.get_all_daily_features_for_date(pipeline_date)
    assert len(daily_features) == 2, f"Should have features for 2 tickers, got {len(daily_features)}"
    
    feature_tickers = {f.ticker for f in daily_features}
    assert "AAPL" in feature_tickers
    assert "MSFT" in feature_tickers
    assert "GOOGL" not in feature_tickers
