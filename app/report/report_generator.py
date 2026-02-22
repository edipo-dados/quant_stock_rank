"""
Gerador de explicações automáticas para scores de ativos.

Valida: Requisitos 7.1, 7.2, 7.3, 7.4
"""

from typing import List, Tuple, Dict
import logging

from app.scoring.scoring_engine import ScoreResult
from app.scoring.ranker import RankingEntry

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Gera explicações automáticas em linguagem natural para scores de ativos.
    
    O ReportGenerator converte dados técnicos de scoring em explicações legíveis
    em português, destacando os principais drivers positivos e negativos do score.
    
    Valida: Requisitos 7.1, 7.2, 7.3, 7.4
    """
    
    # Mapeamento de nomes técnicos para descrições legíveis
    FACTOR_DESCRIPTIONS = {
        # Fatores de Momentum
        'return_6m': 'Retorno de 6 meses',
        'return_12m': 'Retorno de 12 meses',
        'rsi_14': 'RSI (Índice de Força Relativa)',
        'volatility_90d': 'Volatilidade de 90 dias',
        'recent_drawdown': 'Drawdown recente',
        
        # Fatores de Qualidade
        'roe': 'ROE (Retorno sobre Patrimônio)',
        'net_margin': 'Margem Líquida',
        'revenue_growth_3y': 'Crescimento de Receita (3 anos)',
        'debt_to_ebitda': 'Dívida/EBITDA',
        
        # Fatores de Valor
        'pe_ratio': 'P/L (Preço/Lucro)',
        'ev_ebitda': 'EV/EBITDA',
        'pb_ratio': 'P/VP (Preço/Valor Patrimonial)'
    }
    
    # Fatores que são invertidos no cálculo (menor é melhor)
    INVERTED_FACTORS = {
        'volatility_90d',
        'recent_drawdown',
        'debt_to_ebitda',
        'pe_ratio',
        'ev_ebitda',
        'pb_ratio'
    }
    
    def generate_asset_explanation(
        self, 
        ticker: str,
        score_result: ScoreResult,
        ranking_entry: RankingEntry
    ) -> str:
        """
        Gera explicação em português para o score de um ativo.
        
        A explicação inclui:
        - Score final e posição no ranking
        - Principais fatores positivos (top 3)
        - Principais fatores negativos (bottom 3)
        - Interpretação geral baseada nos scores por categoria
        
        Args:
            ticker: Símbolo do ativo
            score_result: Resultado do scoring com breakdown
            ranking_entry: Entrada do ranking com posição
            
        Returns:
            String com explicação completa em português
            
        Exemplo:
            "PETR4 possui score de 1.85, ocupando a 3ª posição no ranking.
            
            Pontos Fortes:
            - Momentum excepcional com retorno de 12 meses de +45%
            - ROE sólido de 18%, acima da média do setor
            
            Pontos de Atenção:
            - Valuation elevado com P/L de 22x
            - Volatilidade recente acima da média
            
            Conclusão: Ativo com forte momentum e qualidade, mas valuation esticado."
            
        Valida: Requisitos 7.1, 7.2, 7.3, 7.4
        """
        # Cabeçalho com score e posição
        explanation = self._generate_header(ticker, score_result, ranking_entry)
        
        # Identificar fatores mais fortes e mais fracos
        top_factors = self._identify_top_factors(score_result.raw_factors, n=3)
        bottom_factors = self._identify_bottom_factors(score_result.raw_factors, n=3)
        
        # Seção de pontos fortes
        explanation += "\n\nPontos Fortes:\n"
        for factor_name, value in top_factors:
            description = self._format_factor_description(factor_name, value, is_positive=True)
            explanation += f"- {description}\n"
        
        # Seção de pontos de atenção
        explanation += "\nPontos de Atenção:\n"
        for factor_name, value in bottom_factors:
            description = self._format_factor_description(factor_name, value, is_positive=False)
            explanation += f"- {description}\n"
        
        # Conclusão baseada nos scores por categoria
        conclusion = self._generate_conclusion(score_result)
        explanation += f"\n{conclusion}"
        
        logger.debug(f"Generated explanation for {ticker}")
        
        return explanation
    
    def _generate_header(
        self,
        ticker: str,
        score_result: ScoreResult,
        ranking_entry: RankingEntry
    ) -> str:
        """
        Gera cabeçalho da explicação com score e posição.
        
        Args:
            ticker: Símbolo do ativo
            score_result: Resultado do scoring
            ranking_entry: Entrada do ranking
            
        Returns:
            String com cabeçalho formatado
            
        Valida: Requisitos 7.1, 7.4
        """
        # Formatar posição com ordinal (1ª, 2ª, 3ª, etc)
        rank = ranking_entry.rank
        if rank == 1:
            rank_str = "1ª"
        elif rank == 2:
            rank_str = "2ª"
        elif rank == 3:
            rank_str = "3ª"
        else:
            rank_str = f"{rank}ª"
        
        header = (
            f"{ticker} possui score de {score_result.final_score:.2f}, "
            f"ocupando a {rank_str} posição no ranking."
        )
        
        return header
    
    def _identify_top_factors(
        self, 
        factors: Dict[str, float], 
        n: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Identifica os N fatores mais fortes (positivos).
        
        Considera a inversão de fatores onde menor é melhor.
        Para fatores invertidos, valores negativos (normalizados) são positivos.
        
        Args:
            factors: Dicionário com fatores normalizados
            n: Número de fatores a retornar
            
        Returns:
            Lista de tuplas (nome_fator, valor) ordenada por força
            
        Valida: Requisitos 7.2
        """
        # Ajustar valores considerando inversão
        adjusted_factors = []
        for name, value in factors.items():
            if name in self.INVERTED_FACTORS:
                # Para fatores invertidos, inverter o sinal
                adjusted_value = -value
            else:
                adjusted_value = value
            adjusted_factors.append((name, value, adjusted_value))
        
        # Ordenar por valor ajustado (maior = melhor)
        sorted_factors = sorted(adjusted_factors, key=lambda x: x[2], reverse=True)
        
        # Retornar top N com valores originais
        top_n = [(name, original_value) for name, original_value, _ in sorted_factors[:n]]
        
        return top_n
    
    def _identify_bottom_factors(
        self, 
        factors: Dict[str, float], 
        n: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Identifica os N fatores mais fracos (negativos).
        
        Considera a inversão de fatores onde menor é melhor.
        Para fatores invertidos, valores positivos (normalizados) são negativos.
        
        Args:
            factors: Dicionário com fatores normalizados
            n: Número de fatores a retornar
            
        Returns:
            Lista de tuplas (nome_fator, valor) ordenada por fraqueza
            
        Valida: Requisitos 7.3
        """
        # Ajustar valores considerando inversão
        adjusted_factors = []
        for name, value in factors.items():
            if name in self.INVERTED_FACTORS:
                # Para fatores invertidos, inverter o sinal
                adjusted_value = -value
            else:
                adjusted_value = value
            adjusted_factors.append((name, value, adjusted_value))
        
        # Ordenar por valor ajustado (menor = pior)
        sorted_factors = sorted(adjusted_factors, key=lambda x: x[2])
        
        # Retornar bottom N com valores originais
        bottom_n = [(name, original_value) for name, original_value, _ in sorted_factors[:n]]
        
        return bottom_n
    
    def _format_factor_description(
        self, 
        factor_name: str, 
        value: float,
        is_positive: bool
    ) -> str:
        """
        Converte nome técnico de fator em descrição legível.
        
        Gera descrição contextualizada indicando se o fator é forte ou fraco.
        
        Args:
            factor_name: Nome técnico do fator
            value: Valor normalizado do fator
            is_positive: Se True, descreve como ponto forte; se False, como ponto fraco
            
        Returns:
            String com descrição legível do fator
            
        Exemplo:
            _format_factor_description('roe', 1.5, True)
            -> "ROE (Retorno sobre Patrimônio) excepcional, acima da média"
            
        Valida: Requisitos 7.2, 7.3, 7.5
        """
        # Obter descrição legível
        readable_name = self.FACTOR_DESCRIPTIONS.get(factor_name, factor_name)
        
        # Determinar intensidade baseada no valor normalizado
        abs_value = abs(value)
        if abs_value > 2.0:
            intensity = "excepcional"
        elif abs_value > 1.0:
            intensity = "forte"
        elif abs_value > 0.5:
            intensity = "moderado"
        else:
            intensity = "leve"
        
        # Construir descrição contextualizada
        if is_positive:
            # Ponto forte
            if factor_name in self.INVERTED_FACTORS:
                # Fator invertido: valor negativo é bom
                description = f"{readable_name} {intensity}, abaixo da média (positivo)"
            else:
                # Fator normal: valor positivo é bom
                description = f"{readable_name} {intensity}, acima da média"
        else:
            # Ponto fraco
            if factor_name in self.INVERTED_FACTORS:
                # Fator invertido: valor positivo é ruim
                description = f"{readable_name} {intensity}, acima da média (negativo)"
            else:
                # Fator normal: valor negativo é ruim
                description = f"{readable_name} {intensity}, abaixo da média"
        
        return description
    
    def _generate_conclusion(self, score_result: ScoreResult) -> str:
        """
        Gera conclusão baseada nos scores por categoria.
        
        Analisa os scores de momentum, qualidade e valor para gerar uma
        interpretação geral do ativo.
        
        Args:
            score_result: Resultado do scoring com breakdown
            
        Returns:
            String com conclusão interpretativa
            
        Valida: Requisitos 7.1, 7.5
        """
        # Identificar categorias fortes e fracas
        categories = {
            'momentum': score_result.momentum_score,
            'qualidade': score_result.quality_score,
            'valor': score_result.value_score
        }
        
        # Classificar categorias
        strong_categories = [name for name, score in categories.items() if score > 0.5]
        weak_categories = [name for name, score in categories.items() if score < -0.5]
        neutral_categories = [name for name, score in categories.items() 
                            if -0.5 <= score <= 0.5]
        
        # Construir conclusão
        conclusion = "Conclusão: Ativo com "
        
        if strong_categories:
            conclusion += f"{' e '.join(strong_categories)} {'forte' if len(strong_categories) == 1 else 'fortes'}"
        elif neutral_categories:
            # Se não há categorias fortes, mencionar as neutras
            conclusion += f"perfil neutro em {', '.join(neutral_categories)}"
        else:
            conclusion += "perfil neutro"
        
        if weak_categories:
            if strong_categories:
                conclusion += f", mas {' e '.join(weak_categories)} {'fraco' if len(weak_categories) == 1 else 'fracos'}"
            elif neutral_categories:
                conclusion += f", mas {' e '.join(weak_categories)} {'fraco' if len(weak_categories) == 1 else 'fracos'}"
            else:
                conclusion += f"{' e '.join(weak_categories)} {'fraco' if len(weak_categories) == 1 else 'fracos'}"
        
        conclusion += "."
        
        return conclusion
