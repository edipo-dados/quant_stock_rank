"""
Testes unitários para cálculo de fatores de momentum.

Valida: Requisitos 3.1, 3.2, 3.3, 3.4, 3.5, 3.8
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.factor_engine.momentum_factors import MomentumFactorCalculator
from app.core.exceptions import InsufficientDataError, CalculationError


@pytest.fixture
def calculator():
    """Fixture para criar instância do calculador."""
    return MomentumFactorCalculator()


@pytest.fixture
def sample_prices_1y():
    """Fixture com 1 ano de dados de preços diários."""
    dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
    # Criar série de preços com tendência de alta
    base_price = 100
    prices = [base_price * (1 + 0.001 * i) for i in range(252)]
    
    df = pd.DataFrame({
        'date': dates,
        'adj_close': prices
    })
    df.set_index('date', inplace=True)
    return df


@pytest.fixture
def sample_prices_6m():
    """Fixture com 6 meses de dados de preços diários."""
    dates = pd.date_range(end=datetime.now(), periods=126, freq='D')
    base_price = 100
    prices = [base_price * (1 + 0.001 * i) for i in range(126)]
    
    df = pd.DataFrame({
        'date': dates,
        'adj_close': prices
    })
    df.set_index('date', inplace=True)
    return df


@pytest.fixture
def sample_prices_90d():
    """Fixture com 90 dias de dados de preços."""
    dates = pd.date_range(end=datetime.now(), periods=91, freq='D')
    base_price = 100
    prices = [base_price * (1 + 0.001 * i) for i in range(91)]
    
    df = pd.DataFrame({
        'date': dates,
        'adj_close': prices
    })
    df.set_index('date', inplace=True)
    return df


class TestReturn6MCalculation:
    """Testes para cálculo de retorno de 6 meses. Valida: Requisito 3.1"""
    
    def test_return_6m_with_valid_data(self, calculator, sample_prices_1y):
        """Testa cálculo de retorno de 6 meses com dados válidos."""
        ret = calculator.calculate_return_6m(sample_prices_1y)
        
        # Verificar que retorno foi calculado
        assert ret is not None
        assert isinstance(ret, float)
        
        # Com tendência de alta, retorno deve ser positivo
        assert ret > 0
    
    def test_return_6m_exact_calculation(self, calculator):
        """Testa cálculo exato de retorno de 6 meses."""
        # Criar dados simples: preço inicial 100, final 120
        dates = pd.date_range(end=datetime.now(), periods=126, freq='D')
        prices = [100] * 126
        prices[-1] = 120  # Último preço = 120
        
        df = pd.DataFrame({
            'date': dates,
            'adj_close': prices
        })
        df.set_index('date', inplace=True)
        
        ret = calculator.calculate_return_6m(df)
        expected = (120 / 100) - 1  # 0.20 ou 20%
        assert ret == pytest.approx(expected, rel=1e-6)
    
    def test_return_6m_insufficient_data(self, calculator):
        """
        Testa que retorno de 6m lança erro com dados insuficientes.
        Valida: Requisito 3.8
        """
        # Apenas 100 dias (menos que 126 necessários)
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'adj_close': [100] * 100
        })
        df.set_index('date', inplace=True)
        
        with pytest.raises(InsufficientDataError):
            calculator.calculate_return_6m(df)
    
    def test_return_6m_missing_column(self, calculator):
        """Testa que retorno de 6m lança erro quando coluna adj_close está faltando."""
        dates = pd.date_range(end=datetime.now(), periods=126, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'close': [100] * 126  # Coluna errada
        })
        df.set_index('date', inplace=True)
        
        with pytest.raises(InsufficientDataError):
            calculator.calculate_return_6m(df)
    
    def test_return_6m_zero_initial_price(self, calculator):
        """Testa que retorno de 6m lança erro quando preço inicial é zero."""
        dates = pd.date_range(end=datetime.now(), periods=126, freq='D')
        prices = [0] + [100] * 125
        
        df = pd.DataFrame({
            'date': dates,
            'adj_close': prices
        })
        df.set_index('date', inplace=True)
        
        with pytest.raises(CalculationError):
            calculator.calculate_return_6m(df)


class TestReturn12MCalculation:
    """Testes para cálculo de retorno de 12 meses. Valida: Requisito 3.2"""
    
    def test_return_12m_with_valid_data(self, calculator, sample_prices_1y):
        """Testa cálculo de retorno de 12 meses com dados válidos."""
        ret = calculator.calculate_return_12m(sample_prices_1y)
        
        # Verificar que retorno foi calculado
        assert ret is not None
        assert isinstance(ret, float)
        
        # Com tendência de alta, retorno deve ser positivo
        assert ret > 0
    
    def test_return_12m_exact_calculation(self, calculator):
        """Testa cálculo exato de retorno de 12 meses."""
        # Criar dados simples: preço inicial 100, final 150
        dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
        prices = [100] * 252
        prices[-1] = 150  # Último preço = 150
        
        df = pd.DataFrame({
            'date': dates,
            'adj_close': prices
        })
        df.set_index('date', inplace=True)
        
        ret = calculator.calculate_return_12m(df)
        expected = (150 / 100) - 1  # 0.50 ou 50%
        assert ret == pytest.approx(expected, rel=1e-6)
    
    def test_return_12m_insufficient_data(self, calculator, sample_prices_6m):
        """
        Testa que retorno de 12m lança erro com dados insuficientes.
        Valida: Requisito 3.8
        """
        with pytest.raises(InsufficientDataError):
            calculator.calculate_return_12m(sample_prices_6m)


class TestRSI14Calculation:
    """Testes para cálculo de RSI. Valida: Requisito 3.3"""
    
    def test_rsi_with_valid_data(self, calculator, sample_prices_90d):
        """Testa cálculo de RSI com dados válidos."""
        rsi = calculator.calculate_rsi_14(sample_prices_90d)
        
        # Verificar que RSI foi calculado
        assert rsi is not None
        assert isinstance(rsi, float)
        
        # RSI deve estar entre 0 e 100
        assert 0 <= rsi <= 100
    
    def test_rsi_upper_limit(self, calculator):
        """
        Testa RSI em limite superior (preços sempre subindo).
        Caso extremo: Requisito 3.3
        """
        # Criar série com preços sempre subindo
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        prices = [100 + i * 2 for i in range(30)]  # Sempre subindo
        
        df = pd.DataFrame({
            'date': dates,
            'adj_close': prices
        })
        df.set_index('date', inplace=True)
        
        rsi = calculator.calculate_rsi_14(df)
        
        # RSI deve estar próximo de 100 (sobrecomprado)
        assert rsi > 70  # Geralmente considerado sobrecomprado
        assert rsi <= 100
    
    def test_rsi_lower_limit(self, calculator):
        """
        Testa RSI em limite inferior (preços sempre caindo).
        Caso extremo: Requisito 3.3
        """
        # Criar série com preços sempre caindo
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        prices = [100 - i * 2 for i in range(30)]  # Sempre caindo
        
        df = pd.DataFrame({
            'date': dates,
            'adj_close': prices
        })
        df.set_index('date', inplace=True)
        
        rsi = calculator.calculate_rsi_14(df)
        
        # RSI deve estar próximo de 0 (sobrevendido)
        assert rsi < 30  # Geralmente considerado sobrevendido
        assert rsi >= 0
    
    def test_rsi_insufficient_data(self, calculator):
        """
        Testa que RSI lança erro com dados insuficientes.
        Valida: Requisito 3.8
        """
        # Apenas 10 dias (menos que 15 necessários)
        dates = pd.date_range(end=datetime.now(), periods=10, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'adj_close': [100] * 10
        })
        df.set_index('date', inplace=True)
        
        with pytest.raises(InsufficientDataError):
            calculator.calculate_rsi_14(df)
    
    def test_rsi_no_losses(self, calculator):
        """
        Testa RSI quando não há perdas (apenas ganhos).
        Caso extremo: Requisito 3.3
        """
        dates = pd.date_range(end=datetime.now(), periods=20, freq='D')
        prices = [100] * 20
        prices[10:] = [100 + i for i in range(10)]  # Apenas ganhos após dia 10
        
        df = pd.DataFrame({
            'date': dates,
            'adj_close': prices
        })
        df.set_index('date', inplace=True)
        
        rsi = calculator.calculate_rsi_14(df)
        
        # Quando não há perdas, RSI deve ser 100
        assert rsi == pytest.approx(100.0, rel=1e-6)


class TestVolatility90DCalculation:
    """Testes para cálculo de volatilidade. Valida: Requisito 3.4"""
    
    def test_volatility_with_valid_data(self, calculator, sample_prices_90d):
        """Testa cálculo de volatilidade com dados válidos."""
        vol = calculator.calculate_volatility_90d(sample_prices_90d)
        
        # Verificar que volatilidade foi calculada
        assert vol is not None
        assert isinstance(vol, float)
        
        # Volatilidade deve ser positiva
        assert vol > 0
    
    def test_volatility_zero(self, calculator):
        """
        Testa volatilidade zero (preços constantes).
        Caso extremo: Requisito 3.4
        """
        dates = pd.date_range(end=datetime.now(), periods=91, freq='D')
        prices = [100] * 91  # Preços constantes
        
        df = pd.DataFrame({
            'date': dates,
            'adj_close': prices
        })
        df.set_index('date', inplace=True)
        
        vol = calculator.calculate_volatility_90d(df)
        
        # Volatilidade deve ser zero ou muito próxima de zero
        assert vol == pytest.approx(0.0, abs=1e-10)
    
    def test_volatility_high(self, calculator):
        """
        Testa volatilidade alta (preços muito variáveis).
        Caso extremo: Requisito 3.4
        """
        dates = pd.date_range(end=datetime.now(), periods=91, freq='D')
        # Criar preços oscilando muito
        prices = [100 + (10 if i % 2 == 0 else -10) for i in range(91)]
        
        df = pd.DataFrame({
            'date': dates,
            'adj_close': prices
        })
        df.set_index('date', inplace=True)
        
        vol = calculator.calculate_volatility_90d(df)
        
        # Volatilidade deve ser alta
        assert vol > 0.1  # Mais de 10% anualizado
    
    def test_volatility_insufficient_data(self, calculator):
        """
        Testa que volatilidade lança erro com dados insuficientes.
        Valida: Requisito 3.8
        """
        # Apenas 80 dias (menos que 91 necessários)
        dates = pd.date_range(end=datetime.now(), periods=80, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'adj_close': [100] * 80
        })
        df.set_index('date', inplace=True)
        
        with pytest.raises(InsufficientDataError):
            calculator.calculate_volatility_90d(df)


class TestRecentDrawdownCalculation:
    """Testes para cálculo de drawdown. Valida: Requisito 3.5"""
    
    def test_drawdown_with_valid_data(self, calculator, sample_prices_90d):
        """Testa cálculo de drawdown com dados válidos."""
        dd = calculator.calculate_recent_drawdown(sample_prices_90d)
        
        # Verificar que drawdown foi calculado
        assert dd is not None
        assert isinstance(dd, float)
        
        # Drawdown deve ser <= 0 (zero ou negativo)
        assert dd <= 0
    
    def test_drawdown_at_peak(self, calculator):
        """
        Testa drawdown quando preço atual está no pico.
        Caso extremo: Requisito 3.5
        """
        dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
        # Preços subindo até o final
        prices = [100 + i for i in range(90)]
        
        df = pd.DataFrame({
            'date': dates,
            'adj_close': prices
        })
        df.set_index('date', inplace=True)
        
        dd = calculator.calculate_recent_drawdown(df)
        
        # Drawdown deve ser zero (no pico)
        assert dd == pytest.approx(0.0, abs=1e-10)
    
    def test_drawdown_after_decline(self, calculator):
        """Testa drawdown após queda de preço."""
        dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
        # Preços sobem até dia 50, depois caem
        prices = [100 + i for i in range(50)] + [150 - i for i in range(40)]
        
        df = pd.DataFrame({
            'date': dates,
            'adj_close': prices
        })
        df.set_index('date', inplace=True)
        
        dd = calculator.calculate_recent_drawdown(df)
        
        # Drawdown deve ser negativo
        assert dd < 0
        
        # Verificar cálculo aproximado
        peak = max(prices)
        current = prices[-1]
        expected = (current - peak) / peak
        assert dd == pytest.approx(expected, rel=1e-6)
    
    def test_drawdown_insufficient_data(self, calculator):
        """
        Testa que drawdown lança erro com dados insuficientes.
        Valida: Requisito 3.8
        """
        # Apenas 80 dias (menos que 90 necessários)
        dates = pd.date_range(end=datetime.now(), periods=80, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'adj_close': [100] * 80
        })
        df.set_index('date', inplace=True)
        
        with pytest.raises(InsufficientDataError):
            calculator.calculate_recent_drawdown(df)


class TestCalculateAllFactors:
    """
    Testes para cálculo de todos os fatores.
    Valida: Requisitos 3.1-3.5, 3.8
    """
    
    def test_calculate_all_factors_complete_data(self, calculator, sample_prices_1y):
        """Testa cálculo de todos os fatores com dados completos."""
        factors = calculator.calculate_all_factors(
            ticker='TEST',
            prices=sample_prices_1y
        )
        
        # Verificar que todos os fatores foram calculados
        assert factors['return_6m'] is not None
        assert factors['return_12m'] is not None
        assert factors['rsi_14'] is not None
        assert factors['volatility_90d'] is not None
        assert factors['recent_drawdown'] is not None
        
        # Verificar tipos
        assert isinstance(factors['return_6m'], float)
        assert isinstance(factors['return_12m'], float)
        assert isinstance(factors['rsi_14'], float)
        assert isinstance(factors['volatility_90d'], float)
        assert isinstance(factors['recent_drawdown'], float)
        
        # Verificar ranges razoáveis
        assert 0 <= factors['rsi_14'] <= 100
        assert factors['volatility_90d'] >= 0
        assert factors['recent_drawdown'] <= 0
    
    def test_calculate_all_factors_insufficient_data(self, calculator):
        """
        Testa que fatores com dados insuficientes retornam None.
        Valida: Requisito 3.8
        """
        # Apenas 50 dias (insuficiente para a maioria dos fatores)
        dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'adj_close': [100] * 50
        })
        df.set_index('date', inplace=True)
        
        factors = calculator.calculate_all_factors(
            ticker='TEST',
            prices=df
        )
        
        # Fatores que requerem mais dados devem ser None
        assert factors['return_6m'] is None
        assert factors['return_12m'] is None
        
        # RSI pode ser calculado com 15+ dias
        assert factors['rsi_14'] is not None
        
        # Volatilidade e drawdown requerem 90+ dias
        assert factors['volatility_90d'] is None
        assert factors['recent_drawdown'] is None
    
    def test_calculate_all_factors_partial_data(self, calculator, sample_prices_6m):
        """
        Testa cálculo com dados parciais (6 meses).
        Valida: Requisito 3.8
        """
        factors = calculator.calculate_all_factors(
            ticker='TEST',
            prices=sample_prices_6m
        )
        
        # Fatores de 6 meses devem ser calculados
        assert factors['return_6m'] is not None
        assert factors['rsi_14'] is not None
        assert factors['volatility_90d'] is not None
        assert factors['recent_drawdown'] is not None
        
        # Fator de 12 meses deve ser None
        assert factors['return_12m'] is None



class TestVolatility180DCalculation:
    """Testes para cálculo de volatilidade de 180 dias. Valida: Requisito 4.2"""
    
    def test_volatility_180d_with_valid_data(self, calculator):
        """Testa cálculo de volatilidade de 180 dias com dados válidos."""
        dates = pd.date_range(end=datetime.now(), periods=181, freq='D')
        base_price = 100
        prices = [base_price * (1 + 0.001 * i) for i in range(181)]
        
        df = pd.DataFrame({
            'date': dates,
            'adj_close': prices
        })
        df.set_index('date', inplace=True)
        
        vol = calculator.calculate_volatility_180d(df)
        
        # Verificar que volatilidade foi calculada
        assert vol is not None
        assert isinstance(vol, float)
        
        # Volatilidade deve ser positiva
        assert vol > 0
    
    def test_volatility_180d_zero(self, calculator):
        """
        Testa volatilidade de 180 dias zero (preços constantes).
        Caso extremo: Requisito 4.2
        """
        dates = pd.date_range(end=datetime.now(), periods=181, freq='D')
        prices = [100] * 181  # Preços constantes
        
        df = pd.DataFrame({
            'date': dates,
            'adj_close': prices
        })
        df.set_index('date', inplace=True)
        
        vol = calculator.calculate_volatility_180d(df)
        
        # Volatilidade deve ser zero ou muito próxima de zero
        assert vol == pytest.approx(0.0, abs=1e-10)
    
    def test_volatility_180d_insufficient_data(self, calculator):
        """
        Testa que volatilidade de 180 dias lança erro com dados insuficientes.
        Valida: Requisito 4.2
        """
        # Apenas 150 dias (menos que 181 necessários)
        dates = pd.date_range(end=datetime.now(), periods=150, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'adj_close': [100] * 150
        })
        df.set_index('date', inplace=True)
        
        with pytest.raises(InsufficientDataError):
            calculator.calculate_volatility_180d(df)


class TestMaxDrawdown3YCalculation:
    """Testes para cálculo de drawdown máximo de 3 anos. Valida: Requisito 4.3"""
    
    def test_max_drawdown_3y_with_valid_data(self, calculator):
        """Testa cálculo de drawdown máximo de 3 anos com dados válidos."""
        dates = pd.date_range(end=datetime.now(), periods=756, freq='D')
        base_price = 100
        prices = [base_price * (1 + 0.001 * i) for i in range(756)]
        
        df = pd.DataFrame({
            'date': dates,
            'adj_close': prices
        })
        df.set_index('date', inplace=True)
        
        dd = calculator.calculate_max_drawdown_3y(df)
        
        # Verificar que drawdown foi calculado
        assert dd is not None
        assert isinstance(dd, float)
        
        # Drawdown deve ser <= 0 (zero ou negativo)
        assert dd <= 0
    
    def test_max_drawdown_3y_at_peak(self, calculator):
        """
        Testa drawdown máximo quando preços estão sempre subindo.
        Caso extremo: Requisito 4.3
        """
        dates = pd.date_range(end=datetime.now(), periods=756, freq='D')
        # Preços sempre subindo
        prices = [100 + i * 0.1 for i in range(756)]
        
        df = pd.DataFrame({
            'date': dates,
            'adj_close': prices
        })
        df.set_index('date', inplace=True)
        
        dd = calculator.calculate_max_drawdown_3y(df)
        
        # Drawdown deve ser zero (sempre no pico)
        assert dd == pytest.approx(0.0, abs=1e-10)
    
    def test_max_drawdown_3y_with_crash(self, calculator):
        """Testa drawdown máximo com queda significativa."""
        dates = pd.date_range(end=datetime.now(), periods=756, freq='D')
        # Preços sobem até dia 400, depois caem 50%
        prices = []
        for i in range(756):
            if i < 400:
                prices.append(100 + i * 0.5)  # Sobe até 300
            else:
                prices.append(300 - (i - 400) * 0.5)  # Cai de volta
        
        df = pd.DataFrame({
            'date': dates,
            'adj_close': prices
        })
        df.set_index('date', inplace=True)
        
        dd = calculator.calculate_max_drawdown_3y(df)
        
        # Drawdown deve ser negativo e significativo
        assert dd < -0.3  # Pelo menos -30%
        
        # Verificar que é o drawdown máximo correto
        peak = max(prices)
        trough = min(prices[prices.index(peak):])
        expected = (trough - peak) / peak
        assert dd == pytest.approx(expected, rel=1e-6)
    
    def test_max_drawdown_3y_insufficient_data(self, calculator):
        """
        Testa que drawdown máximo de 3 anos lança erro com dados insuficientes.
        Valida: Requisito 4.3
        """
        # Apenas 500 dias (menos que 756 necessários)
        dates = pd.date_range(end=datetime.now(), periods=500, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'adj_close': [100] * 500
        })
        df.set_index('date', inplace=True)
        
        with pytest.raises(InsufficientDataError):
            calculator.calculate_max_drawdown_3y(df)


class TestCalculateAllFactorsEnhanced:
    """
    Testes para cálculo de todos os fatores incluindo novos fatores.
    Valida: Requisitos 3.1-3.5, 4.2, 4.3
    """
    
    def test_calculate_all_factors_with_3y_data(self, calculator):
        """Testa cálculo de todos os fatores com 3 anos de dados."""
        dates = pd.date_range(end=datetime.now(), periods=756, freq='D')
        base_price = 100
        prices = [base_price * (1 + 0.001 * i) for i in range(756)]
        
        df = pd.DataFrame({
            'date': dates,
            'adj_close': prices
        })
        df.set_index('date', inplace=True)
        
        factors = calculator.calculate_all_factors(
            ticker='TEST',
            prices=df
        )
        
        # Verificar que todos os fatores foram calculados
        assert factors['return_6m'] is not None
        assert factors['return_12m'] is not None
        assert factors['rsi_14'] is not None
        assert factors['volatility_90d'] is not None
        assert factors['volatility_180d'] is not None
        assert factors['recent_drawdown'] is not None
        assert factors['max_drawdown_3y'] is not None
        
        # Verificar tipos
        assert isinstance(factors['volatility_180d'], float)
        assert isinstance(factors['max_drawdown_3y'], float)
        
        # Verificar ranges razoáveis
        assert factors['volatility_180d'] >= 0
        assert factors['max_drawdown_3y'] <= 0
    
    def test_calculate_all_factors_insufficient_for_3y(self, calculator):
        """
        Testa que fatores de 3 anos retornam None com dados insuficientes.
        Valida: Requisito 4.2, 4.3
        """
        # Apenas 1 ano de dados (252 dias)
        dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'adj_close': [100] * 252
        })
        df.set_index('date', inplace=True)
        
        factors = calculator.calculate_all_factors(
            ticker='TEST',
            prices=df
        )
        
        # Fatores de curto prazo devem ser calculados
        assert factors['return_6m'] is not None
        assert factors['return_12m'] is not None
        assert factors['volatility_90d'] is not None
        
        # Fatores de 180 dias devem ser calculados
        assert factors['volatility_180d'] is not None
        
        # Fator de 3 anos deve ser None
        assert factors['max_drawdown_3y'] is None
