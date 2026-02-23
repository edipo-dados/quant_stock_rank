# Pipeline Inteligente - Documentação

## Visão Geral

O Pipeline Inteligente é um sistema automatizado que detecta automaticamente se deve executar uma carga FULL (completa) ou INCREMENTAL (apenas novos dados), baseado no histórico de execuções anteriores.

## Características

- ✅ **Detecção Automática**: Identifica automaticamente o melhor modo de execução
- ✅ **Rastreamento de Execuções**: Grava todas as execuções no banco de dados
- ✅ **Controle de Carga**: Sabe exatamente quando foi a última carga
- ✅ **Rate Limiting**: Proteção contra bloqueio de APIs
- ✅ **Retry Automático**: Tenta novamente em caso de falha
- ✅ **Logs Detalhados**: Histórico completo de cada execução
- ✅ **Estatísticas**: Métricas de cada etapa do pipeline

## Modos de Execução

### FULL (Carga Completa)

Executado automaticamente quando:
- É a primeira execução (sem histórico)
- Última execução foi há mais de 7 dias
- Usuário força com `--force-full`

**O que faz:**
- Busca 400 dias de histórico de preços
- Busca todos os fundamentos disponíveis
- Recalcula todas as features
- Recalcula todos os scores

**Tempo estimado:**
- 5 ativos: ~2 minutos
- 50 ativos: ~20 minutos
- 100 ativos: ~40 minutos

### INCREMENTAL (Atualização)

Executado automaticamente quando:
- Há execução anterior bem-sucedida
- Última execução foi há menos de 7 dias

**O que faz:**
- Busca apenas preços novos (desde última execução até hoje)
- Busca fundamentos apenas para tickers sem dados
- Recalcula features apenas para dados novos
- Recalcula scores

**Tempo estimado:**
- 5 ativos: ~30 segundos
- 50 ativos: ~5 minutos
- 100 ativos: ~10 minutos

## Como Usar

### Comando Principal

O pipeline agora usa um único script Docker otimizado:

```bash
# Modo automático (detecta FULL ou INCREMENTAL)
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 200"

# Forçar modo FULL
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 200 --force-full"

# Modo teste (5 ativos)
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode test"
```

### Scripts Batch Windows (Atalhos)

Para facilitar no Windows, use os scripts batch:

```bash
# Executar pipeline com detecção automática
docker-pipeline.bat

# Iniciar todos os containers
docker-start.bat

# Parar todos os containers
docker-stop.bat
```

## Tabela de Controle

### pipeline_executions

Armazena informações sobre cada execução do pipeline:

```sql
CREATE TABLE pipeline_executions (
    id INTEGER PRIMARY KEY,
    execution_date DATETIME NOT NULL,
    execution_type VARCHAR(20) NOT NULL,  -- 'FULL' ou 'INCREMENTAL'
    mode VARCHAR(20) NOT NULL,            -- 'test', 'liquid', 'manual'
    status VARCHAR(20) NOT NULL,          -- 'RUNNING', 'SUCCESS', 'FAILED'
    started_at DATETIME NOT NULL,
    completed_at DATETIME,
    
    -- Estatísticas
    tickers_processed INTEGER,
    tickers_success INTEGER,
    tickers_failed INTEGER,
    prices_ingested INTEGER,
    fundamentals_ingested INTEGER,
    features_calculated INTEGER,
    scores_calculated INTEGER,
    
    -- Período de dados
    data_start_date DATE,
    data_end_date DATE,
    
    -- Metadados
    tickers_list JSON,
    error_log JSON,
    config_snapshot JSON
);
```

## Consultar Histórico

### Ver Resumo de Todas as Execuções
```bash
docker exec quant-ranker-backend bash -c "cd /app && python scripts/check_pipeline_history.py"
```

