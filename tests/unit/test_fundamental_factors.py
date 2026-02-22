"""
Testes unitários para cálculo de fatores fundamentalistas.

Valida: Requisitos 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.10
"""

import pytest
from app.factor_engine.fundamental_factors import FundamentalFactorCalculator
from app.core.exceptions import InsufficientDataError, CalculationError


@pytest.fixture
def calculator():
    """Fixture para criar instância do calculador."""
    return FundamentalFactorCalculator()


@pytest.fixture
def sample_fundamentals():
    """Fixture com dados fundamentalistas de exemplo."""
    return {
        'net_income': 1000000,
        'revenue': 5000000,
        'shareholders_equity': 8000000,
        'ebitda': 1500000,
        'total_debt': 3000000,
        'eps': 2.50,
        'enterprise_value': 12000000,
        'book_value_per_share': 20.0
    }


class TestROECalculation:
    """Testes para cálculo de ROE. Valida: Requisito 2.1"""
    
    def test_roe_with_valid_data(self, calculator, sample_fundamentals):
        """Testa cálculo de ROE com dados válidos."""
        roe = calculator.calculate_roe(sample_fundamentals)
        expected = 1000000 / 8000000  # 0.125 ou 12.5%
        assert roe == pytest.approx(expected, rel=1e-6)
    
    def test_roe_missing_net_income(self, calculator):
        """Testa que ROE lança erro quando net_income está faltando."""
        fundamentals = {'shareholders_equity': 8000000}
        with pytest.raises(InsufficientDataError):
            calculator.calculate_roe(fundamentals)
    
    def test_roe_missing_shareholders_equity(self, calculator):
        """Testa que ROE lança erro quando shareholders_equity está faltando."""
        fundamentals = {'net_income': 1000000}
        with pytest.raises(InsufficientDataError):
            calculator.calculate_roe(fundamentals)
    
    def test_roe_zero_shareholders_equity(self, calculator):
        """Testa que ROE lança erro quando shareholders_equity é zero."""
        fundamentals = {'net_income': 1000000, 'shareholders_equity': 0}
        with pytest.raises(CalculationError):
            calculator.calculate_roe(fundamentals)
    
    def test_roe_negative_shareholders_equity(self, calculator):
        """Testa que ROE lança erro quando shareholders_equity é negativo."""
        fundamentals = {'net_income': 1000000, 'shareholders_equity': -1000}
        with pytest.raises(CalculationError):
            calculator.calculate_roe(fundamentals)


class TestNetMarginCalculation:
    """Testes para cálculo de margem líquida. Valida: Requisito 2.2"""
    
    def test_net_margin_with_valid_data(self, calculator, sample_fundamentals):
        """Testa cálculo de margem líquida com dados válidos."""
        margin = calculator.calculate_net_margin(sample_fundamentals)
        expected = 1000000 / 5000000  # 0.20 ou 20%
        assert margin == pytest.approx(expected, rel=1e-6)
    
    def test_net_margin_missing_net_income(self, calculator):
        """Testa que margem líquida lança erro quando net_income está faltando."""
        fundamentals = {'revenue': 5000000}
        with pytest.raises(InsufficientDataError):
            calculator.calculate_net_margin(fundamentals)
    
    def test_net_margin_missing_revenue(self, calculator):
        """Testa que margem líquida lança erro quando revenue está faltando."""
        fundamentals = {'net_income': 1000000}
        with pytest.raises(InsufficientDataError):
            calculator.calculate_net_margin(fundamentals)
    
    def test_net_margin_zero_revenue(self, calculator):
        """Testa que margem líquida lança erro quando revenue é zero."""
        fundamentals = {'net_income': 1000000, 'revenue': 0}
        with pytest.raises(CalculationError):
            calculator.calculate_net_margin(fundamentals)


