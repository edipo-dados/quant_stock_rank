# Pipeline Inteligente - Decisão Automática FULL vs INCREMENTAL

Pipeline que analisa o estado do banco de dados e decide automaticamente entre execução FULL ou INCREMENTAL.

## Como Funciona

### 1. Análise Automática

O pipeline verifica:
- ✅ Última execução do pipeline
- ✅ Última data de preços no banco
- ✅ Última data de scores
- ✅ Quantidade de registros
- ✅ Número de tickers únicos

### 2. Decisão Inteligente

**Executa FULL se:**
- Banco de dados vazio
- Primeira execução
- Última execução há mais de 7 dias
- Últimos preços há mais de 7 dias  
- Menos de 50 tickers no banco

**Executa INCREMENTAL se:**
- Dados atualizados (última execução <7 dias)
- Preços recentes (<7 dias)
- Mais de 50 tickers disponíveis

### 3. Execução Automática

**FULL:**
1. Limpa dados antigos
2. Ingere histórico completo
3. Calcula todas as features
4. Calcula todos os scores
5. Aplica suavização temporal

**INCREMENTAL:**
1. Atualiza apenas dados novos
2. Calcula features incrementais
3. Calcula scores do dia
4. Aplica suavização temporal

## Uso Básico

### Execução Automática (Recomendado)

```bash
# Pipeline decide automaticamente
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py
```

### Ver Análise Sem Executar

```bash
# Dry-run: mostra o que seria executado
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --dry-run
```

Exemplo de output:
```
================================================================================
ANÁLISE DO BANCO DE DADOS
================================================================================
Última execução: 2024-03-02 19:00:00
  Tipo: INCREMENTAL
  Há 1 dias

Última data de preços: 2024-03-02
  Há 1 dias

Última data de scores: 2024-03-02

Estatísticas:
  Preços: 125,476 registros
  Scores: 3,640 registros
  Tickers: 63

================================================================================
RECOMENDAÇÃO: INCREMENTAL
================================================================================
  • Dados atualizados (última execução há 1 dias)
  • Preços recentes (há 1 dias)
  • 63 tickers disponíveis

🔍 DRY RUN - Não executando pipeline
   Seria executado: INCREMENTAL
```

## Opções Avançadas

### Forçar FULL

```bash
# Ignora análise e executa FULL
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --force-full
```

Use quando:
- Quer reprocessar tudo do zero
- Suspeita de dados corrompidos
- Mudou configurações importantes

### Forçar INCREMENTAL

```bash
# Ignora análise e executa INCREMENTAL
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --force-incremental
```

Use quando:
- Tem certeza que dados estão OK
- Quer apenas atualização rápida
- Está testando

### Limitar Tickers

```bash
# Processar apenas 20 tickers (mais rápido)
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --limit 20

# Processar todos os tickers líquidos (~63)
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --limit 100
```

### Pular Suavização

```bash
# Não aplicar suavização temporal
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --skip-smoothing
```

## Exemplos Práticos

### 1. Execução Diária Automática

```bash
# Deixa o pipeline decidir (recomendado para cron)
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --limit 50
```

### 2. Primeira Execução / Setup

```bash
# Forçar FULL na primeira vez
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --force-full --limit 63
```

### 3. Recuperação de Falha

```bash
# Se pipeline falhou há dias, forçar FULL
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --force-full
```

### 4. Teste Rápido

```bash
# Ver o que seria executado
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --dry-run

# Executar com poucos tickers
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --limit 10
```

### 5. Atualização Manual

```bash
# Forçar incremental para atualização rápida
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --force-incremental --limit 50
```

## Configuração no Cron

### Recomendado (Automático)

```bash
# Editar crontab
crontab -e

# Adicionar (executa às 19:00 todos os dias)
0 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --limit 50 >> ~/pipeline.log 2>&1
```

### Alternativa (FULL Semanal + INCREMENTAL Diário)