Saída:
```
================================================================================
HISTÓRICO DE EXECUÇÕES DO PIPELINE
================================================================================

Total de execuções: 15
  Sucesso: 13
  Falha: 2
  Em execução: 0

Última execução bem-sucedida:
  Data: 22/02/2026 14:30:15
  Tipo: INCREMENTAL
  Tickers: 63
  Período: 2026-02-21 a 2026-02-22

ID    Data/Hora            Tipo         Modo       Status     Tickers  Duração
--------------------------------------------------------------------------------
15    22/02/2026 14:30     INCREMENTAL  liquid     SUCCESS    63       5.2min
14    21/02/2026 18:45     INCREMENTAL  liquid     SUCCESS    63       4.8min
13    20/02/2026 19:00     FULL         liquid     SUCCESS    63       30.3min
...
```

### Ver Detalhes de uma Execução Específica
```bash
docker exec quant-ranker-backend bash -c "cd /app && python scripts/check_pipeline_history.py --id 15"
```

### Ver Última Execução
```bash
docker exec quant-ranker-backend bash -c "cd /app && python scripts/check_pipeline_history.py --last"
```

### Ver Última Execução Bem-Sucedida
```bash
docker exec quant-ranker-backend bash -c "cd /app && python scripts/check_pipeline_history.py --last-success"
```

## Lógica de Detecção

### Fluxograma

```
Início
  ↓
Forçar FULL? ──Sim──→ FULL
  ↓ Não
Existe execução anterior? ──Não──→ FULL
  ↓ Sim
Última execução > 7 dias? ──Sim──→ FULL
  ↓ Não
INCREMENTAL
```

### Código

```python
def determine_execution_type(db: Session, force_full: bool = False):
    # 1. Forçar FULL
    if force_full:
        return 'FULL', start_date, end_date
    
    # 2. Verificar última execução
    last_execution = get_last_successful_execution(db)
    if not last_execution:
        return 'FULL', start_date, end_date
    
    # 3. Verificar idade dos dados
    days_since_last = (date.today() - last_execution.data_end_date).days
    if days_since_last > FULL_THRESHOLD_DAYS:
        return 'FULL', start_date, end_date
    
    # 4. Incremental
    start_date = last_execution.data_end_date + timedelta(days=1)
    return 'INCREMENTAL', start_date, end_date
```

## Configurações

### Ajustar Thresholds

Edite `scripts/run_pipeline_docker.py`:

```python
# Configurações de detecção de modo
# Função: check_if_full_run_needed()
# Se dados > 7 dias, executa FULL
# Se dados <= 7 dias, executa INCREMENTAL

# Lookback days
lookback_days = 400  # FULL: busca 400 dias
lookback_days = 7    # INCREMENTAL: busca 7 dias
```

### Ajustar Rate Limiting

Edite `scripts/run_pipeline_docker.py`:

```python
# Configurações de rate limiting
SLEEP_BETWEEN_TICKERS = 2  # segundos entre cada ticker
SLEEP_BETWEEN_BATCHES = 5  # segundos entre batches
BATCH_SIZE = 5  # número de tickers por batch
MAX_RETRIES = 3  # tentativas máximas por ticker
```

## Casos de Uso

### Uso Diário (Recomendado)

Execute o pipeline automático todos os dias após o fechamento do mercado:

```bash
docker-pipeline.bat
```

Ou diretamente:

```bash
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 200"
```

**Comportamento:**
- Primeira execução: FULL (400 dias)
- Execuções seguintes (≤7 dias): INCREMENTAL (apenas novos dados)
- Após 7+ dias sem executar: FULL novamente

### Primeira Execução

```bash
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 200 --force-full"
```

Busca todo o histórico necessário (400 dias).

### Reprocessar Tudo

```bash
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 200 --force-full"
```

Força reprocessamento completo, útil quando:
- Mudou configuração de pesos
- Corrigiu bug no cálculo
- Quer garantir consistência

### Atualização Rápida (Teste)

```bash
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode test"
```

