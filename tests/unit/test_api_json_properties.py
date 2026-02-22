"""
Testes de propriedade para formato JSON das respostas da API.

Valida: Propriedade 12 - Formato JSON das Respostas API
Valida: Requisito 6.8
"""

import pytest
import json
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from datetime import date, timedelta
from sqlalchemy.orm import Session

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


def create_test_scores(db: Session, test_date: date, num_assets: int):
    """Helper para criar scores de teste no banco."""
    # Limpar dados existentes
    db.query(ScoreDaily).filter(ScoreDaily.date == test_date).delete()
    db.commit()
    
    for i in range(num_assets):
        score = ScoreDaily(
            ticker=f"TEST{i}",
            date=test_date,
            final_score=float(num_assets - i),
            momentum_score=0.5,
            quality_score=0.3,
            value_score=0.2,
            confidence=0.5,
            rank=i + 1
        )
        db.add(score)
    db.commit()


def create_test_asset_data(
    db: Session,
    ticker: str,
    test_date: date,
    final_score: float,
    rank: int
):
    """Helper para criar dados completos de um ativo."""
    # Limpar dados existentes
    db.query(ScoreDaily).filter(ScoreDaily.ticker == ticker, ScoreDaily.date == test_date).delete()
    db.commit()
    
    # Score
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
    
    # Features diárias
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
    
    # Features mensais
    month_start = test_date.replace(day=1)
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
    num_assets=st.integers(min_value=1, max_value=30)
)
def test_ranking_endpoint_returns_valid_json(
    db_session: Session,
    num_assets: int
):
    """
    Propriedade 12: Formato JSON das Respostas API - Endpoint /ranking
    
    Para qualquer resposta bem-sucedida do endpoint /ranking:
    - Content-Type deve ser application/json
    - Corpo da resposta deve ser JSON válido e parseável
    
    Valida: Requisito 6.8
    """
    # Arrange: Criar scores de teste
    test_date = date.today()
    create_test_scores(db_session, test_date, num_assets)
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/ranking?date={test_date}")
    
    # Assert: Verificar formato JSON
    assert response.status_code == 200
    
    # Verificar Content-Type
    assert "application/json" in response.headers["content-type"]
    
    # Verificar que resposta é JSON parseável
    try:
        data = response.json()
        assert isinstance(data, dict)
    except json.JSONDecodeError:
        pytest.fail("Response is not valid JSON")
    
    # Verificar que pode ser serializado novamente
    try:
        json.dumps(data)
    except (TypeError, ValueError):
        pytest.fail("Response data cannot be serialized to JSON")


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    ticker_suffix=st.integers(min_value=1, max_value=999)
)
def test_asset_endpoint_returns_valid_json(
    db_session: Session,
    ticker_suffix: int
):
    """
    Propriedade 12: Formato JSON das Respostas API - Endpoint /asset/{ticker}
    
    Para qualquer resposta bem-sucedida do endpoint /asset/{ticker}:
    - Content-Type deve ser application/json
    - Corpo da resposta deve ser JSON válido e parseável
    
    Valida: Requisito 6.8
    """
    # Arrange: Criar dados de teste
    ticker = f"TEST{ticker_suffix}"
    test_date = date.today()
    create_test_asset_data(db_session, ticker, test_date, 1.5, 1)
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/asset/{ticker}?date={test_date}")
    
    # Assert: Verificar formato JSON
    assert response.status_code == 200
    
    # Verificar Content-Type
    assert "application/json" in response.headers["content-type"]
    
    # Verificar que resposta é JSON parseável
    try:
        data = response.json()
        assert isinstance(data, dict)
    except json.JSONDecodeError:
        pytest.fail("Response is not valid JSON")
    
    # Verificar que pode ser serializado novamente
    try:
        json.dumps(data)
    except (TypeError, ValueError):
        pytest.fail("Response data cannot be serialized to JSON")


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_assets=st.integers(min_value=1, max_value=30),
    n_requested=st.integers(min_value=1, max_value=20)
)
def test_top_endpoint_returns_valid_json(
    db_session: Session,
    num_assets: int,
    n_requested: int
):
    """
    Propriedade 12: Formato JSON das Respostas API - Endpoint /top
    
    Para qualquer resposta bem-sucedida do endpoint /top:
    - Content-Type deve ser application/json
    - Corpo da resposta deve ser JSON válido e parseável
    
    Valida: Requisito 6.8
    """
    # Arrange: Criar scores de teste
    test_date = date.today()
    create_test_scores(db_session, test_date, num_assets)
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/top?n={n_requested}&date={test_date}")
    
    # Assert: Verificar formato JSON
    assert response.status_code == 200
    
    # Verificar Content-Type
    assert "application/json" in response.headers["content-type"]
    
    # Verificar que resposta é JSON parseável
    try:
        data = response.json()
        assert isinstance(data, dict)
    except json.JSONDecodeError:
        pytest.fail("Response is not valid JSON")
    
    # Verificar que pode ser serializado novamente
    try:
        json.dumps(data)
    except (TypeError, ValueError):
        pytest.fail("Response data cannot be serialized to JSON")


