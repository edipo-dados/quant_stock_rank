"""
Modelos SQLAlchemy para todas as tabelas do sistema.

Valida: Requisitos 8.1, 8.2, 8.3, 8.4, 8.5, 8.7, 8.8
"""

from sqlalchemy import (
    Column, Integer, String, Float, BigInteger, Date, DateTime,
    Boolean, JSON, UniqueConstraint, Index
)
from datetime import datetime
from app.models.database import Base


class RawPriceDaily(Base):
    """
    Tabela para armazenar dados brutos de preços diários.
    
    Valida: Requisitos 8.1, 8.7, 8.8
    """
    __tablename__ = "raw_prices_daily"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger)
    adj_close = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('ticker', 'date', name='uix_ticker_date'),
        Index('idx_ticker_date', 'ticker', 'date'),
    )
    
    def __repr__(self):
        return f"<RawPriceDaily(ticker={self.ticker}, date={self.date}, close={self.close})>"


class RawFundamental(Base):
    """
    Tabela para armazenar dados brutos fundamentalistas.
    
    Valida: Requisitos 8.2, 8.7, 8.8
    """
    __tablename__ = "raw_fundamentals"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    period_end_date = Column(Date, nullable=False)
    period_type = Column(String(20))  # annual, quarterly
    
    # Income Statement
    revenue = Column(Float)
    net_income = Column(Float)
    ebitda = Column(Float)
    eps = Column(Float)
    
    # Balance Sheet
    total_assets = Column(Float)
    total_debt = Column(Float)
    shareholders_equity = Column(Float)
    book_value_per_share = Column(Float)
    
    # Cash Flow
    operating_cash_flow = Column(Float)
    free_cash_flow = Column(Float)
    
    # Metrics
    market_cap = Column(Float)
    enterprise_value = Column(Float)
    
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('ticker', 'period_end_date', 'period_type', 
                        name='uix_ticker_period'),
        Index('idx_ticker_period', 'ticker', 'period_end_date'),
    )
    
    def __repr__(self):
        return f"<RawFundamental(ticker={self.ticker}, period_end_date={self.period_end_date})>"


class AssetInfo(Base):
    """
    Tabela para armazenar informações básicas dos ativos (setor, indústria, etc).
    
    Valida: Requisitos 8.2, 8.7, 8.8
    """
    __tablename__ = "asset_info"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), nullable=False, unique=True, index=True)
    
    # Sector and Industry information
    sector = Column(String(100))  # e.g., "Financial Services"
    industry = Column(String(100))  # e.g., "Banks - Regional"
    sector_key = Column(String(50))  # e.g., "financial-services"
    industry_key = Column(String(50))  # e.g., "banks-regional"
    
    # Company information
    company_name = Column(String(200))
    country = Column(String(50))
    currency = Column(String(10))
    
    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AssetInfo(ticker={self.ticker}, sector={self.sector}, industry={self.industry})>"


class FeatureDaily(Base):
    """
    Tabela para armazenar fatores de momentum calculados diariamente.
    
    Valida: Requisitos 8.3, 8.7, 8.8
    """
    __tablename__ = "features_daily"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Momentum Factors (normalized)
    return_6m = Column(Float)
    return_12m = Column(Float)
    rsi_14 = Column(Float)
    volatility_90d = Column(Float)
    recent_drawdown = Column(Float)
    
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('ticker', 'date', name='uix_ticker_date_features'),
        Index('idx_ticker_date_features', 'ticker', 'date'),
    )
    
    def __repr__(self):
        return f"<FeatureDaily(ticker={self.ticker}, date={self.date})>"


class FeatureMonthly(Base):
    """
    Tabela para armazenar fatores fundamentalistas calculados mensalmente.
    
    Valida: Requisitos 8.4, 8.7, 8.8
    """
    __tablename__ = "features_monthly"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    month = Column(Date, nullable=False, index=True)  # First day of month
    
    # Fundamental Factors (normalized)
    roe = Column(Float)
    net_margin = Column(Float)
    revenue_growth_3y = Column(Float)
    debt_to_ebitda = Column(Float)
    pe_ratio = Column(Float)
    ev_ebitda = Column(Float)
    pb_ratio = Column(Float)
    
    # Robustness fields (added for scoring improvements)
    roe_mean_3y = Column(Float)
    roe_volatility = Column(Float)
    debt_to_ebitda_raw = Column(Float)
    net_income_last_year = Column(Float)
    net_income_history = Column(JSON)  # List of net income values
    
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('ticker', 'month', name='uix_ticker_month_features'),
        Index('idx_ticker_month_features', 'ticker', 'month'),
    )
    
    def __repr__(self):
        return f"<FeatureMonthly(ticker={self.ticker}, month={self.month})>"


class ScoreDaily(Base):
    """
    Tabela para armazenar scores finais e rankings diários.
    
    Valida: Requisitos 8.5, 8.7, 8.8
    """
    __tablename__ = "scores_daily"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Scores
    final_score = Column(Float, nullable=False)
    momentum_score = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=False)
    value_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Enhanced scoring fields
    base_score = Column(Float)
    risk_penalty_factor = Column(Float)
    passed_eligibility = Column(Boolean, default=True)
    exclusion_reasons = Column(JSON)
    risk_penalties = Column(JSON)
    distress_flag = Column(Boolean, default=False)  # Added for robustness improvements
    
    # Ranking
    rank = Column(Integer)
    
    # Metadata
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('ticker', 'date', name='uix_ticker_date_scores'),
        Index('idx_date_score', 'date', 'final_score'),
        Index('idx_ticker_date_scores', 'ticker', 'date'),
    )
    
    def __repr__(self):
        return f"<ScoreDaily(ticker={self.ticker}, date={self.date}, final_score={self.final_score}, rank={self.rank})>"
