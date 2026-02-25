"""
Suavização temporal de scores para reduzir turnover.

Implementa suavização exponencial:
final_score_smoothed = alpha * score_current + (1 - alpha) * score_previous

Onde alpha = 0.7 (70% peso no score atual, 30% no anterior)
"""

from typing import Dict, Optional
from datetime import date, timedelta
import logging

from sqlalchemy.orm import Session
from app.models.schemas import ScoreDaily

logger = logging.getLogger(__name__)


class TemporalSmoothing:
    """
    Aplica suavização temporal aos scores para reduzir turnover.
    
    A suavização exponencial combina o score atual com o score anterior,
    reduzindo mudanças bruscas no ranking e consequentemente o turnover
    do portfólio.
    """
    
    def __init__(self, alpha: float = 0.7):
        """
        Inicializa suavização temporal.
        
        Args:
            alpha: Peso do score atual (0-1). Default 0.7 (70% atual, 30% anterior)
        """
        if not 0 <= alpha <= 1:
            raise ValueError(f"Alpha must be between 0 and 1, got {alpha}")
        
        self.alpha = alpha
        logger.info(f"TemporalSmoothing initialized with alpha={alpha}")
    
    def get_previous_score(
        self,
        db: Session,
        ticker: str,
        current_date: date,
        lookback_days: int = 30
    ) -> Optional[float]:
        """
        Obtém score anterior do ativo.
        
        Busca o score mais recente dentro do período de lookback.
        
        Args:
            db: Sessão do banco de dados
            ticker: Ticker do ativo
            current_date: Data atual
            lookback_days: Número de dias para buscar score anterior
            
        Returns:
            Score anterior (final_score_smoothed se disponível, senão final_score)
            ou None se não encontrado
        """
        # Data mínima para busca
        min_date = current_date - timedelta(days=lookback_days)
        
        # Buscar score mais recente (excluindo data atual)
        previous_score = db.query(ScoreDaily).filter(
            ScoreDaily.ticker == ticker,
            ScoreDaily.date < current_date,
            ScoreDaily.date >= min_date,
            ScoreDaily.passed_eligibility == True
        ).order_by(ScoreDaily.date.desc()).first()
        
        if previous_score is None:
            return None
        
        # Preferir score suavizado se disponível
        if previous_score.final_score_smoothed is not None:
            return previous_score.final_score_smoothed
        else:
            return previous_score.final_score
    
    def smooth_score(
        self,
        current_score: float,
        previous_score: Optional[float]
    ) -> float:
        """
        Aplica suavização exponencial ao score.
        
        Formula: smoothed = alpha * current + (1 - alpha) * previous
        
        Se não há score anterior, retorna o score atual.
        
        Args:
            current_score: Score atual
            previous_score: Score anterior (ou None)
            
        Returns:
            Score suavizado
        """
        if previous_score is None:
            # Sem histórico, usar score atual
            return current_score
        
        # Suavização exponencial
        smoothed = self.alpha * current_score + (1 - self.alpha) * previous_score
        
        return smoothed
    
    def smooth_scores_batch(
        self,
        db: Session,
        scores: Dict[str, float],
        current_date: date,
        lookback_days: int = 30
    ) -> Dict[str, float]:
        """
        Aplica suavização a um batch de scores.
        
        Args:
            db: Sessão do banco de dados
            scores: Dicionário {ticker: current_score}
            current_date: Data atual
            lookback_days: Número de dias para buscar scores anteriores
            
        Returns:
            Dicionário {ticker: smoothed_score}
        """
        smoothed_scores = {}
        
        for ticker, current_score in scores.items():
            # Obter score anterior
            previous_score = self.get_previous_score(
                db,
                ticker,
                current_date,
                lookback_days
            )
            
            # Aplicar suavização
            smoothed = self.smooth_score(current_score, previous_score)
            smoothed_scores[ticker] = smoothed
            
            if previous_score is not None:
                logger.debug(
                    f"{ticker}: current={current_score:.3f}, "
                    f"previous={previous_score:.3f}, "
                    f"smoothed={smoothed:.3f}"
                )
        
        return smoothed_scores
    
    def update_smoothed_scores(
        self,
        db: Session,
        current_date: date,
        lookback_days: int = 30
    ) -> int:
        """
        Atualiza scores suavizados para todos os ativos de uma data.
        
        Busca todos os scores da data atual e aplica suavização.
        
        Args:
            db: Sessão do banco de dados
            current_date: Data para atualizar
            lookback_days: Número de dias para buscar scores anteriores
            
        Returns:
            Número de scores atualizados
        """
        # Buscar todos os scores da data
        scores = db.query(ScoreDaily).filter(
            ScoreDaily.date == current_date,
            ScoreDaily.passed_eligibility == True
        ).all()
        
        if not scores:
            logger.warning(f"No scores found for {current_date}")
            return 0
        
        updated_count = 0
        
        for score_obj in scores:
            # Obter score anterior
            previous_score = self.get_previous_score(
                db,
                score_obj.ticker,
                current_date,
                lookback_days
            )
            
            # Aplicar suavização
            smoothed = self.smooth_score(score_obj.final_score, previous_score)
            
            # Atualizar no banco
            score_obj.final_score_smoothed = smoothed
            updated_count += 1
        
        db.commit()
        
        logger.info(f"Updated {updated_count} smoothed scores for {current_date}")
        
        return updated_count
