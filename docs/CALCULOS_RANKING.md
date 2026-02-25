# Cálculos de Ranking - Documentação Técnica

## Visão Geral

O sistema de ranking quantitativo avalia ações brasileiras usando uma abordagem multi-fator que combina momentum, qualidade, valor e tamanho (size). O score final é calculado através da normalização cross-sectional de features e aplicação de pesos configuráveis.

**Versão**: 2.4.0  
**Última Atualização**: 2026-02-25

## Melhorias Acadêmicas Implementadas

- ✅ **Momentum Acadêmico**: Exclui último mês para evitar reversão de curto prazo
- ✅ **Expansão VALUE**: Price-to-Book, FCF Yield, EV/EBITDA calculado
- ✅ **Fator SIZE**: Size premium (-log market cap)
- ✅ **Tratamento de Missing**: Fatores críticos vs secundários, imputação setorial
- ✅ **Remoção de Penalidades Fixas**: Penalização contínua baseada em fatores normalizados

## Arquitetura de Cálculo

```
Dados Brutos (Yahoo Finance)
        ↓
Filtro de Elegibilidade (Fatores Críticos)
        ↓
Cálculo de Features
        ↓
Imputação Setorial (Fatores Secundários)
        ↓
Normalização Cross-Sectional
        ↓
Cálculo de Scores por Fator
        ↓
Score Final Ponderado (Momentum + Quality + Value + Size)
        ↓
Ranking
```

## 1. Ingestão de Dados

### 1.1 Preços Diários
- **Fonte**: Yahoo Finance (yfinance)
- **Dados**: Open, High, Low, Close, Volume, Adjusted Close
- **Período**: 400 dias (modo FULL) ou 7 dias (modo INCREMENTAL)
- **Frequência**: Diária

### 1.2 Fundamentos
- **Fonte**: Yahoo Finance (yfinance)
- **Dados**:
  - Income Statement: Revenue, Net Income, EBITDA, EPS
  - Balance Sheet: Total Assets, Total Debt, Shareholders Equity
  - Cash Flow: Operating Cash Flow, Free Cash Flow
- **Período**: Anual (últimos 4-5 anos)
- **Frequência**: Anual

## 2. Filtro de Elegibilidade

Antes do cálculo de features, os ativos passam por filtros de elegibilidade rigorosos.

### 2.1 Critérios Obrigatórios Básicos
- ✅ Possui dados de preços (mínimo 90 dias)
- ✅ Possui dados fundamentalistas
- ✅ Patrimônio líquido positivo (`shareholders_equity > 0`)
- ✅ EBITDA positivo (`ebitda > 0`, exceto instituições financeiras)
- ✅ Receita positiva (`revenue > 0`)
- ✅ Volume médio diário >= mínimo configurado

### 2.2 Critérios de Qualidade Financeira
- ✅ Lucro líquido positivo no último ano (`net_income_last_year >= 0`)
- ✅ Lucro positivo em pelo menos 2 dos últimos 3 anos
- ✅ Dívida líquida/EBITDA <= 8 (`net_debt_to_ebitda <= 8`, exceto financeiras)

### 2.3 Critérios de Fatores Críticos (NOVO v2.4.0)

**Fatores Críticos de Momentum:**
- ✅ `momentum_6m_ex_1m` presente (não None, não NaN)
- ✅ `momentum_12m_ex_1m` presente (não None, não NaN)

**Fatores Críticos de Quality:**
- ✅ `roe_mean_3y` presente (não None, não NaN)
- ✅ `net_margin` presente (não None, não NaN)

**Fatores Críticos de Value:**
- ✅ `pe_ratio` presente (não None, não NaN)
- ✅ `price_to_book` presente (não None, não NaN)

**Justificativa:** Fatores críticos são essenciais para o cálculo do score. Sua ausência indica dados insuficientes para avaliação confiável.

### 2.4 Motivos de Exclusão
- `insufficient_data`: Dados insuficientes
- `missing_shareholders_equity`: Patrimônio líquido ausente
- `negative_or_zero_equity`: Patrimônio líquido <= 0
- `missing_ebitda`: EBITDA ausente (não financeiras)
- `negative_or_zero_ebitda`: EBITDA <= 0 (não financeiras)
- `missing_revenue`: Receita ausente
- `negative_or_zero_revenue`: Receita <= 0
- `negative_net_income_last_year`: Prejuízo no último ano
- `negative_net_income_2_of_3_years`: Prejuízo em 2+ dos últimos 3 anos
- `excessive_leverage_debt_to_ebitda_gt_8`: Dívida/EBITDA > 8
- `insufficient_volume_data`: Dados de volume insuficientes
- `low_volume`: Volume médio abaixo do mínimo
- `missing_critical_factor_*`: Fator crítico ausente (momentum, quality ou value)

