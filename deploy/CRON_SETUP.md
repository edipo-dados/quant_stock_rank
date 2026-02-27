# Configuração de Cron Jobs - Quant Stock Ranker

Guia completo para configurar execução automática do pipeline e suavização temporal.

## 📅 Cronograma de Execução

```
19:00 - Pipeline diário (atualização de dados e cálculo de scores)
19:30 - Suavização temporal (redução de turnover)
```

## 🔧 Configuração

### 1. Editar Crontab

```bash
# Abrir editor de crontab
crontab -e
```

### 2. Adicionar Jobs

Copie e cole as seguintes linhas no crontab:

```bash
# ============================================================================
# Quant Stock Ranker - Execução Automática
# ============================================================================

# Pipeline diário às 19:00 (após fechamento do mercado)
# Atualiza dados, calcula features e scores
0 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> /var/log/pipeline.log 2>&1

# Suavização temporal às 19:30 (30 min após pipeline)
# Aplica smoothing exponencial para reduzir turnover
30 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all >> /var/log/smoothing.log 2>&1
```

### 3. Salvar e Sair

- **vim/vi**: Pressione `ESC`, digite `:wq`, pressione `ENTER`
- **nano**: Pressione `CTRL+X`, depois `Y`, depois `ENTER`

### 4. Verificar Configuração

```bash
# Listar cron jobs configurados
crontab -l

# Verificar sintaxe do cron
crontab -l | grep quant
```

## 📊 Formato do Cron

```
┌───────────── minuto (0 - 59)
│ ┌───────────── hora (0 - 23)
│ │ ┌───────────── dia do mês (1 - 31)
│ │ │ ┌───────────── mês (1 - 12)
│ │ │ │ ┌───────────── dia da semana (0 - 6) (Domingo=0)
│ │ │ │ │
│ │ │ │ │
* * * * * comando a ser executado
```

### Exemplos

```bash
# Executar às 19:00 todos os dias
0 19 * * *

# Executar às 19:30 todos os dias
30 19 * * *

# Executar às 9:00 apenas dias úteis (segunda a sexta)
0 9 * * 1-5

# Executar a cada 6 horas
0 */6 * * *
```

## 📝 Logs

### Localização dos Logs

```bash
/var/log/pipeline.log    # Logs do pipeline
/var/log/smoothing.log   # Logs da suavização
```

### Visualizar Logs

```bash
# Ver últimas 50 linhas do pipeline
tail -50 /var/log/pipeline.log

# Ver últimas 50 linhas da suavização
tail -50 /var/log/smoothing.log

# Monitorar logs em tempo real
tail -f /var/log/pipeline.log

# Ver logs de hoje
grep "$(date +%Y-%m-%d)" /var/log/pipeline.log

# Ver apenas erros
grep ERROR /var/log/pipeline.log
```

### Rotação de Logs

Para evitar que os logs cresçam indefinidamente, configure logrotate:

```bash
# Criar arquivo de configuração
sudo nano /etc/logrotate.d/quant-ranker

# Adicionar:
/var/log/pipeline.log /var/log/smoothing.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 ubuntu ubuntu
}
```

## 🧪 Testes

### Testar Pipeline Manualmente

```bash
# Executar pipeline
cd ~/quant_stock_rank
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50

# Verificar resultado
docker exec quant-ranker-backend python scripts/check_latest_scores.py
```

### Testar Suavização Manualmente

```bash
# Executar suavização
cd ~/quant_stock_rank
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all

# Verificar scores suavizados
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date

db = SessionLocal()
scores = db.query(ScoreDaily).filter(ScoreDaily.date == date.today()).limit(5).all()
print('Ticker | Raw Score | Smoothed Score')
print('-' * 40)
for s in scores:
    smoothed = s.final_score_smoothed if s.final_score_smoothed else s.final_score
    print(f'{s.ticker:8} | {s.final_score:9.3f} | {smoothed:14.3f}')
db.close()
"
```

### Simular Execução do Cron

```bash
# Executar comando exatamente como o cron faria
cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> /var/log/pipeline.log 2>&1

# Verificar se log foi criado
tail /var/log/pipeline.log
```

## 🔍 Monitoramento

### Verificar Última Execução

```bash
# Ver última linha do log do pipeline
tail -1 /var/log/pipeline.log

# Ver última execução bem-sucedida
grep "COMPLETED" /var/log/pipeline.log | tail -1

# Ver última execução com erro
grep "ERROR" /var/log/pipeline.log | tail -1
```

