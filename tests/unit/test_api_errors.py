"""
Testes unitários para tratamento de erros da API.

Valida: Requisito 6.7
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.main import app as fastapi_app
from app.models.database import SessionLocal, engine, Base
from app.models.schemas import ScoreDaily, RawPriceDaily, RawFundamental, FeatureDaily, FeatureMonthly
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


def test_asset_endpoint_returns_404_for_nonexistent_ticker(db_session: Session):
    """
    Teste: Endpoint /asset/{ticker} retorna 404 para ticker inexistente
    
    Quando um ticker não existe no banco de dados,
    o endpoint deve retornar HTTP 404 com mensagem de erro.
    
    Valida: Requisito 6.7
    """
    # Arrange: Ticker que não existe
    nonexistent_ticker = "NONEXIST"
    test_date = date.today()
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/asset/{nonexistent_ticker}?date={test_date}")
    
    # Assert: Verificar 404
    assert response.status_code == 404
    
    # Verificar que resposta contém detail
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)
    assert len(data["detail"]) > 0
    
    # Verificar que mensagem menciona o ticker
    assert nonexistent_ticker.upper() in data["detail"] or "não encontrado" in data["detail"].lower()


def test_ranking_endpoint_returns_404_for_date_without_data(db_session: Session):
    """
    Teste: Endpoint /ranking retorna 404 para data sem dados
    
    Quando não há scores para uma data específica,
    o endpoint deve retornar HTTP 404 com mensagem de erro.
    
    Valida: Requisito 6.7
    """
    # Arrange: Data sem dados (muito antiga)
    date_without_data = date(2000, 1, 1)
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/ranking?date={date_without_data}")
    
    # Assert: Verificar 404
    assert response.status_code == 404
    
    # Verificar que resposta contém detail
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)
    assert len(data["detail"]) > 0


def test_top_endpoint_returns_404_for_date_without_data(db_session: Session):
    """
    Teste: Endpoint /top retorna 404 para data sem dados
    
    Quando não há scores para uma data específica,
    o endpoint deve retornar HTTP 404 com mensagem de erro.
    
    Valida: Requisito 6.7
    """
    # Arrange: Data sem dados
    date_without_data = date(2000, 1, 1)
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/top?n=10&date={date_without_data}")
    
    # Assert: Verificar 404
    assert response.status_code == 404
    
    # Verificar que resposta contém detail
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)


def test_ranking_endpoint_returns_404_when_database_empty(db_session: Session):
    """
    Teste: Endpoint /ranking retorna 404 quando banco está vazio
    
    Quando não há nenhum score no banco e nenhuma data é especificada,
    o endpoint deve retornar HTTP 404.
    
    Valida: Requisito 6.7
    """
    # Arrange: Banco vazio (nenhum score)
    
    # Act: Chamar endpoint sem especificar data
    response = client.get("/api/v1/ranking")
    
    # Assert: Verificar 404
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data


def test_asset_endpoint_returns_404_when_ticker_exists_but_not_for_date(db_session: Session):
    """
    Teste: Endpoint /asset/{ticker} retorna 404 quando ticker existe mas não para a data
    
    Quando um ticker existe no banco mas não tem dados para a data especificada,
    o endpoint deve retornar HTTP 404.
    
    Valida: Requisito 6.7
    """
    # Arrange: Criar score para uma data
    ticker = "TEST1"
    existing_date = date.today()
    different_date = date.today() - timedelta(days=10)
    
    score = ScoreDaily(
        ticker=ticker,
        date=existing_date,
        final_score=1.0,
        momentum_score=0.5,
        quality_score=0.3,
        value_score=0.2,
        confidence=0.5,
        rank=1
    )
    db_session.add(score)
    db_session.commit()
    
    # Act: Chamar endpoint com data diferente
    response = client.get(f"/api/v1/asset/{ticker}?date={different_date}")
    
    # Assert: Verificar 404
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data


def test_api_returns_json_error_format(db_session: Session):
    """
    Teste: Erros da API retornam formato JSON consistente
    
    Todos os erros devem retornar JSON com campo 'detail'.
    
    Valida: Requisitos 6.7, 6.8
    """
    # Arrange & Act: Gerar erro 404
    response = client.get("/api/v1/asset/INVALID")
    
    # Assert: Verificar formato JSON
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/json"
    
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)


def test_top_endpoint_validates_n_parameter(db_session: Session):
    """
    Teste: Endpoint /top valida parâmetro n
    
    Quando n é inválido (negativo ou zero), deve retornar erro de validação.
    
    Valida: Requisito 6.7
    """
    # Arrange: Criar alguns scores
    test_date = date.today()
    score = ScoreDaily(
        ticker="TEST1",
        date=test_date,
        final_score=1.0,
        momentum_score=0.5,
        quality_score=0.3,
        value_score=0.2,
        confidence=0.5,
        rank=1
    )
    db_session.add(score)
    db_session.commit()
    
    # Act: Chamar endpoint com n inválido
    response = client.get(f"/api/v1/top?n=0&date={test_date}")
    
    # Assert: Verificar erro de validação (422)
    assert response.status_code == 422
    
    data = response.json()
    assert "detail" in data
