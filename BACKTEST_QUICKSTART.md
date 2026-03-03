# Backtest - Guia Rápido

## Visão Geral

Para executar backtests, você precisa primeiro gerar scores históricos point-in-time e depois executar o backtest.

## Pré-requisitos

- Dados históricos de preços e fundamentos já ingeridos (via `scripts/ingest_prices_sequential.py`)
- Mínimo de 5 anos de dados para backtest robusto

## Passo 1: Gerar Scores Históricos

Os scores históricos são calculados usando apenas dados disponíveis até cada data (point-in-time), evitando look-ahead bias.

### Teste Rápido (uma data)

```bash
docker exec quant-ranker-backend python scripts/test_historical_scores.py
```

### Gerar Scores Completos

```bash
# Gerar scores mensais de 2021 a 2024
docker exec quant-ranker-backend python scripts/calculate_historical_scores.py \
  --start 2021-01-01 \
  --end 2024-12-31 \
  --frequency monthly
```

Parâmetros:
- `--start`: Data inicial (YYYY-MM-DD)
- `--end`: Data final (YYYY-MM-DD)
- `--frequency`: Frequência (apenas 'monthly' suportado)

O script:
- Gera datas mensais (último dia de cada mês)
- Para cada data, calcula features e scores usando apenas dados até aquela data
- Salva scores na tabela `scores_daily`
- Pula datas que já têm scores calculados

### Verificar Scores Gerados

```bash
docker exec quant-ranker-backend python scripts/check_latest_scores.py
```

## Passo 2: Executar Backtest

Após gerar os scores históricos, execute o backtest:

```bash
# Backtest básico (Top 10, equal weight)
docker exec quant-ranker-backend python scripts/run_backtest.py \
  --start 2021-01-01 \
  --end 2024-12-31 \
  --top-n 10 \
  --weight-method equal \
  --name "backtest_top10_equal"
```

Parâmetros:
- `--start`: Data inicial do backtest
- `--end`: Data final do backtest
- `--top-n`: Número de ativos a selecionar (default: 10)
- `--weight-method`: Método de ponderação ('equal' ou 'score_weighted')
- `--use-smoothing`: Flag para usar scores suavizados
- `--name`: Nome do backtest (para salvar resultados)

### Exemplos de Backtests

```bash
# Top 10 com equal weight
docker exec quant-ranker-backend python scripts/run_backtest.py \
  --start 2021-01-01 --end 2024-12-31 \
  --top-n 10 --weight-method equal \
  --name "top10_equal"

# Top 20 com score weighted
docker exec quant-ranker-backend python scripts/run_backtest.py \
  --start 2021-01-01 --end 2024-12-31 \
  --top-n 20 --weight-method score_weighted \
  --name "top20_weighted"

# Top 10 com suavização temporal
docker exec quant-ranker-backend python scripts/run_backtest.py \
  --start 2021-01-01 --end 2024-12-31 \
  --top-n 10 --weight-method equal \
  --use-smoothing \
  --name "top10_smoothed"
```

## Métricas Calculadas

O backtest calcula:
- **Retorno Total**: Retorno acumulado do período
- **CAGR**: Compound Annual Growth Rate
- **Volatilidade**: Volatilidade anualizada dos retornos
- **Sharpe Ratio**: Retorno ajustado ao risco
- **Max Drawdown**: Maior queda do pico ao vale
- **Turnover Médio**: Rotatividade média por rebalanceamento
- **Número de Rebalanceamentos**: Total de rebalanceamentos mensais
- **Número de Trades**: Total de trades executados

## Resultados

Os resultados são salvos em:
- Tabela `backtest_results` no banco de dados
- Logs detalhados no console

## Troubleshooting

### Erro: "No scores found for snapshot date"

Você precisa gerar scores históricos primeiro:
```bash
docker exec quant-ranker-backend python scripts/calculate_historical_scores.py \
  --start 2021-01-01 --end 2024-12-31
```

### Erro: "Insufficient price data"

Verifique se tem dados históricos suficientes:
```bash
docker exec quant-ranker-backend python scripts/check_historical_coverage.py
```

### Performance Lenta

- O cálculo de scores históricos pode levar tempo (5-10 min para 4 anos)
- Use `--start` e `--end` para processar períodos menores
- Scores já calculados são pulados automaticamente

## Arquitetura

```
1. Dados Brutos (raw_prices_daily, raw_fundamentals)
   ↓
2. Cálculo de Scores Históricos (calculate_historical_scores.py)
   - Busca dados até data alvo
   - Calcula features (momentum, fundamentais)
   - Normaliza cross-sectional
   - Calcula scores
   - Salva em scores_daily
   ↓
3. Backtest Engine (run_backtest.py)
   - Cria snapshots mensais (ranking_history)
   - Para cada mês:
     * Seleciona Top N
     * Calcula pesos
     * Busca retornos do mês seguinte
     * Calcula retorno do portfólio
   - Calcula métricas
   - Salva em backtest_results
```

## Próximos Passos

1. Gerar scores históricos para o período desejado
2. Executar backtests com diferentes parâmetros
3. Comparar resultados na interface Streamlit (página Research - Backtest)
4. Ajustar pesos e parâmetros conforme necessário
