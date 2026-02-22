"""
Testes de propriedade para o motor de scoring.

Valida: Requisitos 4.1, 4.2, 4.3, 4.4, 9.1, 9.2
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from app.scoring import ScoringEngine, ScoreResult
from app.config import Settings


# Estratégia para gerar fatores normalizados (z-scores típicos entre -3 e 3)
normalized_factor = st.floats(min_value=-3.0, max_value=3.0, allow_nan=False, allow_infinity=False)

# Estratégia para gerar pesos válidos que somam 1.0
@st.composite
def valid_weights(draw):
    """Gera três pesos que somam 1.0."""
    # Gerar dois pesos aleatórios entre 0 e 1
    w1 = draw(st.floats(min_value=0.0, max_value=1.0))
    w2 = draw(st.floats(min_value=0.0, max_value=1.0 - w1))
    w3 = 1.0 - w1 - w2
    
    # Garantir que todos são não-negativos
    assume(w3 >= 0.0)
    
    return w1, w2, w3


@st.composite
def momentum_factors_dict(draw):
    """Gera dicionário com fatores de momentum normalizados."""
    return {
        'return_6m': draw(normalized_factor),
        'return_12m': draw(normalized_factor),
        'rsi_14': draw(normalized_factor),
        'volatility_90d': draw(normalized_factor),
        'recent_drawdown': draw(normalized_factor)
    }


@st.composite
def fundamental_factors_dict(draw):
    """Gera dicionário com fatores fundamentalistas normalizados."""
    return {
        'roe': draw(normalized_factor),
        'net_margin': draw(normalized_factor),
        'revenue_growth_3y': draw(normalized_factor),
        'debt_to_ebitda': draw(normalized_factor),
        'pe_ratio': draw(normalized_factor),
        'ev_ebitda': draw(normalized_factor),
        'pb_ratio': draw(normalized_factor)
    }


class TestScoringProperties:
    """
    Testes de propriedade para o ScoringEngine.
    
    Feature: quant-stock-ranker
    """
    
    @given(
        momentum_factors=momentum_factors_dict(),
        fundamental_factors=fundamental_factors_dict(),
        weights=valid_weights()
    )
    @settings(max_examples=20, deadline=None)
    def test_property_5_weighted_score_calculation(
        self, 
        momentum_factors, 
        fundamental_factors,
        weights
    ):
        """
        Propriedade 5: Cálculo de Score Ponderado
        
        Para qualquer conjunto de scores de momentum, qualidade e valor, e qualquer
        conjunto de pesos configurados, o score final deve ser igual à soma ponderada:
        final_score = momentum_weight * momentum_score + 
                     quality_weight * quality_score + 
                     value_weight * value_score
        
        Valida: Requisitos 4.1, 4.2, 4.3, 4.4
        
        Feature: quant-stock-ranker, Property 5: Cálculo de Score Ponderado
        """
        # Configurar pesos customizados
        momentum_weight, quality_weight, value_weight = weights
        config = Settings(
            momentum_weight=momentum_weight,
            quality_weight=quality_weight,
            value_weight=value_weight,
            database_url="postgresql://test:test@localhost/test",
            fmp_api_key="test"
        )
        
        # Criar engine com pesos customizados
        engine = ScoringEngine(config=config)
        
        # Calcular score completo
        result = engine.score_asset(
            ticker="TEST",
            fundamental_factors=fundamental_factors,
            momentum_factors=momentum_factors,
            confidence=0.5
        )
        
        # Calcular scores individuais manualmente
        momentum_score = engine.calculate_momentum_score(momentum_factors)
        quality_score = engine.calculate_quality_score(fundamental_factors)
        value_score = engine.calculate_value_score(fundamental_factors)
        
        # Calcular score final esperado manualmente
        expected_final_score = (
            momentum_weight * momentum_score +
            quality_weight * quality_score +
            value_weight * value_score
        )
        
        # Verificar que o score final calculado pelo engine é igual ao esperado
        # Usar tolerância para erros de ponto flutuante
        assert abs(result.final_score - expected_final_score) < 1e-10, (
            f"Final score mismatch: got {result.final_score}, "
            f"expected {expected_final_score}"
        )
        
        # Verificar que os scores individuais no resultado são corretos
        assert abs(result.momentum_score - momentum_score) < 1e-10
        assert abs(result.quality_score - quality_score) < 1e-10
        assert abs(result.value_score - value_score) < 1e-10
        
        # Verificar que o ticker está correto
        assert result.ticker == "TEST"
        
        # Verificar que confidence foi preservado
        assert result.confidence == 0.5
        
        # Verificar que raw_factors contém todos os fatores
        assert len(result.raw_factors) == len(momentum_factors) + len(fundamental_factors)
        for key in momentum_factors:
            assert key in result.raw_factors
        for key in fundamental_factors:
            assert key in result.raw_factors
    
    @given(momentum_factors=momentum_factors_dict())
    @settings(max_examples=20, deadline=None)
    def test_momentum_score_calculation(self, momentum_factors):
        """
        Testa que o score de momentum é calculado corretamente.
        
        Score de momentum = média dos fatores (com volatilidade e drawdown invertidos).
        
        Valida: Requisitos 4.1
        """
        engine = ScoringEngine()
        
        momentum_score = engine.calculate_momentum_score(momentum_factors)
        
        # Calcular manualmente
        expected = (
            momentum_factors['return_6m'] +
            momentum_factors['return_12m'] +
            momentum_factors['rsi_14'] +
            (-momentum_factors['volatility_90d']) +  # Invertido
            (-momentum_factors['recent_drawdown'])    # Invertido
        ) / 5
        
        assert abs(momentum_score - expected) < 1e-10
    
    @given(fundamental_factors=fundamental_factors_dict())
    @settings(max_examples=20, deadline=None)
    def test_quality_score_calculation(self, fundamental_factors):
        """
        Testa que o score de qualidade é calculado corretamente.
        
        Score de qualidade = média dos fatores (com debt_to_ebitda invertido).
        
        Valida: Requisitos 4.2
        """
        engine = ScoringEngine()
        
        quality_score = engine.calculate_quality_score(fundamental_factors)
        
        # Calcular manualmente
        expected = (
            fundamental_factors['roe'] +
            fundamental_factors['net_margin'] +
            fundamental_factors['revenue_growth_3y'] +
            (-fundamental_factors['debt_to_ebitda'])  # Invertido
        ) / 4
        
        assert abs(quality_score - expected) < 1e-10
    
    @given(fundamental_factors=fundamental_factors_dict())
    @settings(max_examples=20, deadline=None)
    def test_value_score_calculation(self, fundamental_factors):
        """
        Testa que o score de valor é calculado corretamente.
        
        Score de valor = média dos fatores (todos invertidos).
        
        Valida: Requisitos 4.3
        """
        engine = ScoringEngine()
        
        value_score = engine.calculate_value_score(fundamental_factors)
        
        # Calcular manualmente
        expected = (
            (-fundamental_factors['pe_ratio']) +    # Invertido
            (-fundamental_factors['ev_ebitda']) +   # Invertido
            (-fundamental_factors['pb_ratio'])      # Invertido
        ) / 3
        
        assert abs(value_score - expected) < 1e-10
    
    def test_missing_momentum_factors_uses_available(self):
        """Testa que fatores de momentum faltando usa apenas os disponíveis."""
        engine = ScoringEngine()
        
        incomplete_factors = {
            'return_6m': 0.6,
            'return_12m': 0.4
            # Faltando: rsi_14, volatility_90d, recent_drawdown
        }
        
        # Deve calcular média dos fatores disponíveis
        score = engine.calculate_momentum_score(incomplete_factors)
        expected = (0.6 + 0.4) / 2
        assert abs(score - expected) < 1e-10
    
    def test_missing_quality_factors_uses_available(self):
        """Testa que fatores de qualidade faltando usa apenas os disponíveis."""
        engine = ScoringEngine()
        
        incomplete_factors = {
            'roe': 0.8,
            'net_margin': 0.6
            # Faltando: revenue_growth_3y, debt_to_ebitda
        }
        
        # Deve calcular média dos fatores disponíveis
        score = engine.calculate_quality_score(incomplete_factors)
        expected = (0.8 + 0.6) / 2
        assert abs(score - expected) < 1e-10
    
    def test_missing_value_factors_uses_available(self):
        """Testa que fatores de valor faltando usa apenas os disponíveis."""
        engine = ScoringEngine()
        
        incomplete_factors = {
            'pe_ratio': 0.5
            # Faltando: ev_ebitda, pb_ratio
        }
        
        # Deve calcular média dos fatores disponíveis (pe_ratio invertido)
        score = engine.calculate_value_score(incomplete_factors)
        expected = -0.5
        assert abs(score - expected) < 1e-10
    
    def test_default_weights_sum_to_one(self):
        """Testa que os pesos padrão somam 1.0."""
        engine = ScoringEngine()
        
        total = engine.momentum_weight + engine.quality_weight + engine.value_weight
        
        assert abs(total - 1.0) < 1e-10
    
    def test_custom_weights_are_loaded(self):
        """Testa que pesos customizados são carregados corretamente."""
        config = Settings(
            momentum_weight=0.5,
            quality_weight=0.3,
            value_weight=0.2,
            database_url="postgresql://test:test@localhost/test",
            fmp_api_key="test"
        )
        
        engine = ScoringEngine(config=config)
        
        assert engine.momentum_weight == 0.5
        assert engine.quality_weight == 0.3
        assert engine.value_weight == 0.2
