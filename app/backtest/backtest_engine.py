"""
Engine de backtest para estratégias quantitativas.

Implementa backtest mensal com:
- Snapshot mensal do ranking
- Seleção Top N
- Equal weight ou score weighted
- Rebalanceamento mensal
- Cálculo de métricas (CAGR, Sharpe, Max Drawdown, etc.)
"""

from typing import List, Dict, Optional
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
import logging

from sqlalchemy.orm import Session
from app.models.schemas import ScoreDaily, RankingHistory, BacktestResult
from app.models.database import SessionLocal
from app.backtest.portfolio import Portfolio
from app.backtest.metrics import PerformanceMetrics
from app.ingestion.yahoo_client import YahooFinanceClient

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Engine para executar backtests de estratégias quantitativas.
    
    Fluxo:
    1. Carregar histórico de rankings (ou criar snapshots mensais)
    2. Para cada mês:
       a. Selecionar Top N ativos
       b. Calcular pesos (equal ou score weighted)
       c. Buscar retornos do mês seguinte
       d. Calcular retorno do portfólio
    3. Calcular métricas de performance
    4. Salvar resultados
    """
    
    def __init__(
        self,
        start_date: date,
        end_date: date,
        top_n: int = 10,
        rebalance_frequency: str = 'monthly',
        weight_method: str = 'equal',
        use_smoothing: bool = False,
        risk_free_rate: float = 0.0
    ):
        """
        Inicializa engine de backtest.
        
        Args:
            start_date: Data inicial do backtest
            end_date: Data final do backtest
            top_n: Número de ativos a selecionar
            rebalance_frequency: Frequência de rebalanceamento ('monthly')
            weight_method: Método de ponderação ('equal' ou 'score_weighted')
            use_smoothing: Se usa score suavizado
            risk_free_rate: Taxa livre de risco anualizada (ex: 0.05 para 5%)
        """
        self.start_date = start_date
        self.end_date = end_date
        self.top_n = top_n
        self.rebalance_frequency = rebalance_frequency
        self.weight_method = weight_method
        self.use_smoothing = use_smoothing
        self.risk_free_rate = risk_free_rate
        
        self.yahoo_client = YahooFinanceClient()
        
        logger.info(
            f"BacktestEngine initialized: {start_date} to {end_date}, "
            f"top_n={top_n}, weight={weight_method}, smoothing={use_smoothing}"
        )
    
    def get_monthly_dates(self) -> List[date]:
        """
        Gera lista de datas mensais para rebalanceamento.
        
        Returns:
            Lista de datas (último dia útil de cada mês)
        """
        dates = []
        current = self.start_date
        
        while current <= self.end_date:
            # Último dia do mês
            next_month = current + relativedelta(months=1)
            last_day = next_month - relativedelta(days=1)
            
            dates.append(last_day)
            current = next_month
        
        return dates
    
    def create_monthly_snapshots(self, db: Session) -> None:
        """
        Cria snapshots mensais do ranking na tabela ranking_history.
        
        Para cada último dia útil do mês, copia o ranking mais recente
        disponível para a tabela de histórico.
        
        Args:
            db: Sessão do banco de dados
        """
        logger.info("Creating monthly snapshots...")
        
        monthly_dates = self.get_monthly_dates()
        snapshots_created = 0
        
        for snapshot_date in monthly_dates:
            # Verificar se snapshot já existe
            existing = db.query(RankingHistory).filter(
                RankingHistory.date == snapshot_date
            ).first()
            
            if existing:
                logger.debug(f"Snapshot for {snapshot_date} already exists, skipping")
                continue
            
            # Buscar ranking mais recente até essa data
            scores = db.query(ScoreDaily).filter(
                ScoreDaily.date <= snapshot_date,
                ScoreDaily.passed_eligibility == True
            ).order_by(ScoreDaily.date.desc()).limit(100).all()
            
            if not scores:
                logger.warning(f"No scores found for snapshot date {snapshot_date}")
                continue
            
            # Agrupar por ticker (pegar o mais recente de cada)
            ticker_scores = {}
            for score in scores:
                if score.ticker not in ticker_scores:
                    ticker_scores[score.ticker] = score
            
            # Criar snapshots
            for ticker, score in ticker_scores.items():
                snapshot = RankingHistory(
                    date=snapshot_date,
                    ticker=ticker,
                    final_score=score.final_score,
                    final_score_smoothed=score.final_score_smoothed,
                    momentum_score=score.momentum_score,
                    quality_score=score.quality_score,
                    value_score=score.value_score,
                    rank=score.rank
                )
                db.add(snapshot)
            
            snapshots_created += 1
            logger.info(f"Created snapshot for {snapshot_date} with {len(ticker_scores)} assets")
        
        db.commit()
        logger.info(f"Created {snapshots_created} monthly snapshots")
    
    def get_ranking_snapshot(
        self,
        db: Session,
        snapshot_date: date
    ) -> pd.DataFrame:
        """
        Obtém snapshot do ranking para uma data específica.
        
        Args:
            db: Sessão do banco de dados
            snapshot_date: Data do snapshot
            
        Returns:
            DataFrame com colunas ['ticker', 'final_score', 'final_score_smoothed', 'rank']
        """
        # Buscar snapshot
        snapshots = db.query(RankingHistory).filter(
            RankingHistory.date == snapshot_date
        ).all()
        
        if not snapshots:
            logger.warning(f"No snapshot found for {snapshot_date}")
            return pd.DataFrame()
        
        # Converter para DataFrame
        data = []
        for snapshot in snapshots:
            data.append({
                'ticker': snapshot.ticker,
                'final_score': snapshot.final_score,
                'final_score_smoothed': snapshot.final_score_smoothed,
                'rank': snapshot.rank
            })
        
        df = pd.DataFrame(data)
        
        # Ordenar por rank
        df = df.sort_values('rank')
        
        return df
    
    def get_monthly_returns(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date
    ) -> Dict[str, float]:
        """
        Obtém retornos mensais dos ativos.
        
        Args:
            tickers: Lista de tickers
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Dicionário {ticker: return}
        """
        returns = {}
        
        for ticker in tickers:
            try:
                # Buscar preços
                prices_df = self.yahoo_client.fetch_daily_prices(
                    ticker,
                    start_date,
                    end_date
                )
                
                if prices_df.empty or len(prices_df) < 2:
                    logger.warning(f"Insufficient price data for {ticker}")
                    returns[ticker] = 0.0
                    continue
                
                # Calcular retorno
                start_price = prices_df.iloc[0]['adj_close']
                end_price = prices_df.iloc[-1]['adj_close']
                
                monthly_return = (end_price - start_price) / start_price
                returns[ticker] = monthly_return
                
            except Exception as e:
                logger.error(f"Error fetching returns for {ticker}: {e}")
                returns[ticker] = 0.0
        
        return returns
    
    def run_backtest(self, db: Session = None) -> Dict:
        """
        Executa backtest completo.
        
        Args:
            db: Sessão do banco de dados (opcional, cria nova se None)
            
        Returns:
            Dicionário com resultados do backtest
        """
        if db is None:
            db = SessionLocal()
            close_db = True
        else:
            close_db = False
        
        try:
            # Criar snapshots mensais se necessário
            self.create_monthly_snapshots(db)
            
            # Obter datas de rebalanceamento
            rebalance_dates = self.get_monthly_dates()
            
            # Inicializar variáveis
            portfolio_history = []
            monthly_returns = []
            
            logger.info(f"Running backtest with {len(rebalance_dates)} rebalance periods")
            
            # Para cada período de rebalanceamento
            for i, rebalance_date in enumerate(rebalance_dates[:-1]):
                # Data do próximo rebalanceamento
                next_rebalance = rebalance_dates[i + 1]
                
                # Obter ranking do período
                ranking_df = self.get_ranking_snapshot(db, rebalance_date)
                
                if ranking_df.empty:
                    logger.warning(f"No ranking for {rebalance_date}, skipping period")
                    continue
                
                # Selecionar score column
                score_col = 'final_score_smoothed' if self.use_smoothing else 'final_score'
                
                # Selecionar Top N
                selected_tickers = Portfolio.select_top_n(
                    ranking_df,
                    self.top_n,
                    score_col
                )
                
                if not selected_tickers:
                    logger.warning(f"No assets selected for {rebalance_date}")
                    continue
                
                # Criar portfólio
                scores_dict = dict(zip(ranking_df['ticker'], ranking_df[score_col]))
                portfolio = Portfolio(selected_tickers, scores_dict)
                
                # Calcular pesos
                if self.weight_method == 'equal':
                    weights = portfolio.calculate_equal_weights()
                else:
                    weights = portfolio.calculate_score_weights()
                
                portfolio_history.append(weights)
                
                # Obter retornos do período
                period_returns = self.get_monthly_returns(
                    selected_tickers,
                    rebalance_date,
                    next_rebalance
                )
                
                # Calcular retorno do portfólio
                portfolio_return = portfolio.calculate_portfolio_return(
                    period_returns,
                    weights
                )
                
                monthly_returns.append(portfolio_return)
                
                logger.info(
                    f"Period {rebalance_date} to {next_rebalance}: "
                    f"return={portfolio_return*100:.2f}%, assets={len(selected_tickers)}"
                )
            
            # Calcular métricas
            returns_series = pd.Series(monthly_returns)
            metrics = PerformanceMetrics.calculate_all_metrics(
                returns_series,
                portfolio_history,
                self.risk_free_rate,
                periods_per_year=12
            )
            
            # Adicionar estatísticas adicionais
            metrics['num_rebalances'] = len(portfolio_history)
            metrics['num_trades'] = sum(len(p) for p in portfolio_history)
            
            # Preparar resultado
            result = {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'top_n': self.top_n,
                'weight_method': self.weight_method,
                'use_smoothing': self.use_smoothing,
                'metrics': metrics,
                'monthly_returns': monthly_returns,
                'portfolio_history': portfolio_history
            }
            
            logger.info(
                f"Backtest completed: CAGR={metrics['cagr']:.2f}%, "
                f"Sharpe={metrics['sharpe_ratio']:.2f}, "
                f"MaxDD={metrics['max_drawdown']:.2f}%"
            )
            
            return result
            
        finally:
            if close_db:
                db.close()
    
    def save_backtest_result(
        self,
        backtest_name: str,
        result: Dict,
        db: Session = None
    ) -> BacktestResult:
        """
        Salva resultado do backtest no banco de dados.
        
        Args:
            backtest_name: Nome do backtest
            result: Dicionário com resultados
            db: Sessão do banco de dados
            
        Returns:
            Objeto BacktestResult salvo
        """
        if db is None:
            db = SessionLocal()
            close_db = True
        else:
            close_db = False
        
        try:
            metrics = result['metrics']
            
            backtest_result = BacktestResult(
                backtest_name=backtest_name,
                start_date=result['start_date'],
                end_date=result['end_date'],
                top_n=result['top_n'],
                rebalance_frequency=self.rebalance_frequency,
                weight_method=result['weight_method'],
                use_smoothing=result['use_smoothing'],
                total_return=metrics['total_return'],
                cagr=metrics['cagr'],
                volatility=metrics['volatility'],
                sharpe_ratio=metrics['sharpe_ratio'],
                max_drawdown=metrics['max_drawdown'],
                avg_turnover=metrics['avg_turnover'],
                num_rebalances=metrics['num_rebalances'],
                num_trades=metrics['num_trades'],
                monthly_returns=result['monthly_returns'],
                portfolio_history=[
                    {k: float(v) for k, v in p.items()}
                    for p in result['portfolio_history']
                ]
            )
            
            db.add(backtest_result)
            db.commit()
            db.refresh(backtest_result)
            
            logger.info(f"Saved backtest result: {backtest_name}")
            
            return backtest_result
            
        finally:
            if close_db:
                db.close()