Testa com apenas 5 ativos, útil para:
- Verificar se pipeline está funcionando
- Testar mudanças no código
- Debug rápido

## Monitoramento

### Logs

Logs são salvos em:
- Console (stdout)
- Arquivo: `pipeline_docker.log` (dentro do container)

```bash
# Ver logs em tempo real
docker logs quant-ranker-backend -f

# Ver últimas 100 linhas
docker logs quant-ranker-backend --tail 100

# Ver logs do arquivo dentro do container
docker exec quant-ranker-backend bash -c "tail -f /app/pipeline_docker.log"
```

### Métricas

Cada execução registra:
- Tickers processados/sucesso/falha
- Registros ingeridos (preços/fundamentos)
- Features calculadas
- Scores calculados
- Duração total
- Erros detalhados

### Alertas

Monitore execuções com falha:

```sql
SELECT * FROM pipeline_executions 
WHERE status = 'FAILED' 
ORDER BY execution_date DESC;
```

## Troubleshooting

### Pipeline sempre executa FULL

**Causa**: Última execução não foi bem-sucedida ou dados muito antigos.

**Solução**:
1. Verifique histórico: `check_pipeline_history.py`
2. Verifique se última execução foi SUCCESS
3. Verifique se data_end_date está correta

### Execução fica em RUNNING

**Causa**: Pipeline travou ou foi interrompido.

**Solução**:
```sql
UPDATE pipeline_executions 
SET status = 'FAILED', completed_at = NOW() 
WHERE status = 'RUNNING';
```

### Muitos erros de API

**Causa**: Rate limiting insuficiente.

**Solução**: Aumente delays em `run_pipeline_docker.py`:
```python
SLEEP_BETWEEN_TICKERS = 5  # Aumentar de 2 para 5
SLEEP_BETWEEN_BATCHES = 10 # Aumentar de 5 para 10
```

Depois reconstrua o container:
```bash
docker-compose build backend
docker restart quant-ranker-backend
```

### Dados duplicados

**Causa**: Execução FULL sobrescreveu dados incrementais.

**Solução**: O sistema já trata isso com UPSERT (INSERT ou UPDATE).

## Migração do Pipeline Antigo

Se você estava usando scripts antigos, agora use apenas:

### Passo 1: Iniciar Containers

```bash
docker-start.bat
# ou
docker-compose up -d
```

### Passo 2: Executar Primeira Carga

```bash
docker-pipeline.bat
# ou
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 200 --force-full"
```

### Passo 3: Usar Pipeline Diariamente

A partir de agora, use:
```bash
docker-pipeline.bat  # Diariamente
```

O sistema detecta automaticamente se precisa FULL ou INCREMENTAL.

## Comparação com Pipeline Antigo

| Característica | Pipeline Antigo | Pipeline Atual (Docker) |
|----------------|-----------------|-------------------------|
| Detecção de modo | Manual | Automática |
| Rastreamento | Não | Sim (banco de dados) |
| Histórico | Não | Sim (completo) |
| Estatísticas | Logs apenas | Banco + Logs |
| Incremental | Não | Sim |
| Otimização | Não | Sim (apenas novos dados) |
| Tempo (63 ativos) | 30 min sempre | 30 min (FULL) / 5-10 min (INC) |
| Rate Limiting | Básico | Avançado (batch + retry) |
| Conversão Tipos | Não | Sim (NumPy → Python) |
| Tratamento Erros | Básico | Completo (None/NaN) |

## Próximos Passos

1. Execute primeira carga FULL
2. Configure execução diária automática
3. Monitore histórico regularmente
4. Ajuste thresholds conforme necessário

## Referências

- [Guia de Uso](GUIA_USO.md)
- [Cálculos de Ranking](CALCULOS_RANKING.md)
- [Estrutura de Dados](../ESTRUTURA_DADOS_E_CALCULOS_RANKING.md)
