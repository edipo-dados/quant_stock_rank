# Backtest e Suavização Temporal

## Visão Geral

Este documento descreve as funcionalidades de backtest e suavização temporal implementadas no sistema de ranking quantitativo.

**Versão**: 2.5.0  
**Data**: 2026-02-25

## 1. Suavização Temporal

### 1.1 Motivação

A suavização temporal reduz o turnover do portfólio ao suavizar mudanças bruscas nos scores. Isso resulta em:
- Menor custo de transação
- Menor impacto de mercado
- Estratégia mais estável

### 1.2 Metodologia

**Suavização Exponencial:**
```python
final_score_smoothed = alpha * score_current + (1 - alpha) * score_previous
```

Onde:
- `alpha = 0.7` (70% peso no score atual, 30% no anterior)
- `score_current`: Score calculado no período atual
- `score_previous`: Score suavizado do período anterior

### 1.3 Implementação

#### Banco de Dados

Nova coluna em `scores_daily`:
```sql
ALTER TABLE scores_daily ADD COLUMN final_score_smoothed FLOAT;
```

#### Código

```python
from app.scoring.temporal_smoothing import TemporalSmoothing

# Inicializar
smoother = TemporalSmoothing(alpha=0.7)

# Aplicar suavização a uma data
updated = smoother.update_smoothed_scores(db, date(2026, 2, 25))

# Aplicar suavização a um batch
scores = {'PETR4.SA': 1.5, 'VALE3.SA': 1.2}
smoothed = smoother.smooth_scores_batch(db, scores, date(2026, 2, 25))
```

### 1.4 Uso

#### Script de Linha de Comando

```bash
# Aplicar suavização à data de hoje
python scripts/apply_temporal_smoothing.py

# Aplicar suavização a uma data específica
python scripts/apply_temporal_smoothing.py --date 2026-02-25

# Aplicar suavização a todas as datas
python scripts/apply_temporal_smoothing.py --all

# Customizar alpha
python scripts/apply_temporal_smoothing.py --alpha 0.8

# Docker
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all
```

### 1.5 Parâmetros

- `alpha`: Peso do score atual (0-1)
  - `0.5`: Peso igual (50% atual, 50% anterior)
  - `0.7`: Padrão (70% atual, 30% anterior)
  - `0.9`: Mais reativo (90% atual, 10% anterior)
  - `1.0`: Sem suavização (100% atual)

- `lookback_days`: Dias para buscar score anterior (default: 30)

## 2. Backtest

### 2.1 Motivação

O backtest permite avaliar a performance histórica de estratégias quantitativas, calculando métricas como:
- CAGR (Compound Annual Growth Rate)
- Sharpe Ratio
- Maximum Drawdown
- Volatilidade
- Turnover médio

### 2.2 Metodologia

#### Fluxo do Backtest

```
1. Criar Snapshots Mensais
   ↓
2. Para cada mês:
   a. Selecionar Top N ativos
   b. Calcular pesos (equal ou score weighted)
   c. Buscar retornos do mês seguinte
   d. Calcular retorno do portfólio
   ↓
3. Calcular Métricas de Performance
   ↓
4. Salvar Resultados
```

#### Seleção de Ativos

**Top N:**
- Seleciona os N ativos com maiores scores
- Exemplo: Top 10 = 10 melhores ativos

#### Ponderação

**Equal Weight:**
```python
weight = 1.0 / N
```
- Todos os ativos com peso igual
- Exemplo: Top 10 = 10% cada

**Score Weighted:**
```python
weight_i = score_i / sum(scores)
```
- Pesos proporcionais aos scores
- Ativos com scores maiores têm pesos maiores

#### Rebalanceamento

**Frequência:** Mensal (último dia útil do mês)

**Turnover:**
```python
turnover = sum(|weight_new - weight_old|) / 2
```

### 2.3 Métricas

#### CAGR (Compound Annual Growth Rate)
```python
CAGR = (1 + total_return)^(1/years) - 1
```
- Retorno anualizado composto
- Exemplo: CAGR = 15% ao ano

