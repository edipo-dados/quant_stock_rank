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
    
    # Scoring Weights
    momentum_weight: float = 0.4
    quality_weight: float = 0.3
    value_weight: float = 0.3
    size_weight: float = 0.0  # Size premium weight (0.0 = disabled, 0.1 = 10%)
    
    # Eligibility Filter Parameters
    minimum_volume: float = 100000  # Minimum average daily volume
    
    # Quality Factor Parameters
    max_roe_limit: float = 0.50  # Cap ROE at 50%
    debt_ebitda_limit: float = 4.0  # Penalty threshold for debt/EBITDA
    
    # Risk Penalization Parameters
    volatility_limit: float = 0.60  # 60% annualized volatility
    drawdown_limit: float = -0.50  # -50% maximum drawdown
    
    # Winsorization Parameters
    winsorize_lower_pct: float = 0.05  # 5th percentile
    winsorize_upper_pct: float = 0.95  # 95th percentile
    
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
