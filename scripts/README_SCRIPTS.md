# Scripts - Guia de Referência

## Pipelines Principais

| Script | Descrição | Quando usar |
|--------|-----------|-------------|
| `clear_and_run_full.py` | Pipeline FULL (limpa banco e roda do zero) | Primeira execução, reset |
| `run_pipeline_docker.py` | Pipeline incremental (atualiza dados) | Atualização diária |
| `run_smart_pipeline.py` | Pipeline inteligente (decide FULL ou INCREMENTAL) | CRON automático |
| `run_backtest_pipeline.py` | Pipeline de backtest completo | Após pipeline de dados |
| `run_enhanced_backtest.py` | Backtest com melhorias v2.7.0 | Testar volatility targeting |

## Ordem de Execução

```
1. clear_and_run_full.py     (primeira vez)
   OU run_pipeline_docker.py (atualizações)
   OU run_smart_pipeline.py  (automático)

2. generate_historical_scores.py  (antes do primeiro backtest)

3. run_backtest_pipeline.py       (backtest padrão)
   OU run_enhanced_backtest.py    (backtest v2.7.0)
```

## Scripts de Dados

| Script | Descrição |
|--------|-----------|
| `ingest_prices_sequential.py` | Ingestão sequencial de preços |
| `ingest_full_history.py` | Ingestão de histórico completo |
| `ingest_benchmark.py` | Ingestão de dados do IBOVESPA |
| `generate_historical_scores.py` | Gera scores para datas passadas |
| `calculate_historical_scores.py` | Calcula scores históricos |
| `update_liquid_stocks.py` | Atualiza lista de ações líquidas B3 |
| `apply_temporal_smoothing.py` | Aplica suavização temporal nos scores |
| `apply_adaptive_history.py` | Aplica histórico adaptativo |
| `recalculate_scores.py` | Recalcula scores existentes |
| `force_refresh_data.py` | Força atualização de dados |

## Scripts de Verificação

| Script | Descrição |
|--------|-----------|
| `check_latest_scores.py` | Mostra scores mais recentes |
| `check_historical_coverage.py` | Verifica cobertura de dados históricos |
| `check_backtest_data.py` | Verifica dados de backtest |
| `check_confidence_factors.py` | Verifica fatores de confiança |
| `check_data_dates.py` | Verifica datas dos dados |
| `check_db.py` | Verifica estado do banco |
| `check_eligibility_filters.py` | Verifica filtros de elegibilidade |
| `check_new_features.py` | Verifica novas features |
| `check_pipeline_history.py` | Verifica histórico de execuções |
| `check_today_scores.py` | Verifica scores de hoje |
| `validate_backtest_data.py` | Valida dados de backtest |
| `validate_features.py` | Valida features calculadas |

## Scripts de Manutenção

| Script | Descrição |
|--------|-----------|
| `clear_backtest_data.py` | Limpa dados de backtest |
| `clear_and_run_full.sh` | Shell script para pipeline full |
| `cleanup_ec2_disk.sh` | Limpa disco do EC2 |
| `setup_ec2_swap.sh` | Configura swap no EC2 |
| `pre_deploy_check.py` | Verificação pré-deploy |
| `init_db.py` | Inicializa banco de dados |

## Scripts de Backtest

| Script | Descrição |
|--------|-----------|
| `run_backtest.py` | Executa backtest simples |
| `run_backtest_pipeline.py` | Pipeline completo de backtest |
| `run_enhanced_backtest.py` | Backtest com melhorias v2.7.0 |
| `run_optimized_backtest.py` | Backtest otimizado |
| `compare_strategies.py` | Compara diferentes estratégias |

## Scripts Docker

| Script | Descrição |
|--------|-----------|
| `docker_entrypoint.sh` | Entrypoint do container |
| `docker_init.sh` | Inicialização do container |
| `run_research_app.sh` | Inicia app de research |

## Uso com Docker

Todos os scripts devem ser executados dentro do container:

```bash
docker exec -it quant-ranker-backend python scripts/<nome_do_script>.py
```
