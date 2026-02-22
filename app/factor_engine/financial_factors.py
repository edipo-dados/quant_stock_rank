"""
Cálculo de fatores específicos para instituições financeiras.

Bancos e seguradoras têm características diferentes de empresas industriais:
- Não usam EBITDA (conceito não aplicável)
- Foco em ROE, ROA, eficiência operacional
- Métricas específicas como P/B, spread de juros
"""

from typing import Dict, List, Optional, Tuple
from app.core.exceptions import InsufficientDataError, CalculationError
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class FinancialFactorCalculator:
    """
    Calcula fatores específicos para instituições financeiras.
    
    Foco em métricas relevantes para bancos, seguradoras e outras financeiras.
    """
    
    def __init__(self):
        """Inicializa o calculador de fatores financeiros."""
        from app.factor_engine.normalizer import CrossSectionalNormalizer
        self.normalizer = CrossSectionalNormalizer()
    
    def calculate_roe_robust(
        self,
        fundamentals_history: List[Dict],
        winsorize_percentiles: Tuple[float, float] = (0.05, 0.95),
        max_roe_cap: float = 0.30  # Cap menor para bancos (30% vs 50%)
    ) -> float:
        """
        Calcula ROE robusto para instituições financeiras.
        
        Similar ao cálculo industrial, mas com cap menor (30% vs 50%)
        pois ROEs muito altos em bancos podem indicar risco excessivo.
        
        Args:
            fundamentals_history: Lista de dicts com net_income, shareholders_equity
            winsorize_percentiles: Tupla de (lower, upper) percentis
            max_roe_cap: Valor máximo permitido de ROE (30% para bancos)
            
        Returns:
            ROE robusto como float
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
            
            # Aplicar cap específico para bancos
            capped_roe = min(avg_roe, max_roe_cap)
            
            return capped_roe
            
        except (TypeError, ValueError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating robust ROE for financial: {e}")
    
    def calculate_roa(self, fundamentals: Dict) -> float:
        """
        Calcula ROA (Return on Assets) - métrica chave para bancos.
        
        ROA = Net Income / Total Assets
        
        Args:
            fundamentals: Dict contendo net_income e total_assets
            
        Returns:
            ROA como float
        """
        try:
            net_income = fundamentals.get('net_income')
            total_assets = fundamentals.get('total_assets')
            
            if net_income is None or total_assets is None:
                raise InsufficientDataError(
                    "Missing net_income or total_assets for ROA calculation"
                )
            
            if total_assets <= 0:
                raise CalculationError(
                    f"Invalid total_assets for ROA: {total_assets}"
                )
            
            return net_income / total_assets
            
        except (TypeError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating ROA: {e}")
    
    def calculate_efficiency_ratio(self, fundamentals: Dict) -> float:
        """
        Calcula Efficiency Ratio para bancos.
        
        Efficiency Ratio = Operating Expenses / (Net Interest Income + Non-Interest Income)
        
        Como proxy, usamos: Operating Expenses / Revenue
        Menor é melhor (mais eficiente).
        
        Args:
            fundamentals: Dict contendo revenue e operating expenses
            
        Returns:
            Efficiency ratio como float
        """
        try:
            revenue = fundamentals.get('revenue')
            # Estimar operating expenses como revenue - net_income - taxes
            net_income = fundamentals.get('net_income')
            
            if revenue is None or net_income is None:
                raise InsufficientDataError(
                    "Missing revenue or net_income for efficiency ratio calculation"
                )
            
            if revenue <= 0:
                raise CalculationError(
                    f"Invalid revenue for efficiency ratio: {revenue}"
                )
            
            # Proxy: assumir que operating expenses = revenue - net_income
            # (simplificação, mas captura a eficiência operacional)
            operating_expenses = revenue - net_income
            
            if operating_expenses < 0:
                # Se net_income > revenue, algo está errado, retornar ratio alto
                return 1.0
            
            efficiency_ratio = operating_expenses / revenue
            
            return efficiency_ratio
            
        except (TypeError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating efficiency ratio: {e}")
    
    def calculate_book_value_growth(self, fundamentals_history: List[Dict]) -> float:
        """
        Calcula crescimento do valor patrimonial (book value) - importante para bancos.
        
        Book Value Growth = (Book_Value_final / Book_Value_inicial)^(1/anos) - 1
        
        Args:
            fundamentals_history: Lista de dicts ordenados cronologicamente
            
        Returns:
            CAGR do book value como float
        """
        try:
            if len(fundamentals_history) < 2:
                raise InsufficientDataError(
                    f"Need at least 2 periods for book value growth, got {len(fundamentals_history)}"
                )
            
            # Pegar primeiro e último período
            initial_equity = fundamentals_history[0].get('shareholders_equity')
            final_equity = fundamentals_history[-1].get('shareholders_equity')
            
            if initial_equity is None or final_equity is None:
                raise InsufficientDataError(
                    "Missing shareholders_equity data in fundamentals history"
                )
            
            if initial_equity <= 0:
                raise CalculationError(
                    f"Invalid initial shareholders_equity: {initial_equity}"
                )
            
            # Calcular número de anos entre períodos
            years = len(fundamentals_history) - 1
            
            if years == 0:
                raise InsufficientDataError("Need at least 2 different periods")
            
            # CAGR = (final/initial)^(1/years) - 1
            cagr = (final_equity / initial_equity) ** (1 / years) - 1
            
            return cagr
            
        except (TypeError, ValueError, ZeroDivisionError) as e:
            raise CalculationError(f"Error calculating book value growth: {e}")
    
    def calculate_net_margin(self, fundamentals: Dict) -> float:
        """
        Calcula Margem Líquida - aplicável também para bancos.
        
        Net Margin = Net Income / Revenue
        
        Args:
            fundamentals: Dict contendo net_income e revenue
            
        Returns:
            Margem líquida como float
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
    
    def calculate_pb_ratio(self, fundamentals: Dict, price: float) -> float:
        """
        Calcula razão P/VP - métrica chave para bancos.
        
        P/VP = Price / Book Value per Share
        
        Args:
            fundamentals: Dict contendo book_value_per_share
            price: Preço atual da ação
            
        Returns:
            Razão P/VP como float
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
    
    def calculate_pe_ratio(self, fundamentals: Dict, price: float) -> float:
        """
        Calcula razão P/L - aplicável para bancos.
        
        P/L = Price / EPS
        
        Args:
            fundamentals: Dict contendo eps
            price: Preço atual da ação
            
        Returns:
            Razão P/L como float
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
    
    def calculate_all_factors(
        self,
        ticker: str,
        fundamentals_data: Dict,
        fundamentals_history: Optional[List[Dict]] = None,
        current_price: Optional[float] = None,
        winsorize_percentiles: Tuple[float, float] = (0.05, 0.95),
        max_roe_cap: float = 0.30  # Cap menor para bancos
    ) -> Dict[str, float]:
        """
        Calcula todos os fatores específicos para instituições financeiras.
        
        Fatores calculados:
        - ROE robusto (cap 30%)
        - ROA (Return on Assets)
        - Margem líquida
        - Efficiency ratio
        - Crescimento do book value
        - P/VP (métrica chave para bancos)
        - P/L
        
        Args:
            ticker: Símbolo do ativo
            fundamentals_data: Dict com dados fundamentalistas mais recentes
            fundamentals_history: Lista opcional de dados históricos
            current_price: Preço atual opcional para cálculos de valuation
            winsorize_percentiles: Tupla de (lower, upper) percentis
            max_roe_cap: Valor máximo permitido de ROE (30% para bancos)
            
        Returns:
            Dict com fatores específicos para financeiras
        """
        factors = {}
        
        # ROE Robusto (com cap menor para bancos)
        if fundamentals_history and len(fundamentals_history) >= 2:
            try:
                factors['roe'] = self.calculate_roe_robust(
                    fundamentals_history,
                    winsorize_percentiles=winsorize_percentiles,
                    max_roe_cap=max_roe_cap
                )
            except (InsufficientDataError, CalculationError) as e:
                logger.warning(f"Could not calculate robust ROE for financial {ticker}: {e}")
                factors['roe'] = None
        else:
            logger.warning(f"Insufficient history for robust ROE for financial {ticker}")
            factors['roe'] = None
        
        # ROA (Return on Assets) - métrica chave para bancos
        try:
            factors['roa'] = self.calculate_roa(fundamentals_data)
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate ROA for financial {ticker}: {e}")
            factors['roa'] = None
        
        # Net Margin
        try:
            factors['net_margin'] = self.calculate_net_margin(fundamentals_data)
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate net margin for financial {ticker}: {e}")
            factors['net_margin'] = None
        
        # Efficiency Ratio (menor é melhor)
        try:
            factors['efficiency_ratio'] = self.calculate_efficiency_ratio(fundamentals_data)
        except (InsufficientDataError, CalculationError) as e:
            logger.warning(f"Could not calculate efficiency ratio for financial {ticker}: {e}")
            factors['efficiency_ratio'] = None
        
        # Book Value Growth
        if fundamentals_history and len(fundamentals_history) >= 2:
            try:
                factors['book_value_growth'] = self.calculate_book_value_growth(
                    fundamentals_history
                )
            except (InsufficientDataError, CalculationError) as e:
                logger.warning(f"Could not calculate book value growth for financial {ticker}: {e}")
                factors['book_value_growth'] = None
        else:
            logger.warning(f"Insufficient history for book value growth for financial {ticker}")
            factors['book_value_growth'] = None
        
        # P/VP Ratio (métrica chave para bancos)
        if current_price is not None:
            try:
                factors['pb_ratio'] = self.calculate_pb_ratio(fundamentals_data, current_price)
            except (InsufficientDataError, CalculationError) as e:
                logger.warning(f"Could not calculate P/B for financial {ticker}: {e}")
                factors['pb_ratio'] = None
        else:
            logger.warning(f"No price provided for P/B calculation for financial {ticker}")
            factors['pb_ratio'] = None
        
        # P/E Ratio
        if current_price is not None:
            try:
                factors['pe_ratio'] = self.calculate_pe_ratio(fundamentals_data, current_price)
            except (InsufficientDataError, CalculationError) as e:
                logger.warning(f"Could not calculate P/E for financial {ticker}: {e}")
                factors['pe_ratio'] = None
        else:
            logger.warning(f"No price provided for P/E calculation for financial {ticker}")
            factors['pe_ratio'] = None
        
        # Campos específicos para compatibilidade com sistema existente
        # (alguns fatores industriais não se aplicam a bancos)
        factors['revenue_growth_3y'] = factors.get('book_value_growth')  # Usar book value growth como proxy
        factors['debt_to_ebitda'] = None  # Não aplicável para bancos
        factors['debt_to_ebitda_raw'] = None  # Não aplicável para bancos
        factors['ev_ebitda'] = None  # Não aplicável para bancos
        
        # Campos de robustez (compatibilidade)
        factors['roe_mean_3y'] = factors.get('roe')  # Usar ROE robusto
        factors['roe_volatility'] = None  # Pode ser calculado se necessário
        factors['net_income_last_year'] = fundamentals_data.get('net_income')
        
        if fundamentals_history:
            factors['net_income_history'] = [
                period.get('net_income') for period in fundamentals_history
                if period.get('net_income') is not None
            ]
        else:
            factors['net_income_history'] = []
        
        # Campos específicos para financeiras (não normalizados ainda)
        factors['roa_raw'] = factors.get('roa')
        factors['efficiency_ratio_raw'] = factors.get('efficiency_ratio')
        
        roe_str = f"{factors.get('roe'):.3f}" if factors.get('roe') is not None else 'N/A'
        roa_str = f"{factors.get('roa'):.3f}" if factors.get('roa') is not None else 'N/A'
        pb_str = f"{factors.get('pb_ratio'):.2f}" if factors.get('pb_ratio') is not None else 'N/A'
        
        logger.info(
            f"Calculated financial factors for {ticker}: "
            f"ROE={roe_str}, ROA={roa_str}, P/B={pb_str}"
        )
        
        return factors