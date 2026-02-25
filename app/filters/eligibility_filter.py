"""
Eligibility filter for pre-screening financially distressed assets.

This module implements the eligibility filter layer that excludes assets
failing minimum financial health criteria before scoring.

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
"""

from typing import Dict, List, Tuple
import pandas as pd
import logging
from app.config import Settings

logger = logging.getLogger(__name__)


class EligibilityFilter:
    """
    Pre-screening filter to exclude financially distressed assets.
    
    This filter ensures that only fundamentally viable investments
    are included in the scoring universe.
    """
    
    def __init__(self, config: Settings):
        """
        Initialize the eligibility filter with configuration.
        
        Args:
            config: Settings object containing minimum_volume threshold
        """
        self.minimum_volume = config.minimum_volume
    
    def is_eligible(
        self,
        ticker: str,
        fundamentals: Dict[str, float],
        volume_data: pd.DataFrame
    ) -> Tuple[bool, List[str]]:
        """
        Check if asset meets minimum eligibility criteria.
        
        Exclusion criteria:
        - shareholders_equity <= 0
        - ebitda <= 0 (except financial institutions)
        - revenue <= 0
        - average daily volume < minimum_volume
        - net_income_last_year < 0 (negative profit)
        - net_income negative in 2 of last 3 years
        - net_debt_to_ebitda > 8 (excessive leverage)
        - Critical momentum factors missing (momentum_6m_ex_1m, momentum_12m_ex_1m)
        - Critical quality factors missing (roe_mean_3y, net_margin)
        - Critical value factors missing (pe_ratio, price_to_book)
        
        Args:
            ticker: Asset symbol
            fundamentals: Dict with shareholders_equity, ebitda, revenue, 
                         net_income_last_year, net_income_history (list of 3 years),
                         net_debt_to_ebitda, and all factor values
            volume_data: DataFrame with daily volume history (must have 'volume' column)
        
        Returns:
            Tuple of (is_eligible, exclusion_reasons)
            - is_eligible: True if asset passes all criteria
            - exclusion_reasons: List of reasons for exclusion (empty if eligible)
        
        Validates: Requirements 1.2, 1.3, 1.4, 1.5, 1.6
        """
        exclusion_reasons = []
        
        # Check for missing fundamental data
        if fundamentals is None:
            exclusion_reasons.append("insufficient_data")
            return False, exclusion_reasons
        
        # Extract fundamental values
        shareholders_equity = fundamentals.get('shareholders_equity')
        ebitda = fundamentals.get('ebitda')
        revenue = fundamentals.get('revenue')
        net_income_last_year = fundamentals.get('net_income_last_year')
        net_income_history = fundamentals.get('net_income_history', [])
        net_debt_to_ebitda = fundamentals.get('net_debt_to_ebitda')
        
        # Check validity of each metric
        has_valid_equity = shareholders_equity is not None and shareholders_equity > 0
        has_valid_ebitda = ebitda is not None and ebitda > 0
        has_valid_revenue = revenue is not None and revenue > 0
        
        # Determine if this is a financial institution (bank, insurance, etc.)
        # Financial institutions typically don't report EBITDA but have revenue and equity
        is_likely_financial_institution = (not has_valid_ebitda) and has_valid_revenue and has_valid_equity
        
        # Check shareholders_equity > 0 (Requirement 1.2)
        # Always required for all companies
        if not has_valid_equity:
            if shareholders_equity is None:
                exclusion_reasons.append("missing_shareholders_equity")
            else:
                exclusion_reasons.append("negative_or_zero_equity")
        
        # Check revenue > 0 (Requirement 1.4)
        # Always required for all companies
        if not has_valid_revenue:
            if revenue is None:
                exclusion_reasons.append("missing_revenue")
            else:
                exclusion_reasons.append("negative_or_zero_revenue")
        
        # Check ebitda > 0 (Requirement 1.3)
        # Exception: Financial institutions (banks) may not report EBITDA
        # We allow them to pass if they have valid revenue and equity
        if not has_valid_ebitda and not is_likely_financial_institution:
            if ebitda is None:
                exclusion_reasons.append("missing_ebitda")
            else:
                exclusion_reasons.append("negative_or_zero_ebitda")
        elif is_likely_financial_institution and not has_valid_ebitda:
            # For financial institutions, we don't require EBITDA
            logger.debug(f"Financial institution {ticker} - EBITDA not required")
        
        # NEW: Check net income last year >= 0
        if net_income_last_year is not None and net_income_last_year < 0:
            exclusion_reasons.append("negative_net_income_last_year")
        
        # NEW: Check net income history - exclude if negative in 2 of last 3 years
        if net_income_history and len(net_income_history) >= 3:
            negative_years = sum(1 for ni in net_income_history if ni is not None and ni < 0)
            if negative_years >= 2:
                exclusion_reasons.append("negative_net_income_2_of_3_years")
        
        # NEW: Check net debt to EBITDA ratio <= 8
        # Only apply to non-financial institutions (banks don't use this metric)
        if not is_likely_financial_institution:
            if net_debt_to_ebitda is not None and net_debt_to_ebitda > 8:
                exclusion_reasons.append("excessive_leverage_debt_to_ebitda_gt_8")
        
        # NEW: Check critical momentum factors
        critical_momentum = ['momentum_6m_ex_1m', 'momentum_12m_ex_1m']
        for factor in critical_momentum:
            value = fundamentals.get(factor)
            if value is None:
                exclusion_reasons.append(f"missing_critical_factor_{factor}")
        
        # NEW: Check critical quality factors
        critical_quality = ['roe_mean_3y', 'net_margin']
        for factor in critical_quality:
            value = fundamentals.get(factor)
            if value is None:
                exclusion_reasons.append(f"missing_critical_factor_{factor}")
        
        # NEW: Check critical value factors
        critical_value = ['pe_ratio', 'price_to_book']
        for factor in critical_value:
            value = fundamentals.get(factor)
            if value is None:
                exclusion_reasons.append(f"missing_critical_factor_{factor}")
        
        # Check average daily volume >= minimum_volume (Requirement 1.5)
        if volume_data is None or volume_data.empty:
            exclusion_reasons.append("insufficient_volume_data")
        else:
            if 'volume' not in volume_data.columns:
                exclusion_reasons.append("missing_volume_column")
            else:
                avg_volume = volume_data['volume'].mean()
                if pd.isna(avg_volume) or avg_volume < self.minimum_volume:
                    exclusion_reasons.append("low_volume")
        
        # Asset is eligible only if no exclusion reasons (Requirement 1.6)
        is_eligible = len(exclusion_reasons) == 0
        
        return is_eligible, exclusion_reasons
    
    def filter_universe(
        self,
        assets_data: Dict[str, Dict]
    ) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Filter entire universe of assets.
        
        Args:
            assets_data: Dict mapping ticker to {
                'fundamentals': Dict[str, float],
                'volume_data': pd.DataFrame
            }
        
        Returns:
            Tuple of (eligible_tickers, exclusion_reasons_by_ticker)
            - eligible_tickers: List of tickers that passed eligibility
            - exclusion_reasons_by_ticker: Dict mapping excluded tickers to their reasons
        
        Validates: Requirements 1.1, 1.6
        """
        eligible_tickers = []
        exclusion_reasons_by_ticker = {}
        
        for ticker, data in assets_data.items():
            fundamentals = data.get('fundamentals')
            volume_data = data.get('volume_data')
            
            is_eligible, reasons = self.is_eligible(ticker, fundamentals, volume_data)
            
            if is_eligible:
                eligible_tickers.append(ticker)
            else:
                exclusion_reasons_by_ticker[ticker] = reasons
        
        return eligible_tickers, exclusion_reasons_by_ticker
