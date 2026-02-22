"""
Testes unitários para schemas de banco de dados.

Valida: Requisitos 8.7, 8.8
"""

import pytest
from datetime import date, datetime
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.models.database import Base
from app.models.schemas import (
    RawPriceDaily,
    RawFundamental,
    FeatureDaily,
    FeatureMonthly,
    ScoreDaily
)


@pytest.fixture(scope="module")
def test_engine():
    """Cria engine de teste em memória."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Cria sessão de teste para cada teste."""
    # Recria todas as tabelas para cada teste
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.rollback()
    session.close()


class TestTimestampFields:
    """
    Testa que todas as tabelas têm campos de timestamp.
    
    Valida: Requisito 8.8
    """
    
    def test_raw_price_daily_has_timestamp(self, test_db):
        """RawPriceDaily deve ter campo created_at."""
        price = RawPriceDaily(
            ticker="TEST",
            date=date(2024, 1, 1),
            close=100.0,
            adj_close=100.0
        )
        test_db.add(price)
        test_db.commit()
        
        assert price.created_at is not None
        assert isinstance(price.created_at, datetime)
    
    def test_raw_fundamental_has_timestamp(self, test_db):
        """RawFundamental deve ter campo fetched_at."""
        fundamental = RawFundamental(
            ticker="TEST",
            period_end_date=date(2024, 1, 1),
            period_type="annual"
        )
        test_db.add(fundamental)
        test_db.commit()
        
        assert fundamental.fetched_at is not None
        assert isinstance(fundamental.fetched_at, datetime)
    
    def test_feature_daily_has_timestamp(self, test_db):
        """FeatureDaily deve ter campo calculated_at."""
        feature = FeatureDaily(
            ticker="TEST",
            date=date(2024, 1, 1)
        )
        test_db.add(feature)
        test_db.commit()
        
        assert feature.calculated_at is not None
        assert isinstance(feature.calculated_at, datetime)
    
    def test_feature_monthly_has_timestamp(self, test_db):
        """FeatureMonthly deve ter campo calculated_at."""
        feature = FeatureMonthly(
            ticker="TEST",
            month=date(2024, 1, 1)
        )
        test_db.add(feature)
        test_db.commit()
        
        assert feature.calculated_at is not None
        assert isinstance(feature.calculated_at, datetime)
    
    def test_score_daily_has_timestamp(self, test_db):
        """ScoreDaily deve ter campo calculated_at."""
        score = ScoreDaily(
            ticker="TEST",
            date=date(2024, 1, 1),
            final_score=1.5,
            momentum_score=1.0,
            quality_score=2.0,
            value_score=1.5,
            confidence=0.5
        )
        test_db.add(score)
        test_db.commit()
        
        assert score.calculated_at is not None
        assert isinstance(score.calculated_at, datetime)


class TestIndexConfiguration:
    """
    Testa que índices estão configurados corretamente.
    
    Valida: Requisito 8.7
    """
    
    def test_raw_price_daily_indexes(self, test_engine):
        """RawPriceDaily deve ter índices corretos."""
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes("raw_prices_daily")
        
        # Verifica que existem índices
        assert len(indexes) > 0
        
        # Verifica índice em ticker
        ticker_indexed = any(
            'ticker' in idx['column_names'] 
            for idx in indexes
        )
        assert ticker_indexed, "Ticker deve estar indexado"
        
        # Verifica índice em date
        date_indexed = any(
            'date' in idx['column_names'] 
            for idx in indexes
        )
        assert date_indexed, "Date deve estar indexado"
    
    def test_raw_fundamental_indexes(self, test_engine):
        """RawFundamental deve ter índices corretos."""
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes("raw_fundamentals")
        
        # Verifica que existem índices
        assert len(indexes) > 0
        
        # Verifica índice em ticker
        ticker_indexed = any(
            'ticker' in idx['column_names'] 
            for idx in indexes
        )
        assert ticker_indexed, "Ticker deve estar indexado"
    
    def test_feature_daily_indexes(self, test_engine):
        """FeatureDaily deve ter índices corretos."""
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes("features_daily")
        
        # Verifica que existem índices
        assert len(indexes) > 0
        
        # Verifica índice em ticker
        ticker_indexed = any(
            'ticker' in idx['column_names'] 
            for idx in indexes
        )
        assert ticker_indexed, "Ticker deve estar indexado"
        
        # Verifica índice em date
        date_indexed = any(
            'date' in idx['column_names'] 
            for idx in indexes
        )
        assert date_indexed, "Date deve estar indexado"
    
    def test_feature_monthly_indexes(self, test_engine):
        """FeatureMonthly deve ter índices corretos."""
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes("features_monthly")
        
        # Verifica que existem índices
        assert len(indexes) > 0
        
        # Verifica índice em ticker
        ticker_indexed = any(
            'ticker' in idx['column_names'] 
            for idx in indexes
        )
        assert ticker_indexed, "Ticker deve estar indexado"
        
        # Verifica índice em month
        month_indexed = any(
            'month' in idx['column_names'] 
            for idx in indexes
        )
        assert month_indexed, "Month deve estar indexado"
    
    def test_score_daily_indexes(self, test_engine):
        """ScoreDaily deve ter índices corretos."""
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes("scores_daily")
        
        # Verifica que existem índices
        assert len(indexes) > 0
        
        # Verifica índice em ticker
        ticker_indexed = any(
            'ticker' in idx['column_names'] 
            for idx in indexes
        )
        assert ticker_indexed, "Ticker deve estar indexado"
        
        # Verifica índice em date
        date_indexed = any(
            'date' in idx['column_names'] 
            for idx in indexes
        )
        assert date_indexed, "Date deve estar indexado"


