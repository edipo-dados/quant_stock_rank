"""
Detecção de regime de mercado baseado em média móvel.

Usa média móvel de 200 dias do IBOVESPA para determinar regime:
- Bullish: Preço > MA200 → Exposição 100%
- Bearish: Preço <= MA200 → Exposição 50%
"""

import pandas as pd
import logging
from typing import Dict, Optional
from datetime import date
from sqlalchemy.orm import Session

from app.backtest.benchmark import BenchmarkManager

logger = logging.getLogger(__name__)


class MarketRegimeFilter:
    """
    Filtro de regime de mercado baseado em média móvel.
    """
    
    def __init__(
        self,
        db: Session,
        ma_period: int = 200,
        bullish_exposure: float = 1.0,
        bearish_exposure: float = 0.5,
        benchmark_symbol: str = "^BVSP"
    ):
        """
        Inicializa filtro de regime.
        
        Args:
            db: Sessão do banco de dados
            ma_period: Período da média móvel (default: 200 dias)
            bullish_exposure: Exposição em mercado de alta (default: 1.0 = 100%)
            bearish_exposure: Exposição em mercado de baixa (default: 0.5 = 50%)
            benchmark_symbol: Símbolo do benchmark (default: ^BVSP)
        """
        self.db = db
        self.ma_period = ma_period
        self.bullish_exposure = bullish_exposure
        self.bearish_exposure = bearish_exposure
        self.benchmark_manager = BenchmarkManager(db, symbol=benchmark_symbol)
        self.ma_cache = {}  # Cache de médias móveis
    
    def calculate_moving_average(
        self,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Calcula média móvel do benchmark.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            DataFrame com colunas ['date', 'price', 'ma']
        """
        # Buscar dados do benchmark
        # Adicionar período extra para calcular MA
        from datetime import timedelta
        extended_start = start_date - timedelta(days=self.ma_period * 2)
        
        benchmark_data = self.benchmark_manager.get_benchmark_data(
            start_date=extended_start,
            end_date=end_date
        )
        
        if not benchmark_data:
            logger.warning("No benchmark data available for MA calculation")
            return pd.DataFrame()
        
        # Converter para DataFrame
        df = pd.DataFrame(benchmark_data)
        df = df.sort_values('date')
        
        # Calcular média móvel
        df['ma'] = df['adj_close'].rolling(window=self.ma_period, min_periods=self.ma_period).mean()
        
        # Filtrar para período solicitado
        df = df[df['date'] >= start_date]
        
        # Renomear colunas
        df = df.rename(columns={'adj_close': 'price'})
        
        return df[['date', 'price', 'ma']]
    
    def get_regime(self, current_date: date) -> str:
        """
        Determina regime de mercado para uma data.
        
        Args:
            current_date: Data para verificar regime
            
        Returns:
            'bullish' ou 'bearish'
        """
        # Verificar cache
        if current_date in self.ma_cache:
            return self.ma_cache[current_date]
        
        # Buscar dados do benchmark
        from datetime import timedelta
        start_date = current_date - timedelta(days=self.ma_period * 2)
        
        df = self.calculate_moving_average(start_date, current_date)
        
        if df.empty:
            logger.warning(f"No MA data for {current_date}, assuming bullish")
            return 'bullish'
        
        # Pegar último registro
        last_row = df.iloc[-1]
        
        if pd.isna(last_row['ma']):
            logger.warning(f"MA not available for {current_date}, assuming bullish")
            return 'bullish'
        
        # Determinar regime
        if last_row['price'] > last_row['ma']:
            regime = 'bullish'
        else:
            regime = 'bearish'
        
        # Cachear resultado
        self.ma_cache[current_date] = regime
        
        logger.info(
            f"Market regime on {current_date}: {regime.upper()} "
            f"(Price={last_row['price']:.2f}, MA{self.ma_period}={last_row['ma']:.2f})"
        )
        
        return regime
    
    def get_exposure(self, current_date: date) -> float:
        """
        Retorna exposição recomendada para uma data.
        
        Args:
            current_date: Data para verificar exposição
            
        Returns:
            Multiplicador de exposição (0.5 a 1.0)
        """
        regime = self.get_regime(current_date)
        
        if regime == 'bullish':
            exposure = self.bullish_exposure
        else:
            exposure = self.bearish_exposure
        
        return exposure
    
    def apply_regime_filter(
        self,
        weights: Dict[str, float],
        current_date: date
    ) -> Dict[str, float]:
        """
        Aplica filtro de regime aos pesos do portfólio.
        
        Args:
            weights: Dicionário {ticker: weight} original
            current_date: Data atual
            
        Returns:
            Dicionário {ticker: adjusted_weight}
        """
        exposure = self.get_exposure(current_date)
        
        # Aplicar multiplicador de exposição
        adjusted_weights = {
            ticker: weight * exposure
            for ticker, weight in weights.items()
        }
        
        # Calcular cash position
        total_invested = sum(adjusted_weights.values())
        cash_position = 1.0 - total_invested
        
        logger.info(
            f"Applied regime filter: exposure={exposure:.1%}, "
            f"invested={total_invested:.1%}, cash={cash_position:.1%}"
        )
        
        return adjusted_weights
    
    def get_regime_history(
        self,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Retorna histórico de regimes de mercado.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            DataFrame com colunas ['date', 'price', 'ma', 'regime', 'exposure']
        """
        df = self.calculate_moving_average(start_date, end_date)
        
        if df.empty:
            return df
        
        # Determinar regime para cada data
        df['regime'] = df.apply(
            lambda row: 'bullish' if row['price'] > row['ma'] else 'bearish',
            axis=1
        )
        
        # Adicionar exposição
        df['exposure'] = df['regime'].apply(
            lambda r: self.bullish_exposure if r == 'bullish' else self.bearish_exposure
        )
        
        return df
