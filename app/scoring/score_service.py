"""
Serviço para persistência de scores calculados.

Valida: Requisitos 4.5, 4.6
"""

import logging
from datetime import date
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.schemas import ScoreDaily
from app.scoring.scoring_engine import ScoreResult

logger = logging.getLogger(__name__)


class ScoreService:
    """
    Serviço para salvar e recuperar scores calculados.
    
    Valida: Requisitos 4.5, 4.6
    """
    
    def __init__(self, db_session: Session):
        """
        Inicializa o serviço de scores.
        
        Args:
            db_session: Sessão do banco de dados
        """
        self.db = db_session
    
    def save_score(
        self,
        score_result: ScoreResult,
        score_date: date,
        rank: Optional[int] = None
    ) -> ScoreDaily:
        """
        Salva score diário para um ativo com breakdown por categoria.
        
        Args:
            score_result: Resultado do scoring contendo score final e breakdown
            score_date: Data do score
            rank: Posição no ranking (opcional)
        
        Returns:
            Objeto ScoreDaily salvo
            
        Raises:
            Exception: Se houver erro ao salvar
            
        Valida: Requisitos 4.5, 4.6, 5.1, 5.2, 5.3, 5.5
        """
        try:
            # Verifica se registro já existe
            existing = self.db.query(ScoreDaily).filter_by(
                ticker=score_result.ticker,
                date=score_date
            ).first()
            
            # Calculate risk penalty factor from base_score and final_score
            risk_penalty_factor = None
            if score_result.base_score and score_result.base_score != 0:
                risk_penalty_factor = score_result.final_score / score_result.base_score
            
            if existing:
                # Atualiza registro existente
                existing.final_score = score_result.final_score
                existing.momentum_score = score_result.momentum_score
                existing.quality_score = score_result.quality_score
                existing.value_score = score_result.value_score
                existing.confidence = score_result.confidence
                existing.rank = rank
                
                # Update enhanced fields
                existing.base_score = score_result.base_score
                existing.risk_penalty_factor = risk_penalty_factor
                existing.passed_eligibility = score_result.passed_eligibility
                existing.exclusion_reasons = score_result.exclusion_reasons if score_result.exclusion_reasons else None
                existing.risk_penalties = score_result.risk_penalties if score_result.risk_penalties else None
                existing.distress_flag = score_result.distress_flag if hasattr(score_result, 'distress_flag') else False
                
                logger.info(
                    f"Updated score for {score_result.ticker} on {score_date}: "
                    f"final={score_result.final_score:.3f}, rank={rank}, "
                    f"passed_eligibility={score_result.passed_eligibility}"
                )
                record = existing
            else:
                # Cria novo registro
                record = ScoreDaily(
                    ticker=score_result.ticker,
                    date=score_date,
                    final_score=score_result.final_score,
                    momentum_score=score_result.momentum_score,
                    quality_score=score_result.quality_score,
                    value_score=score_result.value_score,
                    confidence=score_result.confidence,
                    rank=rank,
                    base_score=score_result.base_score,
                    risk_penalty_factor=risk_penalty_factor,
                    passed_eligibility=score_result.passed_eligibility,
                    exclusion_reasons=score_result.exclusion_reasons if score_result.exclusion_reasons else None,
                    risk_penalties=score_result.risk_penalties if score_result.risk_penalties else None,
                    distress_flag=score_result.distress_flag if hasattr(score_result, 'distress_flag') else False
                )
                self.db.add(record)
                logger.info(
                    f"Created score for {score_result.ticker} on {score_date}: "
                    f"final={score_result.final_score:.3f}, rank={rank}, "
                    f"passed_eligibility={score_result.passed_eligibility}"
                )
            
            # Commit
            self.db.commit()
            self.db.refresh(record)
            
            return record
            
        except Exception as e:
            logger.error(f"Error saving score for {score_result.ticker}: {e}")
            self.db.rollback()
            raise
    
    def save_batch_scores(
        self,
        scores: List[ScoreResult],
        score_date: date,
        ranks: Optional[Dict[str, int]] = None
    ) -> Dict[str, any]:
        """
        Salva múltiplos scores em batch.
        
        Args:
            scores: Lista de ScoreResult
            score_date: Data dos scores
            ranks: Dicionário opcional mapeando ticker -> rank
        
        Returns:
            Dict com estatísticas:
            {
                "success": [lista de tickers com sucesso],
                "failed": [lista de dicts com ticker e erro],
                "total_records": número total de registros inseridos
            }
            
        Valida: Requisitos 4.5, 4.6
        """
        results = {
            "success": [],
            "failed": [],
            "total_records": 0
        }
        
        for score_result in scores:
            try:
                rank = ranks.get(score_result.ticker) if ranks else None
                
                self.save_score(score_result, score_date, rank)
                
                results["success"].append(score_result.ticker)
                results["total_records"] += 1
                
            except Exception as e:
                ticker = score_result.ticker
                logger.error(f"Failed to save score for {ticker}: {e}")
                results["failed"].append({"ticker": ticker, "error": str(e)})
                continue
        
        logger.info(
            f"Batch score save complete: {len(results['success'])} succeeded, "
            f"{len(results['failed'])} failed"
        )
        
        return results
    
    def get_score(
        self,
        ticker: str,
        score_date: date
    ) -> Optional[ScoreDaily]:
        """
        Recupera score para um ativo em uma data específica.
        
        Args:
            ticker: Símbolo do ativo
            score_date: Data do score
        
        Returns:
            Objeto ScoreDaily ou None se não encontrado
            
        Valida: Requisitos 4.5, 4.6
        """
        return self.db.query(ScoreDaily).filter_by(
            ticker=ticker,
            date=score_date
        ).first()
    
    def get_all_scores_for_date(
        self,
        score_date: date
    ) -> List[ScoreDaily]:
        """
        Recupera scores de todos os ativos para uma data específica.
        
        Args:
            score_date: Data dos scores
        
        Returns:
            Lista de objetos ScoreDaily ordenada por score (maior primeiro)
            
        Valida: Requisitos 4.5, 4.6, 5.1
        """
        return self.db.query(ScoreDaily).filter_by(
            date=score_date
        ).order_by(ScoreDaily.final_score.desc()).all()
    
    def get_latest_score(
        self,
        ticker: str
    ) -> Optional[ScoreDaily]:
        """
        Recupera o score mais recente para um ativo.
        
        Args:
            ticker: Símbolo do ativo
        
        Returns:
            Objeto ScoreDaily mais recente ou None se não encontrado
        """
        return self.db.query(ScoreDaily).filter_by(
            ticker=ticker
        ).order_by(ScoreDaily.date.desc()).first()
    
    def get_latest_date(self) -> Optional[date]:
        """
        Recupera a data mais recente com scores disponíveis.
        
        Returns:
            Data mais recente ou None se não há scores
        """
        result = self.db.query(ScoreDaily.date).order_by(
            ScoreDaily.date.desc()
        ).first()
        
        return result[0] if result else None
    
    def get_top_n_scores(
        self,
        score_date: date,
        n: int = 10
    ) -> List[ScoreDaily]:
        """
        Recupera os top N scores para uma data específica.
        
        Args:
            score_date: Data dos scores
            n: Número de scores a retornar
        
        Returns:
            Lista dos top N objetos ScoreDaily ordenados por score
            
        Valida: Requisitos 5.1, 6.6
        """
        return self.db.query(ScoreDaily).filter_by(
            date=score_date
        ).order_by(ScoreDaily.final_score.desc()).limit(n).all()
    
    def update_ranks(
        self,
        score_date: date
    ) -> int:
        """
        Atualiza os ranks de todos os scores para uma data específica.
        
        Ordena por score final (maior primeiro) e atribui ranks sequenciais.
        
        Args:
            score_date: Data dos scores a atualizar
        
        Returns:
            Número de registros atualizados
            
        Valida: Requisitos 5.1, 5.2
        """
        try:
            # Buscar todos os scores da data ordenados por score final
            scores = self.db.query(ScoreDaily).filter_by(
                date=score_date
            ).order_by(ScoreDaily.final_score.desc()).all()
            
            # Atribuir ranks sequenciais
            for rank, score in enumerate(scores, start=1):
                score.rank = rank
            
            # Commit
            self.db.commit()
            
            logger.info(f"Updated ranks for {len(scores)} scores on {score_date}")
            
            return len(scores)
            
        except Exception as e:
            logger.error(f"Error updating ranks for {score_date}: {e}")
            self.db.rollback()
            raise
    
    def get_score_by_rank(
        self,
        score_date: date,
        rank: int
    ) -> Optional[ScoreDaily]:
        """
        Recupera score por posição no ranking.
        
        Args:
            score_date: Data do score
            rank: Posição no ranking
        
        Returns:
            Objeto ScoreDaily ou None se não encontrado
        """
        return self.db.query(ScoreDaily).filter_by(
            date=score_date,
            rank=rank
        ).first()
