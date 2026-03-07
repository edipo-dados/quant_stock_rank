# Regras e Configurações do Sistema

Documentação completa das regras de negócio, configurações e parâmetros do sistema de ranking quantitativo.

## 📊 Modelo Multifator

### Pesos dos Fatores (Otimizados)

```python
# app/config.py
momentum_weight: float = 0.5   # 50% - Maior prêmio histórico
value_weight: float = 0.25     # 25% - Prêmio moderado
quality_weight: float = 0.15   # 15% - Reduz risco
risk_weight: float = 0.10      # 10% - Penalização
size_weight: float = 0.0       # 0% - Desabilitado
```

### Justificativa dos Pesos

1. **Momentum (50%)**: Literatura acadêmica mostra que momentum é o fator com maior prêmio no mercado brasileiro
2. **Value (25%)**: Complementa momentum, captura reversão de longo prazo
3. **Quality (15%)**: Melhora Sharpe Ratio, reduz risco de falências
4. **Risk (10%)**: Penaliza volatilidade excessiva, protege capital

## 🎯 Fatores Quantitativos

### 1. Momentum (50%)

**Cálculo**: Média ponderada de retornos passados

```python
# Retornos com skip de 1 mês (evita reversão de curto prazo)
momentum_12m = (preço_atual / preço_13m_atrás) - 1  # Peso: 50%
momentum_6m = (preço_atual / preço_7m_atrás) - 1    # Peso: 30%
momentum_3m = (preço_atual / preço_4m_atrás) - 1    # Peso: 20%

momentum_score = 0.5 * mom_12m + 0.3 * mom_6m + 0.2 * mom_3m
```

**Normalização**: Min-Max (0-1)

**Tratamento de Missing**:
- Se faltam dados: score = 0.5 (neutro)
- Penalidade de confiança aplicada

### 2. Value (25%)

**Métricas**:
- P/E Ratio (Price-to-Earnings)
- P/B Ratio (Price-to-Book)
- EV/EBITDA (Enterprise Value to EBITDA)
- Dividend Yield

**Cálculo**:
```python
# Inverter para que menor = melhor
value_pe = 1 / PE_ratio
value_pb = 1 / PB_ratio
value_ev_ebitda = 1 / EV_EBITDA
value_dy = Dividend_Yield  # Já é melhor quando maior

value_score = média(value_pe, value_pb, value_ev_ebitda, value_dy)
```

**Normalização**: Min-Max (0-1)

**Limites**:
- P/E < 0 ou > 100: excluir
- P/B < 0 ou > 20: excluir
- EV/EBITDA < 0 ou > 50: excluir

### 3. Quality (15%)

**Métricas**:
- ROE (Return on Equity)
- ROA (Return on Assets)
- Debt/EBITDA
- Margem Líquida

**Cálculo**:
```python
# ROE com cap em 50%
quality_roe = min(ROE, 0.50)

# ROA normalizado
quality_roa = ROA

# Debt/EBITDA invertido (menor = melhor)
quality_debt = 1 / (1 + Debt_EBITDA) if Debt_EBITDA < 4 else 0

# Margem líquida
quality_margin = Net_Margin

quality_score = média(quality_roe, quality_roa, quality_debt, quality_margin)
```

**Normalização**: Min-Max (0-1)

**Limites**:
- ROE: cap em 50% (evita outliers)
- Debt/EBITDA > 4: penalização severa
- Margem < 0: score = 0

### 4. Risk (10%)

**Métricas**:
- Volatilidade anualizada (252 dias)
- Maximum Drawdown (252 dias)

**Cálculo**:
```python
# Penalização (menor risco = maior score)
risk_volatility = 1 - min(volatility / volatility_limit, 1.0)
risk_drawdown = 1 - min(abs(max_dd) / abs(drawdown_limit), 1.0)

risk_score = 0.5 * risk_volatility + 0.5 * risk_drawdown
```

**Normalização**: Já normalizado (0-1)

**Limites**:
- Volatilidade > 60%: penalização máxima
- Drawdown < -50%: penalização máxima

