"""
Cálculo de métricas de performance para backtest.
"""

import numpy as np
import pandas as pd
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """
    Calcula métricas de performance de estratégias de investimento.
    
    Métricas implementadas:
    - CAGR (Compound Annual Growth Rate)
    - Volatilidade anualizada
    - Sharpe Ratio
    - Maximum Drawdown
    - Turnover médio
    """
    
    @staticmethod
    def calculate_cagr(returns: pd.Series, periods_per_year: int = 12) -> float:
        """
        Calcula CAGR (Compound Annual Growth Rate).
        
        Args:
            returns: Série de retornos (ex: retornos mensais)
            periods_per_year: Número de períodos por ano (12 para mensal, 252 para diário)
            
        Returns:
            CAGR em percentual
        """
        if len(returns) == 0:
            return 0.0
        
        # Calcular retorno total
        cumulative_return = (1 + returns).prod() - 1
        
        # Calcular número de anos
        num_years = len(returns) / periods_per_year
        
        if num_years <= 0:
            return 0.0
        
        # CAGR = (1 + total_return)^(1/years) - 1
        cagr = (1 + cumulative_return) ** (1 / num_years) - 1
        
        return cagr * 100  # Retornar em percentual
    
    @staticmethod
    def calculate_volatility(returns: pd.Series, periods_per_year: int = 12) -> float:
        """
        Calcula volatilidade anualizada.
        
        Args:
            returns: Série de retornos
            periods_per_year: Número de períodos por ano
            
        Returns:
            Volatilidade anualizada em percentual
        """
        if len(returns) == 0:
            return 0.0
        
        # Volatilidade = desvio padrão * sqrt(períodos por ano)
        volatility = returns.std() * np.sqrt(periods_per_year)
        
        return volatility * 100  # Retornar em percentual
    
    @staticmethod
    def calculate_sharpe_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 12
    ) -> float:
        """
        Calcula Sharpe Ratio.
        
        Args:
            returns: Série de retornos
            risk_free_rate: Taxa livre de risco anualizada (ex: 0.05 para 5%)
            periods_per_year: Número de períodos por ano
            
        Returns:
            Sharpe Ratio
        """
        if len(returns) == 0:
            return 0.0
        
        # Retorno médio anualizado
        mean_return = returns.mean() * periods_per_year
        
        # Volatilidade anualizada
        volatility = returns.std() * np.sqrt(periods_per_year)
        
        if volatility == 0:
            return 0.0
        
        # Sharpe = (retorno - risk_free) / volatilidade
        sharpe = (mean_return - risk_free_rate) / volatility
        
        return sharpe
    
    @staticmethod
    def calculate_max_drawdown(cumulative_returns: pd.Series) -> float:
        """
        Calcula Maximum Drawdown.
        
        Args:
            cumulative_returns: Série de retornos acumulados (1 + retorno)
            
        Returns:
            Maximum Drawdown em percentual (valor negativo)
        """
        if len(cumulative_returns) == 0:
            return 0.0
        
        # Calcular running maximum
        running_max = cumulative_returns.cummax()
        
        # Calcular drawdown
        drawdown = (cumulative_returns - running_max) / running_max
        
        # Maximum drawdown (valor mais negativo)
        max_dd = drawdown.min()
        
        return max_dd * 100  # Retornar em percentual
    
    @staticmethod
    def calculate_turnover(
        old_weights: Dict[str, float],
        new_weights: Dict[str, float]
    ) -> float:
        """
        Calcula turnover entre dois portfólios.
        
        Turnover = soma dos valores absolutos das mudanças de peso / 2
        
        Args:
            old_weights: Pesos do portfólio anterior {ticker: weight}
            new_weights: Pesos do novo portfólio {ticker: weight}
            
        Returns:
            Turnover em percentual (0-100%)
        """
        # Obter todos os tickers
        all_tickers = set(old_weights.keys()) | set(new_weights.keys())
        
        # Calcular mudanças de peso
        total_change = 0.0
        for ticker in all_tickers:
            old_weight = old_weights.get(ticker, 0.0)
            new_weight = new_weights.get(ticker, 0.0)
            total_change += abs(new_weight - old_weight)
        
        # Turnover = soma das mudanças / 2
        turnover = total_change / 2.0
        
        return turnover * 100  # Retornar em percentual
    
    @staticmethod
    def calculate_all_metrics(
        returns: pd.Series,
        portfolio_history: List[Dict[str, float]],
        risk_free_rate: float = 0.0,
        periods_per_year: int = 12,
        benchmark_returns: pd.Series = None
    ) -> Dict[str, float]:
        """
        Calcula todas as métricas de performance.
        
        Args:
            returns: Série de retornos periódicos
            portfolio_history: Lista de portfólios {ticker: weight} por período
            risk_free_rate: Taxa livre de risco anualizada
            periods_per_year: Número de períodos por ano
            benchmark_returns: Série de retornos do benchmark (opcional)
            
        Returns:
            Dicionário com todas as métricas
        """
        # Calcular retornos acumulados
        cumulative_returns = (1 + returns).cumprod()
        
        # Calcular métricas básicas
        metrics = {
            'total_return': (cumulative_returns.iloc[-1] - 1) * 100 if len(cumulative_returns) > 0 else 0.0,
            'cagr': PerformanceMetrics.calculate_cagr(returns, periods_per_year),
            'volatility': PerformanceMetrics.calculate_volatility(returns, periods_per_year),
            'sharpe_ratio': PerformanceMetrics.calculate_sharpe_ratio(returns, risk_free_rate, periods_per_year),
            'max_drawdown': PerformanceMetrics.calculate_max_drawdown(cumulative_returns),
        }
        
        # Calcular turnover médio
        if len(portfolio_history) > 1:
            turnovers = []
            for i in range(1, len(portfolio_history)):
                turnover = PerformanceMetrics.calculate_turnover(
                    portfolio_history[i-1],
                    portfolio_history[i]
                )
                turnovers.append(turnover)
            metrics['avg_turnover'] = np.mean(turnovers) if turnovers else 0.0
        else:
            metrics['avg_turnover'] = 0.0
        
        # Calcular métricas vs benchmark (se disponível)
        if benchmark_returns is not None and len(benchmark_returns) > 0:
            # Usar novos métodos corrigidos
            alpha, beta = PerformanceMetrics.calculate_alpha_beta(
                returns,
                benchmark_returns,
                risk_free_rate,
                periods_per_year
            )
            
            metrics['alpha'] = alpha  # Já em %
            metrics['beta'] = beta
            
            # Information Ratio corrigido
            metrics['information_ratio'] = PerformanceMetrics.calculate_information_ratio_v2(
                returns,
                benchmark_returns,
                periods_per_year
            )
            
            # Métricas do benchmark
            benchmark_cumulative = (1 + benchmark_returns).cumprod()
            metrics['benchmark_total_return'] = (benchmark_cumulative.iloc[-1] - 1) * 100 if len(benchmark_cumulative) > 0 else 0.0
            metrics['benchmark_cagr'] = PerformanceMetrics.calculate_cagr(benchmark_returns, periods_per_year)
            metrics['benchmark_volatility'] = PerformanceMetrics.calculate_volatility(benchmark_returns, periods_per_year)
            metrics['benchmark_sharpe'] = PerformanceMetrics.calculate_sharpe_ratio(benchmark_returns, risk_free_rate, periods_per_year)
            metrics['benchmark_max_drawdown'] = PerformanceMetrics.calculate_max_drawdown(benchmark_cumulative)
        else:
            metrics['alpha'] = None
            metrics['beta'] = None
            metrics['information_ratio'] = None
            metrics['benchmark_total_return'] = None
            metrics['benchmark_cagr'] = None
            metrics['benchmark_volatility'] = None
            metrics['benchmark_sharpe'] = None
            metrics['benchmark_max_drawdown'] = None
        
        # Adicionar Sortino e Calmar
        metrics['sortino_ratio'] = PerformanceMetrics.calculate_sortino_ratio(returns, risk_free_rate, periods_per_year)
        metrics['calmar_ratio'] = PerformanceMetrics.calculate_calmar_ratio(returns, periods_per_year)
        
        # Validar métricas
        warnings = PerformanceMetrics.validate_metrics(metrics)
        if warnings:
            metrics['validation_warnings'] = warnings
        
        return metrics


    @staticmethod
    def calculate_alpha_beta(
        strategy_returns: pd.Series,
        benchmark_returns: pd.Series,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 12
    ) -> tuple[float, float]:
        """
        Calcula Alpha e Beta usando CAPM com validações robustas.
        
        CAPM (Capital Asset Pricing Model):
        Beta = Cov(Rs, Rb) / Var(Rb)
        Alpha = E[Rs] - (Rf + Beta * (E[Rb] - Rf))
        
        Onde:
        - Rs = retornos da estratégia
        - Rb = retornos do benchmark
        - Rf = taxa livre de risco
        - E[] = valor esperado (média)
        
        Args:
            strategy_returns: Série de retornos periódicos da estratégia
            benchmark_returns: Série de retornos periódicos do benchmark
            risk_free_rate: Taxa livre de risco anualizada (ex: 0.05 para 5%)
            periods_per_year: Número de períodos por ano (12 para mensal)
        
        Returns:
            Tuple de (alpha_anualizado_pct, beta)
            - alpha em % anualizado
            - beta como float
        """
        # Validação de entrada
        if len(strategy_returns) == 0 or len(benchmark_returns) == 0:
            logger.warning("Empty returns series for alpha/beta calculation")
            return 0.0, 1.0
        
        # Alinhar séries pelo índice (garantir mesmas datas)
        aligned = pd.DataFrame({
            'strategy': strategy_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if len(aligned) < 2:
            logger.warning(f"Insufficient aligned data points for alpha/beta: {len(aligned)}")
            return 0.0, 1.0
        
        strategy = aligned['strategy']
        benchmark = aligned['benchmark']
        
        logger.info(f"Calculating alpha/beta with {len(strategy)} aligned periods")
        
        # Calcular Beta usando covariância
        covariance = strategy.cov(benchmark)
        benchmark_variance = benchmark.var()
        
        if benchmark_variance == 0:
            logger.warning("Benchmark variance is zero, setting beta=1.0")
            beta = 1.0
        else:
            beta = covariance / benchmark_variance
        
        # Validar Beta (deve estar entre -2 e 3 tipicamente)
        if abs(beta) > 5:
            logger.warning(f"Beta value seems unrealistic: {beta:.2f}")
        
        # Calcular retornos médios periódicos
        strategy_mean = strategy.mean()
        benchmark_mean = benchmark.mean()
        
        # Converter risk_free_rate anualizada para periódica
        rf_periodic = risk_free_rate / periods_per_year
        
        # Calcular Alpha periódico usando CAPM
        # Alpha = Rs - (Rf + Beta * (Rb - Rf))
        alpha_periodic = strategy_mean - (rf_periodic + beta * (benchmark_mean - rf_periodic))
        
        # Anualizar Alpha
        alpha_annual = alpha_periodic * periods_per_year
        
        # Validar Alpha (deve estar entre -50% e +50% tipicamente)
        if abs(alpha_annual) > 0.5:
            logger.warning(
                f"Alpha value seems unrealistic: {alpha_annual*100:.2f}%. "
                f"Strategy mean: {strategy_mean*100:.4f}%, "
                f"Benchmark mean: {benchmark_mean*100:.4f}%, "
                f"Beta: {beta:.2f}"
            )
        
        logger.info(
            f"Alpha/Beta calculated: Alpha={alpha_annual*100:.2f}%, Beta={beta:.2f} "
            f"(Strategy mean={strategy_mean*periods_per_year*100:.2f}%, "
            f"Benchmark mean={benchmark_mean*periods_per_year*100:.2f}%)"
        )
        
        return alpha_annual * 100, beta  # Alpha em %
    
    @staticmethod
    def calculate_information_ratio_v2(
        strategy_returns: pd.Series,
        benchmark_returns: pd.Series,
        periods_per_year: int = 12
    ) -> float:
        """
        Calcula Information Ratio com validações robustas.
        
        IR = E[Rs - Rb] / σ[Rs - Rb]
        
        Anualizado:
        IR = (mean(excess_returns) / std(excess_returns)) * sqrt(periods_per_year)
        
        Args:
            strategy_returns: Série de retornos periódicos da estratégia
            benchmark_returns: Série de retornos periódicos do benchmark
            periods_per_year: Número de períodos por ano
        
        Returns:
            Information Ratio anualizado
        """
        # Validação de entrada
        if len(strategy_returns) == 0 or len(benchmark_returns) == 0:
            logger.warning("Empty returns series for IR calculation")
            return 0.0
        
        # Alinhar séries pelo índice
        aligned = pd.DataFrame({
            'strategy': strategy_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if len(aligned) < 2:
            logger.warning(f"Insufficient aligned data points for IR: {len(aligned)}")
            return 0.0
        
        strategy = aligned['strategy']
        benchmark = aligned['benchmark']
        
        # Calcular excess returns
        excess_returns = strategy - benchmark
        
        # Calcular IR
        mean_excess = excess_returns.mean()
        std_excess = excess_returns.std()
        
        if std_excess == 0:
            logger.warning("Tracking error is zero, cannot calculate IR")
            return 0.0
        
        # Anualizar
        ir = (mean_excess / std_excess) * np.sqrt(periods_per_year)
        
        # Validar IR (deve estar entre -2 e 2 tipicamente)
        if abs(ir) > 3:
            logger.warning(
                f"IR value seems unrealistic: {ir:.2f}. "
                f"Mean excess: {mean_excess*100:.4f}%, "
                f"Tracking error: {std_excess*100:.4f}%"
            )
        
        logger.info(
            f"Information Ratio calculated: {ir:.2f} "
            f"(Mean excess={mean_excess*periods_per_year*100:.2f}%, "
            f"Tracking error={std_excess*np.sqrt(periods_per_year)*100:.2f}%)"
        )
        
        return ir
    
    @staticmethod
    def calculate_sortino_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 12
    ) -> float:
        """
        Calcula Sortino Ratio (penaliza apenas downside).
        
        Sortino = (E[R] - Rf) / σ_downside
        
        Onde σ_downside = std(retornos negativos) anualizado
        
        Args:
            returns: Série de retornos periódicos
            risk_free_rate: Taxa livre de risco anualizada
            periods_per_year: Número de períodos por ano
        
        Returns:
            Sortino Ratio
        """
        mean_return = returns.mean() * periods_per_year
        
        # Calcular downside deviation (apenas retornos negativos)
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0:
            return np.inf  # Sem downside
        
        downside_std = downside_returns.std() * np.sqrt(periods_per_year)
        
        if downside_std == 0:
            return 0.0
        
        sortino = (mean_return - risk_free_rate) / downside_std
        
        return sortino
    
    @staticmethod
    def calculate_calmar_ratio(
        returns: pd.Series,
        periods_per_year: int = 12
    ) -> float:
        """
        Calcula Calmar Ratio.
        
        Calmar = CAGR / |Max Drawdown|
        
        Args:
            returns: Série de retornos periódicos
            periods_per_year: Número de períodos por ano
        
        Returns:
            Calmar Ratio
        """
        cagr = PerformanceMetrics.calculate_cagr(returns, periods_per_year)
        
        cumulative_returns = (1 + returns).cumprod()
        max_dd = PerformanceMetrics.calculate_max_drawdown(cumulative_returns)
        
        if max_dd == 0:
            return np.inf
        
        # CAGR e max_dd já estão em %
        calmar = (cagr / 100) / abs(max_dd / 100)
        
        return calmar
    
    @staticmethod
    def validate_metrics(metrics: Dict[str, float]) -> Dict[str, str]:
        """
        Valida métricas calculadas e retorna warnings para valores anômalos.
        
        Args:
            metrics: Dicionário com métricas calculadas
            
        Returns:
            Dicionário com warnings {metric_name: warning_message}
        """
        warnings = {}
        
        # Validar Alpha (-20% a +20% é razoável)
        if metrics.get('alpha') is not None:
            alpha = metrics['alpha']
            if abs(alpha) > 20:
                warnings['alpha'] = f"Alpha anual muito alto: {alpha:.2f}%. Valores típicos: -20% a +20%"
            elif abs(alpha) > 50:
                warnings['alpha'] = f"CRÍTICO: Alpha anual irrealista: {alpha:.2f}%. Revisar cálculo!"
        
        # Validar Beta (0.5 a 1.5 é típico para ações)
        if metrics.get('beta') is not None:
            beta = metrics['beta']
            if abs(beta) > 3:
                warnings['beta'] = f"Beta muito alto: {beta:.2f}. Valores típicos: 0.5 a 1.5"
        
        # Validar Information Ratio (-1 a 1 é típico)
        if metrics.get('information_ratio') is not None:
            ir = metrics['information_ratio']
            if abs(ir) > 2:
                warnings['information_ratio'] = f"IR muito alto: {ir:.2f}. Valores típicos: -1 a 1"
        
        # Validar Sharpe Ratio (-1 a 3 é razoável)
        if metrics.get('sharpe_ratio') is not None:
            sharpe = metrics['sharpe_ratio']
            if abs(sharpe) > 5:
                warnings['sharpe_ratio'] = f"Sharpe muito alto: {sharpe:.2f}. Valores típicos: -1 a 3"
        
        # Validar Volatilidade (5% a 50% é típico para ações)
        if metrics.get('volatility') is not None:
            vol = metrics['volatility']
            if vol > 100:
                warnings['volatility'] = f"Volatilidade muito alta: {vol:.2f}%. Valores típicos: 5% a 50%"
        
        # Validar Max Drawdown (-80% a 0% é razoável)
        if metrics.get('max_drawdown') is not None:
            dd = metrics['max_drawdown']
            if dd < -80:
                warnings['max_drawdown'] = f"Drawdown muito alto: {dd:.2f}%. Revisar estratégia!"
        
        # Log warnings
        if warnings:
            logger.warning("Métricas anômalas detectadas:")
            for metric, warning in warnings.items():
                logger.warning(f"  {metric}: {warning}")
        else:
            logger.info("Todas as métricas estão dentro de faixas razoáveis")
        
        return warnings
