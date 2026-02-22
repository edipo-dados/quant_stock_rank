# 💡 Render - Dicas e Melhores Práticas

## 🎯 Dicas Gerais

### 1. Escolha a Região Certa

**Recomendação:** Escolha a região mais próxima dos seus usuários.

```
🇺🇸 Oregon (US West) - Melhor para Brasil
🇺🇸 Ohio (US East) - Alternativa para Brasil
🇪🇺 Frankfurt - Melhor para Europa
🇸🇬 Singapore - Melhor para Ásia
```

**IMPORTANTE:** Todos os serviços (DB, Backend, Frontend) devem estar na MESMA região para melhor performance.

### 2. Use Internal URLs

Quando um serviço precisa se comunicar com outro no Render:

✅ **CORRETO:** Use Internal Database URL
```
postgresql://user:pass@dpg-xxxxx/dbname
```

❌ **ERRADO:** Usar External URL
```
postgresql://user:pass@dpg-xxxxx-a.oregon-postgres.render.com/dbname
```

**Por quê?** Internal URLs são mais rápidas e não contam para bandwidth.

### 3. Comece com Free Tier

Para testar e validar:
1. Use Free Tier primeiro
2. Teste tudo funciona
3. Depois faça upgrade para Starter

**Limitações do Free Tier:**
- Services dormem após 15 min
- Database expira em 90 dias
- 750 horas/mês total
- Pode ser lento

### 4. Monitore Uso de Recursos

Dashboard → Service → Metrics

Fique de olho em:
- **CPU Usage:** Se >80% constantemente, considere upgrade
- **Memory Usage:** Se >80%, considere upgrade
- **Request Count:** Para entender tráfego
- **Response Time:** Se >1s, otimize ou upgrade

---

## 🚀 Performance

### 1. Otimize Dockerfiles

**Use multi-stage builds:**
```dockerfile
# Stage 1: Build
FROM python:3.11 as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY app/ ./app/
CMD ["uvicorn", "app.main:app"]
```

**Benefícios:**
- Imagens menores
- Build mais rápido
- Menos uso de disco

### 2. Use Cache de Dependências

No Dockerfile:
```dockerfile
# Copiar requirements primeiro (cache layer)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiar código depois
COPY app/ ./app/
```

**Por quê?** Docker cacheia layers. Se requirements não mudar, não reinstala.

### 3. Configure Workers

Para FastAPI:
```dockerfile
CMD ["uvicorn", "app.main:app", "--workers", "2"]
```

**Regra geral:** `workers = (2 x CPU cores) + 1`

Planos:
- Free/Starter (0.5 CPU): 1 worker
- Standard (1 CPU): 2-3 workers
- Pro (2 CPU): 4-5 workers

### 4. Use Gunicorn + Uvicorn

Para produção:
```dockerfile
CMD ["gunicorn", "app.main:app", "-w", "2", "-k", "uvicorn.workers.UvicornWorker"]
```

**Benefícios:**
- Melhor gerenciamento de workers
- Graceful shutdown
- Mais estável

---

## 💾 Banco de Dados

### 1. Use Connection Pooling

No código:
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True  # Verifica conexão antes de usar
)
```

### 2. Índices no Banco

Para queries rápidas:
```sql
CREATE INDEX idx_ticker ON raw_price_daily(ticker);
CREATE INDEX idx_date ON raw_price_daily(date);
CREATE INDEX idx_ticker_date ON raw_price_daily(ticker, date);
```

### 3. Backups Automáticos

Planos Starter+ têm backup diário automático.

**Recomendação adicional:**
- Configure backup manual semanal
- Guarde em S3 ou Google Drive
- Teste restore periodicamente

### 4. Monitore Tamanho do Banco

```sql
SELECT pg_size_pretty(pg_database_size('quant_ranker'));
```

**Planos:**
- Starter: 1 GB
- Standard: 10 GB
- Pro: 100 GB

Se estiver perto do limite, considere:
- Limpar dados antigos
- Arquivar histórico
- Upgrade de plano

---

## 🔐 Segurança

### 1. Nunca Exponha Secrets

❌ **ERRADO:**
```python
DATABASE_URL = "postgresql://user:pass@host/db"
```

✅ **CORRETO:**
```python
import os
DATABASE_URL = os.getenv("DATABASE_URL")
```

### 2. Use HTTPS Sempre

Render provisiona SSL automaticamente. Certifique-se:
```python
# No FastAPI
app.add_middleware(
    HTTPSRedirectMiddleware
)
```

### 3. Configure CORS Corretamente

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://quant-ranker-frontend.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/ranking")
@limiter.limit("10/minute")
async def get_ranking():
    ...
```

---

## 📊 Monitoramento

### 1. Configure Health Checks

```python
@app.get("/health")
async def health_check():
    # Verificar banco
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": db_status,
        "version": "1.0.0"
    }
```

### 2. Use Logging Estruturado

```python
import logging
import json

logger = logging.getLogger(__name__)

logger.info(json.dumps({
    "event": "ranking_calculated",
    "ticker_count": 62,
    "duration_ms": 1234
}))
```

**Benefícios:**
- Fácil de parsear
- Fácil de filtrar
- Fácil de analisar

### 3. Configure Alertas

Render → Service → Settings → Notifications

Configure para:
- Deploy failed
- Service down
- High error rate (>5%)
- High response time (>2s)

