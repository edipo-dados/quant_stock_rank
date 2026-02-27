"""
Módulo de backtest para avaliação de estratégias quantitativas.

Componentes:
- BacktestEngine: Motor de simulação
- Portfolio: Gerenciamento de portfólio
- PerformanceMetrics: Cálculo de métricas
- Models: Persistência de resultados (NOVO)
- Repository: Operações de banco (NOVO)
- Service: Orquestração de backtest (NOVO)
"""

from app.backtest.backtest_engine import BacktestEngine
from app.backtest.portfolio import Portfolio
from app.backtest.metrics import PerformanceMetrics
from app.backtest.models import (
    BacktestRun,
    BacktestNAV,
    BacktestPosition,
    BacktestMetrics
)
from app.backtest.repository import BacktestRepository
from app.backtest.service import BacktestService

__all__ = [
    'BacktestEngine',
    'Portfolio',
    'PerformanceMetrics',
    'BacktestRun',
    'BacktestNAV',
    'BacktestPosition',
    'BacktestMetrics',
    'BacktestRepository',
    'BacktestService'
]