## 🔍 Filtros de Elegibilidade

### Filtro de Liquidez

```python
minimum_volume: float = 5_000_000  # R$ 5 milhões/dia
```

**Cálculo**: Média móvel de 20 dias do volume financeiro

**Justificativa**: Garante execução eficiente, reduz impacto de mercado

### Filtro de Market Cap

```python
minimum_market_cap: float = 1_000_000_000  # R$ 1 bilhão
```

**Cálculo**: Preço × Shares Outstanding

**Justificativa**: Evita micro-caps com alta volatilidade

### Universo de Ações

**Fontes**:
1. Componentes do Ibovespa (dinâmico via yfinance)
2. Lista B3 de ações líquidas (fallback)

**Atualização**: Mensal via `scripts/update_liquid_stocks.py`

**Prioridade**: ITUB3 sempre incluído (top holding histórico)

## 🎨 Normalização e Winsorização

### Normalização Min-Max

```python
score_normalized = (score - min_score) / (max_score - min_score)
```

**Aplicação**: Todos os fatores (momentum, value, quality, risk)

**Vantagem**: Scores entre 0-1, fácil interpretação

### Winsorização

```python
winsorize_lower_pct: float = 0.05  # 5º percentil
winsorize_upper_pct: float = 0.95  # 95º percentil
```

**Aplicação**: Antes da normalização

**Justificativa**: Remove outliers extremos que distorcem distribuição

## 🔄 Temporal Smoothing

### Fórmula

```python
score_smoothed = 0.7 * score_atual + 0.3 * score_anterior
```

**Aplicação**: Score final após agregação de fatores

**Benefícios**:
- Reduz ruído de curto prazo
- Diminui turnover (~19%)
- Melhora estabilidade do ranking

**Implementação**: `app/scoring/temporal_smoothing.py`

## 📈 Score-Weighted Portfolio

### Cálculo de Pesos

```python
# Normalizar scores para soma = 1
peso_i = score_i / soma(scores)

# Aplicar limite máximo
peso_i = min(peso_i, 0.25)  # Máx 25% por ativo

# Renormalizar
pesos_finais = pesos / soma(pesos)
```

**Vantagens**:
- Maior exposição a ativos com melhores scores
- Reduz concentração (máx 25%)
- Melhora Sharpe Ratio vs equal weight

## 🌡️ Market Regime Filter

### Detecção de Regime

```python
regime_ma_period: int = 200  # MA200 do IBOVESPA

if IBOV_close > IBOV_MA200:
    regime = "bullish"
    exposure = 1.0  # 100%
else:
    regime = "bearish"
    exposure = 0.5  # 50%
```

**Aplicação**: Ajusta exposição do portfólio

**Benefícios**:
- Protege capital em mercados baixistas
- Reduz drawdown máximo
- Melhora Calmar Ratio

**Implementação**: `app/backtest/market_regime.py`

## 🔄 Rebalanceamento

### Frequência

```python
rebalance_frequency: str = 'monthly'  # Mensal
```

**Datas**: Primeiro dia útil de cada mês

**Processo**:
1. Calcular scores de todos os ativos elegíveis
2. Aplicar temporal smoothing
3. Selecionar top N (padrão: 10)
4. Calcular pesos (score-weighted)
5. Executar trades necessários

**Turnover Médio**: ~19% (baixo)

## 📊 Métricas de Performance

### Cálculo de Retornos

```python
# Retorno mensal do portfólio
portfolio_return = soma(peso_i * retorno_i)

# CAGR
CAGR = (valor_final / valor_inicial)^(1/anos) - 1

# Volatilidade anualizada
volatility = std(retornos_mensais) * sqrt(12)
```

### Métricas Ajustadas ao Risco

```python
# Sharpe Ratio
sharpe = (retorno_anual - risk_free) / volatilidade

# Sortino Ratio (penaliza apenas downside)
sortino = (retorno_anual - risk_free) / downside_deviation

# Calmar Ratio
calmar = CAGR / abs(max_drawdown)
```

