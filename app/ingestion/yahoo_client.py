"""Cliente para buscar dados de preços do Yahoo Finance."""

import logging
import time
from datetime import date, datetime
from typing import Dict, List

import pandas as pd
import yfinance as yf

# Importar configuração do yfinance ANTES de usar
from app.ingestion.yfinance_config import configure_yfinance

from app.core.exceptions import DataFetchError

logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """Cliente para buscar dados de preços do Yahoo Finance."""

    def __init__(self):
        """Inicializa o cliente."""
        # Garantir que yfinance está configurado
        configure_yfinance()

    def fetch_daily_prices(
        self, 
        ticker: str, 
        start_date: date, 
        end_date: date
    ) -> pd.DataFrame:
        """
        Busca preços diários para um ticker.
        
        Args:
            ticker: Símbolo do ticker (ex: "PETR4.SA")
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            DataFrame com colunas: date, open, high, low, close, volume, adj_close
            
        Raises:
            DataFetchError: Se a busca falhar
        """
        try:
            logger.info(f"Fetching daily prices for {ticker} from {start_date} to {end_date}")
            
            # Busca dados usando yfinance
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(start=start_date, end=end_date)
            
            if df.empty:
                raise DataFetchError(f"No data returned for ticker {ticker}")
            
            # Renomeia colunas para padrão do sistema
            df = df.reset_index()
            df = df.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Adiciona adj_close (close ajustado)
            # yfinance já retorna close ajustado na coluna Close
            df['adj_close'] = df['close']
            
            # Seleciona apenas as colunas necessárias
            df = df[['date', 'open', 'high', 'low', 'close', 'volume', 'adj_close']]
            
            # Converte date para date (remove timezone se houver)
            df['date'] = pd.to_datetime(df['date']).dt.date
            
            logger.info(f"Successfully fetched {len(df)} days of data for {ticker}")
            return df
            
        except DataFetchError:
            raise
        except Exception as e:
            error_msg = f"Failed to fetch data for {ticker}: {str(e)}"
            logger.error(error_msg)
            raise DataFetchError(error_msg) from e

    def fetch_batch_prices(
        self, 
        tickers: List[str], 
        start_date: date, 
        end_date: date,
        delay_seconds: float = 2.0
    ) -> Dict[str, pd.DataFrame]:
        """
        Busca preços para múltiplos tickers.
        
        Args:
            tickers: Lista de símbolos de tickers
            start_date: Data inicial
            end_date: Data final
            delay_seconds: Delay entre requisições para evitar rate limiting
            
        Returns:
            Dicionário mapeando ticker -> DataFrame de preços
            Tickers que falharam não estarão no dicionário
        """
        results = {}
        
        for i, ticker in enumerate(tickers):
            try:
                # Adiciona delay entre requisições (exceto na primeira)
                if i > 0:
                    logger.debug(f"Waiting {delay_seconds}s before next request...")
                    time.sleep(delay_seconds)
                
                df = self.fetch_daily_prices(ticker, start_date, end_date)
                results[ticker] = df
            except DataFetchError as e:
                logger.warning(f"Skipping {ticker}: {e}")
                continue
        
        logger.info(f"Successfully fetched data for {len(results)}/{len(tickers)} tickers")
        return results