## 3. Cálculo de Features

### 3.1 Features de Momentum (Diárias) - METODOLOGIA ACADÊMICA

O sistema implementa a **metodologia acadêmica de momentum** que exclui o último mês dos retornos para evitar o efeito de reversão de curto prazo (short-term reversal effect). Esta abordagem é amplamente documentada na literatura de finanças quantitativas.

#### Return 1M (Retorno 1 mês)
```python
return_1m = (price_today - price_1m_ago) / price_1m_ago
```
- **Interpretação**: Retorno acumulado no último mês
- **Uso**: Apenas para cálculo de momentum ex-1m (não usado diretamente no score)

#### Return 6M (Retorno 6 meses)
```python
return_6m = (price_today - price_6m_ago) / price_6m_ago
```
- **Interpretação**: Retorno acumulado nos últimos 6 meses
- **Uso**: Apenas para cálculo de momentum ex-1m (não usado diretamente no score)

#### Return 12M (Retorno 12 meses)
```python
return_12m = (price_today - price_12m_ago) / price_12m_ago
```
- **Interpretação**: Retorno acumulado nos últimos 12 meses
- **Uso**: Apenas para cálculo de momentum ex-1m (não usado diretamente no score)

#### Momentum 6M Excluindo Último Mês (momentum_6m_ex_1m) ⭐
```python
momentum_6m_ex_1m = return_6m - return_1m
```
- **Interpretação**: Momentum de médio prazo sem ruído de curto prazo
- **Melhor**: Valores positivos e altos
- **Justificativa Acadêmica**: Evita reversão de curto prazo documentada em Jegadeesh (1990)

#### Momentum 12M Excluindo Último Mês (momentum_12m_ex_1m) ⭐
```python
momentum_12m_ex_1m = return_12m - return_1m
```
- **Interpretação**: Momentum de longo prazo sem ruído de curto prazo
- **Melhor**: Valores positivos e altos
- **Justificativa Acadêmica**: Captura tendência persistente sem efeito de reversão

#### RSI 14 (Relative Strength Index) - DESCONTINUADO
```python
# Cálculo padrão RSI
gains = [max(0, price[i] - price[i-1]) for i in range(1, 15)]
losses = [max(0, price[i-1] - price[i]) for i in range(1, 15)]
avg_gain = sum(gains) / 14
avg_loss = sum(losses) / 14
rs = avg_gain / avg_loss if avg_loss != 0 else 0
rsi_14 = 100 - (100 / (1 + rs))
```
- **Status**: Mantido para compatibilidade, mas **REMOVIDO do score final**
- **Justificativa**: Metodologia acadêmica prefere momentum puro sem indicadores técnicos

#### Volatility 90D (Volatilidade 90 dias)
```python
returns = [log(price[i] / price[i-1]) for i in range(1, 91)]
volatility_90d = std(returns) * sqrt(252)  # Anualizada
```
- **Interpretação**: Volatilidade anualizada dos retornos
- **Melhor**: Valores baixos (menor risco)

#### Recent Drawdown (Drawdown recente)
```python
peak = max(prices[-90:])
current = prices[-1]
recent_drawdown = (current - peak) / peak
```
- **Interpretação**: Queda desde o pico recente
- **Melhor**: Valores próximos de 0 (sem drawdown)

### 3.2 Features Fundamentalistas (Mensais)

#### ROE Mean 3Y (ROE Médio 3 anos) ⭐ CRÍTICO
```python
roe_mean_3y = mean([roe_y1, roe_y2, roe_y3])
```
- **Interpretação**: Consistência de rentabilidade sobre patrimônio
- **Melhor**: Valores altos e estáveis (>15%)
- **Crítico**: Ausência resulta em exclusão do ranking

#### Net Margin (Margem Líquida) ⭐ CRÍTICO
```python
net_margin = net_income / revenue
```
- **Interpretação**: Lucratividade sobre receita
- **Melhor**: Valores altos (>10%)
- **Crítico**: Ausência resulta em exclusão do ranking

#### ROE (Return on Equity)
```python
roe = net_income / shareholders_equity
```
- **Interpretação**: Retorno sobre patrimônio líquido
- **Melhor**: Valores altos (>15%)
- **Setor Financeiro**: Calculado diretamente
- **Setor Industrial**: Média dos últimos 3 anos