### Verificar Status dos Containers

```bash
# Verificar se containers estão rodando
docker ps | grep quant-ranker

# Verificar health dos containers
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Alertas por Email (Opcional)

Para receber emails em caso de falha:

```bash
# Instalar mailutils
sudo apt-get install mailutils

# Modificar cron para enviar email em caso de erro
0 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> /var/log/pipeline.log 2>&1 || echo "Pipeline failed" | mail -s "Quant Ranker Alert" seu-email@example.com
```

## 🛠️ Troubleshooting

### Cron não está executando

**Verificar se cron está rodando**:
```bash
sudo systemctl status cron
```

**Iniciar cron**:
```bash
sudo systemctl start cron
sudo systemctl enable cron
```

### Comando funciona manualmente mas não no cron

**Problema**: Cron tem PATH diferente do shell interativo

**Solução**: Use caminhos absolutos
```bash
# Descobrir caminho do docker
which docker
# Resultado: /usr/bin/docker

# Usar caminho completo no cron
0 19 * * * cd ~/quant_stock_rank && /usr/bin/docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> /var/log/pipeline.log 2>&1
```

### Logs não são criados

**Verificar permissões**:
```bash
# Criar diretório de logs se não existir
sudo mkdir -p /var/log

# Dar permissões
sudo touch /var/log/pipeline.log /var/log/smoothing.log
sudo chown ubuntu:ubuntu /var/log/pipeline.log /var/log/smoothing.log
sudo chmod 644 /var/log/pipeline.log /var/log/smoothing.log
```

### Container não está rodando quando cron executa

**Verificar se containers iniciam com o sistema**:
```bash
# Ver restart policy
docker inspect quant-ranker-backend | grep RestartPolicy -A 3

# Deve mostrar: "Name": "unless-stopped"
```

**Configurar restart automático**:
```bash
docker update --restart unless-stopped quant-ranker-backend
docker update --restart unless-stopped quant-ranker-frontend
docker update --restart unless-stopped quant-ranker-db
```

## 📋 Checklist de Configuração

- [ ] Cron jobs adicionados ao crontab
- [ ] Crontab salvo e verificado com `crontab -l`
- [ ] Diretório de logs criado (`/var/log`)
- [ ] Permissões de logs configuradas
- [ ] Pipeline testado manualmente
- [ ] Suavização testada manualmente
- [ ] Containers configurados para restart automático
- [ ] Logrotate configurado (opcional)
- [ ] Alertas por email configurados (opcional)
- [ ] Primeira execução automática verificada

## 🔄 Modificar Horários

Para alterar os horários de execução:

```bash
# Editar crontab
crontab -e

# Exemplos de modificações:

# Executar às 20:00 e 20:30 (em vez de 19:00 e 19:30)
0 20 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> /var/log/pipeline.log 2>&1
30 20 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all >> /var/log/smoothing.log 2>&1

# Executar apenas dias úteis (segunda a sexta)
0 19 * * 1-5 cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> /var/log/pipeline.log 2>&1
30 19 * * 1-5 cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all >> /var/log/smoothing.log 2>&1

# Executar duas vezes por dia (9:00 e 19:00)
0 9,19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> /var/log/pipeline.log 2>&1
30 9,19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all >> /var/log/smoothing.log 2>&1
```

## 📚 Referências

- [Crontab Guru](https://crontab.guru/) - Gerador e validador de expressões cron
- [Cron Documentation](https://man7.org/linux/man-pages/man5/crontab.5.html) - Manual oficial
- [Docker Exec](https://docs.docker.com/engine/reference/commandline/exec/) - Documentação do docker exec

## 💡 Dicas

1. **Sempre teste manualmente antes de configurar o cron**
2. **Use redirecionamento de logs (`>>`) para debug**
3. **Configure logrotate para evitar logs gigantes**
4. **Monitore a primeira execução automática**
5. **Documente qualquer modificação nos horários**
6. **Mantenha backup do crontab**: `crontab -l > ~/crontab-backup.txt`

## 🆘 Suporte

Se encontrar problemas:

1. Verificar logs: `tail -100 /var/log/pipeline.log`
2. Verificar containers: `docker ps`
3. Testar manualmente: `docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode test --limit 5`
4. Consultar documentação: `docs/INDEX.md`
5. Abrir issue no GitHub
