"""
Testes de propriedade para normalização cross-sectional.

Valida: Requisitos 2.8, 3.6
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import pandas as pd
import numpy as np
from app.factor_engine.normalizer import CrossSectionalNormalizer


# Estratégia para gerar DataFrames com fatores
@st.composite
def factor_dataframe(draw):
    """
    Gera DataFrame com fatores para teste.
    
    Retorna DataFrame com:
    - Índice: tickers (strings)
    - Colunas: fatores numéricos
    - Valores: floats variados
    """
    # Gerar número de ativos (mínimo 3 para ter estatísticas significativas)
    n_assets = draw(st.integers(min_value=3, max_value=20))
    
    # Gerar número de fatores
    n_factors = draw(st.integers(min_value=1, max_value=5))
    
    # Gerar tickers
    tickers = [f"TICK{i}" for i in range(n_assets)]
    
    # Gerar nomes de fatores
    factor_names = [f"factor_{i}" for i in range(n_factors)]
    
    # Gerar valores para cada fator
    # Usar floats finitos para evitar inf/nan
    data = {}
    for factor in factor_names:
        values = draw(
            st.lists(
                st.floats(
                    min_value=-1000.0,
                    max_value=1000.0,
                    allow_nan=False,
                    allow_infinity=False
                ),
                min_size=n_assets,
                max_size=n_assets
            )
        )
        data[factor] = values
    
    df = pd.DataFrame(data, index=tickers)
    
    return df, factor_names


class TestNormalizationProperties:
    """
    Testes de propriedade para normalização cross-sectional.
    
    **Propriedade 2: Normalização Cross-Sectional**
    **Valida: Requisitos 2.8, 3.6**
    """
    
    @given(factor_dataframe())
    @settings(max_examples=20, deadline=None)
    def test_property_2_cross_sectional_normalization(self, data):
        """
        **Propriedade 2: Normalização Cross-Sectional**
        
        *Para qualquer* conjunto de fatores (fundamentalistas ou momentum) 
        calculados para múltiplos ativos na mesma data, após normalização 
        via z-score cross-sectional, a média dos valores normalizados deve 
        ser aproximadamente 0 e o desvio padrão aproximadamente 1.
        
        **Valida: Requisitos 2.8, 3.6**
        
        Feature: quant-stock-ranker, Property 2: Normalização Cross-Sectional
        """
        factors_df, factor_columns = data
        
        # Assumir que temos variação nos dados (std > 0)
        # Se todos os valores são iguais, o teste não é aplicável
        for col in factor_columns:
            std = factors_df[col].std()
            assume(std > 1e-10)  # Assumir que há variação
        
        # Normalizar
        normalizer = CrossSectionalNormalizer()
        normalized_df = normalizer.normalize_factors(factors_df, factor_columns)
        
        # Verificar que o DataFrame tem a mesma estrutura
        assert normalized_df.shape == factors_df.shape
        assert list(normalized_df.index) == list(factors_df.index)
        assert list(normalized_df.columns) == list(factors_df.columns)
        
        # Para cada fator normalizado, verificar propriedades estatísticas
        for col in factor_columns:
            normalized_values = normalized_df[col].dropna()
            
            # Pular se não há valores suficientes
            if len(normalized_values) < 2:
                continue
            
            mean = normalized_values.mean()
            std = normalized_values.std()
            
            # Média deve ser aproximadamente 0 (tolerância de 1e-10)
            assert abs(mean) < 1e-10, (
                f"Mean of normalized {col} should be ~0, got {mean}"
            )
            
            # Desvio padrão deve ser aproximadamente 1 (tolerância de 1e-10)
            assert abs(std - 1.0) < 1e-10, (
                f"Std of normalized {col} should be ~1, got {std}"
            )
    
    @given(factor_dataframe())
    @settings(max_examples=20, deadline=None)
    def test_normalization_preserves_order(self, data):
        """
        Teste adicional: Normalização preserva ordem relativa.
        
        Se A > B antes da normalização, então A_norm > B_norm após.
        """
        factors_df, factor_columns = data
        
        # Assumir que temos pelo menos 2 ativos
        assume(len(factors_df) >= 2)
        
        # Assumir que temos variação nos dados
        for col in factor_columns:
            std = factors_df[col].std()
            assume(std > 1e-10)
        
        normalizer = CrossSectionalNormalizer()
        normalized_df = normalizer.normalize_factors(factors_df, factor_columns)
        
        # Para cada fator, verificar que a ordem é preservada
        for col in factor_columns:
            original_values = factors_df[col].dropna()
            normalized_values = normalized_df[col].loc[original_values.index]
            
            # Pular se não há valores suficientes
            if len(original_values) < 2:
                continue
            
            # Verificar que a ordem é preservada
            for i in range(len(original_values) - 1):
                for j in range(i + 1, len(original_values)):
                    idx_i = original_values.index[i]
                    idx_j = original_values.index[j]
                    
                    # Usar tolerância para comparações de floating point
                    diff_original = original_values.iloc[i] - original_values.iloc[j]
                    diff_normalized = normalized_values.loc[idx_i] - normalized_values.loc[idx_j]
                    
                    # Se a diferença original é significativa (não devido a precisão numérica)
                    if abs(diff_original) > 1e-10:
                        # A ordem deve ser preservada
                        assert np.sign(diff_original) == np.sign(diff_normalized), (
                            f"Order not preserved: original diff={diff_original}, "
                            f"normalized diff={diff_normalized}"
                        )


class TestWinsorization:
    """Testes para winsorização de outliers."""
    
    @given(
        st.lists(
            st.floats(
                min_value=-1000.0,
                max_value=1000.0,
                allow_nan=False,
                allow_infinity=False
            ),
            min_size=10,
            max_size=100
        )
    )
    @settings(max_examples=20, deadline=None)
    def test_winsorization_limits_extremes(self, values):
        """
        Teste: Winsorização limita valores aos percentis especificados.
        """
        series = pd.Series(values)
        
        # Assumir que há variação
        assume(series.std() > 1e-10)
        
        normalizer = CrossSectionalNormalizer()
        winsorized = normalizer.winsorize(series, lower_percentile=0.05, upper_percentile=0.95)
        
        # Calcular limites esperados
        lower_limit = series.quantile(0.05)
        upper_limit = series.quantile(0.95)
        
        # Verificar que todos os valores estão dentro dos limites
        assert winsorized.min() >= lower_limit - 1e-10
        assert winsorized.max() <= upper_limit + 1e-10
        
        # Verificar que valores dentro dos limites não foram alterados
        mask = (series >= lower_limit) & (series <= upper_limit)
        pd.testing.assert_series_equal(
            winsorized[mask],
            series[mask],
            check_exact=False,
            rtol=1e-10
        )