#### ROE Volatility (Volatilidade do ROE)
```python
roe_volatility = std([roe_y1, roe_y2, roe_y3])
```
- **Interpretação**: Estabilidade de rentabilidade
- **Melhor**: Valores baixos (ROE consistente)
- **Secundário**: Ausência imputada com média setorial

#### Revenue Growth 3Y (Crescimento de Receita 3 anos)
```python
revenue_growth_3y = (revenue_latest - revenue_3y_ago) / revenue_3y_ago / 3
```
- **Interpretação**: Taxa de crescimento anual composta
- **Melhor**: Valores positivos e altos
- **Secundário**: Ausência imputada com média setorial

#### Debt to EBITDA (Dívida sobre EBITDA)
```python
debt_to_ebitda = total_debt / ebitda
```
- **Interpretação**: Alavancagem financeira
- **Melhor**: Valores baixos (<3x)
- **Nota**: Não aplicável a instituições financeiras
- **Secundário**: Ausência imputada com média setorial

#### P/E Ratio (Preço sobre Lucro) ⭐ CRÍTICO
```python
pe_ratio = market_cap / net_income
# ou
pe_ratio = price / eps
```
- **Interpretação**: Múltiplo de lucro
- **Melhor**: Valores baixos (<20x)
- **Crítico**: Ausência resulta em exclusão do ranking

#### Price-to-Book (Preço sobre Valor Patrimonial) ⭐ CRÍTICO - NOVO v2.3.0
```python
price_to_book = market_cap / shareholders_equity
```
- **Interpretação**: Múltiplo de valor patrimonial
- **Melhor**: Valores baixos (<3x)
- **Crítico**: Ausência resulta em exclusão do ranking
- **Justificativa**: Fama-French (1992) - fator value fundamental

#### EV/EBITDA (Enterprise Value sobre EBITDA) - NOVO v2.3.0
```python
enterprise_value = market_cap + total_debt - cash
ev_ebitda = enterprise_value / ebitda
```
- **Interpretação**: Múltiplo de valuation ajustado por dívida
- **Melhor**: Valores baixos (<10x)
- **Secundário**: Ausência imputada com média setorial
- **Nota**: Não aplicável a instituições financeiras

#### FCF Yield (Free Cash Flow Yield) - NOVO v2.3.0
```python
fcf_yield = free_cash_flow / market_cap
```
- **Interpretação**: Retorno de caixa livre sobre valor de mercado
- **Melhor**: Valores altos (>5%)
- **Secundário**: Ausência imputada com média setorial
- **Justificativa**: Captura geração de caixa real

#### Size Factor (Fator de Tamanho) - NOVO v2.3.0
```python
size_factor = -log(market_cap)
```
- **Interpretação**: Size premium (empresas menores tendem a ter retornos maiores)
- **Melhor**: Valores altos (empresas menores)
- **Normalização**: Z-score setorial
- **Justificativa**: Fama-French (1992, 1993), Banz (1981)
- **Nota**: Após normalização, valores positivos = empresas menores que a média

## 4. Tratamento de Valores Ausentes (NOVO v2.4.0)

O sistema implementa tratamento sofisticado de valores ausentes baseado em metodologia acadêmica.

### 4.1 Filosofia

**Valores ausentes ≠ Valores ruins**

Valores ausentes indicam falta de dados, não necessariamente má qualidade. Tratá-los como zero distorce a análise.

### 4.2 Classificação de Fatores

#### Fatores Críticos (Ausência = Exclusão)

**Momentum:**
- `momentum_6m_ex_1m`
- `momentum_12m_ex_1m`

**Quality:**
- `roe_mean_3y`
- `net_margin`

**Value:**
- `pe_ratio`
- `price_to_book`

**Tratamento:** Se qualquer fator crítico estiver ausente, o ativo é excluído do ranking no filtro de elegibilidade.

#### Fatores Secundários (Ausência = Imputação Setorial)

**Momentum:**
- `volatility_90d`
- `recent_drawdown`

**Quality:**
- `roe_volatility`
- `revenue_growth_3y`
- `debt_to_ebitda`

**Value:**
- `ev_ebitda`
- `fcf_yield`

**Tratamento:** Valores ausentes são imputados com a média do setor. Se o setor não tiver valores suficientes, usa-se a média global.

### 4.3 Imputação Setorial

