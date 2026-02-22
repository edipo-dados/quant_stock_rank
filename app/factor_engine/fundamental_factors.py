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
    
    def calculate_revenue_growth_3y(self, fundamentals_history: List[Dict]) -> float:
        """
        Calcula crescimento de receita de 3 anos (CAGR).
        
        CAGR = (Revenue_final / Revenue_initial)^(1/years) - 1
        
        Args:
            fundamentals_history: Lista de dicts ordenados cronologicamente,
                                 cada um contendo revenue
            
        Returns:
            CAGR de 3 anos como float
            
        Raises:
            InsufficientDataError: Se não há dados suficientes (mínimo 2 períodos)
            CalculationError: Se revenue inicial é zero ou negativo
            
        Valida: Requisito 2.3
        """
        try:
            if len(fundamentals_history) < 2:
                raise InsufficientDataError(
                    f"Need at least 2 periods for revenue growth, got {len(fundamentals_history)}"
                )
            
            # Pegar primeiro e último período
            initial = fundamentals_history[0].get('revenue')
            final = fundamentals_history[-1].get('revenue')
            
            if initial is None or final is None:
                raise InsufficientDataError(
                    "Missing revenue data in fundamentals history"
                )
            
            if initial <= 0:
                raise CalculationError(
                    f"Invalid initial revenue for growth calculation: {initial}"
                )
            
            # Calcular número de anos entre períodos
            years = len(fundamentals_history) - 1
            
            if years == 0:
                raise InsufficientDataError("Need at least 2 different periods")
            
            # CAGR = (final/initial)^(1/years) - 1
            cagr = (final / initial) ** (1 / years) - 1
            
            return cagr
            
        except (TypeError, ValueError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating revenue growth: {e}")

    def calculate_roe_mean_3y(self, fundamentals_history: List[Dict]) -> float:
        """
        Calcula ROE médio dos últimos 3 anos.
        
        ROE_mean = mean(ROE_year1, ROE_year2, ROE_year3)
        
        Args:
            fundamentals_history: Lista de dicts ordenados cronologicamente,
                                 cada um contendo net_income e shareholders_equity
            
        Returns:
            ROE médio como float
            
        Raises:
            InsufficientDataError: Se não há dados suficientes (mínimo 2 períodos)
            CalculationError: Se shareholders_equity é zero ou negativo
        """
        try:
            if len(fundamentals_history) < 2:
                raise InsufficientDataError(
                    f"Need at least 2 periods for ROE mean, got {len(fundamentals_history)}"
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
            
            # Calcular média
            import numpy as np
            return np.mean(roes)
            
        except (TypeError, ValueError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating ROE mean: {e}")
    
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
        
        return factors
