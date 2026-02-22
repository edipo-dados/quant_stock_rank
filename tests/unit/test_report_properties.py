"""
Testes de propriedade para o gerador de relatórios.

Valida: Requisitos 7.1, 7.2, 7.3, 7.4
"""

import pytest
from hypothesis import given, strategies as st, settings
from app.report.report_generator import ReportGenerator
from app.scoring.scoring_engine import ScoreResult
from app.scoring.ranker import RankingEntry


# Estratégia para gerar fatores normalizados (z-scores típicos entre -3 e 3)
normalized_factor = st.floats(min_value=-3.0, max_value=3.0, allow_nan=False, allow_infinity=False)

# Estratégia para gerar tickers válidos
ticker_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu',), max_codepoint=90),  # A-Z
    min_size=3,
    max_size=6
).map(lambda s: s + st.integers(min_value=1, max_value=4).example().__str__())


@st.composite
def all_factors_dict(draw):
    """Gera dicionário com todos os fatores (momentum + fundamentalistas)."""
    return {
        # Momentum
        'return_6m': draw(normalized_factor),
        'return_12m': draw(normalized_factor),
        'rsi_14': draw(normalized_factor),
        'volatility_90d': draw(normalized_factor),
        'recent_drawdown': draw(normalized_factor),
        # Fundamentalistas
        'roe': draw(normalized_factor),
        'net_margin': draw(normalized_factor),
        'revenue_growth_3y': draw(normalized_factor),
        'debt_to_ebitda': draw(normalized_factor),
        'pe_ratio': draw(normalized_factor),
        'ev_ebitda': draw(normalized_factor),
        'pb_ratio': draw(normalized_factor)
    }


@st.composite
def score_result_strategy(draw):
    """Gera um ScoreResult válido."""
    ticker = draw(st.text(min_size=3, max_size=6, alphabet=st.characters(
        whitelist_categories=('Lu', 'Nd')
    )))
    
    # Gerar scores entre -3 e 3 (típico para z-scores normalizados)
    momentum_score = draw(st.floats(min_value=-3.0, max_value=3.0))
    quality_score = draw(st.floats(min_value=-3.0, max_value=3.0))
    value_score = draw(st.floats(min_value=-3.0, max_value=3.0))
    
    # Score final é combinação dos três
    final_score = (momentum_score + quality_score + value_score) / 3
    
    # Confidence entre 0 e 1
    confidence = draw(st.floats(min_value=0.0, max_value=1.0))
    
    # Fatores brutos
    raw_factors = draw(all_factors_dict())
    
    return ScoreResult(
        ticker=ticker,
        final_score=final_score,
        momentum_score=momentum_score,
        quality_score=quality_score,
        value_score=value_score,
        confidence=confidence,
        raw_factors=raw_factors
    )


@st.composite
def ranking_entry_strategy(draw, ticker=None, score=None):
    """Gera um RankingEntry válido."""
    if ticker is None:
        ticker = draw(st.text(min_size=3, max_size=6, alphabet=st.characters(
            whitelist_categories=('Lu', 'Nd')
        )))
    
    if score is None:
        score = draw(st.floats(min_value=-3.0, max_value=3.0))
    
    rank = draw(st.integers(min_value=1, max_value=1000))
    confidence = draw(st.floats(min_value=0.0, max_value=1.0))
    momentum_score = draw(st.floats(min_value=-3.0, max_value=3.0))
    quality_score = draw(st.floats(min_value=-3.0, max_value=3.0))
    value_score = draw(st.floats(min_value=-3.0, max_value=3.0))
    
    return RankingEntry(
        ticker=ticker,
        score=score,
        rank=rank,
        confidence=confidence,
        momentum_score=momentum_score,
        quality_score=quality_score,
        value_score=value_score
    )


