# Scripts do Quant Stock Ranker

Este diretório contém scripts utilitários para manutenção e operação do sistema.

## 🚀 Scripts Principais

### Pipeline

#### `run_pipeline_docker.py`
Executa o pipeline principal de ingestão, cálculo de features e scoring.

```bash
# Modo teste (5 ativos)
python scripts/run_pipeline_docker.py --mode test

# Modo produção (50 ativos mais líquidos)
python scripts/run_pipeline_docker.py --mode liquid --limit 50

# Forçar execução FULL (buscar histórico completo)
python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full
```

#### `clear_and_run_full.py` ⚠️
Limpa TODOS os dados do banco e roda pipeline FULL do zero.

**ATENÇÃO**: Esta operação é DESTRUTIVA! Faça backup antes!

```bash
# Limpar e rodar com 10 ativos
python scripts/clear_and_run_full.py --mode liquid --limit 10

# Limpar e rodar com 50 ativos (produção)
python scripts/clear_and_run_full.py --mode liquid --limit 50

# Apenas limpar dados (sem rodar pipeline)
python scripts/clear_and_run_full.py --clear-only

# Sem confirmação (use com cuidado!)
python scripts/clear_and_run_full.py --mode liquid --limit 50 --no-confirm
```

#### `clear_and_run_full.sh`
Versão bash do script acima.

```bash
./scripts/clear_and_run_full.sh liquid 50
```

### Verificação e Diagnóstico

#### `check_latest_scores.py`
Verifica os scores mais recentes calculados.

```bash
python scripts/check_latest_scores.py
```

#### `check_data_dates.py`
Verifica as datas dos dados no banco.

```bash
python scripts/check_data_dates.py
```

#### `check_confidence_factors.py`
Verifica os confidence factors (v2.6.0).

```bash
python scripts/check_confidence_factors.py
```

#### `check_pipeline_history.py`
Mostra histórico de execuções do pipeline.

```bash
python scripts/check_pipeline_history.py
```

#### `validate_features.py`
Valida features calculadas.

```bash
python scripts/validate_features.py
```

### Migrations

#### `migrate_add_confidence_factors.py`
Adiciona colunas de confidence factors (v2.6.0).

```bash
python scripts/migrate_add_confidence_factors.py
```

#### `migrate_add_backtest_smoothing.py`
Adiciona colunas para backtest e smoothing.

```bash
python scripts/migrate_add_backtest_smoothing.py
```

### Testes

#### `test_adaptive_history.py`
Testa implementação de histórico adaptativo.

```bash
python scripts/test_adaptive_history.py
```

#### `test_missing_treatment.py`
Testa tratamento de missing values.

```bash
python scripts/test_missing_treatment.py
```

#### `test_quality_score.py`
Testa cálculo de quality score.

```bash
python scripts/test_quality_score.py
```

### Suavização Temporal

#### `apply_temporal_smoothing.py`
Aplica suavização exponencial aos scores para reduzir turnover do portfólio.

**Fórmula**: `final_score_smoothed = 0.7 * score_atual + 0.3 * score_anterior`

```bash
# Aplicar suavização à data de hoje
python scripts/apply_temporal_smoothing.py

# Aplicar a uma data específica
python scripts/apply_temporal_smoothing.py --date 2026-02-26

# Aplicar a TODAS as datas com scores
python scripts/apply_temporal_smoothing.py --all

# Customizar alpha (peso do score atual)
python scripts/apply_temporal_smoothing.py --alpha 0.8

# Customizar lookback (dias para buscar score anterior)
python scripts/apply_temporal_smoothing.py --lookback-days 60

# Docker - Aplicar a todas as datas
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all
```

**Parâmetros**:
- `--date`: Data específica (YYYY-MM-DD). Default: hoje
- `--alpha`: Peso do score atual (0-1). Default: 0.7
  - 0.5 = peso igual (50% atual, 50% anterior)
  - 0.7 = padrão (70% atual, 30% anterior)
  - 0.9 = mais reativo (90% atual, 10% anterior)
  - 1.0 = sem suavização (100% atual)
- `--lookback-days`: Dias para buscar score anterior. Default: 30
- `--all`: Processar todas as datas com scores

