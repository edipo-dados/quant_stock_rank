"""
Missing value handler for feature engineering.

LAYER 2: Feature Engineering - Handle missing derived features
This module ensures NO asset is excluded due to missing calculated features.

Strategy:
1. Calculate all features for all eligible assets
2. If feature is missing, impute using:
   - Sector median (if sector has >= 5 assets)
   - Universe median (if sector < 5 assets)
3. Log all imputations for transparency

Architecture:
- LAYER 1: Structural Eligibility - raw data validation
- LAYER 2: Feature Engineering (this module) - calculate & impute features
- LAYER 3: Scoring & Normalization - rank assets
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MissingValueHandler:
    """
    Handles missing values in calculated features using sector/universe medians.
    
    Ensures no asset is excluded due to missing derived features.
    """
    
    def __init__(self):
        """Initialize missing value handler."""
        self.imputation_log = []
    
    def impute_missing_features(
        self,
        features_df: pd.DataFrame,
        sector_map: Optional[Dict[str, str]] = None,
        min_sector_size: int = 5
    ) -> pd.DataFrame:
        """
        Impute missing features using sector or universe medians.
        
        Strategy:
        1. For each feature with missing values:
           - Try sector median (if sector >= min_sector_size)
           - Fall back to universe median
        2. Log all imputations
        3. Return complete DataFrame (no NaN in critical features)
        
        Args:
            features_df: DataFrame with tickers as index, features as columns
            sector_map: Dict mapping ticker -> sector (optional)
            min_sector_size: Minimum sector size to use sector median
        
        Returns:
            DataFrame with imputed values
        """
        df = features_df.copy()
        
        # Log initial missing counts
        missing_counts = df.isnull().sum()
        total_missing = missing_counts.sum()
        
        if total_missing > 0:
            logger.info(f"Missing values detected: {total_missing} total across {(missing_counts > 0).sum()} features")
            for col in missing_counts[missing_counts > 0].index:
                logger.info(f"  - {col}: {missing_counts[col]} missing ({missing_counts[col]/len(df)*100:.1f}%)")
        
        # Impute each feature
        for col in df.columns:
            missing_mask = df[col].isnull()
            n_missing = missing_mask.sum()
            
            if n_missing == 0:
                continue
            
            # Try sector-based imputation if sector_map provided
            if sector_map is not None:
                imputed_count = self._impute_by_sector(
                    df, col, missing_mask, sector_map, min_sector_size
                )
                
                # Update missing mask after sector imputation
                missing_mask = df[col].isnull()
                n_still_missing = missing_mask.sum()
                
                if n_still_missing > 0:
                    # Fall back to universe median for remaining
                    self._impute_by_universe(df, col, missing_mask)
            else:
                # No sector info, use universe median directly
                self._impute_by_universe(df, col, missing_mask)
        
        # Verify no missing values remain
        final_missing = df.isnull().sum().sum()
        if final_missing > 0:
            logger.warning(f"Still have {final_missing} missing values after imputation!")
        else:
            logger.info(f"Successfully imputed all missing values ({total_missing} total)")
        
        return df
    
    def _impute_by_sector(
        self,
        df: pd.DataFrame,
        col: str,
        missing_mask: pd.Series,
        sector_map: Dict[str, str],
        min_sector_size: int
    ) -> int:
        """
        Impute missing values using sector median.
        
        Returns:
            Number of values imputed
        """
        imputed_count = 0
        
        for ticker in df[missing_mask].index:
            sector = sector_map.get(ticker)
            
            if sector is None:
                continue
            
            # Get sector peers
            sector_tickers = [t for t, s in sector_map.items() if s == sector and t in df.index]
            
            if len(sector_tickers) < min_sector_size:
                continue
            
            # Calculate sector median (excluding missing)
            sector_values = df.loc[sector_tickers, col].dropna()
            
            if len(sector_values) == 0:
                continue
            
            sector_median = sector_values.median()
            df.loc[ticker, col] = sector_median
            
            self.imputation_log.append({
                'ticker': ticker,
                'feature': col,
                'method': 'sector_median',
                'sector': sector,
                'value': sector_median
            })
            
            imputed_count += 1
        
        if imputed_count > 0:
            logger.debug(f"Imputed {imputed_count} values for {col} using sector median")
        
        return imputed_count
    
    def _impute_by_universe(
        self,
        df: pd.DataFrame,
        col: str,
        missing_mask: pd.Series
    ):
        """
        Impute missing values using universe median.
        """
        # Calculate universe median (excluding missing)
        universe_median = df.loc[~missing_mask, col].median()
        
        if pd.isna(universe_median):
            # All values are missing, use 0 as fallback
            logger.warning(f"All values missing for {col}, using 0 as fallback")
            universe_median = 0.0
        
        # Impute
        n_imputed = missing_mask.sum()
        df.loc[missing_mask, col] = universe_median
        
        for ticker in df[missing_mask].index:
            self.imputation_log.append({
                'ticker': ticker,
                'feature': col,
                'method': 'universe_median',
                'value': universe_median
            })
        
        logger.debug(f"Imputed {n_imputed} values for {col} using universe median ({universe_median:.4f})")
    
    def get_imputation_summary(self) -> pd.DataFrame:
        """
        Get summary of all imputations performed.
        
        Returns:
            DataFrame with imputation log
        """
        if not self.imputation_log:
            return pd.DataFrame()
        
        return pd.DataFrame(self.imputation_log)
    
    def clear_log(self):
        """Clear imputation log."""
        self.imputation_log = []
