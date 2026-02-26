# Cálculos do Ranking - Regras Completas v2.5.2

## 📋 Índice

1. [Arquitetura do Pipeline](#arquitetura-do-pipeline)
2. [Layer 1: Elegibilidade Estrutural](#layer-1-elegibilidade-estrutural)
3. [Layer 2: Feature Engineering](#layer-2-feature-engineering)
4. [Layer 3: Scoring & Normalization](#layer-3-scoring--normalization)
5. [Tratamento de Missing Values](#tratamento-de-missing-values)
6. [Pesos e Fórmulas](#pesos-e-fórmulas)

---

## Arquitetura do Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ INPUT: 50 tickers (modo liquid)                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: STRUCTURAL ELIGIBILITY                             │
│ • Valida dados brutos (equity, ebitda, revenue, volume)    │
│ • Exclui ativos estruturalmente inviáveis                   │
│ • Meta: >= 80% passam                                       │
│ • NUNCA verifica fatores derivados                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    40-45 elegíveis
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: FEATURE ENGINEERING                                │
│ • Calcula TODAS as features (mantém NaN se insuficiente)   │
│ • Imputa missing values (mediana setorial/universal)        │
│ • Normaliza cross-sectional (z-score + winsorização)        │
│ • NUNCA exclui ativos                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    40-45 com features
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: SCORING & NORMALIZATION                            │
│ • Calcula scores por categoria (retorna NaN se ausente)    │
│ • Redistribui pesos quando há NaN                           │
│ • Gera ranking final                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    OUTPUT: Ranking
```

---

## Layer 1: Elegibilidade Estrutural

### Objetivo
Excluir apenas ativos com problemas estruturais graves que indicam distress financeiro ou iliquidez.

### Critérios de Exclusão

#### 1. Patrimônio Líquido <= 0
```python
if shareholders_equity is None or shareholders_equity <= 0:
    exclude("negative_or_zero_equity")
```
**Razão**: Patrimônio negativo indica falência técnica.

#### 2. EBITDA <= 0 (exceto bancos)
```python
if ebitda is None or ebitda <= 0:
    if not is_financial_institution:
        exclude("negative_or_zero_ebitda")
```
**Razão**: Sem geração operacional de caixa.
**Exceção**: Bancos não reportam EBITDA.

#### 3. Receita <= 0
```python
if revenue is None or revenue <= 0:
    exclude("negative_or_zero_revenue")
```
**Razão**: Sem atividade comercial.

#### 4. Volume Médio < 100k
```python
if avg_volume_90d < 100_000:
    exclude("low_volume")
```
**Razão**: Ativo ilíquido, difícil de negociar.

#### 5. Lucro Líquido Negativo (último ano)
```python
if net_income_last_year < 0:
    exclude("negative_net_income_last_year")
```
**Razão**: Prejuízo atual.

#### 6. Lucro Negativo em 2 dos Últimos 3 Anos
```python
negative_years = sum(1 for ni in net_income_history if ni < 0)
if negative_years >= 2:
    exclude("negative_net_income_2_of_3_years")
```
**Razão**: Prejuízo persistente.

#### 7. Dívida Líquida / EBITDA > 8
```python
if net_debt_to_ebitda > 8:
    exclude("excessive_leverage_debt_to_ebitda_gt_8")
```
**Razão**: Alavancagem excessiva, risco de default.

### ⚠️ REGRA CRÍTICA

**NUNCA exclui por ausência de fatores derivados**:
- ❌ NÃO verifica: momentum_6m_ex_1m, roe_mean_3y, pe_ratio, price_to_book
- ✅ Verifica APENAS: dados brutos (equity, ebitda, revenue, volume)

---

## Layer 2: Feature Engineering

### 2.1 Cálculo de Features

#### Momentum Factors (Diários)

**momentum_6m_ex_1m** (Acadêmico)
```python
# Retorno de 6 meses excluindo último mês
# Evita reversão de curto prazo
price_6m_ago = prices.iloc[-126]  # ~6 meses
price_1m_ago = prices.iloc[-21]   # ~1 mês
momentum_6m_ex_1m = (price_1m_ago / price_6m_ago) - 1
```

**momentum_12m_ex_1m** (Acadêmico)
```python
# Retorno de 12 meses excluindo último mês
price_12m_ago = prices.iloc[-252]  # ~12 meses
price_1m_ago = prices.iloc[-21]    # ~1 mês
momentum_12m_ex_1m = (price_1m_ago / price_12m_ago) - 1
```

**volatility_90d**
```python
# Volatilidade anualizada
returns = prices.pct_change()
volatility_90d = returns.tail(90).std() * np.sqrt(252)
```

**recent_drawdown**
```python
# Drawdown atual vs máximo recente
rolling_max = prices.rolling(90).max()
drawdown = (prices / rolling_max) - 1
recent_drawdown = drawdown.iloc[-1]
```

#### Quality Factors (Mensais)

**roe_mean_3y**
```python
# ROE médio dos últimos 3 anos
roe_history = [f.net_income / f.shareholders_equity for f in last_3_years]
roe_mean_3y = np.mean(roe_history)
```

**roe_volatility**
```python
# Volatilidade do ROE (estabilidade)
roe_volatility = np.std(roe_history)
```

**net_margin**
```python
# Margem líquida
net_margin = net_income / revenue
```

**revenue_growth_3y**
```python
# CAGR de receita 3 anos
revenue_growth_3y = (revenue_now / revenue_3y_ago) ** (1/3) - 1
```

**debt_to_ebitda**
```python
# Alavancagem
debt_to_ebitda = total_debt / ebitda
```

#### Value Factors (Mensais)

**pe_ratio**
```python
# Price-to-Earnings
pe_ratio = current_price / eps
```

**price_to_book**
```python
# Price-to-Book
price_to_book = market_cap / shareholders_equity
```

**ev_ebitda**
```python
# Enterprise Value / EBITDA
ev_ebitda = enterprise_value / ebitda
```

**fcf_yield**
```python
# Free Cash Flow Yield
fcf_yield = free_cash_flow / market_cap
```

#### Size Factor (Mensal)

**size_factor**
```python
# Logaritmo negativo do market cap
# Empresas menores = valores maiores (size premium)
size_factor = -np.log(market_cap)
```

### 2.2 Tratamento de Missing Values

#### Ordem de Execução
```
1. Calcular features (mantém NaN se dados insuficientes)
2. Identificar NaNs
3. Impute valores
4. Aplicar winsorização (±3σ)
5. Aplicar z-score cross-sectional
6. Salvar features normalizadas
```

#### Regra de Imputação
```python
def impute_missing(feature, sector_map):
    for ticker with NaN:
        # Tentar mediana setorial
        sector = sector_map[ticker]
        sector_tickers = [t for t in tickers if sector_map[t] == sector]
        
        if len(sector_tickers) >= 5:
            # Usar mediana do setor
            value = median([feature[t] for t in sector_tickers if not isnan(feature[t])])
        else:
            # Usar mediana do universo
            value = median([feature[t] for t in tickers if not isnan(feature[t])])
        
        feature[ticker] = value
```

#### Fallback
```python
# Se TODOS os valores forem NaN
if all(isnan(feature[t]) for t in tickers):
    # Usar 0 após normalização
    feature[:] = 0.0
```

### 2.3 Normalização

#### Z-Score Cross-Sectional
```python
def normalize(features):
    mean = features.mean()
    std = features.std()
    normalized = (features - mean) / std
    return normalized
```

#### Winsorização
```python
def winsorize(features, n_std=3):
    mean = features.mean()
    std = features.std()
    lower = mean - n_std * std
    upper = mean + n_std * std
    return features.clip(lower, upper)
```

---

## Layer 3: Scoring & Normalization

### 3.1 Scores por Categoria

#### Momentum Score
```python
def calculate_momentum_score(factors):
    # Fatores disponíveis (ignorando NaN)
    momentum_factors = []
    
    # Adicionar momentum_6m_ex_1m se disponível
    if not isnan(factors['momentum_6m_ex_1m']):
        momentum_factors.append(factors['momentum_6m_ex_1m'])
    
    # Adicionar momentum_12m_ex_1m se disponível
    if not isnan(factors['momentum_12m_ex_1m']):
        momentum_factors.append(factors['momentum_12m_ex_1m'])
    
    # Adicionar volatility_90d se disponível (invertido)
    if not isnan(factors['volatility_90d']):
        momentum_factors.append(-factors['volatility_90d'])
    
    # Adicionar recent_drawdown se disponível (invertido)
    if not isnan(factors['recent_drawdown']):
        momentum_factors.append(-factors['recent_drawdown'])
    
    # Se nenhum fator disponível, retorna NaN
    if not momentum_factors:
        return NaN
    
    # Média dos fatores disponíveis
    return mean(momentum_factors)
```

#### Quality Score
```python
def calculate_quality_score(factors):
    quality_factors = []
    
    # Adicionar fatores positivos
    for factor in ['roe_mean_3y', 'net_margin', 'revenue_growth_3y']:
        if not isnan(factors[factor]):
            quality_factors.append(factors[factor])
    
    # Adicionar fatores invertidos (menor é melhor)
    for factor in ['roe_volatility', 'debt_to_ebitda']:
        if not isnan(factors[factor]):
            quality_factors.append(-factors[factor])
    
    if not quality_factors:
        return NaN
    
    return mean(quality_factors)
```

#### Value Score
```python
def calculate_value_score(factors):
    value_factors = []
    
    # Fatores invertidos (menor é melhor)
    for factor in ['pe_ratio', 'price_to_book', 'ev_ebitda']:
        if not isnan(factors[factor]):
            value_factors.append(-factors[factor])
    
    # FCF Yield (maior é melhor)
    if not isnan(factors['fcf_yield']):
        value_factors.append(factors['fcf_yield'])
    
    if not value_factors:
        return NaN
    
    return mean(value_factors)
```

#### Size Score
```python
def calculate_size_score(factors):
    # Size factor já está normalizado e com sinal correto
    # Valores positivos = empresas menores = size premium
    if not isnan(factors['size_factor']):
        return factors['size_factor']
    return 0.0
```

### 3.2 Score Final

#### Redistribuição de Pesos
```python
def calculate_final_score(momentum_score, quality_score, value_score, size_score):
    # Pesos configuráveis
    weights = {
        'momentum': 0.35,
        'quality': 0.25,
        'value': 0.30,
        'size': 0.10
    }
    
    # Coletar scores e pesos válidos (não NaN)
    scores_and_weights = []
    
    if not isnan(momentum_score):
        scores_and_weights.append((momentum_score, weights['momentum']))
    
    if not isnan(quality_score):
        scores_and_weights.append((quality_score, weights['quality']))
    
    if not isnan(value_score):
        scores_and_weights.append((value_score, weights['value']))
    
    if size_score != 0.0 and not isnan(size_score):
        scores_and_weights.append((size_score, weights['size']))
    
    # Se nenhum score disponível, retorna 0
    if not scores_and_weights:
        return 0.0
    
    # Calcular soma dos pesos válidos
    total_weight = sum(weight for _, weight in scores_and_weights)
    
    # Calcular score final ponderado (renormalizando pesos)
    final_score = sum(score * (weight / total_weight) 
                     for score, weight in scores_and_weights)
    
    return final_score
```

#### Exemplo de Redistribuição
```
Caso 1: Todos os scores disponíveis
  momentum=0.5, quality=0.3, value=-0.2, size=0.1
  final = 0.5*0.35 + 0.3*0.25 + (-0.2)*0.30 + 0.1*0.10
  final = 0.175 + 0.075 - 0.06 + 0.01 = 0.20

Caso 2: Value ausente (NaN)
  momentum=0.5, quality=0.3, value=NaN, size=0.1
  Pesos redistribuídos: momentum=50%, quality=35.7%, size=14.3%
  final = 0.5*0.50 + 0.3*0.357 + 0.1*0.143
  final = 0.25 + 0.107 + 0.014 = 0.371

Caso 3: Apenas momentum disponível
  momentum=0.5, quality=NaN, value=NaN, size=NaN
  Peso redistribuído: momentum=100%
  final = 0.5*1.0 = 0.50
```

---

## Pesos e Fórmulas

### Pesos Padrão

```python
MOMENTUM_WEIGHT = 0.35  # 35%
QUALITY_WEIGHT = 0.25   # 25%
VALUE_WEIGHT = 0.30     # 30%
SIZE_WEIGHT = 0.10      # 10%
```

### Fórmula Final

```
final_score = Σ (score_i * weight_i) / Σ weight_i

onde:
  score_i = score da categoria i (se não NaN)
  weight_i = peso da categoria i (se score_i não NaN)
```

### Distribuição Esperada

```
Média: ~0.00
Desvio padrão: 0.2 - 0.5
Range: [-3, +3]
```

---

## Garantias do Sistema

### ✅ Determinismo
- Mesmos inputs → mesmos outputs
- Sem aleatoriedade no pipeline

### ✅ Sem Exclusões por Missing
- Nenhum ativo excluído por ausência de fatores derivados
- Imputação automática de missing values

### ✅ Estabilidade Estatística
- Scores distribuídos em faixa razoável
- Sem valores extremos artificiais
- Normalização robusta

### ✅ Transparência
- Logs detalhados em cada camada
- Rastreamento de imputações
- Métricas de qualidade

---

## Referências

- Jegadeesh, N., & Titman, S. (1993). Returns to Buying Winners and Selling Losers
- Fama, F. F., & French, K. R. (1992). The Cross-Section of Expected Stock Returns
- Piotroski, J. D. (2000). Value Investing: The Use of Historical Financial Statement Information
- Novy-Marx, R. (2013). The Other Side of Value: The Gross Profitability Premium
