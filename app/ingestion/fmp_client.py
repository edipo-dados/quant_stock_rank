"""Cliente para buscar dados fundamentalistas do Financial Modeling Prep."""

import logging
from typing import Dict, List, Optional

import requests

from app.core.exceptions import DataFetchError

logger = logging.getLogger(__name__)


class FMPClient:
    """Cliente para buscar dados fundamentalistas do FMP."""

    def __init__(self, api_key: str):
        """
        Inicializa o cliente FMP.
        
        Args:
            api_key: Chave de API do Financial Modeling Prep
        """
        self.api_key = api_key
        # ATUALIZADO: Novo base URL (stable API)
        self.base_url = "https://financialmodelingprep.com/stable"
        self.timeout = 30  # segundos

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Faz requisição à API do FMP.
        
        Args:
            endpoint: Endpoint da API (ex: "/income-statement/AAPL")
            params: Parâmetros adicionais da query
            
        Returns:
            Resposta JSON da API
            
        Raises:
            DataFetchError: Se a requisição falhar
        """
        if params is None:
            params = {}
        
        # Adiciona API key aos parâmetros
        params['apikey'] = self.api_key
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.debug(f"Making request to {url}")
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # FMP retorna erro como dict com chave "Error Message"
            if isinstance(data, dict) and "Error Message" in data:
                raise DataFetchError(f"FMP API error: {data['Error Message']}")
            
            return data
            
        except requests.exceptions.Timeout:
            error_msg = f"Request timeout for {url}"
            logger.error(error_msg)
            raise DataFetchError(error_msg)
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error for {url}: {e}"
            logger.error(error_msg)
            raise DataFetchError(error_msg) from e
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed for {url}: {e}"
            logger.error(error_msg)
            raise DataFetchError(error_msg) from e
        except ValueError as e:
            error_msg = f"Invalid JSON response from {url}: {e}"
            logger.error(error_msg)
            raise DataFetchError(error_msg) from e

    def fetch_income_statement(
        self, 
        ticker: str, 
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict]:
        """
        Busca demonstração de resultados.
        
        Args:
            ticker: Símbolo do ticker
            period: "annual" ou "quarter"
            limit: Número de períodos a buscar
            
        Returns:
            Lista de demonstrações de resultados (mais recente primeiro)
            
        Raises:
            DataFetchError: Se a busca falhar
        """
        try:
            logger.info(f"Fetching income statement for {ticker} (period={period})")
            
            endpoint = f"/income-statement/{ticker}"
            params = {"period": period, "limit": limit}
            
            data = self._make_request(endpoint, params)
            
            if not isinstance(data, list):
                raise DataFetchError(f"Unexpected response format for {ticker}")
            
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
            
            endpoint = f"/balance-sheet-statement/{ticker}"
            params = {"period": period, "limit": limit}
            
            data = self._make_request(endpoint, params)
            
            if not isinstance(data, list):
                raise DataFetchError(f"Unexpected response format for {ticker}")
            
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
            
            endpoint = f"/cash-flow-statement/{ticker}"
            params = {"period": period, "limit": limit}
            
            data = self._make_request(endpoint, params)
            
            if not isinstance(data, list):
                raise DataFetchError(f"Unexpected response format for {ticker}")
            
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
            period: "annual" ou "quarter"
            limit: Número de períodos a buscar
            
        Returns:
            Lista de métricas chave (mais recente primeiro)
            
        Raises:
            DataFetchError: Se a busca falhar
        """
        try:
            logger.info(f"Fetching key metrics for {ticker} (period={period})")
            
            endpoint = f"/key-metrics/{ticker}"
            params = {"period": period, "limit": limit}
            
            data = self._make_request(endpoint, params)
            
            if not isinstance(data, list):
                raise DataFetchError(f"Unexpected response format for {ticker}")
            
            if not data:
                raise DataFetchError(f"No key metrics data for {ticker}")
            
            logger.info(f"Successfully fetched {len(data)} key metrics for {ticker}")
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
        period: str = "annual"
    ) -> Dict[str, List[Dict]]:
        """
        Busca todos os dados fundamentalistas para um ticker.
        
        Args:
            ticker: Símbolo do ticker
            period: "annual" ou "quarter"
            
        Returns:
            Dicionário com chaves: income_statement, balance_sheet, cash_flow, key_metrics
            
        Raises:
            DataFetchError: Se qualquer busca falhar
        """
        try:
            logger.info(f"Fetching all fundamentals for {ticker}")
            
            result = {
                "income_statement": self.fetch_income_statement(ticker, period),
                "balance_sheet": self.fetch_balance_sheet(ticker, period),
                "cash_flow": self.fetch_cash_flow(ticker, period),
                "key_metrics": self.fetch_key_metrics(ticker, period)
            }
            
            logger.info(f"Successfully fetched all fundamentals for {ticker}")
            return result
            
        except DataFetchError:
            raise
        except Exception as e:
            error_msg = f"Failed to fetch all fundamentals for {ticker}: {str(e)}"
            logger.error(error_msg)
            raise DataFetchError(error_msg) from e
