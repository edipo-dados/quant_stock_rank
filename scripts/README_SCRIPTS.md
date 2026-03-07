# Scripts do Quant Stock Ranker

Documentação completa de todos os scripts disponíveis no sistema.

## 🚀 Scripts Principais (Produção)

### Pipeline Completo

#### `run_smart_pipeline.py`
**Uso**: Pipeline completo de ingestão e cálculo de scores

```bash
# EC2
docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py

# Local
python scripts/run_smart_pipeline.py
```

**O que faz**:
1. Atualiza lista de ações líquidas
2. Ingere preços diários (últimos 30 dias)
3. Ingere fundamentalistas (FMP API)
4. Calcula fatores quantitativos
5. Gera ranking atual
6. Salva no banco de dados

**Quando usar**: Atualização diária (cron 19h)

---

### Backtest

#### `run_optimized_backtest.py`
**Uso**: Executa backtest com configurações otimizadas

```bash
docker exec -it quant-ranker-backend python scripts/run_optimized_backtest.py
```

**Configurações**:
- Score-weighted portfolio (máx 25% por ativo)
- Market regime filter (MA200)
- Temporal smoothing (0.7 + 0.3)
- Rebalanceamento mensal
- Top 10 ações

**Saída**: Métricas de performance completas

#### `run_backtest_pipeline.py`
**Uso**: Pipeline de backtest com opções avançadas

```bash
docker exec -it quant-ranker-backend python scripts/run_backtest_pipeline.py \
  --start 2022-01-01 \
  --end 2026-03-01 \
  --generate-scores \
  --configs full
```

**Opções**:
- `--start`: Data inicial
- `--end`: Data final
- `--generate-scores`: Gerar snapshots históricos
- `--force-scores`: Forçar recálculo
- `--clear-old`: Limpar dados antigos
- `--configs`: Configurações (default, full, quick)

#### `compare_strategies.py`
**Uso**: Compara diferentes estratégias

```bash
docker exec -it quant-ranker-backend python scripts/compare_strategies.py
```

**Compara**:
- Equal weight vs Score-weighted
- Com/sem market regime filter
- Com/sem temporal smoothing

---

### Ingestão de Dados

#### `ingest_benchmark.py`
**Uso**: Ingere dados do IBOVESPA (benchmark)

```bash
docker exec -it quant-ranker-backend python scripts/ingest_benchmark.py
```

**Período**: Últimos 3 anos (ajustável)

**Necessário para**: Cálculo de Alpha, Beta, Information Ratio

#### `ingest_full_history.py`
**Uso**: Ingere histórico completo de preços

```bash
docker exec -it quant-ranker-backend python scripts/ingest_full_history.py \
  --start 2020-01-01 \
  --end 2026-03-01
```

**Quando usar**: Setup inicial ou expansão histórica

#### `ingest_prices_sequential.py`
**Uso**: Ingere preços sequencialmente (evita rate limits)

```bash
docker exec -it quant-ranker-backend python scripts/ingest_prices_sequential.py \
  --start 2022-01-01 \
  --end 2026-03-01 \
  --delay 2
```

**Opções**:
- `--delay`: Segundos entre requests (padrão: 1)

---

### Geração de Snapshots

#### `generate_historical_scores.py`
**Uso**: Gera snapshots históricos de ranking

```bash
docker exec -it quant-ranker-backend python scripts/generate_historical_scores.py \
  --start 2022-01-01 \
  --end 2026-03-01 \
  --frequency monthly
```

**Opções**:
- `--frequency`: daily, weekly, monthly (padrão: monthly)

**Necessário para**: Backtest funcionar

#### `calculate_historical_scores.py`
**Uso**: Calcula scores para datas específicas

```bash
docker exec -it quant-ranker-backend python scripts/calculate_historical_scores.py \
  --date 2025-01-01
```

---

### Atualização de Dados

#### `update_liquid_stocks.py`
**Uso**: Atualiza lista de ações líquidas

```bash
docker exec -it quant-ranker-backend python scripts/update_liquid_stocks.py
```

**O que faz**:
1. Busca componentes do Ibovespa (yfinance)
2. Adiciona ações da lista B3
3. Garante ITUB3 está incluído
4. Atualiza tabela AssetInfo

**Quando usar**: Mensal ou quando mudar composição do Ibovespa

#### `recalculate_scores.py`
**Uso**: Recalcula scores de todos os ativos

```bash
docker exec -it quant-ranker-backend python scripts/recalculate_scores.py
```

**Quando usar**: Após mudança de pesos ou fórmulas

---

## 🔍 Scripts de Verificação

### Dados

#### `check_historical_coverage.py`
**Uso**: Verifica cobertura de dados históricos

```bash
docker exec -it quant-ranker-backend python scripts/check_historical_coverage.py
```

**Mostra**:
- Período de dados disponíveis
- Gaps de dados
- Cobertura por ticker

#### `check_backtest_data.py`
**Uso**: Valida dados para backtest

```bash
docker exec -it quant-ranker-backend python scripts/check_backtest_data.py
```

**Verifica**:
- Snapshots de ranking
- Preços disponíveis
- Benchmark disponível
- Consistência de datas

#### `check_latest_scores.py`
**Uso**: Verifica scores mais recentes

```bash
docker exec -it quant-ranker-backend python scripts/check_latest_scores.py
```

