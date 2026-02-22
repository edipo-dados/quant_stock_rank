"""
Gerador de rankings a partir de scores.

Valida: Requisitos 5.1, 5.2, 5.3, 5.4, 5.5
"""

from typing import List, Optional
from dataclasses import dataclass
from datetime import date
import logging

from app.scoring.scoring_engine import ScoreResult

logger = logging.getLogger(__name__)


@dataclass
class RankingEntry:
    """
    Entrada individual no ranking.
    
    Attributes:
        ticker: Símbolo do ativo
        score: Score final do ativo
        rank: Posição no ranking (1 = melhor)
        confidence: Score de confiança (0-1)
        momentum_score: Score de momentum
        quality_score: Score de qualidade
        value_score: Score de valor
    """
    ticker: str
    score: float
    rank: int
    confidence: float
    momentum_score: float
    quality_score: float
    value_score: float


class Ranker:
    """
    Gera rankings a partir de scores.
    
    O Ranker é responsável por ordenar ativos por score final e atribuir
    posições no ranking. Garante que o ranking seja consistente e completo.
    
    Valida: Requisitos 5.1, 5.2, 5.3, 5.4, 5.5
    """
    
    def generate_ranking(
        self, 
        scores: List[ScoreResult],
        ranking_date: date
    ) -> List[RankingEntry]:
        """
        Gera ranking ordenado por score final.
        
        O ranking é gerado ordenando todos os ativos por score final em ordem
        decrescente (maior score = melhor posição). Posições são atribuídas
        sequencialmente de 1 a N.
        
        Args:
            scores: Lista de ScoreResult para rankear
            ranking_date: Data do ranking (para logging)
            
        Returns:
            Lista de RankingEntry ordenada por score (maior primeiro)
            Cada entry contém: ticker, score, rank, confidence
            
        Valida: Requisitos 5.1, 5.2, 5.3, 5.4, 5.5
        """
        if not scores:
            logger.warning(f"No scores provided for ranking on {ranking_date}")
            return []
        
        # Ordenar scores por final_score em ordem decrescente
        sorted_scores = sorted(scores, key=lambda x: x.final_score, reverse=True)
        
        # Criar ranking entries com posições sequenciais
        ranking = []
        for rank, score_result in enumerate(sorted_scores, start=1):
            entry = RankingEntry(
                ticker=score_result.ticker,
                score=score_result.final_score,
                rank=rank,
                confidence=score_result.confidence,
                momentum_score=score_result.momentum_score,
                quality_score=score_result.quality_score,
                value_score=score_result.value_score
            )
            ranking.append(entry)
        
        logger.info(
            f"Generated ranking for {ranking_date} with {len(ranking)} assets. "
            f"Top asset: {ranking[0].ticker} (score={ranking[0].score:.3f})"
        )
        
        return ranking
    
    def get_top_n(self, ranking: List[RankingEntry], n: int) -> List[RankingEntry]:
        """
        Retorna top N ativos do ranking.
        
        Args:
            ranking: Lista de RankingEntry ordenada
            n: Número de ativos a retornar
            
        Returns:
            Lista com os top N ativos (ou todos se N > len(ranking))
            
        Valida: Requisitos 5.1, 5.2
        """
        if n <= 0:
            logger.warning(f"Invalid n={n} for get_top_n, returning empty list")
            return []
        
        top_n = ranking[:n]
        
        logger.debug(f"Returning top {len(top_n)} assets from ranking")
        
        return top_n
    
    def get_asset_rank(
        self, 
        ranking: List[RankingEntry], 
        ticker: str
    ) -> Optional[RankingEntry]:
        """
        Retorna entrada do ranking para um ticker específico.
        
        Args:
            ranking: Lista de RankingEntry ordenada
            ticker: Símbolo do ativo a buscar
            
        Returns:
            RankingEntry para o ticker, ou None se não encontrado
            
        Valida: Requisitos 5.1, 5.2, 5.3, 5.4, 5.5
        """
        for entry in ranking:
            if entry.ticker == ticker:
                logger.debug(
                    f"Found {ticker} at rank {entry.rank} with score {entry.score:.3f}"
                )
                return entry
        
        logger.warning(f"Ticker {ticker} not found in ranking")
        return None
