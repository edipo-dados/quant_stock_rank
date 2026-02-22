"""Cliente para buscar dados fundamentalistas do Yahoo Finance."""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

import yfinance as yf
import pandas as pd

# Importar configuração do yfinance ANTES de usar
from app.ingestion.yfinance_config import configure_yfinance

from app.core.exceptions import DataFetchError

logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """Cliente para buscar dados fundamentalistas do Yahoo Finance."""

    def __init__(self):
        """Inicializa o cliente Yahoo Finance."""
        self.timeout = 30  # segundos
        # Garantir que yfinance está configurado
        configure_yfinance()

    def _convert_to_dict_list(self, df: pd.DataFrame, ticker: str) -> List[Dict]:
        """
        Converte DataFrame do yfinance para lista de dicts (formato compatível com FMP).
        
        Args:
            df: DataFrame com dados financeiros
            ticker: Símbolo do ticker
            
        Returns:
            Lista de dicionários com dados financeiros
        """
        if df is None or df.empty:
            return []
        
        # Transpor para ter períodos como linhas
        df_transposed = df.T
        
        result = []
        for date_idx in df_transposed.index:
            period_data = df_transposed.loc[date_idx].to_dict()
            
            # Adicionar metadados
            period_data['date'] = date_idx.strftime('%Y-%m-%d') if hasattr(date_idx, 'strftime') else str(date_idx)
            period_data['symbol'] = ticker
            
            # Converter valores NaN para None
            period_data = {k: (None if pd.isna(v) else v) for k, v in period_data.items()}
            
            result.append(period_data)
        
        return result

    def fetch_income_statement(
        self, 
        ticker: str, 
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict]:
        """
        Busca demonstração de resultados.
        
        Args:
            ticker: Símbolo do ticker (ex: PETR4.SA para ações brasileiras)
            period: "annual" ou "quarter"
            limit: Número de períodos a buscar
            
        Returns:
            Lista de demonstrações de resultados (mais recente primeiro)
            
        Raises:
            DataFetchError: Se a busca falhar
        """
        try:
            logger.info(f"Fetching income statement for {ticker} (period={period})")
            
            stock = yf.Ticker(ticker)
            
            # Buscar dados baseado no período
            if period == "annual":
                df = stock.income_stmt  # Anual
            elif period == "quarter":
                df = stock.quarterly_income_stmt  # Trimestral
            else:
                raise DataFetchError(f"Invalid period: {period}. Use 'annual' or 'quarter'")
            
            if df is None or df.empty:
                raise DataFetchError(f"No income statement data for {ticker}")
            
            # Converter para formato de lista de dicts
            data = self._convert_to_dict_list(df, ticker)
            
            # Limitar número de períodos
            data = data[:limit]
            
            if not data:
                raise DataFetchError(f"No income statement data for {ticker}")
            
            logger.info(f"Successfully fetched {len(data)} income statements for {ticker}")
            return data
            
        except DataFetchError:
            raise
        except Exception as e:
            error_msg = f"Failed to fetch income statement for {ticker}: {str(e)}"
            logger.error(error_msg)
            raise DataFetchError(error_msg) from e

    def fetch_balance_sheet(
        self, 
        ticker: str, 
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict]:
        """
        Busca balanço patrimonial.
        
        Args:
            ticker: Símbolo do ticker
            period: "annual" ou "quarter"
            limit: Número de períodos a buscar
            
        Returns:
            Lista de balanços patrimoniais (mais recente primeiro)
            
        Raises:
            DataFetchError: Se a busca falhar
        """
        try:
            logger.info(f"Fetching balance sheet for {ticker} (period={period})")
            
            stock = yf.Ticker(ticker)
            
            if period == "annual":
                df = stock.balance_sheet
            elif period == "quarter":
                df = stock.quarterly_balance_sheet
            else:
                raise DataFetchError(f"Invalid period: {period}. Use 'annual' or 'quarter'")
            
            if df is None or df.empty:
                raise DataFetchError(f"No balance sheet data for {ticker}")
            
            data = self._convert_to_dict_list(df, ticker)
            data = data[:limit]
            
            if not data:
                raise DataFetchError(f"No balance sheet data for {ticker}")
            
            logger.info(f"Successfully fetched {len(data)} balance sheets for {ticker}")
            return data
            
        except DataFetchError:
            raise
        except Exception as e:
            error_msg = f"Failed to fetch balance sheet for {ticker}: {str(e)}"
            logger.error(error_msg)
            raise DataFetchError(error_msg) from e

    def fetch_cash_flow(
        self, 
        ticker: str, 
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict]:
        """
        Busca fluxo de caixa.
        
        Args:
            ticker: Símbolo do ticker
            period: "annual" ou "quarter"
            limit: Número de períodos a buscar
            
        Returns:
            Lista de fluxos de caixa (mais recente primeiro)
            
        Raises:
            DataFetchError: Se a busca falhar
        """
        try:
            logger.info(f"Fetching cash flow for {ticker} (period={period})")
            
            stock = yf.Ticker(ticker)
            
            if period == "annual":
                df = stock.cashflow
            elif period == "quarter":
                df = stock.quarterly_cashflow
            else:
                raise DataFetchError(f"Invalid period: {period}. Use 'annual' or 'quarter'")
            
            if df is None or df.empty:
                raise DataFetchError(f"No cash flow data for {ticker}")
            
            data = self._convert_to_dict_list(df, ticker)
            data = data[:limit]
            
            if not data:
                raise DataFetchError(f"No cash flow data for {ticker}")
            
            logger.info(f"Successfully fetched {len(data)} cash flows for {ticker}")
            return data
            
        except DataFetchError:
            raise
        except Exception as e:
            error_msg = f"Failed to fetch cash flow for {ticker}: {str(e)}"
            logger.error(error_msg)
            raise DataFetchError(error_msg) from e

    def fetch_key_metrics(
        self, 
        ticker: str, 
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict]:
        """
        Busca métricas chave (P/E, P/B, ROE, etc).
        
        Args:
            ticker: Símbolo do ticker
            period: "annual" ou "quarter" (ignorado - Yahoo retorna dados atuais)
            limit: Número de períodos a buscar (ignorado - Yahoo retorna snapshot atual)
            
        Returns:
            Lista com um único dict contendo métricas atuais
            
        Raises:
            DataFetchError: Se a busca falhar
        """
        try:
            logger.info(f"Fetching key metrics for {ticker}")
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info:
                raise DataFetchError(f"No key metrics data for {ticker}")
            
            # Extrair métricas relevantes
            metrics = {
                'symbol': ticker,
                'date': datetime.now().strftime('%Y-%m-%d'),
                
                # Valuation ratios
                'peRatio': info.get('trailingPE'),
                'forwardPE': info.get('forwardPE'),
                'priceToBook': info.get('priceToBook'),
                'priceToSales': info.get('priceToSalesTrailing12Months'),
                'enterpriseValueMultiple': info.get('enterpriseToEbitda'),
                
                # Profitability
                'returnOnEquity': info.get('returnOnEquity'),
                'returnOnAssets': info.get('returnOnAssets'),
                'profitMargin': info.get('profitMargins'),
                'operatingMargin': info.get('operatingMargins'),
                'grossMargin': info.get('grossMargins'),
                
                # Financial health
                'debtToEquity': info.get('debtToEquity'),
                'currentRatio': info.get('currentRatio'),
                'quickRatio': info.get('quickRatio'),
                
                # Growth
                'revenueGrowth': info.get('revenueGrowth'),
                'earningsGrowth': info.get('earningsGrowth'),
                
                # Market data
                'marketCap': info.get('marketCap'),
                'enterpriseValue': info.get('enterpriseValue'),
                'beta': info.get('beta'),
                
                # Per share data
                'bookValuePerShare': info.get('bookValue'),
                'earningsPerShare': info.get('trailingEps'),
                'dividendYield': info.get('dividendYield'),
            }
            
            # Retornar como lista com um elemento (compatibilidade com FMP)
            data = [metrics]
            
            logger.info(f"Successfully fetched key metrics for {ticker}")
            return data
            
        except DataFetchError:
            raise
        except Exception as e:
            error_msg = f"Failed to fetch key metrics for {ticker}: {str(e)}"
            logger.error(error_msg)
            raise DataFetchError(error_msg) from e

    def fetch_all_fundamentals(
        self, 
        ticker: str, 
        period: str = "annual",
        delay_seconds: float = 1.0
    ) -> Dict[str, List[Dict]]:
        """
        Busca todos os dados fundamentalistas para um ticker.
        
        Args:
            ticker: Símbolo do ticker
            period: "annual" ou "quarter"
            delay_seconds: Delay entre requisições para evitar rate limiting
            
        Returns:
            Dicionário com chaves: income_statement, balance_sheet, cash_flow, key_metrics
            
        Raises:
            DataFetchError: Se qualquer busca falhar
        """
        try:
            logger.info(f"Fetching all fundamentals for {ticker}")
            
            result = {}
            
            # Income statement
            result["income_statement"] = self.fetch_income_statement(ticker, period)
            time.sleep(delay_seconds)
            
            # Balance sheet
            result["balance_sheet"] = self.fetch_balance_sheet(ticker, period)
            time.sleep(delay_seconds)
            
            # Cash flow
            result["cash_flow"] = self.fetch_cash_flow(ticker, period)
            time.sleep(delay_seconds)
            
            # Key metrics
            result["key_metrics"] = self.fetch_key_metrics(ticker, period)
            
            logger.info(f"Successfully fetched all fundamentals for {ticker}")
            return result
            
        except DataFetchError:
            raise
        except Exception as e:
            error_msg = f"Failed to fetch all fundamentals for {ticker}: {str(e)}"
            logger.error(error_msg)
            raise DataFetchError(error_msg) from e
