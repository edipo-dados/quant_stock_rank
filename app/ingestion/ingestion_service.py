"""Serviço de orquestração de ingestão de dados."""

import logging
from datetime import date, timedelta
from typing import Dict, List

from sqlalchemy.orm import Session

from app.core.exceptions import DataFetchError
from app.ingestion.yahoo_client import YahooFinanceClient
from app.ingestion.yahoo_finance_client import YahooFinanceClient as YahooFundamentalsClient
from app.models.schemas import RawPriceDaily, RawFundamental

logger = logging.getLogger(__name__)


class IngestionService:
    """Orquestra a ingestão de dados e persistência."""

    def __init__(
        self,
        yahoo_client: YahooFinanceClient,
        yahoo_fundamentals_client: YahooFundamentalsClient,
        db_session: Session
    ):
        """
        Inicializa o serviço de ingestão.
        
        Args:
            yahoo_client: Cliente para buscar dados de preços
            yahoo_fundamentals_client: Cliente para buscar dados fundamentalistas
            db_session: Sessão do banco de dados
        """
        self.yahoo_client = yahoo_client
        self.yahoo_fundamentals_client = yahoo_fundamentals_client
        self.db = db_session

    def ingest_prices(
        self, 
        tickers: List[str], 
        lookback_days: int = 365
    ) -> Dict[str, any]:
        """
        Ingere preços diários para lista de tickers.
        
        - Busca dados do Yahoo Finance
        - Armazena em raw_prices_daily
        - Registra erros sem interromper o processo
        
        Args:
            tickers: Lista de símbolos de tickers
            lookback_days: Número de dias históricos a buscar
            
        Returns:
            Dicionário com estatísticas: 
            {
                "success": [lista de tickers com sucesso],
                "failed": [lista de dicts com ticker e erro],
                "total_records": número total de registros inseridos
            }
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)
        
        results = {
            "success": [],
            "failed": [],
            "total_records": 0
        }
        
        logger.info(f"Starting price ingestion for {len(tickers)} tickers")
        logger.info(f"Date range: {start_date} to {end_date}")
        
        for ticker in tickers:
            try:
                # Busca dados do Yahoo Finance
                df = self.yahoo_client.fetch_daily_prices(ticker, start_date, end_date)
                
                # Persiste cada linha no banco
                records_inserted = 0
                for _, row in df.iterrows():
                    try:
                        # Verifica se registro já existe
                        existing = self.db.query(RawPriceDaily).filter_by(
                            ticker=ticker,
                            date=row['date']
                        ).first()
                        
                        if existing:
                            # Atualiza registro existente
                            existing.open = float(row['open'])
                            existing.high = float(row['high'])
                            existing.low = float(row['low'])
                            existing.close = float(row['close'])
                            existing.volume = int(row['volume'])
                            existing.adj_close = float(row['adj_close'])
                        else:
                            # Cria novo registro
                            price_record = RawPriceDaily(
                                ticker=ticker,
                                date=row['date'],
                                open=float(row['open']),
                                high=float(row['high']),
                                low=float(row['low']),
                                close=float(row['close']),
                                volume=int(row['volume']),
                                adj_close=float(row['adj_close'])
                            )
                            self.db.add(price_record)
                        
                        records_inserted += 1
                    except Exception as e:
                        logger.warning(f"Failed to insert record for {ticker} on {row['date']}: {e}")
                        continue
                
                # Commit após processar todos os registros do ticker
                self.db.commit()
                
                results["success"].append(ticker)
                results["total_records"] += records_inserted
                logger.info(f"Successfully ingested {records_inserted} price records for {ticker}")
                
            except DataFetchError as e:
                logger.warning(f"Failed to fetch prices for {ticker}: {e}")
                results["failed"].append({"ticker": ticker, "error": str(e)})
                continue
            except Exception as e:
                logger.error(f"Unexpected error ingesting prices for {ticker}: {e}")
                results["failed"].append({"ticker": ticker, "error": str(e)})
                # Rollback em caso de erro inesperado
                self.db.rollback()
                continue
        
        logger.info(
            f"Price ingestion complete: {len(results['success'])} succeeded, "
            f"{len(results['failed'])} failed, {results['total_records']} total records"
        )
        
        return results

    def ingest_fundamentals(
        self, 
        tickers: List[str],
        period: str = "annual"
    ) -> Dict[str, any]:
        """
        Ingere dados fundamentalistas para lista de tickers.
        
        - Busca dados do Yahoo Finance
        - Armazena em raw_fundamentals
        - Registra erros sem interromper o processo
        
        Args:
            tickers: Lista de símbolos de tickers
            period: "annual" ou "quarter"
            
        Returns:
            Dicionário com estatísticas:
            {
                "success": [lista de tickers com sucesso],
                "failed": [lista de dicts com ticker e erro],
                "total_records": número total de registros inseridos
            }
        """
        results = {
            "success": [],
            "failed": [],
            "total_records": 0
        }
        
        logger.info(f"Starting fundamentals ingestion for {len(tickers)} tickers")
        
        for ticker in tickers:
            try:
                # Busca todos os dados fundamentalistas do Yahoo Finance
                fundamentals = self.yahoo_fundamentals_client.fetch_all_fundamentals(ticker, period)
                
                # Processa cada período (assumindo que todos têm o mesmo número de períodos)
                income_statements = fundamentals.get("income_statement", [])
                balance_sheets = fundamentals.get("balance_sheet", [])
                cash_flows = fundamentals.get("cash_flow", [])
                key_metrics = fundamentals.get("key_metrics", [])
                
                records_inserted = 0
                
                # Itera pelos períodos (assumindo que estão alinhados por data)
                for i in range(len(income_statements)):
                    try:
                        income = income_statements[i] if i < len(income_statements) else {}
                        balance = balance_sheets[i] if i < len(balance_sheets) else {}
                        cash = cash_flows[i] if i < len(cash_flows) else {}
                        metrics = key_metrics[i] if i < len(key_metrics) else {}
                        
                        # Extrai data do período
                        period_date_str = income.get("date") or balance.get("date") or cash.get("date")
                        if not period_date_str:
                            logger.warning(f"No date found for {ticker} period {i}")
                            continue
                        
                        # Converte string de data para objeto date
                        from datetime import datetime
                        period_date = datetime.strptime(period_date_str, "%Y-%m-%d").date()
                        
                        # Verifica se registro já existe
                        existing = self.db.query(RawFundamental).filter_by(
                            ticker=ticker,
                            period_end_date=period_date,
                            period_type=period
                        ).first()
                        
                        if existing:
                            # Atualiza registro existente
                            self._update_fundamental_record(existing, income, balance, cash, metrics)
                        else:
                            # Cria novo registro
                            fundamental_record = self._create_fundamental_record(
                                ticker, period_date, period, income, balance, cash, metrics
                            )
                            self.db.add(fundamental_record)
                        
                        records_inserted += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to insert fundamental record for {ticker} period {i}: {e}")
                        continue
                
                # Commit após processar todos os registros do ticker
                self.db.commit()
                
                results["success"].append(ticker)
                results["total_records"] += records_inserted
                logger.info(f"Successfully ingested {records_inserted} fundamental records for {ticker}")
                
            except DataFetchError as e:
                logger.warning(f"Failed to fetch fundamentals for {ticker}: {e}")
                results["failed"].append({"ticker": ticker, "error": str(e)})
                continue
            except Exception as e:
                logger.error(f"Unexpected error ingesting fundamentals for {ticker}: {e}")
                results["failed"].append({"ticker": ticker, "error": str(e)})
                # Rollback em caso de erro inesperado
                self.db.rollback()
                continue
        
        logger.info(
            f"Fundamentals ingestion complete: {len(results['success'])} succeeded, "
            f"{len(results['failed'])} failed, {results['total_records']} total records"
        )
        
        return results

    def _create_fundamental_record(
        self,
        ticker: str,
        period_date: date,
        period_type: str,
        income: Dict,
        balance: Dict,
        cash: Dict,
        metrics: Dict
    ) -> RawFundamental:
        """
        Cria um registro de dados fundamentalistas.
        
        Args:
            ticker: Símbolo do ticker
            period_date: Data do período
            period_type: "annual" ou "quarter"
            income: Dados da demonstração de resultados
            balance: Dados do balanço patrimonial
            cash: Dados do fluxo de caixa
            metrics: Métricas chave
            
        Returns:
            Objeto RawFundamental
        """
        return RawFundamental(
            ticker=ticker,
            period_end_date=period_date,
            period_type=period_type,
            # Income Statement - Campos corretos do Yahoo Finance
            revenue=income.get("Total Revenue"),
            net_income=income.get("Net Income"),
            ebitda=income.get("EBITDA"),
            eps=income.get("Basic EPS"),
            # Balance Sheet - Campos corretos do Yahoo Finance
            total_assets=balance.get("Total Assets"),
            total_debt=balance.get("Total Debt"),
            shareholders_equity=balance.get("Stockholders Equity"),
            book_value_per_share=metrics.get("bookValuePerShare"),
            # Cash Flow - Campos corretos do Yahoo Finance
            operating_cash_flow=cash.get("Operating Cash Flow"),
            free_cash_flow=cash.get("Free Cash Flow"),
            # Metrics - Do Yahoo Finance info
            market_cap=metrics.get("marketCap"),
            enterprise_value=metrics.get("enterpriseValue")
        )

    def _update_fundamental_record(
        self,
        record: RawFundamental,
        income: Dict,
        balance: Dict,
        cash: Dict,
        metrics: Dict
    ):
        """
        Atualiza um registro existente de dados fundamentalistas.
        
        Args:
            record: Registro existente a ser atualizado
            income: Dados da demonstração de resultados
            balance: Dados do balanço patrimonial
            cash: Dados do fluxo de caixa
            metrics: Métricas chave
        """
        # Income Statement - Campos corretos do Yahoo Finance
        record.revenue = income.get("Total Revenue")
        record.net_income = income.get("Net Income")
        record.ebitda = income.get("EBITDA")
        record.eps = income.get("Basic EPS")
        # Balance Sheet - Campos corretos do Yahoo Finance
        record.total_assets = balance.get("Total Assets")
        record.total_debt = balance.get("Total Debt")
        record.shareholders_equity = balance.get("Stockholders Equity")
        record.book_value_per_share = metrics.get("bookValuePerShare")
        # Cash Flow - Campos corretos do Yahoo Finance
        record.operating_cash_flow = cash.get("Operating Cash Flow")
        record.free_cash_flow = cash.get("Free Cash Flow")
        # Metrics - Do Yahoo Finance info
        record.market_cap = metrics.get("marketCap")
        record.enterprise_value = metrics.get("enterpriseValue")