### 4. Use Ferramentas Externas

**UptimeRobot** (Grátis)
- Monitora uptime
- Alerta se cair
- Histórico de disponibilidade

**Sentry** (Grátis até 5k eventos/mês)
- Captura erros
- Stack traces
- Performance monitoring

**Papertrail** (Grátis até 50 MB/mês)
- Logs centralizados
- Busca avançada
- Alertas customizados

---

## 💰 Otimização de Custos

### 1. Use Free Tier Inteligentemente

Você tem 750 horas/mês grátis. Isso é suficiente para:
- 1 serviço 24/7 (720 horas)
- Ou 2 serviços 12h/dia cada
- Ou 3 serviços 8h/dia cada

**Estratégia:**
- Backend: Free (sempre ativo)
- Frontend: Free (dorme)
- Database: Starter ($7) - não expira

### 2. Combine Serviços

Se possível, rode backend + frontend no mesmo container:
```dockerfile
# Usar Nginx para servir ambos
```

**Economia:** $7/mês (1 serviço em vez de 2)

### 3. Use Cron Jobs em Vez de Workers

Para tarefas periódicas, use Cron Jobs (grátis) em vez de workers rodando 24/7.

**Exemplo:**
- ❌ Worker rodando 24/7 checando a cada hora: $7/mês
- ✅ Cron Job rodando 1x/hora: Grátis

### 4. Otimize Database

- Limpe dados antigos regularmente
- Use índices para queries rápidas
- Evite queries N+1
- Use paginação

**Resultado:** Pode usar plano menor por mais tempo.

---

## 🔄 CI/CD

### 1. Deploy Automático

Render já faz deploy automático quando você faz push.

**Configurar:**
- Settings → Auto-Deploy: ON
- Branch: main

### 2. Preview Environments

Para testar antes de produção:
- Settings → Pull Request Previews: ON

Cada PR cria um ambiente temporário.

### 3. Rollback Rápido

Se algo der errado:
1. Dashboard → Service → Events
2. Encontrar deploy anterior
3. Clicar em "Rollback"

**Tempo:** ~30 segundos

### 4. Blue-Green Deployment

Para zero downtime:
1. Criar novo serviço (green)
2. Testar completamente
3. Trocar DNS/URL
4. Deletar serviço antigo (blue)

---

## 🧪 Testes

### 1. Teste Localmente Primeiro

Antes de fazer deploy:
```bash
# Build local
docker build -f docker/Dockerfile.backend.render -t backend .

# Rodar local
docker run -p 8000:8000 backend

# Testar
curl http://localhost:8000/health
```

### 2. Use Staging Environment

Crie um ambiente de staging:
- Database: Free (para testes)
- Backend: Free
- Frontend: Free

**Custo:** $0

### 3. Smoke Tests Pós-Deploy

Após cada deploy, teste automaticamente:
```bash
#!/bin/bash
curl -f https://backend.onrender.com/health || exit 1
curl -f https://backend.onrender.com/api/v1/ranking || exit 1
```

---

## 📝 Documentação

### 1. Documente URLs

Crie um arquivo `URLS.md`:
```markdown
# URLs de Produção

Frontend: https://quant-ranker-frontend.onrender.com
Backend: https://quant-ranker-backend.onrender.com
API Docs: https://quant-ranker-backend.onrender.com/docs
```

### 2. Documente Variáveis de Ambiente

```markdown
# Variáveis de Ambiente

## Backend
- DATABASE_URL: Connection string do PostgreSQL
- MOMENTUM_WEIGHT: Peso do fator momentum (0.4)
- QUALITY_WEIGHT: Peso do fator qualidade (0.3)
- VALUE_WEIGHT: Peso do fator valor (0.3)
```

### 3. Documente Processos

- Como fazer deploy
- Como fazer rollback
- Como executar pipeline manualmente
- Como fazer backup/restore

---

## 🎓 Aprendizado Contínuo

### 1. Monitore Métricas

Acompanhe semanalmente:
- Uptime
- Response time
- Error rate
- Database size
- Custos

### 2. Otimize Continuamente

- Identifique queries lentas
- Otimize código
- Adicione cache onde faz sentido
- Reduza dependências desnecessárias

### 3. Mantenha Atualizado

- Atualize dependências regularmente
- Monitore security advisories
- Teste em staging primeiro

---

## 🆘 Quando Pedir Ajuda

Peça ajuda se:
- Build falha repetidamente
- Performance está ruim (>2s response time)
- Custos estão muito altos
- Erros frequentes nos logs
- Database está crescendo muito rápido

**Onde pedir:**
- Render Support (support@render.com)
- Render Community (community.render.com)
- Stack Overflow (tag: render)

---

## ✨ Resumo das Melhores Práticas

✅ Use Internal URLs entre serviços  
✅ Comece com Free Tier para testar  
✅ Monitore recursos constantemente  
✅ Configure health checks  
✅ Use connection pooling  
✅ Configure backups automáticos  
✅ Nunca exponha secrets  
✅ Use HTTPS sempre  
✅ Configure rate limiting  
✅ Use logging estruturado  
✅ Configure alertas  
✅ Teste localmente primeiro  
✅ Documente tudo  
✅ Otimize continuamente  

---

**Boa sorte com seu deploy! 🚀**

