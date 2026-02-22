"""
Testes de propriedade para persistência de scores.

Valida: Requisitos 4.5, 4.6
"""

import pytest
from datetime import date, timedelta
from contextlib import contextmanager
from hypothesis import given, strategies as st, assume, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.database import Base
from app.models.schemas import ScoreDaily
from app.scoring import ScoringEngine, ScoreResult, ScoreService


# Estratégias para gerar dados de teste
ticker_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu',)), 
    min_size=3, 
    max_size=5
)

score_strategy = st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False)

date_strategy = st.dates(
    min_value=date(2020, 1, 1),
    max_value=date(2025, 12, 31)
)

confidence_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

rank_strategy = st.integers(min_value=1, max_value=1000)


@st.composite
def score_result_strategy(draw):
    """Gera um ScoreResult válido."""
    ticker = draw(ticker_strategy)
    final_score = draw(score_strategy)
    momentum_score = draw(score_strategy)
    quality_score = draw(score_strategy)
    value_score = draw(score_strategy)
    confidence = draw(confidence_strategy)
    
    # Gerar fatores brutos (não são usados na persistência, mas são parte do ScoreResult)
    raw_factors = {
        'return_6m': draw(score_strategy),
        'return_12m': draw(score_strategy),
        'rsi_14': draw(score_strategy),
        'volatility_90d': draw(score_strategy),
        'recent_drawdown': draw(score_strategy),
        'roe': draw(score_strategy),
        'net_margin': draw(score_strategy),
        'revenue_growth_3y': draw(score_strategy),
        'debt_to_ebitda': draw(score_strategy),
        'pe_ratio': draw(score_strategy),
        'ev_ebitda': draw(score_strategy),
        'pb_ratio': draw(score_strategy)
    }
    
    return ScoreResult(
        ticker=ticker,
        final_score=final_score,
        momentum_score=momentum_score,
        quality_score=quality_score,
        value_score=value_score,
        confidence=confidence,
        raw_factors=raw_factors
    )


