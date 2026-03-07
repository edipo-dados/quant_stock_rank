"""Gerenciamento centralizado de configurações do sistema."""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Configurações do sistema carregadas de variáveis de ambiente.
    
    Valida: Requisitos 9.1, 9.2, 9.3, 9.4, 9.5, 13.5
    """
    
    # Database Configuration
    database_url: str = "sqlite:///./quant_ranker.db"
    
    # API Keys
    fmp_api_key: str = ""  # Default vazio para testes
    
    # Scoring Weights (Modelo Multifator Otimizado)
    momentum_weight: float = 0.5   # Momentum premium (aumentado)
    quality_weight: float = 0.15   # Quality premium (reduzido)
    value_weight: float = 0.25     # Value premium (reduzido)
    risk_weight: float = 0.10      # Low volatility premium
    size_weight: float = 0.0       # Size premium weight (0.0 = disabled)
    
    # Eligibility Filter Parameters
    minimum_volume: float = 5_000_000  # Minimum average daily volume (aumentado para 5M)
    minimum_market_cap: float = 1_000_000_000  # Minimum market cap (1 billion BRL)
    
    # Quality Factor Parameters
    max_roe_limit: float = 0.50  # Cap ROE at 50%
    debt_ebitda_limit: float = 4.0  # Penalty threshold for debt/EBITDA
    
    # Risk Penalization Parameters
    volatility_limit: float = 0.60  # 60% annualized volatility
    drawdown_limit: float = -0.50  # -50% maximum drawdown
    
    # Winsorization Parameters
    winsorize_lower_pct: float = 0.05  # 5th percentile
    winsorize_upper_pct: float = 0.95  # 95th percentile
    
    # Market Regime Filter Parameters
    regime_ma_period: int = 200  # Moving average period for regime detection
    regime_bullish_exposure: float = 1.0  # 100% exposure in bullish regime
    regime_bearish_exposure: float = 0.5  # 50% exposure in bearish regime
    
    # Portfolio Risk Management (v2.7.0)
    use_volatility_targeting: bool = True  # Enable volatility targeting
    target_portfolio_volatility: float = 0.15  # 15% target annual volatility
    volatility_lookback_days: int = 90  # Days for volatility calculation
    use_sector_limits: bool = True  # Enable sector exposure limits
    max_sector_exposure: float = 0.30  # 30% maximum per sector
    max_single_asset_weight: float = 0.25  # 25% maximum per asset
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Logging
    log_level: str = "INFO"
    
    # Frontend Configuration (optional)
    frontend_port: int = 8501
    backend_url: str = "http://localhost:8000"
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Instância global de configurações
settings = Settings()
