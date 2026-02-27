"""
Modelos SQLAlchemy para persistência de backtesting.

Estrutura isolada para armazenar:
- Execuções de backtest
- NAV diário (equity curve)
- Posições por rebalance
- Métricas finais

IMPORTANTE: Estas tabelas são isoladas e NÃO afetam dados de produção.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Text,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.database import Base


class BacktestRun(Base):
    """
    Armazena metadados de cada execução de backtest.
    
    Permite comparar versões de modelo e armazenar histórico de experimentos.
    """
    __tablename__ = "backtest_runs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=True, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    rebalance_frequency = Column(String(20), nullable=False, default="monthly")
    top_n = Column(Integer, nullable=False)
    transaction_cost = Column(Float, nullable=False, default=0.001)
    initial_capital = Column(Float, nullable=False, default=100000.0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    # Relacionamentos
    nav_records = relationship("BacktestNAV", back_populates="run", cascade="all, delete-orphan")
    positions = relationship("BacktestPosition", back_populates="run", cascade="all, delete-orphan")
    metrics = relationship("BacktestMetrics", back_populates="run", cascade="all, delete-orphan", uselist=False)
    
    __table_args__ = (
        Index('idx_backtest_runs_dates', 'start_date', 'end_date'),
        Index('idx_backtest_runs_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<BacktestRun(id={self.id}, name={self.name}, period={self.start_date} to {self.end_date})>"


class BacktestNAV(Base):
    """
    Armazena equity curve do backtest (NAV diário).
    
    Permite visualizar evolução do portfólio ao longo do tempo.
    """
    __tablename__ = "backtest_nav"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(36), ForeignKey('backtest_runs.id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    nav = Column(Float, nullable=False)
    benchmark_nav = Column(Float, nullable=True)
    daily_return = Column(Float, nullable=False)
    benchmark_return = Column(Float, nullable=True)
    
    # Relacionamento
    run = relationship("BacktestRun", back_populates="nav_records")
    
    __table_args__ = (
        Index('idx_backtest_nav_run_date', 'run_id', 'date'),
        UniqueConstraint('run_id', 'date', name='uix_backtest_nav_run_date'),
    )
    
    def __repr__(self):
        return f"<BacktestNAV(run_id={self.run_id}, date={self.date}, nav={self.nav:.2f})>"


class BacktestPosition(Base):
    """
    Armazena carteira em cada rebalance.
    
    Permite auditar composição do portfólio em cada período.
    """
    __tablename__ = "backtest_positions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(36), ForeignKey('backtest_runs.id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    ticker = Column(String(20), nullable=False, index=True)
    weight = Column(Float, nullable=False)
    score_at_selection = Column(Float, nullable=True)
    
    # Relacionamento
    run = relationship("BacktestRun", back_populates="positions")
    
    __table_args__ = (
        Index('idx_backtest_positions_run_date', 'run_id', 'date'),
        Index('idx_backtest_positions_ticker', 'ticker'),
        UniqueConstraint('run_id', 'date', 'ticker', name='uix_backtest_position_run_date_ticker'),
    )
    
    def __repr__(self):
        return f"<BacktestPosition(run_id={self.run_id}, date={self.date}, ticker={self.ticker}, weight={self.weight:.2%})>"


class BacktestMetrics(Base):
    """
    Métricas finais da execução de backtest.
    
    Armazena todas as métricas de performance calculadas.
    """
    __tablename__ = "backtest_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(36), ForeignKey('backtest_runs.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Métricas de retorno
    total_return = Column(Float, nullable=False)
    cagr = Column(Float, nullable=False)
    
    # Métricas de risco
    volatility = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=False)
    sortino_ratio = Column(Float, nullable=False)
    max_drawdown = Column(Float, nullable=False)
    
    # Métricas operacionais
    turnover_avg = Column(Float, nullable=False)
    
    # Métricas vs benchmark (opcionais)
    alpha = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    information_ratio = Column(Float, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relacionamento
    run = relationship("BacktestRun", back_populates="metrics")
    
    __table_args__ = (
        Index('idx_backtest_metrics_run', 'run_id'),
    )
    
    def __repr__(self):
        return f"<BacktestMetrics(run_id={self.run_id}, cagr={self.cagr:.2%}, sharpe={self.sharpe_ratio:.2f})>"