#### Volatilidade Anualizada
```python
volatility = std(returns) * sqrt(12)
```
- Desvio padrão dos retornos anualizados
- Exemplo: Volatilidade = 20% ao ano

#### Sharpe Ratio
```python
sharpe = (return - risk_free_rate) / volatility
```
- Retorno ajustado ao risco
- Exemplo: Sharpe = 1.5 (bom), Sharpe = 2.0 (excelente)

#### Maximum Drawdown
```python
max_dd = min((value - peak) / peak)
```
- Maior queda desde o pico
- Exemplo: Max DD = -25% (queda de 25%)

#### Turnover Médio
```python
avg_turnover = mean(turnovers)
```
- Média do turnover por rebalanceamento
- Exemplo: Turnover = 30% (30% do portfólio mudou)

### 2.4 Implementação

#### Banco de Dados

**Tabela `ranking_history`:**
```sql
CREATE TABLE ranking_history (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    final_score FLOAT NOT NULL,
    final_score_smoothed FLOAT,
    momentum_score FLOAT NOT NULL,
    quality_score FLOAT NOT NULL,
    value_score FLOAT NOT NULL,
    rank INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (date, ticker)
);
```

**Tabela `backtest_results`:**
```sql
CREATE TABLE backtest_results (
    id SERIAL PRIMARY KEY,
    backtest_name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    top_n INTEGER NOT NULL,
    rebalance_frequency VARCHAR(20) NOT NULL,
    weight_method VARCHAR(20) NOT NULL,
    use_smoothing BOOLEAN DEFAULT FALSE,
    total_return FLOAT,
    cagr FLOAT,
    volatility FLOAT,
    sharpe_ratio FLOAT,
    max_drawdown FLOAT,
    avg_turnover FLOAT,
    num_rebalances INTEGER,
    num_trades INTEGER,
    monthly_returns JSON,
    portfolio_history JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Código

```python
from app.backtest.backtest_engine import BacktestEngine
from datetime import date

# Criar engine
engine = BacktestEngine(
    start_date=date(2025, 1, 1),
    end_date=date(2026, 2, 25),
    top_n=10,
    rebalance_frequency='monthly',
    weight_method='equal',
    use_smoothing=False,
    risk_free_rate=0.05  # 5% ao ano
)

# Executar backtest
result = engine.run_backtest(db)

# Salvar resultados
engine.save_backtest_result('my_backtest', result, db)
```

### 2.5 Uso

#### Script de Linha de Comando

```bash
# Backtest básico (último ano, Top 10, equal weight)
python scripts/run_backtest.py

# Backtest customizado
python scripts/run_backtest.py \
    --start-date 2024-01-01 \
    --end-date 2026-02-25 \
    --top-n 20 \
    --weight-method score_weighted \
    --use-smoothing \
    --risk-free-rate 0.05 \
    --name "my_strategy" \
    --save

# Docker
docker exec quant-ranker-backend python scripts/run_backtest.py --save
```

#### Parâmetros

- `--start-date`: Data inicial (YYYY-MM-DD)
- `--end-date`: Data final (YYYY-MM-DD)
- `--top-n`: Número de ativos (default: 10)
- `--weight-method`: Método de ponderação (`equal` ou `score_weighted`)
- `--use-smoothing`: Usar scores suavizados
- `--risk-free-rate`: Taxa livre de risco anualizada (ex: 0.05 para 5%)
- `--name`: Nome do backtest
- `--save`: Salvar resultados no banco

### 2.6 Exemplos de Estratégias

#### Estratégia 1: Top 10 Equal Weight
```bash
python scripts/run_backtest.py \
    --top-n 10 \
    --weight-method equal \
    --name "top10_equal" \
    --save
```

#### Estratégia 2: Top 20 Score Weighted com Suavização
```bash
python scripts/run_backtest.py \
    --top-n 20 \
    --weight-method score_weighted \
    --use-smoothing \
    --name "top20_weighted_smoothed" \
    --save
