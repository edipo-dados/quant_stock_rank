"""
Módulo de backtest para avaliação de estratégias quantitativas.
"""

from app.backtest.backtest_engine import BacktestEngine
from app.backtest.portfolio import Portfolio
from app.backtest.metrics import PerformanceMetrics

__all__ = ['BacktestEngine', 'Portfolio', 'PerformanceMetrics']