class TestRevenueGrowthCalculation:
    """Testes para cálculo de crescimento de receita. Valida: Requisito 2.3"""
    
    def test_revenue_growth_3y_with_valid_data(self, calculator):
        """Testa cálculo de crescimento de receita com 3 anos de dados."""
        history = [
            {'revenue': 1000000},  # Ano 0
            {'revenue': 1200000},  # Ano 1
            {'revenue': 1440000},  # Ano 2
            {'revenue': 1728000}   # Ano 3
        ]
        growth = calculator.calculate_revenue_growth_3y(history)
        # CAGR = (1728000/1000000)^(1/3) - 1 ≈ 0.20 ou 20%
        expected = (1728000 / 1000000) ** (1/3) - 1
        assert growth == pytest.approx(expected, rel=1e-6)
    
    def test_revenue_growth_with_2_periods(self, calculator):
        """Testa cálculo de crescimento com apenas 2 períodos."""
        history = [
            {'revenue': 1000000},
            {'revenue': 1200000}
        ]
        growth = calculator.calculate_revenue_growth_3y(history)
        expected = (1200000 / 1000000) - 1  # 0.20 ou 20%
        assert growth == pytest.approx(expected, rel=1e-6)
    
    def test_revenue_growth_insufficient_data(self, calculator):
        """Testa que crescimento lança erro com dados insuficientes."""
        history = [{'revenue': 1000000}]
        with pytest.raises(InsufficientDataError):
            calculator.calculate_revenue_growth_3y(history)
    
    def test_revenue_growth_missing_revenue(self, calculator):
        """Testa que crescimento lança erro quando revenue está faltando."""
        history = [
            {'revenue': 1000000},
            {'other_field': 1200000}
        ]
        with pytest.raises(InsufficientDataError):
            calculator.calculate_revenue_growth_3y(history)
    
    def test_revenue_growth_zero_initial_revenue(self, calculator):
        """Testa que crescimento lança erro quando revenue inicial é zero."""
        history = [
            {'revenue': 0},
            {'revenue': 1200000}
        ]
        with pytest.raises(CalculationError):
            calculator.calculate_revenue_growth_3y(history)


class TestDebtToEBITDACalculation:
    """Testes para cálculo de Dívida/EBITDA. Valida: Requisito 2.4"""
    
    def test_debt_to_ebitda_with_valid_data(self, calculator, sample_fundamentals):
        """Testa cálculo de Dívida/EBITDA com dados válidos."""
        ratio = calculator.calculate_debt_to_ebitda(sample_fundamentals)
        expected = 3000000 / 1500000  # 2.0
        assert ratio == pytest.approx(expected, rel=1e-6)
    
    def test_debt_to_ebitda_missing_total_debt(self, calculator):
        """Testa que Dívida/EBITDA lança erro quando total_debt está faltando."""
        fundamentals = {'ebitda': 1500000}
        with pytest.raises(InsufficientDataError):
            calculator.calculate_debt_to_ebitda(fundamentals)
    
    def test_debt_to_ebitda_missing_ebitda(self, calculator):
        """Testa que Dívida/EBITDA lança erro quando ebitda está faltando."""
        fundamentals = {'total_debt': 3000000}
        with pytest.raises(InsufficientDataError):
            calculator.calculate_debt_to_ebitda(fundamentals)
    
    def test_debt_to_ebitda_zero_ebitda(self, calculator):
        """Testa que Dívida/EBITDA lança erro quando ebitda é zero."""
        fundamentals = {'total_debt': 3000000, 'ebitda': 0}
        with pytest.raises(CalculationError):
            calculator.calculate_debt_to_ebitda(fundamentals)


class TestPERatioCalculation:
    """Testes para cálculo de P/L. Valida: Requisito 2.5"""
    
    def test_pe_ratio_with_valid_data(self, calculator, sample_fundamentals):
        """Testa cálculo de P/L com dados válidos."""
        price = 50.0
        ratio = calculator.calculate_pe_ratio(sample_fundamentals, price)
        expected = 50.0 / 2.50  # 20.0
        assert ratio == pytest.approx(expected, rel=1e-6)
    
    def test_pe_ratio_missing_eps(self, calculator):
        """Testa que P/L lança erro quando eps está faltando."""
        fundamentals = {}
        with pytest.raises(InsufficientDataError):
            calculator.calculate_pe_ratio(fundamentals, 50.0)
    
    def test_pe_ratio_missing_price(self, calculator, sample_fundamentals):
        """Testa que P/L lança erro quando price está faltando."""
        with pytest.raises(InsufficientDataError):
            calculator.calculate_pe_ratio(sample_fundamentals, None)
    
    def test_pe_ratio_zero_eps(self, calculator):
        """Testa que P/L lança erro quando eps é zero."""
        fundamentals = {'eps': 0}
        with pytest.raises(CalculationError):
            calculator.calculate_pe_ratio(fundamentals, 50.0)