### Métricas vs Benchmark

```python
# Beta (sensibilidade ao mercado)
beta = cov(retornos_estrategia, retornos_benchmark) / var(retornos_benchmark)

# Alpha (retorno excedente ajustado)
alpha = retorno_estrategia - (risk_free + beta * (retorno_benchmark - risk_free))

# Information Ratio
IR = (retorno_estrategia - retorno_benchmark) / tracking_error
```

### Validações de Métricas

```python
# Alpha: -50% a +50% (valores fora indicam erro)
alpha = max(-0.5, min(0.5, alpha))

# Beta: -3 a +3 (típico: 0.5 a 1.5)
beta = max(-3.0, min(3.0, beta))

# Information Ratio: -3 a +3 (típico: -1 a 1)
IR = max(-3.0, min(3.0, IR))
```

## 🗄️ Banco de Dados

### Tabelas Principais

1. **AssetInfo**: Informações dos ativos
2. **RawPriceDaily**: Preços diários
3. **RawFundamentals**: Dados fundamentalistas
4. **RankingHistory**: Snapshots de ranking
5. **BenchmarkPrice**: Preços do IBOVESPA

### Convenções

- **Tickers**: SEM sufixo .SA (ex: ITUB3, não ITUB3.SA)
- **Datas**: Formato date (YYYY-MM-DD)
- **Scores**: Float entre 0-1
- **Retornos**: Float decimal (0.05 = 5%)

### Integridade

- Unique constraints em (ticker, date)
- Índices em date para queries rápidas
- Foreign keys desabilitadas (SQLite)

## 🔧 Configurações de Produção

### Variáveis de Ambiente (.env)

```bash
# API Keys
FMP_API_KEY=your_key_here

# Database
DATABASE_URL=sqlite:///./quant_ranker.db

# API
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
FRONTEND_PORT=8501
BACKEND_URL=http://localhost:8000

# Logging
LOG_LEVEL=INFO
```

### Docker

```yaml
# docker-compose.yml
services:
  backend:
    container_name: quant-ranker-backend
    ports:
      - "8000:8000"
    volumes:
      - ./quant_ranker.db:/app/quant_ranker.db
  
  frontend:
    container_name: quant-ranker-frontend
    ports:
      - "8501:8501"
```

## 📅 Automação (Cron)

### Atualização Diária

```bash
# Executar às 19h (após fechamento da B3)
0 19 * * 1-5 cd /home/ubuntu/quant_stock_rank && \
  docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py \
  >> /var/log/quant_ranker.log 2>&1
```

### Backup Semanal

```bash
# Domingo às 2h
0 2 * * 0 cd /home/ubuntu/quant_stock_rank && \
  ./deploy/backup-db.sh \
  >> /var/log/quant_backup.log 2>&1
```

## 🚨 Limites e Alertas

### Limites de Qualidade

```python
max_roe_limit: float = 0.50        # Cap ROE em 50%
debt_ebitda_limit: float = 4.0     # Penalizar Debt/EBITDA > 4
```

### Limites de Risco

```python
volatility_limit: float = 0.60     # 60% anualizado
drawdown_limit: float = -0.50      # -50%
```

### Alertas de Métricas

- Alpha > 50% ou < -50%: Revisar cálculo
- Beta > 3 ou < -3: Revisar cálculo
- Volatilidade > 100%: Verificar dados
- Drawdown < -80%: Revisar estratégia

## 📚 Referências

### Literatura Acadêmica

1. **Momentum**: Jegadeesh & Titman (1993)
2. **Value**: Fama & French (1992)
3. **Quality**: Asness, Frazzini & Pedersen (2019)
4. **Low Volatility**: Ang, Hodrick, Xing & Zhang (2006)

### Implementação

- **Normalização**: Min-Max scaling
- **Winsorização**: 5º e 95º percentis
- **Temporal Smoothing**: EWMA com α=0.7
- **Market Regime**: MA200 (Faber, 2007)

---

**Última atualização**: Março 2026  
**Versão**: 2.6.0  
**Status**: ✅ Produção
