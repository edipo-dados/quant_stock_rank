# 🛠️ Render - Comandos Úteis

## 📋 Comandos via Render Shell

### Acessar Shell do Backend

1. Dashboard → quant-ranker-backend
2. Aba "Shell"
3. Executar comandos abaixo

---

## 🗄️ Banco de Dados

### Inicializar Banco (Criar Tabelas)
```bash
python scripts/init_db.py
```

### Verificar Conexão com Banco
```python
python -c "
from app.models.database import engine
with engine.connect() as conn:
    print('✅ Conexão OK')
"
```

### Ver Quantidade de Registros
```python
python -c "
from app.models.database import SessionLocal
from app.models.schemas import RawPriceDaily, RawFundamental, ScoreDaily

db = SessionLocal()
print(f'Preços: {db.query(RawPriceDaily).count()}')
print(f'Fundamentos: {db.query(RawFundamental).count()}')
print(f'Scores: {db.query(ScoreDaily).count()}')
db.close()
"
```

### Limpar Banco (CUIDADO!)
```bash
python scripts/init_db.py --drop
```

---

## 📊 Pipeline

### Executar Pipeline Manualmente
```bash
# Modo teste (5 ativos)
python -m scripts.run_pipeline --mode test

# Modo completo (62 ativos líquidos)
python -m scripts.run_pipeline --mode liquid

# Ativos específicos
python -m scripts.run_pipeline --mode manual --tickers PETR4.SA,VALE3.SA,ITUB4.SA
```

### Ver Logs do Pipeline
```bash
tail -f logs/pipeline.log
```

---

## 🔍 Diagnóstico

### Verificar Saúde da API
```bash
curl http://localhost:8000/health
```

### Testar Endpoints
```bash
# Ranking completo
curl http://localhost:8000/api/v1/ranking

# Top 5
curl http://localhost:8000/api/v1/top?limit=5

# Ativo específico
curl http://localhost:8000/api/v1/asset/PETR4.SA
```

### Verificar Variáveis de Ambiente
```bash
env | grep DATABASE_URL
env | grep MOMENTUM_WEIGHT
```

---

## 📦 Dependências

### Listar Pacotes Instalados
```bash
pip list
```

### Verificar Versão do Python
```bash
python --version
```

### Reinstalar Dependências
```bash
pip install -r requirements.txt --force-reinstall
```

---

## 🔄 Atualização e Deploy

### Via Git (Automático)

1. Faça commit e push no GitHub:
```bash
git add .
git commit -m "Update: descrição da mudança"
git push origin main
```

2. Render detecta automaticamente e faz redeploy

### Deploy Manual

1. Dashboard → Service
2. Botão "Manual Deploy"
3. Selecione branch
4. Clique em "Deploy"

### Rollback para Deploy Anterior

1. Dashboard → Service
2. Aba "Events"
3. Encontre deploy anterior
4. Clique em "Rollback"

---

## 📝 Logs

### Ver Logs em Tempo Real

1. Dashboard → Service
2. Aba "Logs"
3. Logs aparecem automaticamente

### Filtrar Logs

Use a busca no topo da página de logs:
```
ERROR
WARNING
INFO
```

### Download de Logs

1. Aba "Logs"
2. Botão "Download Logs"
3. Escolha período

---

## 🔐 Secrets e Variáveis

### Adicionar Nova Variável

1. Dashboard → Service
2. Aba "Environment"
3. Botão "Add Environment Variable"
4. Preencher Key e Value
5. Salvar (causa redeploy automático)

### Atualizar Variável Existente

1. Dashboard → Service
2. Aba "Environment"
3. Clicar na variável
4. Editar valor
5. Salvar

### Remover Variável

1. Dashboard → Service
2. Aba "Environment"
3. Clicar no X ao lado da variável

---

## ⏰ Cron Jobs

### Executar Cron Job Manualmente

1. Dashboard → Cron Job
2. Botão "Trigger Run"
3. Aguardar execução

### Ver Histórico de Execuções

1. Dashboard → Cron Job
2. Aba "Events"
3. Ver status de cada execução

### Alterar Schedule

1. Dashboard → Cron Job
2. Aba "Settings"
3. Editar "Schedule"
4. Formato: `minuto hora dia mês dia_semana`

Exemplos:
```bash
0 21 * * *     # Todo dia às 21h UTC
0 */6 * * *    # A cada 6 horas
0 9,18 * * *   # Às 9h e 18h UTC
0 18 * * 1-5   # Dias úteis às 18h UTC
```

---

## 🔧 Troubleshooting

### Service Não Inicia

```bash
# Verificar logs de build
Dashboard → Service → Logs → Filtrar "Build"

# Verificar health check
Dashboard → Service → Settings → Health Check Path
```

### Erro de Memória

```bash
# Ver uso de memória
Dashboard → Service → Metrics

# Solução: Upgrade de plano
Settings → Plan → Escolher plano maior
```

### Erro de Timeout

```bash
# Aumentar timeout (se disponível no plano)
Settings → Advanced → Request Timeout
```

### Database Connection Error

```bash
# Verificar DATABASE_URL
Environment → DATABASE_URL

# Testar conexão
python -c "from app.models.database import engine; engine.connect()"

# Verificar se database está online
Dashboard → Database → Status
```

---

## 📊 Monitoramento

### Métricas Disponíveis

1. Dashboard → Service → Metrics
2. Ver:
   - CPU Usage
   - Memory Usage
   - Request Count
   - Response Time
   - Error Rate

### Configurar Alertas

1. Dashboard → Service → Settings
2. "Notifications"
3. Adicionar email ou webhook
4. Escolher eventos:
   - Deploy failed
   - Service down
   - High error rate

---

## 💾 Backup e Restore

### Backup Manual do Database

```bash
# Via Render Shell (no backend)
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Download do backup
# (copiar conteúdo do arquivo)
```

### Backup Automático

Render Starter e planos superiores têm backup automático diário.

Ver backups:
1. Dashboard → Database
2. Aba "Backups"
3. Lista de backups disponíveis

### Restore de Backup

```bash
# Via Render Shell
psql $DATABASE_URL < backup_20260220.sql
```

Ou via Dashboard:
1. Database → Backups
2. Escolher backup
3. Botão "Restore"

---

## 🔄 Scaling

### Horizontal Scaling (Múltiplas Instâncias)

Disponível apenas em planos Pro e superiores.

1. Dashboard → Service → Settings
2. "Scaling"
3. Aumentar "Number of Instances"

### Vertical Scaling (Mais Recursos)

1. Dashboard → Service → Settings
2. "Plan"
3. Escolher plano maior

---

## 🌐 Custom Domain

### Adicionar Domínio Customizado

1. Dashboard → Service → Settings
2. "Custom Domains"
3. Botão "Add Custom Domain"
4. Inserir domínio (ex: api.seudominio.com)
5. Configurar DNS:
   ```
   Type: CNAME
   Name: api
   Value: quant-ranker-backend.onrender.com
   ```

### SSL/HTTPS

Render provisiona SSL automaticamente via Let's Encrypt.

Aguarde 5-10 minutos após adicionar domínio.

---

## 📞 Suporte

### Documentação Oficial
- https://render.com/docs

### Status do Render
- https://status.render.com

### Suporte
- Dashboard → Help → Contact Support
- Email: support@render.com

