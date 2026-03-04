# Pipeline Automatizado de Backtest

Pipeline completo que executa todas as etapas necessárias para gerar e executar backtests automaticamente.

## O Que o Pipeline Faz

1. ✅ Verifica disponibilidade de dados históricos
2. ✅ Gera scores históricos faltantes (se necessário)
3. ✅ Limpa backtests antigos (opcional)
4. ✅ Executa múltiplos backtests com diferentes configurações
5. ✅ Gera resumo comparativo

## Uso Rápido

### Execução Padrão (Recomendado)

```bash
# Executa 3 backtests principais (2021-hoje)
docker exec quant-ranker-backend python scripts/run_backtest_pipeline.py \
  --generate-scores \
  --clear-old
```

Isso vai executar:
- Top 10 Equal Weight
- Top 15 Equal Weight  
- Top 10 Equal Weight com Smoothing

### Teste Rápido

```bash
# Apenas 1 backtest para testar
docker exec quant-ranker-backend python scripts/run_backtest_pipeline.py \
  --configs quick \
  --generate-scores
```

### Teste Completo

```bash
# Executa 5 backtests com diferentes configurações
docker exec quant-ranker-backend python scripts/run_backtest_pipeline.py \
  --configs full \
  --generate-scores \
  --clear-old
```

Isso vai executar:
- Top 10 Equal Weight
- Top 10 Score Weighted
- Top 10 com Smoothing
- Top 15 Equal Weight
- Top 20 Equal Weight

## Parâmetros

### Período

```bash
# Período específico
docker exec quant-ranker-backend python scripts/run_backtest_pipeline.py \
  --start 2022-01-01 \
  --end 2024-12-31 \
  --generate-scores

# Período padrão: 2021-01-01 até ontem
docker exec quant-ranker-backend python scripts/run_backtest_pipeline.py \
  --generate-scores
```

### Configurações

```bash
# Quick: 1 backtest (teste rápido)
--configs quick

# Default: 3 backtests principais (recomendado)
--configs default

# Full: 5 backtests completos (análise detalhada)
--configs full
```

### Opções

```bash
# Gerar scores históricos faltantes
--generate-scores

# Forçar regeneração de TODOS os scores
--force-scores

# Limpar backtests antigos antes de executar
--clear-old
```

## Exemplos Práticos

### 1. Primeira Execução (Setup Inicial)

```bash
# Gera todos os scores e executa backtests
docker exec quant-ranker-backend python scripts/run_backtest_pipeline.py \
  --start 2021-01-01 \
  --generate-scores \
  --configs default
```

### 2. Atualização Mensal

```bash
# Atualiza scores do último mês e reexecuta backtests
docker exec quant-ranker-backend python scripts/run_backtest_pipeline.py \
  --generate-scores \
  --clear-old \
  --configs default
```

### 3. Análise de Período Específico

```bash
# Backtest apenas 2023-2024
docker exec quant-ranker-backend python scripts/run_backtest_pipeline.py \
  --start 2023-01-01 \
  --end 2024-12-31 \
  --generate-scores \
  --configs full
```

### 4. Regenerar Tudo do Zero

```bash
# Limpa e regenera tudo
docker exec quant-ranker-backend python scripts/run_backtest_pipeline.py \
  --force-scores \
  --clear-old \
  --configs full
```

## Fluxo de Execução

```
┌─────────────────────────────────────────┐
│ 1. Verificação de Dados                 │
│    - Preços históricos                  │
│    - Scores existentes                  │
│    - Cobertura temporal                 │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 2. Geração de Scores (se necessário)    │
│    - Identifica datas faltantes         │
│    - Calcula scores point-in-time       │
│    - Salva em scores_daily              │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 3. Limpeza (opcional)                   │
│    - Remove backtests antigos           │
│    - Evita duplicação                   │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 4. Execução de Backtests                │
│    - Top 10 Equal Weight                │
│    - Top 15 Equal Weight                │
│    - Top 10 Smoothed                    │
│    - (+ outros conforme --configs)      │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ 5. Resumo e Resultados                  │
│    - Métricas de cada backtest          │
│    - Taxa de sucesso                    │
│    - Próximos passos                    │
└─────────────────────────────────────────┘
```

