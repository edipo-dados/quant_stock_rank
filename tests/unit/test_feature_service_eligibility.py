"""
Unit tests for eligibility filter integration in FeatureService.

Validates: Requirements 1.1, 1.6
"""

import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd

from app.models.database import Base
from app.models.schemas import RawPriceDaily, RawFundamental
from app.factor_engine.feature_service import FeatureService
from app.config import Settings


@pytest.fixture
def test_db():
    """Create in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)
    session = TestSessionLocal()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def test_config():
    """Create test configuration."""
    return Settings(
        minimum_volume=100000,
        database_url="sqlite:///:memory:",
        fmp_api_key=""
    )


def test_filter_eligible_assets_all_eligible(test_db, test_config):
    """
    Test that filter_eligible_assets correctly identifies all eligible assets.
    
    Validates: Requirements 1.1, 1.6
    """
    # Setup: Add eligible assets to database
    tickers = ["AAPL", "MSFT", "GOOGL"]
    reference_date = date(2024, 12, 31)
    
    for ticker in tickers:
        # Add fundamental data (all positive)
        fundamental = RawFundamental(
            ticker=ticker,
            period_end_date=reference_date,
            period_type='annual',
            shareholders_equity=100000000,
            ebitda=50000000,
            revenue=200000000,
            net_income=30000000,
            total_debt=20000000,
            eps=5.0,
            enterprise_value=500000000,
            book_value_per_share=50.0
        )
        test_db.add(fundamental)
        
        # Add volume data (above minimum)
        for i in range(90):
            price_date = date(2024, 10, 1) + timedelta(days=i)
            if price_date > reference_date:
                break
            price = RawPriceDaily(
                ticker=ticker,
                date=price_date,
                open=100.0,
                high=102.0,
                low=98.0,
                close=100.0,
                volume=150000,  # Above minimum
                adj_close=100.0
            )
            test_db.add(price)
    
    test_db.commit()
    
    # Execute
    feature_service = FeatureService(test_db, test_config)
    eligible_tickers, exclusion_reasons = feature_service.filter_eligible_assets(
        tickers,
        reference_date
    )
    
    # Verify
    assert len(eligible_tickers) == 3
    assert set(eligible_tickers) == set(tickers)
    assert len(exclusion_reasons) == 0


def test_filter_eligible_assets_some_excluded(test_db, test_config):
    """
    Test that filter_eligible_assets correctly excludes ineligible assets.
    
    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
    """
    reference_date = date(2024, 12, 31)
    
    # Add eligible asset
    fundamental_eligible = RawFundamental(
        ticker="AAPL",
        period_end_date=reference_date,
        period_type='annual',
        shareholders_equity=100000000,
        ebitda=50000000,
        revenue=200000000,
        net_income=30000000,
        total_debt=20000000,
        eps=5.0,
        enterprise_value=500000000,
        book_value_per_share=50.0
    )
    test_db.add(fundamental_eligible)
    
    for i in range(90):
        price_date = date(2024, 10, 1) + timedelta(days=i)
        if price_date > reference_date:
            break
        price = RawPriceDaily(
            ticker="AAPL",
            date=price_date,
            open=100.0,
            high=102.0,
            low=98.0,
            close=100.0,
            volume=150000,
            adj_close=100.0
        )
        test_db.add(price)
    
    # Add ineligible asset (negative equity)
    fundamental_ineligible = RawFundamental(
        ticker="MSFT",
        period_end_date=reference_date,
        period_type='annual',
        shareholders_equity=-10000000,  # Negative!
        ebitda=50000000,
        revenue=200000000,
        net_income=30000000,
        total_debt=20000000,
        eps=5.0,
        enterprise_value=500000000,
        book_value_per_share=50.0
    )
    test_db.add(fundamental_ineligible)
    
    for i in range(90):
        price_date = date(2024, 10, 1) + timedelta(days=i)
        if price_date > reference_date:
            break
        price = RawPriceDaily(
            ticker="MSFT",
            date=price_date,
            open=100.0,
            high=102.0,
            low=98.0,
            close=100.0,
            volume=150000,
            adj_close=100.0
        )
        test_db.add(price)
    
    # Add ineligible asset (low volume)
    fundamental_low_volume = RawFundamental(
        ticker="GOOGL",
        period_end_date=reference_date,
        period_type='annual',
        shareholders_equity=100000000,
        ebitda=50000000,
        revenue=200000000,
        net_income=30000000,
        total_debt=20000000,
        eps=5.0,
        enterprise_value=500000000,
        book_value_per_share=50.0
    )
    test_db.add(fundamental_low_volume)
    
    for i in range(90):
        price_date = date(2024, 10, 1) + timedelta(days=i)
        if price_date > reference_date:
            break
        price = RawPriceDaily(
            ticker="GOOGL",
            date=price_date,
            open=100.0,
            high=102.0,
            low=98.0,
            close=100.0,
            volume=50000,  # Below minimum!
            adj_close=100.0
        )
        test_db.add(price)
    
    test_db.commit()
    
    # Execute
    feature_service = FeatureService(test_db, test_config)
    eligible_tickers, exclusion_reasons = feature_service.filter_eligible_assets(
        ["AAPL", "MSFT", "GOOGL"],
        reference_date
    )
    
    # Verify
    assert len(eligible_tickers) == 1
    assert eligible_tickers[0] == "AAPL"
    
    assert len(exclusion_reasons) == 2
    assert "MSFT" in exclusion_reasons
    assert "GOOGL" in exclusion_reasons
    
    assert "negative_or_zero_equity" in exclusion_reasons["MSFT"]
    assert "low_volume" in exclusion_reasons["GOOGL"]


def test_filter_eligible_assets_missing_data(test_db, test_config):
    """
    Test that filter_eligible_assets handles missing data gracefully.
    
    Validates: Requirements 1.1, 1.6
    """
    reference_date = date(2024, 12, 31)
    
    # Don't add any data to database
    
    # Execute
    feature_service = FeatureService(test_db, test_config)
    eligible_tickers, exclusion_reasons = feature_service.filter_eligible_assets(
        ["AAPL", "MSFT"],
        reference_date
    )
    
    # Verify
    assert len(eligible_tickers) == 0
    assert len(exclusion_reasons) == 2
    
    # Both should be excluded due to insufficient data
    assert "AAPL" in exclusion_reasons
    assert "MSFT" in exclusion_reasons
    assert "insufficient_data" in exclusion_reasons["AAPL"]
    assert "insufficient_data" in exclusion_reasons["MSFT"]


def test_filter_eligible_assets_empty_list(test_db, test_config):
    """
    Test that filter_eligible_assets handles empty ticker list.
    
    Validates: Requirements 1.1, 1.6
    """
    reference_date = date(2024, 12, 31)
    
    # Execute with empty list
    feature_service = FeatureService(test_db, test_config)
    eligible_tickers, exclusion_reasons = feature_service.filter_eligible_assets(
        [],
        reference_date
    )
    
    # Verify
    assert len(eligible_tickers) == 0
    assert len(exclusion_reasons) == 0
