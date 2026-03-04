# Configuração Rápida do Cron - Pipeline Diário

## Configuração em 3 Passos

### 1. Editar Crontab

```bash
crontab -e
```

Se perguntar qual editor usar, escolha `nano` (mais fácil).

### 2. Adicionar as Linhas

Cole estas linhas no final do arquivo:

```bash
# ============================================================================
# Quant Stock Ranker - Execução Automática Diária (INTELIGENTE)
# ============================================================================

# Pipeline inteligente diário às 19:00 (após fechamento do mercado)
# Decide automaticamente entre FULL e INCREMENTAL
# Inclui suavização temporal automaticamente
0 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --limit 50 >> ~/pipeline.log 2>&1
```

**Alternativa (Pipeline Manual):**

Se preferir controlar manualmente FULL vs INCREMENTAL:

```bash
# Pipeline incremental diário às 19:00
0 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> ~/pipeline.log 2>&1

# Suavização temporal às 19:30 (30 min após pipeline)
30 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all >> ~/smoothing.log 2>&1
```

### 3. Salvar e Sair

- **nano**: Pressione `CTRL+X`, depois `Y`, depois `ENTER`
- **vim**: Pressione `ESC`, digite `:wq`, pressione `ENTER`

## Verificar Configuração

```bash
# Ver cron configurado
crontab -l

# Deve mostrar as 2 linhas que você adicionou
```

## O Que Vai Acontecer

**Todos os dias às 19:00 (Pipeline Inteligente):**

O pipeline analisa o banco de dados e decide automaticamente:

**FULL** (se necessário):
- Limpa dados antigos
- Ingere histórico completo de preços
- Ingere fundamentos
- Calcula todas as features
- Calcula todos os scores
- Aplica suavização temporal

**INCREMENTAL** (se dados estão atualizados):
- Atualiza apenas preços do dia
- Atualiza fundamentos novos
- Calcula features incrementais
- Calcula scores do dia
- Aplica suavização temporal

**Critérios para FULL:**
- Banco de dados vazio
- Primeira execução
- Última execução há mais de 7 dias
- Últimos preços há mais de 7 dias
- Menos de 50 tickers no banco

**Critérios para INCREMENTAL:**
- Dados atualizados (última execução <7 dias)
- Preços recentes (<7 dias)
- Mais de 50 tickers disponíveis

## Verificar Logs

```bash
# Ver log do pipeline
tail -50 ~/pipeline.log

# Ver log da suavização
tail -50 ~/smoothing.log

# Monitorar em tempo real (CTRL+C para sair)
tail -f ~/pipeline.log
```

## Testar Manualmente (Antes do Cron)

```bash
# Testar pipeline inteligente (recomendado)
cd ~/quant_stock_rank
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --limit 50

# Ver análise sem executar (dry-run)
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --dry-run

# Forçar FULL
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --force-full --limit 50

# Forçar INCREMENTAL
docker exec quant-ranker-backend python scripts/run_smart_pipeline.py --force-incremental --limit 50

# Verificar scores
docker exec quant-ranker-backend python scripts/check_latest_scores.py
```

## Modificar Horários

Se quiser executar em horários diferentes, edite o cron:

```bash
crontab -e
```

Exemplos:

```bash
# Executar às 20:00 (em vez de 19:00)
0 20 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> ~/pipeline.log 2>&1

# Executar apenas dias úteis (segunda a sexta)
0 19 * * 1-5 cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> ~/pipeline.log 2>&1

# Executar duas vezes por dia (9:00 e 19:00)
0 9,19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> ~/pipeline.log 2>&1
```

## Formato do Cron

```
┌─── minuto (0-59)
│ ┌─── hora (0-23)
│ │ ┌─── dia do mês (1-31)
│ │ │ ┌─── mês (1-12)
│ │ │ │ ┌─── dia da semana (0-6, 0=domingo)
│ │ │ │ │
* * * * * comando
```

## Troubleshooting

### Cron não está executando

```bash
# Verificar se cron está rodando
sudo systemctl status cron

# Iniciar cron
sudo systemctl start cron
```

### Verificar se containers estão rodando

```bash
docker ps | grep quant-ranker

# Se não estiverem, iniciar
cd ~/quant_stock_rank
docker-compose up -d
```

### Logs não aparecem

```bash
# Criar arquivos de log manualmente
touch ~/pipeline.log ~/smoothing.log
chmod 644 ~/pipeline.log ~/smoothing.log
```

## Backup do Crontab

Sempre faça backup antes de modificar:

```bash
# Salvar backup
crontab -l > ~/crontab-backup.txt

# Restaurar backup (se necessário)
crontab ~/crontab-backup.txt
```

## Remover Cron (se necessário)

```bash
# Editar e remover as linhas
crontab -e

# Ou remover tudo
crontab -r
```

## Próximos Passos

Após configurar o cron:

1. ✅ Aguardar primeira execução (19:00)
2. ✅ Verificar logs: `tail -50 ~/pipeline.log`
3. ✅ Verificar scores: `docker exec quant-ranker-backend python scripts/check_latest_scores.py`
4. ✅ Acessar interface Streamlit para ver ranking atualizado

## Documentação Completa

Para mais detalhes, consulte: `deploy/CRON_SETUP.md`