## Tempo de Execução

- **Quick** (1 backtest): ~2-3 minutos
- **Default** (3 backtests): ~5-8 minutos
- **Full** (5 backtests): ~10-15 minutos

*Tempo inclui geração de scores se necessário*

## Verificar Resultados

### Via CLI

```bash
# Listar backtests salvos
docker exec quant-ranker-backend python scripts/clear_backtest_data.py --action list

# Ver últimos scores
docker exec quant-ranker-backend python scripts/check_latest_scores.py
```

### Via Interface

Acesse a página **Research - Backtest** no Streamlit para:
- Visualizar equity curves
- Comparar métricas
- Analisar composição dos portfólios
- Ver drawdowns

## Automatização com Cron

Para executar backtests automaticamente todo mês:

```bash
# Editar crontab
crontab -e

# Adicionar linha (executa dia 1 de cada mês às 2:00)
0 2 1 * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_backtest_pipeline.py --generate-scores --clear-old --configs default >> ~/backtest_pipeline.log 2>&1
```

## Troubleshooting

### Erro: "Sem dados de preços históricos"

```bash
# Ingerir dados históricos primeiro
docker exec quant-ranker-backend python scripts/ingest_prices_sequential.py
```

### Erro: "duplicate key violates unique constraint"

```bash
# Limpar backtests antigos
docker exec quant-ranker-backend python scripts/clear_backtest_data.py --action clear-all

# Executar novamente
docker exec quant-ranker-backend python scripts/run_backtest_pipeline.py --generate-scores
```

### Cobertura de scores baixa

```bash
# Forçar regeneração de todos os scores
docker exec quant-ranker-backend python scripts/run_backtest_pipeline.py \
  --force-scores \
  --configs quick
```

### Backtest muito lento

```bash
# Usar período menor
docker exec quant-ranker-backend python scripts/run_backtest_pipeline.py \
  --start 2023-01-01 \
  --configs quick
```

## Configurações Disponíveis

### Quick (1 backtest)
- Top 10 Equal Weight

### Default (3 backtests)
- Top 10 Equal Weight
- Top 15 Equal Weight
- Top 10 Equal Weight + Smoothing

### Full (5 backtests)
- Top 10 Equal Weight
- Top 10 Score Weighted
- Top 10 Equal Weight + Smoothing
- Top 15 Equal Weight
- Top 20 Equal Weight

## Métricas Calculadas

Cada backtest calcula:
- **CAGR**: Retorno anualizado composto
- **Sharpe Ratio**: Retorno ajustado ao risco
- **Max Drawdown**: Maior queda do pico
- **Volatilidade**: Desvio padrão anualizado
- **Turnover**: Rotatividade média do portfólio
- **Total Return**: Retorno acumulado

## Próximos Passos

Após executar o pipeline:

1. ✅ Visualizar resultados no Streamlit
2. ✅ Comparar métricas entre configurações
3. ✅ Identificar melhor configuração (Sharpe, Drawdown)
4. ✅ Ajustar parâmetros se necessário
5. ✅ Automatizar execução mensal via cron

## Documentação Relacionada

- `BACKTEST_QUICKSTART.md` - Guia básico de backtest
- `CRON_QUICKSTART.md` - Automatização do pipeline diário
- `deploy/CRON_SETUP.md` - Configuração detalhada de cron
- `docs/BACKTEST_SMOOTHING.md` - Suavização temporal

## Comandos Úteis

```bash
# Ver log do pipeline
tail -50 ~/backtest_pipeline.log

# Limpar todos os backtests
docker exec quant-ranker-backend python scripts/clear_backtest_data.py --action clear-all

# Verificar cobertura de dados
docker exec quant-ranker-backend python scripts/check_historical_coverage.py

# Testar um backtest individual
docker exec quant-ranker-backend python scripts/run_backtest.py \
  --start 2021-01-01 --end 2024-12-31 \
  --top-n 10 --weight-method equal \
  --name "test_backtest"
```
