"""
Cálculo de fatores de momentum diários.

Valida: Requisitos 3.1, 3.2, 3.3, 3.4, 3.5
"""

from typing import Dict
import pandas as pd
import numpy as np
from app.core.exceptions import InsufficientDataError, CalculationError
import logging

logger = logging.getLogger(__name__)


class MomentumFactorCalculator:
    """
    Calcula fatores de momentum diários a partir de dados de preços.
    
    Valida: Requisitos 3.1, 3.2, 3.3, 3.4, 3.5
    """
    
    def calculate_return_6m(self, prices: pd.DataFrame) -> float:
        """
        Calcula retorno acumulado dos últimos 6 meses.
        
        Retorno = (Preço_final / Preço_inicial) - 1
        
        Args:
            prices: DataFrame com coluna 'adj_close' e índice de datas,
                   ordenado cronologicamente (mais antigo primeiro)
            
        Returns:
            Retorno de 6 meses como float
            
        Raises:
            InsufficientDataError: Se não há dados suficientes (mínimo ~126 dias úteis)
            CalculationError: Se preço inicial é zero ou inválido
            
        Valida: Requisito 3.1
        """
        try:
            if len(prices) < 126:  # ~6 meses de dias úteis
                raise InsufficientDataError(
                    f"Need at least 126 days for 6m return, got {len(prices)}"
                )
            
            if 'adj_close' not in prices.columns:
                raise InsufficientDataError("Missing 'adj_close' column in prices")
            
            # Pegar últimos 126 dias úteis (~6 meses)
            recent_prices = prices.tail(126)
            
            initial_price = recent_prices['adj_close'].iloc[0]
            final_price = recent_prices['adj_close'].iloc[-1]
            
            if pd.isna(initial_price) or pd.isna(final_price):
                raise InsufficientDataError("Missing price data for 6m return")
            
            if initial_price <= 0:
                raise CalculationError(
                    f"Invalid initial price for 6m return: {initial_price}"
                )
            
            return (final_price / initial_price) - 1
            
        except (TypeError, ValueError, KeyError) as e:
            raise CalculationError(f"Error calculating 6m return: {e}")
    
    def calculate_return_12m(self, prices: pd.DataFrame) -> float:
        """
        Calcula retorno acumulado dos últimos 12 meses.
        
        Retorno = (Preço_final / Preço_inicial) - 1
        
        Args:
            prices: DataFrame com coluna 'adj_close' e índice de datas,
                   ordenado cronologicamente (mais antigo primeiro)
            
        Returns:
            Retorno de 12 meses como float
            
        Raises:
            InsufficientDataError: Se não há dados suficientes (mínimo ~252 dias úteis)
            CalculationError: Se preço inicial é zero ou inválido
            
        Valida: Requisito 3.2
        """
        try:
            if len(prices) < 252:  # ~12 meses de dias úteis
                raise InsufficientDataError(
                    f"Need at least 252 days for 12m return, got {len(prices)}"
                )
            
            if 'adj_close' not in prices.columns:
                raise InsufficientDataError("Missing 'adj_close' column in prices")
            
            # Pegar últimos 252 dias úteis (~12 meses)
            recent_prices = prices.tail(252)
            
            initial_price = recent_prices['adj_close'].iloc[0]
            final_price = recent_prices['adj_close'].iloc[-1]
            
            if pd.isna(initial_price) or pd.isna(final_price):
                raise InsufficientDataError("Missing price data for 12m return")
            
            if initial_price <= 0:
                raise CalculationError(
                    f"Invalid initial price for 12m return: {initial_price}"
                )
            
            return (final_price / initial_price) - 1
            
        except (TypeError, ValueError, KeyError) as e:
            raise CalculationError(f"Error calculating 12m return: {e}")
    
    def calculate_rsi_14(self, prices: pd.DataFrame) -> float:
        """
        Calcula RSI (Relative Strength Index) de 14 períodos.
        
        RSI = 100 - (100 / (1 + RS))
        onde RS = Média de ganhos / Média de perdas
        
        Args:
            prices: DataFrame com coluna 'adj_close' e índice de datas,
                   ordenado cronologicamente (mais antigo primeiro)
            
        Returns:
            RSI como float (0-100)
            
        Raises:
            InsufficientDataError: Se não há dados suficientes (mínimo 15 dias)
            CalculationError: Se cálculo falhar
            
        Valida: Requisito 3.3
        """
        try:
            if len(prices) < 15:  # Precisa de 15 dias para calcular RSI de 14 períodos
                raise InsufficientDataError(
                    f"Need at least 15 days for RSI-14, got {len(prices)}"
                )
            
            if 'adj_close' not in prices.columns:
                raise InsufficientDataError("Missing 'adj_close' column in prices")
            
            # Calcular mudanças de preço
            close_prices = prices['adj_close'].copy()
            delta = close_prices.diff()
            
            # Separar ganhos e perdas
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            # Calcular médias móveis exponenciais de 14 períodos
            avg_gain = gains.rolling(window=14, min_periods=14).mean().iloc[-1]
            avg_loss = losses.rolling(window=14, min_periods=14).mean().iloc[-1]
            
            if pd.isna(avg_gain) or pd.isna(avg_loss):
                raise InsufficientDataError("Insufficient data for RSI calculation")
            
            # Caso especial: se não há perdas, RSI = 100
            if avg_loss == 0:
                return 100.0
            
            # Calcular RS e RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except (TypeError, ValueError, KeyError) as e:
            raise CalculationError(f"Error calculating RSI: {e}")
    
    def calculate_volatility_90d(self, prices: pd.DataFrame) -> float:
        """
        Calcula volatilidade (desvio padrão dos retornos) de 90 dias.
        
        Volatilidade = std(retornos diários) * sqrt(252) (anualizada)
        
        Args:
            prices: DataFrame com coluna 'adj_close' e índice de datas,
                   ordenado cronologicamente (mais antigo primeiro)
            
        Returns:
            Volatilidade anualizada como float
            
        Raises:
            InsufficientDataError: Se não há dados suficientes (mínimo 91 dias)
            CalculationError: Se cálculo falhar
            
        Valida: Requisito 3.4
        """
        try:
            if len(prices) < 91:  # Precisa de 91 dias para calcular volatilidade de 90 dias
                raise InsufficientDataError(
                    f"Need at least 91 days for 90d volatility, got {len(prices)}"
                )
            
            if 'adj_close' not in prices.columns:
                raise InsufficientDataError("Missing 'adj_close' column in prices")
            
            # Pegar últimos 90 dias
            recent_prices = prices.tail(91)
            
            # Calcular retornos diários
            returns = recent_prices['adj_close'].pct_change().dropna()
            
            if len(returns) < 90:
                raise InsufficientDataError("Insufficient returns for volatility calculation")
            
            # Calcular desvio padrão e anualizar
            daily_std = returns.std()
            
            if pd.isna(daily_std):
                raise InsufficientDataError("Could not calculate standard deviation")
            
            # Anualizar (252 dias úteis por ano)
            annualized_vol = daily_std * np.sqrt(252)
            
            return annualized_vol
            
        except (TypeError, ValueError, KeyError) as e:
            raise CalculationError(f"Error calculating volatility: {e}")
    
    def calculate_volatility_180d(self, prices: pd.DataFrame) -> float:
        """
        Calcula volatilidade (desvio padrão dos retornos) de 180 dias.
        
        Volatilidade = std(retornos diários) * sqrt(252) (anualizada)
        
        Args:
            prices: DataFrame com coluna 'adj_close' e índice de datas,
                   ordenado cronologicamente (mais antigo primeiro)
            
        Returns:
            Volatilidade anualizada como float
            
        Raises:
            InsufficientDataError: Se não há dados suficientes (mínimo 181 dias)
            CalculationError: Se cálculo falhar
            
        Valida: Requisito 4.2
        """
        try:
            if len(prices) < 181:  # Precisa de 181 dias para calcular volatilidade de 180 dias
                raise InsufficientDataError(
                    f"Need at least 181 days for 180d volatility, got {len(prices)}"
                )
            
            if 'adj_close' not in prices.columns:
                raise InsufficientDataError("Missing 'adj_close' column in prices")
            
            # Pegar últimos 180 dias
            recent_prices = prices.tail(181)
            
            # Calcular retornos diários
            returns = recent_prices['adj_close'].pct_change().dropna()
            
            if len(returns) < 180:
                raise InsufficientDataError("Insufficient returns for volatility calculation")
            
            # Calcular desvio padrão e anualizar
            daily_std = returns.std()
            
            if pd.isna(daily_std):
                raise InsufficientDataError("Could not calculate standard deviation")
            
            # Anualizar (252 dias úteis por ano)
            annualized_vol = daily_std * np.sqrt(252)
            
            return annualized_vol
            
        except (TypeError, ValueError, KeyError) as e:
            raise CalculationError(f"Error calculating 180d volatility: {e}")
    
    def calculate_recent_drawdown(self, prices: pd.DataFrame) -> float:
        """
        Calcula drawdown desde o pico recente (últimos 90 dias).
        
        Drawdown = (Preço_atual - Pico_recente) / Pico_recente
        
        Args:
            prices: DataFrame com coluna 'adj_close' e índice de datas,
                   ordenado cronologicamente (mais antigo primeiro)
            
        Returns:
            Drawdown como float (valor negativo ou zero)
            
        Raises:
            InsufficientDataError: Se não há dados suficientes (mínimo 90 dias)
            CalculationError: Se cálculo falhar
            
        Valida: Requisito 3.5
        """
        try:
            if len(prices) < 90:
                raise InsufficientDataError(
                    f"Need at least 90 days for drawdown, got {len(prices)}"
                )
            
            if 'adj_close' not in prices.columns:
                raise InsufficientDataError("Missing 'adj_close' column in prices")
            
            # Pegar últimos 90 dias
            recent_prices = prices.tail(90)
            
            # Encontrar pico recente
            peak = recent_prices['adj_close'].max()
            current = recent_prices['adj_close'].iloc[-1]
            
            if pd.isna(peak) or pd.isna(current):
                raise InsufficientDataError("Missing price data for drawdown")
            
            if peak <= 0:
                raise CalculationError(f"Invalid peak price for drawdown: {peak}")
            
            # Calcular drawdown
            drawdown = (current - peak) / peak
            
            return drawdown
            
        except (TypeError, ValueError, KeyError) as e:
            raise CalculationError(f"Error calculating drawdown: {e}")
    
    def calculate_max_drawdown_3y(self, prices: pd.DataFrame) -> float:
        """
        Calcula drawdown máximo dos últimos 3 anos.
        
        Drawdown máximo = min((Preço - Pico_anterior) / Pico_anterior)
        para todos os pontos no período
        
        Args:
            prices: DataFrame com coluna 'adj_close' e índice de datas,
                   ordenado cronologicamente (mais antigo primeiro)
            
        Returns:
            Drawdown máximo como float (valor negativo ou zero)
            
        Raises:
            InsufficientDataError: Se não há dados suficientes (mínimo 756 dias)
            CalculationError: Se cálculo falhar
            
        Valida: Requisito 4.3
        """
        try:
            if len(prices) < 756:  # ~3 anos de dias úteis
                raise InsufficientDataError(
                    f"Need at least 756 days for 3y max drawdown, got {len(prices)}"
                )
            
            if 'adj_close' not in prices.columns:
                raise InsufficientDataError("Missing 'adj_close' column in prices")
            
            # Pegar últimos 756 dias úteis (~3 anos)
            recent_prices = prices.tail(756)
            
            # Calcular pico acumulado (running maximum)
            close_prices = recent_prices['adj_close']
            running_max = close_prices.expanding().max()
            
            # Calcular drawdown em cada ponto
            drawdowns = (close_prices - running_max) / running_max
            
            # Encontrar drawdown máximo (mais negativo)
            max_drawdown = drawdowns.min()
            
            if pd.isna(max_drawdown):
                raise InsufficientDataError("Could not calculate max drawdown")
            
            return max_drawdown
            
        except (TypeError, ValueError, KeyError) as e:
            raise CalculationError(f"Error calculating 3y max drawdown: {e}")
    
    def calculate_all_factors(
        self,
        ticker: str,
        prices: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calcula todos os fatores de momentum para um ativo.
        
        Args:
            ticker: Símbolo do ativo
            prices: DataFrame com coluna 'adj_close' e índice de datas,
                   ordenado cronologicamente (mais antigo primeiro)
            
        Returns:
            Dict com chaves: return_6m, return_12m, rsi_14,
                           volatility_90d, volatility_180d, recent_drawdown,
                           max_drawdown_3y
            Fatores que não podem ser calculados terão valor None
            
        Valida: Requisitos 3.1, 3.2, 3.3, 3.4, 3.5, 4.2, 4.3
        """
        factors = {}
        
        # Return 6m
        try:
            factors['return_6m'] = self.calculate_return_6m(prices)
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate 6m return for {ticker}: {e}")
            factors['return_6m'] = None
        
        # Return 12m
        try:
            factors['return_12m'] = self.calculate_return_12m(prices)
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate 12m return for {ticker}: {e}")
            factors['return_12m'] = None
        
        # RSI 14
        try:
            factors['rsi_14'] = self.calculate_rsi_14(prices)
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate RSI for {ticker}: {e}")
            factors['rsi_14'] = None
        
        # Volatility 90d
        try:
            factors['volatility_90d'] = self.calculate_volatility_90d(prices)
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate volatility for {ticker}: {e}")
            factors['volatility_90d'] = None
        
        # Volatility 180d
        try:
            factors['volatility_180d'] = self.calculate_volatility_180d(prices)
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate 180d volatility for {ticker}: {e}")
            factors['volatility_180d'] = None
        
        # Recent Drawdown
        try:
            factors['recent_drawdown'] = self.calculate_recent_drawdown(prices)
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate drawdown for {ticker}: {e}")
            factors['recent_drawdown'] = None
        
        # Max Drawdown 3y
        try:
            factors['max_drawdown_3y'] = self.calculate_max_drawdown_3y(prices)
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate 3y max drawdown for {ticker}: {e}")
            factors['max_drawdown_3y'] = None
        
        return factors
