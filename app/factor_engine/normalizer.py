"""
Normalização cross-sectional de fatores.

Valida: Requisitos 2.8, 3.6
"""

from typing import List
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class CrossSectionalNormalizer:
    """
    Normaliza fatores usando ranking percentual cross-sectional.
    
    A normalização cross-sectional compara todos os ativos no mesmo período,
    usando ranking percentual em vez de z-score para evitar explosão estatística
    causada por outliers em múltiplos financeiros.
    
    Método: percentile_rank = rank(x) / N, depois normaliza para [-1, +1]
    
    Valida: Requisitos 2.8, 3.6
    """
    
    def normalize_factors(
        self, 
        factors_df: pd.DataFrame, 
        factor_columns: List[str]
    ) -> pd.DataFrame:
        """
        Normaliza fatores via ranking percentual cross-sectional.
        
        Para cada fator:
            1. percentile_rank = rank(x) / N  (valores entre 0 e 1)
            2. normalized = 2 * percentile_rank - 1  (valores entre -1 e +1)
        
        Este método é mais robusto que z-score pois:
        - Elimina explosão estatística causada por outliers
        - Não assume distribuição normal
        - Trata múltiplos financeiros de forma mais adequada
        
        Args:
            factors_df: DataFrame com tickers como índice e fatores como colunas
            factor_columns: Lista de colunas a normalizar
            
        Returns:
            DataFrame com fatores normalizados entre -1 e +1 (mesma estrutura do input)
            
        Raises:
            ValueError: Se factor_columns não existem no DataFrame
            
        Valida: Requisitos 2.8, 3.6
        
        Exemplo:
            >>> df = pd.DataFrame({
            ...     'roe': [0.15, 0.20, 0.10],
            ...     'pe_ratio': [15, 20, 10]
            ... }, index=['AAPL', 'MSFT', 'GOOGL'])
            >>> normalizer = CrossSectionalNormalizer()
            >>> normalized = normalizer.normalize_factors(df, ['roe', 'pe_ratio'])
            >>> # normalized['roe'] terá valores entre -1 e +1 baseados no ranking
        """
        # Validar que as colunas existem
        missing_cols = [col for col in factor_columns if col not in factors_df.columns]
        if missing_cols:
            raise ValueError(f"Columns not found in DataFrame: {missing_cols}")
        
        # Criar cópia para não modificar o original
        normalized_df = factors_df.copy()
        
        # Normalizar cada fator usando ranking percentual
        for col in factor_columns:
            # Pular se a coluna tem todos valores nulos
            if normalized_df[col].isna().all():
                logger.warning(f"Column '{col}' has all NaN values, skipping normalization")
                continue
            
            # Contar valores não-nulos
            non_null_count = normalized_df[col].notna().sum()
            
            # Se todos os valores são iguais ou há apenas 1 valor, normalizar para zero
            if non_null_count <= 1 or normalized_df[col].nunique() == 1:
                logger.warning(
                    f"Column '{col}' has {non_null_count} non-null values or all equal values, "
                    f"setting normalized values to 0"
                )
                normalized_df[col] = 0.0
            else:
                # Aplicar ranking percentual:
                # 1. rank() retorna posição (1 a N), method='average' para empates
                # 2. Dividir por N para obter percentil (0 a 1)
                # 3. Transformar para [-1, +1]: 2 * percentil - 1
                ranks = normalized_df[col].rank(method='average', na_option='keep')
                percentile_rank = ranks / non_null_count
                normalized_df[col] = 2 * percentile_rank - 1
        
        return normalized_df
    
    def winsorize(
        self, 
        series: pd.Series, 
        lower_percentile: float = 0.01,
        upper_percentile: float = 0.99
    ) -> pd.Series:
        """
        Winsoriza outliers antes da normalização.
        
        Winsorização limita valores extremos aos percentis especificados,
        reduzindo o impacto de outliers na normalização.
        
        Args:
            series: Série de valores a winsorizar
            lower_percentile: Percentil inferior (default 0.01 = 1%)
            upper_percentile: Percentil superior (default 0.99 = 99%)
            
        Returns:
            Série winsorizada
            
        Raises:
            ValueError: Se percentis são inválidos
            
        Exemplo:
            >>> s = pd.Series([1, 2, 3, 4, 100])  # 100 é outlier
            >>> normalizer = CrossSectionalNormalizer()
            >>> winsorized = normalizer.winsorize(s, 0.01, 0.99)
            >>> # Valor 100 será limitado ao percentil 99
        """
        # Validar percentis
        if not (0 <= lower_percentile < upper_percentile <= 1):
            raise ValueError(
                f"Invalid percentiles: lower={lower_percentile}, upper={upper_percentile}. "
                f"Must satisfy 0 <= lower < upper <= 1"
            )
        
        # Criar cópia para não modificar o original
        winsorized = series.copy()
        
        # Pular se todos os valores são nulos
        if winsorized.isna().all():
            logger.warning("Series has all NaN values, skipping winsorization")
            return winsorized
        
        # Calcular limites dos percentis (ignorando NaN)
        lower_limit = winsorized.quantile(lower_percentile)
        upper_limit = winsorized.quantile(upper_percentile)
        
        # Aplicar limites
        winsorized = winsorized.clip(lower=lower_limit, upper=upper_limit)
        
        return winsorized
    
    def winsorize_series(
        self,
        series: pd.Series,
        lower_pct: float = 0.05,
        upper_pct: float = 0.95
    ) -> pd.Series:
        """
        Winsorize series at specified percentiles.
        
        This method limits extreme values to specified percentiles,
        reducing the impact of outliers on normalization.
        
        Args:
            series: Series to winsorize
            lower_pct: Lower percentile (default 5%)
            upper_pct: Upper percentile (default 95%)
        
        Returns:
            Winsorized series
            
        Raises:
            ValueError: If percentiles are invalid
            
        Validates: Requirements 3.1, 3.2, 3.3, 3.4
        
        Example:
            >>> s = pd.Series([1, 2, 3, 4, 100])  # 100 is outlier
            >>> normalizer = CrossSectionalNormalizer()
            >>> winsorized = normalizer.winsorize_series(s, 0.05, 0.95)
            >>> # Value 100 will be limited to 95th percentile
        """
        # Delegate to existing winsorize method
        return self.winsorize(series, lower_pct, upper_pct)
    
    def normalize_factors_with_winsorization(
        self,
        factors_df: pd.DataFrame,
        factor_columns: List[str],
        winsorize: bool = True,
        lower_pct: float = 0.05,
        upper_pct: float = 0.95
    ) -> pd.DataFrame:
        """
        Normalize factors with optional winsorization using percentile ranking.
        
        Steps:
        1. Apply winsorization to each factor (if enabled)
        2. Calculate cross-sectional percentile ranks and normalize to [-1, +1]
        
        Args:
            factors_df: DataFrame with factors
            factor_columns: Columns to normalize
            winsorize: Whether to apply winsorization
            lower_pct: Lower percentile for winsorization
            upper_pct: Upper percentile for winsorization
        
        Returns:
            Normalized DataFrame with values between -1 and +1
            
        Raises:
            ValueError: If factor_columns don't exist in DataFrame
            
        Validates: Requirements 3.1, 3.2
        
        Example:
            >>> df = pd.DataFrame({
            ...     'roe': [0.15, 0.20, 0.10, 2.50],  # 2.50 is outlier
            ...     'pe_ratio': [15, 20, 10, 200]  # 200 is outlier
            ... }, index=['AAPL', 'MSFT', 'GOOGL', 'OUTLIER'])
            >>> normalizer = CrossSectionalNormalizer()
            >>> normalized = normalizer.normalize_factors_with_winsorization(
            ...     df, ['roe', 'pe_ratio'], winsorize=True, lower_pct=0.05, upper_pct=0.95
            ... )
            >>> # Outliers will be limited before percentile ranking
        """
        # Validar que as colunas existem
        missing_cols = [col for col in factor_columns if col not in factors_df.columns]
        if missing_cols:
            raise ValueError(f"Columns not found in DataFrame: {missing_cols}")
        
        # Criar cópia para não modificar o original
        processed_df = factors_df.copy()
        
        # Step 1: Apply winsorization to each factor (if enabled)
        if winsorize:
            for col in factor_columns:
                # Pular se a coluna tem todos valores nulos
                if processed_df[col].isna().all():
                    logger.warning(f"Column '{col}' has all NaN values, skipping winsorization")
                    continue
                
                # Aplicar winsorização
                processed_df[col] = self.winsorize_series(
                    processed_df[col],
                    lower_pct=lower_pct,
                    upper_pct=upper_pct
                )
        
        # Step 2: Calculate cross-sectional percentile ranks
        normalized_df = processed_df.copy()
        
        for col in factor_columns:
            # Pular se a coluna tem todos valores nulos
            if normalized_df[col].isna().all():
                logger.warning(f"Column '{col}' has all NaN values, skipping normalization")
                continue
            
            # Contar valores não-nulos
            non_null_count = normalized_df[col].notna().sum()
            
            # Se todos os valores são iguais ou há apenas 1 valor, normalizar para zero
            if non_null_count <= 1 or normalized_df[col].nunique() == 1:
                logger.warning(
                    f"Column '{col}' has {non_null_count} non-null values or all equal values, "
                    f"setting normalized values to 0"
                )
                normalized_df[col] = 0.0
            else:
                # Aplicar ranking percentual:
                # 1. rank() retorna posição (1 a N), method='average' para empates
                # 2. Dividir por N para obter percentil (0 a 1)
                # 3. Transformar para [-1, +1]: 2 * percentil - 1
                ranks = normalized_df[col].rank(method='average', na_option='keep')
                percentile_rank = ranks / non_null_count
                normalized_df[col] = 2 * percentile_rank - 1
        
        return normalized_df
