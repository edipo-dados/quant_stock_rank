"""
Service layer para backtesting.

Orquestra lógica de simulação e persistência.
"""

from typing import Optional, Dict, List
from datetime import date
from sqlalchemy.orm import Session
import logging

from app.backtest.repository import BacktestRepository
from app.backtest.models import BacktestRun

logger = logging.getLogger(__name__)


class BacktestService:
    """
    Service para gerenciar execuções de backtest.
    
    Separa lógica de negócio da persistência.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa service com sessão do banco.
        
        Args:
            db: Sessão SQLAlchemy
        """
        self.db = db
        self.repository = BacktestRepository(db)
    
    def create_backtest_run(
        self,
        name: Optional[str] = None,
        start_date: date = None,
        end_date: date = None,
        rebalance_frequency: str = "monthly",
        top_n: int = 10,
        transaction_cost: float = 0.001,
        initial_capital: float = 100000.0,
        notes: Optional[str] = None
    ) -> BacktestRun:
        """
        Cria nova execução de backtest.
        
        Args:
            name: Nome identificador
            start_date: Data inicial
            end_date: Data final
            rebalance_frequency: Frequência de rebalanceamento
            top_n: Número de ativos
            transaction_cost: Custo de transação
            initial_capital: Capital inicial
            notes: Notas adicionais
            
        Returns:
            BacktestRun criado
        """
        logger.info(f"Creating backtest run: {name}")
        
        run = self.repository.create_run(
            name=name,
            start_date=start_date,
            end_date=end_date,
            rebalance_frequency=rebalance_frequency,
            top_n=top_n,
            transaction_cost=transaction_cost,
            initial_capital=initial_capital,
            notes=notes
        )
        
        logger.info(f"Backtest run created: {run.id}")
        return run
    
    def save_backtest_results(
        self,
        run_id: str,
        nav_records: List[Dict],
        positions: List[Dict],
        metrics: Dict
    ) -> bool:
        """
        Salva resultados completos de um backtest.
        
        Args:
            run_id: ID da execução
            nav_records: Lista de registros de NAV
            positions: Lista de posições
            metrics: Dict com métricas finais
            
        Returns:
            True se sucesso
        """
        try:
            logger.info(f"Saving backtest results for run {run_id}")
            
            # Salvar NAV
            nav_count = self.repository.save_nav_records(run_id, nav_records)
            logger.info(f"Saved {nav_count} NAV records")
            
            # Salvar posições
            pos_count = self.repository.save_positions(run_id, positions)
            logger.info(f"Saved {pos_count} positions")
            
            # Salvar métricas
            self.repository.save_metrics(run_id, metrics)
            logger.info(f"Saved metrics")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving backtest results: {e}")
            raise
    
    def get_backtest_summary(self, run_id: str) -> Optional[Dict]:
        """
        Retorna resumo completo de uma execução.
        
        Args:
            run_id: ID da execução
            
        Returns:
            Dict com informações completas
        """
        return self.repository.get_run_summary(run_id)
    
    def list_backtests(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[BacktestRun]:
        """
        Lista execuções de backtest.
        
        Args:
            limit: Número máximo de resultados
            offset: Offset para paginação
            
        Returns:
            Lista de BacktestRun
        """
        return self.repository.list_runs(limit=limit, offset=offset)
    
    def delete_backtest(self, run_id: str) -> bool:
        """
        Deleta execução de backtest.
        
        Args:
            run_id: ID da execução
            
        Returns:
            True se deletado
        """
        logger.info(f"Deleting backtest run {run_id}")
        return self.repository.delete_run(run_id)
    
    def get_equity_curve(
        self,
        run_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict]:
        """
        Retorna equity curve formatada.
        
        Args:
            run_id: ID da execução
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            
        Returns:
            Lista de dicts com date, nav, daily_return
        """
        nav_records = self.repository.get_nav_records(run_id, start_date, end_date)
        
        return [
            {
                'date': record.date,
                'nav': record.nav,
                'benchmark_nav': record.benchmark_nav,
                'daily_return': record.daily_return,
                'benchmark_return': record.benchmark_return
            }
            for record in nav_records
        ]
    
    def get_portfolio_composition(
        self,
        run_id: str,
        rebalance_date: Optional[date] = None
    ) -> List[Dict]:
        """
        Retorna composição do portfólio.
        
        Args:
            run_id: ID da execução
            rebalance_date: Data específica (opcional)
            
        Returns:
            Lista de dicts com ticker, weight, score
        """
        positions = self.repository.get_positions(run_id, rebalance_date)
        
        return [
            {
                'date': pos.date,
                'ticker': pos.ticker,
                'weight': pos.weight,
                'score_at_selection': pos.score_at_selection
            }
            for pos in positions
        ]
    
    def compare_runs(self, run_ids: List[str]) -> Dict:
        """
        Compara múltiplas execuções de backtest.
        
        Args:
            run_ids: Lista de IDs para comparar
            
        Returns:
            Dict com comparação de métricas
        """
        comparison = {
            'runs': [],
            'metrics_comparison': {}
        }
        
        for run_id in run_ids:
            summary = self.get_backtest_summary(run_id)
            if summary:
                comparison['runs'].append({
                    'id': run_id,
                    'name': summary['run'].name,
                    'period': f"{summary['run'].start_date} to {summary['run'].end_date}",
                    'metrics': summary['metrics']
                })
        
        return comparison