class TestEVToEBITDACalculation:
    """Testes para cálculo de EV/EBITDA. Valida: Requisito 2.6"""
    
    def test_ev_ebitda_with_valid_data(self, calculator, sample_fundamentals):
        """Testa cálculo de EV/EBITDA com dados válidos."""
        ratio = calculator.calculate_ev_ebitda(sample_fundamentals)
        expected = 12000000 / 1500000  # 8.0
        assert ratio == pytest.approx(expected, rel=1e-6)
    
    def test_ev_ebitda_missing_enterprise_value(self, calculator):
        """Testa que EV/EBITDA lança erro quando enterprise_value está faltando."""
        fundamentals = {'ebitda': 1500000}
        with pytest.raises(InsufficientDataError):
            calculator.calculate_ev_ebitda(fundamentals)
    
    def test_ev_ebitda_missing_ebitda(self, calculator):
        """Testa que EV/EBITDA lança erro quando ebitda está faltando."""
        fundamentals = {'enterprise_value': 12000000}
        with pytest.raises(InsufficientDataError):
            calculator.calculate_ev_ebitda(fundamentals)
    
    def test_ev_ebitda_zero_ebitda(self, calculator):
        """Testa que EV/EBITDA lança erro quando ebitda é zero."""
        fundamentals = {'enterprise_value': 12000000, 'ebitda': 0}
        with pytest.raises(CalculationError):
            calculator.calculate_ev_ebitda(fundamentals)


class TestPBRatioCalculation:
    """Testes para cálculo de P/VP. Valida: Requisito 2.7"""
    
    def test_pb_ratio_with_valid_data(self, calculator, sample_fundamentals):
        """Testa cálculo de P/VP com dados válidos."""
        price = 50.0
        ratio = calculator.calculate_pb_ratio(sample_fundamentals, price)
        expected = 50.0 / 20.0  # 2.5
        assert ratio == pytest.approx(expected, rel=1e-6)
    
    def test_pb_ratio_missing_book_value(self, calculator):
        """Testa que P/VP lança erro quando book_value_per_share está faltando."""
        fundamentals = {}
        with pytest.raises(InsufficientDataError):
            calculator.calculate_pb_ratio(fundamentals, 50.0)
    
    def test_pb_ratio_missing_price(self, calculator, sample_fundamentals):
        """Testa que P/VP lança erro quando price está faltando."""
        with pytest.raises(InsufficientDataError):
            calculator.calculate_pb_ratio(sample_fundamentals, None)
    
    def test_pb_ratio_zero_book_value(self, calculator):
        """Testa que P/VP lança erro quando book_value é zero."""
        fundamentals = {'book_value_per_share': 0}
        with pytest.raises(CalculationError):
            calculator.calculate_pb_ratio(fundamentals, 50.0)