```python
# Para cada fator secundário com valores ausentes:
for sector in unique_sectors:
    sector_mean = mean(factor_values[sector])
    
    if sector_mean is not None:
        # Imputar com média setorial
        missing_values[sector] = sector_mean
    else:
        # Fallback para média global
        missing_values[sector] = global_mean
```

**Vantagens:**
- Preserva características setoriais
- Mais robusto que média global
- Transparente (logs indicam imputação)

### 4.4 Scoring com Missing Values

```python
# Exemplo: Momentum Score
critical_factors = ['momentum_6m_ex_1m', 'momentum_12m_ex_1m']
secondary_factors = ['volatility_90d', 'recent_drawdown']

# Verificar fatores críticos
missing_critical = [f for f in critical_factors if factors[f] is None]
if missing_critical:
    return -999.0  # Score muito baixo = exclusão

# Usar apenas fatores secundários disponíveis
available_factors = []
for f in critical_factors:
    available_factors.append(factors[f])

for f in secondary_factors:
    if factors[f] is not None:
        available_factors.append(-factors[f])  # Invertido

# Calcular média dos fatores disponíveis
score = sum(available_factors) / len(available_factors)
```

## 5. Normalização Cross-Sectional

## 5. Normalização Cross-Sectional

Todas as features são normalizadas usando percentile ranking cross-sectional (preferido sobre z-score por robustez a outliers):

```python
# Percentile Ranking
ranks = feature.rank(method='average')
percentile_rank = ranks / count(non_null_values)
normalized_feature = 2 * percentile_rank - 1  # Escala para [-1, +1]
```

### 5.1 Alternativa: Z-Score Setorial (Disponível, Não Ativado)

```python
# Z-Score intra-setor
for sector in unique_sectors:
    sector_mean = mean(feature[sector])
    sector_std = std(feature[sector])
    normalized_feature[sector] = (feature[sector] - sector_mean) / sector_std
```

**Status:** Implementado mas não ativado (requer dados de setor de qualidade).

### 5.2 Tratamento de Outliers (Winsorização)
- Valores extremos limitados aos percentis 5% e 95%
- Reduz impacto de outliers na normalização
- Opcional, configurável

### 5.3 Inversão de Features
Features onde "menor é melhor" são invertidas após normalização:
- `volatility_90d`: multiplicado por -1
- `recent_drawdown`: multiplicado por -1
- `debt_to_ebitda`: multiplicado por -1
- `pe_ratio`: multiplicado por -1
- `price_to_book`: multiplicado por -1
- `ev_ebitda`: multiplicado por -1
- `roe_volatility`: multiplicado por -1

## 6. Cálculo de Scores por Fator

## 6. Cálculo de Scores por Fator

### 6.1 Momentum Score (Metodologia Acadêmica v2.2.0)
```python
# Fatores críticos (obrigatórios)
critical = [
    momentum_6m_ex_1m_normalized,   # Momentum 6m excluindo último mês
    momentum_12m_ex_1m_normalized   # Momentum 12m excluindo último mês
]

# Fatores secundários (opcionais)
secondary = [
    -volatility_90d_normalized,     # Invertido - menor volatilidade é melhor
    -recent_drawdown_normalized     # Invertido - menor drawdown é melhor
]

# Verificar fatores críticos
if any(f is None for f in critical):
    momentum_score = -999.0  # Exclusão
else:
    # Usar críticos + secundários disponíveis
    available = critical + [f for f in secondary if f is not None]
    momentum_score = mean(available)
```
- **Peso padrão**: 35%
- **Interpretação**: Força de tendência e momentum sem ruído de curto prazo
- **Mudança v2.2.0**: RSI removido, momentum exclui último mês
- **Mudança v2.4.0**: Tratamento de missing values

### 6.2 Quality Score (v2.4.0)
```python
# Fatores críticos (obrigatórios)
critical = [
    roe_mean_3y_normalized,
    net_margin_normalized
]

# Fatores secundários (opcionais)
secondary = [
    roe_normalized,
    revenue_growth_3y_normalized,
    -roe_volatility_normalized,  # Invertido
    -debt_to_ebitda_normalized   # Invertido
]

# Verificar fatores críticos
if any(f is None for f in critical):
    quality_score = -999.0  # Exclusão
else:
    # Usar críticos + secundários disponíveis
    available = critical + [f for f in secondary if f is not None]
    quality_score = mean(available)
```
- **Peso padrão**: 25%
- **Interpretação**: Qualidade e consistência dos fundamentos
- **Mudança v2.4.0**: Penalidades fixas removidas, tratamento de missing

