"""
Unit tests for eligibility filter.

Tests specific examples and edge cases for the EligibilityFilter class.
"""

import pytest
import pandas as pd
from app.filters.eligibility_filter import EligibilityFilter
from app.config import Settings


@pytest.fixture
def config():
    """Create a test configuration."""
    return Settings(minimum_volume=100000)


@pytest.fixture
def eligibility_filter(config):
    """Create an eligibility filter instance."""
    return EligibilityFilter(config)


class TestEligibilityFilterExamples:
    """Test specific examples of eligibility filtering."""
    
    def test_eligible_asset_passes_all_criteria(self, eligibility_filter):
        """Test that an asset with all positive values and sufficient volume is eligible."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'ebitda': 50000,
            'revenue': 200000
        }
        volume_data = pd.DataFrame({'volume': [150000] * 90})
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is True
        assert len(reasons) == 0
    
    def test_negative_equity_excludes_asset(self, eligibility_filter):
        """Test that negative shareholders_equity excludes the asset."""
        fundamentals = {
            'shareholders_equity': -1000,
            'ebitda': 5000,
            'revenue': 10000
        }
        volume_data = pd.DataFrame({'volume': [150000] * 90})
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is False
        assert 'negative_or_zero_equity' in reasons
    
    def test_zero_equity_excludes_asset(self, eligibility_filter):
        """Test that zero shareholders_equity excludes the asset."""
        fundamentals = {
            'shareholders_equity': 0,
            'ebitda': 5000,
            'revenue': 10000
        }
        volume_data = pd.DataFrame({'volume': [150000] * 90})
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is False
        assert 'negative_or_zero_equity' in reasons
    
    def test_negative_ebitda_excludes_asset(self, eligibility_filter):
        """Test that negative EBITDA excludes the asset."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'ebitda': -5000,
            'revenue': 10000
        }
        volume_data = pd.DataFrame({'volume': [150000] * 90})
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is False
        assert 'negative_or_zero_ebitda' in reasons
    
    def test_zero_ebitda_excludes_asset(self, eligibility_filter):
        """Test that zero EBITDA excludes the asset."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'ebitda': 0,
            'revenue': 10000
        }
        volume_data = pd.DataFrame({'volume': [150000] * 90})
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is False
        assert 'negative_or_zero_ebitda' in reasons
    
    def test_negative_revenue_excludes_asset(self, eligibility_filter):
        """Test that negative revenue excludes the asset."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'ebitda': 5000,
            'revenue': -10000
        }
        volume_data = pd.DataFrame({'volume': [150000] * 90})
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is False
        assert 'negative_or_zero_revenue' in reasons
    
    def test_zero_revenue_excludes_asset(self, eligibility_filter):
        """Test that zero revenue excludes the asset."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'ebitda': 5000,
            'revenue': 0
        }
        volume_data = pd.DataFrame({'volume': [150000] * 90})
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is False
        assert 'negative_or_zero_revenue' in reasons
    
    def test_low_volume_excludes_asset(self, eligibility_filter):
        """Test that volume below minimum excludes the asset."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'ebitda': 5000,
            'revenue': 10000
        }
        volume_data = pd.DataFrame({'volume': [50000] * 90})  # Below 100000
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is False
        assert 'low_volume' in reasons
    
    def test_volume_exactly_at_threshold_is_eligible(self, eligibility_filter):
        """Test that volume exactly at minimum is eligible."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'ebitda': 5000,
            'revenue': 10000
        }
        volume_data = pd.DataFrame({'volume': [100000] * 90})  # Exactly at threshold
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is True
        assert len(reasons) == 0
    
    def test_multiple_violations_returns_all_reasons(self, eligibility_filter):
        """Test that multiple violations are all captured."""
        fundamentals = {
            'shareholders_equity': -1000,
            'ebitda': 0,
            'revenue': -5000
        }
        volume_data = pd.DataFrame({'volume': [50000] * 90})
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is False
        assert 'negative_or_zero_equity' in reasons
        assert 'negative_or_zero_ebitda' in reasons
        assert 'negative_or_zero_revenue' in reasons
        assert 'low_volume' in reasons
        assert len(reasons) == 4


class TestEligibilityFilterEdgeCases:
    """Test edge cases for eligibility filtering."""
    
    def test_missing_fundamental_data(self, eligibility_filter):
        """Test with None fundamentals."""
        is_eligible, reasons = eligibility_filter.is_eligible(
            'TEST',
            None,
            pd.DataFrame({'volume': [150000] * 90})
        )
        
        assert is_eligible is False
        assert 'insufficient_data' in reasons
    
    def test_missing_shareholders_equity_field(self, eligibility_filter):
        """Test with missing shareholders_equity field."""
        fundamentals = {
            'ebitda': 5000,
            'revenue': 10000
        }
        volume_data = pd.DataFrame({'volume': [150000] * 90})
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is False
        assert 'missing_shareholders_equity' in reasons
    
    def test_missing_ebitda_field(self, eligibility_filter):
        """Test with missing ebitda field."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'revenue': 10000
        }
        volume_data = pd.DataFrame({'volume': [150000] * 90})
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is False
        assert 'missing_ebitda' in reasons
    
    def test_missing_revenue_field(self, eligibility_filter):
        """Test with missing revenue field."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'ebitda': 5000
        }
        volume_data = pd.DataFrame({'volume': [150000] * 90})
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is False
        assert 'missing_revenue' in reasons
    
    def test_empty_volume_data(self, eligibility_filter):
        """Test with empty volume DataFrame."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'ebitda': 5000,
            'revenue': 10000
        }
        volume_data = pd.DataFrame()
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is False
        assert 'insufficient_volume_data' in reasons
    
    def test_none_volume_data(self, eligibility_filter):
        """Test with None volume data."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'ebitda': 5000,
            'revenue': 10000
        }
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, None)
        
        assert is_eligible is False
        assert 'insufficient_volume_data' in reasons
    
    def test_missing_volume_column(self, eligibility_filter):
        """Test with DataFrame missing volume column."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'ebitda': 5000,
            'revenue': 10000
        }
        volume_data = pd.DataFrame({'price': [100] * 90})  # Wrong column
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is False
        assert 'missing_volume_column' in reasons


