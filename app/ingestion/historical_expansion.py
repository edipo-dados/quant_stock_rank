"""
Módulo para expansão histórica de preços e fundamentos.

Busca dados históricos completos (5 anos) para todos os tickers da B3
já cadastrados no sistema, garantindo base robusta para backtests.
"""

import logging
import time
from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import yfinance as yf

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.schemas import RawPriceDaily, RawFundamental
from app.ingestion.yfinance_config import configure_yfinance
from app.core.exceptions import DataFetchError

logger = logging.getLogger(__name__)


class HistoricalExpansion:
    """Gerencia expansão histórica de dados."""
    
    def __init__(self, db: Session):
        """
        Inicializa o expansor histórico.
        
        Args:
            db: Sessão do banco de dados
        """
        self.db = db
        configure_yfinance()
    
    def get_all_tickers_from_db(self) -> List[str]:
        """
        Busca todos os tickers únicos já cadastrados no banco.
        
        Returns:
            Lista de tickers no formato TICKER.SA
        """
        logger.info("Buscando tickers cadastrados no banco...")
        
        # Buscar tickers de preços
        price_tickers = self.db.query(RawPriceDaily.ticker).distinct().all()
        price_tickers = [t[0] for t in price_tickers]
        
        # Buscar tickers de fundamentos
        fundamental_tickers = self.db.query(RawFundamental.ticker).distinct().all()
        fundamental_tickers = [t[0] for t in fundamental_tickers]
        
        # Combinar e remover duplicatas
        all_tickers = list(set(price_tickers + fundamental_tickers))
        
        # Validar formato TICKER.SA
        valid_tickers = []
        for ticker in all_tickers:
            if self._validate_ticker_format(ticker):
                valid_tickers.append(ticker)
            else:
                logger.warning(f"Ticker inválido ignorado: {ticker}")
        
        logger.info(f"Total de tickers válidos encontrados: {len(valid_tickers)}")
        return sorted(valid_tickers)
    
    def _validate_ticker_format(self, ticker: str) -> bool:
        """
        Valida formato do ticker (deve ser TICKER.SA).
        
        Args:
            ticker: Ticker a validar
            
        Returns:
            True se válido, False caso contrário
        """
        if not ticker:
            return False
        
        # Deve terminar com .SA
        if not ticker.endswith('.SA'):
            return False
        
        # Parte antes do .SA deve ter 4-6 caracteres alfanuméricos
        base = ticker[:-3]
        if len(base) < 4 or len(base) > 6:
            return False
        
        if not base.isalnum():
            return False
        
        return True
    
    def fetch_full_price_history(
        self,
        ticker: str,
        start_date: str = "2018-01-01",
        mode: str = "full"
    ) -> Dict:
        """
        Busca histórico completo de preços para um ticker.
        
        Args:
            ticker: Ticker no formato TICKER.SA
            start_date: Data inicial (YYYY-MM-DD)
            mode: 'full' ou 'incremental'
            
        Returns:
            Dict com status e estatísticas
        """
        try:
            logger.info(f"Buscando preços históricos para {ticker} desde {start_date}")
            
            # Validar ticker
            if not self._validate_ticker_format(ticker):
                raise DataFetchError(f"Formato de ticker inválido: {ticker}")
            
            # Determinar período
            if mode == "incremental":
                # Buscar última data no banco
                last_price = self.db.query(RawPriceDaily).filter(
                    RawPriceDaily.ticker == ticker
                ).order_by(RawPriceDaily.date.desc()).first()
                
                if last_price:
                    start_date = (last_price.date + timedelta(days=1)).strftime('%Y-%m-%d')
                    logger.info(f"Modo incremental: buscando desde {start_date}")
            
            end_date = date.today().strftime('%Y-%m-%d')
            
            # Buscar dados do yfinance
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(start=start_date, end=end_date)
            
            if df.empty:
                logger.warning(f"Sem dados para {ticker}")
                return {
                    "ticker": ticker,
                    "success": False,
                    "records_inserted": 0,
                    "error": "No data available"
                }
            
            # Processar dados
            df = df.reset_index()
            df['date'] = pd.to_datetime(df['Date']).dt.date
            
            # Remover datas futuras
            today = date.today()
            df = df[df['date'] <= today]
            
            # Remover duplicatas
            df = df.drop_duplicates(subset=['date'], keep='last')
            
            # Ordenar por data
            df = df.sort_values('date')
            
            # Inserir no banco (upsert) - commit por batch para evitar rollback
            records_inserted = 0
            batch_size = 100
            
            for idx, row in df.iterrows():
                try:
                    # Verificar se já existe
                    existing = self.db.query(RawPriceDaily).filter(
                        RawPriceDaily.ticker == ticker,
                        RawPriceDaily.date == row['date']
                    ).first()
                    
                    if existing:
                        # Atualizar
                        existing.open = float(row['Open'])
                        existing.high = float(row['High'])
                        existing.low = float(row['Low'])
                        existing.close = float(row['Close'])
                        existing.volume = int(row['Volume'])
                        existing.adj_close = float(row['Close'])  # yfinance já retorna ajustado
                    else:
                        # Inserir novo
                        price_record = RawPriceDaily(
                            ticker=ticker,
                            date=row['date'],
                            open=float(row['Open']),
                            high=float(row['High']),
                            low=float(row['Low']),
                            close=float(row['Close']),
                            volume=int(row['Volume']),
                            adj_close=float(row['Close'])
                        )
                        self.db.add(price_record)
                    
                    records_inserted += 1
                    
                    # Commit em batches
                    if records_inserted % batch_size == 0:
                        try:
                            self.db.commit()
                        except Exception as commit_error:
                            logger.warning(f"Erro no commit batch para {ticker}: {commit_error}")
                            self.db.rollback()
                    
                except Exception as e:
                    logger.warning(f"Erro ao processar registro para {ticker} em {row['date']}: {e}")
                    self.db.rollback()
                    continue
            
            # Commit final
            try:
                self.db.commit()
            except Exception as e:
                logger.warning(f"Erro no commit final para {ticker}: {e}")
                self.db.rollback()
            
            logger.info(f"✓ {ticker}: {records_inserted} registros inseridos/atualizados")
            
            return {
                "ticker": ticker,
                "success": True,
                "records_inserted": records_inserted,
                "start_date": df['date'].min(),
                "end_date": df['date'].max(),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"✗ {ticker}: {str(e)}")
            return {
                "ticker": ticker,
                "success": False,
                "records_inserted": 0,
                "error": str(e)
            }
    
    def fetch_full_fundamentals_history(
        self,
        ticker: str
    ) -> Dict:
        """
        Busca histórico completo de fundamentos (últimos 5 anos).
        
        Args:
            ticker: Ticker no formato TICKER.SA
            
        Returns:
            Dict com status e estatísticas
        """
        try:
            logger.info(f"Buscando fundamentos históricos para {ticker}")
            
            # Validar ticker
            if not self._validate_ticker_format(ticker):
                raise DataFetchError(f"Formato de ticker inválido: {ticker}")
            
            ticker_obj = yf.Ticker(ticker)
            
            # Buscar demonstrações financeiras
            income_stmt = ticker_obj.income_stmt  # Anual
            balance_sheet = ticker_obj.balance_sheet  # Anual
            cashflow = ticker_obj.cashflow  # Anual
            
            if income_stmt is None or income_stmt.empty:
                logger.warning(f"Sem fundamentos para {ticker}")
                return {
                    "ticker": ticker,
                    "success": False,
                    "records_inserted": 0,
                    "years_available": 0,
                    "error": "No fundamental data available"
                }
            
            # Processar dados por ano fiscal
            records_inserted = 0
            years_available = 0
            
            for date_col in income_stmt.columns:
                try:
                    fiscal_year = date_col.year
                    period_end_date = date_col.date()
                    
                    # Extrair dados
                    revenue = self._safe_get(income_stmt, 'Total Revenue', date_col)
                    net_income = self._safe_get(income_stmt, 'Net Income', date_col)
                    ebitda = self._safe_get(income_stmt, 'EBITDA', date_col)
                    
                    total_assets = self._safe_get(balance_sheet, 'Total Assets', date_col)
                    total_debt = self._safe_get(balance_sheet, 'Total Debt', date_col)
                    shareholders_equity = self._safe_get(balance_sheet, 'Stockholders Equity', date_col)
                    
                    operating_cashflow = self._safe_get(cashflow, 'Operating Cash Flow', date_col)
                    free_cashflow = self._safe_get(cashflow, 'Free Cash Flow', date_col)
                    
                    # Calcular métricas derivadas
                    eps = None
                    if net_income and shareholders_equity and shareholders_equity != 0:
                        # Estimativa simples de EPS (precisa de shares outstanding)
                        eps = net_income / 1_000_000  # Placeholder
                    
                    # Verificar se já existe
                    existing = self.db.query(RawFundamental).filter(
                        RawFundamental.ticker == ticker,
                        RawFundamental.period_end_date == period_end_date,
                        RawFundamental.period_type == 'annual'
                    ).first()
                    
                    if existing:
                        # Atualizar
                        existing.revenue = revenue
                        existing.net_income = net_income
                        existing.ebitda = ebitda
                        existing.total_assets = total_assets
                        existing.total_debt = total_debt
                        existing.shareholders_equity = shareholders_equity
                        existing.operating_cash_flow = operating_cashflow
                        existing.free_cash_flow = free_cashflow
                        existing.eps = eps
                        existing.fetched_at = datetime.utcnow()
                    else:
                        # Inserir novo
                        fundamental = RawFundamental(
                            ticker=ticker,
                            period_end_date=period_end_date,
                            period_type='annual',
                            revenue=revenue,
                            net_income=net_income,
                            ebitda=ebitda,
                            total_assets=total_assets,
                            total_debt=total_debt,
                            shareholders_equity=shareholders_equity,
                            operating_cash_flow=operating_cashflow,
                            free_cash_flow=free_cashflow,
                            eps=eps,
                            fetched_at=datetime.utcnow()
                        )
                        self.db.add(fundamental)
                    
                    records_inserted += 1
                    years_available += 1
                    
                except Exception as e:
                    logger.warning(f"Erro ao processar ano {date_col} para {ticker}: {e}")
                    self.db.rollback()
                    continue
            
            # Commit final
            try:
                self.db.commit()
            except Exception as e:
                logger.warning(f"Erro no commit para {ticker}: {e}")
                self.db.rollback()
            
            if years_available < 3:
                logger.warning(f"⚠ {ticker}: apenas {years_available} anos disponíveis (< 3)")
            else:
                logger.info(f"✓ {ticker}: {records_inserted} registros, {years_available} anos")
            
            return {
                "ticker": ticker,
                "success": True,
                "records_inserted": records_inserted,
                "years_available": years_available,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"✗ {ticker}: {str(e)}")
            return {
                "ticker": ticker,
                "success": False,
                "records_inserted": 0,
                "years_available": 0,
                "error": str(e)
            }
    
    def _safe_get(self, df: pd.DataFrame, field: str, column) -> Optional[float]:
        """
        Extrai valor de forma segura do DataFrame.
        
        Args:
            df: DataFrame
            field: Nome do campo
            column: Coluna (data)
            
        Returns:
            Valor float ou None
        """
        try:
            if df is None or df.empty:
                return None
            
            if field not in df.index:
                return None
            
            if column not in df.columns:
                return None
            
            value = df.loc[field, column]
            
            if pd.isna(value):
                return None
            
            return float(value)
        except:
            return None
    
    def expand_prices_parallel(
        self,
        tickers: List[str],
        start_date: str = "2018-01-01",
        mode: str = "full",
        max_workers: int = 5,
        delay_seconds: float = 1.0
    ) -> Dict:
        """
        Expande preços históricos em paralelo.
        
        Args:
            tickers: Lista de tickers
            start_date: Data inicial
            mode: 'full' ou 'incremental'
            max_workers: Número máximo de threads
            delay_seconds: Delay entre requisições
            
        Returns:
            Dict com estatísticas
        """
        logger.info(f"Expandindo preços para {len(tickers)} tickers (paralelo, {max_workers} workers)")
        
        results = []
        total_records = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submeter tarefas
            future_to_ticker = {
                executor.submit(self.fetch_full_price_history, ticker, start_date, mode): ticker
                for ticker in tickers
            }
            
            # Processar resultados conforme completam
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    result = future.result()
                    results.append(result)
                    if result['success']:
                        total_records += result['records_inserted']
                    
                    # Delay entre requisições
                    time.sleep(delay_seconds)
                    
                except Exception as e:
                    logger.error(f"Erro ao processar {ticker}: {e}")
                    results.append({
                        "ticker": ticker,
                        "success": False,
                        "records_inserted": 0,
                        "error": str(e)
                    })
        
        success_count = sum(1 for r in results if r['success'])
        failed_count = len(results) - success_count
        
        logger.info(f"Preços: {success_count} sucesso, {failed_count} falhas, {total_records} registros")
        
        return {
            "total_tickers": len(tickers),
            "success_count": success_count,
            "failed_count": failed_count,
            "total_records": total_records,
            "results": results
        }
    
    def expand_fundamentals_parallel(
        self,
        tickers: List[str],
        max_workers: int = 5,
        delay_seconds: float = 2.0
    ) -> Dict:
        """
        Expande fundamentos históricos em paralelo.
        
        Args:
            tickers: Lista de tickers
            max_workers: Número máximo de threads
            delay_seconds: Delay entre requisições
            
        Returns:
            Dict com estatísticas
        """
        logger.info(f"Expandindo fundamentos para {len(tickers)} tickers (paralelo, {max_workers} workers)")
        
        results = []
        total_records = 0
        insufficient_tickers = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ticker = {
                executor.submit(self.fetch_full_fundamentals_history, ticker): ticker
                for ticker in tickers
            }
            
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    result = future.result()
                    results.append(result)
                    if result['success']:
                        total_records += result['records_inserted']
                        if result['years_available'] < 3:
                            insufficient_tickers.append({
                                "ticker": ticker,
                                "years_available": result['years_available']
                            })
                    
                    time.sleep(delay_seconds)
                    
                except Exception as e:
                    logger.error(f"Erro ao processar {ticker}: {e}")
                    results.append({
                        "ticker": ticker,
                        "success": False,
                        "records_inserted": 0,
                        "years_available": 0,
                        "error": str(e)
                    })
        
        success_count = sum(1 for r in results if r['success'])
        failed_count = len(results) - success_count
        
        logger.info(f"Fundamentos: {success_count} sucesso, {failed_count} falhas, {total_records} registros")
        logger.info(f"Tickers com < 3 anos: {len(insufficient_tickers)}")
        
        return {
            "total_tickers": len(tickers),
            "success_count": success_count,
            "failed_count": failed_count,
            "total_records": total_records,
            "insufficient_tickers": insufficient_tickers,
            "results": results
        }