### 6.3 Value Score (v2.3.0 + v2.4.0)
```python
# Fatores críticos (obrigatórios)
critical = [
    -pe_ratio_normalized,        # Invertido - menor P/L é melhor
    -price_to_book_normalized    # Invertido - menor P/VP é melhor
]

# Fatores secundários (opcionais)
secondary = [
    -ev_ebitda_normalized,       # Invertido - menor EV/EBITDA é melhor
    fcf_yield_normalized,        # Maior FCF Yield é melhor
    -debt_to_ebitda_normalized   # Invertido - menor dívida é melhor
]

# Verificar fatores críticos
if any(f is None for f in critical):
    value_score = -999.0  # Exclusão
else:
    # Usar críticos + secundários disponíveis
    available = critical + [f for f in secondary if f is not None]
    value_score = mean(available)
```
- **Peso padrão**: 30%
- **Interpretação**: Atratividade de valuation
- **Mudança v2.3.0**: Expandido com Price-to-Book, FCF Yield, EV/EBITDA
- **Mudança v2.4.0**: Tratamento de missing values

### 6.4 Size Score (NOVO v2.3.0)
```python
size_score = size_factor_normalized
```
- **Peso padrão**: 10% (ou 0% se desabilitado)
- **Interpretação**: Size premium (empresas menores)
- **Nota**: Valores positivos = empresas menores que a média
- **Configurável**: `SIZE_WEIGHT` no .env (0.0 = desabilitado, 0.1 = 10%)

## 7. Score Final

## 7. Score Final

### 7.1 Cálculo Base (v2.3.0)
```python
final_score = (
    momentum_score * momentum_weight +
    quality_score * quality_weight +
    value_score * value_weight +
    size_score * size_weight
)
```

**Pesos Padrão (v2.3.0):**
- `MOMENTUM_WEIGHT = 0.35` (35%)
- `QUALITY_WEIGHT = 0.25` (25%)
- `VALUE_WEIGHT = 0.30` (30%)
- `SIZE_WEIGHT = 0.10` (10%)
- **Total = 1.00** (100%)

### 7.2 Penalidades de Risco (REMOVIDAS v2.4.0)

**ANTES (v2.3.0 e anteriores):**
```python
# REMOVIDO - Penalidades fixas arbitrárias
if debt_to_ebitda_raw > 5:
    quality_score *= 0.5  # Penalidade de 50%

if net_income_last_year < 0:
    quality_score *= 0.4  # Penalidade de 60%
```

**DEPOIS (v2.4.0):**
- ✅ Risco capturado diretamente em fatores normalizados
- ✅ Penalização contínua (sem thresholds arbitrários)
- ✅ Critérios extremos movidos para filtro de elegibilidade:
  - `debt_to_ebitda > 8` → exclusão
  - `net_income < 0` no último ano → exclusão
  - `net_income < 0` em 2 dos últimos 3 anos → exclusão

**Justificativa:** Penalidades fixas causavam dupla penalização (threshold + fator normalizado) e não tinham base acadêmica sólida.

### 7.3 Score Final
```python
# Versão 2.4.0 (atual)
final_score = (
    momentum_score * 0.35 +
    quality_score * 0.25 +
    value_score * 0.30 +
    size_score * 0.10
)

# Sem penalidades adicionais
# Risco já capturado nos fatores normalizados
```

## 8. Ranking

## 8. Ranking

### 8.1 Ordenação
Ativos são ordenados por `final_score` em ordem decrescente:
- Rank 1: Maior score (melhor ativo)
- Rank N: Menor score

### 8.2 Ativos Excluídos
Ativos que não passaram no filtro de elegibilidade:
- `final_score = 0` (ou não calculado)
- `passed_eligibility = False`
- `exclusion_reasons` lista os motivos
- Não aparecem no ranking (excluídos antes do scoring)

### 8.3 Scores Muito Baixos (-999.0)
Ativos com fatores críticos ausentes durante o scoring:
- `final_score` muito baixo (próximo de -999.0)
- Aparecem no final do ranking
- Indicam dados insuficientes para avaliação confiável

## 9. Configuração de Pesos

## 9. Configuração de Pesos

Os pesos dos fatores podem ser ajustados via variáveis de ambiente:

```env
# Configuração Padrão (v2.3.0+)
MOMENTUM_WEIGHT=0.35  # 35%
QUALITY_WEIGHT=0.25   # 25%
VALUE_WEIGHT=0.30     # 30%
SIZE_WEIGHT=0.10      # 10%
# Total = 1.00 (100%)
```