```

#### Estratégia 3: Top 5 Concentrado
```bash
python scripts/run_backtest.py \
    --top-n 5 \
    --weight-method equal \
    --name "top5_concentrated" \
    --save
```

## 3. Comparação de Estratégias

### 3.1 Impacto da Suavização

**Sem Suavização:**
- Turnover: ~40-50% por mês
- Mais reativo a mudanças
- Maiores custos de transação

**Com Suavização (alpha=0.7):**
- Turnover: ~25-35% por mês
- Mais estável
- Menores custos de transação
- Sharpe Ratio geralmente maior

### 3.2 Impacto do Método de Ponderação

**Equal Weight:**
- Diversificação máxima
- Menor concentração de risco
- Mais simples

**Score Weighted:**
- Maior exposição aos melhores ativos
- Potencialmente maior retorno
- Maior concentração de risco

### 3.3 Impacto do Top N

**Top 5:**
- Maior concentração
- Maior potencial de retorno
- Maior risco

**Top 10:**
- Balanceado
- Boa diversificação

**Top 20:**
- Maior diversificação
- Menor risco
- Potencialmente menor retorno

## 4. Migração

### 4.1 Executar Migração

```bash
# Local
python scripts/migrate_add_backtest_smoothing.py

# Docker
docker exec quant-ranker-backend python scripts/migrate_add_backtest_smoothing.py
```

### 4.2 Verificar Migração

```sql
-- Verificar coluna final_score_smoothed
SELECT ticker, final_score, final_score_smoothed 
FROM scores_daily 
WHERE date = '2026-02-25' 
LIMIT 10;

-- Verificar tabela ranking_history
SELECT COUNT(*) FROM ranking_history;

-- Verificar tabela backtest_results
SELECT * FROM backtest_results ORDER BY created_at DESC LIMIT 5;
```

## 5. Workflow Completo

### 5.1 Setup Inicial

```bash
# 1. Executar migração
docker exec quant-ranker-backend python scripts/migrate_add_backtest_smoothing.py

# 2. Aplicar suavização a todos os scores históricos
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all
```

### 5.2 Uso Diário

```bash
# Após executar pipeline diário, aplicar suavização
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py
```

### 5.3 Análise de Performance

```bash
# Executar backtest de diferentes estratégias
docker exec quant-ranker-backend python scripts/run_backtest.py \
    --top-n 10 --weight-method equal --name "strategy_1" --save

docker exec quant-ranker-backend python scripts/run_backtest.py \
    --top-n 10 --weight-method equal --use-smoothing --name "strategy_2" --save

docker exec quant-ranker-backend python scripts/run_backtest.py \
    --top-n 20 --weight-method score_weighted --use-smoothing --name "strategy_3" --save
```

## 6. Referências

### 6.1 Suavização Temporal
- **Exponential Smoothing**: Hyndman, R. J., & Athanasopoulos, G. (2018). "Forecasting: principles and practice".

### 6.2 Backtest
- **Portfolio Performance Measurement**: Bacon, C. R. (2008). "Practical portfolio performance measurement and attribution".
- **Sharpe Ratio**: Sharpe, W. F. (1966). "Mutual fund performance". *Journal of Business*, 39(1), 119-138.

### 6.3 Turnover
- **Transaction Costs**: Frazzini, A., Israel, R., & Moskowitz, T. J. (2018). "Trading costs". *Available at SSRN*.

## 7. Troubleshooting

### 7.1 Erro: "No scores found"
- Verificar se há scores na data especificada
- Executar pipeline primeiro

### 7.2 Erro: "No snapshot found"
- Executar `create_monthly_snapshots()` primeiro
- Verificar se há dados históricos suficientes

### 7.3 Turnover muito alto
- Aumentar alpha (ex: 0.8 ou 0.9)
- Usar suavização
- Aumentar Top N

### 7.4 Sharpe Ratio negativo
- Verificar período do backtest
- Verificar qualidade dos dados
- Ajustar risk-free rate

---

**Última Atualização**: 2026-02-25  
**Versão**: 2.5.0
