"""
Testes de propriedade para endpoint /ranking da API.

Valida: Propriedade 10 (parcial) - Resposta Completa da API
Valida: Requisito 6.1
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
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


def create_test_scores(db: Session, test_date: date, num_assets: int):
    """
    Helper para criar scores de teste no banco.
    
    Args:
        db: Sessão do banco
        test_date: Data dos scores
        num_assets: Número de ativos a criar
    """
    # Limpar dados existentes
    db.query(ScoreDaily).filter(ScoreDaily.date == test_date).delete()
    db.commit()
    
    for i in range(num_assets):
        score = ScoreDaily(
            ticker=f"TEST{i}",
            date=test_date,
            final_score=float(num_assets - i),  # Scores decrescentes
            momentum_score=0.5,
            quality_score=0.3,
            value_score=0.2,
            confidence=0.5,
            rank=i + 1
        )
        db.add(score)
    db.commit()


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_assets=st.integers(min_value=1, max_value=50),
    days_ago=st.integers(min_value=0, max_value=30)
)
def test_ranking_endpoint_returns_complete_response(
    db_session: Session,
    num_assets: int,
    days_ago: int
):
    """
    Propriedade 10 (parcial): Resposta Completa da API de Ranking
    
    Para qualquer número de ativos e qualquer data válida,
    quando o endpoint /ranking é chamado, a resposta deve conter:
    - Campo 'date' com a data correta
    - Campo 'rankings' com lista de ativos
    - Campo 'total_assets' igual ao número de ativos
    - Cada ativo deve ter todos os campos obrigatórios
    
    Valida: Requisito 6.1
    """
    # Arrange: Criar scores de teste
    test_date = date.today() - timedelta(days=days_ago)
    create_test_scores(db_session, test_date, num_assets)
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/ranking?date={test_date}")
    
    # Assert: Verificar resposta completa
    assert response.status_code == 200
    
    data = response.json()
    
    # Verificar campos principais
    assert "date" in data
    assert "rankings" in data
    assert "total_assets" in data
    
    # Verificar valores
    assert data["date"] == str(test_date)
    assert data["total_assets"] == num_assets
    assert len(data["rankings"]) == num_assets
    
    # Verificar que cada ativo tem todos os campos obrigatórios do ScoreBreakdown
    for asset in data["rankings"]:
        assert "ticker" in asset
        assert "final_score" in asset
        assert "base_score" in asset
        assert "momentum_score" in asset
        assert "quality_score" in asset
        assert "value_score" in asset
        assert "confidence" in asset
        assert "passed_eligibility" in asset
        assert "exclusion_reasons" in asset
        assert "risk_penalties" in asset
        assert "penalty_factor" in asset
        
        # Verificar tipos
        assert isinstance(asset["ticker"], str)
        assert isinstance(asset["final_score"], (int, float))
        assert isinstance(asset["confidence"], (int, float))
        assert isinstance(asset["passed_eligibility"], bool)


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_assets=st.integers(min_value=2, max_value=50)
)
def test_ranking_endpoint_returns_ordered_by_score(
    db_session: Session,
    num_assets: int
):
    """
    Propriedade: Rankings são ordenados por score decrescente
    
    Para qualquer conjunto de ativos, o endpoint /ranking deve
    retornar os ativos ordenados por score final em ordem decrescente.
    
    Valida: Requisito 6.1
    """
    # Arrange: Criar scores de teste
    test_date = date.today()
    create_test_scores(db_session, test_date, num_assets)
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/ranking?date={test_date}")
    
    # Assert: Verificar ordenação
    assert response.status_code == 200
    
    data = response.json()
    rankings = data["rankings"]
    
    # Verificar que scores estão em ordem decrescente
    for i in range(len(rankings) - 1):
        assert rankings[i]["final_score"] >= rankings[i + 1]["final_score"]


def test_ranking_endpoint_returns_404_for_missing_date(db_session: Session):
    """
    Teste: Endpoint retorna 404 para data sem dados
    
    Quando não há dados para uma data específica,
    o endpoint deve retornar HTTP 404.
    
    Valida: Requisito 6.7
    """
    # Arrange: Data sem dados
    test_date = date(2020, 1, 1)
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/ranking?date={test_date}")
    
    # Assert: Verificar 404
    assert response.status_code == 404
    assert "detail" in response.json()


def test_ranking_endpoint_uses_latest_date_when_not_specified(db_session: Session):
    """
    Teste: Endpoint usa data mais recente quando não especificada
    
    Quando o parâmetro date não é fornecido,
    o endpoint deve usar a data mais recente disponível.
    
    Valida: Requisito 6.1
    """
    # Arrange: Criar scores em duas datas
    older_date = date.today() - timedelta(days=5)
    newer_date = date.today()
    
    create_test_scores(db_session, older_date, 5)
    create_test_scores(db_session, newer_date, 3)
    
    # Act: Chamar endpoint sem especificar data
    response = client.get("/api/v1/ranking")
    
    # Assert: Verificar que usa data mais recente
    assert response.status_code == 200
    
    data = response.json()
    assert data["date"] == str(newer_date)
    assert data["total_assets"] == 3
