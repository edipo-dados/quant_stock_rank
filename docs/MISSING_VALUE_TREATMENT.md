# Tratamento de Valores Ausentes (Missing Values)

## Visão Geral

Este documento descreve a metodologia implementada para tratamento de valores ausentes (missing values) no sistema de ranking quantitativo.

## Filosofia

**Não tratar valores ausentes como zero.** Valores ausentes indicam falta de dados, não valores ruins. Tratar como zero distorce a análise e pode levar a decisões incorretas.

## Classificação de Fatores

### Fatores Críticos

Fatores críticos são essenciais para o cálculo do score. Se ausentes, o ativo é excluído do ranking.

#### Momentum (Críticos)
- `momentum_6m_ex_1m`: Retorno de 6 meses excluindo último mês
- `momentum_12m_ex_1m`: Retorno de 12 meses excluindo último mês

#### Quality (Críticos)
- `roe_mean_3y`: ROE médio de 3 anos
- `net_margin`: Margem líquida

#### Value (Críticos)
- `pe_ratio`: Price-to-Earnings
- `price_to_book`: Price-to-Book

### Fatores Secundários

Fatores secundários complementam a análise. Se ausentes, usa-se a média setorial.

#### Momentum (Secundários)
- `volatility_90d`: Volatilidade de 90 dias
- `recent_drawdown`: Drawdown recente

#### Quality (Secundários)
- `roe_volatility`: Volatilidade do ROE
- `revenue_growth_3y`: Crescimento de receita 3 anos
- `debt_to_ebitda`: Dívida/EBITDA

#### Value (Secundários)
- `ev_ebitda`: EV/EBITDA
- `fcf_yield`: Free Cash Flow Yield
- `debt_to_ebitda`: Dívida/EBITDA (também usado em quality)

## Metodologia de Tratamento

### 1. Filtro de Elegibilidade (Eligibility Filter)

O filtro de elegibilidade verifica se o ativo possui todos os fatores críticos antes do scoring.

**Critérios de Exclusão:**
- Ausência de qualquer fator crítico de momentum, quality ou value
- Patrimônio líquido <= 0
- EBITDA <= 0 (exceto instituições financeiras)
- Receita <= 0
- Volume médio diário < mínimo configurado
- Lucro líquido negativo no último ano
- Lucro negativo em 2 dos últimos 3 anos
- Dívida líquida/EBITDA > 8

**Implementação:** `app/filters/eligibility_filter.py`

### 2. Scoring Engine

O scoring engine trata valores ausentes de forma diferenciada por categoria.

#### Tratamento de Fatores Críticos

Se fatores críticos estão ausentes, retorna score muito baixo (-999.0):

```python
# Exemplo: Momentum Score
critical_factors = ['momentum_6m_ex_1m', 'momentum_12m_ex_1m']
missing_critical = []

for factor_name in critical_factors:
    value = factors.get(factor_name)
    if value is None or math.isnan(value):
        missing_critical.append(factor_name)

if missing_critical:
    logger.warning(f"Critical momentum factors missing: {missing_critical}")
    return -999.0
```

#### Tratamento de Fatores Secundários

Se fatores secundários estão ausentes, usa apenas os disponíveis:

```python
# Exemplo: Momentum Score com fatores secundários
secondary_factors = ['volatility_90d', 'recent_drawdown']

for factor_name in secondary_factors:
    value = factors.get(factor_name)
    if value is not None and not math.isnan(value):
        momentum_factors.append(-value)  # Invertido

# Calcular média dos fatores disponíveis
momentum_score = sum(momentum_factors) / len(momentum_factors)
```

**Implementação:** `app/scoring/scoring_engine.py`

### 3. Normalização com Imputação Setorial

O normalizador oferece imputação de valores ausentes usando média setorial.

#### Método: `impute_missing_with_sector_mean()`

Para cada fator com valores ausentes:
1. Calcular média do setor para aquele fator
2. Substituir valores ausentes pela média setorial
3. Se setor não tem valores suficientes, usar média global

```python
normalizer = CrossSectionalNormalizer()

# Imputar valores ausentes com média setorial
imputed_df = normalizer.impute_missing_with_sector_mean(
    factors_df,
    factor_columns=['volatility_90d', 'recent_drawdown'],
    sector_col='sector'
)
```

#### Integração com Normalização Setorial

