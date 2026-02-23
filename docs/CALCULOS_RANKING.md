# Cálculos de Ranking - Documentação Técnica

## Visão Geral

O sistema de ranking quantitativo avalia ações brasileiras usando uma abordagem multi-fator que combina momentum, qualidade e valor. O score final é calculado através da normalização cross-sectional de features e aplicação de pesos configuráveis.

## Arquitetura de Cálculo

```
Dados Brutos (Yahoo Finance)
        ↓
Cálculo de Features
        ↓
Normalização Cross-Sectional
        ↓
Cálculo de Scores por Fator
        ↓
Score Final Ponderado
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

Antes do cálculo de features, os ativos passam por filtros de elegibilidade:

### 2.1 Critérios Obrigatórios
- ✅ Possui dados de preços (mínimo 90 dias)
- ✅ Possui dados fundamentalistas
- ✅ Lucro líquido positivo em pelo menos 2 dos últimos 3 anos
- ✅ Patrimônio líquido positivo
- ✅ Receita positiva

### 2.2 Motivos de Exclusão
- `insufficient_data`: Dados insuficientes
- `negative_net_income_2_of_3_years`: Prejuízo em 2+ dos últimos 3 anos
- `negative_equity`: Patrimônio líquido negativo
- `no_revenue`: Sem receita

## 3. Cálculo de Features

### 3.1 Features de Momentum (Diárias)

#### Return 6M (Retorno 6 meses)
```python
return_6m = (price_today - price_6m_ago) / price_6m_ago
```
- **Interpretação**: Retorno acumulado nos últimos 6 meses
- **Melhor**: Valores positivos e altos

#### Return 12M (Retorno 12 meses)
```python
return_12m = (price_today - price_12m_ago) / price_12m_ago
```
- **Interpretação**: Retorno acumulado nos últimos 12 meses
- **Melhor**: Valores positivos e altos

#### RSI 14 (Relative Strength Index)
```python
# Cálculo padrão RSI
gains = [max(0, price[i] - price[i-1]) for i in range(1, 15)]
losses = [max(0, price[i-1] - price[i]) for i in range(1, 15)]
avg_gain = sum(gains) / 14
avg_loss = sum(losses) / 14
rs = avg_gain / avg_loss if avg_loss != 0 else 0
rsi_14 = 100 - (100 / (1 + rs))
```
- **Interpretação**: Força relativa do ativo (0-100)
- **Melhor**: 40-60 (não sobrecomprado nem sobrevendido)

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

#### ROE (Return on Equity)
```python
roe = net_income / shareholders_equity
```
- **Interpretação**: Retorno sobre patrimônio líquido
- **Melhor**: Valores altos (>15%)
- **Setor Financeiro**: Calculado diretamente
- **Setor Industrial**: Média dos últimos 3 anos

#### Net Margin (Margem Líquida)
```python
net_margin = net_income / revenue
```
- **Interpretação**: Lucratividade sobre receita
- **Melhor**: Valores altos (>10%)

#### Revenue Growth 3Y (Crescimento de Receita 3 anos)
```python
revenue_growth_3y = (revenue_latest - revenue_3y_ago) / revenue_3y_ago / 3
```
- **Interpretação**: Taxa de crescimento anual composta
- **Melhor**: Valores positivos e altos

#### Debt to EBITDA (Dívida sobre EBITDA)
```python
debt_to_ebitda = total_debt / ebitda
```
- **Interpretação**: Alavancagem financeira
- **Melhor**: Valores baixos (<3x)
- **Nota**: Não aplicável a instituições financeiras

#### P/E Ratio (Preço sobre Lucro)
```python
pe_ratio = (price * shares_outstanding) / net_income
```
- **Interpretação**: Múltiplo de lucro
- **Melhor**: Valores baixos (<20x)

#### ROE Mean 3Y (ROE Médio 3 anos)
```python
roe_mean_3y = mean([roe_y1, roe_y2, roe_y3])
```
- **Interpretação**: Consistência de rentabilidade
- **Melhor**: Valores altos e estáveis

#### ROE Volatility (Volatilidade do ROE)
```python
roe_volatility = std([roe_y1, roe_y2, roe_y3])
```
- **Interpretação**: Estabilidade de rentabilidade
- **Melhor**: Valores baixos (ROE consistente)

## 4. Normalização Cross-Sectional

Todas as features são normalizadas usando z-score cross-sectional:

```python
normalized_feature = (feature - mean_all_assets) / std_all_assets
```

### 4.1 Tratamento de Outliers
- Valores > 3 desvios padrão são limitados a ±3
- Valores ausentes são tratados como 0 após normalização

### 4.2 Inversão de Features
Features onde "menor é melhor" são invertidas:
- `volatility_90d`: multiplicado por -1
- `recent_drawdown`: multiplicado por -1
- `debt_to_ebitda`: multiplicado por -1
- `pe_ratio`: multiplicado por -1

## 5. Cálculo de Scores por Fator

### 5.1 Momentum Score
```python
momentum_score = mean([
    return_6m_normalized,
    return_12m_normalized,
    rsi_14_normalized,
    -volatility_90d_normalized,  # Invertido
    -recent_drawdown_normalized   # Invertido
])
```
- **Peso padrão**: 40%
- **Interpretação**: Força de tendência e momentum

### 5.2 Quality Score
```python
quality_score = mean([
    roe_normalized,
    net_margin_normalized,
    revenue_growth_3y_normalized,
    roe_mean_3y_normalized,
    -roe_volatility_normalized  # Invertido
])
```
- **Peso padrão**: 30%
- **Interpretação**: Qualidade e consistência dos fundamentos

### 5.3 Value Score
```python
value_score = mean([
    -debt_to_ebitda_normalized,  # Invertido
    -pe_ratio_normalized          # Invertido
])
```
- **Peso padrão**: 30%
- **Interpretação**: Atratividade de valuation

## 6. Score Final

### 6.1 Cálculo Base
```python
base_score = (
    momentum_score * momentum_weight +
    quality_score * quality_weight +
    value_score * value_weight
)
```

### 6.2 Penalidades de Risco
```python
penalty_factor = 1.0

