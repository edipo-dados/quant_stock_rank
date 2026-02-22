"""
Testes de propriedade para o gerador de rankings.

Valida: Requisitos 5.1, 5.2, 5.3, 5.4, 5.5
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import date
from app.scoring import Ranker, RankingEntry, ScoreResult


# Estratégia para gerar scores normalizados
score_value = st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False)

# Estratégia para gerar confidence entre 0 e 1
confidence_value = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


@st.composite
def score_result(draw, ticker=None):
    """Gera um ScoreResult válido."""
    if ticker is None:
        ticker = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))))
    
    final_score = draw(score_value)
    momentum_score = draw(score_value)
    quality_score = draw(score_value)
    value_score = draw(score_value)
    confidence = draw(confidence_value)
    
    return ScoreResult(
        ticker=ticker,
        final_score=final_score,
        momentum_score=momentum_score,
        quality_score=quality_score,
        value_score=value_score,
        confidence=confidence,
        raw_factors={}
    )


@st.composite
def score_results_list(draw, min_size=1, max_size=50):
    """Gera uma lista de ScoreResults com tickers únicos."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    
    # Gerar tickers únicos
    tickers = []
    for i in range(size):
        tickers.append(f"TICK{i:04d}")
    
    # Gerar ScoreResults
    results = []
    for ticker in tickers:
        result = draw(score_result(ticker=ticker))
        results.append(result)
    
    return results