```bash
# INCREMENTAL de segunda a sexta
0 19 * * 1-5 cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --force-incremental --limit 50 >> ~/pipeline.log 2>&1

# FULL aos sábados
0 9 * * 6 cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --force-full --limit 63 >> ~/pipeline_full.log 2>&1
```

## Logs e Monitoramento

### Ver Logs

```bash
# Últimas 50 linhas
tail -50 ~/pipeline.log

# Monitorar em tempo real
tail -f ~/pipeline.log

# Ver apenas análises
grep "RECOMENDAÇÃO" ~/pipeline.log

# Ver apenas erros
grep "ERROR\|✗" ~/pipeline.log
```

### Verificar Última Execução

```bash
# Ver última linha do log
tail -1 ~/pipeline.log

# Ver resumo da última execução
grep "RESUMO" ~/pipeline.log -A 10 | tail -11
```

## Troubleshooting

### Pipeline sempre executa FULL

**Problema**: Última execução não está sendo registrada

**Solução**:
```bash
# Verificar tabela pipeline_executions
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import PipelineExecution

db = SessionLocal()
last = db.query(PipelineExecution).order_by(PipelineExecution.execution_date.desc()).first()
if last:
    print(f'Última execução: {last.execution_date}')
    print(f'Tipo: {last.execution_type}')
    print(f'Status: {last.status}')
else:
    print('Nenhuma execução registrada')
db.close()
"
```

### Pipeline sempre executa INCREMENTAL

**Problema**: Dados antigos mas pipeline não detecta

**Solução**:
```bash
# Forçar FULL manualmente
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --force-full
```

### Análise mostra dados antigos mas estão atualizados

**Problema**: Timezone ou data do sistema incorreta

**Solução**:
```bash
# Verificar data do sistema
date

# Verificar timezone
timedatectl

# Ajustar se necessário
sudo timedatectl set-timezone America/Sao_Paulo
```

## Comparação: Manual vs Inteligente

### Pipeline Manual

```bash
# Você decide FULL ou INCREMENTAL
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid
docker exec quant-ranker-backend python scripts/clear_and_run_full.py
```

**Vantagens:**
- Controle total
- Previsível

**Desvantagens:**
- Precisa decidir manualmente
- Pode esquecer de fazer FULL
- Pode fazer FULL desnecessário

### Pipeline Inteligente

```bash
# Pipeline decide automaticamente
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py
```

**Vantagens:**
- Decisão automática
- Otimiza recursos
- Recupera de falhas automaticamente
- Ideal para cron

**Desvantagens:**
- Menos controle direto
- Precisa confiar na lógica

## Quando Usar Cada Um

**Use Pipeline Inteligente:**
- ✅ Execução automática via cron
- ✅ Não quer se preocupar com FULL vs INCREMENTAL
- ✅ Quer otimização automática
- ✅ Produção

**Use Pipeline Manual:**
- ✅ Desenvolvimento e testes
- ✅ Quer controle total
- ✅ Situações específicas
- ✅ Debug

## Métricas de Decisão

O pipeline usa estas métricas para decidir:

| Métrica | FULL | INCREMENTAL |
|---------|------|-------------|
| Dias desde última execução | >7 | ≤7 |
| Dias desde últimos preços | >7 | ≤7 |
| Número de tickers | <50 | ≥50 |
| Registros de preços | 0 | >0 |
| Primeira execução | Sim | Não |

## Próximos Passos

Após configurar o pipeline inteligente:

1. ✅ Testar com `--dry-run`
2. ✅ Executar manualmente uma vez
3. ✅ Verificar logs
4. ✅ Configurar no cron
5. ✅ Monitorar primeira execução automática

## Documentação Relacionada

- `CRON_QUICKSTART.md` - Configuração de cron
- `deploy/CRON_SETUP.md` - Configuração detalhada
- `BACKTEST_PIPELINE.md` - Pipeline de backtest