@contextmanager
def get_test_db():
    """Context manager para criar banco de dados em memória para testes."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_db():
    """Fixture para testes não-hypothesis."""
    with get_test_db() as session:
        yield session


class TestScorePersistenceProperties:
    """
    Testes de propriedade para persistência de scores.
    
    Feature: quant-stock-ranker
    """
    
    @given(
        score_result=score_result_strategy(),
        score_date=date_strategy,
        rank=st.one_of(st.none(), rank_strategy)
    )
    @settings(max_examples=20, deadline=None)
    def test_property_6_score_persistence_roundtrip(
        self, 
        score_result, 
        score_date,
        rank
    ):
        """
        Propriedade 6: Round-trip de Persistência de Scores
        
        Para qualquer score calculado com seu breakdown por categoria, quando
        armazenado no banco de dados com timestamp e posteriormente recuperado,
        todos os valores (score final, breakdown, timestamp) devem ser idênticos
        aos valores originais.
        
        Valida: Requisitos 4.5, 4.6
        
        Feature: quant-stock-ranker, Property 6: Round-trip de Persistência de Scores
        """
        with get_test_db() as test_db:
            # Criar serviço de scores
            service = ScoreService(test_db)
            
            # Salvar score
            saved_record = service.save_score(score_result, score_date, rank)
            
            # Recuperar score
            retrieved_record = service.get_score(score_result.ticker, score_date)
            
            # Verificar que o registro foi recuperado
            assert retrieved_record is not None, "Score should be retrievable after saving"
            
            # Verificar round-trip: todos os valores devem ser idênticos
            assert retrieved_record.ticker == score_result.ticker
            assert retrieved_record.date == score_date
            
            # Verificar scores com tolerância para erros de ponto flutuante
            assert abs(retrieved_record.final_score - score_result.final_score) < 1e-10, (
                f"Final score mismatch: saved {score_result.final_score}, "
                f"retrieved {retrieved_record.final_score}"
            )
            assert abs(retrieved_record.momentum_score - score_result.momentum_score) < 1e-10, (
                f"Momentum score mismatch: saved {score_result.momentum_score}, "
                f"retrieved {retrieved_record.momentum_score}"
            )
            assert abs(retrieved_record.quality_score - score_result.quality_score) < 1e-10, (
                f"Quality score mismatch: saved {score_result.quality_score}, "
                f"retrieved {retrieved_record.quality_score}"
            )
            assert abs(retrieved_record.value_score - score_result.value_score) < 1e-10, (
                f"Value score mismatch: saved {score_result.value_score}, "
                f"retrieved {retrieved_record.value_score}"
            )
            assert abs(retrieved_record.confidence - score_result.confidence) < 1e-10, (
                f"Confidence mismatch: saved {score_result.confidence}, "
                f"retrieved {retrieved_record.confidence}"
            )
            
            # Verificar rank
            if rank is not None:
                assert retrieved_record.rank == rank, (
                    f"Rank mismatch: saved {rank}, retrieved {retrieved_record.rank}"
                )
            
            # Verificar que timestamp foi criado
            assert retrieved_record.calculated_at is not None, (
                "Timestamp should be automatically created"
            )
    
    @given(
        score_results=st.lists(score_result_strategy(), min_size=1, max_size=10, unique_by=lambda x: x.ticker),
        score_date=date_strategy
    )
    @settings(max_examples=20, deadline=None)
    def test_batch_save_and_retrieve(self, score_results, score_date):
        """
        Testa que múltiplos scores podem ser salvos e recuperados corretamente.
        
        Valida: Requisitos 4.5, 4.6
        """
        with get_test_db() as test_db:
            service = ScoreService(test_db)
            
            # Salvar batch de scores
            results = service.save_batch_scores(score_results, score_date)
            
            # Verificar que todos foram salvos com sucesso
            assert len(results["success"]) == len(score_results)
            assert len(results["failed"]) == 0
            assert results["total_records"] == len(score_results)
            
            # Recuperar todos os scores da data
            all_scores = service.get_all_scores_for_date(score_date)
            
            # Verificar que todos foram recuperados
            assert len(all_scores) == len(score_results)
            
            # Verificar que cada score original pode ser encontrado
            for original in score_results:
                retrieved = service.get_score(original.ticker, score_date)
                assert retrieved is not None
                assert abs(retrieved.final_score - original.final_score) < 1e-10
    
    @given(
        score_result=score_result_strategy(),
        score_date=date_strategy,
        rank1=rank_strategy,
        rank2=rank_strategy
    )
    @settings(max_examples=20, deadline=None)
    def test_update_existing_score(self, score_result, score_date, rank1, rank2):
        """
        Testa que salvar um score existente atualiza o registro.
        
        Valida: Requisitos 4.5, 4.6
        """
        assume(rank1 != rank2)  # Garantir que ranks são diferentes
        
        with get_test_db() as test_db:
            service = ScoreService(test_db)
            
            # Salvar score inicial
            service.save_score(score_result, score_date, rank1)
            
            # Modificar score e salvar novamente
            modified_score = ScoreResult(
                ticker=score_result.ticker,
                final_score=score_result.final_score + 1.0,
                momentum_score=score_result.momentum_score,
                quality_score=score_result.quality_score,
                value_score=score_result.value_score,
                confidence=score_result.confidence,
                raw_factors=score_result.raw_factors
            )
            
            service.save_score(modified_score, score_date, rank2)
            
            # Verificar que existe apenas um registro
            all_scores = service.get_all_scores_for_date(score_date)
            ticker_scores = [s for s in all_scores if s.ticker == score_result.ticker]
            assert len(ticker_scores) == 1, "Should have only one record per ticker/date"
            
            # Verificar que o registro foi atualizado
            retrieved = ticker_scores[0]
            assert abs(retrieved.final_score - modified_score.final_score) < 1e-10
            assert retrieved.rank == rank2
    
    @given(
        score_results=st.lists(score_result_strategy(), min_size=2, max_size=20, unique_by=lambda x: x.ticker),
        score_date=date_strategy
    )
    @settings(max_examples=20, deadline=None)
    def test_scores_ordered_by_final_score(self, score_results, score_date):
        """
        Testa que get_all_scores_for_date retorna scores ordenados por score final.
        
        Valida: Requisitos 4.5, 4.6, 5.1
        """
        with get_test_db() as test_db:
            service = ScoreService(test_db)
            
            # Salvar scores
            service.save_batch_scores(score_results, score_date)
            
            # Recuperar scores ordenados
            retrieved_scores = service.get_all_scores_for_date(score_date)
            
            # Verificar ordenação (maior primeiro)
            for i in range(len(retrieved_scores) - 1):
                assert retrieved_scores[i].final_score >= retrieved_scores[i + 1].final_score, (
                    f"Scores should be ordered descending: "
                    f"{retrieved_scores[i].final_score} >= {retrieved_scores[i + 1].final_score}"
                )
    
    @given(
        score_results=st.lists(score_result_strategy(), min_size=5, max_size=20, unique_by=lambda x: x.ticker),
        score_date=date_strategy,
        n=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=20, deadline=None)
    def test_get_top_n_scores(self, score_results, score_date, n):
        """
        Testa que get_top_n_scores retorna exatamente n scores (ou menos se não houver n disponíveis).
        
        Valida: Requisitos 5.1, 6.6
        """
        with get_test_db() as test_db:
            service = ScoreService(test_db)
            
            # Salvar scores
            service.save_batch_scores(score_results, score_date)
            
            # Recuperar top n
            top_scores = service.get_top_n_scores(score_date, n)
            
            # Verificar quantidade
            expected_count = min(n, len(score_results))
            assert len(top_scores) == expected_count
            
            # Verificar que estão ordenados
            for i in range(len(top_scores) - 1):
                assert top_scores[i].final_score >= top_scores[i + 1].final_score
    
    @given(
        score_results=st.lists(score_result_strategy(), min_size=3, max_size=10, unique_by=lambda x: x.ticker),
        score_date=date_strategy
    )
    @settings(max_examples=20, deadline=None)
    def test_update_ranks(self, score_results, score_date):
        """
        Testa que update_ranks atribui ranks sequenciais corretos.
        
        Valida: Requisitos 5.1, 5.2
        """
        with get_test_db() as test_db:
            service = ScoreService(test_db)
            
            # Salvar scores sem ranks
            service.save_batch_scores(score_results, score_date)
            
            # Atualizar ranks
            count = service.update_ranks(score_date)
            
            # Verificar que todos foram atualizados
            assert count == len(score_results)
            
            # Recuperar scores
            scores = service.get_all_scores_for_date(score_date)
            
            # Verificar que ranks são sequenciais de 1 a N
            ranks = [s.rank for s in scores]
            expected_ranks = list(range(1, len(scores) + 1))
            assert sorted(ranks) == expected_ranks, "Ranks should be sequential from 1 to N"
            
            # Verificar que ranks correspondem à ordenação por score
            for i, score in enumerate(scores, start=1):
                assert score.rank == i, f"Rank should match position in ordered list"
    
    def test_get_latest_date(self, test_db):
        """
        Testa que get_latest_date retorna a data mais recente.
        
        Valida: Requisitos 4.5, 4.6
        """
        service = ScoreService(test_db)
        
        # Inicialmente não deve haver data
        assert service.get_latest_date() is None
        
        # Salvar scores em diferentes datas
        dates = [date(2024, 1, 1), date(2024, 1, 15), date(2024, 1, 10)]
        
        for d in dates:
            score = ScoreResult(
                ticker="TEST",
                final_score=1.0,
                momentum_score=0.5,
                quality_score=0.3,
                value_score=0.2,
                confidence=0.5,
                raw_factors={}
            )
            service.save_score(score, d)
        
        # Verificar que retorna a data mais recente
        latest = service.get_latest_date()
        assert latest == date(2024, 1, 15)
