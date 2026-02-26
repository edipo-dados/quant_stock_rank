"""
Cálculo de fatores fundamentalistas mensais.

Valida: Requisitos 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7
"""

from typing import Dict, List, Optional, Tuple
from app.core.exceptions import InsufficientDataError, CalculationError
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class FundamentalFactorCalculator:
    """
    Calcula fatores fundamentalistas mensais a partir de dados brutos.
    
    Valida: Requisitos 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7
    """
    
    def __init__(self):
        """Inicializa o calculador de fatores fundamentalistas."""
        from app.factor_engine.normalizer import CrossSectionalNormalizer
        self.normalizer = CrossSectionalNormalizer()
    
    def _calculate_confidence_factor(self, periods_available: int, periods_ideal: int = 3) -> float:
        """
        Calcula fator de confiança baseado no histórico disponível.
        
        Args:
            periods_available: Número de períodos disponíveis
            periods_ideal: Número ideal de períodos (padrão: 3)
            
        Returns:
            Fator de confiança entre 0 e 1
            
        Examples:
            3 anos → 1.0
            2 anos → 0.66
            1 ano → 0.33
        """
        if periods_available >= periods_ideal:
            return 1.0
        return periods_available / periods_ideal
    
    def calculate_roe_robust(
        self,
        fundamentals_history: List[Dict],
        winsorize_percentiles: Tuple[float, float] = (0.05, 0.95),
        max_roe_cap: float = 0.50
    ) -> float:
        """
        Calcula ROE robusto usando média de 3 anos com winsorização.
        
        Passos:
        1. Calcula ROE para cada um dos últimos 3 anos
        2. Aplica winsorização nos percentis 5º/95º
        3. Calcula média
        4. Aplica cap em max_roe_cap (default 50%)
        
        Args:
            fundamentals_history: Lista de dicts com net_income, shareholders_equity
            winsorize_percentiles: Tupla de (lower, upper) percentis
            max_roe_cap: Valor máximo permitido de ROE
            
        Returns:
            ROE robusto como float
            
        Raises:
            InsufficientDataError: Se não há dados suficientes (mínimo 2 períodos)
            CalculationError: Se shareholders_equity é zero ou negativo
            
        Valida: Requisitos 2.1, 2.2, 2.3
        """
        try:
            if len(fundamentals_history) < 2:
                raise InsufficientDataError(
                    f"Need at least 2 periods for robust ROE, got {len(fundamentals_history)}"
                )
            
            # Calcular ROE para cada período
            roes = []
            for period in fundamentals_history:
                net_income = period.get('net_income')
                shareholders_equity = period.get('shareholders_equity')
                
                if net_income is None or shareholders_equity is None:
                    raise InsufficientDataError(
                        "Missing net_income or shareholders_equity in fundamentals history"
                    )
                
                if shareholders_equity <= 0:
                    raise CalculationError(
                        f"Invalid shareholders_equity for ROE: {shareholders_equity}"
                    )
                
                roe = net_income / shareholders_equity
                roes.append(roe)
            
            # Converter para Series para usar winsorização
            roe_series = pd.Series(roes)
            
            # Aplicar winsorização
            lower_pct, upper_pct = winsorize_percentiles
            winsorized_roes = self.normalizer.winsorize(
                roe_series,
                lower_percentile=lower_pct,
                upper_percentile=upper_pct
            )
            
            # Calcular média dos ROEs winsorized
            avg_roe = winsorized_roes.mean()
            
            # Aplicar cap
            capped_roe = min(avg_roe, max_roe_cap)
            
            return capped_roe
            
        except (TypeError, ValueError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating robust ROE: {e}")
    
    def calculate_roe(self, fundamentals: Dict) -> float:
        """
        Calcula ROE (Return on Equity).
        
        ROE = Net Income / Shareholders Equity
        
        Args:
            fundamentals: Dict contendo net_income e shareholders_equity
            
        Returns:
            ROE como float
            
        Raises:
            InsufficientDataError: Se dados necessários estão faltando
            CalculationError: Se shareholders_equity é zero ou negativo
            
        Valida: Requisito 2.1
        """
        try:
            net_income = fundamentals.get('net_income')
            shareholders_equity = fundamentals.get('shareholders_equity')
            
            if net_income is None or shareholders_equity is None:
                raise InsufficientDataError(
                    "Missing net_income or shareholders_equity for ROE calculation"
                )
            
            if shareholders_equity <= 0:
                raise CalculationError(
                    f"Invalid shareholders_equity for ROE: {shareholders_equity}"
                )
            
            return net_income / shareholders_equity
            
        except (TypeError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating ROE: {e}")
    
    def calculate_net_margin(self, fundamentals: Dict) -> float:
        """
        Calcula Margem Líquida.
        
        Margem Líquida = Net Income / Revenue
        
        Args:
            fundamentals: Dict contendo net_income e revenue
            
        Returns:
            Margem líquida como float
            
        Raises:
            InsufficientDataError: Se dados necessários estão faltando
            CalculationError: Se revenue é zero ou negativo
            
        Valida: Requisito 2.2
        """
        try:
            net_income = fundamentals.get('net_income')
            revenue = fundamentals.get('revenue')
            
            if net_income is None or revenue is None:
                raise InsufficientDataError(
                    "Missing net_income or revenue for net margin calculation"
                )
            
            if revenue <= 0:
                raise CalculationError(
                    f"Invalid revenue for net margin: {revenue}"
                )
            
            return net_income / revenue
            
        except (TypeError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating net margin: {e}")
    
    def calculate_revenue_growth_3y(self, fundamentals_history: List[Dict]) -> Tuple[float, float]:
        """
        Calcula crescimento de receita usando histórico adaptativo.
        
        HISTÓRICO ADAPTATIVO:
        - 3+ anos → CAGR 3Y
        - 2 anos → crescimento simples entre os dois anos
        - 1 ano → usa último valor (crescimento = 0)
        - 0 anos → retorna (None, 0.33)
        
        Args:
            fundamentals_history: Lista de dicts ordenados cronologicamente,
                                 cada um contendo revenue
            
        Returns:
            Tuple (growth_rate, confidence_factor)
            - growth_rate: Taxa de crescimento ou None
            - confidence_factor: 0.33 a 1.0 baseado em períodos disponíveis
            
        Valida: Requisito 2.3 (adaptativo)
        """
        try:
            periods = len(fundamentals_history)
            
            if periods == 0:
                return (None, 0.33)
            
            if periods == 1:
                # Apenas 1 período: não há crescimento para calcular
                return (0.0, 0.33)
            
            # Pegar primeiro e último período
            initial = fundamentals_history[0].get('revenue')
            final = fundamentals_history[-1].get('revenue')
            
            if initial is None or final is None:
                return (None, self._calculate_confidence_factor(periods))
            
            if initial <= 0:
                return (None, self._calculate_confidence_factor(periods))
            
            # Calcular número de anos entre períodos
            years = periods - 1
            
            if years == 1:
                # 2 períodos: crescimento simples
                growth = (final / initial) - 1
            else:
                # 3+ períodos: CAGR
                growth = (final / initial) ** (1 / years) - 1
            
            confidence = self._calculate_confidence_factor(periods)
            
            return (growth, confidence)
            
        except (TypeError, ValueError, ZeroDivisionError) as e:
            logger.warning(f"Error calculating revenue growth: {e}")
            return (None, 0.33)

    def calculate_roe_mean_3y(self, fundamentals_history: List[Dict]) -> Tuple[Optional[float], float]:
        """
        Calcula ROE médio usando histórico adaptativo.
        
        HISTÓRICO ADAPTATIVO:
        - 3+ anos → média de 3 anos
        - 2 anos → média de 2 anos
        - 1 ano → usa último valor
        - 0 anos → retorna (None, 0.33)
        
        Args:
            fundamentals_history: Lista de dicts ordenados cronologicamente,
                                 cada um contendo net_income e shareholders_equity
            
        Returns:
            Tuple (roe_mean, confidence_factor)
            - roe_mean: ROE médio ou None
            - confidence_factor: 0.33 a 1.0 baseado em períodos disponíveis
        """
        try:
            periods = len(fundamentals_history)
            
            if periods == 0:
                return (None, 0.33)
            
            # Calcular ROE para cada período disponível
            roes = []
            for period in fundamentals_history:
                net_income = period.get('net_income')
                shareholders_equity = period.get('shareholders_equity')
                
                if net_income is not None and shareholders_equity is not None and shareholders_equity > 0:
                    roe = net_income / shareholders_equity
                    roes.append(roe)
            
            if not roes:
                return (None, self._calculate_confidence_factor(periods))
            
            # Calcular média dos ROEs disponíveis
            import numpy as np
            roe_mean = np.mean(roes)
            confidence = self._calculate_confidence_factor(len(roes))
            
            return (roe_mean, confidence)
            
        except (TypeError, ValueError, ZeroDivisionError) as e:
            logger.warning(f"Error calculating ROE mean: {e}")
            return (None, 0.33)
    
    def calculate_roe_volatility(self, fundamentals_history: List[Dict]) -> float:
        """
        Calcula volatilidade do ROE (desvio padrão).
        
        ROE_volatility = std(ROE_year1, ROE_year2, ROE_year3)
        
        Args:
            fundamentals_history: Lista de dicts ordenados cronologicamente,
                                 cada um contendo net_income e shareholders_equity
            
        Returns:
            Desvio padrão do ROE como float
            
        Raises:
            InsufficientDataError: Se não há dados suficientes (mínimo 2 períodos)
            CalculationError: Se shareholders_equity é zero ou negativo
        """
        try:
            if len(fundamentals_history) < 2:
                raise InsufficientDataError(
                    f"Need at least 2 periods for ROE volatility, got {len(fundamentals_history)}"
                )
            
            # Calcular ROE para cada período
            roes = []
            for period in fundamentals_history:
                net_income = period.get('net_income')
                shareholders_equity = period.get('shareholders_equity')
                
                if net_income is None or shareholders_equity is None:
                    raise InsufficientDataError(
                        "Missing net_income or shareholders_equity in fundamentals history"
                    )
                
                if shareholders_equity <= 0:
                    raise CalculationError(
                        f"Invalid shareholders_equity for ROE: {shareholders_equity}"
                    )
                
                roe = net_income / shareholders_equity
                roes.append(roe)
            
            # Calcular desvio padrão
            import numpy as np
            return np.std(roes, ddof=1)  # Sample std
            
        except (TypeError, ValueError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating ROE volatility: {e}")
    
    def calculate_net_income_volatility(self, fundamentals_history: List[Dict]) -> float:
        """
        Calcula volatilidade do lucro líquido (coeficiente de variação).
        
        Volatility = std(net_income) / mean(net_income)
        
        Args:
            fundamentals_history: Lista de dicts ordenados cronologicamente,
                                 cada um contendo net_income
            
        Returns:
            Coeficiente de variação como float
            
        Raises:
            InsufficientDataError: Se não há dados suficientes (mínimo 2 períodos)
            CalculationError: Se média é zero ou todos os valores são iguais
            
        Valida: Requisito 2.4
        """
        try:
            if len(fundamentals_history) < 2:
                raise InsufficientDataError(
                    f"Need at least 2 periods for volatility calculation, got {len(fundamentals_history)}"
                )
            
            # Extrair net_income de cada período
            net_incomes = []
            for period in fundamentals_history:
                net_income = period.get('net_income')
                if net_income is None:
                    raise InsufficientDataError(
                        "Missing net_income data in fundamentals history"
                    )
                net_incomes.append(net_income)
            
            # Calcular média e desvio padrão
            import numpy as np
            mean_income = np.mean(net_incomes)
            std_income = np.std(net_incomes, ddof=1)  # Sample std
            
            # Se média é zero ou muito próxima de zero, não podemos calcular CV
            if abs(mean_income) < 1e-10:
                raise CalculationError(
                    f"Mean net income too close to zero for volatility calculation: {mean_income}"
                )
            
            # Coeficiente de variação = std / mean
            cv = std_income / abs(mean_income)
            
            return cv
            
        except (TypeError, ValueError) as e:
            raise CalculationError(f"Error calculating net income volatility: {e}")
    
    def calculate_financial_strength(
        self,
        fundamentals: Dict,
        debt_ebitda_limit: float = 4.0
    ) -> float:
        """
        Calcula força financeira baseada em alavancagem.
        
        Retorna score normalizado onde:
        - net_debt/EBITDA < 2: score = 1.0 (forte)
        - net_debt/EBITDA = 2-4: score = 0.5 (moderado)
        - net_debt/EBITDA > 4: score = 0.0 (fraco)
        
        Args:
            fundamentals: Dict contendo total_debt, cash, ebitda
            debt_ebitda_limit: Limite para penalização (default 4.0)
            
        Returns:
            Score de força financeira (0-1)
            
        Raises:
            InsufficientDataError: Se dados necessários estão faltando
            CalculationError: Se EBITDA é zero ou negativo
            
        Valida: Requisitos 2.5, 2.6
        """
        try:
            total_debt = fundamentals.get('total_debt')
            cash = fundamentals.get('cash')
            ebitda = fundamentals.get('ebitda')
            
            if total_debt is None or cash is None or ebitda is None:
                raise InsufficientDataError(
                    "Missing total_debt, cash, or ebitda for financial strength calculation"
                )
            
            if ebitda <= 0:
                raise CalculationError(
                    f"Invalid EBITDA for financial strength: {ebitda}"
                )
            
            # Calcular dívida líquida
            net_debt = total_debt - cash
            
            # Calcular razão net_debt / EBITDA
            debt_ratio = net_debt / ebitda
            
            # Retornar score normalizado
            if debt_ratio < 2.0:
                return 1.0  # Forte
            elif debt_ratio <= debt_ebitda_limit:
                return 0.5  # Moderado
            else:
                return 0.0  # Fraco
            
        except (TypeError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating financial strength: {e}")
    
    def calculate_debt_to_ebitda(self, fundamentals: Dict) -> float:
        """
        Calcula razão Dívida/EBITDA.
        
        Debt/EBITDA = Total Debt / EBITDA
        
        Args:
            fundamentals: Dict contendo total_debt e ebitda
            
        Returns:
            Razão Dívida/EBITDA como float
            
        Raises:
            InsufficientDataError: Se dados necessários estão faltando
            CalculationError: Se EBITDA é zero ou negativo
            
        Valida: Requisito 2.4
        """
        try:
            total_debt = fundamentals.get('total_debt')
            ebitda = fundamentals.get('ebitda')
            
            if total_debt is None or ebitda is None:
                raise InsufficientDataError(
                    "Missing total_debt or ebitda for debt/EBITDA calculation"
                )
            
            if ebitda <= 0:
                raise CalculationError(
                    f"Invalid EBITDA for debt/EBITDA: {ebitda}"
                )
            
            return total_debt / ebitda
            
        except (TypeError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating debt/EBITDA: {e}")
    
    def calculate_pe_ratio(self, fundamentals: Dict, price: float) -> float:
        """
        Calcula razão P/L (Price to Earnings).
        
        P/L = Price / EPS
        
        Args:
            fundamentals: Dict contendo eps
            price: Preço atual da ação
            
        Returns:
            Razão P/L como float
            
        Raises:
            InsufficientDataError: Se dados necessários estão faltando
            CalculationError: Se EPS é zero ou negativo
            
        Valida: Requisito 2.5
        """
        try:
            eps = fundamentals.get('eps')
            
            if eps is None or price is None:
                raise InsufficientDataError(
                    "Missing eps or price for P/E calculation"
                )
            
            if eps <= 0:
                raise CalculationError(
                    f"Invalid EPS for P/E: {eps}"
                )
            
            return price / eps
            
        except (TypeError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating P/E ratio: {e}")
    
    def calculate_ev_ebitda(self, fundamentals: Dict) -> float:
        """
        Calcula razão EV/EBITDA (Enterprise Value to EBITDA).
        
        EV/EBITDA = Enterprise Value / EBITDA
        
        Args:
            fundamentals: Dict contendo enterprise_value e ebitda
            
        Returns:
            Razão EV/EBITDA como float
            
        Raises:
            InsufficientDataError: Se dados necessários estão faltando
            CalculationError: Se EBITDA é zero ou negativo
            
        Valida: Requisito 2.6
        """
        try:
            enterprise_value = fundamentals.get('enterprise_value')
            ebitda = fundamentals.get('ebitda')
            
            if enterprise_value is None or ebitda is None:
                raise InsufficientDataError(
                    "Missing enterprise_value or ebitda for EV/EBITDA calculation"
                )
            
            if ebitda <= 0:
                raise CalculationError(
                    f"Invalid EBITDA for EV/EBITDA: {ebitda}"
                )
            
            return enterprise_value / ebitda
            
        except (TypeError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating EV/EBITDA: {e}")
    
    def calculate_pb_ratio(self, fundamentals: Dict, price: float) -> float:
        """
        Calcula razão P/VP (Price to Book Value).
        
        P/VP = Price / Book Value per Share
        
        Args:
            fundamentals: Dict contendo book_value_per_share
            price: Preço atual da ação
            
        Returns:
            Razão P/VP como float
            
        Raises:
            InsufficientDataError: Se dados necessários estão faltando
            CalculationError: Se book value é zero ou negativo
            
        Valida: Requisito 2.7
        """
        try:
            book_value_per_share = fundamentals.get('book_value_per_share')
            
            if book_value_per_share is None or price is None:
                raise InsufficientDataError(
                    "Missing book_value_per_share or price for P/B calculation"
                )
            
            if book_value_per_share <= 0:
                raise CalculationError(
                    f"Invalid book value for P/B: {book_value_per_share}"
                )
            
            return price / book_value_per_share
            
        except (TypeError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating P/B ratio: {e}")
    
    def calculate_price_to_book(self, fundamentals: Dict) -> float:
        """
        Calcula razão Price-to-Book usando market cap e shareholders equity.
        
        Price-to-Book = Market Cap / Shareholders Equity
        
        Args:
            fundamentals: Dict contendo market_cap e shareholders_equity
            
        Returns:
            Razão Price-to-Book como float
            
        Raises:
            InsufficientDataError: Se dados necessários estão faltando
            CalculationError: Se shareholders equity é zero ou negativo
        """
        try:
            market_cap = fundamentals.get('market_cap')
            shareholders_equity = fundamentals.get('shareholders_equity')
            
            if market_cap is None or shareholders_equity is None:
                raise InsufficientDataError(
                    "Missing market_cap or shareholders_equity for Price-to-Book calculation"
                )
            
            if shareholders_equity <= 0:
                raise CalculationError(
                    f"Invalid shareholders equity for Price-to-Book: {shareholders_equity}"
                )
            
            return market_cap / shareholders_equity
            
        except (TypeError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating Price-to-Book: {e}")
    
    def calculate_fcf_yield(self, fundamentals: Dict) -> float:
        """
        Calcula FCF Yield (Free Cash Flow Yield).
        
        FCF Yield = Free Cash Flow / Market Cap
        
        Args:
            fundamentals: Dict contendo free_cash_flow e market_cap
            
        Returns:
            FCF Yield como float (percentual)
            
        Raises:
            InsufficientDataError: Se dados necessários estão faltando
            CalculationError: Se market cap é zero ou negativo
        """
        try:
            free_cash_flow = fundamentals.get('free_cash_flow')
            market_cap = fundamentals.get('market_cap')
            
            if free_cash_flow is None or market_cap is None:
                raise InsufficientDataError(
                    "Missing free_cash_flow or market_cap for FCF Yield calculation"
                )
            
            if market_cap <= 0:
                raise CalculationError(
                    f"Invalid market cap for FCF Yield: {market_cap}"
                )
            
            return free_cash_flow / market_cap
            
        except (TypeError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating FCF Yield: {e}")
    
    def calculate_ev_ebitda_from_components(self, fundamentals: Dict) -> float:
        """
        Calcula EV/EBITDA a partir dos componentes.
        
        EV = Market Cap + Total Debt - Cash
        EV/EBITDA = EV / EBITDA
        
        Args:
            fundamentals: Dict contendo market_cap, total_debt, cash, ebitda
            
        Returns:
            Razão EV/EBITDA como float
            
        Raises:
            InsufficientDataError: Se dados necessários estão faltando
            CalculationError: Se EBITDA é zero ou negativo
        """
        try:
            market_cap = fundamentals.get('market_cap')
            total_debt = fundamentals.get('total_debt', 0)  # Default 0 se não tiver dívida
            cash = fundamentals.get('cash', 0)  # Default 0 se não tiver cash
            ebitda = fundamentals.get('ebitda')
            
            if market_cap is None or ebitda is None:
                raise InsufficientDataError(
                    "Missing market_cap or ebitda for EV/EBITDA calculation"
                )
            
            if ebitda <= 0:
                raise CalculationError(
                    f"Invalid EBITDA for EV/EBITDA: {ebitda}"
                )
            
            # Calcular Enterprise Value
            enterprise_value = market_cap + total_debt - cash
            
            return enterprise_value / ebitda
            
        except (TypeError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating EV/EBITDA from components: {e}")
    
    def calculate_size_factor(self, fundamentals: Dict) -> float:
        """
        Calcula fator SIZE (tamanho da empresa).
        
        Size Factor = -log(Market Cap)
        
        O sinal negativo é porque empresas menores tendem a ter retornos maiores
        (size premium). Assim, valores mais altos do fator indicam empresas menores.
        
        Args:
            fundamentals: Dict contendo market_cap
            
        Returns:
            Size factor como float
            
        Raises:
            InsufficientDataError: Se market_cap está faltando
            CalculationError: Se market_cap é zero ou negativo
        """
        try:
            import math
            
            market_cap = fundamentals.get('market_cap')
            
            if market_cap is None:
                raise InsufficientDataError(
                    "Missing market_cap for size factor calculation"
                )
            
            if market_cap <= 0:
                raise CalculationError(
                    f"Invalid market cap for size factor: {market_cap}"
                )
            
            # Size factor = -log(market_cap)
            # Empresas menores terão valores maiores (mais positivos)
            size_factor = -math.log(market_cap)
            
            return size_factor
            
        except (TypeError, ValueError) as e:
            raise CalculationError(f"Error calculating size factor: {e}")
    
    def calculate_all_factors(
        self,
        ticker: str,
        fundamentals_data: Dict,
        fundamentals_history: Optional[List[Dict]] = None,
        current_price: Optional[float] = None,
        winsorize_percentiles: Tuple[float, float] = (0.05, 0.95),
        max_roe_cap: float = 0.50,
        debt_ebitda_limit: float = 4.0,
        db_session: Optional[object] = None
    ) -> Dict[str, float]:
        """
        Calcula todos os fatores fundamentalistas para um ativo.
        
        Detecta automaticamente se é instituição financeira e delega para
        o calculador apropriado.
        
        Args:
            ticker: Símbolo do ativo
            fundamentals_data: Dict com dados fundamentalistas mais recentes
            fundamentals_history: Lista opcional de dados históricos para crescimento
            current_price: Preço atual opcional para cálculos de valuation
            winsorize_percentiles: Tupla de (lower, upper) percentis para winsorização
            max_roe_cap: Valor máximo permitido de ROE
            debt_ebitda_limit: Limite para penalização de dívida
            db_session: Sessão do banco de dados para buscar informações de setor
            
        Returns:
            Dict com chaves: roe, roe_mean_3y, roe_volatility, net_margin, revenue_growth_3y,
                           debt_to_ebitda, debt_to_ebitda_raw, pe_ratio, ev_ebitda, pb_ratio,
                           net_income_volatility, financial_strength, net_income_last_year,
                           net_income_history
            Fatores que não podem ser calculados terão valor None
            
        Valida: Requisitos 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7
        """
        # Detectar se é instituição financeira
        is_financial = self._is_financial_institution(ticker, fundamentals_data, db_session)
        
        if is_financial:
            logger.info(f"Detected financial institution: {ticker}, using financial calculator")
            return self._calculate_financial_factors(
                ticker=ticker,
                fundamentals_data=fundamentals_data,
                fundamentals_history=fundamentals_history,
                current_price=current_price,
                winsorize_percentiles=winsorize_percentiles
            )
        else:
            logger.info(f"Using industrial calculator for: {ticker}")
            return self._calculate_industrial_factors(
                ticker=ticker,
                fundamentals_data=fundamentals_data,
                fundamentals_history=fundamentals_history,
                current_price=current_price,
                winsorize_percentiles=winsorize_percentiles,
                max_roe_cap=max_roe_cap,
                debt_ebitda_limit=debt_ebitda_limit
            )
    
    def _is_financial_institution(
        self, 
        ticker: str, 
        fundamentals_data: Dict, 
        db_session: Optional[object] = None
    ) -> bool:
        """
        Detecta se o ativo é uma instituição financeira.
        
        Critérios:
        1. Se temos db_session, usar AssetInfoService para verificar setor
        2. Caso contrário, usar heurística: não tem EBITDA mas tem revenue e equity
        
        Args:
            ticker: Símbolo do ativo
            fundamentals_data: Dados fundamentalistas
            db_session: Sessão do banco (opcional)
            
        Returns:
            True se for instituição financeira
        """
        # Método 1: Usar AssetInfoService se temos sessão do banco
        if db_session is not None:
            try:
                from app.ingestion.asset_info_service import AssetInfoService
                asset_service = AssetInfoService(db_session)
                return asset_service.is_financial_sector(ticker)
            except Exception as e:
                logger.warning(f"Could not use AssetInfoService for {ticker}: {e}")
                # Fallback para heurística
        
        # Método 2: Heurística baseada nos dados
        ebitda = fundamentals_data.get('ebitda')
        revenue = fundamentals_data.get('revenue')
        shareholders_equity = fundamentals_data.get('shareholders_equity')
        
        # Bancos tipicamente não reportam EBITDA mas têm revenue e equity válidos
        has_valid_ebitda = ebitda is not None and ebitda > 0
        has_valid_revenue = revenue is not None and revenue > 0
        has_valid_equity = shareholders_equity is not None and shareholders_equity > 0
        
        is_likely_financial = (not has_valid_ebitda) and has_valid_revenue and has_valid_equity
        
        if is_likely_financial:
            logger.info(f"Detected likely financial institution {ticker} (no EBITDA, has revenue/equity)")
        
        return is_likely_financial
    
    def _calculate_financial_factors(
        self,
        ticker: str,
        fundamentals_data: Dict,
        fundamentals_history: Optional[List[Dict]] = None,
        current_price: Optional[float] = None,
        winsorize_percentiles: Tuple[float, float] = (0.05, 0.95)
    ) -> Dict[str, float]:
        """
        Calcula fatores específicos para instituições financeiras.
        
        Fatores para bancos:
        Qualidade:
        - ROE 3Y (cap 30%)
        - Crescimento lucro 3Y
        - Estabilidade do lucro
        - Índice de eficiência (se disponível)
        
        Valor:
        - P/L
        - P/VP
        
        Remove:
        - EV/EBITDA
        - Debt/EBITDA
        """
        from app.factor_engine.financial_factors import FinancialFactorCalculator
        
        financial_calc = FinancialFactorCalculator()
        
        # Usar calculador específico para financeiras
        financial_factors = financial_calc.calculate_all_factors(
            ticker=ticker,
            fundamentals_data=fundamentals_data,
            fundamentals_history=fundamentals_history,
            current_price=current_price,
            winsorize_percentiles=winsorize_percentiles,
            max_roe_cap=0.30  # Cap menor para bancos
        )
        
        # Mapear para estrutura esperada pelo sistema
        factors = {}
        
        # Qualidade (bancos)
        factors['roe'] = financial_factors.get('roe')  # ROE 3Y robusto
        factors['roe_mean_3y'] = financial_factors.get('roe')  # Usar mesmo ROE
        factors['roe_volatility'] = None  # Pode ser implementado depois
        factors['net_margin'] = financial_factors.get('net_margin')
        factors['revenue_growth_3y'] = financial_factors.get('book_value_growth')  # Crescimento lucro 3Y
        factors['net_income_volatility'] = None  # Estabilidade do lucro - implementar depois
        factors['financial_strength'] = None  # Não aplicável para bancos
        
        # Valor (bancos)
        factors['pe_ratio'] = financial_factors.get('pe_ratio')  # P/L
        factors['pb_ratio'] = financial_factors.get('pb_ratio')  # P/VP
        
        # Remover métricas não aplicáveis para bancos
        factors['debt_to_ebitda'] = None  # Não aplicável
        factors['debt_to_ebitda_raw'] = None  # Não aplicável
        factors['ev_ebitda'] = None  # Não aplicável
        
        # Campos de compatibilidade
        factors['net_income_last_year'] = financial_factors.get('net_income_last_year')
        factors['net_income_history'] = financial_factors.get('net_income_history', [])
        
        # Campos específicos para financeiras (para uso futuro)
        factors['roa'] = financial_factors.get('roa')  # ROA específico para bancos
        factors['efficiency_ratio'] = financial_factors.get('efficiency_ratio')  # Índice de eficiência
        
        logger.info(f"Calculated financial factors for {ticker}")
        return factors
    
    def _calculate_industrial_factors(
        self,
        ticker: str,
        fundamentals_data: Dict,
        fundamentals_history: Optional[List[Dict]] = None,
        current_price: Optional[float] = None,
        winsorize_percentiles: Tuple[float, float] = (0.05, 0.95),
        max_roe_cap: float = 0.50,
        debt_ebitda_limit: float = 4.0
    ) -> Dict[str, float]:
        """
        Calcula fatores para empresas industriais (não-financeiras).
        
        Esta é a implementação original para empresas industriais.
        """
        factors = {}
        
        # ROE Robusto (usa histórico se disponível, senão usa cálculo simples)
        if fundamentals_history and len(fundamentals_history) >= 2:
            try:
                factors['roe'] = self.calculate_roe_robust(
                    fundamentals_history,
                    winsorize_percentiles=winsorize_percentiles,
                    max_roe_cap=max_roe_cap
                )
            except (InsufficientDataError, CalculationError) as e:
                logger.warning(f"Could not calculate robust ROE for {ticker}: {e}")
                # Fallback para ROE simples
                try:
                    factors['roe'] = self.calculate_roe(fundamentals_data)
                except (InsufficientDataError, CalculationError) as e2:
                    logger.warning(f"Could not calculate simple ROE for {ticker}: {e2}")
                    factors['roe'] = None
        else:
            try:
                factors['roe'] = self.calculate_roe(fundamentals_data)
            except (InsufficientDataError, CalculationError) as e:
                logger.warning(f"Could not calculate ROE for {ticker}: {e}")
                factors['roe'] = None
        
        # ROE Mean 3Y (NOVO)
        if fundamentals_history and len(fundamentals_history) >= 2:
            try:
                factors['roe_mean_3y'] = self.calculate_roe_mean_3y(fundamentals_history)
            except (InsufficientDataError, CalculationError) as e:
                logger.warning(f"Could not calculate ROE mean 3y for {ticker}: {e}")
                factors['roe_mean_3y'] = None
        else:
            logger.warning(f"Insufficient history for ROE mean 3y for {ticker}")
            factors['roe_mean_3y'] = None
        
        # ROE Volatility (NOVO)
        if fundamentals_history and len(fundamentals_history) >= 2:
            try:
                factors['roe_volatility'] = self.calculate_roe_volatility(fundamentals_history)
            except (InsufficientDataError, CalculationError) as e:
                logger.warning(f"Could not calculate ROE volatility for {ticker}: {e}")
                factors['roe_volatility'] = None
        else:
            logger.warning(f"Insufficient history for ROE volatility for {ticker}")
            factors['roe_volatility'] = None
        
        # Net Margin
        try:
            factors['net_margin'] = self.calculate_net_margin(fundamentals_data)
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate net margin for {ticker}: {e}")
            factors['net_margin'] = None
        
        # Revenue Growth 3Y
        if fundamentals_history and len(fundamentals_history) >= 2:
            try:
                factors['revenue_growth_3y'] = self.calculate_revenue_growth_3y(
                    fundamentals_history
                )
            except (InsufficientDataError, CalculationError) as e:
                logger.warning(f"Could not calculate revenue growth for {ticker}: {e}")
                factors['revenue_growth_3y'] = None
        else:
            logger.warning(f"Insufficient history for revenue growth for {ticker}")
            factors['revenue_growth_3y'] = None
        
        # Net Income Volatility
        if fundamentals_history and len(fundamentals_history) >= 2:
            try:
                factors['net_income_volatility'] = self.calculate_net_income_volatility(
                    fundamentals_history
                )
            except (InsufficientDataError, CalculationError) as e:
                logger.warning(f"Could not calculate net income volatility for {ticker}: {e}")
                factors['net_income_volatility'] = None
        else:
            logger.warning(f"Insufficient history for net income volatility for {ticker}")
            factors['net_income_volatility'] = None
        
        # Financial Strength
        try:
            factors['financial_strength'] = self.calculate_financial_strength(
                fundamentals_data,
                debt_ebitda_limit=debt_ebitda_limit
            )
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate financial strength for {ticker}: {e}")
            factors['financial_strength'] = None
        
        # Debt to EBITDA (normalizado)
        try:
            factors['debt_to_ebitda'] = self.calculate_debt_to_ebitda(fundamentals_data)
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate debt/EBITDA for {ticker}: {e}")
            factors['debt_to_ebitda'] = None
        
        # Debt to EBITDA Raw (NOVO - não normalizado, para penalização)
        factors['debt_to_ebitda_raw'] = factors['debt_to_ebitda']
        
        # Net Income Last Year (NOVO)
        factors['net_income_last_year'] = fundamentals_data.get('net_income')
        
        # Net Income History (NOVO)
        if fundamentals_history:
            factors['net_income_history'] = [
                period.get('net_income') for period in fundamentals_history
                if period.get('net_income') is not None
            ]
        else:
            factors['net_income_history'] = []
        
        # P/E Ratio
        if current_price is not None:
            try:
                factors['pe_ratio'] = self.calculate_pe_ratio(fundamentals_data, current_price)
            except (InsufficientDataError, CalculationError) as e:
                logger.warning(f"Could not calculate P/E for {ticker}: {e}")
                factors['pe_ratio'] = None
        else:
            logger.warning(f"No price provided for P/E calculation for {ticker}")
            factors['pe_ratio'] = None
        
        # EV/EBITDA
        try:
            factors['ev_ebitda'] = self.calculate_ev_ebitda(fundamentals_data)
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate EV/EBITDA for {ticker}: {e}")
            factors['ev_ebitda'] = None
        
        # P/B Ratio
        if current_price is not None:
            try:
                factors['pb_ratio'] = self.calculate_pb_ratio(fundamentals_data, current_price)
            except (InsufficientDataError, CalculationError) as e:
                logger.warning(f"Could not calculate P/B for {ticker}: {e}")
                factors['pb_ratio'] = None
        else:
            logger.warning(f"No price provided for P/B calculation for {ticker}")
            factors['pb_ratio'] = None
        
        # Price-to-Book (usando market cap)
        try:
            factors['price_to_book'] = self.calculate_price_to_book(fundamentals_data)
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate Price-to-Book for {ticker}: {e}")
            factors['price_to_book'] = None
        
        # FCF Yield
        try:
            factors['fcf_yield'] = self.calculate_fcf_yield(fundamentals_data)
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate FCF Yield for {ticker}: {e}")
            factors['fcf_yield'] = None
        
        # EV/EBITDA (tentar calcular a partir de componentes se não tiver enterprise_value)
        if fundamentals_data.get('enterprise_value') is not None:
            try:
                factors['ev_ebitda'] = self.calculate_ev_ebitda(fundamentals_data)
            except (InsufficientDataError, CalculationError) as e:
                logger.warning(f"Could not calculate EV/EBITDA for {ticker}: {e}")
                # Tentar calcular a partir de componentes
                try:
                    factors['ev_ebitda'] = self.calculate_ev_ebitda_from_components(fundamentals_data)
                except (InsufficientDataError, CalculationError) as e2:
                    logger.warning(f"Could not calculate EV/EBITDA from components for {ticker}: {e2}")
                    factors['ev_ebitda'] = None
        else:
            # Calcular a partir de componentes
            try:
                factors['ev_ebitda'] = self.calculate_ev_ebitda_from_components(fundamentals_data)
            except (InsufficientDataError, CalculationError) as e:
                logger.warning(f"Could not calculate EV/EBITDA from components for {ticker}: {e}")
                factors['ev_ebitda'] = None
        
        # Size Factor
        try:
            factors['size_factor'] = self.calculate_size_factor(fundamentals_data)
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate size factor for {ticker}: {e}")
            factors['size_factor'] = None
        
        return factors