class TestCalculateAllFactors:
    """
    Testes para cálculo de todos os fatores.
    Valida: Requisitos 2.1-2.7, 2.10
    """
    
    def test_calculate_all_factors_complete_data(self, calculator, sample_fundamentals):
        """Testa cálculo de todos os fatores com dados completos."""
        history = [
            {'revenue': 4000000},
            {'revenue': 4500000},
            {'revenue': 5000000}
        ]
        price = 50.0
        
        factors = calculator.calculate_all_factors(
            ticker='TEST',
            fundamentals_data=sample_fundamentals,
            fundamentals_history=history,
            current_price=price
        )
        
        # Verificar que todos os fatores foram calculados
        assert factors['roe'] is not None
        assert factors['net_margin'] is not None
        assert factors['revenue_growth_3y'] is not None
        assert factors['debt_to_ebitda'] is not None
        assert factors['pe_ratio'] is not None
        assert factors['ev_ebitda'] is not None
        assert factors['pb_ratio'] is not None
        
        # Verificar valores aproximados
        assert factors['roe'] == pytest.approx(0.125, rel=1e-6)
        assert factors['net_margin'] == pytest.approx(0.20, rel=1e-6)
        assert factors['debt_to_ebitda'] == pytest.approx(2.0, rel=1e-6)
        assert factors['pe_ratio'] == pytest.approx(20.0, rel=1e-6)
        assert factors['ev_ebitda'] == pytest.approx(8.0, rel=1e-6)
        assert factors['pb_ratio'] == pytest.approx(2.5, rel=1e-6)
    
    def test_calculate_all_factors_missing_data(self, calculator):
        """
        Testa que fatores com dados faltantes retornam None.
        Valida: Requisito 2.10
        """
        incomplete_fundamentals = {
            'net_income': 1000000,
            'revenue': 5000000
            # Faltando outros campos
        }
        
        factors = calculator.calculate_all_factors(
            ticker='TEST',
            fundamentals_data=incomplete_fundamentals,
            fundamentals_history=None,
            current_price=None
        )
        
        # Fatores que podem ser calculados
        assert factors['net_margin'] is not None
        
        # Fatores que não podem ser calculados devem ser None
        assert factors['roe'] is None
        assert factors['revenue_growth_3y'] is None
        assert factors['debt_to_ebitda'] is None
        assert factors['pe_ratio'] is None
        assert factors['ev_ebitda'] is None
        assert factors['pb_ratio'] is None
    
    def test_calculate_all_factors_no_price(self, calculator, sample_fundamentals):
        """
        Testa que fatores dependentes de preço retornam None quando preço não fornecido.
        Valida: Requisito 2.10
        """
        factors = calculator.calculate_all_factors(
            ticker='TEST',
            fundamentals_data=sample_fundamentals,
            fundamentals_history=None,
            current_price=None
        )
        
        # Fatores independentes de preço devem ser calculados
        assert factors['roe'] is not None
        assert factors['net_margin'] is not None
        assert factors['debt_to_ebitda'] is not None
        assert factors['ev_ebitda'] is not None
        
        # Fatores dependentes de preço devem ser None
        assert factors['pe_ratio'] is None
        assert factors['pb_ratio'] is None
    
    def test_calculate_all_factors_no_history(self, calculator, sample_fundamentals):
        """
        Testa que crescimento de receita retorna None sem histórico.
        Valida: Requisito 2.10
        """
        factors = calculator.calculate_all_factors(
            ticker='TEST',
            fundamentals_data=sample_fundamentals,
            fundamentals_history=None,
            current_price=50.0
        )
        
        # Crescimento de receita deve ser None
        assert factors['revenue_growth_3y'] is None
        
        # Outros fatores devem ser calculados
        assert factors['roe'] is not None
        assert factors['net_margin'] is not None


class TestNetIncomeVolatility:
    """Testes para cálculo de volatilidade do lucro líquido. Valida: Requisito 2.4"""
    
    def test_net_income_volatility_with_valid_data(self, calculator):
        """Testa cálculo de volatilidade com dados válidos."""
        history = [
            {'net_income': 1000000},
            {'net_income': 1200000},
            {'net_income': 900000},
            {'net_income': 1100000}
        ]
        volatility = calculator.calculate_net_income_volatility(history)
        
        # Calcular manualmente para verificar
        import numpy as np
        incomes = [1000000, 1200000, 900000, 1100000]
        expected_cv = np.std(incomes, ddof=1) / abs(np.mean(incomes))
        
        assert volatility == pytest.approx(expected_cv, rel=1e-6)
    
    def test_net_income_volatility_insufficient_data(self, calculator):
        """Testa que volatilidade lança erro com dados insuficientes."""
        history = [{'net_income': 1000000}]
        with pytest.raises(InsufficientDataError):
            calculator.calculate_net_income_volatility(history)
    
    def test_net_income_volatility_missing_net_income(self, calculator):
        """Testa que volatilidade lança erro quando net_income está faltando."""
        history = [
            {'net_income': 1000000},
            {'other_field': 1200000}
        ]
        with pytest.raises(InsufficientDataError):
            calculator.calculate_net_income_volatility(history)
    
    def test_net_income_volatility_zero_mean(self, calculator):
        """Testa que volatilidade lança erro quando média é zero."""
        history = [
            {'net_income': 100000},
            {'net_income': -100000}
        ]
        with pytest.raises(CalculationError):
            calculator.calculate_net_income_volatility(history)


