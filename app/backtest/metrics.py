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
        
        return metrics


    @staticmethod
    def calculate_alpha_beta(
        strategy_returns: pd.Series,
        benchmark_returns: pd.Series,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 12
    ) -> tuple[float, float]:
        """
        Calcula Alpha e Beta usando CAPM.
        
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
        # Alinhar séries (garantir mesmo tamanho)
        min_len = min(len(strategy_returns), len(benchmark_returns))
        strategy = strategy_returns.iloc[:min_len]
        benchmark = benchmark_returns.iloc[:min_len]
        
        # Calcular Beta
        covariance = strategy.cov(benchmark)
        benchmark_variance = benchmark.var()
        beta = covariance / benchmark_variance if benchmark_variance != 0 else 0.0
        
        # Calcular retornos médios anualizados
        strategy_mean_annual = strategy.mean() * periods_per_year
        benchmark_mean_annual = benchmark.mean() * periods_per_year
        
        # Calcular Alpha anualizado usando CAPM
        # Alpha = Rs - (Rf + Beta * (Rb - Rf))
        alpha = strategy_mean_annual - (risk_free_rate + beta * (benchmark_mean_annual - risk_free_rate))
        
        return alpha * 100, beta  # Alpha em %
    
    @staticmethod
    def calculate_information_ratio_v2(
        strategy_returns: pd.Series,
        benchmark_returns: pd.Series,
        periods_per_year: int = 12
    ) -> float:
        """
        Calcula Information Ratio (versão corrigida).
        
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
        # Alinhar séries
        min_len = min(len(strategy_returns), len(benchmark_returns))
        strategy = strategy_returns.iloc[:min_len]
        benchmark = benchmark_returns.iloc[:min_len]
        
        # Calcular excess returns
        excess_returns = strategy - benchmark
        
        # Calcular IR
        mean_excess = excess_returns.mean()
        std_excess = excess_returns.std()
        
        if std_excess == 0:
            return 0.0
        
        # Anualizar
        ir = (mean_excess / std_excess) * np.sqrt(periods_per_year)
        
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
