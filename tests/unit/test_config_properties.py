"""
Testes de propriedade para carregamento de configuração.

Valida: Requisitos 9.1, 9.2
"""

import pytest
from hypothesis import given, strategies as st, assume
from app.config import Settings
from app.scoring import ScoringEngine


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


class TestConfigurationProperties:
    """
    Testes de propriedade para carregamento de configuração.
    
    Feature: quant-stock-ranker
    """
    
    @given(weights=valid_weights())
    def test_property_15_configuration_loading(self, weights):
        """
        Propriedade 15: Carregamento de Configuração
        
        Para qualquer arquivo de configuração válido contendo pesos de fatores,
        quando o sistema é inicializado, os pesos carregados devem ser idênticos
        aos pesos especificados no arquivo.
        
        Valida: Requisitos 9.1, 9.2
        
        Feature: quant-stock-ranker, Property 15: Carregamento de Configuração
        """
        momentum_weight, quality_weight, value_weight = weights
        
        # Criar configuração com pesos específicos
        config = Settings(
            momentum_weight=momentum_weight,
            quality_weight=quality_weight,
            value_weight=value_weight,
            database_url="postgresql://test:test@localhost/test",
            fmp_api_key="test"
        )
        
        # Verificar que os pesos foram carregados corretamente
        assert abs(config.momentum_weight - momentum_weight) < 1e-10, (
            f"Momentum weight mismatch: got {config.momentum_weight}, "
            f"expected {momentum_weight}"
        )
        assert abs(config.quality_weight - quality_weight) < 1e-10, (
            f"Quality weight mismatch: got {config.quality_weight}, "
            f"expected {quality_weight}"
        )
        assert abs(config.value_weight - value_weight) < 1e-10, (
            f"Value weight mismatch: got {config.value_weight}, "
            f"expected {value_weight}"
        )
        
        # Verificar que os pesos somam 1.0
        total = config.momentum_weight + config.quality_weight + config.value_weight
        assert abs(total - 1.0) < 1e-10, f"Weights do not sum to 1.0: {total}"
        
        # Verificar que o ScoringEngine usa os pesos da configuração
        engine = ScoringEngine(config=config)
        
        assert abs(engine.momentum_weight - momentum_weight) < 1e-10
        assert abs(engine.quality_weight - quality_weight) < 1e-10
        assert abs(engine.value_weight - value_weight) < 1e-10
    
    def test_default_weights_are_correct(self):
        """
        Testa que os pesos padrão são os especificados nos requisitos.
        
        Valida: Requisitos 9.3
        """
        config = Settings(
            database_url="postgresql://test:test@localhost/test",
            fmp_api_key="test"
        )
        
        # Pesos padrão conforme Requisito 9.3
        assert config.momentum_weight == 0.4
        assert config.quality_weight == 0.3
        assert config.value_weight == 0.3
        
        # Verificar que somam 1.0
        total = config.momentum_weight + config.quality_weight + config.value_weight
        assert abs(total - 1.0) < 1e-10
    
    def test_scoring_engine_uses_default_config_when_none_provided(self):
        """
        Testa que o ScoringEngine usa configuração padrão quando nenhuma é fornecida.
        
        Valida: Requisitos 9.3
        """
        engine = ScoringEngine()
        
        # Deve usar pesos padrão
        assert engine.momentum_weight == 0.4
        assert engine.quality_weight == 0.3
        assert engine.value_weight == 0.3
    
    @given(
        momentum_weight=st.floats(min_value=0.0, max_value=1.0),
        quality_weight=st.floats(min_value=0.0, max_value=1.0),
        value_weight=st.floats(min_value=0.0, max_value=1.0)
    )
    def test_configuration_accepts_any_positive_weights(
        self, 
        momentum_weight, 
        quality_weight, 
        value_weight
    ):
        """
        Testa que a configuração aceita quaisquer pesos positivos.
        
        Nota: O sistema emite um warning se os pesos não somam 1.0,
        mas não rejeita a configuração.
        
        Valida: Requisitos 9.1, 9.2
        """
        config = Settings(
            momentum_weight=momentum_weight,
            quality_weight=quality_weight,
            value_weight=value_weight,
            database_url="postgresql://test:test@localhost/test",
            fmp_api_key="test"
        )
        
        # Verificar que os valores foram aceitos
        assert config.momentum_weight == momentum_weight
        assert config.quality_weight == quality_weight
        assert config.value_weight == value_weight
        
        # Verificar que o ScoringEngine pode ser criado com esses pesos
        engine = ScoringEngine(config=config)
        
        assert engine.momentum_weight == momentum_weight
        assert engine.quality_weight == quality_weight
        assert engine.value_weight == value_weight
    
    def test_other_config_fields_are_loaded(self):
        """
        Testa que outros campos de configuração são carregados corretamente.
        
        Valida: Requisitos 9.4, 9.5
        """
        config = Settings(
            database_url="postgresql://custom:pass@host:5432/db",
            fmp_api_key="custom_key_123",
            api_host="127.0.0.1",
            api_port=9000,
            log_level="DEBUG"
        )
        
        assert config.database_url == "postgresql://custom:pass@host:5432/db"
        assert config.fmp_api_key == "custom_key_123"
        assert config.api_host == "127.0.0.1"
        assert config.api_port == 9000
        assert config.log_level == "DEBUG"