class TestFinancialStrength:
    """Testes para cálculo de força financeira. Valida: Requisitos 2.5, 2.6"""
    
    def test_financial_strength_strong(self, calculator):
        """Testa força financeira com baixa alavancagem (score = 1.0)."""
        fundamentals = {
            'total_debt': 1000000,
            'cash': 500000,
            'ebitda': 1000000
        }
        # net_debt = 500000, ratio = 0.5 < 2.0
        strength = calculator.calculate_financial_strength(fundamentals)
        assert strength == 1.0
    
    def test_financial_strength_moderate(self, calculator):
        """Testa força financeira com alavancagem moderada (score = 0.5)."""
        fundamentals = {
            'total_debt': 3000000,
            'cash': 0,
            'ebitda': 1000000
        }
        # net_debt = 3000000, ratio = 3.0 (entre 2 e 4)
        strength = calculator.calculate_financial_strength(fundamentals)
        assert strength == 0.5
    
    def test_financial_strength_weak(self, calculator):
        """Testa força financeira com alta alavancagem (score = 0.0)."""
        fundamentals = {
            'total_debt': 5000000,
            'cash': 0,
            'ebitda': 1000000
        }
        # net_debt = 5000000, ratio = 5.0 > 4.0
        strength = calculator.calculate_financial_strength(fundamentals)
        assert strength == 0.0
    
    def test_financial_strength_missing_data(self, calculator):
        """Testa que força financeira lança erro com dados faltantes."""
        fundamentals = {'total_debt': 1000000}
        with pytest.raises(InsufficientDataError):
            calculator.calculate_financial_strength(fundamentals)
    
    def test_financial_strength_zero_ebitda(self, calculator):
        """Testa que força financeira lança erro quando EBITDA é zero."""
        fundamentals = {
            'total_debt': 1000000,
            'cash': 500000,
            'ebitda': 0
        }
        with pytest.raises(CalculationError):
            calculator.calculate_financial_strength(fundamentals)


class TestROERobust:
    """Testes para cálculo de ROE robusto. Valida: Requisitos 2.1, 2.2, 2.3"""
    
    def test_roe_robust_with_3_years(self, calculator):
        """Testa ROE robusto com 3 anos de dados."""
        history = [
            {'net_income': 800000, 'shareholders_equity': 8000000},  # ROE = 0.10
            {'net_income': 1000000, 'shareholders_equity': 8000000},  # ROE = 0.125
            {'net_income': 1200000, 'shareholders_equity': 8000000}   # ROE = 0.15
        ]
        roe = calculator.calculate_roe_robust(history)
        
        # Média de [0.10, 0.125, 0.15] = 0.125
        assert roe == pytest.approx(0.125, rel=1e-6)
    
    def test_roe_robust_with_capping(self, calculator):
        """Testa que ROE robusto aplica cap em 50%."""
        history = [
            {'net_income': 4000000, 'shareholders_equity': 8000000},  # ROE = 0.50
            {'net_income': 5000000, 'shareholders_equity': 8000000},  # ROE = 0.625 -> capped
            {'net_income': 6000000, 'shareholders_equity': 8000000}   # ROE = 0.75 -> capped
        ]
        roe = calculator.calculate_roe_robust(history, max_roe_cap=0.50)
        
        # Após winsorização e cap, deve ser <= 0.50
        assert roe <= 0.50
    
    def test_roe_robust_insufficient_data(self, calculator):
        """Testa que ROE robusto lança erro com dados insuficientes."""
        history = [{'net_income': 1000000, 'shareholders_equity': 8000000}]
        with pytest.raises(InsufficientDataError):
            calculator.calculate_roe_robust(history)
    
    def test_roe_robust_missing_data(self, calculator):
        """Testa que ROE robusto lança erro quando dados estão faltando."""
        history = [
            {'net_income': 1000000, 'shareholders_equity': 8000000},
            {'net_income': 1200000}  # Faltando shareholders_equity
        ]
        with pytest.raises(InsufficientDataError):
            calculator.calculate_roe_robust(history)
    
    def test_roe_robust_zero_equity(self, calculator):
        """Testa que ROE robusto lança erro quando equity é zero."""
        history = [
            {'net_income': 1000000, 'shareholders_equity': 8000000},
            {'net_income': 1200000, 'shareholders_equity': 0}
        ]
        with pytest.raises(CalculationError):
            calculator.calculate_roe_robust(history)