**Quando usar**:
- Após rodar o pipeline para suavizar scores recém-calculados
- Para reprocessamento histórico (use `--all`)
- Para ajustar estratégia testando diferentes valores de alpha

### Manutenção

#### `force_refresh_data.py`
Força refresh dos dados (re-ingestão).

```bash
python scripts/force_refresh_data.py
```

#### `recalculate_scores.py`
Recalcula scores sem re-ingerir dados.

```bash
python scripts/recalculate_scores.py
```

#### `init_db.py`
Inicializa o banco de dados (cria tabelas).

```bash
python scripts/init_db.py
```

## 🐳 Uso com Docker

Todos os scripts podem ser executados dentro do container:

```bash
# Executar script Python
docker exec quant-ranker-backend python scripts/NOME_DO_SCRIPT.py

# Executar script bash
docker exec quant-ranker-backend bash scripts/NOME_DO_SCRIPT.sh

# Modo interativo (para confirmações)
docker exec -it quant-ranker-backend python scripts/clear_and_run_full.py
```

## 📊 Fluxo Típico de Uso

### Primeira Execução (Setup Inicial)

```bash
# 1. Inicializar banco
docker exec quant-ranker-backend python scripts/init_db.py

# 2. Executar migration (v2.6.0)
docker exec quant-ranker-backend python scripts/migrate_add_confidence_factors.py

# 3. Executar migration (smoothing)
docker exec quant-ranker-backend python scripts/migrate_add_backtest_smoothing.py

# 4. Rodar pipeline FULL
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full

# 5. Aplicar suavização a todo histórico
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all

# 6. Verificar scores
docker exec quant-ranker-backend python scripts/check_latest_scores.py
```

### Execução Diária (Atualização)

```bash
# 1. Rodar pipeline incremental
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50

# 2. Aplicar suavização temporal
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py

# 3. Verificar scores
docker exec quant-ranker-backend python scripts/check_latest_scores.py
```

### Troubleshooting

```bash
# 1. Verificar datas dos dados
docker exec quant-ranker-backend python scripts/check_data_dates.py

# 2. Verificar confidence factors
docker exec quant-ranker-backend python scripts/check_confidence_factors.py

# 3. Validar features
docker exec quant-ranker-backend python scripts/validate_features.py

# 4. Se necessário, limpar e reprocessar
docker exec -it quant-ranker-backend python scripts/clear_and_run_full.py --mode liquid --limit 50
```

## ⚠️ Scripts Destrutivos

Estes scripts DELETAM dados. Use com cuidado!

- `clear_and_run_full.py` - Deleta TODOS os dados
- `clear_and_run_full.sh` - Versão bash do acima

**SEMPRE faça backup antes de usar scripts destrutivos!**

```bash
# Backup do banco
docker exec quant-ranker-db pg_dump -U postgres quant_ranker > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore do banco
cat backup_YYYYMMDD_HHMMSS.sql | docker exec -i quant-ranker-db psql -U postgres quant_ranker
```

## 📝 Logs

Todos os scripts geram logs. Para ver:

```bash
# Logs do container
docker logs quant-ranker-backend --tail 100

# Logs em tempo real
docker logs -f quant-ranker-backend

# Logs do pipeline
cat pipeline_docker.log
```

## 🔧 Desenvolvimento

Para adicionar novos scripts:

1. Criar arquivo `.py` ou `.sh` em `scripts/`
2. Adicionar shebang e docstring
3. Adicionar ao `.gitignore` se for temporário
4. Documentar neste README
5. Testar localmente antes de commit

## 📚 Documentação Relacionada

- [EC2_DEPLOY_V2.6.0.md](../deploy/EC2_DEPLOY_V2.6.0.md) - Procedimento de deploy
- [ADAPTIVE_HISTORY_IMPLEMENTATION.md](../ADAPTIVE_HISTORY_IMPLEMENTATION.md) - Histórico adaptativo
- [PIPELINE_ARCHITECTURE.md](../docs/PIPELINE_ARCHITECTURE.md) - Arquitetura do pipeline
- [GUIA_USO.md](../docs/GUIA_USO.md) - Guia de uso completo
