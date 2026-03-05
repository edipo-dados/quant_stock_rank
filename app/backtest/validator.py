"""
Validador de dados para backtest.

Valida disponibilidade e qualidade dos dados antes de executar backtest.
"""

from typing import Dict, Any, List
from datetime import date
from sqlalchemy.orm import Session
import logging

from app.models.schemas import ScoreDaily, RawPriceDaily
from app.backtest.benchmark import BenchmarkManager

logger = logging.getLogger(__name__)


class BacktestDataValidator:
    """Valida dados antes de executar backtest."""
    
    def __init__(self, db: Session):
        """
        Inicializa o validador.
        
        Args:
            db: Sessão do banco de dados
        """
        self.db = db
        self.benchmark_manager = BenchmarkManager(db)
    
    def validate_universe(
        self,
        start_date: date,
        end_date: date,
        min_scores_required: int = 10
    ) -> Dict[str, Any]:
        """
        Valida disponibilidade e qualidade dos dados.
        
        Args:
            start_date: Data inicial do backtest
            end_date: Data final do backtest
            min_scores_required: Número mínimo de scores necessários
            
        Returns:
            Dict com status e warnings:
            {
                'valid': bool,
                'warnings': List[str],
                'score_count': int,
                'tickers_count': int,
                'dates_count': int,
                'benchmark_count': int,
                'missing_data_tickers': List[str]
            }
        """
        warnings = []
        
        # 1. Verificar scores disponíveis
        score_count = self.db.query(ScoreDaily).filter(
            ScoreDaily.date >= start_date,
            ScoreDaily.date <= end_date
        ).count()
        
        if score_count == 0:
            warnings.append("CRITICAL: Sem scores disponíveis no período")
            return {
                'valid': False,
                'warnings': warnings,
                'score_count': 0,
                'tickers_count': 0,
                'dates_count': 0,
                'benchmark_count': 0,
                'missing_data_tickers': []
            }
        
        # 2. Verificar número de tickers únicos
        tickers_count = self.db.query(ScoreDaily.ticker).filter(
            ScoreDaily.date >= start_date,
            ScoreDaily.date <= end_date
        ).distinct().count()
        
        if tickers_count < min_scores_required:
            warnings.append(
                f"WARNING: Apenas {tickers_count} tickers disponíveis "
                f"(mínimo recomendado: {min_scores_required})"
            )
        
        # 3. Verificar número de datas únicas
        dates_count = self.db.query(ScoreDaily.date).filter(
            ScoreDaily.date >= start_date,
            ScoreDaily.date <= end_date
        ).distinct().count()
        
        if dates_count < 60:  # ~2 meses
            warnings.append(
                f"WARNING: Apenas {dates_count} dias com dados "
                f"(mínimo recomendado: 60)"
            )
        
        # 4. Verificar tickers com scores faltantes
        tickers_with_missing = self.db.query(ScoreDaily.ticker).filter(
            ScoreDaily.date >= start_date,
            ScoreDaily.date <= end_date,
            ScoreDaily.final_score.is_(None)
        ).distinct().all()
        
        missing_data_tickers = [t[0] for t in tickers_with_missing]
        
        if missing_data_tickers:
            warnings.append(
                f"WARNING: {len(missing_data_tickers)} tickers com scores faltantes"
            )
            logger.debug(f"Tickers com scores faltantes: {missing_data_tickers[:10]}")
        
        # 5. Verificar benchmark
        benchmark_count = self.benchmark_manager.get_benchmark_data(
            start_date=start_date,
            end_date=end_date
        )
        
        if not benchmark_count:
            warnings.append("WARNING: Benchmark não disponível no período")
            benchmark_count = 0
        else:
            benchmark_count = len(benchmark_count)
        
        # 6. Verificar preços históricos
        price_count = self.db.query(RawPriceDaily).filter(
            RawPriceDaily.date >= start_date,
            RawPriceDaily.date <= end_date
        ).count()
        
        if price_count == 0:
            warnings.append("CRITICAL: Sem preços históricos disponíveis")
            return {
                'valid': False,
                'warnings': warnings,
                'score_count': score_count,
                'tickers_count': tickers_count,
                'dates_count': dates_count,
                'benchmark_count': benchmark_count,
                'missing_data_tickers': missing_data_tickers
            }
        
        # Determinar se é válido (sem erros CRITICAL)
        critical_errors = [w for w in warnings if 'CRITICAL' in w]
        valid = len(critical_errors) == 0
        
        return {
            'valid': valid,
            'warnings': warnings,
            'score_count': score_count,
            'tickers_count': tickers_count,
            'dates_count': dates_count,
            'benchmark_count': benchmark_count,
            'missing_data_tickers': missing_data_tickers
        }
    
    def validate_rebalance_date(
        self,
        rebalance_date: date,
        top_n: int
    ) -> Dict[str, Any]:
        """
        Valida se há dados suficientes para um rebalanceamento.
        
        Args:
            rebalance_date: Data do rebalanceamento
            top_n: Número de ativos a selecionar
            
        Returns:
            Dict com status e warnings:
            {
                'valid': bool,
                'warnings': List[str],
                'available_tickers': int
            }
        """
        warnings = []
        
        # Verificar scores disponíveis na data
        available_scores = self.db.query(ScoreDaily).filter(
            ScoreDaily.date == rebalance_date,
            ScoreDaily.final_score.isnot(None)
        ).count()
        
        if available_scores == 0:
            warnings.append(f"CRITICAL: Sem scores disponíveis em {rebalance_date}")
            return {
                'valid': False,
                'warnings': warnings,
                'available_tickers': 0
            }
        
        if available_scores < top_n:
            warnings.append(
                f"WARNING: Apenas {available_scores} scores disponíveis "
                f"em {rebalance_date} (top_n={top_n})"
            )
        
        # Verificar preços disponíveis na data
        available_prices = self.db.query(RawPriceDaily).filter(
            RawPriceDaily.date == rebalance_date
        ).count()
        
        if available_prices == 0:
            warnings.append(f"WARNING: Sem preços disponíveis em {rebalance_date}")
        
        valid = len([w for w in warnings if 'CRITICAL' in w]) == 0
        
        return {
            'valid': valid,
            'warnings': warnings,
            'available_tickers': available_scores
        }
    
    def log_validation_summary(self, validation_result: Dict[str, Any]) -> None:
        """
        Loga resumo da validação.
        
        Args:
            validation_result: Resultado da validação
        """
        logger.info("=" * 60)
        logger.info("VALIDAÇÃO DE DADOS DO BACKTEST")
        logger.info("=" * 60)
        logger.info(f"Status: {'✅ VÁLIDO' if validation_result['valid'] else '❌ INVÁLIDO'}")
        logger.info(f"Scores disponíveis: {validation_result.get('score_count', 0)}")
        logger.info(f"Tickers únicos: {validation_result.get('tickers_count', 0)}")
        logger.info(f"Datas únicas: {validation_result.get('dates_count', 0)}")
        logger.info(f"Benchmark disponível: {validation_result.get('benchmark_count', 0)} registros")
        
        if validation_result.get('warnings'):
            logger.info("\nAvisos:")
            for warning in validation_result['warnings']:
                if 'CRITICAL' in warning:
                    logger.error(f"  ❌ {warning}")
                else:
                    logger.warning(f"  ⚠️  {warning}")
        
        logger.info("=" * 60)