A normalização setorial pode incluir imputação automática:

```python
normalized_df = normalizer.normalize_factors_sector_neutral(
    factors_df,
    factor_columns=['roe', 'pe_ratio', 'volatility_90d'],
    sector_col='sector',
    impute_missing=True  # Ativa imputação setorial
)
```

**Implementação:** `app/factor_engine/normalizer.py`

## Fluxo de Tratamento

```
1. Ingestão de Dados
   ↓
2. Cálculo de Fatores
   ↓
3. Filtro de Elegibilidade
   ├─ Verifica fatores críticos
   ├─ Exclui ativos com fatores críticos ausentes
   └─ Passa apenas ativos elegíveis
   ↓
4. Imputação Setorial (Fatores Secundários)
   ├─ Identifica valores ausentes
   ├─ Calcula média setorial
   └─ Imputa valores ausentes
   ↓
5. Normalização Cross-Sectional
   ├─ Winsorização (opcional)
   ├─ Z-score setorial ou percentile ranking
   └─ Fatores normalizados [-1, +1]
   ↓
6. Scoring
   ├─ Momentum Score
   ├─ Quality Score
   ├─ Value Score
   ├─ Size Score
   └─ Final Score (ponderado)
   ↓
7. Ranking
```

## Vantagens da Abordagem

### 1. Precisão
- Valores ausentes não são confundidos com valores ruins
- Fatores críticos garantem qualidade mínima dos dados

### 2. Robustez
- Imputação setorial preserva características setoriais
- Fallback para média global quando setor é pequeno

### 3. Transparência
- Razões de exclusão são registradas
- Logs indicam quando imputação é aplicada

### 4. Flexibilidade
- Imputação pode ser ativada/desativada
- Fácil adicionar novos fatores críticos/secundários

## Configuração

### Fatores Críticos

Definidos diretamente no código do scoring engine:

```python
# app/scoring/scoring_engine.py

# Momentum
critical_momentum = ['momentum_6m_ex_1m', 'momentum_12m_ex_1m']

# Quality
critical_quality = ['roe_mean_3y', 'net_margin']

# Value
critical_value = ['pe_ratio', 'price_to_book']
```

### Imputação Setorial

Configurada na chamada do normalizador:

```python
# app/factor_engine/feature_service.py

normalized_df = normalizer.normalize_factors_sector_neutral(
    factors_df,
    factor_columns=all_factors,
    sector_col='sector',
    impute_missing=True,  # Ativar imputação
    winsorize=True,
    lower_pct=0.05,
    upper_pct=0.95
)
```

## Monitoramento

### Logs de Exclusão

```
WARNING - Critical momentum factors missing: ['momentum_6m_ex_1m']
WARNING - Critical quality factors missing: ['roe_mean_3y', 'net_margin']
```

### Logs de Imputação

```
DEBUG - Imputed 3 missing values in 'volatility_90d' for sector 'Technology' with mean 0.2543
DEBUG - Imputed 1 missing values in 'recent_drawdown' for sector 'Finance' with mean -0.1234
```

### Razões de Exclusão no Banco

```sql
SELECT ticker, exclusion_reasons
FROM scores_daily
WHERE passed_eligibility = false
AND date = '2024-02-24';
```

Exemplo de resultado:
```
ticker | exclusion_reasons
-------|------------------
ABCD3  | ["missing_critical_factor_momentum_6m_ex_1m", "missing_critical_factor_pe_ratio"]
EFGH4  | ["negative_net_income_last_year", "excessive_leverage_debt_to_ebitda_gt_8"]
```

## Referências

- Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers: Implications for stock market efficiency. Journal of Finance, 48(1), 65-91.
- Fama, F. F., & French, K. R. (1992). The cross-section of expected stock returns. Journal of Finance, 47(2), 427-465.
- Piotroski, J. D. (2000). Value investing: The use of historical financial statement information to separate winners from losers. Journal of Accounting Research, 38, 1-41.

## Histórico de Mudanças

### v2.2.0 (2024-02-24)
- Implementação inicial do tratamento de missing values
- Classificação de fatores em críticos e secundários
- Imputação setorial para fatores secundários
- Atualização do filtro de elegibilidade
- Remoção de penalidades fixas (debt_to_ebitda > 5, net_income < 0)
- Documentação completa da metodologia