class TestFilterUniverse:
    """Test the filter_universe method."""
    
    def test_filter_universe_with_mixed_assets(self, eligibility_filter):
        """Test filtering a universe with both eligible and ineligible assets."""
        assets_data = {
            'AAPL': {
                'fundamentals': {
                    'shareholders_equity': 1000000,
                    'ebitda': 50000,
                    'revenue': 200000
                },
                'volume_data': pd.DataFrame({'volume': [150000] * 90})
            },
            'BADCO': {
                'fundamentals': {
                    'shareholders_equity': -1000,
                    'ebitda': 5000,
                    'revenue': 10000
                },
                'volume_data': pd.DataFrame({'volume': [150000] * 90})
            },
            'MSFT': {
                'fundamentals': {
                    'shareholders_equity': 2000000,
                    'ebitda': 100000,
                    'revenue': 400000
                },
                'volume_data': pd.DataFrame({'volume': [200000] * 90})
            },
            'LOWVOL': {
                'fundamentals': {
                    'shareholders_equity': 500000,
                    'ebitda': 10000,
                    'revenue': 50000
                },
                'volume_data': pd.DataFrame({'volume': [50000] * 90})
            }
        }
        
        eligible, excluded = eligibility_filter.filter_universe(assets_data)
        
        assert 'AAPL' in eligible
        assert 'MSFT' in eligible
        assert 'BADCO' not in eligible
        assert 'LOWVOL' not in eligible
        assert len(eligible) == 2
        assert len(excluded) == 2
        assert 'negative_or_zero_equity' in excluded['BADCO']
        assert 'low_volume' in excluded['LOWVOL']
    
    def test_filter_universe_all_eligible(self, eligibility_filter):
        """Test filtering when all assets are eligible."""
        assets_data = {
            'AAPL': {
                'fundamentals': {
                    'shareholders_equity': 1000000,
                    'ebitda': 50000,
                    'revenue': 200000
                },
                'volume_data': pd.DataFrame({'volume': [150000] * 90})
            },
            'MSFT': {
                'fundamentals': {
                    'shareholders_equity': 2000000,
                    'ebitda': 100000,
                    'revenue': 400000
                },
                'volume_data': pd.DataFrame({'volume': [200000] * 90})
            }
        }
        
        eligible, excluded = eligibility_filter.filter_universe(assets_data)
        
        assert len(eligible) == 2
        assert len(excluded) == 0
        assert 'AAPL' in eligible
        assert 'MSFT' in eligible
    
    def test_filter_universe_all_ineligible(self, eligibility_filter):
        """Test filtering when all assets are ineligible."""
        assets_data = {
            'BADCO1': {
                'fundamentals': {
                    'shareholders_equity': -1000,
                    'ebitda': 5000,
                    'revenue': 10000
                },
                'volume_data': pd.DataFrame({'volume': [150000] * 90})
            },
            'BADCO2': {
                'fundamentals': {
                    'shareholders_equity': 1000000,
                    'ebitda': 0,
                    'revenue': 10000
                },
                'volume_data': pd.DataFrame({'volume': [150000] * 90})
            }
        }
        
        eligible, excluded = eligibility_filter.filter_universe(assets_data)
        
        assert len(eligible) == 0
        assert len(excluded) == 2
        assert 'BADCO1' in excluded
        assert 'BADCO2' in excluded
    
    def test_filter_universe_empty_input(self, eligibility_filter):
        """Test filtering with empty assets_data."""
        assets_data = {}
        
        eligible, excluded = eligibility_filter.filter_universe(assets_data)
        
        assert len(eligible) == 0
        assert len(excluded) == 0