class TestRankingProperties:
    """
    Testes de propriedade para o Ranker.
    
    Feature: quant-stock-ranker
    """
    
    @given(scores=score_results_list(min_size=2, max_size=50))
    @settings(max_examples=20, deadline=None)
    def test_property_7_ranking_ordering(self, scores):
        """
        Propriedade 7: Ordenação de Ranking
        
        Para qualquer conjunto de ativos com scores calculados, quando um ranking
        é gerado, os ativos devem estar ordenados em ordem decrescente de score,
        tal que para qualquer posição i no ranking, score[i] >= score[i+1].
        
        Valida: Requisitos 5.1
        
        Feature: quant-stock-ranker, Property 7: Ordenação de Ranking
        """
        ranker = Ranker()
        ranking_date = date(2024, 1, 15)
        
        # Gerar ranking
        ranking = ranker.generate_ranking(scores, ranking_date)
        
        # Verificar que ranking não está vazio
        assert len(ranking) == len(scores), "Ranking deve conter todos os ativos"
        
        # Verificar ordenação: score[i] >= score[i+1] para todo i
        for i in range(len(ranking) - 1):
            current_score = ranking[i].score
            next_score = ranking[i + 1].score
            
            assert current_score >= next_score, (
                f"Ranking não está ordenado: posição {i} tem score {current_score}, "
                f"mas posição {i+1} tem score {next_score}"
            )
    
    @given(scores=score_results_list(min_size=1, max_size=50))
    @settings(max_examples=20, deadline=None)
    def test_property_8_sequential_positions(self, scores):
        """
        Propriedade 8: Sequencialidade de Posições no Ranking
        
        Para qualquer ranking gerado com N ativos, as posições devem ser
        sequenciais de 1 a N, sem gaps ou duplicatas.
        
        Valida: Requisitos 5.2
        
        Feature: quant-stock-ranker, Property 8: Sequencialidade de Posições no Ranking
        """
        ranker = Ranker()
        ranking_date = date(2024, 1, 15)
        
        # Gerar ranking
        ranking = ranker.generate_ranking(scores, ranking_date)
        
        n = len(ranking)
        
        # Extrair todas as posições
        positions = [entry.rank for entry in ranking]
        
        # Verificar que posições são sequenciais de 1 a N
        expected_positions = list(range(1, n + 1))
        
        assert sorted(positions) == expected_positions, (
            f"Posições não são sequenciais: esperado {expected_positions}, "
            f"obtido {sorted(positions)}"
        )
        
        # Verificar que não há duplicatas
        assert len(positions) == len(set(positions)), (
            "Existem posições duplicadas no ranking"
        )
        
        # Verificar que primeira posição é 1
        assert ranking[0].rank == 1, "Primeira posição deve ser 1"
        
        # Verificar que última posição é N
        assert ranking[-1].rank == n, f"Última posição deve ser {n}"
    
    @given(scores=score_results_list(min_size=1, max_size=50))
    @settings(max_examples=20, deadline=None)
    def test_property_9_data_completeness(self, scores):
        """
        Propriedade 9: Completude de Dados no Ranking
        
        Para qualquer ativo incluído no ranking, todos os campos obrigatórios
        (ticker, score final, score de confiança, posição) devem estar presentes
        e não-nulos.
        
        Valida: Requisitos 5.3, 5.4, 5.5
        
        Feature: quant-stock-ranker, Property 9: Completude de Dados no Ranking
        """
        ranker = Ranker()
        ranking_date = date(2024, 1, 15)
        
        # Gerar ranking
        ranking = ranker.generate_ranking(scores, ranking_date)
        
        # Verificar completude de dados para cada entrada
        for entry in ranking:
            # Verificar que ticker está presente e não é vazio
            assert entry.ticker is not None, "Ticker não pode ser None"
            assert len(entry.ticker) > 0, "Ticker não pode ser vazio"
            
            # Verificar que score está presente e é um número válido
            assert entry.score is not None, "Score não pode ser None"
            assert isinstance(entry.score, (int, float)), "Score deve ser numérico"
            assert not (entry.score != entry.score), "Score não pode ser NaN"  # NaN check
            
            # Verificar que confidence está presente e é válido
            assert entry.confidence is not None, "Confidence não pode ser None"
            assert isinstance(entry.confidence, (int, float)), "Confidence deve ser numérico"
            assert 0.0 <= entry.confidence <= 1.0, (
                f"Confidence deve estar entre 0 e 1, obtido {entry.confidence}"
            )
            
            # Verificar que rank está presente e é válido
            assert entry.rank is not None, "Rank não pode ser None"
            assert isinstance(entry.rank, int), "Rank deve ser inteiro"
            assert entry.rank >= 1, f"Rank deve ser >= 1, obtido {entry.rank}"
            
            # Verificar que scores de breakdown estão presentes
            assert entry.momentum_score is not None, "Momentum score não pode ser None"
            assert entry.quality_score is not None, "Quality score não pode ser None"
            assert entry.value_score is not None, "Value score não pode ser None"
    
    @given(
        scores=score_results_list(min_size=5, max_size=50),
        n=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=20, deadline=None)
    def test_get_top_n_returns_correct_size(self, scores, n):
        """
        Testa que get_top_n retorna o número correto de ativos.
        
        Quando existem pelo menos n ativos, deve retornar exatamente n.
        Quando existem menos de n ativos, deve retornar todos.
        
        Valida: Requisitos 5.1, 5.2
        """
        ranker = Ranker()
        ranking_date = date(2024, 1, 15)
        
        # Gerar ranking
        ranking = ranker.generate_ranking(scores, ranking_date)
        
        # Obter top N
        top_n = ranker.get_top_n(ranking, n)
        
        # Verificar tamanho correto
        expected_size = min(n, len(ranking))
        assert len(top_n) == expected_size, (
            f"get_top_n({n}) deveria retornar {expected_size} ativos, "
            f"mas retornou {len(top_n)}"
        )
        
        # Verificar que são os N primeiros do ranking
        for i, entry in enumerate(top_n):
            assert entry.ticker == ranking[i].ticker, (
                f"Top N não contém os primeiros ativos do ranking"
            )
            assert entry.rank == i + 1, (
                f"Posição incorreta no top N: esperado {i+1}, obtido {entry.rank}"
            )
    
    @given(scores=score_results_list(min_size=1, max_size=50))
    @settings(max_examples=20, deadline=None)
    def test_get_asset_rank_finds_all_assets(self, scores):
        """
        Testa que get_asset_rank encontra todos os ativos no ranking.
        
        Valida: Requisitos 5.1, 5.2, 5.3, 5.4, 5.5
        """
        ranker = Ranker()
        ranking_date = date(2024, 1, 15)
        
        # Gerar ranking
        ranking = ranker.generate_ranking(scores, ranking_date)
        
        # Verificar que todos os tickers podem ser encontrados
        for original_score in scores:
            ticker = original_score.ticker
            
            # Buscar no ranking
            entry = ranker.get_asset_rank(ranking, ticker)
            
            # Verificar que foi encontrado
            assert entry is not None, f"Ticker {ticker} não encontrado no ranking"
            
            # Verificar que é o ticker correto
            assert entry.ticker == ticker, (
                f"get_asset_rank retornou ticker errado: esperado {ticker}, "
                f"obtido {entry.ticker}"
            )
            
            # Verificar que o score corresponde
            assert entry.score == original_score.final_score, (
                f"Score não corresponde para {ticker}: esperado {original_score.final_score}, "
                f"obtido {entry.score}"
            )
    
    @given(scores=score_results_list(min_size=1, max_size=50))
    @settings(max_examples=20, deadline=None)
    def test_get_asset_rank_returns_none_for_missing_ticker(self, scores):
        """
        Testa que get_asset_rank retorna None para ticker não existente.
        
        Valida: Requisitos 5.1, 5.2
        """
        ranker = Ranker()
        ranking_date = date(2024, 1, 15)
        
        # Gerar ranking
        ranking = ranker.generate_ranking(scores, ranking_date)
        
        # Buscar ticker que não existe
        non_existent_ticker = "NONEXISTENT999"
        
        # Garantir que o ticker realmente não existe
        assume(non_existent_ticker not in [s.ticker for s in scores])
        
        # Buscar no ranking
        entry = ranker.get_asset_rank(ranking, non_existent_ticker)
        
        # Verificar que retorna None
        assert entry is None, (
            f"get_asset_rank deveria retornar None para ticker inexistente, "
            f"mas retornou {entry}"
        )
    
    def test_empty_scores_returns_empty_ranking(self):
        """Testa que lista vazia de scores retorna ranking vazio."""
        ranker = Ranker()
        ranking_date = date(2024, 1, 15)
        
        # Gerar ranking com lista vazia
        ranking = ranker.generate_ranking([], ranking_date)
        
        # Verificar que ranking está vazio
        assert len(ranking) == 0, "Ranking deveria estar vazio"
    
    def test_get_top_n_with_zero_returns_empty(self):
        """Testa que get_top_n com n=0 retorna lista vazia."""
        ranker = Ranker()
        
        # Criar ranking simples
        scores = [
            ScoreResult("A", 1.0, 0.5, 0.5, 0.5, 0.5, {}),
            ScoreResult("B", 0.5, 0.3, 0.3, 0.3, 0.5, {})
        ]
        ranking = ranker.generate_ranking(scores, date(2024, 1, 15))
        
        # Obter top 0
        top_0 = ranker.get_top_n(ranking, 0)
        
        # Verificar que está vazio
        assert len(top_0) == 0, "get_top_n(0) deveria retornar lista vazia"
    
    def test_get_top_n_with_negative_returns_empty(self):
        """Testa que get_top_n com n negativo retorna lista vazia."""
        ranker = Ranker()
        
        # Criar ranking simples
        scores = [
            ScoreResult("A", 1.0, 0.5, 0.5, 0.5, 0.5, {}),
            ScoreResult("B", 0.5, 0.3, 0.3, 0.3, 0.5, {})
        ]
        ranking = ranker.generate_ranking(scores, date(2024, 1, 15))
        
        # Obter top -1
        top_neg = ranker.get_top_n(ranking, -1)
        
        # Verificar que está vazio
        assert len(top_neg) == 0, "get_top_n(-1) deveria retornar lista vazia"
    
    @given(scores=score_results_list(min_size=2, max_size=50))
    @settings(max_examples=20, deadline=None)
    def test_ranking_preserves_all_score_components(self, scores):
        """
        Testa que o ranking preserva todos os componentes do score.
        
        Valida: Requisitos 5.3, 5.4, 5.5
        """
        ranker = Ranker()
        ranking_date = date(2024, 1, 15)
        
        # Gerar ranking
        ranking = ranker.generate_ranking(scores, ranking_date)
        
        # Criar mapa de scores originais por ticker
        original_scores = {s.ticker: s for s in scores}
        
        # Verificar que todos os componentes foram preservados
        for entry in ranking:
            original = original_scores[entry.ticker]
            
            assert entry.score == original.final_score
            assert entry.momentum_score == original.momentum_score
            assert entry.quality_score == original.quality_score
            assert entry.value_score == original.value_score
            assert entry.confidence == original.confidence