class TestReportGeneratorProperties:
    """
    Testes de propriedade para o ReportGenerator.
    
    Feature: quant-stock-ranker
    """
    
    @given(
        score_result=score_result_strategy(),
        ranking_entry=ranking_entry_strategy()
    )
    @settings(max_examples=20, deadline=None)
    def test_property_13_explanation_completeness(
        self,
        score_result,
        ranking_entry
    ):
        """
        Propriedade 13: Completude de Explicações Automáticas
        
        Para qualquer ativo com score calculado, a explicação gerada deve conter:
        1. O valor numérico do score final
        2. Menção aos fatores positivos mais fortes
        3. Menção aos fatores negativos mais fracos
        4. A posição no ranking
        
        Valida: Requisitos 7.1, 7.2, 7.3, 7.4
        
        Feature: quant-stock-ranker, Property 13: Completude de Explicações Automáticas
        """
        # Garantir que ticker e score são consistentes
        ticker = score_result.ticker
        ranking_entry = RankingEntry(
            ticker=ticker,
            score=score_result.final_score,
            rank=ranking_entry.rank,
            confidence=score_result.confidence,
            momentum_score=score_result.momentum_score,
            quality_score=score_result.quality_score,
            value_score=score_result.value_score
        )
        
        # Gerar explicação
        generator = ReportGenerator()
        explanation = generator.generate_asset_explanation(
            ticker=ticker,
            score_result=score_result,
            ranking_entry=ranking_entry
        )
        
        # Verificar que a explicação não está vazia
        assert explanation, "Explanation should not be empty"
        assert len(explanation) > 0, "Explanation should have content"
        
        # 1. Verificar que contém o valor numérico do score final
        # O score deve aparecer formatado com 2 casas decimais
        score_str = f"{score_result.final_score:.2f}"
        assert score_str in explanation, (
            f"Explanation should contain final score {score_str}"
        )
        
        # 2. Verificar que contém menção aos fatores positivos
        assert "Pontos Fortes:" in explanation, (
            "Explanation should have 'Pontos Fortes:' section"
        )
        
        # Verificar que há pelo menos uma linha após "Pontos Fortes:"
        fortes_section = explanation.split("Pontos Fortes:")[1].split("Pontos de Atenção:")[0]
        assert fortes_section.strip(), "Pontos Fortes section should not be empty"
        assert "-" in fortes_section, "Pontos Fortes should have bullet points"
        
        # 3. Verificar que contém menção aos fatores negativos
        assert "Pontos de Atenção:" in explanation, (
            "Explanation should have 'Pontos de Atenção:' section"
        )
        
        # Verificar que há pelo menos uma linha após "Pontos de Atenção:"
        atencao_section = explanation.split("Pontos de Atenção:")[1].split("Conclusão:")[0]
        assert atencao_section.strip(), "Pontos de Atenção section should not be empty"
        assert "-" in atencao_section, "Pontos de Atenção should have bullet points"
        
        # 4. Verificar que contém a posição no ranking
        # A posição deve aparecer como "Xª posição"
        assert "posição no ranking" in explanation, (
            "Explanation should mention ranking position"
        )
        
        # Verificar que o ticker aparece na explicação
        assert ticker in explanation, (
            f"Explanation should mention ticker {ticker}"
        )
        
        # Verificar que há uma conclusão
        assert "Conclusão:" in explanation, (
            "Explanation should have a 'Conclusão:' section"
        )
    
    @given(all_factors=all_factors_dict())
    @settings(max_examples=20, deadline=None)
    def test_identify_top_factors_returns_correct_count(self, all_factors):
        """
        Testa que _identify_top_factors retorna o número correto de fatores.
        
        Valida: Requisitos 7.2
        """
        generator = ReportGenerator()
        
        # Pedir top 3
        top_factors = generator._identify_top_factors(all_factors, n=3)
        
        # Deve retornar exatamente 3 fatores
        assert len(top_factors) == 3, "Should return exactly 3 top factors"
        
        # Cada item deve ser uma tupla (nome, valor)
        for item in top_factors:
            assert isinstance(item, tuple), "Each item should be a tuple"
            assert len(item) == 2, "Each tuple should have 2 elements"
            assert isinstance(item[0], str), "First element should be factor name"
            assert isinstance(item[1], (int, float)), "Second element should be numeric"
    
    @given(all_factors=all_factors_dict())
    @settings(max_examples=20, deadline=None)
    def test_identify_bottom_factors_returns_correct_count(self, all_factors):
        """
        Testa que _identify_bottom_factors retorna o número correto de fatores.
        
        Valida: Requisitos 7.3
        """
        generator = ReportGenerator()
        
        # Pedir bottom 3
        bottom_factors = generator._identify_bottom_factors(all_factors, n=3)
        
        # Deve retornar exatamente 3 fatores
        assert len(bottom_factors) == 3, "Should return exactly 3 bottom factors"
        
        # Cada item deve ser uma tupla (nome, valor)
        for item in bottom_factors:
            assert isinstance(item, tuple), "Each item should be a tuple"
            assert len(item) == 2, "Each tuple should have 2 elements"
            assert isinstance(item[0], str), "First element should be factor name"
            assert isinstance(item[1], (int, float)), "Second element should be numeric"
    
    @given(
        factor_name=st.sampled_from([
            'return_6m', 'return_12m', 'rsi_14', 'volatility_90d', 'recent_drawdown',
            'roe', 'net_margin', 'revenue_growth_3y', 'debt_to_ebitda',
            'pe_ratio', 'ev_ebitda', 'pb_ratio'
        ]),
        value=normalized_factor,
        is_positive=st.booleans()
    )
    @settings(max_examples=20, deadline=None)
    def test_format_factor_description_returns_string(
        self,
        factor_name,
        value,
        is_positive
    ):
        """
        Testa que _format_factor_description sempre retorna uma string não-vazia.
        
        Valida: Requisitos 7.2, 7.3, 7.5
        """
        generator = ReportGenerator()
        
        description = generator._format_factor_description(
            factor_name=factor_name,
            value=value,
            is_positive=is_positive
        )
        
        # Deve retornar uma string não-vazia
        assert isinstance(description, str), "Description should be a string"
        assert len(description) > 0, "Description should not be empty"
        
        # Deve conter o nome legível do fator
        readable_name = generator.FACTOR_DESCRIPTIONS.get(factor_name, factor_name)
        assert readable_name in description, (
            f"Description should contain readable name '{readable_name}'"
        )
    
    @given(score_result=score_result_strategy())
    @settings(max_examples=20, deadline=None)
    def test_generate_conclusion_returns_string(self, score_result):
        """
        Testa que _generate_conclusion sempre retorna uma string não-vazia.
        
        Valida: Requisitos 7.1, 7.5
        """
        generator = ReportGenerator()
        
        conclusion = generator._generate_conclusion(score_result)
        
        # Deve retornar uma string não-vazia
        assert isinstance(conclusion, str), "Conclusion should be a string"
        assert len(conclusion) > 0, "Conclusion should not be empty"
        
        # Deve começar com "Conclusão:"
        assert conclusion.startswith("Conclusão:"), (
            "Conclusion should start with 'Conclusão:'"
        )
        
        # Deve mencionar pelo menos uma categoria
        categories = ['momentum', 'qualidade', 'valor']
        assert any(cat in conclusion.lower() for cat in categories), (
            "Conclusion should mention at least one category"
        )
    
    @given(
        ticker=st.text(min_size=3, max_size=6, alphabet=st.characters(
            whitelist_categories=('Lu', 'Nd')
        )),
        score=st.floats(min_value=-3.0, max_value=3.0),
        rank=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=20, deadline=None)
    def test_generate_header_contains_required_elements(self, ticker, score, rank):
        """
        Testa que _generate_header contém ticker, score e posição.
        
        Valida: Requisitos 7.1, 7.4
        """
        generator = ReportGenerator()
        
        # Criar objetos mínimos
        score_result = ScoreResult(
            ticker=ticker,
            final_score=score,
            momentum_score=0.0,
            quality_score=0.0,
            value_score=0.0,
            confidence=0.5,
            raw_factors={}
        )
        
        ranking_entry = RankingEntry(
            ticker=ticker,
            score=score,
            rank=rank,
            confidence=0.5,
            momentum_score=0.0,
            quality_score=0.0,
            value_score=0.0
        )
        
        header = generator._generate_header(ticker, score_result, ranking_entry)
        
        # Deve conter o ticker
        assert ticker in header, f"Header should contain ticker {ticker}"
        
        # Deve conter o score formatado
        score_str = f"{score:.2f}"
        assert score_str in header, f"Header should contain score {score_str}"
        
        # Deve conter menção à posição
        assert "posição no ranking" in header, "Header should mention ranking position"
    
    def test_inverted_factors_are_correctly_identified(self):
        """
        Testa que fatores invertidos são corretamente identificados.
        
        Fatores invertidos (menor é melhor):
        - volatility_90d, recent_drawdown
        - debt_to_ebitda
        - pe_ratio, ev_ebitda, pb_ratio
        """
        generator = ReportGenerator()
        
        expected_inverted = {
            'volatility_90d',
            'recent_drawdown',
            'debt_to_ebitda',
            'pe_ratio',
            'ev_ebitda',
            'pb_ratio'
        }
        
        assert generator.INVERTED_FACTORS == expected_inverted, (
            "INVERTED_FACTORS should match expected set"
        )
    
    def test_all_factors_have_descriptions(self):
        """
        Testa que todos os fatores têm descrições legíveis.
        """
        generator = ReportGenerator()
        
        expected_factors = {
            'return_6m', 'return_12m', 'rsi_14', 'volatility_90d', 'recent_drawdown',
            'roe', 'net_margin', 'revenue_growth_3y', 'debt_to_ebitda',
            'pe_ratio', 'ev_ebitda', 'pb_ratio'
        }
        
        for factor in expected_factors:
            assert factor in generator.FACTOR_DESCRIPTIONS, (
                f"Factor {factor} should have a description"
            )
            assert len(generator.FACTOR_DESCRIPTIONS[factor]) > 0, (
                f"Description for {factor} should not be empty"
            )
