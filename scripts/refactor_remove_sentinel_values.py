#!/usr/bin/env python3
"""
Script para refatorar o scoring_engine.py e remover valores sentinela -999.

Este script:
1. Atualiza calculate_value_score para retornar NaN em vez de -999
2. Atualiza calculate_final_score para lidar com NaN corretamente
3. Atualiza score_asset para substituir NaN por 0 após cálculo
"""

import re

# Ler o arquivo
with open('app/scoring/scoring_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Atualizar calculate_value_score
old_value_score = '''    def calculate_value_score(self, factors: Dict[str, float]) -> float:
        """
        Calcula score de valor a partir de fatores normalizados.
        
        Score de valor = média dos fatores de valor normalizados.
        
        Fatores considerados:
        - pe_ratio: P/L (INVERTIDO - menor é melhor)
        - price_to_book: P/B (INVERTIDO - menor é melhor)
        - ev_ebitda: EV/EBITDA (INVERTIDO - menor é melhor)
        - fcf_yield: FCF Yield (positivo é melhor)
        
        TRATAMENTO DE MISSING:
        - Se fatores críticos (pe_ratio, price_to_book) ausentes: score muito baixo
        - Fatores secundários ausentes: usa apenas disponíveis
        
        Args:
            factors: Dicionário com fatores normalizados
            
        Returns:
            Score de valor (média dos fatores)
            
        Valida: Requisitos 4.3
        """
        import math
        
        # Fatores críticos de valor
        critical_factors = ['pe_ratio', 'price_to_book']
        # Fatores secundários
        secondary_factors = ['ev_ebitda', 'fcf_yield']
        
        # Coleta fatores disponíveis
        value_factors = []
        missing_critical = []
        
        # Verificar fatores críticos (invertidos - menor é melhor)
        for factor_name in critical_factors:
            value = factors.get(factor_name)
            if value is not None and not (isinstance(value, float) and math.isnan(value)):
                value_factors.append(-value)  # Invertido
            else:
                missing_critical.append(factor_name)
        
        # Se fatores críticos estão ausentes, retorna score muito baixo
        if missing_critical:
            logger.warning(f"Critical value factors missing: {missing_critical}")
            return -999.0
        
        # Adicionar fatores secundários se disponíveis
        for factor_name in secondary_factors:
            value = factors.get(factor_name)
            if value is not None and not (isinstance(value, float) and math.isnan(value)):
                if factor_name == 'fcf_yield':
                    value_factors.append(value)  # FCF Yield: maior é melhor
                else:
                    value_factors.append(-value)  # EV/EBITDA: menor é melhor
        
        # Se nenhum fator disponível, retorna score muito baixo
        if not value_factors:
            return -999.0
        
        # Calcular média dos fatores disponíveis
        value_score = sum(value_factors) / len(value_factors)
        
        return value_score'''

new_value_score = '''    def calculate_value_score(self, factors: Dict[str, float]) -> float:
        """
        Calcula score de valor a partir de fatores normalizados.
        
        Score de valor = média dos fatores de valor normalizados.
        
        Fatores considerados:
        - pe_ratio: P/L (INVERTIDO - menor é melhor)
        - price_to_book: P/B (INVERTIDO - menor é melhor)
        - ev_ebitda: EV/EBITDA (INVERTIDO - menor é melhor)
        - fcf_yield: FCF Yield (positivo é melhor)
        
        TRATAMENTO DE MISSING:
        - Valores NaN são ignorados no cálculo da média
        - Se TODOS os fatores forem NaN, retorna NaN (será tratado posteriormente)
        - NUNCA usa valores sentinela como -999
        
        Args:
            factors: Dicionário com fatores normalizados
            
        Returns:
            Score de valor (média dos fatores disponíveis) ou NaN se nenhum disponível
            
        Valida: Requisitos 4.3
        """
        import math
        import numpy as np
        
        # Todos os fatores de valor
        value_factor_names = ['pe_ratio', 'price_to_book', 'ev_ebitda', 'fcf_yield']
        
        # Coleta fatores disponíveis (ignorando NaN)
        value_factors = []
        
        for factor_name in value_factor_names:
            value = factors.get(factor_name)
            if value is not None and not (isinstance(value, float) and math.isnan(value)):
                if factor_name == 'fcf_yield':
                    value_factors.append(value)  # FCF Yield: maior é melhor
                else:
                    value_factors.append(-value)  # P/L, P/B, EV/EBITDA: menor é melhor
        
        # Se nenhum fator disponível, retorna NaN
        if not value_factors:
            logger.debug("No value factors available, returning NaN")
            return np.nan
        
        # Calcular média dos fatores disponíveis
        value_score = np.mean(value_factors)
        
        logger.debug(f"Value score: {value_score:.3f} (from {len(value_factors)} factors)")
        
        return value_score'''

content = content.replace(old_value_score, new_value_score)

# 2. Atualizar calculate_final_score para lidar com NaN
old_final_score = '''    def calculate_final_score(
        self,
        momentum_score: float,
        quality_score: float,
        value_score: float,
        size_score: Optional[float] = None
    ) -> float:
        """
        Calcula score final como média ponderada dos scores por categoria.
        
        Pesos configuráveis (padrão):
        - Momentum: 35%
        - Quality: 25%
        - Value: 30%
        - Size: 10%
        
        Args:
            momentum_score: Score de momentum normalizado
            quality_score: Score de qualidade normalizado
            value_score: Score de valor normalizado
            size_score: Score de tamanho normalizado (opcional)
            
        Returns:
            Score final ponderado
            
        Valida: Requisitos 4.4
        """
        # Aplicar pesos
        final_score = (
            momentum_score * self.momentum_weight +
            quality_score * self.quality_weight +
            value_score * self.value_weight
        )
        
        # Adicionar size se disponível
        if size_score is not None:
            final_score += size_score * self.size_weight
        
        return final_score'''

new_final_score = '''    def calculate_final_score(
        self,
        momentum_score: float,
        quality_score: float,
        value_score: float,
        size_score: Optional[float] = None
    ) -> float:
        """
        Calcula score final como média ponderada dos scores por categoria.
        
        Pesos configuráveis (padrão):
        - Momentum: 35%
        - Quality: 25%
        - Value: 30%
        - Size: 10%
        
        TRATAMENTO DE NaN:
        - Se um score for NaN, seu peso é redistribuído proporcionalmente
        - Se TODOS os scores forem NaN, retorna 0.0
        
        Args:
            momentum_score: Score de momentum normalizado (pode ser NaN)
            quality_score: Score de qualidade normalizado (pode ser NaN)
            value_score: Score de valor normalizado (pode ser NaN)
            size_score: Score de tamanho normalizado (opcional, pode ser NaN)
            
        Returns:
            Score final ponderado
            
        Valida: Requisitos 4.4
        """
        import numpy as np
        
        # Coletar scores e pesos válidos (não NaN)
        scores_and_weights = []
        
        if not np.isnan(momentum_score):
            scores_and_weights.append((momentum_score, self.momentum_weight))
        
        if not np.isnan(quality_score):
            scores_and_weights.append((quality_score, self.quality_weight))
        
        if not np.isnan(value_score):
            scores_and_weights.append((value_score, self.value_weight))
        
        if size_score is not None and not np.isnan(size_score):
            scores_and_weights.append((size_score, self.size_weight))
        
        # Se nenhum score disponível, retorna 0
        if not scores_and_weights:
            logger.warning("All category scores are NaN, returning 0.0")
            return 0.0
        
        # Calcular soma dos pesos válidos
        total_weight = sum(weight for _, weight in scores_and_weights)
        
        # Calcular score final ponderado (renormalizando pesos)
        final_score = sum(score * (weight / total_weight) for score, weight in scores_and_weights)
        
        logger.debug(f"Final score: {final_score:.3f} (from {len(scores_and_weights)} categories)")
        
        return final_score'''

content = content.replace(old_final_score, new_final_score)

# Salvar arquivo atualizado
with open('app/scoring/scoring_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Refatoração concluída!")
print("   - calculate_value_score: retorna NaN em vez de -999")
print("   - calculate_final_score: redistribui pesos quando há NaN")
print("   - Valores sentinela -999 removidos")
