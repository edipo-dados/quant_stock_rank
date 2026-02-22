# Estrutura de Dados e Cálculos do Sistema de Ranking

## Visão Geral

Este documento explica detalhadamente como o sistema de ranking quantitativo processa dados brutos de ações e calcula scores finais para gerar o ranking. O sistema segue uma arquitetura em camadas com separação clara entre dados brutos, features calculadas e scores finais.

## Índice

1. [Fluxo de Dados Completo](#fluxo-de-dados-completo)
2. [Estrutura de Dados por Camada](#estrutura-de-dados-por-camada)
3. [Etapa 1: Ingestão de Dados](#etapa-1-ingestão-de-dados)
4. [Etapa 2: Filtro de Elegibilidade](#etapa-2-filtro-de-elegibilidade)
5. [Etapa 3: Cálculo de Fatores](#etapa-3-cálculo-de-fatores)
6. [Etapa 4: Normalização Cross-Sectional](#etapa-4-normalização-cross-sectional)
7. [Etapa 5: Cálculo de Scores](#etapa-5-cálculo-de-scores)
8. [Etapa 6: Geração de Ranking](#etapa-6-geração-de-ranking)
9. [Exemplos Práticos](#exemplos-práticos)
10. [Configurações e Pesos](#configurações-e-pesos)

---

## Fluxo de Dados Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE RANKING                          │
└─────────────────────────────────────────────────────────────────┘

1. INGESTÃO DE DADOS
   ├─ Yahoo Finance (Preços) → raw_prices_daily
   └─ Yahoo Finance (Fundamentos) → raw_fundamentals

2. FILTRO DE ELEGIBILIDADE
   ├─ Verifica saúde financeira mínima
   ├─ Exclui empresas em distress
   └─ Retorna: ativos elegíveis + razões de exclusão

3. CÁLCULO DE FATORES (apenas ativos elegíveis)
   ├─ Fatores de Momentum → features_daily
   └─ Fatores Fundamentalistas → features_monthly

4. NORMALIZAÇÃO CROSS-SECTIONAL
   ├─ Aplica z-score em cada fator
   ├─ Compara todos os ativos no mesmo período
   └─ Resultado: fatores com média ~0 e std ~1

5. CÁLCULO DE SCORES
   ├─ Score de Momentum (peso 40%)
   ├─ Score de Qualidade (peso 30%)
   ├─ Score de Valor (peso 30%)
   ├─ Penalidades de Risco
   └─ Score Final → scores_daily

6. GERAÇÃO DE RANKING
   ├─ Ordena por score final (decrescente)
   ├─ Atribui posições (1 = melhor)
   └─ Resultado: ranking completo
```

---

## Estrutura de Dados por Camada

### Camada 1: Dados Brutos (Raw Data)

#### Tabela: `raw_prices_daily`
Armazena dados históricos de preços diários.

```python
{
    "ticker": "PETR4.SA",
    "date": "2024-02-20",
    "open": 38.50,
    "high": 39.20,
    "low": 38.30,
    "close": 38.90,
    "adj_close": 38.90,  # Ajustado por splits/dividendos
    "volume": 45_234_567
}
```

**Fonte**: Yahoo Finance API (yfinance)
**Período**: Últimos 400 dias (para cálculos de 12 meses)

#### Tabela: `raw_fundamentals`
Armazena dados fundamentalistas anuais.

```python
{
    "ticker": "PETR4.SA",
    "period_end_date": "2023-12-31",
    "period_type": "annual",
    
    # Income Statement
    "revenue": 450_000_000_000,
    "net_income": 120_000_000_000,
    "ebitda": 180_000_000_000,
    "eps": 9.50,
    
    # Balance Sheet
    "total_assets": 800_000_000_000,
    "total_debt": 200_000_000_000,
    "shareholders_equity": 400_000_000_000,
    "book_value_per_share": 32.00,
    
    # Cash Flow
    "operating_cash_flow": 150_000_000_000,
    "free_cash_flow": 100_000_000_000,
    
    # Metrics
    "market_cap": 500_000_000_000,
    "enterprise_value": 650_000_000_000
}
```

**Fonte**: Yahoo Finance API (fundamentals)
**Período**: Últimos 3-4 anos anuais

---

### Camada 2: Features Calculadas

#### Tabela: `features_daily`
Fatores de momentum calculados e normalizados.

```python
{
    "ticker": "PETR4.SA",
    "date": "2024-02-20",
    
    # Fatores de Momentum (normalizados via z-score)
    "return_6m": 0.85,        # Retorno 6 meses (z-score)
    "return_12m": 1.20,       # Retorno 12 meses (z-score)
    "rsi_14": -0.30,          # RSI 14 períodos (z-score)
    "volatility_90d": -0.50,  # Volatilidade 90 dias (z-score, invertido)
    "recent_drawdown": 0.20   # Drawdown recente (z-score, invertido)
}
```

#### Tabela: `features_monthly`
Fatores fundamentalistas calculados e normalizados.

```python
{
    "ticker": "PETR4.SA",
    "month": "2024-02-01",  # Primeiro dia do mês
    
    # Fatores Fundamentalistas (normalizados via z-score)
    "roe": 1.50,                    # ROE robusto (média 3 anos, z-score)
    "roe_mean_3y": 0.28,            # ROE médio 3 anos (valor bruto)
    "roe_volatility": 0.05,         # Volatilidade do ROE
    "net_margin": 0.90,             # Margem líquida (z-score)
    "revenue_growth_3y": 0.60,      # Crescimento receita 3 anos (z-score)
    "debt_to_ebitda": -0.80,        # Dívida/EBITDA (z-score, invertido)
    "debt_to_ebitda_raw": 1.2,      # Dívida/EBITDA (valor bruto)
    "pe_ratio": -0.40,              # P/L (z-score, invertido)
    "ev_ebitda": -0.30,             # EV/EBITDA (z-score, invertido)
    "pb_ratio": -0.20,              # P/VP (z-score, invertido)
    
    # Campos de Robustez
    "net_income_last_year": 120_000_000_000,
    "net_income_history": [100_000_000_000, 110_000_000_000, 120_000_000_000]
}
```

---

### Camada 3: Scores Finais

#### Tabela: `scores_daily`
Scores finais e ranking.

```python
{
    "ticker": "PETR4.SA",
    "date": "2024-02-20",
    
    # Scores por Categoria
    "momentum_score": 0.65,    # Média dos fatores de momentum
    "quality_score": 0.80,     # Média dos fatores de qualidade
    "value_score": -0.30,      # Média dos fatores de valor
    
    # Score Final
    "base_score": 0.48,        # Score antes das penalidades
    "final_score": 0.38,       # Score após penalidades
    "confidence": 0.50,        # Confiança (placeholder)
    
    # Penalidades de Risco
    "risk_penalty_factor": 0.8,
    "risk_penalties": {
        "volatility": 1.0,     # Sem penalidade
        "drawdown": 0.8,       # Penalidade aplicada
        "distress": 1.0        # Sem penalidade
    },
    
    # Elegibilidade
    "passed_eligibility": true,
    "exclusion_reasons": [],
    "distress_flag": false,
    
    # Ranking
    "rank": 5  # Posição no ranking (1 = melhor)
}
```

---

## Etapa 1: Ingestão de Dados

### Objetivo
Coletar dados brutos de preços e fundamentos das APIs externas.

### Fontes de Dados

#### Yahoo Finance - Preços Diários
```python
# Biblioteca: yfinance
import yfinance as yf

ticker_obj = yf.Ticker("PETR4.SA")
df = ticker_obj.history(start="2023-01-01", end="2024-02-20")

# Retorna DataFrame com:
# - Date (índice)
# - Open, High, Low, Close
# - Volume
# - Dividends, Stock Splits
```

#### Yahoo Finance - Fundamentos
```python
# Dados fundamentalistas anuais
ticker_obj = yf.Ticker("PETR4.SA")

# Income Statement
income_stmt = ticker_obj.financials  # Anual

# Balance Sheet
balance_sheet = ticker_obj.balance_sheet

# Cash Flow
cash_flow = ticker_obj.cashflow

# Métricas calculadas
info = ticker_obj.info  # Contém market_cap, enterprise_value, etc.
```

### Persistência
Os dados brutos são salvos sem transformações nas tabelas:
- `raw_prices_daily`: Um registro por ticker/data
- `raw_fundamentals`: Um registro por ticker/período

---

## Etapa 2: Filtro de Elegibilidade

### Objetivo
Excluir empresas financeiramente distressed antes do cálculo de fatores.

### Critérios de Exclusão

Um ativo é **EXCLUÍDO** se:

1. **Patrimônio Líquido ≤ 0**
   ```python
   shareholders_equity <= 0
   # Razão: "negative_or_zero_equity"
   ```

2. **EBITDA ≤ 0** (exceto instituições financeiras)
   ```python
   ebitda <= 0 and not is_financial_institution
   # Razão: "negative_or_zero_ebitda"
   ```

3. **Receita ≤ 0**
   ```python
   revenue <= 0
   # Razão: "negative_or_zero_revenue"
   ```

4. **Volume Médio < Mínimo** (default: 100.000 ações/dia)
   ```python
   avg_daily_volume < minimum_volume
   # Razão: "low_volume"
   ```

5. **Lucro Líquido Negativo no Último Ano**
   ```python
   net_income_last_year < 0
   # Razão: "negative_net_income_last_year"
   ```

6. **Lucro Negativo em 2 dos Últimos 3 Anos**
   ```python
   negative_years = sum(1 for ni in net_income_history if ni < 0)
   if negative_years >= 2:
       # Razão: "negative_net_income_2_of_3_years"
   ```

7. **Dívida Líquida / EBITDA > 8**
   ```python
   net_debt_to_ebitda > 8
   # Razão: "excessive_leverage_debt_to_ebitda_gt_8"
   ```

### Exemplo de Exclusão

```python
# Americanas (AMER3.SA) - Exemplo real
{
    "ticker": "AMER3.SA",
    "passed_eligibility": False,
    "exclusion_reasons": [
        "negative_net_income_last_year",
        "negative_net_income_2_of_3_years",
        "excessive_leverage_debt_to_ebitda_gt_8"
    ]
}

# Banco com EBITDA ausente (normal) - NÃO é excluído
{
    "ticker": "ITUB4.SA",
    "passed_eligibility": True,
    "exclusion_reasons": [],
    "note": "EBITDA ausente é normal para bancos"
}
```

### Resultado
- **Ativos Elegíveis**: Prosseguem para cálculo de fatores
- **Ativos Excluídos**: Recebem score = 0 e não aparecem no ranking

---

## Etapa 3: Cálculo de Fatores

### Detecção Automática de Setor

O sistema detecta automaticamente se um ativo é uma **instituição financeira** ou **empresa industrial** e aplica fatores específicos:

#### Critérios de Detecção:
1. **Método Preferencial**: Consulta tabela `AssetInfo` para verificar setor
   - Setores financeiros: "Financial Services", "Financial", "Banks", "Insurance", "Real Estate"
2. **Método Heurístico (Fallback)**: Análise dos dados fundamentalistas
   - Bancos tipicamente não reportam EBITDA mas têm revenue e equity válidos

#### Fatores por Setor:

**Instituições Financeiras (Bancos)**:
- **Qualidade**: ROE 3Y (cap 30%), Crescimento lucro 3Y, Estabilidade lucro, Índice eficiência
- **Valor**: P/L, P/VP
- **Remove**: EV/EBITDA, Debt/EBITDA (não aplicáveis)

**Empresas Industriais**:
- **Qualidade**: ROE 3Y (cap 50%), Margem líquida, Crescimento receita 3Y, Debt/EBITDA
- **Valor**: P/L, EV/EBITDA, P/VP
- **Inclui**: Todas as métricas tradicionais

### 3.1 Fatores de Momentum (Diários)

Calculados a partir de dados de preços históricos (aplicados igualmente para todos os setores).

#### Return 6 Meses
```python
# Fórmula
return_6m = (preço_final / preço_inicial) - 1

# Exemplo
preço_126_dias_atrás = 35.00
preço_hoje = 38.90
return_6m = (38.90 / 35.00) - 1 = 0.1114  # 11.14%
```

#### Return 12 Meses
```python
# Fórmula
return_12m = (preço_final / preço_inicial) - 1

# Exemplo
preço_252_dias_atrás = 30.00
preço_hoje = 38.90
return_12m = (38.90 / 30.00) - 1 = 0.2967  # 29.67%
```

#### RSI 14 Períodos
```python
# Fórmula
# 1. Calcular mudanças de preço diárias
delta = preços.diff()

# 2. Separar ganhos e perdas
ganhos = delta.where(delta > 0, 0)
perdas = -delta.where(delta < 0, 0)

# 3. Calcular médias móveis de 14 dias
avg_ganho = ganhos.rolling(14).mean()
avg_perda = perdas.rolling(14).mean()

# 4. Calcular RS e RSI
RS = avg_ganho / avg_perda
RSI = 100 - (100 / (1 + RS))

# Exemplo
avg_ganho = 0.50
avg_perda = 0.30
RS = 0.50 / 0.30 = 1.67
RSI = 100 - (100 / (1 + 1.67)) = 62.5
```

#### Volatilidade 90 Dias
```python
# Fórmula
# 1. Calcular retornos diários
retornos = preços.pct_change()

# 2. Calcular desvio padrão
std_diário = retornos.std()

# 3. Anualizar (252 dias úteis/ano)
volatilidade = std_diário * sqrt(252)

# Exemplo
std_diário = 0.025  # 2.5% ao dia
volatilidade = 0.025 * sqrt(252) = 0.397  # 39.7% ao ano
```

#### Drawdown Recente
```python
# Fórmula
# 1. Encontrar pico nos últimos 90 dias
pico = max(preços_90d)

# 2. Calcular drawdown atual
drawdown = (preço_atual - pico) / pico

# Exemplo
pico = 42.00
preço_atual = 38.90
drawdown = (38.90 - 42.00) / 42.00 = -0.0738  # -7.38%
```

### 3.2 Fatores Fundamentalistas (Mensais)

Calculados a partir de demonstrações financeiras com **diferenciação por setor**.

#### Para Instituições Financeiras (Bancos)

##### ROE Robusto (Cap 30% para Bancos)
```python
# Fórmula (igual às industriais, mas com cap menor)
ROE_final = min(ROE_robusto, 0.30)  # Cap de 30% vs 50% para industriais

# Exemplo para banco
ROE_ano1 = 0.25  # 25%
ROE_ano2 = 0.28  # 28%
ROE_ano3 = 0.35  # 35% (será limitado)
ROE_robusto = (0.25 + 0.28 + 0.35) / 3 = 0.293
ROE_final = min(0.293, 0.30) = 0.293  # 29.3%
```

##### ROA (Return on Assets) - Específico para Bancos
```python
# Fórmula
ROA = net_income / total_assets

# Exemplo
net_income = 15_000_000_000
total_assets = 1_500_000_000_000
ROA = 15 / 1500 = 0.01  # 1.0%
```

##### Índice de Eficiência - Específico para Bancos
```python
# Fórmula (menor é melhor)
efficiency_ratio = operating_expenses / (net_interest_income + non_interest_income)

# Exemplo
operating_expenses = 8_000_000_000
net_interest_income = 12_000_000_000
non_interest_income = 3_000_000_000
efficiency_ratio = 8 / (12 + 3) = 0.533  # 53.3%
```

##### Crescimento do Patrimônio Líquido (Book Value Growth)
```python
# Fórmula (proxy para crescimento de lucro em bancos)
book_value_growth = (equity_final / equity_inicial)^(1/anos) - 1

# Exemplo
equity_2021 = 80_000_000_000
equity_2023 = 95_000_000_000
anos = 2
growth = (95 / 80)^(1/2) - 1 = 0.089  # 8.9% ao ano
```

#### Para Empresas Industriais

##### ROE Robusto (Cap 50% para Industriais)
```python
# Fórmula
# 1. Calcular ROE para cada ano
ROE_ano1 = net_income_ano1 / shareholders_equity_ano1
ROE_ano2 = net_income_ano2 / shareholders_equity_ano2
ROE_ano3 = net_income_ano3 / shareholders_equity_ano3

# 2. Aplicar winsorização (limitar outliers aos percentis 5º/95º)
roes = [ROE_ano1, ROE_ano2, ROE_ano3]
roes_winsorized = winsorize(roes, lower=0.05, upper=0.95)

# 3. Calcular média
ROE_robusto = mean(roes_winsorized)

# 4. Aplicar cap em 50%
ROE_final = min(ROE_robusto, 0.50)

# Exemplo
ROE_ano1 = 0.25  # 25%
ROE_ano2 = 0.28  # 28%
ROE_ano3 = 0.30  # 30%
ROE_robusto = (0.25 + 0.28 + 0.30) / 3 = 0.277  # 27.7%
```

#### Margem Líquida
```python
# Fórmula
margem_liquida = net_income / revenue

# Exemplo
net_income = 120_000_000_000
revenue = 450_000_000_000
margem_liquida = 120 / 450 = 0.267  # 26.7%
```

#### Crescimento de Receita 3 Anos (CAGR)
```python
# Fórmula
CAGR = (receita_final / receita_inicial)^(1/anos) - 1

# Exemplo
receita_2021 = 350_000_000_000
receita_2023 = 450_000_000_000
anos = 2
CAGR = (450 / 350)^(1/2) - 1 = 0.131  # 13.1% ao ano
```

#### Dívida / EBITDA
```python
# Fórmula
debt_to_ebitda = total_debt / ebitda

# Exemplo
total_debt = 200_000_000_000
ebitda = 180_000_000_000
debt_to_ebitda = 200 / 180 = 1.11
```

#### P/L (Price to Earnings)
```python
# Fórmula
pe_ratio = preço_ação / lucro_por_ação

# Exemplo
preço = 38.90
eps = 9.50
pe_ratio = 38.90 / 9.50 = 4.09
```

#### EV/EBITDA
```python
# Fórmula
ev_ebitda = enterprise_value / ebitda

# Exemplo
enterprise_value = 650_000_000_000
ebitda = 180_000_000_000
ev_ebitda = 650 / 180 = 3.61
```

#### P/VP (Price to Book)
```python
# Fórmula
pb_ratio = preço_ação / valor_patrimonial_por_ação

# Exemplo
preço = 38.90
book_value_per_share = 32.00
pb_ratio = 38.90 / 32.00 = 1.22
```

---

## Etapa 4: Normalização Cross-Sectional

### Objetivo
Transformar fatores para serem comparáveis entre ativos diferentes.

### Método: Z-Score Cross-Sectional

Para cada fator, comparamos todos os ativos no mesmo período:

```python
# Fórmula
z_score = (valor - média) / desvio_padrão

# Onde:
# - média = média de todos os ativos no mesmo dia/mês
# - desvio_padrão = desvio padrão de todos os ativos
```

### Exemplo Prático

Suponha 3 ativos com ROE:

```python
# Valores brutos
PETR4: ROE = 0.28  # 28%
VALE3: ROE = 0.15  # 15%
ITUB4: ROE = 0.22  # 22%

# Calcular média e desvio padrão
média = (0.28 + 0.15 + 0.22) / 3 = 0.217
desvio = sqrt(((0.28-0.217)² + (0.15-0.217)² + (0.22-0.217)²) / 2) = 0.065

# Normalizar cada valor
PETR4: z_score = (0.28 - 0.217) / 0.065 = 0.97
VALE3: z_score = (0.15 - 0.217) / 0.065 = -1.03
ITUB4: z_score = (0.22 - 0.217) / 0.065 = 0.05
```

### Interpretação do Z-Score

- **z > 0**: Acima da média (melhor que a média)
- **z = 0**: Na média
- **z < 0**: Abaixo da média (pior que a média)
- **|z| > 2**: Outlier (muito acima ou abaixo da média)

### Inversão de Fatores

Alguns fatores são **invertidos** porque valores menores são melhores:

```python
# Fatores invertidos (menor é melhor)
- volatility_90d: z_score_final = -z_score_original
- recent_drawdown: z_score_final = -z_score_original
- debt_to_ebitda: z_score_final = -z_score_original
- pe_ratio: z_score_final = -z_score_original
- ev_ebitda: z_score_final = -z_score_original
- pb_ratio: z_score_final = -z_score_original
```

---

## Etapa 5: Cálculo de Scores

### Detecção Automática de Setor no Scoring

O sistema detecta automaticamente o setor e aplica scoring específico:

```python
# Critério de detecção
is_financial = (
    debt_to_ebitda is None and 
    ev_ebitda is None and 
    (roa is not None or efficiency_ratio is not None)
)
```

### 5.1 Score de Momentum (Peso 40%)

Aplicado igualmente para todos os setores:

Média dos fatores de momentum normalizados:

```python
# Fórmula
momentum_score = mean([
    return_6m,
    return_12m,
    rsi_14,
    -volatility_90d,      # Invertido
    -recent_drawdown      # Invertido
])

# Exemplo
return_6m = 0.85
return_12m = 1.20
rsi_14 = -0.30
volatility_90d = -0.50  # Já invertido
recent_drawdown = 0.20  # Já invertido

momentum_score = (0.85 + 1.20 + (-0.30) + (-0.50) + 0.20) / 5
momentum_score = 1.45 / 5 = 0.29
```

### 5.2 Score de Qualidade (Peso 30%)

#### Para Instituições Financeiras

```python
# Fórmula para bancos
quality_score_financial = mean([
    roe_3y,                    # ROE 3Y (cap 30%)
    book_value_growth,         # Crescimento lucro 3Y
    -net_income_volatility,    # Estabilidade lucro (invertido)
    -efficiency_ratio          # Índice eficiência (invertido)
])

# Exemplo
roe_3y = 1.20              # Z-score normalizado
book_value_growth = 0.80   # Z-score normalizado
net_income_volatility = -0.30  # Já invertido
efficiency_ratio = -0.50   # Já invertido

quality_score = (1.20 + 0.80 + (-0.30) + (-0.50)) / 4 = 0.30
```

#### Para Empresas Industriais

Média dos fatores de qualidade normalizados:

```python
# Fórmula
quality_score = mean([
    roe_mean_3y,
    -roe_volatility,      # Invertido
    net_margin,
    revenue_growth_3y,
    -debt_to_ebitda       # Invertido
])

# Exemplo
roe_mean_3y = 1.50
roe_volatility = -0.20  # Já invertido
net_margin = 0.90
revenue_growth_3y = 0.60
debt_to_ebitda = -0.80  # Já invertido

quality_score = (1.50 + (-0.20) + 0.90 + 0.60 + (-0.80)) / 5
quality_score = 2.00 / 5 = 0.40
```

#### Penalidades no Score de Qualidade

O score de qualidade pode sofrer penalizações:

```python
# 1. Penalidade por Prejuízo Recente
if net_income_last_year < 0:
    quality_score *= 0.4  # Reduz em 60%

# 2. Penalização Progressiva de Endividamento
if debt_to_ebitda_raw > 5:
    quality_score *= 0.7  # Penalização forte
elif debt_to_ebitda_raw > 3:
    quality_score *= 0.9  # Penalização leve
```

### 5.3 Score de Valor (Peso 30%)

#### Para Instituições Financeiras

```python
# Fórmula para bancos (remove EV/EBITDA)
value_score_financial = mean([
    -pe_ratio,      # P/L (invertido)
    -pb_ratio       # P/VP (invertido - métrica chave para bancos)
])

# Exemplo
pe_ratio = -0.40  # Já invertido
pb_ratio = -0.60  # Já invertido (P/VP é mais importante para bancos)

value_score = ((-0.40) + (-0.60)) / 2 = -0.50
```

#### Para Empresas Industriais

Média dos fatores de valor normalizados (todos invertidos):

```python
# Fórmula
value_score = mean([
    -pe_ratio,      # Invertido
    -ev_ebitda,     # Invertido
    -pb_ratio       # Invertido
])

# Exemplo
pe_ratio = -0.40  # Já invertido
ev_ebitda = -0.30  # Já invertido
pb_ratio = -0.20  # Já invertido

value_score = ((-0.40) + (-0.30) + (-0.20)) / 3
value_score = -0.90 / 3 = -0.30
```

### 5.4 Score Base

Combinação ponderada dos três scores:

```python
# Fórmula (pesos configuráveis)
base_score = (
    momentum_weight * momentum_score +
    quality_weight * quality_score +
    value_weight * value_score
)

# Pesos padrão
momentum_weight = 0.40  # 40%
quality_weight = 0.30   # 30%
value_weight = 0.30     # 30%

# Exemplo
base_score = (0.40 * 0.29) + (0.30 * 0.40) + (0.30 * -0.30)
base_score = 0.116 + 0.120 + (-0.090)
base_score = 0.146
```

### 5.5 Penalidades de Risco

Aplicadas ao score base para obter o score final:

```python
# Penalidade de Volatilidade
if volatility_180d > volatility_limit:  # default: 0.40 (40% ao ano)
    volatility_penalty = 0.8
else:
    volatility_penalty = 1.0

# Penalidade de Drawdown
if max_drawdown_3y < drawdown_limit:  # default: -0.30 (-30%)
    drawdown_penalty = 0.8
else:
    drawdown_penalty = 1.0

# Penalidade de Distress (condições críticas)
distress_conditions = [
    net_income_last_year < 0,
    negative_years >= 2,  # 2 dos últimos 3 anos
    debt_to_ebitda_raw > 5
]

if any(distress_conditions):
    distress_penalty = 0.5  # Reduz em 50%
else:
    distress_penalty = 1.0

# Combinar penalidades (multiplicativo)
risk_penalty_factor = volatility_penalty * drawdown_penalty * distress_penalty
```

### 5.6 Score Final

```python
# Fórmula
final_score = base_score * risk_penalty_factor

# Exemplo 1: Sem penalidades
base_score = 0.146
risk_penalty_factor = 1.0 * 1.0 * 1.0 = 1.0
final_score = 0.146 * 1.0 = 0.146

# Exemplo 2: Com penalidade de drawdown
base_score = 0.146
risk_penalty_factor = 1.0 * 0.8 * 1.0 = 0.8
final_score = 0.146 * 0.8 = 0.117

# Exemplo 3: Com múltiplas penalidades
base_score = 0.146
risk_penalty_factor = 0.8 * 0.8 * 0.5 = 0.32
final_score = 0.146 * 0.32 = 0.047
```

---

## Etapa 6: Geração de Ranking

### Ordenação

Os ativos são ordenados por `final_score` em ordem **decrescente**:

```python
# Ordenar por score (maior primeiro)
ranking = sorted(scores, key=lambda x: x.final_score, reverse=True)

# Atribuir posições
for rank, score in enumerate(ranking, start=1):
    score.rank = rank
```

### Exemplo de Ranking

```python
Rank | Ticker    | Final Score | Momentum | Quality | Value
-----|-----------|-------------|----------|---------|-------
  1  | PRIO3.SA  |    0.848    |   0.92   |  0.85   |  0.78
  2  | BBSE3.SA  |    0.825    |   0.75   |  0.90   |  0.82
  3  | SBSP3.SA  |    0.569    |   0.45   |  0.70   |  0.55
  4  | PETR4.SA  |    0.146    |   0.29   |  0.40   | -0.30
  5  | VALE3.SA  |    0.089    |   0.15   |  0.25   | -0.10
 ...
 39  | ITUB4.SA  |   -0.234    |  -0.20   | -0.15   | -0.35
```

### Ativos Excluídos

Ativos que não passaram no filtro de elegibilidade:

```python
# Não aparecem no ranking principal
# Mas são salvos no banco com:
{
    "ticker": "AMER3.SA",
    "final_score": 0.0,
    "passed_eligibility": False,
    "exclusion_reasons": [
        "negative_net_income_last_year",
        "excessive_leverage_debt_to_ebitda_gt_8"
    ],
    "rank": null  # Sem posição no ranking
}
```

---

## Exemplos Práticos

### Exemplo 1: Petrobras (PETR4.SA) - Ativo Típico

#### Dados Brutos
```python
# Preços (últimos 12 meses)
preço_inicial = 30.00
preço_final = 38.90
volume_médio = 45_234_567

# Fundamentos
revenue = 450_000_000_000
net_income = 120_000_000_000
shareholders_equity = 400_000_000_000
total_debt = 200_000_000_000
ebitda = 180_000_000_000
```

#### Fatores Calculados (Brutos)
```python
# Momentum
return_12m = (38.90 / 30.00) - 1 = 0.297  # 29.7%
volatility_90d = 0.35  # 35% ao ano
recent_drawdown = -0.074  # -7.4%

# Fundamentalistas
roe = 120_000_000_000 / 400_000_000_000 = 0.30  # 30%
net_margin = 120_000_000_000 / 450_000_000_000 = 0.267  # 26.7%
debt_to_ebitda = 200_000_000_000 / 180_000_000_000 = 1.11
```

#### Fatores Normalizados (Z-Score)
```python
# Após normalização cross-sectional
return_12m_z = 1.20
volatility_90d_z = -0.50  # Invertido
recent_drawdown_z = 0.20  # Invertido
roe_z = 1.50
net_margin_z = 0.90
debt_to_ebitda_z = -0.80  # Invertido
```

#### Scores
```python
momentum_score = 0.29
quality_score = 0.40
value_score = -0.30

base_score = (0.40 * 0.29) + (0.30 * 0.40) + (0.30 * -0.30) = 0.146

# Sem penalidades de risco
risk_penalty_factor = 1.0
final_score = 0.146

# Rank: 4º lugar
```

---

### Exemplo 2: Americanas (AMER3.SA) - Ativo Excluído

#### Dados Brutos
```python
# Fundamentos
revenue = 50_000_000_000
net_income = -5_000_000_000  # PREJUÍZO
shareholders_equity = 10_000_000_000
total_debt = 30_000_000_000
ebitda = 2_000_000_000

# Histórico de lucro
net_income_history = [-3_000_000_000, -4_000_000_000, -5_000_000_000]
```

#### Filtro de Elegibilidade
```python
# Verificações
net_income_last_year < 0  # ✗ FALHA
negative_years = 3  # ✗ FALHA (3 de 3 anos)
debt_to_ebitda = 30_000_000_000 / 2_000_000_000 = 15  # ✗ FALHA (> 8)

# Resultado
passed_eligibility = False
exclusion_reasons = [
    "negative_net_income_last_year",
    "negative_net_income_2_of_3_years",
    "excessive_leverage_debt_to_ebitda_gt_8"
]
```

#### Score Final
```python
# Ativo excluído não recebe score calculado
final_score = 0.0
rank = null  # Não aparece no ranking
```

---

### Exemplo 3: PRIO (PRIO3.SA) - Melhor Ranqueado

#### Por que ficou em 1º lugar?

```python
# Scores por categoria
momentum_score = 0.92   # Excelente performance de preço
quality_score = 0.85    # Alta rentabilidade e baixa dívida
value_score = 0.78      # Múltiplos atrativos

# Score base
base_score = (0.40 * 0.92) + (0.30 * 0.85) + (0.30 * 0.78)
base_score = 0.368 + 0.255 + 0.234 = 0.857

# Sem penalidades
risk_penalty_factor = 1.0

# Score final
final_score = 0.857

# Rank: 1º lugar
```

---

### Exemplo 4: Itaú (ITUB4.SA) - Banco Bem Ranqueado

#### Por que bancos agora são melhor avaliados?

```python
# Dados Brutos (banco típico)
revenue = 80_000_000_000
net_income = 25_000_000_000
total_assets = 1_800_000_000_000
shareholders_equity = 180_000_000_000
ebitda = None  # Bancos não reportam EBITDA

# Detecção automática
is_financial = True  # Sem EBITDA, mas com revenue/equity válidos

# Fatores específicos para bancos
roe = 25_000_000_000 / 180_000_000_000 = 0.139  # 13.9% (dentro do cap 30%)
roa = 25_000_000_000 / 1_800_000_000_000 = 0.014  # 1.4%
pb_ratio = preço / book_value_per_share = 1.2  # P/VP baixo (bom para bancos)
pe_ratio = preço / eps = 8.5  # P/L atrativo

# Scoring específico para financeiras
quality_score = 0.65   # Usa ROE, estabilidade, eficiência
value_score = 0.45     # Usa apenas P/L e P/VP (remove EV/EBITDA)
momentum_score = 0.20  # Performance de preço moderada

# Score final
base_score = (0.40 * 0.20) + (0.30 * 0.65) + (0.30 * 0.45) = 0.41

# Sem penalidades (banco sólido)
final_score = 0.41

# Rank: Posição melhor que antes (ex: 15º vs 35º anteriormente)
```

#### Comparação: Antes vs Depois da Implementação

```python
# ANTES (scoring industrial aplicado incorretamente)
quality_score = -0.80  # Penalizado por não ter EV/EBITDA, Debt/EBITDA
value_score = -0.60    # Penalizado por não ter EV/EBITDA
final_score = -0.35    # Score muito baixo
rank = 35              # Posição ruim

# DEPOIS (scoring específico para bancos)
quality_score = 0.65   # Avalia ROE, eficiência, estabilidade
value_score = 0.45     # Avalia P/L e P/VP (métricas corretas)
final_score = 0.41     # Score justo
rank = 15              # Posição melhor
```

---

## Configurações e Pesos

### Pesos dos Scores (Configuráveis)

```python
# Arquivo: app/config.py ou .env

# Pesos padrão
MOMENTUM_WEIGHT = 0.40  # 40%
QUALITY_WEIGHT = 0.30   # 30%
VALUE_WEIGHT = 0.30     # 30%

# Total deve somar 1.0 (100%)
```

### Limites de Penalidades

```python
# Volatilidade
VOLATILITY_LIMIT = 0.40  # 40% ao ano

# Drawdown
DRAWDOWN_LIMIT = -0.30  # -30%

# Dívida
DEBT_EBITDA_LIMIT = 8.0  # 8x EBITDA

# Volume mínimo
MINIMUM_VOLUME = 100_000  # 100k ações/dia
```

### Percentis de Winsorização

```python
# Para ROE robusto
WINSORIZE_LOWER_PCT = 0.05  # 5º percentil
WINSORIZE_UPPER_PCT = 0.95  # 95º percentil

# Cap de ROE
MAX_ROE_CAP = 0.50  # 50%
```

---

## Resumo do Fluxo Completo

```
1. DADOS BRUTOS
   ├─ Preços: 400 dias de histórico
   └─ Fundamentos: 3-4 anos anuais

2. FILTRO DE ELEGIBILIDADE
   ├─ Verifica 7 critérios de saúde financeira
   └─ Separa: elegíveis vs excluídos

3. CÁLCULO DE FATORES (apenas elegíveis)
   ├─ 5 fatores de momentum
   └─ 7 fatores fundamentalistas

4. NORMALIZAÇÃO
   ├─ Z-score cross-sectional
   └─ Inversão de fatores (menor = melhor)

5. CÁLCULO DE SCORES
   ├─ Momentum (40%)
   ├─ Qualidade (30%)
   ├─ Valor (30%)
   ├─ Score Base = média ponderada
   ├─ Penalidades de Risco
   └─ Score Final = base × penalidades

6. RANKING
   ├─ Ordenar por score final (decrescente)
   ├─ Atribuir posições (1 = melhor)
   └─ Salvar no banco de dados
```

---

## Interpretação dos Scores

### Score Final

- **> 0.50**: Excelente - Top performers
- **0.20 a 0.50**: Bom - Acima da média
- **-0.20 a 0.20**: Neutro - Próximo da média
- **< -0.20**: Fraco - Abaixo da média

### Breakdown por Categoria

#### Momentum Score
- Indica performance recente de preço
- Positivo: Tendência de alta
- Negativo: Tendência de baixa

#### Quality Score
- Indica saúde financeira e rentabilidade
- Positivo: Empresa sólida
- Negativo: Empresa fraca

#### Value Score
- Indica se está barato ou caro
- Positivo: Múltiplos atrativos (barato)
- Negativo: Múltiplos elevados (caro)

---

## Perguntas Frequentes

### 1. Por que normalizar os fatores?

Fatores têm escalas diferentes (ex: ROE em %, P/L em múltiplos). A normalização permite compará-los de forma justa.

### 2. Por que alguns fatores são invertidos?

Para fatores onde "menor é melhor" (volatilidade, dívida, múltiplos de valuation), invertemos o z-score para que valores positivos sempre indiquem "melhor".

### 3. Como funciona a normalização cross-sectional?

Comparamos todos os ativos no mesmo período. Um ativo com ROE de 30% pode ter z-score positivo se a média do mercado for 20%, ou negativo se a média for 40%.

### 4. Por que usar média ponderada?

Permite ajustar a importância de cada categoria (momentum, qualidade, valor) conforme a estratégia desejada.

### 5. O que são as penalidades de risco?

Reduzem o score de ativos com alta volatilidade, grandes drawdowns ou sinais de distress financeiro, protegendo o investidor.

### 6. Por que ativos excluídos não recebem score?

Empresas em distress financeiro não são investimentos viáveis. Excluí-las antes do cálculo evita que apareçam no ranking.

### 7. Como interpretar um score negativo?

Score negativo significa que o ativo está abaixo da média do mercado em múltiplas dimensões. Não é necessariamente ruim, mas indica performance relativa inferior.

### 8. Os pesos podem ser alterados?

Sim! Os pesos são configuráveis via arquivo `.env`. Você pode ajustar para dar mais importância a momentum, qualidade ou valor.

### 9. Com que frequência o ranking é atualizado?

O pipeline pode ser executado diariamente. Fatores de momentum são recalculados diariamente, fatores fundamentalistas mensalmente.

### 10. Como validar se os cálculos estão corretos?

O sistema inclui testes de propriedade que validam:
- Normalização resulta em média ~0 e std ~1
- Scores estão no range esperado
- Ranking está ordenado corretamente
- Penalidades são aplicadas corretamente

---

## Referências Técnicas

### Arquivos de Código

- **Ingestão**: `app/ingestion/yahoo_client.py`, `app/ingestion/yahoo_finance_client.py`
- **Filtro**: `app/filters/eligibility_filter.py`
- **Fatores**: `app/factor_engine/fundamental_factors.py`, `app/factor_engine/momentum_factors.py`
- **Fatores Financeiros**: `app/factor_engine/financial_factors.py` (específico para bancos)
- **Normalização**: `app/factor_engine/normalizer.py`
- **Scoring**: `app/scoring/scoring_engine.py` (com detecção automática de setor)
- **Ranking**: `app/scoring/ranker.py`
- **Pipeline**: `scripts/run_pipeline.py`
- **Informações de Setor**: `app/ingestion/asset_info_service.py`

### Documentação Adicional

- `README.md`: Visão geral do sistema
- `COMO_USAR_ATIVOS_LIQUIDOS.md`: Busca automática de ativos
- `IMPLEMENTACAO_FATORES_SETOR_ESPECIFICO.md`: Detalhes da implementação por setor
- `ROBUSTNESS_IMPROVEMENTS_SUMMARY.md`: Melhorias de robustez
- `.kiro/specs/quant-stock-ranker/design.md`: Design detalhado

---

**Documento criado em**: 2024-02-20  
**Versão**: 1.0  
**Autor**: Sistema de Ranking Quantitativo