class TestUniqueConstraints:
    """Testa que constraints únicos funcionam corretamente."""
    
    def test_raw_price_daily_unique_constraint(self, test_db):
        """Não deve permitir duplicatas de ticker+date em RawPriceDaily."""
        price1 = RawPriceDaily(
            ticker="TEST",
            date=date(2024, 1, 1),
            close=100.0,
            adj_close=100.0
        )
        test_db.add(price1)
        test_db.commit()
        
        # Tenta adicionar duplicata
        price2 = RawPriceDaily(
            ticker="TEST",
            date=date(2024, 1, 1),
            close=101.0,
            adj_close=101.0
        )
        test_db.add(price2)
        
        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()
    
    def test_feature_daily_unique_constraint(self, test_db):
        """Não deve permitir duplicatas de ticker+date em FeatureDaily."""
        feature1 = FeatureDaily(
            ticker="TEST",
            date=date(2024, 1, 1),
            return_6m=0.1
        )
        test_db.add(feature1)
        test_db.commit()
        
        # Tenta adicionar duplicata
        feature2 = FeatureDaily(
            ticker="TEST",
            date=date(2024, 1, 1),
            return_6m=0.2
        )
        test_db.add(feature2)
        
        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()
    
    def test_score_daily_unique_constraint(self, test_db):
        """Não deve permitir duplicatas de ticker+date em ScoreDaily."""
        score1 = ScoreDaily(
            ticker="TEST",
            date=date(2024, 1, 1),
            final_score=1.5,
            momentum_score=1.0,
            quality_score=2.0,
            value_score=1.5,
            confidence=0.5
        )
        test_db.add(score1)
        test_db.commit()
        
        # Tenta adicionar duplicata
        score2 = ScoreDaily(
            ticker="TEST",
            date=date(2024, 1, 1),
            final_score=2.0,
            momentum_score=1.5,
            quality_score=2.5,
            value_score=2.0,
            confidence=0.6
        )
        test_db.add(score2)
        
        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()


class TestModelRepresentations:
    """Testa que os modelos têm representações string adequadas."""
    
    def test_raw_price_daily_repr(self):
        """RawPriceDaily deve ter __repr__ legível."""
        price = RawPriceDaily(
            ticker="TEST",
            date=date(2024, 1, 1),
            close=100.0,
            adj_close=100.0
        )
        repr_str = repr(price)
        assert "TEST" in repr_str
        assert "2024-01-01" in repr_str
        assert "100.0" in repr_str
    
    def test_score_daily_repr(self):
        """ScoreDaily deve ter __repr__ legível."""
        score = ScoreDaily(
            ticker="TEST",
            date=date(2024, 1, 1),
            final_score=1.5,
            momentum_score=1.0,
            quality_score=2.0,
            value_score=1.5,
            confidence=0.5,
            rank=1
        )
        repr_str = repr(score)
        assert "TEST" in repr_str
        assert "2024-01-01" in repr_str
        assert "1.5" in repr_str
        assert "1" in repr_str
