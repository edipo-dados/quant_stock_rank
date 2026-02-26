# Implementação de Histórico Adaptativo - v2.6.0

## Objetivo

Modificar o cálculo das métricas fundamentalistas para não exigir obrigatoriamente 3 anos de histórico, usando o máximo de dados disponíveis sem gerar NaN desnecessários.

## Problema Atual

Quality e Value estão retornando NaN porque o modelo exige 3 anos completos de dados (ROE médio 3Y, crescimento 3Y etc.). Muitos ativos possuem apenas 1 ou 2 anos disponíveis via Yahoo, o que está zerando os fatores.

## Solução: Histórico Adaptativo

### 1. Regras de Histórico Adaptativo

Para qualquer métrica que use 3 anos:
- **3+ anos** → usar média/CAGR de 3 anos
- **2 anos** → usar média/crescimento de 2 anos
- **1 ano** → usar último valor
- **0 anos** → manter NaN para imputação posterior

**Não excluir o ativo por falta de histórico.**

### 2. Confidence Factor

Criar variável que reflete a qualidade do histórico:

```python
confidence_factor = anos_disponíveis / 3
```

Exemplos:
- 3 anos → 1.0
- 2 anos → 0.66
- 1 ano → 0.33

Aplicar no final do fator Quality:
```python
quality_score = quality_score * confidence_factor
```

Isso reduz peso de empresas com pouco histórico sem excluí-las.

## Implementação

### Fase 1: Modificar Métodos de Cálculo ✅

#### 1.1 Adicionar método auxiliar ✅

```python
def _calculate_confidence_factor(self, periods_available: int, periods_ideal: int = 3) -> float:
    """
    Calcula fator de confiança baseado no histórico disponível.
    
    Args:
        periods_available: Número de períodos disponíveis
        periods_ideal: Número ideal de períodos (padrão: 3)
        
    Returns:
        Fator de confiança entre 0 e 1
    """
    if periods_available >= periods_ideal:
        return 1.0
    return periods_available / periods_ideal
```

#### 1.2 Modificar calculate_revenue_growth_3y() ✅

Agora retorna `Tuple[Optional[float], float]`:
- Primeiro valor: taxa de crescimento ou None
- Segundo valor: confidence_factor

Lógica:
- 0 períodos → (None, 0.33)
- 1 período → (0.0, 0.33) - sem crescimento
- 2 períodos → (crescimento simples, 0.66)
- 3+ períodos → (CAGR, 1.0)

#### 1.3 Modificar calculate_roe_mean_3y() ✅

Agora retorna `Tuple[Optional[float], float]`:
- Primeiro valor: ROE médio ou None
- Segundo valor: confidence_factor

Lógica:
- Calcula ROE para todos os períodos disponíveis
- Retorna média dos ROEs válidos
- Confidence baseado em quantos períodos foram usados

#### 1.4 Modificar calculate_roe_volatility() ⏳

Precisa retornar `Tuple[Optional[float], float]`:
- 0 períodos → (None, 0.33)
- 1 período → (0.0, 0.33) - sem volatilidade
- 2+ períodos → (std, confidence)

#### 1.5 Modificar calculate_net_income_volatility() ⏳

Similar ao ROE volatility.

### Fase 2: Atualizar Chamadores ⏳

#### 2.1 Modificar _calculate_industrial_factors()

Atualizar para desempacotar tuplas:

```python
# Antes
factors['revenue_growth_3y'] = self.calculate_revenue_growth_3y(fundamentals_history)

# Depois
growth, confidence = self.calculate_revenue_growth_3y(fundamentals_history)
factors['revenue_growth_3y'] = growth
factors['revenue_growth_confidence'] = confidence
```

Fazer o mesmo para:
- `roe_mean_3y`
- `roe_volatility`
- `net_income_volatility`

#### 2.2 Modificar _calculate_financial_factors()

Aplicar mesmas mudanças para instituições financeiras.

### Fase 3: Adicionar Confidence ao Schema ⏳

#### 3.1 Adicionar campos ao FeatureMonthly

```python
class FeatureMonthly(Base):
    # ... campos existentes ...
    
    # Confidence factors (NOVO)
    revenue_growth_confidence = Column(Float)
    roe_mean_confidence = Column(Float)
    roe_volatility_confidence = Column(Float)
    net_income_volatility_confidence = Column(Float)
    overall_confidence = Column(Float)  # Média dos confidence factors
```

#### 3.2 Criar migração

```bash
python scripts/migrate_add_confidence_factors.py
```

### Fase 4: Aplicar Confidence no Scoring ⏳

#### 4.1 Modificar ScoringEngine.calculate_quality_score()

```python
def calculate_quality_score(self, features: Dict[str, float]) -> float:
    """
    Calcula score de qualidade com confidence factor.
    """
    # Calcular score base
    quality_components = []
    
    if features.get('roe_mean_3y') is not None:
        quality_components.append(features['roe_mean_3y'])
    
    # ... outros componentes ...
    
    if not quality_components:
        return 0.0
    
    quality_score = np.mean(quality_components)
    
    # Aplicar confidence factor
    confidence = features.get('overall_confidence', 1.0)
    quality_score = quality_score * confidence
    
    return quality_score
```