def test_error_responses_return_valid_json(db_session: Session):
    """
    Propriedade 12: Formato JSON das Respostas de Erro
    
    Para qualquer resposta de erro (404, 422, 500):
    - Content-Type deve ser application/json
    - Corpo da resposta deve ser JSON válido e parseável
    - Deve conter campo 'detail'
    
    Valida: Requisitos 6.7, 6.8
    """
    # Test 404 error
    response_404 = client.get("/api/v1/asset/INVALID")
    
    assert response_404.status_code == 404
    assert "application/json" in response_404.headers["content-type"]
    
    try:
        data_404 = response_404.json()
        assert isinstance(data_404, dict)
        assert "detail" in data_404
    except json.JSONDecodeError:
        pytest.fail("404 response is not valid JSON")
    
    # Test 422 validation error
    test_date = date.today()
    create_test_scores(db_session, test_date, 5)
    
    response_422 = client.get(f"/api/v1/top?n=0&date={test_date}")
    
    assert response_422.status_code == 422
    assert "application/json" in response_422.headers["content-type"]
    
    try:
        data_422 = response_422.json()
        assert isinstance(data_422, dict)
        assert "detail" in data_422
    except json.JSONDecodeError:
        pytest.fail("422 response is not valid JSON")


def test_health_endpoint_returns_valid_json():
    """
    Teste: Endpoint /health retorna JSON válido
    
    O endpoint de health check deve retornar JSON válido.
    
    Valida: Requisito 6.8
    """
    # Act: Chamar endpoint
    response = client.get("/health")
    
    # Assert: Verificar formato JSON
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    
    try:
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
    except json.JSONDecodeError:
        pytest.fail("Health response is not valid JSON")


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_assets=st.integers(min_value=1, max_value=20)
)
def test_all_numeric_values_are_json_serializable(
    db_session: Session,
    num_assets: int
):
    """
    Propriedade: Todos os valores numéricos são serializáveis em JSON
    
    Para qualquer resposta da API, todos os valores numéricos
    (scores, confidence, etc) devem ser serializáveis em JSON
    (não podem ser NaN ou Infinity).
    
    Valida: Requisito 6.8
    """
    # Arrange: Criar scores de teste
    test_date = date.today()
    create_test_scores(db_session, test_date, num_assets)
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/ranking?date={test_date}")
    
    # Assert: Verificar que todos os valores são serializáveis
    assert response.status_code == 200
    
    data = response.json()
    
    # Tentar serializar novamente (falharia com NaN ou Infinity)
    try:
        json_str = json.dumps(data)
        # Tentar parsear de volta
        parsed = json.loads(json_str)
        assert parsed == data
    except (TypeError, ValueError) as e:
        pytest.fail(f"Response contains non-JSON-serializable values: {e}")
