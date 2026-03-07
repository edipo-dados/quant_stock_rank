"""
Gerenciamento de portfólio para backtest.

Implementa:
- Equal weight e score-weighted portfolios
- Volatility targeting (v2.7.0)
- Sector exposure limits (v2.7.0)
- Risk-adjusted weighting
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class Portfolio:
    """
    Representa um portfólio de ativos com pesos.
    
    Suporta diferentes métodos de ponderação:
    - Equal weight: Todos os ativos com peso igual
    - Score weighted: Pesos proporcionais aos scores
    """
    
    def __init__(
        self,
        tickers: List[str],
        scores: Dict[str, float] = None,
        sectors: Dict[str, str] = None
    ):
        """
        Inicializa portfólio.
        
        Args:
            tickers: Lista de tickers no portfólio
            scores: Dicionário opcional {ticker: score} para ponderação
            sectors: Dicionário opcional {ticker: sector} para limites setoriais
        """
        self.tickers = tickers
        self.scores = scores or {}
        self.sectors = sectors or {}
        self.weights = {}
        self.sector_exposures = {}  # Exposição por setor
    
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
    
    def apply_volatility_targeting(
        self,
        weights: Dict[str, float],
        volatilities: Dict[str, float],
        returns_history: Dict[str, pd.Series],
        target_vol: float = 0.15
    ) -> Dict[str, float]:
        """
        Aplica volatility targeting ao portfólio.
        
        Ajusta exposição total para atingir volatilidade alvo.
        
        Args:
            weights: Pesos atuais do portfólio {ticker: weight}
            volatilities: Volatilidades individuais {ticker: vol_annual}
            returns_history: Histórico de retornos {ticker: Series}
            target_vol: Volatilidade alvo anualizada (ex: 0.15 = 15%)
            
        Returns:
            Pesos ajustados {ticker: weight}
        """
        if not weights or not returns_history:
            logger.warning("Cannot apply volatility targeting: missing data")
            return weights
        
        try:
            # Construir matriz de retornos
            tickers_with_data = [t for t in weights.keys() if t in returns_history]
            
            if len(tickers_with_data) < 2:
                logger.warning("Insufficient return history for volatility targeting")
                return weights
            
            # Alinhar séries de retornos
            returns_df = pd.DataFrame({
                ticker: returns_history[ticker]
                for ticker in tickers_with_data
            }).dropna()
            
            if len(returns_df) < 20:  # Mínimo de 20 observações
                logger.warning(f"Insufficient data points for vol targeting: {len(returns_df)}")
                return weights
            
            # Calcular matriz de covariância anualizada
            cov_matrix = returns_df.cov() * 252  # Anualizar (assumindo retornos diários)
            
            # Vetor de pesos
            weight_vector = np.array([weights.get(t, 0.0) for t in tickers_with_data])
            
            # Calcular volatilidade do portfólio
            portfolio_variance = np.dot(weight_vector, np.dot(cov_matrix, weight_vector))
            portfolio_vol = np.sqrt(portfolio_variance)
            
            logger.info(f"Portfolio volatility (before targeting): {portfolio_vol*100:.2f}%")
            
            # Calcular fator de ajuste
            if portfolio_vol > 0:
                adjustment_factor = target_vol / portfolio_vol
                
                # Limitar ajuste para evitar alavancagem excessiva ou redução drástica
                adjustment_factor = max(0.5, min(1.5, adjustment_factor))
                
                logger.info(f"Volatility adjustment factor: {adjustment_factor:.3f}")
                
                # Aplicar ajuste
                adjusted_weights = {
                    ticker: weight * adjustment_factor
                    for ticker, weight in weights.items()
                }
                
                # Renormalizar
                total_weight = sum(adjusted_weights.values())
                if total_weight > 0:
                    adjusted_weights = {
                        ticker: weight / total_weight
                        for ticker, weight in adjusted_weights.items()
                    }
                
                # Calcular volatilidade ajustada
                adjusted_weight_vector = np.array([
                    adjusted_weights.get(t, 0.0) for t in tickers_with_data
                ])
                adjusted_variance = np.dot(
                    adjusted_weight_vector,
                    np.dot(cov_matrix, adjusted_weight_vector)
                )
                adjusted_vol = np.sqrt(adjusted_variance)
                
                logger.info(f"Portfolio volatility (after targeting): {adjusted_vol*100:.2f}%")
                
                return adjusted_weights
            else:
                logger.warning("Portfolio volatility is zero, cannot apply targeting")
                return weights
                
        except Exception as e:
            logger.error(f"Error applying volatility targeting: {e}", exc_info=True)
            return weights
    
    def apply_sector_limits(
        self,
        weights: Dict[str, float],
        sectors: Dict[str, str],
        max_sector_exposure: float = 0.30
    ) -> Dict[str, float]:
        """
        Aplica limites de exposição por setor.
        
        Args:
            weights: Pesos atuais {ticker: weight}
            sectors: Mapeamento {ticker: sector}
            max_sector_exposure: Exposição máxima por setor (ex: 0.30 = 30%)
            
        Returns:
            Pesos ajustados {ticker: weight}
        """
        if not weights or not sectors:
            logger.warning("Cannot apply sector limits: missing data")
            return weights
        
        # Calcular exposição por setor
        sector_exposures = {}
        for ticker, weight in weights.items():
            sector = sectors.get(ticker, 'Unknown')
            sector_exposures[sector] = sector_exposures.get(sector, 0.0) + weight
        
        # Identificar setores que excedem o limite
        violating_sectors = {
            sector: exposure
            for sector, exposure in sector_exposures.items()
            if exposure > max_sector_exposure
        }
        
        if not violating_sectors:
            logger.info("All sectors within limits")
            self.sector_exposures = sector_exposures
            return weights
        
        logger.info(f"Sectors exceeding limit: {violating_sectors}")
        
        # Ajustar pesos dos setores que excedem
        adjusted_weights = weights.copy()
        
        for sector, current_exposure in violating_sectors.items():
            # Calcular fator de redução
            reduction_factor = max_sector_exposure / current_exposure
            
            # Reduzir pesos dos ativos deste setor
            sector_tickers = [
                t for t, s in sectors.items()
                if s == sector and t in adjusted_weights
            ]
            
            excess_weight = 0.0
            for ticker in sector_tickers:
                old_weight = adjusted_weights[ticker]
                new_weight = old_weight * reduction_factor
                adjusted_weights[ticker] = new_weight
                excess_weight += (old_weight - new_weight)
            
            logger.info(
                f"Reduced {sector} exposure from {current_exposure*100:.1f}% "
                f"to {max_sector_exposure*100:.1f}% (excess: {excess_weight*100:.2f}%)"
            )
        
        # Redistribuir peso excedente para setores abaixo do limite
        total_excess = sum(weights.values()) - sum(adjusted_weights.values())
        
        if total_excess > 0.001:  # Tolerância numérica
            # Setores que podem receber peso adicional
            eligible_sectors = {
                sector: exposure
                for sector, exposure in sector_exposures.items()
                if sector not in violating_sectors and exposure < max_sector_exposure
            }
            
            if eligible_sectors:
                # Calcular capacidade de cada setor
                sector_capacity = {
                    sector: max_sector_exposure - exposure
                    for sector, exposure in eligible_sectors.items()
                }
                
                total_capacity = sum(sector_capacity.values())
                
                if total_capacity > 0:
                    # Distribuir proporcionalmente à capacidade
                    for ticker, weight in adjusted_weights.items():
                        sector = sectors.get(ticker, 'Unknown')
                        if sector in sector_capacity:
                            capacity_share = sector_capacity[sector] / total_capacity
                            additional_weight = total_excess * capacity_share
                            
                            # Distribuir dentro do setor proporcionalmente
                            sector_tickers = [
                                t for t, s in sectors.items()
                                if s == sector and t in adjusted_weights
                            ]
                            sector_total = sum(adjusted_weights[t] for t in sector_tickers)
                            
                            if sector_total > 0:
                                ticker_share = adjusted_weights[ticker] / sector_total
                                adjusted_weights[ticker] += additional_weight * ticker_share
        
        # Renormalizar para garantir soma = 1
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            adjusted_weights = {
                ticker: weight / total_weight
                for ticker, weight in adjusted_weights.items()
            }
        
        # Recalcular exposições finais
        final_exposures = {}
        for ticker, weight in adjusted_weights.items():
            sector = sectors.get(ticker, 'Unknown')
            final_exposures[sector] = final_exposures.get(sector, 0.0) + weight
        
        self.sector_exposures = final_exposures
        
        logger.info(f"Final sector exposures: {final_exposures}")
        
        return adjusted_weights
    
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
        # Garantir que score_column é numérico
        if score_column in scores_df.columns:
            scores_df[score_column] = pd.to_numeric(scores_df[score_column], errors='coerce')
            
            # Remover NaN
            scores_df = scores_df.dropna(subset=[score_column])
        
        if scores_df.empty:
            logger.warning(f"No valid scores in column {score_column}")
            return []
        
        # Ordenar por score (descendente) e selecionar top N
        top_assets = scores_df.nlargest(top_n, score_column)
        
        return top_assets['ticker'].tolist()
    
    def __repr__(self):
        return f"<Portfolio(tickers={len(self.tickers)}, weights={self.weights})>"