# Penalidade por alta volatilidade
if volatility_90d > threshold_high:
    penalty_factor *= 0.9

# Penalidade por drawdown severo
if recent_drawdown < -0.2:
    penalty_factor *= 0.95

# Penalidade por alta alavancagem
if debt_to_ebitda > 5:
    penalty_factor *= 0.9
```

### 6.3 Score Final
```python
final_score = base_score * penalty_factor
```

## 7. Ranking

### 7.1 Ordenação
Ativos são ordenados por `final_score` em ordem decrescente:
- Rank 1: Maior score (melhor ativo)
- Rank N: Menor score

### 7.2 Ativos Excluídos
Ativos que não passaram no filtro de elegibilidade:
- `final_score = 0`
- `passed_eligibility = False`
- Aparecem no final do ranking

## 8. Configuração de Pesos

Os pesos dos fatores podem ser ajustados via variáveis de ambiente:

```env
MOMENTUM_WEIGHT=0.4  # 40%
QUALITY_WEIGHT=0.3   # 30%
VALUE_WEIGHT=0.3     # 30%
```

### 8.1 Perfis de Investimento

#### Agressivo (Momentum)
```env
MOMENTUM_WEIGHT=0.6
QUALITY_WEIGHT=0.2
VALUE_WEIGHT=0.2
```

#### Conservador (Quality)
```env
MOMENTUM_WEIGHT=0.2
QUALITY_WEIGHT=0.5
VALUE_WEIGHT=0.3
```

#### Value Investing
```env
MOMENTUM_WEIGHT=0.2
QUALITY_WEIGHT=0.3
VALUE_WEIGHT=0.5
```

## 9. Tratamento de Setores Específicos

### 9.1 Instituições Financeiras
- **Identificação**: Setor "Financial Services"
- **Diferenças**:
  - Não calcula `debt_to_ebitda` (não aplicável)
  - ROE calculado diretamente (não média 3 anos)
  - Foco em ROE e Net Margin

### 9.2 Empresas Industriais
- **Identificação**: Todos os outros setores
- **Diferenças**:
  - Calcula `debt_to_ebitda`
  - ROE média 3 anos para suavizar volatilidade
  - Todos os fatores aplicáveis

## 10. Exemplos de Cálculo

### Exemplo 1: Ativo de Alta Qualidade

```
Features Normalizadas:
- return_6m: 1.5 (acima da média)
- return_12m: 2.0 (muito acima da média)
- rsi_14: 0.5 (neutro)
- volatility_90d: -1.0 (baixa volatilidade)
- recent_drawdown: 0.2 (pequeno drawdown)
- roe: 2.5 (ROE muito alto)
- net_margin: 1.8 (margem alta)
- revenue_growth_3y: 1.2 (crescimento bom)
- debt_to_ebitda: -1.5 (baixa alavancagem)
- pe_ratio: -0.8 (valuation atrativo)