### 9.1 Perfis de Investimento

#### Padrão Balanceado (Recomendado)
```env
MOMENTUM_WEIGHT=0.35
QUALITY_WEIGHT=0.25
VALUE_WEIGHT=0.30
SIZE_WEIGHT=0.10
```
- Balanceado entre momentum, quality e value
- Size premium moderado (10%)

#### Agressivo (Momentum + Size)
```env
MOMENTUM_WEIGHT=0.50
QUALITY_WEIGHT=0.15
VALUE_WEIGHT=0.20
SIZE_WEIGHT=0.15
```
- Foco em momentum e empresas menores
- Maior volatilidade esperada

#### Conservador (Quality)
```env
MOMENTUM_WEIGHT=0.20
QUALITY_WEIGHT=0.50
VALUE_WEIGHT=0.30
SIZE_WEIGHT=0.00
```
- Foco em qualidade e fundamentos
- Menor volatilidade esperada
- Size desabilitado

#### Value Investing
```env
MOMENTUM_WEIGHT=0.20
QUALITY_WEIGHT=0.30
VALUE_WEIGHT=0.50
SIZE_WEIGHT=0.00
```
- Foco em valuation atrativo
- Estilo Graham & Dodd
- Size desabilitado

#### Size Premium (Small Cap)
```env
MOMENTUM_WEIGHT=0.30
QUALITY_WEIGHT=0.25
VALUE_WEIGHT=0.25
SIZE_WEIGHT=0.20
```
- Forte viés para empresas menores
- Size premium de 20%

### 9.2 Desabilitar Fator SIZE
```env
SIZE_WEIGHT=0.00
```
- Ajustar outros pesos para somar 1.0
- Exemplo: MOMENTUM=0.40, QUALITY=0.30, VALUE=0.30

## 10. Tratamento de Setores Específicos

## 10. Tratamento de Setores Específicos

### 10.1 Instituições Financeiras
- **Identificação**: Setor "Financial Services" ou ausência de EBITDA
- **Diferenças**:
  - Não calcula `debt_to_ebitda` (não aplicável)
  - Não calcula `ev_ebitda` (não aplicável)
  - ROE calculado diretamente (não média 3 anos)
  - Foco em ROE, Net Margin e Price-to-Book
  - Não penalizado por ausência de EBITDA no filtro de elegibilidade

### 10.2 Empresas Industriais
- **Identificação**: Todos os outros setores
- **Diferenças**:
  - Calcula `debt_to_ebitda`
  - Calcula `ev_ebitda`
  - ROE média 3 anos para suavizar volatilidade
  - Todos os fatores aplicáveis

## 11. Exemplos de Cálculo (Atualizado v2.4.0)

## 11. Exemplos de Cálculo (Atualizado v2.4.0)

### Exemplo 1: Ativo de Alta Qualidade (Todos os Fatores Presentes)

```
Features Normalizadas:
- momentum_6m_ex_1m: 1.2 (acima da média)
- momentum_12m_ex_1m: 1.8 (muito acima da média)
- volatility_90d: -1.0 (baixa volatilidade)
- recent_drawdown: 0.2 (pequeno drawdown)
- roe_mean_3y: 2.5 (ROE muito alto)
- net_margin: 1.8 (margem alta)
- revenue_growth_3y: 1.2 (crescimento bom)
- roe_volatility: -0.8 (ROE estável)
- debt_to_ebitda: -1.5 (baixa alavancagem)
- pe_ratio: -0.8 (valuation atrativo)
- price_to_book: -0.6 (P/VP atrativo)
- fcf_yield: 1.2 (alto FCF yield)
- size_factor: 0.5 (empresa menor que média)

Scores:
- momentum_score = (1.2 + 1.8 + 1.0 - 0.2) / 4 = 0.95
- quality_score = (2.5 + 1.8 + 1.2 + 0.8 + 1.5) / 5 = 1.56
- value_score = (0.8 + 0.6 + 1.5 + 1.2 + 1.5) / 5 = 1.12
- size_score = 0.5

Final Score = 0.95*0.35 + 1.56*0.25 + 1.12*0.30 + 0.5*0.10
            = 0.3325 + 0.39 + 0.336 + 0.05
            = 1.11
```

### Exemplo 2: Ativo com Fatores Secundários Ausentes

