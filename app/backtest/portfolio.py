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
    
    def calculate_score_weights(self) -> Dict[str, float]:
        """
        Calcula pesos proporcionais aos scores.
        
        Pesos são normalizados para somar 1.0.
        Scores negativos são tratados como 0.
        
        Returns:
            Dicionário {ticker: weight}
        """
        if not self.tickers or not self.scores:
            return self.calculate_equal_weights()
        
        # Obter scores dos tickers no portfólio
        portfolio_scores = {}
        for ticker in self.tickers:
            score = self.scores.get(ticker, 0.0)
            # Tratar scores negativos como 0
            portfolio_scores[ticker] = max(0.0, score)
        
        # Calcular soma dos scores
        total_score = sum(portfolio_scores.values())
        
        if total_score == 0:
            # Se todos os scores são 0, usar equal weight
            return self.calculate_equal_weights()
        
        # Calcular pesos proporcionais
        self.weights = {
            ticker: score / total_score
            for ticker, score in portfolio_scores.items()
        }
        
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
