"""
Motor de scoring que combina fatores em score final.

Valida: Requisitos 4.1, 4.2, 4.3, 4.4, 4.7
"""

from typing import Dict, Optional, List
from dataclasses import dataclass, field
import logging
from app.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class ScoreResult:
    """
    Resultado completo do scoring de um ativo.
    
    Attributes:
        ticker: Símbolo do ativo
        final_score: Score final ponderado (após penalidades)
        base_score: Score base antes das penalidades de risco
        momentum_score: Score de momentum
        quality_score: Score de qualidade
        value_score: Score de valor
        confidence: Score de confiança (0-1)
        raw_factors: Dicionário com todos os fatores brutos usados no cálculo
        risk_penalties: Dicionário com breakdown das penalidades aplicadas
        passed_eligibility: Se o ativo passou pelo filtro de elegibilidade
        exclusion_reasons: Lista de razões de exclusão se não passou no filtro
    """
    ticker: str
    final_score: float
    momentum_score: float
    quality_score: float
    value_score: float
    confidence: float
    raw_factors: Dict[str, float]
    base_score: float = 0.0
    risk_penalties: Dict[str, float] = field(default_factory=dict)
    passed_eligibility: bool = True
    exclusion_reasons: List[str] = field(default_factory=list)


class ScoringEngine:
    """
    Combina fatores normalizados em score final.
    
    O scoring engine implementa uma estratégia de scoring híbrido que combina
    três categorias de fatores:
    - Momentum: Fatores técnicos de preço e volume
    - Quality: Fatores fundamentalistas de qualidade
    - Value: Fatores fundamentalistas de valuation
    
    Valida: Requisitos 4.1, 4.2, 4.3, 4.4, 4.7
    """
    
    def __init__(self, config: Optional[Settings] = None):
        """
        Inicializa o scoring engine com configuração.
        
        Args:
            config: Objeto Settings com pesos configurados.
                   Se None, usa configuração padrão.
        
        Valida: Requisitos 4.4, 4.7
        """
        if config is None:
            from app.config import settings
            config = settings
        
        self.momentum_weight = config.momentum_weight
        self.quality_weight = config.quality_weight
        self.value_weight = config.value_weight
        
        # Validar que pesos somam aproximadamente 1.0
        total_weight = self.momentum_weight + self.quality_weight + self.value_weight
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(
                f"Weights do not sum to 1.0: momentum={self.momentum_weight}, "
                f"quality={self.quality_weight}, value={self.value_weight}, "
                f"total={total_weight}"
            )
        
        logger.info(
            f"ScoringEngine initialized with weights: "
            f"momentum={self.momentum_weight}, quality={self.quality_weight}, "
            f"value={self.value_weight}"
        )
    
    def calculate_momentum_score(self, factors: Dict[str, float]) -> float:
        """
        Calcula score de momentum a partir de fatores normalizados.
        
        Score de momentum = média dos fatores de momentum normalizados.
        
        Fatores considerados:
        - return_6m: Retorno de 6 meses (positivo é melhor)
        - return_12m: Retorno de 12 meses (positivo é melhor)
        - rsi_14: RSI de 14 períodos (valores moderados são melhores)
        - volatility_90d: Volatilidade de 90 dias (INVERTIDO - menor é melhor)
        - recent_drawdown: Drawdown recente (INVERTIDO - menor é melhor)
        
        Args:
            factors: Dicionário com fatores normalizados
            
        Returns:
            Score de momentum (média dos fatores)
            
        Raises:
            ValueError: Se todos os fatores obrigatórios estão faltando
            
        Valida: Requisitos 4.1
        """
        import math
        
        required_factors = ['return_6m', 'return_12m', 'rsi_14', 'volatility_90d', 'recent_drawdown']
        
        # Coleta fatores disponíveis (não None e não NaN)
        momentum_factors = []
        for factor_name in required_factors:
            value = factors.get(factor_name)
            # Verificar se o valor é válido (não None e não NaN)
            if value is not None and not (isinstance(value, float) and math.isnan(value)):
                if factor_name in ['volatility_90d', 'recent_drawdown']:
                    momentum_factors.append(-value)  # Invertido
                else:
                    momentum_factors.append(value)
        
        # Se nenhum fator disponível, retorna 0
        if not momentum_factors:
            return 0.0
        
        # Calcular média dos fatores disponíveis
        momentum_score = sum(momentum_factors) / len(momentum_factors)
        
        return momentum_score
    
    def calculate_quality_score(self, factors: Dict[str, float]) -> float:
        """
        Calcula score de qualidade a partir de fatores normalizados.
        
        Score de qualidade = média dos fatores de qualidade normalizados.
        
        Fatores considerados:
        - roe_mean_3y: ROE médio de 3 anos (positivo é melhor)
        - roe_volatility: Volatilidade do ROE (INVERTIDO - menor é melhor)
        - net_margin: Margem líquida (positivo é melhor)
        - revenue_growth_3y: Crescimento de receita 3 anos (positivo é melhor)
        - debt_to_ebitda: Dívida/EBITDA (INVERTIDO - menor é melhor)
        
        Penalidades:
        - Se net_income_last_year < 0: quality_score *= 0.4
        - Penalização progressiva de endividamento:
          - debt_to_ebitda > 3: penalização leve (0.9)
          - debt_to_ebitda > 5: penalização forte (0.7)
        
        Args:
            factors: Dicionário com fatores normalizados
            
        Returns:
            Score de qualidade (média dos fatores com penalidades aplicadas)
            
        Raises:
            ValueError: Se todos os fatores obrigatórios estão faltando
            
        Valida: Requisitos 4.2
        """
        import math
        
        required_factors = ['roe_mean_3y', 'roe_volatility', 'net_margin', 'revenue_growth_3y', 'debt_to_ebitda']
        
        # Coleta fatores disponíveis (não None e não NaN)
        quality_factors = []
        for factor_name in required_factors:
            value = factors.get(factor_name)
            # Verificar se o valor é válido (não None e não NaN)
            if value is not None and not (isinstance(value, float) and math.isnan(value)):
                if factor_name in ['debt_to_ebitda', 'roe_volatility']:
                    quality_factors.append(-value)  # Invertido
                else:
                    quality_factors.append(value)
        
        # Se nenhum fator disponível, retorna 0
        if not quality_factors:
            return 0.0
        
        # Calcular média dos fatores disponíveis
        quality_score = sum(quality_factors) / len(quality_factors)
        
        # Aplicar penalidade por prejuízo recente
        net_income_last_year = factors.get('net_income_last_year')
        if net_income_last_year is not None and not (isinstance(net_income_last_year, float) and math.isnan(net_income_last_year)) and net_income_last_year < 0:
            quality_score *= 0.4
        
        # Aplicar penalização progressiva de endividamento
        debt_to_ebitda_raw = factors.get('debt_to_ebitda_raw')  # Valor não normalizado
        if debt_to_ebitda_raw is not None and not (isinstance(debt_to_ebitda_raw, float) and math.isnan(debt_to_ebitda_raw)):
            if debt_to_ebitda_raw > 5:
                quality_score *= 0.7  # Penalização forte
            elif debt_to_ebitda_raw > 3:
                quality_score *= 0.9  # Penalização leve
        
        return quality_score
    
    def calculate_quality_score_enhanced(
        self,
        factors: Dict[str, float],
        net_income_volatility: float,
        financial_strength: float
    ) -> float:
        """
        Calcula score de qualidade aprimorado com penalidade de volatilidade.
        
        Componentes ponderados:
        - ROE (robusto, média de 3 anos): 30%
        - Margem líquida: 25%
        - Crescimento de receita 3 anos: 20%
        - Força financeira (debt/EBITDA): 15%
        - Estabilidade (inverso da volatilidade): 10%
        
        Args:
            factors: Dicionário com fatores normalizados
            net_income_volatility: Coeficiente de variação do lucro líquido
            financial_strength: Score de força financeira (0-1)
            
        Returns:
            Score de qualidade aprimorado
            
        Valida: Requisitos 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
        """
        # Extrair fatores normalizados
        roe = factors.get('roe', 0.0) if factors.get('roe') is not None else 0.0
        net_margin = factors.get('net_margin', 0.0) if factors.get('net_margin') is not None else 0.0
        revenue_growth = factors.get('revenue_growth_3y', 0.0) if factors.get('revenue_growth_3y') is not None else 0.0
        
        # Calcular componente de estabilidade (inverso da volatilidade)
        stability = 1.0 / (1.0 + net_income_volatility)
        
        # Calcular score ponderado
        quality_score = (
            0.30 * roe +
            0.25 * net_margin +
            0.20 * revenue_growth +
            0.15 * financial_strength +
            0.10 * stability
        )
        
        return quality_score
    
    def calculate_risk_penalty(
        self,
        factors: Dict[str, float],
        volatility_limit: float,
        drawdown_limit: float
    ) -> tuple[float, Dict[str, float]]:
        """
        Calcula fator de penalidade de risco.
        
        Penalidades:
        - Se volatility_180d > volatility_limit: penalidade = 0.8
        - Se max_drawdown_3y < drawdown_limit (mais negativo): penalidade = 0.8
        - Combinadas: multiplicar penalidades
        
        Args:
            factors: Dicionário com volatility_180d, max_drawdown_3y
            volatility_limit: Limite para penalidade de volatilidade
            drawdown_limit: Limite para penalidade de drawdown (valor negativo)
            
        Returns:
            Tupla de (penalty_factor, penalty_breakdown)
            onde penalty_factor está em (0, 1] e breakdown mostra penalidades individuais
            
        Valida: Requisitos 4.1, 4.2, 4.3, 4.4, 4.5
        """
        penalty_breakdown = {}
        penalty_factor = 1.0
        
        # Verificar penalidade de volatilidade
        volatility_180d = factors.get('volatility_180d')
        if volatility_180d is not None and volatility_180d > volatility_limit:
            penalty_breakdown['volatility'] = 0.8
            penalty_factor *= 0.8
        else:
            penalty_breakdown['volatility'] = 1.0
        
        # Verificar penalidade de drawdown
        max_drawdown_3y = factors.get('max_drawdown_3y')
        if max_drawdown_3y is not None and max_drawdown_3y < drawdown_limit:
            penalty_breakdown['drawdown'] = 0.8
            penalty_factor *= 0.8
        else:
            penalty_breakdown['drawdown'] = 1.0
        
        return penalty_factor, penalty_breakdown
    
    def calculate_value_score(self, factors: Dict[str, float]) -> float:
        """
        Calcula score de valor a partir de fatores normalizados.
        
        Score de valor = média dos fatores de valor normalizados.
        
        Fatores considerados (todos invertidos - menor é melhor):
        - pe_ratio: P/L (INVERTIDO - menor é melhor)
        - ev_ebitda: EV/EBITDA (INVERTIDO - menor é melhor)
        - pb_ratio: P/VP (INVERTIDO - menor é melhor)
        
        Args:
            factors: Dicionário com fatores normalizados
            
        Returns:
            Score de valor (média dos fatores invertidos)
            
        Raises:
            ValueError: Se todos os fatores obrigatórios estão faltando
            
        Valida: Requisitos 4.3
        """
        import math
        
        required_factors = ['pe_ratio', 'ev_ebitda', 'pb_ratio']
        
        # Coleta fatores disponíveis (não None e não NaN)
        value_factors = []
        for factor_name in required_factors:
            value = factors.get(factor_name)
            # Verificar se o valor é válido (não None e não NaN)
            if value is not None and not (isinstance(value, float) and math.isnan(value)):
                value_factors.append(-value)  # Invertido
        
        # Se nenhum fator disponível, retorna 0
        if not value_factors:
            return 0.0
        
        # Calcular média dos fatores disponíveis
        value_score = sum(value_factors) / len(value_factors)
        
        return value_score
    
    def calculate_final_score(
        self, 
        momentum_score: float,
        quality_score: float,
        value_score: float
    ) -> float:
        """
        Calcula score final como média ponderada dos três scores.
        
        final_score = (momentum_weight * momentum_score +
                      quality_weight * quality_score +
                      value_weight * value_score)
        
        Args:
            momentum_score: Score de momentum
            quality_score: Score de qualidade
            value_score: Score de valor
            
        Returns:
            Score final ponderado
            
        Valida: Requisitos 4.1, 4.2, 4.3, 4.4
        """
        final_score = (
            self.momentum_weight * momentum_score +
            self.quality_weight * quality_score +
            self.value_weight * value_score
        )
        
        return final_score
    
    def score_asset(
        self, 
        ticker: str,
        fundamental_factors: Dict[str, float],
        momentum_factors: Dict[str, float],
        confidence: float = 0.5
    ) -> ScoreResult:
        """
        Calcula score completo para um ativo.
        
        Combina fatores fundamentalistas e de momentum em um score final único,
        retornando breakdown completo por categoria.
        
        Args:
            ticker: Símbolo do ativo
            fundamental_factors: Dicionário com fatores fundamentalistas normalizados
                                (roe, net_margin, revenue_growth_3y, debt_to_ebitda,
                                 pe_ratio, ev_ebitda, pb_ratio)
            momentum_factors: Dicionário com fatores de momentum normalizados
                            (return_6m, return_12m, rsi_14, volatility_90d, recent_drawdown)
            confidence: Score de confiança (0-1), default 0.5
            
        Returns:
            ScoreResult com final_score e breakdown por categoria
            
        Raises:
            ValueError: Se fatores obrigatórios estão faltando
            
        Valida: Requisitos 4.1, 4.2, 4.3, 4.4, 4.7
        """
        # Combinar todos os fatores
        all_factors = {**fundamental_factors, **momentum_factors}
        
        # Calcular scores por categoria
        momentum_score = self.calculate_momentum_score(momentum_factors)
        quality_score = self.calculate_quality_score(fundamental_factors)
        value_score = self.calculate_value_score(fundamental_factors)
        
        # Calcular score final
        final_score = self.calculate_final_score(momentum_score, quality_score, value_score)
        
        # Criar resultado
        result = ScoreResult(
            ticker=ticker,
            final_score=final_score,
            momentum_score=momentum_score,
            quality_score=quality_score,
            value_score=value_score,
            confidence=confidence,
            raw_factors=all_factors
        )
        
        logger.debug(
            f"Scored {ticker}: final={final_score:.3f}, "
            f"momentum={momentum_score:.3f}, quality={quality_score:.3f}, "
            f"value={value_score:.3f}"
        )
        
        return result
    
    def score_asset_enhanced(
        self,
        ticker: str,
        fundamental_factors: Dict[str, float],
        momentum_factors: Dict[str, float],
        net_income_volatility: float,
        financial_strength: float,
        confidence: float,
        volatility_limit: float,
        drawdown_limit: float,
        passed_eligibility: bool = True,
        exclusion_reasons: Optional[List[str]] = None
    ) -> ScoreResult:
        """
        Calcula score aprimorado com penalidades de risco e distress flag.
        
        Passos:
        1. Calcular scores base (momentum, quality aprimorado, value)
        2. Calcular base_score como média ponderada
        3. Calcular risk_penalty_factor usando calculate_risk_penalty
        4. Aplicar distress_flag se condições críticas detectadas
        5. Aplicar: final_score = base_score * risk_penalty_factor * distress_penalty
        
        Distress flag (reduz score em 50%) é ativado se:
        - Lucro líquido negativo no último ano
        - Lucro negativo em 2 dos últimos 3 anos
        - Dívida líquida / EBITDA > 5
        
        Args:
            ticker: Símbolo do ativo
            fundamental_factors: Fatores fundamentalistas normalizados
            momentum_factors: Fatores de momentum normalizados
            net_income_volatility: Coeficiente de variação do lucro líquido
            financial_strength: Score de força financeira
            confidence: Score de confiança
            volatility_limit: Limite de volatilidade
            drawdown_limit: Limite de drawdown
            passed_eligibility: Se o ativo passou no filtro de elegibilidade
            exclusion_reasons: Razões de exclusão se não passou no filtro
            
        Returns:
            ScoreResult aprimorado com breakdown de penalidades
            
        Valida: Requisitos 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.5
        """
        if exclusion_reasons is None:
            exclusion_reasons = []
        
        # Combinar todos os fatores
        all_factors = {**fundamental_factors, **momentum_factors}
        
        # Calcular scores por categoria
        momentum_score = self.calculate_momentum_score(momentum_factors)
        quality_score = self.calculate_quality_score_enhanced(
            fundamental_factors,
            net_income_volatility,
            financial_strength
        )
        value_score = self.calculate_value_score(fundamental_factors)
        
        # Calcular base_score (antes das penalidades)
        base_score = self.calculate_final_score(momentum_score, quality_score, value_score)
        
        # Calcular penalidade de risco
        risk_penalty_factor, penalty_breakdown = self.calculate_risk_penalty(
            all_factors,
            volatility_limit,
            drawdown_limit
        )
        
        # Calcular distress flag
        distress_penalty = 1.0
        net_income_last_year = fundamental_factors.get('net_income_last_year')
        net_income_history = fundamental_factors.get('net_income_history', [])
        debt_to_ebitda_raw = fundamental_factors.get('debt_to_ebitda_raw')
        
        distress_conditions = []
        
        # Condição 1: Lucro líquido negativo no último ano
        if net_income_last_year is not None and net_income_last_year < 0:
            distress_conditions.append("negative_net_income_last_year")
        
        # Condição 2: Lucro negativo em 2 dos últimos 3 anos
        if net_income_history and len(net_income_history) >= 3:
            negative_years = sum(1 for ni in net_income_history if ni is not None and ni < 0)
            if negative_years >= 2:
                distress_conditions.append("negative_net_income_2_of_3_years")
        
        # Condição 3: Dívida líquida / EBITDA > 5
        if debt_to_ebitda_raw is not None and debt_to_ebitda_raw > 5:
            distress_conditions.append("high_leverage_debt_to_ebitda_gt_5")
        
        # Aplicar distress penalty se qualquer condição for verdadeira
        if distress_conditions:
            distress_penalty = 0.5
            penalty_breakdown['distress'] = 0.5
            penalty_breakdown['distress_reasons'] = distress_conditions
        else:
            penalty_breakdown['distress'] = 1.0
        
        # Aplicar penalidades ao score final
        final_score = base_score * risk_penalty_factor * distress_penalty
        
        # Criar resultado aprimorado
        result = ScoreResult(
            ticker=ticker,
            final_score=final_score,
            base_score=base_score,
            momentum_score=momentum_score,
            quality_score=quality_score,
            value_score=value_score,
            confidence=confidence,
            raw_factors=all_factors,
            risk_penalties=penalty_breakdown,
            passed_eligibility=passed_eligibility,
            exclusion_reasons=exclusion_reasons
        )
        
        logger.debug(
            f"Scored {ticker} (enhanced): final={final_score:.3f}, "
            f"base={base_score:.3f}, risk_penalty={risk_penalty_factor:.3f}, "
            f"distress_penalty={distress_penalty:.3f}, "
            f"momentum={momentum_score:.3f}, quality={quality_score:.3f}, "
            f"value={value_score:.3f}, passed_eligibility={passed_eligibility}"
        )
        
        return result

    def calculate_quality_score_financial(self, factors: Dict[str, float]) -> float:
        """
        Calcula score de qualidade específico para instituições financeiras.

        Fatores para bancos:
        - ROE 3Y (cap 30%)
        - Crescimento lucro 3Y (usando book_value_growth como proxy)
        - Estabilidade do lucro (net_income_volatility invertido)
        - Índice de eficiência (efficiency_ratio invertido)

        Args:
            factors: Dicionário com fatores normalizados

        Returns:
            Score de qualidade para financeiras
        """
        financial_quality_factors = []

        # ROE 3Y (positivo é melhor)
        if factors.get('roe') is not None:
            financial_quality_factors.append(factors['roe'])

        # Crescimento lucro 3Y (usando revenue_growth_3y que mapeia para book_value_growth)
        if factors.get('revenue_growth_3y') is not None:
            financial_quality_factors.append(factors['revenue_growth_3y'])

        # Estabilidade do lucro (net_income_volatility invertido - menor volatilidade é melhor)
        if factors.get('net_income_volatility') is not None:
            financial_quality_factors.append(-factors['net_income_volatility'])

        # Índice de eficiência (efficiency_ratio invertido - menor é melhor)
        if factors.get('efficiency_ratio') is not None:
            financial_quality_factors.append(-factors['efficiency_ratio'])

        # Se nenhum fator disponível, retorna 0
        if not financial_quality_factors:
            return 0.0

        # Calcular média dos fatores disponíveis
        quality_score = sum(financial_quality_factors) / len(financial_quality_factors)

        # Aplicar penalidade por prejuízo recente (mesmo critério)
        net_income_last_year = factors.get('net_income_last_year')
        if net_income_last_year is not None and net_income_last_year < 0:
            quality_score *= 0.4

        return quality_score

    def calculate_value_score_financial(self, factors: Dict[str, float]) -> float:
        """
        Calcula score de valor específico para instituições financeiras.

        Fatores para bancos:
        - P/L (pe_ratio invertido - menor é melhor)
        - P/VP (pb_ratio invertido - menor é melhor)

        Remove:
        - EV/EBITDA (não aplicável para bancos)

        Args:
            factors: Dicionário com fatores normalizados

        Returns:
            Score de valor para financeiras
        """
        financial_value_factors = []

        # P/L (invertido - menor é melhor)
        if factors.get('pe_ratio') is not None:
            financial_value_factors.append(-factors['pe_ratio'])

        # P/VP (invertido - menor é melhor)
        if factors.get('pb_ratio') is not None:
            financial_value_factors.append(-factors['pb_ratio'])

        # Se nenhum fator disponível, retorna 0
        if not financial_value_factors:
            return 0.0

        # Calcular média dos fatores disponíveis
        value_score = sum(financial_value_factors) / len(financial_value_factors)

        return value_score

    def _is_financial_institution(self, factors: Dict[str, float]) -> bool:
        """
        Detecta se o ativo é uma instituição financeira baseado nos fatores.

        Critério: Se debt_to_ebitda e ev_ebitda são None (não aplicáveis para bancos)
        e temos fatores específicos de financeiras como roa ou efficiency_ratio.

        Args:
            factors: Dicionário com fatores calculados

        Returns:
            True se for instituição financeira
        """
        # Bancos não têm debt_to_ebitda nem ev_ebitda
        has_ebitda_metrics = (
            factors.get('debt_to_ebitda') is not None or
            factors.get('ev_ebitda') is not None
        )

        # Bancos têm fatores específicos como ROA ou efficiency_ratio
        has_financial_metrics = (
            factors.get('roa') is not None or
            factors.get('efficiency_ratio') is not None
        )

        return not has_ebitda_metrics and has_financial_metrics
    def calculate_quality_score_financial(self, factors: Dict[str, float]) -> float:
        """
        Calcula score de qualidade específico para instituições financeiras.
        
        Fatores para bancos:
        - ROE 3Y (cap 30%)
        - Crescimento lucro 3Y (usando book_value_growth como proxy)
        - Estabilidade do lucro (net_income_volatility invertido)
        - Índice de eficiência (efficiency_ratio invertido)
        
        Args:
            factors: Dicionário com fatores normalizados
            
        Returns:
            Score de qualidade para financeiras
        """
        financial_quality_factors = []
        
        # ROE 3Y (positivo é melhor)
        if factors.get('roe') is not None:
            financial_quality_factors.append(factors['roe'])
        
        # Crescimento lucro 3Y (usando revenue_growth_3y que mapeia para book_value_growth)
        if factors.get('revenue_growth_3y') is not None:
            financial_quality_factors.append(factors['revenue_growth_3y'])
        
        # Estabilidade do lucro (net_income_volatility invertido - menor volatilidade é melhor)
        if factors.get('net_income_volatility') is not None:
            financial_quality_factors.append(-factors['net_income_volatility'])
        
        # Índice de eficiência (efficiency_ratio invertido - menor é melhor)
        if factors.get('efficiency_ratio') is not None:
            financial_quality_factors.append(-factors['efficiency_ratio'])
        
        # Se nenhum fator disponível, retorna 0
        if not financial_quality_factors:
            return 0.0
        
        # Calcular média dos fatores disponíveis
        quality_score = sum(financial_quality_factors) / len(financial_quality_factors)
        
        # Aplicar penalidade por prejuízo recente (mesmo critério)
        net_income_last_year = factors.get('net_income_last_year')
        if net_income_last_year is not None and net_income_last_year < 0:
            quality_score *= 0.4
        
        return quality_score
    
    def calculate_value_score_financial(self, factors: Dict[str, float]) -> float:
        """
        Calcula score de valor específico para instituições financeiras.
        
        Fatores para bancos:
        - P/L (pe_ratio invertido - menor é melhor)
        - P/VP (pb_ratio invertido - menor é melhor)
        
        Remove:
        - EV/EBITDA (não aplicável para bancos)
        
        Args:
            factors: Dicionário com fatores normalizados
            
        Returns:
            Score de valor para financeiras
        """
        financial_value_factors = []
        
        # P/L (invertido - menor é melhor)
        if factors.get('pe_ratio') is not None:
            financial_value_factors.append(-factors['pe_ratio'])
        
        # P/VP (invertido - menor é melhor)
        if factors.get('pb_ratio') is not None:
            financial_value_factors.append(-factors['pb_ratio'])
        
        # Se nenhum fator disponível, retorna 0
        if not financial_value_factors:
            return 0.0
        
        # Calcular média dos fatores disponíveis
        value_score = sum(financial_value_factors) / len(financial_value_factors)
        
        return value_score
    
    def _is_financial_institution(self, factors: Dict[str, float]) -> bool:
        """
        Detecta se o ativo é uma instituição financeira baseado nos fatores.
        
        Critério: Se debt_to_ebitda e ev_ebitda são None (não aplicáveis para bancos)
        e temos fatores específicos de financeiras como roa ou efficiency_ratio.
        
        Args:
            factors: Dicionário com fatores calculados
            
        Returns:
            True se for instituição financeira
        """
        # Bancos não têm debt_to_ebitda nem ev_ebitda
        has_ebitda_metrics = (
            factors.get('debt_to_ebitda') is not None or 
            factors.get('ev_ebitda') is not None
        )
        
        # Bancos têm fatores específicos como ROA ou efficiency_ratio
        has_financial_metrics = (
            factors.get('roa') is not None or 
            factors.get('efficiency_ratio') is not None
        )
        
        return not has_ebitda_metrics and has_financial_metrics
    
    def score_asset_sector_aware(
        self,
        ticker: str,
        fundamental_factors: Dict[str, float],
        momentum_factors: Dict[str, float],
        confidence: float,
        passed_eligibility: bool = True,
        exclusion_reasons: Optional[List[str]] = None
    ) -> ScoreResult:
        """
        Calcula score com detecção automática de setor (financeiro vs industrial).
        
        Args:
            ticker: Símbolo do ativo
            fundamental_factors: Fatores fundamentalistas normalizados
            momentum_factors: Fatores de momentum normalizados
            confidence: Score de confiança
            passed_eligibility: Se o ativo passou no filtro de elegibilidade
            exclusion_reasons: Razões de exclusão se não passou no filtro
            
        Returns:
            ScoreResult com scoring específico por setor
        """
        if exclusion_reasons is None:
            exclusion_reasons = []
        
        # Combinar todos os fatores
        all_factors = {**fundamental_factors, **momentum_factors}
        
        # Detectar se é instituição financeira
        is_financial = self._is_financial_institution(fundamental_factors)
        
        # Calcular scores por categoria
        momentum_score = self.calculate_momentum_score(momentum_factors)
        
        if is_financial:
            logger.info(f"Using financial scoring for {ticker}")
            quality_score = self.calculate_quality_score_financial(fundamental_factors)
            value_score = self.calculate_value_score_financial(fundamental_factors)
        else:
            logger.info(f"Using industrial scoring for {ticker}")
            quality_score = self.calculate_quality_score(fundamental_factors)
            value_score = self.calculate_value_score(fundamental_factors)
        
        # Calcular score final
        final_score = self.calculate_final_score(momentum_score, quality_score, value_score)
        
        # Criar resultado
        result = ScoreResult(
            ticker=ticker,
            final_score=final_score,
            momentum_score=momentum_score,
            quality_score=quality_score,
            value_score=value_score,
            confidence=confidence,
            raw_factors=all_factors,
            passed_eligibility=passed_eligibility,
            exclusion_reasons=exclusion_reasons
        )
        
        logger.debug(
            f"Scored {ticker} ({'financial' if is_financial else 'industrial'}): "
            f"final={final_score:.3f}, momentum={momentum_score:.3f}, "
            f"quality={quality_score:.3f}, value={value_score:.3f}"
        )
        
        return result