```
Features Normalizadas:
- momentum_6m_ex_1m: 0.8 (presente)
- momentum_12m_ex_1m: 1.0 (presente)
- volatility_90d: None (ausente - imputado com média setorial)
- recent_drawdown: None (ausente - imputado com média setorial)
- roe_mean_3y: 1.5 (presente)
- net_margin: 1.2 (presente)
- revenue_growth_3y: None (ausente - imputado)
- pe_ratio: -0.5 (presente)
- price_to_book: -0.3 (presente)

Após Imputação Setorial:
- volatility_90d: -0.5 (média do setor)
- recent_drawdown: 0.1 (média do setor)
- revenue_growth_3y: 0.8 (média do setor)

Scores:
- momentum_score = (0.8 + 1.0 + 0.5 - 0.1) / 4 = 0.55
- quality_score = (1.5 + 1.2 + 0.8) / 3 = 1.17
- value_score = (0.5 + 0.3) / 2 = 0.40
- size_score = 0.0 (não disponível)

Final Score = 0.55*0.35 + 1.17*0.25 + 0.40*0.30 + 0.0*0.10
            = 0.1925 + 0.2925 + 0.12 + 0.0
            = 0.61
```

### Exemplo 3: Ativo Excluído (Fator Crítico Ausente)

```
Features:
- momentum_6m_ex_1m: None (CRÍTICO AUSENTE)
- momentum_12m_ex_1m: 1.5
- roe_mean_3y: 2.0
- net_margin: 1.5
- pe_ratio: -0.5
- price_to_book: -0.3

Resultado:
- Excluído no filtro de elegibilidade
- Razão: missing_critical_factor_momentum_6m_ex_1m
- final_score: não calculado
- passed_eligibility: False
- Não aparece no ranking
```

### Exemplo 4: Ativo de Alto Risco (Sem Penalidades Fixas v2.4.0)

```
Features Normalizadas:
- momentum_6m_ex_1m: 2.5 (muito alto)
- momentum_12m_ex_1m: 2.0 (muito alto)
- volatility_90d: 2.5 (alta volatilidade - penalizado naturalmente)
- recent_drawdown: -1.5 (drawdown severo - penalizado naturalmente)
- roe_mean_3y: 0.5 (ROE médio)
- net_margin: 0.3 (margem média)
- debt_to_ebitda: 2.0 (alta alavancagem - penalizado naturalmente)
- pe_ratio: 1.5 (valuation caro - penalizado naturalmente)
- price_to_book: 1.2 (P/VP caro - penalizado naturalmente)

Scores:
- momentum_score = (2.5 + 2.0 - 2.5 + 1.5) / 4 = 0.88
- quality_score = (0.5 + 0.3 - 2.0) / 3 = -0.40
- value_score = (-1.5 - 1.2 - 2.0) / 3 = -1.57

Final Score = 0.88*0.35 + (-0.40)*0.25 + (-1.57)*0.30
            = 0.308 - 0.10 - 0.471
            = -0.26

Nota: Sem penalidades fixas adicionais. Risco capturado naturalmente
nos fatores normalizados (volatilidade alta, alavancagem alta, etc.)
```

## 12. Limitações e Considerações

## 12. Limitações e Considerações

### 12.1 Dados Faltantes (Atualizado v2.4.0)
- **Fatores Críticos**: Ausência resulta em exclusão do ranking
- **Fatores Secundários**: Imputados com média setorial
- **Transparência**: Razões de exclusão registradas no banco de dados
- **Logs**: Indicam quando imputação é aplicada

### 12.2 Lookback Periods
- **Momentum**: Requer mínimo 365 dias de preços
- **Fundamentos**: Requer mínimo 3 anos de dados anuais
- **Incremental**: Atualiza apenas últimos 7 dias

### 12.3 Frequência de Atualização
- **Preços**: Diária (após fechamento do mercado)
- **Fundamentos**: Trimestral/Anual (após divulgação)
- **Ranking**: Diário (segunda a sexta, 13:30)

### 12.4 Viés de Sobrevivência
- Sistema não considera empresas que faliram ou foram delistadas
- Pode superestimar retornos históricos
- Filtro de elegibilidade mitiga parcialmente

### 12.5 Limitações do Fator SIZE
- Requer `market_cap` disponível
- Alguns ativos podem não ter market cap atualizado
- SIZE_WEIGHT=0.0 desabilita o fator se necessário

## 13. Histórico de Versões

