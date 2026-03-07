"""
Gerenciamento de benchmark para backtesting.

Responsável por:
- Ingestão de dados do benchmark (IBOVESPA)
- Cálculo de retornos do benchmark
- Sincronização com datas do backtest
"""

from typing import Dict, List, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import logging

from app.models.schemas import Base
from sqlalchemy import Column, Integer, String, Float, Date, UniqueConstraint, Index

logger = logging.getLogger(__name__)


class BenchmarkPrice(Base):
    """
    Tabela para armazenar preços do benchmark (IBOVESPA).
    """
    __tablename__ = "benchmark_prices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)  # ^BVSP
    date = Column(Date, nullable=False, index=True)
    close = Column(Float, nullable=False)
    daily_return = Column(Float)
    
    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uix_benchmark_symbol_date'),
        Index('idx_benchmark_date', 'date'),
    )
    
    def __repr__(self):
        return f"<BenchmarkPrice(symbol={self.symbol}, date={self.date}, close={self.close:.2f})>"


class BenchmarkManager:
    """
    Gerencia dados de benchmark para backtesting.
    """
    
    def __init__(self, db: Session, symbol: str = "^BVSP"):
        """
        Inicializa manager de benchmark.
        
        Args:
            db: Sessão do banco de dados
            symbol: Símbolo do benchmark (padrão: ^BVSP para IBOVESPA)
        """
        self.db = db
        self.symbol = symbol
    
    def get_benchmark_returns(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[date, float]:
        """
        Obtém retornos do benchmark para um período.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Dicionário {date: return}
        """
        prices = self.db.query(BenchmarkPrice).filter(
            BenchmarkPrice.symbol == self.symbol,
            BenchmarkPrice.date >= start_date,
            BenchmarkPrice.date <= end_date
        ).order_by(BenchmarkPrice.date).all()
        
        if not prices:
            logger.warning(f"No benchmark data found for {self.symbol} from {start_date} to {end_date}")
            return {}
        
        # Retornar dicionário de retornos
        returns = {price.date: price.daily_return for price in prices if price.daily_return is not None}
        
        return returns
    
    def get_period_return(
        self,
        start_date: date,
        end_date: date
    ) -> Optional[float]:
        """
        Calcula retorno do benchmark para um período.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Retorno do período (ex: 0.05 para 5%)
        """
        prices = self.db.query(BenchmarkPrice).filter(
            BenchmarkPrice.symbol == self.symbol,
            BenchmarkPrice.date >= start_date,
            BenchmarkPrice.date <= end_date
        ).order_by(BenchmarkPrice.date).all()
        
        if len(prices) < 2:
            logger.warning(f"Insufficient benchmark data for period {start_date} to {end_date}")
            return None
        
        start_price = prices[0].close
        end_price = prices[-1].close
        
        period_return = (end_price - start_price) / start_price
        
        return period_return
    
    def calculate_benchmark_nav(
        self,
        start_date: date,
        end_date: date,
        initial_value: float = 100000.0
    ) -> List[Dict]:
        """
        Calcula NAV do benchmark ao longo do tempo.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            initial_value: Valor inicial do NAV
            
        Returns:
            Lista de dicts com {date, nav, daily_return}
        """
        returns = self.get_benchmark_returns(start_date, end_date)
        
        if not returns:
            return []
        
        nav_records = []
        current_nav = initial_value
        
        for date_key in sorted(returns.keys()):
            daily_return = returns[date_key]
            current_nav = current_nav * (1 + daily_return)
            
            nav_records.append({
                'date': date_key,
                'nav': current_nav,
                'daily_return': daily_return
            })
        
        return nav_records
    
    def get_data_availability(
        self,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Verifica disponibilidade de dados do benchmark.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Dict com estatísticas de disponibilidade
        """
        count = self.db.query(BenchmarkPrice).filter(
            BenchmarkPrice.symbol == self.symbol,
            BenchmarkPrice.date >= start_date,
            BenchmarkPrice.date <= end_date
        ).count()
        
        expected_days = (end_date - start_date).days
        coverage = count / expected_days if expected_days > 0 else 0
        
        return {
            'symbol': self.symbol,
            'start_date': start_date,
            'end_date': end_date,
            'records_found': count,
            'expected_days': expected_days,
            'coverage': coverage,
            'sufficient': coverage >= 0.7  # 70% dos dias
        }
    
    def ingest_benchmark_data(
        self,
        prices_df: pd.DataFrame
    ) -> int:
        """
        Ingere dados do benchmark no banco.
        
        Args:
            prices_df: DataFrame com colunas ['date', 'close']
            
        Returns:
            Número de registros inseridos
        """
        if prices_df.empty:
            logger.warning("Empty DataFrame provided for benchmark ingestion")
            return 0
        
        # Fazer cópia para não modificar o original
        prices_df = prices_df.copy()
        
        # Resetar index
        prices_df = prices_df.reset_index(drop=True)
        
        # Ordenar por data
        prices_df = prices_df.sort_values('date').reset_index(drop=True)
        
        # Calcular retornos diários manualmente
        closes = []
        for idx, row in prices_df.iterrows():
            close_val = row['close']
            # Se close é um array/series, pegar primeiro valor
            if hasattr(close_val, '__iter__') and not isinstance(close_val, str):
                close_val = list(close_val)[0] if len(list(close_val)) > 0 else None
            closes.append(float(close_val) if close_val is not None else None)
        
        returns = [None]  # Primeiro retorno é None
        for i in range(1, len(closes)):
            if closes[i-1] and closes[i-1] != 0 and closes[i] is not None:
                ret = (closes[i] - closes[i-1]) / closes[i-1]
                returns.append(ret)
            else:
                returns.append(None)
        
        prices_df['daily_return'] = returns
        
        records_inserted = 0
        
        for _, row in prices_df.iterrows():
            # Verificar se já existe
            existing = self.db.query(BenchmarkPrice).filter(
                BenchmarkPrice.symbol == self.symbol,
                BenchmarkPrice.date == row['date']
            ).first()
            
            if existing:
                # Atualizar
                existing.close = row['close']
                existing.daily_return = row['daily_return']
            else:
                # Inserir novo
                record = BenchmarkPrice(
                    symbol=self.symbol,
                    date=row['date'],
                    close=row['close'],
                    daily_return=row['daily_return']
                )
                self.db.add(record)
                records_inserted += 1
        
        self.db.commit()
        logger.info(f"Ingested {records_inserted} benchmark records for {self.symbol}")
        
        return records_inserted