### Fase 5: Adicionar Logs ⏳

#### 5.1 No pipeline (run_pipeline_docker.py)

Após calcular features, adicionar:

```python
# Análise de histórico disponível
confidence_factors = []
for ticker in eligible_tickers:
    features = get_monthly_features(ticker)
    if features and features.get('overall_confidence'):
        confidence_factors.append(features['overall_confidence'])

if confidence_factors:
    logger.info(f"📊 Análise de Confidence Factors:")
    logger.info(f"  • Média: {np.mean(confidence_factors):.2f}")
    logger.info(f"  • Mínimo: {np.min(confidence_factors):.2f}")
    logger.info(f"  • Máximo: {np.max(confidence_factors):.2f}")
    
    # Distribuição
    high_conf = sum(1 for c in confidence_factors if c >= 0.9)
    med_conf = sum(1 for c in confidence_factors if 0.6 <= c < 0.9)
    low_conf = sum(1 for c in confidence_factors if c < 0.6)
    
    logger.info(f"  • Alta confiança (≥0.9): {high_conf} ativos")
    logger.info(f"  • Média confiança (0.6-0.9): {med_conf} ativos")
    logger.info(f"  • Baixa confiança (<0.6): {low_conf} ativos")
```

## Resultado Esperado

### Antes (v2.5.2)
```
ITUB4.SA: final=0.500, momentum=0.500, quality=nan, value=nan
BBDC4.SA: final=0.500, momentum=0.500, quality=nan, value=nan
PETR4.SA: final=-0.222, momentum=-0.222, quality=nan, value=nan
```

### Depois (v2.6.0)
```
ITUB4.SA: final=0.650, momentum=0.500, quality=0.450, value=0.320, confidence=0.66
BBDC4.SA: final=0.580, momentum=0.500, quality=0.380, value=0.290, confidence=0.66
PETR4.SA: final=-0.120, momentum=-0.222, quality=0.180, value=-0.050, confidence=0.66
```

### Garantias

- ✅ Nenhum Quality ou Value deve ficar totalmente zerado por falta de histórico
- ✅ Nenhum ativo deve ser excluído por não ter 3 anos completos
- ✅ Modelo continua estatisticamente estável
- ✅ Score final volta a refletir múltiplos fatores, não apenas momentum
- ✅ Ativos com mais histórico têm peso maior (via confidence_factor)

## Testes

### 1. Teste com 1 ano de histórico

```python
# Simular ativo com apenas 1 ano
fundamentals_history = [
    {'revenue': 1000, 'net_income': 100, 'shareholders_equity': 500}
]

growth, conf = calculator.calculate_revenue_growth_3y(fundamentals_history)
# Esperado: growth=0.0, conf=0.33

roe_mean, conf = calculator.calculate_roe_mean_3y(fundamentals_history)
# Esperado: roe_mean=0.2, conf=0.33
```

### 2. Teste com 2 anos de histórico

```python
fundamentals_history = [
    {'revenue': 1000, 'net_income': 100, 'shareholders_equity': 500},
    {'revenue': 1200, 'net_income': 120, 'shareholders_equity': 600}
]

growth, conf = calculator.calculate_revenue_growth_3y(fundamentals_history)
# Esperado: growth=0.2, conf=0.66

roe_mean, conf = calculator.calculate_roe_mean_3y(fundamentals_history)
# Esperado: roe_mean=0.2, conf=0.66
```

### 3. Teste com 3 anos de histórico

```python
fundamentals_history = [
    {'revenue': 1000, 'net_income': 100, 'shareholders_equity': 500},
    {'revenue': 1200, 'net_income': 120, 'shareholders_equity': 600},
    {'revenue': 1440, 'net_income': 144, 'shareholders_equity': 720}
]

growth, conf = calculator.calculate_revenue_growth_3y(fundamentals_history)
# Esperado: growth≈0.2 (CAGR), conf=1.0

roe_mean, conf = calculator.calculate_roe_mean_3y(fundamentals_history)
# Esperado: roe_mean=0.2, conf=1.0
```

## Cronograma

- **Fase 1**: ✅ Concluída (métodos básicos)
- **Fase 2**: ⏳ Próxima (atualizar chamadores)
- **Fase 3**: ⏳ Pendente (schema)
- **Fase 4**: ⏳ Pendente (scoring)
- **Fase 5**: ⏳ Pendente (logs)

## Comandos para Continuar

```bash
# 1. Completar modificações em fundamental_factors.py
# Atualizar calculate_roe_volatility() e calculate_net_income_volatility()

# 2. Atualizar _calculate_industrial_factors() e _calculate_financial_factors()
# Para desempacotar tuplas

# 3. Criar migração para adicionar campos de confidence
python scripts/migrate_add_confidence_factors.py

# 4. Modificar scoring_engine.py para aplicar confidence

# 5. Testar
docker exec quant-ranker-backend bash -c "cd /app && python scripts/run_pipeline_docker.py --mode test"

# 6. Verificar scores
docker exec quant-ranker-backend bash -c "cd /app && python scripts/check_today_scores.py"
```

---

**Status**: Work in Progress (WIP)
**Versão Alvo**: 2.6.0
**Data**: 26/02/2026
