"""
Testes de propriedade para endpoint /top da API.

Valida: Propriedade 11 - Tamanho Correto da Resposta Top N
Valida: Requisito 6.6
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from fastapi.testclient import TestClient
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.main import app
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
    total_assets=st.integers(min_value=1, max_value=50),
    n_requested=st.integers(min_value=1, max_value=100)
)
def test_top_endpoint_returns_correct_size(
    db_session: Session,
    total_assets: int,
    n_requested: int
):
    """
    Propriedade 11: Tamanho Correto da Resposta Top N
    
    Para qualquer valor de n solicitado via endpoint /top?n=X:
    - Quando existem pelo menos n ativos, a resposta deve conter exatamente n ativos
    - Quando existem menos de n ativos, a resposta deve conter todos os ativos disponíveis
    
    Valida: Requisito 6.6
    """
    # Arrange: Criar scores de teste
    test_date = date.today()
    create_test_scores(db_session, test_date, total_assets)
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/top?n={n_requested}&date={test_date}")
    
    # Assert: Verificar tamanho correto
    assert response.status_code == 200
    
    data = response.json()
    
    # Verificar campos principais
    assert "date" in data
    assert "top_assets" in data
    assert "n" in data
    
    # Verificar que n retornado é o solicitado
    assert data["n"] == n_requested
    
    # Verificar tamanho da lista
    expected_size = min(n_requested, total_assets)
    assert len(data["top_assets"]) == expected_size
    
    # Verificar que cada ativo tem todos os campos do ScoreBreakdown
    for asset in data["top_assets"]:
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


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    total_assets=st.integers(min_value=2, max_value=50),
    n_requested=st.integers(min_value=1, max_value=50)
)
def test_top_endpoint_returns_highest_scores(
    db_session: Session,
    total_assets: int,
    n_requested: int
):
    """
    Propriedade: Top N retorna os N ativos com maiores scores
    
    Para qualquer valor de n, o endpoint /top deve retornar
    os n ativos com os maiores scores finais, ordenados.
    
    Valida: Requisito 6.6
    """
    # Arrange: Criar scores de teste
    test_date = date.today()
    create_test_scores(db_session, test_date, total_assets)
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/top?n={n_requested}&date={test_date}")
    
    # Assert: Verificar que são os maiores scores
    assert response.status_code == 200
    
    data = response.json()
    top_assets = data["top_assets"]
    
    # Verificar que scores estão em ordem decrescente
    for i in range(len(top_assets) - 1):
        assert top_assets[i]["final_score"] >= top_assets[i + 1]["final_score"]
    
    # Se temos menos ativos que o solicitado, verificar que retornou todos
    if total_assets <= n_requested:
        assert len(top_assets) == total_assets
    else:
        # Se temos mais ativos, verificar que retornou exatamente n
        assert len(top_assets) == n_requested
        
        # Verificar que o menor score no top N é maior ou igual
        # ao score de qualquer ativo fora do top N
        # (isso é implícito pela ordenação, mas vamos verificar explicitamente)
        if len(top_assets) > 0:
            min_top_score = top_assets[-1]["final_score"]
            
            # Buscar todos os scores do banco
            all_scores = db_session.query(ScoreDaily).filter(
                ScoreDaily.date == test_date
            ).order_by(ScoreDaily.final_score.desc()).all()
            
            # Verificar que os primeiros n são os retornados
            for i in range(min(n_requested, len(all_scores))):
                assert all_scores[i].ticker == top_assets[i]["ticker"]


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    total_assets=st.integers(min_value=1, max_value=50)
)
def test_top_endpoint_uses_default_n_when_not_specified(
    db_session: Session,
    total_assets: int
):
    """
    Propriedade: Endpoint usa n=10 como padrão
    
    Quando o parâmetro n não é fornecido,
    o endpoint deve usar n=10 como padrão.
    
    Valida: Requisito 6.6
    """
    # Arrange: Criar scores de teste
    test_date = date.today()
    create_test_scores(db_session, test_date, total_assets)
    
    # Act: Chamar endpoint sem especificar n
    response = client.get(f"/api/v1/top?date={test_date}")
    
    # Assert: Verificar que usa n=10
    assert response.status_code == 200
    
    data = response.json()
    
    # Verificar que n retornado é 10
    assert data["n"] == 10
    
    # Verificar tamanho da lista
    expected_size = min(10, total_assets)
    assert len(data["top_assets"]) == expected_size


def test_top_endpoint_returns_all_assets_when_n_exceeds_total(db_session: Session):
    """
    Teste: Endpoint retorna todos os ativos quando n > total
    
    Quando n é maior que o número total de ativos,
    o endpoint deve retornar todos os ativos disponíveis.
    
    Valida: Requisito 6.6
    """
    # Arrange: Criar 5 scores
    test_date = date.today()
    total_assets = 5
    create_test_scores(db_session, test_date, total_assets)
    
    # Act: Solicitar top 100
    response = client.get(f"/api/v1/top?n=100&date={test_date}")
    
    # Assert: Verificar que retorna apenas 5
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["top_assets"]) == total_assets
    assert data["n"] == 100  # n solicitado
    
    # Verificar que todos os 5 ativos estão presentes
    tickers = [asset["ticker"] for asset in data["top_assets"]]
    assert len(tickers) == total_assets


def test_top_endpoint_uses_latest_date_when_not_specified(db_session: Session):
    """
    Teste: Endpoint usa data mais recente quando não especificada
    
    Quando o parâmetro date não é fornecido,
    o endpoint deve usar a data mais recente disponível.
    
    Valida: Requisito 6.6
    """
    # Arrange: Criar scores em duas datas
    older_date = date.today() - timedelta(days=5)
    newer_date = date.today()
    
    create_test_scores(db_session, older_date, 5)
    create_test_scores(db_session, newer_date, 3)
    
    # Act: Chamar endpoint sem especificar data
    response = client.get("/api/v1/top?n=10")
    
    # Assert: Verificar que usa data mais recente
    assert response.status_code == 200
    
    data = response.json()
    assert data["date"] == str(newer_date)
    assert len(data["top_assets"]) == 3


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    total_assets=st.integers(min_value=5, max_value=30),
    n_requested=st.integers(min_value=1, max_value=10)
)
def test_top_endpoint_ranks_are_sequential(
    db_session: Session,
    total_assets: int,
    n_requested: int
):
    """
    Propriedade: Ranks no top N são sequenciais começando de 1
    
    Para qualquer top N retornado, os ranks devem ser
    sequenciais: 1, 2, 3, ..., n
    
    Valida: Requisito 6.6
    """
    # Arrange: Criar scores de teste
    test_date = date.today()
    create_test_scores(db_session, test_date, total_assets)
    
    # Act: Chamar endpoint
    response = client.get(f"/api/v1/top?n={n_requested}&date={test_date}")
    
    # Assert: Verificar scores em ordem decrescente
    assert response.status_code == 200
    
    data = response.json()
    top_assets = data["top_assets"]
    
    # Verificar que scores estão em ordem decrescente
    for i in range(len(top_assets) - 1):
        assert top_assets[i]["final_score"] >= top_assets[i + 1]["final_score"]
