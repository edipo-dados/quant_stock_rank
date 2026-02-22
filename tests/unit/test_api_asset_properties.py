"""
Testes de propriedade para endpoint /asset/{ticker} da API.

Valida: Propriedade 10 - Resposta Completa da API de Detalhes de Ativo
Valida: Requisitos 6.2, 6.3, 6.4, 6.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from fastapi.testclient import TestClient
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.main import app
from app.main import app as fastapi_app
from app.models.database import SessionLocal, engine, Base
from app.models.schemas import ScoreDaily, FeatureDaily, FeatureMonthly, RawPriceDaily, RawFundamental
from app.api.dependencies import get_db

# Import all models to register them with Base before creating tables
import app.models.schemas  # noqa: F401


# Override database dependency for testing
def override_get_db():
    """Override para usar banco de testes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


fastapi_app.dependency_overrides[get_db] = override_get_db

client = TestClient(fastapi_app)


@pytest.fixture(scope="function")
def db_session():
    """Fixture para criar sessão de banco de dados para testes."""
    # Criar tabelas
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Limpar tabelas após teste
        Base.metadata.drop_all(bind=engine)


def create_test_asset_data(
    db: Session,
    ticker: str,
    test_date: date,
    final_score: float,
    rank: int
):
    """
    Helper para criar dados completos de um ativo no banco.
    
    Args:
        db: Sessão do banco
        ticker: Símbolo do ativo
        test_date: Data dos dados
        final_score: Score final
        rank: Posição no ranking
    """
    # Limpar dados existentes para este ticker e data
    db.query(ScoreDaily).filter(ScoreDaily.ticker == ticker, ScoreDaily.date == test_date).delete()
    db.query(FeatureDaily).filter(FeatureDaily.ticker == ticker, FeatureDaily.date == test_date).delete()
    
    month_start = test_date.replace(day=1)
    db.query(FeatureMonthly).filter(FeatureMonthly.ticker == ticker, FeatureMonthly.month == month_start).delete()
    
    # Criar score
    score = ScoreDaily(
        ticker=ticker,
        date=test_date,
        final_score=final_score,
        momentum_score=0.5,
        quality_score=0.3,
        value_score=0.2,
        confidence=0.5,
        rank=rank
    )
    db.add(score)
    
    # Criar features diárias
    feature_daily = FeatureDaily(
        ticker=ticker,
        date=test_date,
        return_6m=1.0,
        return_12m=1.5,
        rsi_14=0.8,
        volatility_90d=-0.5,
        recent_drawdown=-0.3
    )
    db.add(feature_daily)
    
    # Criar features mensais
    feature_monthly = FeatureMonthly(
        ticker=ticker,
        month=month_start,
        roe=0.9,
        net_margin=0.7,
        revenue_growth_3y=0.6,
        debt_to_ebitda=-0.4,
        pe_ratio=-0.2,
        ev_ebitda=-0.3,
        pb_ratio=-0.1
    )
    db.add(feature_monthly)
    
    db.commit()


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    ticker_suffix=st.integers(min_value=1, max_value=999),
    final_score=st.floats(min_value=-3.0, max_value=3.0, allow_nan=False, allow_infinity=False),
    rank=st.integers(min_value=1, max_value=100),
    days_ago=st.integers(min_value=0, max_value=30)
)
def test_asset_detail_endpoint_returns_complete_response(
    db_session: Session,
    ticker_suffix: int,
    final_score: float,
    rank: int,
    days_ago: int
):
    """
    Propriedade 10: Resposta Completa da API de Detalhes de Ativo
    
    Para qualquer ticker válido solicitado via endpoint /asset/{ticker},
    a resposta deve conter todos os campos obrigatórios:
    - ticker
    - score (com todos os subcampos)
    - explanation (texto não vazio)
    - raw_factors (dicionário)
    
    Valida: Requisitos 6.2, 6.3, 6.4, 6.5
    """
    # Arrange: Criar dados de teste
    ticker = f"TEST{ticker_suffix}"
    test_date = date.today() - timedelta(days=days_ago)
    
    create_test_asset_data(db_session, ticker, test_date, final_score, rank)
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/asset/{ticker}?date={test_date}")
    
    # Assert: Verificar resposta completa
    assert response.status_code == 200
    
    data = response.json()
    
    # Verificar campos principais
    assert "ticker" in data
    assert "score" in data
    assert "explanation" in data
    assert "raw_factors" in data
    
    # Verificar ticker
    assert data["ticker"] == ticker
    
    # Verificar score completo (ScoreBreakdown)
    score = data["score"]
    assert "ticker" in score
    assert "final_score" in score
    assert "base_score" in score
    assert "momentum_score" in score
    assert "quality_score" in score
    assert "value_score" in score
    assert "confidence" in score
    assert "passed_eligibility" in score
    assert "exclusion_reasons" in score
    assert "risk_penalties" in score
    assert "penalty_factor" in score
    
    # Verificar explanation não vazio
    assert isinstance(data["explanation"], str)
    assert len(data["explanation"]) > 0
    
    # Verificar raw_factors é dicionário
    assert isinstance(data["raw_factors"], dict)
    
    # Verificar tipos
    assert isinstance(score["final_score"], (int, float))
    assert isinstance(score["confidence"], (int, float))
    assert isinstance(score["passed_eligibility"], bool)


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    ticker_suffix=st.integers(min_value=1, max_value=999)
)
def test_asset_detail_explanation_contains_required_elements(
    db_session: Session,
    ticker_suffix: int
):
    """
    Propriedade: Explicação contém elementos obrigatórios
    
    Para qualquer ativo, a explicação gerada deve conter:
    - Menção ao score final
    - Menção à posição no ranking
    - Seção de pontos fortes
    - Seção de pontos de atenção
    
    Valida: Requisitos 7.1, 7.2, 7.3, 7.4
    """
    # Arrange: Criar dados de teste
    ticker = f"TEST{ticker_suffix}"
    test_date = date.today()
    
    create_test_asset_data(db_session, ticker, test_date, 1.5, 3)
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/asset/{ticker}?date={test_date}")
    
    # Assert: Verificar elementos da explicação
    assert response.status_code == 200
    
    data = response.json()
    explanation = data["explanation"]
    
    # Verificar menção ao score
    assert "score" in explanation.lower()
    
    # Verificar menção à posição
    assert "posição" in explanation.lower() or "ranking" in explanation.lower()
    
    # Verificar seções
    assert "pontos fortes" in explanation.lower() or "fortes" in explanation.lower()
    assert "pontos de atenção" in explanation.lower() or "atenção" in explanation.lower()


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    ticker_suffix=st.integers(min_value=1, max_value=999)
)
def test_asset_detail_raw_factors_are_numeric(
    db_session: Session,
    ticker_suffix: int
):
    """
    Propriedade: Fatores brutos são numéricos
    
    Para qualquer ativo, todos os valores em raw_factors
    devem ser numéricos (int ou float).
    
    Valida: Requisito 6.4
    """
    # Arrange: Criar dados de teste
    ticker = f"TEST{ticker_suffix}"
    test_date = date.today()
    
    create_test_asset_data(db_session, ticker, test_date, 1.0, 1)
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/asset/{ticker}?date={test_date}")
    
    # Assert: Verificar tipos dos fatores
    assert response.status_code == 200
    
    data = response.json()
    raw_factors = data["raw_factors"]
    
    # Verificar que todos os valores são numéricos
    for factor_name, factor_value in raw_factors.items():
        assert isinstance(factor_value, (int, float)), \
            f"Factor {factor_name} has non-numeric value: {factor_value}"


