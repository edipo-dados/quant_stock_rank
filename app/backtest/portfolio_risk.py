"""
Módulo de gerenciamento de risco de portfólio (v2.7.0).

Implementa:
- Cálculo de volatilidades
- Obtenção de setores
- Histórico de retornos
"""

from typing import Dict, List
from datetime import date, timedelta
import pandas as pd
import numpy as np
import logging
from sqlalchemy.orm import Session

from app.models.schemas import AssetInfo
from app.ingestion.yahoo_client import YahooFinanceClient

logger = logging.getLogger(__name__)


class PortfolioRiskManager:
    """
    Gerencia cálculos de risco para construção de portfólio.
    """
    
    def __init__(self):
        self.yahoo_client = YahooFinanceClient()
    
    def get_asset_volatilities(
        self,
        tickers: List[str],
        reference_date: date,
        lookback_days: int = 90
    ) -> Dict[str, float]:
        """
        Calcula volatilidades anualizadas dos ativos.
        
        Args:
            tickers: Lista de tickers
            reference_date: Data de referência
            lookback_days: Dias para trás para calcular volatilidade
            
        Returns:
            Dicionário {ticker: volatility_annual}
        """
        volatilities = {}
        start_date = reference_date - timedelta(days=lookback_days + 30)  # Buffer
        
        for ticker in tickers:
            try:
                # Buscar preços históricos
                prices_df = self.yahoo_client.fetch_daily_prices(
                    ticker,
                    start_date,
                    reference_date
                )
                
                if prices_df.empty or len(prices_df) < 20:
                    logger.warning(f"Insufficient data for volatility calc: {ticker}")
                    volatilities[ticker] = 0.20  # Default 20%
                    continue
                
                # Calcular retornos diários
                prices_df['returns'] = prices_df['close'].pct_change()
                
                # Pegar últimos lookback_days
                recent_returns = prices_df['returns'].dropna().tail(lookback_days)
                
                if len(recent_returns) < 20:
                    volatilities[ticker] = 0.20  # Default
                    continue
                
                # Calcular volatilidade anualizada
                daily_vol = recent_returns.std()
                annual_vol = daily_vol * np.sqrt(252)
                
                volatilities[ticker] = annual_vol
                
                logger.debug(f"{ticker} volatility: {annual_vol*100:.2f}%")
                
            except Exception as e:
                logger.error(f"Error calculating volatility for {ticker}: {e}")
                volatilities[ticker] = 0.20  # Default
        
        return volatilities
    
    def get_asset_sectors(
        self,
        tickers: List[str],
        db: Session
    ) -> Dict[str, str]:
        """
        Obtém setores dos ativos.
        
        Args:
            tickers: Lista de tickers
            db: Sessão do banco
            
        Returns:
            Dicionário {ticker: sector}
        """
        sectors = {}
        
        for ticker in tickers:
            try:
                asset_info = db.query(AssetInfo).filter(
                    AssetInfo.ticker == ticker
                ).first()
                
                if asset_info and asset_info.sector:
                    sectors[ticker] = asset_info.sector
                else:
                    sectors[ticker] = 'Unknown'
                    logger.warning(f"No sector info for {ticker}, using 'Unknown'")
                    
            except Exception as e:
                logger.error(f"Error getting sector for {ticker}: {e}")
                sectors[ticker] = 'Unknown'
        
        return sectors
    
    def get_returns_history(
        self,
        tickers: List[str],
        reference_date: date,
        lookback_days: int = 90
    ) -> Dict[str, pd.Series]:
        """
        Obtém histórico de retornos diários dos ativos.
        
        Args:
            tickers: Lista de tickers
            reference_date: Data de referência
            lookback_days: Dias para trás
            
        Returns:
            Dicionário {ticker: Series de retornos}
        """
        returns_history = {}
        start_date = reference_date - timedelta(days=lookback_days + 30)
        
        for ticker in tickers:
            try:
                prices_df = self.yahoo_client.fetch_daily_prices(
                    ticker,
                    start_date,
                    reference_date
                )
                
                if prices_df.empty:
                    logger.warning(f"No price data for {ticker}")
                    continue
                
                # Calcular retornos diários
                prices_df['returns'] = prices_df['close'].pct_change()
                
                # Pegar últimos lookback_days
                recent_returns = prices_df['returns'].dropna().tail(lookback_days)
                
                if len(recent_returns) >= 20:
                    returns_history[ticker] = recent_returns
                    logger.debug(f"{ticker}: {len(recent_returns)} return observations")
                else:
                    logger.warning(f"Insufficient return history for {ticker}: {len(recent_returns)}")
                    
            except Exception as e:
                logger.error(f"Error getting returns history for {ticker}: {e}")
        
        return returns_history
