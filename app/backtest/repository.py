"""
Repository para operações de persistência de backtest.

Separa lógica de persistência da lógica de simulação.
"""

from typing import List, Optional, Dict
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.backtest.models import (
    BacktestRun,
    BacktestNAV,
    BacktestPosition,
    BacktestMetrics
)


class BacktestRepository:
    """
    Repository para operações CRUD de backtest.
    
    Garante isolamento e auditabilidade das execuções.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa repository com sessão do banco.
        
        Args:
            db: Sessão SQLAlchemy
        """
        self.db = db
    
    # ========================================================================
    # BacktestRun Operations
    # ========================================================================
    
    def create_run(
        self,
        name: Optional[str],
        start_date: date,
        end_date: date,
        rebalance_frequency: str,
        top_n: int,
        transaction_cost: float,
        initial_capital: float,
        notes: Optional[str] = None
    ) -> BacktestRun:
        """
        Cria nova execução de backtest.
        
        Args:
            name: Nome identificador (opcional)
            start_date: Data inicial
            end_date: Data final
            rebalance_frequency: Frequência de rebalanceamento
            top_n: Número de ativos no portfólio
            transaction_cost: Custo de transação (ex: 0.001 = 0.1%)
            initial_capital: Capital inicial
            notes: Notas adicionais (opcional)
            
        Returns:
            BacktestRun criado
        """
        run = BacktestRun(
            name=name,
            start_date=start_date,
            end_date=end_date,
            rebalance_frequency=rebalance_frequency,
            top_n=top_n,
            transaction_cost=transaction_cost,
            initial_capital=initial_capital,
            notes=notes
        )
        
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        
        return run
    
    def get_run(self, run_id: str) -> Optional[BacktestRun]:
        """
        Busca execução por ID.
        
        Args:
            run_id: ID da execução
            
        Returns:
            BacktestRun ou None
        """
        return self.db.query(BacktestRun).filter(BacktestRun.id == run_id).first()
    
    def list_runs(
        self,
        limit: int = 50,
        offset: int = 0,
        order_by: str = 'created_at'
    ) -> List[BacktestRun]:
        """
        Lista execuções de backtest.
        
        Args:
            limit: Número máximo de resultados
            offset: Offset para paginação
            order_by: Campo para ordenação
            
        Returns:
            Lista de BacktestRun
        """
        query = self.db.query(BacktestRun)
        
        if order_by == 'created_at':
            query = query.order_by(desc(BacktestRun.created_at))
        elif order_by == 'start_date':
            query = query.order_by(desc(BacktestRun.start_date))
        
        return query.limit(limit).offset(offset).all()
    
    def delete_run(self, run_id: str) -> bool:
        """
        Deleta execução de backtest (cascade delete).
        
        Args:
            run_id: ID da execução
            
        Returns:
            True se deletado, False se não encontrado
        """
        run = self.get_run(run_id)
        if not run:
            return False
        
        self.db.delete(run)
        self.db.commit()
        return True
    
    # ========================================================================
    # BacktestNAV Operations
    # ========================================================================
    
    def save_nav_records(
        self,
        run_id: str,
        nav_records: List[Dict]
    ) -> int:
        """
        Salva registros de NAV em batch.
        
        Args:
            run_id: ID da execução
            nav_records: Lista de dicts com date, nav, daily_return, etc.
            
        Returns:
            Número de registros salvos
        """
        records = []
        for record in nav_records:
            nav = BacktestNAV(
                run_id=run_id,
                date=record['date'],
                nav=record['nav'],
                benchmark_nav=record.get('benchmark_nav'),
                daily_return=record['daily_return'],
                benchmark_return=record.get('benchmark_return')
            )
            records.append(nav)
        
        self.db.bulk_save_objects(records)
        self.db.commit()
        
        return len(records)
    
    def get_nav_records(
        self,
        run_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[BacktestNAV]:
        """
        Busca registros de NAV.
        
        Args:
            run_id: ID da execução
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            
        Returns:
            Lista de BacktestNAV ordenada por data
        """
        query = self.db.query(BacktestNAV).filter(BacktestNAV.run_id == run_id)
        
        if start_date:
            query = query.filter(BacktestNAV.date >= start_date)
        if end_date:
            query = query.filter(BacktestNAV.date <= end_date)
        
        return query.order_by(BacktestNAV.date).all()
    
    # ========================================================================
    # BacktestPosition Operations
    # ========================================================================
    
    def save_positions(
        self,
        run_id: str,
        positions: List[Dict]
    ) -> int:
        """
        Salva posições em batch.
        
        Args:
            run_id: ID da execução
            positions: Lista de dicts com date, ticker, weight, score_at_selection
            
        Returns:
            Número de posições salvas
        """
        records = []
        for pos in positions:
            position = BacktestPosition(
                run_id=run_id,
                date=pos['date'],
                ticker=pos['ticker'],
                weight=pos['weight'],
                score_at_selection=pos.get('score_at_selection')
            )
            records.append(position)
        
        self.db.bulk_save_objects(records)
        self.db.commit()
        
        return len(records)
    
    def get_positions(
        self,
        run_id: str,
        rebalance_date: Optional[date] = None
    ) -> List[BacktestPosition]:
        """
        Busca posições.
        
        Args:
            run_id: ID da execução
            rebalance_date: Data específica de rebalance (opcional)
            
        Returns:
            Lista de BacktestPosition
        """
        query = self.db.query(BacktestPosition).filter(BacktestPosition.run_id == run_id)
        
        if rebalance_date:
            query = query.filter(BacktestPosition.date == rebalance_date)
        
        return query.order_by(BacktestPosition.date, BacktestPosition.ticker).all()
    
    def get_rebalance_dates(self, run_id: str) -> List[date]:
        """
        Retorna todas as datas de rebalance.
        
        Args:
            run_id: ID da execução
            
        Returns:
            Lista de datas únicas ordenadas
        """
        from sqlalchemy import func, distinct
        
        dates = self.db.query(distinct(BacktestPosition.date)).filter(
            BacktestPosition.run_id == run_id
        ).order_by(BacktestPosition.date).all()
        
        return [d[0] for d in dates]
    
    # ========================================================================
    # BacktestMetrics Operations
    # ========================================================================
    
    def save_metrics(
        self,
        run_id: str,
        metrics: Dict
    ) -> BacktestMetrics:
        """
        Salva métricas finais.
        
        Args:
            run_id: ID da execução
            metrics: Dict com todas as métricas
            
        Returns:
            BacktestMetrics criado
        """
        metrics_obj = BacktestMetrics(
            run_id=run_id,
            total_return=metrics['total_return'],
            cagr=metrics['cagr'],
            volatility=metrics['volatility'],
            sharpe_ratio=metrics['sharpe_ratio'],
            sortino_ratio=metrics['sortino_ratio'],
            max_drawdown=metrics['max_drawdown'],
            turnover_avg=metrics['turnover_avg'],
            alpha=metrics.get('alpha'),
            beta=metrics.get('beta'),
            information_ratio=metrics.get('information_ratio')
        )
        
        self.db.add(metrics_obj)
        self.db.commit()
        self.db.refresh(metrics_obj)
        
        return metrics_obj
    
    def get_metrics(self, run_id: str) -> Optional[BacktestMetrics]:
        """
        Busca métricas de uma execução.
        
        Args:
            run_id: ID da execução
            
        Returns:
            BacktestMetrics ou None
        """
        return self.db.query(BacktestMetrics).filter(
            BacktestMetrics.run_id == run_id
        ).first()
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def get_run_summary(self, run_id: str) -> Optional[Dict]:
        """
        Retorna resumo completo de uma execução.
        
        Args:
            run_id: ID da execução
            
        Returns:
            Dict com run, metrics, e estatísticas
        """
        run = self.get_run(run_id)
        if not run:
            return None
        
        metrics = self.get_metrics(run_id)
        nav_count = self.db.query(BacktestNAV).filter(BacktestNAV.run_id == run_id).count()
        position_count = self.db.query(BacktestPosition).filter(BacktestPosition.run_id == run_id).count()
        rebalance_dates = self.get_rebalance_dates(run_id)
        
        return {
            'run': run,
            'metrics': metrics,
            'nav_records_count': nav_count,
            'positions_count': position_count,
            'rebalance_count': len(rebalance_dates),
            'rebalance_dates': rebalance_dates
        }
