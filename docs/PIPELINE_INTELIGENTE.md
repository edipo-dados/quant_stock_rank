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

### Opção 1: Scripts Batch (Recomendado)

#### Pipeline Automático (Detecção Inteligente)
```bash
pipeline-auto.bat
```
Detecta automaticamente se deve fazer FULL ou INCREMENTAL.

#### Pipeline Incremental
```bash
pipeline-incremental.bat
```
Força modo incremental (mas faz FULL se necessário).

#### Pipeline Full
```bash
pipeline-full.bat
```
Força modo FULL sempre.

### Opção 2: Linha de Comando

#### Modo Automático (Recomendado)
```bash
# Teste (5 ativos)
docker-compose exec backend python scripts/run_pipeline_smart.py --mode test

# Top 50 líquidos
docker-compose exec backend python scripts/run_pipeline_smart.py --mode liquid --limit 50

# Tickers customizados
docker-compose exec backend python scripts/run_pipeline_smart.py --mode manual --tickers PETR4.SA VALE3.SA ITUB4.SA
```

#### Forçar FULL
```bash
docker-compose exec backend python scripts/run_pipeline_smart.py --mode test --force-full
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
docker-compose exec backend python scripts/check_pipeline_history.py
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
  Tickers: 50
  Período: 2026-02-21 a 2026-02-22

ID    Data/Hora            Tipo         Modo       Status     Tickers  Duração
--------------------------------------------------------------------------------
15    22/02/2026 14:30     INCREMENTAL  liquid     SUCCESS    50       5.2min
14    21/02/2026 18:45     INCREMENTAL  liquid     SUCCESS    50       4.8min
13    20/02/2026 19:00     FULL         liquid     SUCCESS    50       18.3min
...
```

### Ver Detalhes de uma Execução Específica
```bash
docker-compose exec backend python scripts/check_pipeline_history.py --id 15
```

Saída:
```
================================================================================
EXECUÇÃO #15
================================================================================

Data/Hora: 22/02/2026 14:30:15
Tipo: INCREMENTAL
Modo: liquid
Status: SUCCESS
Duração: 5.2min
Período: 2026-02-21 a 2026-02-22

Estatísticas:
  Tickers processados: 50
  Tickers sucesso: 48
  Tickers falha: 2
  Preços ingeridos: 150
  Fundamentos ingeridos: 0
  Features calculadas: 48
  Scores calculados: 48

Tickers (50):
  PETR4.SA, VALE3.SA, ITUB4.SA, BBDC4.SA, ABEV3.SA, ...

Configuração:
  momentum_weight: 0.4
  quality_weight: 0.3
  value_weight: 0.3
  sleep_between_tickers: 2
  sleep_between_batches: 5
  batch_size: 5

Erros (2):
  1. MGLU3.SA - prices: No data
  2. AMER3.SA - fundamentals: API timeout
```

### Ver Última Execução
```bash
docker-compose exec backend python scripts/check_pipeline_history.py --last
```

### Ver Última Execução Bem-Sucedida
```bash
docker-compose exec backend python scripts/check_pipeline_history.py --last-success
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

Edite `scripts/run_pipeline_smart.py`:

```python
# Configurações de detecção de modo
FULL_THRESHOLD_DAYS = 7  # Se dados > 7 dias, executa FULL
INCREMENTAL_LOOKBACK_DAYS = 7  # Busca últimos 7 dias no incremental
FULL_LOOKBACK_DAYS = 400  # Busca 400 dias no full
```

### Ajustar Rate Limiting

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
# Agendar para 19h (após fechamento)
pipeline-auto.bat
```

**Comportamento:**
- Segunda execução: FULL (400 dias)
- Terça a Sexta: INCREMENTAL (apenas novos dados)
- Segunda seguinte: INCREMENTAL (se executou na sexta)

### Primeira Execução

```bash
pipeline-full.bat
```

Busca todo o histórico necessário (400 dias).

### Reprocessar Tudo

```bash
pipeline-full.bat
```

Força reprocessamento completo, útil quando:
- Mudou configuração de pesos
- Corrigiu bug no cálculo
- Quer garantir consistência

### Atualização Rápida

```bash
pipeline-incremental.bat
```

Atualiza apenas dados novos, útil para:
- Múltiplas atualizações no mesmo dia
- Testes rápidos
- Verificar novos dados

## Monitoramento

### Logs

Logs são salvos em:
- Console (stdout)
- Arquivo: `pipeline_smart.log`

```bash
# Ver logs em tempo real
docker-compose exec backend tail -f pipeline_smart.log

# Ver últimas 100 linhas
docker-compose exec backend tail -n 100 pipeline_smart.log
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

**Solução**: Aumente delays em `run_pipeline_smart.py`:
```python
SLEEP_BETWEEN_TICKERS = 5  # Aumentar de 2 para 5
SLEEP_BETWEEN_BATCHES = 10 # Aumentar de 5 para 10
```

### Dados duplicados

**Causa**: Execução FULL sobrescreveu dados incrementais.

**Solução**: O sistema já trata isso com UPSERT (INSERT ou UPDATE).

## Migração do Pipeline Antigo

### Passo 1: Criar Nova Tabela

```bash
docker-compose exec backend python scripts/init_db.py
```

### Passo 2: Executar Primeira Carga

```bash
pipeline-full.bat
```

### Passo 3: Usar Pipeline Inteligente

A partir de agora, use:
```bash
pipeline-auto.bat  # Diariamente
```

## Comparação com Pipeline Antigo

| Característica | Pipeline Antigo | Pipeline Inteligente |
|----------------|-----------------|---------------------|
| Detecção de modo | Manual | Automática |
| Rastreamento | Não | Sim (banco de dados) |
| Histórico | Não | Sim (completo) |
| Estatísticas | Logs apenas | Banco + Logs |
| Incremental | Não | Sim |
| Otimização | Não | Sim (apenas novos dados) |
| Tempo (50 ativos) | 20 min sempre | 20 min (FULL) / 5 min (INC) |

## Próximos Passos

1. Execute primeira carga FULL
2. Configure execução diária automática
3. Monitore histórico regularmente
4. Ajuste thresholds conforme necessário

## Referências

- [Guia de Uso](GUIA_USO.md)
- [Cálculos de Ranking](CALCULOS_RANKING.md)
- [Estrutura de Dados](../ESTRUTURA_DADOS_E_CALCULOS_RANKING.md)