class TestEnhancedFactorCalculations:
    """
    Testes unitários para cálculos de fatores aprimorados.
    Valida: Requisitos 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
    Task 3.9
    """
    
    def test_roe_capping_at_exactly_50_percent(self, calculator):
        """
        Testa que ROE é limitado exatamente em 50%.
        Valida: Requisito 2.3
        """
        history = [
            {'net_income': 100, 'shareholders_equity': 100},  # ROE = 100%
            {'net_income': 50, 'shareholders_equity': 100},   # ROE = 50%
            {'net_income': 30, 'shareholders_equity': 100}    # ROE = 30%
        ]
        
        roe = calculator.calculate_roe_robust(history, max_roe_cap=0.50)
        
        # Após winsorização e cap, o ROE deve ser <= 50%
        # Com winsorização, o valor de 100% será limitado ao 95º percentil
        # Depois aplicamos o cap de 50%
        assert roe <= 0.50
        assert roe > 0  # Deve ser positivo
    
    def test_financial_strength_with_low_debt_ratio(self, calculator):
        """
        Testa força financeira com baixa alavancagem (ratio < 2).
        Valida: Requisitos 2.5, 2.6
        """
        fundamentals = {
            'total_debt': 1000000,
            'cash': 500000,
            'ebitda': 1000000
        }
        # net_debt = 500000, ratio = 0.5 < 2.0
        strength = calculator.calculate_financial_strength(fundamentals)
        assert strength == 1.0
    
    def test_financial_strength_with_moderate_debt_ratio(self, calculator):
        """
        Testa força financeira com alavancagem moderada (2 <= ratio <= 4).
        Valida: Requisitos 2.5, 2.6
        """
        fundamentals = {
            'total_debt': 3000000,
            'cash': 0,
            'ebitda': 1000000
        }
        # net_debt = 3000000, ratio = 3.0 (entre 2 e 4)
        strength = calculator.calculate_financial_strength(fundamentals)
        assert strength == 0.5
    
    def test_financial_strength_with_high_debt_ratio(self, calculator):
        """
        Testa força financeira com alta alavancagem (ratio > 4).
        Valida: Requisitos 2.5, 2.6
        """
        fundamentals = {
            'total_debt': 5000000,
            'cash': 0,
            'ebitda': 1000000
        }
        # net_debt = 5000000, ratio = 5.0 > 4.0
        strength = calculator.calculate_financial_strength(fundamentals)
        assert strength == 0.0
    
    def test_financial_strength_at_boundary_2(self, calculator):
        """
        Testa força financeira exatamente no limite de 2.0.
        Valida: Requisitos 2.5, 2.6
        """
        fundamentals = {
            'total_debt': 2000000,
            'cash': 0,
            'ebitda': 1000000
        }
        # net_debt = 2000000, ratio = 2.0 (exatamente no limite)
        strength = calculator.calculate_financial_strength(fundamentals)
        # Deve ser 0.5 pois ratio >= 2.0
        assert strength == 0.5
    
    def test_financial_strength_at_boundary_4(self, calculator):
        """
        Testa força financeira exatamente no limite de 4.0.
        Valida: Requisitos 2.5, 2.6
        """
        fundamentals = {
            'total_debt': 4000000,
            'cash': 0,
            'ebitda': 1000000
        }
        # net_debt = 4000000, ratio = 4.0 (exatamente no limite)
        strength = calculator.calculate_financial_strength(fundamentals)
        # Deve ser 0.5 pois ratio <= 4.0
        assert strength == 0.5
    
    def test_net_income_volatility_with_zero_variance(self, calculator):
        """
        Testa volatilidade do lucro líquido quando todos os valores são iguais.
        Valida: Requisito 2.4
        """
        history = [
            {'net_income': 1000000},
            {'net_income': 1000000},
            {'net_income': 1000000}
        ]
        
        volatility = calculator.calculate_net_income_volatility(history)
        
        # Com variância zero, o coeficiente de variação deve ser 0
        assert volatility == pytest.approx(0.0, abs=1e-10)
    
    def test_net_income_volatility_with_varying_values(self, calculator):
        """
        Testa volatilidade do lucro líquido com valores variados.
        Valida: Requisito 2.4
        """
        history = [
            {'net_income': 1000000},
            {'net_income': 1500000},
            {'net_income': 800000}
        ]
        
        volatility = calculator.calculate_net_income_volatility(history)
        
        # Deve retornar um valor positivo
        assert volatility > 0
        # Deve ser um coeficiente de variação razoável
        assert volatility < 1.0  # CV < 100%
    
    def test_roe_robust_with_insufficient_history_less_than_3_years(self, calculator):
        """
        Testa ROE robusto com histórico insuficiente (< 3 anos mas >= 2).
        Valida: Requisito 2.1
        """
        history = [
            {'net_income': 800000, 'shareholders_equity': 8000000},  # ROE = 0.10
            {'net_income': 1000000, 'shareholders_equity': 8000000}  # ROE = 0.125
        ]
        
        # Deve funcionar com 2 períodos
        roe = calculator.calculate_roe_robust(history)
        
        # Deve retornar a média dos 2 valores
        assert roe > 0
        assert roe <= 0.50  # Respeitando o cap
    
    def test_calculate_all_factors_with_insufficient_history(self, calculator):
        """
        Testa cálculo de todos os fatores com histórico insuficiente.
        Valida: Requisitos 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
        """
        fundamentals = {
            'net_income': 1000000,
            'revenue': 5000000,
            'shareholders_equity': 8000000,
            'ebitda': 1500000,
            'total_debt': 3000000,
            'cash': 500000,
            'eps': 2.50,
            'enterprise_value': 12000000,
            'book_value_per_share': 20.0
        }
        
        # Histórico com apenas 1 período (insuficiente)
        history = [{'net_income': 1000000, 'shareholders_equity': 8000000, 'revenue': 5000000}]
        
        factors = calculator.calculate_all_factors(
            ticker='TEST',
            fundamentals_data=fundamentals,
            fundamentals_history=history,
            current_price=50.0
        )
        
        # Fatores que não dependem de histórico devem ser calculados
        assert factors['net_margin'] is not None
        assert factors['debt_to_ebitda'] is not None
        assert factors['financial_strength'] is not None
        assert factors['pe_ratio'] is not None
        assert factors['ev_ebitda'] is not None
        assert factors['pb_ratio'] is not None
        
        # Fatores que dependem de histórico devem ser None
        assert factors['revenue_growth_3y'] is None
        assert factors['net_income_volatility'] is None
        
        # ROE deve usar cálculo simples (fallback)
        assert factors['roe'] is not None
    
    def test_financial_strength_with_negative_net_debt(self, calculator):
        """
        Testa força financeira quando cash > total_debt (net_debt negativo).
        Valida: Requisitos 2.5, 2.6
        """
        fundamentals = {
            'total_debt': 1000000,
            'cash': 2000000,
            'ebitda': 1000000
        }
        # net_debt = -1000000, ratio = -1.0 < 2.0
        strength = calculator.calculate_financial_strength(fundamentals)
        # Deve retornar 1.0 (forte) pois ratio < 2.0
        assert strength == 1.0