**Mostra**:
- Top 10 ações
- Scores por fator
- Data do último cálculo

#### `check_db.py`
**Uso**: Verifica estado geral do banco

```bash
docker exec -it quant-ranker-backend python scripts/check_db.py
```

**Mostra**:
- Contagem de registros por tabela
- Período de dados
- Últimas atualizações

---

### Validação

#### `validate_backtest_data.py`
**Uso**: Valida integridade dos dados de backtest

```bash
docker exec -it quant-ranker-backend python scripts/validate_backtest_data.py
```

**Verifica**:
- Scores normalizados (0-1)
- Tickers sem sufixo .SA
- Datas não futuras
- Preços disponíveis

#### `validate_features.py`
**Uso**: Valida cálculo de features

```bash
docker exec -it quant-ranker-backend python scripts/validate_features.py
```

**Verifica**:
- Momentum calculado corretamente
- Value factors válidos
- Quality factors válidos
- Risk factors válidos

---

## 🧹 Scripts de Manutenção

### Limpeza

#### `clear_backtest_data.py`
**Uso**: Limpa dados de backtest

```bash
docker exec -it quant-ranker-backend python scripts/clear_backtest_data.py \
  --action clear-all
```

**Opções**:
- `--action list`: Lista backtests salvos
- `--action clear-all`: Limpa todos os dados
- `--action clear-name --name "nome"`: Limpa backtest específico

#### `clear_and_run_full.py`
**Uso**: Limpa tudo e executa pipeline completo

```bash
docker exec -it quant-ranker-backend python scripts/clear_and_run_full.py
```

**⚠️ CUIDADO**: Remove todos os dados e recalcula do zero

---

### Migrações

#### `migrate_add_benchmark.py`
**Uso**: Adiciona tabela de benchmark

```bash
docker exec -it quant-ranker-backend python scripts/migrate_add_benchmark.py
```

#### `migrate_add_backtest_tables.py`
**Uso**: Adiciona tabelas de backtest

```bash
docker exec -it quant-ranker-backend python scripts/migrate_add_backtest_tables.py
```

#### `migrate_add_confidence_factors.py`
**Uso**: Adiciona colunas de confiança

```bash
docker exec -it quant-ranker-backend python scripts/migrate_add_confidence_factors.py
```

---

## 🔧 Scripts Utilitários

### Inicialização

#### `init_db.py`
**Uso**: Inicializa banco de dados

```bash
docker exec -it quant-ranker-backend python scripts/init_db.py
```

**O que faz**:
- Cria todas as tabelas
- Aplica índices
- Configura constraints

#### `pre_deploy_check.py`
**Uso**: Verifica sistema antes de deploy

```bash
docker exec -it quant-ranker-backend python scripts/pre_deploy_check.py
```

**Verifica**:
- Variáveis de ambiente
- Conexão com banco
- APIs disponíveis
- Dependências instaladas

---

### Aplicação de Features

#### `apply_temporal_smoothing.py`
**Uso**: Aplica smoothing aos scores existentes

```bash
docker exec -it quant-ranker-backend python scripts/apply_temporal_smoothing.py
```

#### `apply_adaptive_history.py`
**Uso**: Aplica adaptive history aos scores

```bash
docker exec -it quant-ranker-backend python scripts/apply_adaptive_history.py
```

---

## 📊 Scripts de Análise

### Verificação de Features

#### `check_confidence_factors.py`
**Uso**: Verifica fatores de confiança

```bash
docker exec -it quant-ranker-backend python scripts/check_confidence_factors.py
```

#### `check_new_features.py`
**Uso**: Verifica novas features implementadas

```bash
docker exec -it quant-ranker-backend python scripts/check_new_features.py
```

#### `check_pipeline_history.py`
**Uso**: Verifica histórico de execuções do pipeline

```bash
docker exec -it quant-ranker-backend python scripts/check_pipeline_history.py
```

---

## 🐳 Scripts Docker

### `docker_entrypoint.sh`
**Uso**: Entrypoint do container backend

**O que faz**:
- Inicializa banco
- Inicia API FastAPI

### `docker_init.sh`
**Uso**: Inicialização do container

**O que faz**:
- Verifica dependências
- Configura ambiente

---

## 📅 Automação (Cron)

### Atualização Diária

```bash
# Adicionar ao crontab
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

---

## 🔗 Fluxos Comuns

### Setup Inicial

```bash
# 1. Inicializar banco
python scripts/init_db.py

# 2. Atualizar lista de ações
python scripts/update_liquid_stocks.py

# 3. Ingerir histórico completo
python scripts/ingest_full_history.py --start 2020-01-01 --end 2026-03-01

# 4. Ingerir benchmark
python scripts/ingest_benchmark.py

# 5. Executar pipeline
python scripts/run_smart_pipeline.py
```

### Preparar Backtest

```bash
# 1. Verificar dados
python scripts/check_backtest_data.py

# 2. Gerar snapshots históricos
python scripts/generate_historical_scores.py \
  --start 2022-01-01 --end 2026-03-01 --frequency monthly

# 3. Executar backtest
python scripts/run_optimized_backtest.py
```

### Atualização Diária

```bash
# Executar pipeline completo
python scripts/run_smart_pipeline.py
```

---

**Última atualização**: Março 2026  
**Versão**: 2.6.0