# Property-Based Tests
from hypothesis import given, strategies as st, assume, settings
import hypothesis.strategies as st


class TestEligibilityFilterProperties:
    """Property-based tests for eligibility filter."""
    
    @given(
        shareholders_equity=st.floats(max_value=0, allow_nan=False, allow_infinity=False),
        ebitda=st.floats(min_value=0.01, allow_nan=False, allow_infinity=False),
        revenue=st.floats(min_value=0.01, allow_nan=False, allow_infinity=False),
        avg_volume=st.floats(min_value=100000, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=20, deadline=None)
    def test_property_1_negative_or_zero_equity_excludes(
        self,
        shareholders_equity,
        ebitda,
        revenue,
        avg_volume
    ):
        """
        Property 1: Eligibility Filter Exclusion Rules
        Feature: scoring-model-improvements
        
        For any asset with shareholders_equity <= 0, the Eligibility_Filter
        should exclude it from the Universe and provide the specific exclusion reason.
        
        Validates: Requirements 1.2
        """
        config = Settings(minimum_volume=100000)
        filter_instance = EligibilityFilter(config)
        
        fundamentals = {
            'shareholders_equity': shareholders_equity,
            'ebitda': ebitda,
            'revenue': revenue
        }
        volume_data = pd.DataFrame({'volume': [avg_volume] * 90})
        
        is_eligible, reasons = filter_instance.is_eligible('TEST', fundamentals, volume_data)
        
        # Asset should be excluded
        assert is_eligible is False
        # Exclusion reason should include negative_or_zero_equity
        assert 'negative_or_zero_equity' in reasons
    
    @given(
        shareholders_equity=st.floats(min_value=0.01, allow_nan=False, allow_infinity=False),
        ebitda=st.floats(max_value=0, allow_nan=False, allow_infinity=False),
        revenue=st.floats(min_value=0.01, allow_nan=False, allow_infinity=False),
        avg_volume=st.floats(min_value=100000, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=20, deadline=None)
    def test_property_1_negative_or_zero_ebitda_excludes(
        self,
        shareholders_equity,
        ebitda,
        revenue,
        avg_volume
    ):
        """
        Property 1: Eligibility Filter Exclusion Rules
        Feature: scoring-model-improvements
        
        For any asset with EBITDA <= 0, the Eligibility_Filter
        should exclude it from the Universe and provide the specific exclusion reason.
        
        Validates: Requirements 1.3
        """
        config = Settings(minimum_volume=100000)
        filter_instance = EligibilityFilter(config)
        
        fundamentals = {
            'shareholders_equity': shareholders_equity,
            'ebitda': ebitda,
            'revenue': revenue
        }
        volume_data = pd.DataFrame({'volume': [avg_volume] * 90})
        
        is_eligible, reasons = filter_instance.is_eligible('TEST', fundamentals, volume_data)
        
        # Asset should be excluded
        assert is_eligible is False
        # Exclusion reason should include negative_or_zero_ebitda
        assert 'negative_or_zero_ebitda' in reasons
    
    @given(
        shareholders_equity=st.floats(min_value=0.01, allow_nan=False, allow_infinity=False),
        ebitda=st.floats(min_value=0.01, allow_nan=False, allow_infinity=False),
        revenue=st.floats(max_value=0, allow_nan=False, allow_infinity=False),
        avg_volume=st.floats(min_value=100000, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=20, deadline=None)
    def test_property_1_negative_or_zero_revenue_excludes(
        self,
        shareholders_equity,
        ebitda,
        revenue,
        avg_volume
    ):
        """
        Property 1: Eligibility Filter Exclusion Rules
        Feature: scoring-model-improvements
        
        For any asset with revenue <= 0, the Eligibility_Filter
        should exclude it from the Universe and provide the specific exclusion reason.
        
        Validates: Requirements 1.4
        """
        config = Settings(minimum_volume=100000)
        filter_instance = EligibilityFilter(config)
        
        fundamentals = {
            'shareholders_equity': shareholders_equity,
            'ebitda': ebitda,
            'revenue': revenue
        }
        volume_data = pd.DataFrame({'volume': [avg_volume] * 90})
        
        is_eligible, reasons = filter_instance.is_eligible('TEST', fundamentals, volume_data)
        
        # Asset should be excluded
        assert is_eligible is False
        # Exclusion reason should include negative_or_zero_revenue
        assert 'negative_or_zero_revenue' in reasons
    
    @given(
        shareholders_equity=st.floats(min_value=0.01, allow_nan=False, allow_infinity=False),
        ebitda=st.floats(min_value=0.01, allow_nan=False, allow_infinity=False),
        revenue=st.floats(min_value=0.01, allow_nan=False, allow_infinity=False),
        avg_volume=st.floats(min_value=0, max_value=99999.99, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=20, deadline=None)
    def test_property_1_low_volume_excludes(
        self,
        shareholders_equity,
        ebitda,
        revenue,
        avg_volume
    ):
        """
        Property 1: Eligibility Filter Exclusion Rules
        Feature: scoring-model-improvements
        
        For any asset with average daily volume below the configured minimum,
        the Eligibility_Filter should exclude it from the Universe and provide
        the specific exclusion reason.
        
        Validates: Requirements 1.5
        """
        config = Settings(minimum_volume=100000)
        filter_instance = EligibilityFilter(config)
        
        fundamentals = {
            'shareholders_equity': shareholders_equity,
            'ebitda': ebitda,
            'revenue': revenue
        }
        volume_data = pd.DataFrame({'volume': [avg_volume] * 90})
        
        is_eligible, reasons = filter_instance.is_eligible('TEST', fundamentals, volume_data)
        
        # Asset should be excluded
        assert is_eligible is False
        # Exclusion reason should include low_volume
        assert 'low_volume' in reasons
    
    @given(
        shareholders_equity=st.floats(min_value=0.01, max_value=1e12, allow_nan=False, allow_infinity=False),
        ebitda=st.floats(min_value=0.01, max_value=1e12, allow_nan=False, allow_infinity=False),
        revenue=st.floats(min_value=0.01, max_value=1e12, allow_nan=False, allow_infinity=False),
        avg_volume=st.floats(min_value=100000, max_value=1e12, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=20, deadline=None)
    def test_property_2_eligibility_inclusion_rule(
        self,
        shareholders_equity,
        ebitda,
        revenue,
        avg_volume
    ):
        """
        Property 2: Eligibility Filter Inclusion Rule
        Feature: scoring-model-improvements
        
        For any asset that has shareholders_equity > 0, EBITDA > 0, revenue > 0,
        and average daily volume >= the configured minimum, the Eligibility_Filter
        should include it in the Universe for scoring.
        
        Validates: Requirements 1.6
        """
        config = Settings(minimum_volume=100000)
        filter_instance = EligibilityFilter(config)
        
        fundamentals = {
            'shareholders_equity': shareholders_equity,
            'ebitda': ebitda,
            'revenue': revenue
        }
        volume_data = pd.DataFrame({'volume': [avg_volume] * 90})
        
        is_eligible, reasons = filter_instance.is_eligible('TEST', fundamentals, volume_data)
        
        # Asset should be included
        assert is_eligible is True
        # No exclusion reasons should be present
        assert len(reasons) == 0



class TestRobustnessImprovements:
    """Test robustness improvements to eligibility filter."""
    
    def test_negative_net_income_last_year_excludes(self, eligibility_filter):
        """Test that negative net income in last year excludes the asset."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'ebitda': 50000,
            'revenue': 200000,
            'net_income_last_year': -10000,
            'net_income_history': [50000, 60000, -10000],
            'net_debt_to_ebitda': 2.0
        }
        volume_data = pd.DataFrame({'volume': [150000] * 90})
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is False
        assert 'negative_net_income_last_year' in reasons
    
    def test_negative_net_income_2_of_3_years_excludes(self, eligibility_filter):
        """Test that negative net income in 2 of last 3 years excludes the asset."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'ebitda': 50000,
            'revenue': 200000,
            'net_income_last_year': 10000,
            'net_income_history': [-50000, -60000, 10000],
            'net_debt_to_ebitda': 2.0
        }
        volume_data = pd.DataFrame({'volume': [150000] * 90})
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is False
        assert 'negative_net_income_2_of_3_years' in reasons
    
    def test_excessive_leverage_excludes(self, eligibility_filter):
        """Test that net debt to EBITDA > 8 excludes the asset."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'ebitda': 50000,
            'revenue': 200000,
            'net_income_last_year': 10000,
            'net_income_history': [50000, 60000, 10000],
            'net_debt_to_ebitda': 9.0
        }
        volume_data = pd.DataFrame({'volume': [150000] * 90})
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is False
        assert 'excessive_leverage_debt_to_ebitda_gt_8' in reasons
    
    def test_financial_institution_exempt_from_leverage_check(self, eligibility_filter):
        """Test that financial institutions are exempt from leverage checks."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'ebitda': None,  # Financial institutions don't report EBITDA
            'revenue': 200000,
            'net_income_last_year': 10000,
            'net_income_history': [50000, 60000, 10000],
            'net_debt_to_ebitda': 15.0  # Would normally exclude
        }
        volume_data = pd.DataFrame({'volume': [150000] * 90})
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        # Should be eligible - financial institutions are exempt
        assert is_eligible is True
        assert len(reasons) == 0
    
    def test_all_robustness_criteria_pass(self, eligibility_filter):
        """Test that asset with all positive robustness metrics is eligible."""
        fundamentals = {
            'shareholders_equity': 1000000,
            'ebitda': 50000,
            'revenue': 200000,
            'net_income_last_year': 10000,
            'net_income_history': [50000, 60000, 10000],
            'net_debt_to_ebitda': 3.0
        }
        volume_data = pd.DataFrame({'volume': [150000] * 90})
        
        is_eligible, reasons = eligibility_filter.is_eligible('TEST', fundamentals, volume_data)
        
        assert is_eligible is True
        assert len(reasons) == 0
