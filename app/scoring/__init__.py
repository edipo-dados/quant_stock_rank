"""
Módulo de scoring - combina fatores em scores finais.

Valida: Requisitos 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 5.1, 5.2, 5.3, 5.4, 5.5
"""

from app.scoring.scoring_engine import ScoringEngine, ScoreResult
from app.scoring.score_service import ScoreService
from app.scoring.ranker import Ranker, RankingEntry

__all__ = ['ScoringEngine', 'ScoreResult', 'ScoreService', 'Ranker', 'RankingEntry']