class TestScoringModelImprovementsConfigProperties:
    """
    Property tests for scoring model improvements configuration parameters.
    
    Feature: scoring-model-improvements
    """
    
    @given(
        minimum_volume=st.floats(min_value=0.0, max_value=10_000_000.0),
        max_roe_limit=st.floats(min_value=0.0, max_value=2.0),
        debt_ebitda_limit=st.floats(min_value=0.0, max_value=20.0),
        volatility_limit=st.floats(min_value=0.0, max_value=2.0),
        drawdown_limit=st.floats(min_value=-1.0, max_value=0.0),
        winsorize_lower_pct=st.floats(min_value=0.0, max_value=0.5),
        winsorize_upper_pct=st.floats(min_value=0.5, max_value=1.0)
    )
    def test_property_15_scoring_improvements_config_loading(
        self,
        minimum_volume,
        max_roe_limit,
        debt_ebitda_limit,
        volatility_limit,
        drawdown_limit,
        winsorize_lower_pct,
        winsorize_upper_pct
    ):
        """
        Property 15: Configuration Parameter Loading
        
        For any configuration parameter (minimum_volume, max_roe_limit, 
        debt_ebitda_limit, volatility_limit, drawdown_limit), when set 
        via environment variable, the Configuration should load that value; 
        when not set, it should use the documented default value.
        
        Validates: Requirements 6.6, 6.7
        
        Feature: scoring-model-improvements, Property 15: Configuration Parameter Loading
        """
        # Create configuration with specific parameter values
        config = Settings(
            minimum_volume=minimum_volume,
            max_roe_limit=max_roe_limit,
            debt_ebitda_limit=debt_ebitda_limit,
            volatility_limit=volatility_limit,
            drawdown_limit=drawdown_limit,
            winsorize_lower_pct=winsorize_lower_pct,
            winsorize_upper_pct=winsorize_upper_pct,
            database_url="postgresql://test:test@localhost/test",
            fmp_api_key="test"
        )
        
        # Verify that all parameters were loaded correctly
        assert config.minimum_volume == minimum_volume, (
            f"minimum_volume mismatch: got {config.minimum_volume}, "
            f"expected {minimum_volume}"
        )
        assert config.max_roe_limit == max_roe_limit, (
            f"max_roe_limit mismatch: got {config.max_roe_limit}, "
            f"expected {max_roe_limit}"
        )
        assert config.debt_ebitda_limit == debt_ebitda_limit, (
            f"debt_ebitda_limit mismatch: got {config.debt_ebitda_limit}, "
            f"expected {debt_ebitda_limit}"
        )
        assert config.volatility_limit == volatility_limit, (
            f"volatility_limit mismatch: got {config.volatility_limit}, "
            f"expected {volatility_limit}"
        )
        assert config.drawdown_limit == drawdown_limit, (
            f"drawdown_limit mismatch: got {config.drawdown_limit}, "
            f"expected {drawdown_limit}"
        )
        assert config.winsorize_lower_pct == winsorize_lower_pct, (
            f"winsorize_lower_pct mismatch: got {config.winsorize_lower_pct}, "
            f"expected {winsorize_lower_pct}"
        )
        assert config.winsorize_upper_pct == winsorize_upper_pct, (
            f"winsorize_upper_pct mismatch: got {config.winsorize_upper_pct}, "
            f"expected {winsorize_upper_pct}"
        )
    
    def test_default_scoring_improvements_parameters(self):
        """
        Test that default values for scoring improvements parameters are correct.
        
        Validates: Requirements 6.6, 6.7
        """
        config = Settings(
            database_url="postgresql://test:test@localhost/test",
            fmp_api_key="test"
        )
        
        # Verify default values as documented in design
        assert config.minimum_volume == 100000.0
        assert config.max_roe_limit == 0.50
        assert config.debt_ebitda_limit == 4.0
        assert config.volatility_limit == 0.60
        assert config.drawdown_limit == -0.50
        assert config.winsorize_lower_pct == 0.05
        assert config.winsorize_upper_pct == 0.95
