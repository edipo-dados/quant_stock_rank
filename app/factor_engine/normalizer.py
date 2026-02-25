"""
Normalização cross-sectional de fatores.

Valida: Requisitos 2.8, 3.6
"""

from typing import List, Optional
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

    
    def sector_neutral_zscore(
        self,
        df: pd.DataFrame,
        feature: str,
        sector_col: str = "sector",
        min_sector_size: int = 5
    ) -> pd.Series:
        """
        Calcula z-score setorial (sector-neutral) para um fator.
        
        O z-score é calculado dentro de cada setor, comparando ativos apenas
        com seus pares setoriais. Isso elimina viés setorial e permite
        comparação mais justa entre ativos de diferentes setores.
        
        Metodologia:
        1. Agrupar ativos por setor
        2. Para cada setor com >= min_sector_size ativos:
           - Calcular média e desvio padrão do setor
           - z-score = (valor - média_setor) / desvio_setor
        3. Para setores pequenos (< min_sector_size):
           - Usar z-score do universo total como fallback
        
        Args:
            df: DataFrame com índice de tickers e colunas de fatores + setor
            feature: Nome da coluna do fator a normalizar
            sector_col: Nome da coluna de setor (default: "sector")
            min_sector_size: Tamanho mínimo do setor para z-score setorial (default: 5)
            
        Returns:
            Series com z-scores setoriais (índice = tickers)
            
        Raises:
            ValueError: Se feature ou sector_col não existem no DataFrame
            
        Example:
            >>> df = pd.DataFrame({
            ...     'roe': [0.15, 0.20, 0.10, 0.25, 0.18],
            ...     'sector': ['Tech', 'Tech', 'Finance', 'Finance', 'Finance']
            ... }, index=['AAPL', 'MSFT', 'JPM', 'BAC', 'C'])
            >>> normalizer = CrossSectionalNormalizer()
            >>> z_scores = normalizer.sector_neutral_zscore(df, 'roe', 'sector')
            >>> # AAPL e MSFT comparados apenas com Tech
            >>> # JPM, BAC, C comparados apenas com Finance
        """
        # Validar que as colunas existem
        if feature not in df.columns:
            raise ValueError(f"Feature column '{feature}' not found in DataFrame")
        if sector_col not in df.columns:
            raise ValueError(f"Sector column '{sector_col}' not found in DataFrame")
        
        # Criar série de resultado
        result = pd.Series(index=df.index, dtype=float)
        
        # Calcular z-score global como fallback
        global_mean = df[feature].mean()
        global_std = df[feature].std()
        
        if global_std == 0 or pd.isna(global_std):
            logger.warning(f"Global std is zero or NaN for {feature}, returning zeros")
            return pd.Series(0.0, index=df.index)
        
        global_zscore = (df[feature] - global_mean) / global_std
        
        # Agrupar por setor e calcular z-score setorial
        for sector, group in df.groupby(sector_col):
            sector_size = len(group)
            
            # Se setor é muito pequeno, usar z-score global
            if sector_size < min_sector_size:
                logger.debug(
                    f"Sector '{sector}' has only {sector_size} assets (< {min_sector_size}), "
                    f"using global z-score"
                )
                result.loc[group.index] = global_zscore.loc[group.index]
                continue
            
            # Calcular estatísticas do setor
            sector_mean = group[feature].mean()
            sector_std = group[feature].std()
            
            # Se desvio padrão é zero (todos valores iguais), usar zero
            if sector_std == 0 or pd.isna(sector_std):
                logger.debug(
                    f"Sector '{sector}' has zero std for {feature}, setting z-scores to 0"
                )
                result.loc[group.index] = 0.0
            else:
                # Calcular z-score setorial
                sector_zscore = (group[feature] - sector_mean) / sector_std
                result.loc[group.index] = sector_zscore
        
        return result
    
    def normalize_factors_sector_neutral(
        self,
        factors_df: pd.DataFrame,
        factor_columns: List[str],
        sector_col: str = "sector",
        min_sector_size: int = 5,
        winsorize: bool = True,
        lower_pct: float = 0.05,
        upper_pct: float = 0.95
    ) -> pd.DataFrame:
        """
        Normaliza fatores usando z-score setorial (sector-neutral).
        
        Esta é a versão acadêmica da normalização que elimina viés setorial.
        Cada ativo é comparado apenas com seus pares do mesmo setor.
        
        Steps:
        1. Aplicar winsorização (opcional)
        2. Calcular z-score setorial para cada fator
        3. Retornar DataFrame normalizado
        
        Args:
            factors_df: DataFrame com fatores e coluna de setor
            factor_columns: Lista de colunas de fatores a normalizar
            sector_col: Nome da coluna de setor (default: "sector")
            min_sector_size: Tamanho mínimo do setor (default: 5)
            winsorize: Se True, aplica winsorização antes (default: True)
            lower_pct: Percentil inferior para winsorização (default: 0.05)
            upper_pct: Percentil superior para winsorização (default: 0.95)
            
        Returns:
            DataFrame com fatores normalizados (z-scores setoriais)
            
        Raises:
            ValueError: Se colunas não existem no DataFrame
            
        Example:
            >>> df = pd.DataFrame({
            ...     'roe': [0.15, 0.20, 0.10, 0.25, 0.18],
            ...     'pe_ratio': [15, 20, 10, 12, 14],
            ...     'sector': ['Tech', 'Tech', 'Finance', 'Finance', 'Finance']
            ... }, index=['AAPL', 'MSFT', 'JPM', 'BAC', 'C'])
            >>> normalizer = CrossSectionalNormalizer()
            >>> normalized = normalizer.normalize_factors_sector_neutral(
            ...     df, ['roe', 'pe_ratio'], sector_col='sector'
            ... )
        """
        # Validar que as colunas existem
        missing_cols = [col for col in factor_columns if col not in factors_df.columns]
        if missing_cols:
            raise ValueError(f"Columns not found in DataFrame: {missing_cols}")
        
        if sector_col not in factors_df.columns:
            raise ValueError(f"Sector column '{sector_col}' not found in DataFrame")
        
        # Criar cópia para não modificar o original
        processed_df = factors_df.copy()
        
        # Step 1: Aplicar winsorização (se habilitado)
        if winsorize:
            for col in factor_columns:
                if processed_df[col].isna().all():
                    logger.warning(f"Column '{col}' has all NaN values, skipping winsorization")
                    continue
                
                processed_df[col] = self.winsorize_series(
                    processed_df[col],
                    lower_pct=lower_pct,
                    upper_pct=upper_pct
                )
        
        # Step 2: Calcular z-score setorial para cada fator
        normalized_df = processed_df.copy()
        
        for col in factor_columns:
            if normalized_df[col].isna().all():
                logger.warning(f"Column '{col}' has all NaN values, skipping normalization")
                continue
            
            try:
                normalized_df[col] = self.sector_neutral_zscore(
                    normalized_df,
                    feature=col,
                    sector_col=sector_col,
                    min_sector_size=min_sector_size
                )
            except Exception as e:
                logger.error(f"Error normalizing {col} with sector-neutral z-score: {e}")
                # Fallback para z-score global
                mean = normalized_df[col].mean()
                std = normalized_df[col].std()
                if std > 0:
                    normalized_df[col] = (normalized_df[col] - mean) / std
                else:
                    normalized_df[col] = 0.0
        
        return normalized_df
