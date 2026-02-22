"""
Testes de propriedade para persistência de features.

Valida: Requisitos 2.9, 3.7
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.database import Base
from app.factor_engine.feature_service import FeatureService


# Estratégias para gerar dados de teste
@st.composite
def daily_features_data(draw):
    """Gera dados de features diárias para teste."""
    ticker = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu',)),
        min_size=3,
        max_size=5
    ))
    
    # Gerar data nos últimos 365 dias
    days_ago = draw(st.integers(min_value=0, max_value=365))
    feature_date = date.today() - timedelta(days=days_ago)
    
    # Gerar features (podem ser None)
    features = {
        'return_6m': draw(st.one_of(
            st.none(),
            st.floats(min_value=-1.0, max_value=5.0, allow_nan=False, allow_infinity=False)
        )),
        'return_12m': draw(st.one_of(
            st.none(),
            st.floats(min_value=-1.0, max_value=10.0, allow_nan=False, allow_infinity=False)
        )),
        'rsi_14': draw(st.one_of(
            st.none(),
            st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
        )),
        'volatility_90d': draw(st.one_of(
            st.none(),
            st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False)
        )),
        'recent_drawdown': draw(st.one_of(
            st.none(),
            st.floats(min_value=-1.0, max_value=0.0, allow_nan=False, allow_infinity=False)
        ))
    }
    
    return ticker, feature_date, features


@st.composite
def monthly_features_data(draw):
    """Gera dados de features mensais para teste."""
    ticker = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu',)),
        min_size=3,
        max_size=5
    ))
    
    # Gerar mês nos últimos 24 meses
    months_ago = draw(st.integers(min_value=0, max_value=24))
    today = date.today()
    month = date(today.year, today.month, 1) - timedelta(days=months_ago * 30)
    # Garantir que é o primeiro dia do mês
    month = date(month.year, month.month, 1)
    
    # Gerar features (podem ser None)
    features = {
        'roe': draw(st.one_of(
            st.none(),
            st.floats(min_value=-1.0, max_value=2.0, allow_nan=False, allow_infinity=False)
        )),
        'net_margin': draw(st.one_of(
            st.none(),
            st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False)
        )),
        'revenue_growth_3y': draw(st.one_of(
            st.none(),
            st.floats(min_value=-0.5, max_value=2.0, allow_nan=False, allow_infinity=False)
        )),
        'debt_to_ebitda': draw(st.one_of(
            st.none(),
            st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False)
        )),
        'pe_ratio': draw(st.one_of(
            st.none(),
            st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
        )),
        'ev_ebitda': draw(st.one_of(
            st.none(),
            st.floats(min_value=0.0, max_value=50.0, allow_nan=False, allow_infinity=False)
        )),
        'pb_ratio': draw(st.one_of(
            st.none(),
            st.floats(min_value=0.0, max_value=20.0, allow_nan=False, allow_infinity=False)
        ))
    }
    
    return ticker, month, features


def create_test_db_session():
    """Cria uma sessão de banco de dados em memória para testes."""
    # Criar engine SQLite em memória
    engine = create_engine("sqlite:///:memory:")
    
    # Criar todas as tabelas
    Base.metadata.create_all(engine)
    
    # Criar session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    return session


class TestFeaturePersistenceProperties:
    """
    Testes de propriedade para persistência de features.
    
    **Propriedade 3: Round-trip de Persistência de Features**
    **Valida: Requisitos 2.9, 3.7**
    """
    
    @given(daily_features_data())
    @settings(max_examples=20, deadline=None)
    def test_property_3_daily_features_round_trip(self, data):
        """
        **Propriedade 3: Round-trip de Persistência de Features Diárias**
        
        *Para qualquer* conjunto de features diárias calculadas, quando 
        armazenadas no banco de dados e posteriormente recuperadas, os 
        valores recuperados devem ser idênticos aos valores calculados.
        
        **Valida: Requisito 3.7**
        
        Feature: quant-stock-ranker, Property 3: Round-trip de Persistência de Features
        """
        ticker, feature_date, features = data
        
        # Criar sessão de banco de dados para este teste
        db_session = create_test_db_session()
        
        try:
            # Criar serviço
            service = FeatureService(db_session)
            
            # Salvar features
            saved_record = service.save_daily_features(ticker, feature_date, features)
            
            # Recuperar features
            retrieved_record = service.get_daily_features(ticker, feature_date)
            
            # Verificar que o registro foi recuperado
            assert retrieved_record is not None, "Failed to retrieve saved features"
            
            # Verificar que os valores são idênticos
            assert retrieved_record.ticker == ticker
            assert retrieved_record.date == feature_date
            
            # Comparar cada feature (considerando None)
            def compare_floats(a, b):
                """Compara floats considerando None."""
                if a is None and b is None:
                    return True
                if a is None or b is None:
                    return False
                return abs(a - b) < 1e-10
            
            assert compare_floats(retrieved_record.return_6m, features.get('return_6m')), (
                f"return_6m mismatch: {retrieved_record.return_6m} != {features.get('return_6m')}"
            )
            assert compare_floats(retrieved_record.return_12m, features.get('return_12m')), (
                f"return_12m mismatch: {retrieved_record.return_12m} != {features.get('return_12m')}"
            )
            assert compare_floats(retrieved_record.rsi_14, features.get('rsi_14')), (
                f"rsi_14 mismatch: {retrieved_record.rsi_14} != {features.get('rsi_14')}"
            )
            assert compare_floats(retrieved_record.volatility_90d, features.get('volatility_90d')), (
                f"volatility_90d mismatch: {retrieved_record.volatility_90d} != {features.get('volatility_90d')}"
            )
            assert compare_floats(retrieved_record.recent_drawdown, features.get('recent_drawdown')), (
                f"recent_drawdown mismatch: {retrieved_record.recent_drawdown} != {features.get('recent_drawdown')}"
            )
            
            # Verificar que timestamp foi criado
            assert retrieved_record.calculated_at is not None
        finally:
            db_session.close()
    
    @given(monthly_features_data())
    @settings(max_examples=20, deadline=None)
    def test_property_3_monthly_features_round_trip(self, data):
        """
        **Propriedade 3: Round-trip de Persistência de Features Mensais**
        
        *Para qualquer* conjunto de features mensais calculadas, quando 
        armazenadas no banco de dados e posteriormente recuperadas, os 
        valores recuperados devem ser idênticos aos valores calculados.
        
        **Valida: Requisito 2.9**
        
        Feature: quant-stock-ranker, Property 3: Round-trip de Persistência de Features
        """
        ticker, month, features = data
        
        # Criar sessão de banco de dados para este teste
        db_session = create_test_db_session()
        
        try:
            # Criar serviço
            service = FeatureService(db_session)
            
            # Salvar features
            saved_record = service.save_monthly_features(ticker, month, features)
            
            # Recuperar features
            retrieved_record = service.get_monthly_features(ticker, month)
            
            # Verificar que o registro foi recuperado
            assert retrieved_record is not None, "Failed to retrieve saved features"
            
            # Verificar que os valores são idênticos
            assert retrieved_record.ticker == ticker
            assert retrieved_record.month == month
            
            # Comparar cada feature (considerando None)
            def compare_floats(a, b):
                """Compara floats considerando None."""
                if a is None and b is None:
                    return True
                if a is None or b is None:
                    return False
                return abs(a - b) < 1e-10
            
            assert compare_floats(retrieved_record.roe, features.get('roe')), (
                f"roe mismatch: {retrieved_record.roe} != {features.get('roe')}"
            )
            assert compare_floats(retrieved_record.net_margin, features.get('net_margin')), (
                f"net_margin mismatch: {retrieved_record.net_margin} != {features.get('net_margin')}"
            )
            assert compare_floats(retrieved_record.revenue_growth_3y, features.get('revenue_growth_3y')), (
                f"revenue_growth_3y mismatch: {retrieved_record.revenue_growth_3y} != {features.get('revenue_growth_3y')}"
            )
            assert compare_floats(retrieved_record.debt_to_ebitda, features.get('debt_to_ebitda')), (
                f"debt_to_ebitda mismatch: {retrieved_record.debt_to_ebitda} != {features.get('debt_to_ebitda')}"
            )
            assert compare_floats(retrieved_record.pe_ratio, features.get('pe_ratio')), (
                f"pe_ratio mismatch: {retrieved_record.pe_ratio} != {features.get('pe_ratio')}"
            )
            assert compare_floats(retrieved_record.ev_ebitda, features.get('ev_ebitda')), (
                f"ev_ebitda mismatch: {retrieved_record.ev_ebitda} != {features.get('ev_ebitda')}"
            )
            assert compare_floats(retrieved_record.pb_ratio, features.get('pb_ratio')), (
                f"pb_ratio mismatch: {retrieved_record.pb_ratio} != {features.get('pb_ratio')}"
            )
            
            # Verificar que timestamp foi criado
            assert retrieved_record.calculated_at is not None
        finally:
            db_session.close()
    
    @given(daily_features_data())
    @settings(max_examples=10, deadline=None)
    def test_daily_features_update_idempotence(self, data):
        """
        Teste adicional: Salvar features duas vezes deve resultar em update, não duplicata.
        """
        ticker, feature_date, features = data
        
        # Criar sessão de banco de dados para este teste
        db_session = create_test_db_session()
        
        try:
            service = FeatureService(db_session)
            
            # Salvar primeira vez
            first_save = service.save_daily_features(ticker, feature_date, features)
            
            # Modificar features
            modified_features = features.copy()
            if modified_features.get('return_6m') is not None:
                modified_features['return_6m'] = modified_features['return_6m'] + 0.1
            
            # Salvar segunda vez (deve fazer update)
            second_save = service.save_daily_features(ticker, feature_date, modified_features)
            
            # Verificar que é o mesmo registro (mesmo ID)
            assert first_save.id == second_save.id
            
            # Verificar que só existe um registro
            all_records = service.get_all_daily_features_for_date(feature_date)
            ticker_records = [r for r in all_records if r.ticker == ticker]
            assert len(ticker_records) == 1
        finally:
            db_session.close()