def test_asset_detail_endpoint_returns_404_for_invalid_ticker(db_session: Session):
    """
    Teste: Endpoint retorna 404 para ticker inválido
    
    Quando um ticker não existe no banco,
    o endpoint deve retornar HTTP 404.
    
    Valida: Requisito 6.7
    """
    # Arrange: Ticker que não existe
    invalid_ticker = "INVALID"
    test_date = date.today()
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/asset/{invalid_ticker}?date={test_date}")
    
    # Assert: Verificar 404
    assert response.status_code == 404
    assert "detail" in response.json()


def test_asset_detail_endpoint_uses_latest_date_when_not_specified(db_session: Session):
    """
    Teste: Endpoint usa data mais recente quando não especificada
    
    Quando o parâmetro date não é fornecido,
    o endpoint deve usar a data mais recente disponível.
    
    Valida: Requisito 6.2
    """
    # Arrange: Criar dados em duas datas
    ticker = "TEST1"
    older_date = date.today() - timedelta(days=5)
    newer_date = date.today()
    
    create_test_asset_data(db_session, ticker, older_date, 1.0, 1)
    create_test_asset_data(db_session, ticker, newer_date, 2.0, 1)
    
    # Act: Chamar endpoint sem especificar data
    response = client.get(f"/api/v1/asset/{ticker}")
    
    # Assert: Verificar que usa data mais recente (verificando pelo score que é diferente)
    assert response.status_code == 200
    
    data = response.json()
    # A data mais recente tem score 2.0, então se retornar 2.0, está usando a data mais recente
    assert data["score"]["final_score"] == 2.0
