"""
Gerenciamento de portfólio para backtest.
"""

from typing import Dict, List
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class Portfolio:
    """
    Representa um portfólio de ativos com pesos.
    
    Suporta diferentes métodos de ponderação:
    - Equal weight: Todos os ativos com peso igual
    - Score weighted: Pesos proporcionais aos scores
    """
    
    def __init__(self, tickers: List[str], scores: Dict[str, float] = None):
        """
        Inicializa portfólio.
        
        Args:
            tickers: Lista de tickers no portfólio
            scores: Dicionário opcional {ticker: score} para ponderação
        """
        self.tickers = tickers
        self.scores = scores or {}
        self.weights = {}
    
    def calculate_equal_weights(self) -> Dict[str, float]:
        """
        Calcula pesos iguais para todos os ativos.
        
        Returns:
            Dicionário {ticker: weight}
        """
        if not self.tickers:
            return {}
        
        weight = 1.0 / len(self.tickers)
        self.weights = {ticker: weight for ticker in self.tickers}
        
        return self.weights
    
    def calculate_score_weights(
        self,
        max_weight: float = 0.25,
        use_risk_adjusted: bool = False,
        volatilities: Dict[str, float] = None
    ) -> Dict[str, float]:
        """
        Calcula pesos proporcionais aos scores com limite máximo.
        
        Opcionalmente ajusta scores pelo risco (volatilidade).
        
        Args:
            max_weight: Peso máximo por ativo (ex: 0.25 = 25%)
            use_risk_adjusted: Se True, ajusta scores pela volatilidade
            volatilities: Dicionário {ticker: volatility} para ajuste de risco
            
        Returns:
            Dicionário {ticker: weight}
        """
        if not self.tickers or not self.scores:
            return self.calculate_equal_weights()
        
        # Obter scores dos tickers no portfólio
        portfolio_scores = {}
        for ticker in self.tickers:
            score = self.scores.get(ticker, 0.0)
            
            # Ajustar por risco se solicitado
            if use_risk_adjusted and volatilities:
                vol = volatilities.get(ticker)
                if vol and vol > 0:
                    # Score ajustado = score / volatilidade
                    score = score / vol
            
            # Tratar scores negativos como 0
            portfolio_scores[ticker] = max(0.0, score)
        
        # Calcular soma dos scores
        total_score = sum(portfolio_scores.values())
        
        if total_score == 0:
            # Se todos os scores são 0, usar equal weight
            return self.calculate_equal_weights()
        
        # Calcular pesos proporcionais
        raw_weights = {
            ticker: score / total_score
            for ticker, score in portfolio_scores.items()
        }
        
        # Aplicar limite máximo
        capped_weights = {}
        excess_weight = 0.0
        
        for ticker, weight in raw_weights.items():
            if weight > max_weight:
                capped_weights[ticker] = max_weight
                excess_weight += (weight - max_weight)
            else:
                capped_weights[ticker] = weight
        
        # Redistribuir peso excedente proporcionalmente
        if excess_weight > 0:
            # Tickers que não atingiram o limite
            uncapped_tickers = [t for t, w in capped_weights.items() if w < max_weight]
            
            if uncapped_tickers:
                uncapped_total = sum(capped_weights[t] for t in uncapped_tickers)
                
                if uncapped_total > 0:
                    for ticker in uncapped_tickers:
                        # Redistribuir proporcionalmente
                        additional = excess_weight * (capped_weights[ticker] / uncapped_total)
                        capped_weights[ticker] += additional
                        
                        # Garantir que não ultrapasse o limite
                        capped_weights[ticker] = min(capped_weights[ticker], max_weight)
        
        # Normalizar para somar exatamente 1.0
        total_weight = sum(capped_weights.values())
        if total_weight > 0:
            self.weights = {
                ticker: weight / total_weight
                for ticker, weight in capped_weights.items()
            }
        else:
            self.weights = self.calculate_equal_weights()
        
        logger.info(f"Calculated score-weighted portfolio: {len(self.weights)} assets")
        logger.debug(f"Weights: {self.weights}")
        
        return self.weights
    
    def calculate_portfolio_return(
        self,
        returns: Dict[str, float],
        weights: Dict[str, float] = None
    ) -> float:
        """
        Calcula retorno do portfólio dado retornos individuais.
        
        Args:
            returns: Dicionário {ticker: return} com retornos dos ativos
            weights: Dicionário {ticker: weight} opcional (usa self.weights se None)
            
        Returns:
            Retorno do portfólio
        """
        if weights is None:
            weights = self.weights
        
        if not weights:
            return 0.0
        
        # Calcular retorno ponderado
        portfolio_return = 0.0
        for ticker, weight in weights.items():
            asset_return = returns.get(ticker, 0.0)
            portfolio_return += weight * asset_return
        
        return portfolio_return
    
    @staticmethod
    def select_top_n(
        scores_df: pd.DataFrame,
        top_n: int,
        score_column: str = 'final_score'
    ) -> List[str]:
        """
        Seleciona top N ativos por score.
        
        Args:
            scores_df: DataFrame com colunas ['ticker', score_column]
            top_n: Número de ativos a selecionar
            score_column: Nome da coluna de score
            
        Returns:
            Lista de tickers selecionados
        """
        # Ordenar por score (descendente) e selecionar top N
        top_assets = scores_df.nlargest(top_n, score_column)
        
        return top_assets['ticker'].tolist()
    
    def __repr__(self):
        return f"<Portfolio(tickers={len(self.tickers)}, weights={self.weights})>"