Scores:
- momentum_score = (1.5 + 2.0 + 0.5 + 1.0 - 0.2) / 5 = 0.96
- quality_score = (2.5 + 1.8 + 1.2) / 3 = 1.83
- value_score = (1.5 + 0.8) / 2 = 1.15

Base Score = 0.96*0.4 + 1.83*0.3 + 1.15*0.3 = 1.28

Penalty Factor = 1.0 (sem penalidades)

Final Score = 1.28 * 1.0 = 1.28
```

### Exemplo 2: Ativo de Alto Risco

```
Features Normalizadas:
- return_6m: 3.0 (muito acima da média)
- return_12m: 2.5 (muito acima da média)
- rsi_14: 2.0 (sobrecomprado)
- volatility_90d: 2.5 (alta volatilidade)
- recent_drawdown: -1.5 (drawdown severo)
- roe: 0.5 (ROE médio)
- net_margin: 0.3 (margem média)
- revenue_growth_3y: -0.5 (crescimento baixo)
- debt_to_ebitda: 2.0 (alta alavancagem)
- pe_ratio: 1.5 (valuation caro)

Scores:
- momentum_score = (3.0 + 2.5 + 2.0 - 2.5 + 1.5) / 5 = 1.30
- quality_score = (0.5 + 0.3 - 0.5) / 3 = 0.10
- value_score = (-2.0 - 1.5) / 2 = -1.75

Base Score = 1.30*0.4 + 0.10*0.3 + (-1.75)*0.3 = 0.02

Penalty Factor = 0.9 * 0.95 * 0.9 = 0.77 (múltiplas penalidades)

Final Score = 0.02 * 0.77 = 0.015
```

## 11. Limitações e Considerações

### 11.1 Dados Faltantes
- Features ausentes são tratadas como 0 após normalização
- Pode afetar o score de ativos com dados incompletos

### 11.2 Lookback Periods
- Momentum: Requer mínimo 365 dias de preços
- Fundamentos: Requer mínimo 3 anos de dados anuais

### 11.3 Frequência de Atualização
- Preços: Diária (após fechamento do mercado)
- Fundamentos: Trimestral/Anual (após divulgação)

### 11.4 Viés de Sobrevivência
- Sistema não considera empresas que faliram ou foram delistadas
- Pode superestimar retornos históricos

## 12. Referências

### 12.1 Metodologias
- **Momentum**: Jegadeesh & Titman (1993)
- **Quality**: Piotroski F-Score adaptado
- **Value**: Graham & Dodd value investing
- **Multi-Factor**: Fama-French 3-Factor Model

### 12.2 Normalização
- **Z-Score**: Cross-sectional standardization
- **Outlier Treatment**: Winsorization at ±3σ

### 12.3 Fontes de Dados
- **Yahoo Finance**: Preços e fundamentos
- **B3**: Lista de ativos líquidos
