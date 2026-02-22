"""Testes de propriedade para módulo de ingestão."""

import logging
from datetime import date, timedelta
from decimal import Decimal

import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.database import Base
from app.models.schemas import RawPriceDaily

# Configurar logging para testes
logging.basicConfig(level=logging.WARNING)

# Estratégias customizadas para geração de dados
ticker_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
    min_size=3,
    max_size=10
)

date_strategy = st.dates(
    min_value=date(2020, 1, 1),
    max_value=date(2024, 12, 31)
)

price_strategy = st.floats(
    min_value=0.01,
    max_value=10000.0,
    allow_nan=False,
    allow_infinity=False
)

volume_strategy = st.integers(min_value=0, max_value=int(1e9))


def get_test_db():
    """Cria banco de dados em memória para testes."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


# Feature: quant-stock-ranker, Property 1: Round-trip de Persistência de Dados Brutos
@given(
    ticker=ticker_strategy,
    test_date=date_strategy,
    open_price=price_strategy,
    high_price=price_strategy,
    low_price=price_strategy,
    close_price=price_strategy,
    volume=volume_strategy
)
@settings(max_examples=20, deadline=None)
def test_price_data_roundtrip_property(
    ticker,
    test_date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume
):
    """
    Propriedade 1: Round-trip de Persistência de Dados Brutos
    
    Para quaisquer dados de preço, salvar e recuperar deve retornar dados idênticos.
    
    Valida: Requisitos 1.3, 1.4, 1.5
    """
    # Cria banco de dados para este teste
    test_db = get_test_db()
    
    try:
        # Garante que high >= low e que close está entre low e high
        if high_price < low_price:
            high_price, low_price = low_price, high_price
        
        close_price = max(low_price, min(high_price, close_price))
        open_price = max(low_price, min(high_price, open_price))
        
        # Calcula adj_close (para simplificar, usamos o mesmo valor de close)
        adj_close = close_price
        
        # Cria registro original
        original_record = RawPriceDaily(
            ticker=ticker,
            date=test_date,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=volume,
            adj_close=adj_close
        )
        
        # Salva no banco
        test_db.add(original_record)
        test_db.commit()
        
        # Recupera do banco
        retrieved_record = test_db.query(RawPriceDaily).filter_by(
            ticker=ticker,
            date=test_date
        ).first()
        
        # Verifica que o registro foi recuperado
        assert retrieved_record is not None, "Record should be retrieved from database"
        
        # Verifica que todos os campos são idênticos
        assert retrieved_record.ticker == ticker
        assert retrieved_record.date == test_date
        
        # Para floats, usamos comparação com tolerância
        assert abs(retrieved_record.open - open_price) < 1e-6
        assert abs(retrieved_record.high - high_price) < 1e-6
        assert abs(retrieved_record.low - low_price) < 1e-6
        assert abs(retrieved_record.close - close_price) < 1e-6
        assert abs(retrieved_record.adj_close - adj_close) < 1e-6
        
        # Volume deve ser exato
        assert retrieved_record.volume == volume
        
        # Timestamp deve existir
        assert retrieved_record.created_at is not None
    finally:
        test_db.close()


def test_price_data_roundtrip_with_real_data():
    """
    Teste unitário complementar com dados reais conhecidos.
    
    Valida: Requisitos 1.3, 1.4, 1.5
    """
    test_db = get_test_db()
    
    try:
        # Dados de exemplo realistas
        original_record = RawPriceDaily(
            ticker="PETR4.SA",
            date=date(2024, 1, 15),
            open=35.50,
            high=36.20,
            low=35.10,
            close=35.80,
            volume=15000000,
            adj_close=35.80
        )
        
        # Salva
        test_db.add(original_record)
        test_db.commit()
        
        # Recupera
        retrieved = test_db.query(RawPriceDaily).filter_by(
            ticker="PETR4.SA",
            date=date(2024, 1, 15)
        ).first()
        
        # Verifica
        assert retrieved is not None
        assert retrieved.ticker == "PETR4.SA"
        assert retrieved.date == date(2024, 1, 15)
        assert retrieved.open == 35.50
        assert retrieved.high == 36.20
        assert retrieved.low == 35.10
        assert retrieved.close == 35.80
        assert retrieved.volume == 15000000
        assert retrieved.adj_close == 35.80
        assert retrieved.created_at is not None
    finally:
        test_db.close()


def test_price_data_uniqueness_constraint():
    """
    Testa que não é possível inserir dados duplicados para mesmo ticker/data.
    
    Valida: Requisitos 1.3, 1.5
    """
    test_db = get_test_db()
    
    try:
        # Primeiro registro
        record1 = RawPriceDaily(
            ticker="VALE3.SA",
            date=date(2024, 1, 15),
            open=70.00,
            high=71.00,
            low=69.50,
            close=70.50,
            volume=10000000,
            adj_close=70.50
        )
        
        test_db.add(record1)
        test_db.commit()
        
        # Tenta inserir registro duplicado
        record2 = RawPriceDaily(
            ticker="VALE3.SA",
            date=date(2024, 1, 15),
            open=70.10,
            high=71.10,
            low=69.60,
            close=70.60,
            volume=10000001,
            adj_close=70.60
        )
        
        test_db.add(record2)
        
        # Deve falhar devido à constraint de unicidade
        with pytest.raises(Exception):  # IntegrityError ou similar
            test_db.commit()
    finally:
        test_db.close()


# Feature: quant-stock-ranker, Property 4: Resiliência a Erros de Ingestão
@given(
    valid_ticker=ticker_strategy,
    invalid_ticker=st.just("INVALID_TICKER_XYZ_123"),
    test_date=date_strategy,
    price=price_strategy,
    volume=volume_strategy
)
@settings(max_examples=20, deadline=None)
def test_ingestion_error_resilience_property(
    valid_ticker,
    invalid_ticker,
    test_date,
    price,
    volume
):
    """
    Propriedade 4: Resiliência a Erros de Ingestão
    
    Para qualquer batch de tickers contendo pelo menos um ticker inválido e um ticker válido,
    quando o sistema processa o batch, o ticker válido deve ser processado com sucesso
    independentemente da falha do ticker inválido.
    
    Valida: Requisitos 1.6, 2.10, 3.8
    """
    from unittest.mock import Mock, MagicMock
    from app.ingestion.ingestion_service import IngestionService
    from app.core.exceptions import DataFetchError
    
    # Cria banco de dados para este teste
    test_db = get_test_db()
    
    try:
        # Cria mocks dos clientes
        yahoo_client = Mock()
        fmp_client = Mock()
        
        # Configura mock para retornar dados válidos para ticker válido
        valid_df = pd.DataFrame({
            'date': [test_date],
            'open': [price],
            'high': [price * 1.05],
            'low': [price * 0.95],
            'close': [price],
            'volume': [volume],
            'adj_close': [price]
        })
        
        # Mock retorna dados para ticker válido e lança exceção para ticker inválido
        def mock_fetch_prices(ticker, start_date, end_date):
            if ticker == invalid_ticker:
                raise DataFetchError(f"Ticker {ticker} not found")
            return valid_df
        
        yahoo_client.fetch_daily_prices = mock_fetch_prices
        
        # Cria serviço de ingestão
        service = IngestionService(yahoo_client, fmp_client, test_db)
        
        # Processa batch com ticker válido e inválido
        tickers = [invalid_ticker, valid_ticker]  # Inválido primeiro
        results = service.ingest_prices(tickers, lookback_days=1)
        
        # Verifica que o ticker válido foi processado com sucesso
        assert valid_ticker in results["success"], \
            f"Valid ticker {valid_ticker} should be in success list"
        
        # Verifica que o ticker inválido falhou
        failed_tickers = [f["ticker"] for f in results["failed"]]
        assert invalid_ticker in failed_tickers, \
            f"Invalid ticker {invalid_ticker} should be in failed list"
        
        # Verifica que pelo menos um registro foi inserido (do ticker válido)
        assert results["total_records"] >= 1, \
            "At least one record should be inserted for valid ticker"
        
        # Verifica que o registro do ticker válido está no banco
        record = test_db.query(RawPriceDaily).filter_by(
            ticker=valid_ticker,
            date=test_date
        ).first()
        
        assert record is not None, \
            f"Record for valid ticker {valid_ticker} should exist in database"
        
    finally:
        test_db.close()


def test_ingestion_error_resilience_with_real_scenario():
    """
    Teste unitário complementar com cenário realista de erro.
    
    Valida: Requisitos 1.6, 2.10, 3.8
    """
    from unittest.mock import Mock
    from app.ingestion.ingestion_service import IngestionService
    from app.core.exceptions import DataFetchError
    
    test_db = get_test_db()
    
    try:
        # Cria mocks
        yahoo_client = Mock()
        fmp_client = Mock()
        
        # Dados válidos para PETR4.SA
        valid_df = pd.DataFrame({
            'date': [date(2024, 1, 15)],
            'open': [35.50],
            'high': [36.20],
            'low': [35.10],
            'close': [35.80],
            'volume': [15000000],
            'adj_close': [35.80]
        })
        
        # Mock que simula erro para ticker inválido
        def mock_fetch(ticker, start_date, end_date):
            if ticker == "INVALID":
                raise DataFetchError("Ticker not found")
            return valid_df
        
        yahoo_client.fetch_daily_prices = mock_fetch
        
        # Cria serviço
        service = IngestionService(yahoo_client, fmp_client, test_db)
        
        # Processa batch misto
        results = service.ingest_prices(["INVALID", "PETR4.SA"], lookback_days=1)
        
        # Verifica resultados
        assert "PETR4.SA" in results["success"]
        assert len(results["failed"]) == 1
        assert results["failed"][0]["ticker"] == "INVALID"
        assert results["total_records"] == 1
        
        # Verifica que dados válidos foram salvos
        record = test_db.query(RawPriceDaily).filter_by(
            ticker="PETR4.SA",
            date=date(2024, 1, 15)
        ).first()
        
        assert record is not None
        assert record.close == 35.80
        
    finally:
        test_db.close()


def test_ingestion_continues_after_multiple_failures():
    """
    Testa que o sistema continua processando após múltiplas falhas.
    
    Valida: Requisitos 1.6, 1.7
    """
    from unittest.mock import Mock
    from app.ingestion.ingestion_service import IngestionService
    from app.core.exceptions import DataFetchError
    
    test_db = get_test_db()
    
    try:
        yahoo_client = Mock()
        fmp_client = Mock()
        
        # Dados válidos
        valid_df = pd.DataFrame({
            'date': [date(2024, 1, 15)],
            'open': [100.0],
            'high': [105.0],
            'low': [95.0],
            'close': [100.0],
            'volume': [1000000],
            'adj_close': [100.0]
        })
        
        # Mock que falha para alguns tickers
        def mock_fetch(ticker, start_date, end_date):
            if ticker in ["FAIL1", "FAIL2", "FAIL3"]:
                raise DataFetchError(f"Failed to fetch {ticker}")
            return valid_df
        
        yahoo_client.fetch_daily_prices = mock_fetch
        
        service = IngestionService(yahoo_client, fmp_client, test_db)
        
        # Batch com múltiplas falhas intercaladas com sucessos
        tickers = ["FAIL1", "SUCCESS1", "FAIL2", "SUCCESS2", "FAIL3", "SUCCESS3"]
        results = service.ingest_prices(tickers, lookback_days=1)
        
        # Verifica que todos os sucessos foram processados
        assert len(results["success"]) == 3
        assert "SUCCESS1" in results["success"]
        assert "SUCCESS2" in results["success"]
        assert "SUCCESS3" in results["success"]
        
        # Verifica que todas as falhas foram registradas
        assert len(results["failed"]) == 3
        failed_tickers = [f["ticker"] for f in results["failed"]]
        assert "FAIL1" in failed_tickers
        assert "FAIL2" in failed_tickers
        assert "FAIL3" in failed_tickers
        
        # Verifica que 3 registros foram inseridos
        assert results["total_records"] == 3
        
    finally:
        test_db.close()