### v2.4.0 (2026-02-25)
- ✅ Tratamento de valores ausentes (críticos vs secundários)
- ✅ Imputação setorial para fatores secundários
- ✅ Remoção de penalidades fixas arbitrárias
- ✅ Penalização contínua baseada em fatores normalizados
- ✅ Filtro de elegibilidade expandido (fatores críticos)

### v2.3.0 (2026-02-25)
- ✅ Expansão do fator VALUE (Price-to-Book, FCF Yield, EV/EBITDA)
- ✅ Implementação do fator SIZE (size premium)
- ✅ Pesos atualizados: momentum=0.35, quality=0.25, value=0.30, size=0.10
- ✅ Migração de banco de dados (features_monthly)

### v2.2.0 (2026-02-25)
- ✅ Momentum acadêmico (exclui último mês)
- ✅ Novos fatores: return_1m, momentum_6m_ex_1m, momentum_12m_ex_1m
- ✅ RSI removido do score (mantido para compatibilidade)
- ✅ Migração de banco de dados (features_daily)

### v2.1.0 e anteriores
- Implementação inicial
- Momentum, Quality, Value básicos
- Normalização cross-sectional
- Filtro de elegibilidade básico

## 14. Referências

## 14. Referências

### 14.1 Metodologias Acadêmicas

#### Momentum
- **Jegadeesh, N. (1990)**. "Evidence of Predictable Behavior of Security Returns". *Journal of Finance*, 45(3), 881-898.
  - Base para momentum excluindo último mês
- **Lehmann, B. N. (1990)**. "Fads, Martingales, and Market Efficiency". *Quarterly Journal of Economics*, 105(1), 1-28.
  - Efeito de reversão de curto prazo
- **Jegadeesh, N., & Titman, S. (1993)**. "Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency". *Journal of Finance*, 48(1), 65-91.
  - Estratégia de momentum clássica

#### Value & Size
- **Fama, E. F., & French, K. R. (1992)**. "The Cross-Section of Expected Stock Returns". *Journal of Finance*, 47(2), 427-465.
  - Modelo de 3 fatores (market, size, value)
- **Fama, E. F., & French, K. R. (1993)**. "Common risk factors in the returns on stocks and bonds". *Journal of Financial Economics*, 33(1), 3-56.
  - Implementação prática dos fatores
- **Banz, R. W. (1981)**. "The relationship between return and market value of common stocks". *Journal of Financial Economics*, 9(1), 3-18.
  - Size premium original

#### Quality
- **Piotroski, J. D. (2000)**. "Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers". *Journal of Accounting Research*, 38, 1-41.
  - F-Score e qualidade fundamentalista
- **Altman, E. I. (1968)**. "Financial Ratios, Discriminant Analysis and the Prediction of Corporate Bankruptcy". *Journal of Finance*, 23(4), 589-609.
  - Z-Score e análise de risco financeiro

#### Missing Data
- **Little, R. J., & Rubin, D. B. (2019)**. "Statistical Analysis with Missing Data" (3rd ed.). Wiley.
  - Metodologia de tratamento de missing values
- **Enders, C. K. (2010)**. "Applied Missing Data Analysis". Guilford Press.
  - Imputação e análise com dados ausentes

#### Multi-Factor
- **Carhart, M. M. (1997)**. "On Persistence in Mutual Fund Performance". *Journal of Finance*, 52(1), 57-82.
  - Modelo de 4 fatores (adiciona momentum)

### 14.2 Normalização e Estatística
- **Z-Score**: Cross-sectional standardization
- **Percentile Ranking**: Robust alternative to z-score
- **Winsorization**: Outlier treatment at ±3σ or percentiles

### 14.3 Fontes de Dados
- **Yahoo Finance**: Preços diários e fundamentos
- **B3**: Lista de ativos líquidos do mercado brasileiro
- **yfinance**: Biblioteca Python para acesso aos dados

### 14.4 Documentação Adicional
- `docs/ACADEMIC_MOMENTUM_IMPLEMENTATION.md`: Detalhes do momentum acadêmico
- `docs/VALUE_SIZE_IMPLEMENTATION.md`: Detalhes de VALUE e SIZE
- `docs/MISSING_VALUE_TREATMENT.md`: Tratamento de valores ausentes
- `docs/MELHORIAS_ACADEMICAS.md`: Visão geral das melhorias
- `docs/SUMMARY_V2.2.0.md`: Resumo completo v2.2.0-2.4.0
- `CHANGELOG.md`: Histórico detalhado de mudanças

---

**Última Atualização**: 2026-02-25  
**Versão do Documento**: 2.4.0  
**Autor**: Sistema de Ranking Quantitativo
