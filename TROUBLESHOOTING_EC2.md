# Troubleshooting - Deploy EC2 v2.7.0

## Problema Atual

Frontend não consegue acessar a API:
```
Erro: 404 Client Error: Not Found for url: http://backend:8000/api/v1/ranking
```

## Diagnóstico

Execute esses comandos no EC2 para diagnosticar:

### 1. Verificar Status dos Containers

```bash
docker ps
```

Deve mostrar 3 containers rodando:
- `quant-ranker-backend`
- `quant-ranker-frontend`
- `quant-ranker-db`

### 2. Verificar Logs do Backend

```bash
docker logs quant-ranker-backend --tail 50
```

Procure por:
- ✅ "Starting Quant Stock Ranker API"
- ✅ "Application startup complete"
- ❌ Erros de importação ou banco de dados

### 3. Verificar Logs do Frontend

```bash
docker logs quant-ranker-frontend --tail 50
```

Procure por:
- ✅ "You can now view your Streamlit app"
- ❌ Erros de conexão com backend

### 4. Testar API Diretamente

```bash
# Dentro do container backend
docker exec -it quant-ranker-backend curl http://localhost:8000/health

# Deve retornar: {"status":"healthy","version":"1.0.0"}
```

```bash
# Testar endpoint de ranking
docker exec -it quant-ranker-backend curl http://localhost:8000/api/v1/ranking
```

### 5. Verificar Conectividade entre Containers

```bash
# Do frontend para o backend
docker exec -it quant-ranker-frontend ping -c 3 backend

# Testar curl do frontend para backend
docker exec -it quant-ranker-frontend curl http://backend:8000/health
```

## Soluções

### Solução 1: Rebuild Completo

```bash
# Parar tudo
docker-compose down

# Remover containers antigos
docker rm -f $(docker ps -aq)

# Remover imagens antigas
docker rmi quant_stock_rank-backend quant_stock_rank-frontend

# Rebuild
docker-compose build --no-cache

# Subir
docker-compose up -d

# Verificar
docker ps
docker logs quant-ranker-backend --tail 20
docker logs quant-ranker-frontend --tail 20
```

### Solução 2: Verificar Variáveis de Ambiente

```bash
# Ver variáveis do frontend
docker exec -it quant-ranker-frontend env | grep BACKEND

# Deve mostrar: BACKEND_URL=http://backend:8000
```

Se não estiver correto, editar `docker-compose.yml`:

```yaml
frontend:
  environment:
    - BACKEND_URL=http://backend:8000
```

### Solução 3: Executar Pipeline para Gerar Dados

O erro 404 pode ser porque não há dados no banco:

```bash
# Executar pipeline
docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py

# Verificar se gerou dados
docker exec -it quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
db = SessionLocal()
count = db.query(ScoreDaily).count()
print(f'Total scores: {count}')
db.close()
"
```

### Solução 4: Verificar Network Docker

```bash
# Listar networks
docker network ls

# Inspecionar network
docker network inspect quant_stock_rank_quant-network

# Verificar se os 3 containers estão na mesma network
```

### Solução 5: Testar API do Host

```bash
# Do host EC2, testar API
curl http://localhost:8000/health

# Se funcionar, o problema é na comunicação entre containers
```

## Comandos Úteis

### Ver todos os logs em tempo real

```bash
docker-compose logs -f
```

### Reiniciar apenas um container

```bash
docker-compose restart backend
docker-compose restart frontend
```

### Entrar no container para debug

```bash
# Backend
docker exec -it quant-ranker-backend bash

# Frontend
docker exec -it quant-ranker-frontend bash
```

### Verificar se há dados no banco

```bash
docker exec -it quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from sqlalchemy import func
db = SessionLocal()
latest_date = db.query(func.max(ScoreDaily.date)).scalar()
count = db.query(ScoreDaily).count()
print(f'Latest date: {latest_date}')
print(f'Total scores: {count}')
db.close()
"
```

## Checklist de Validação

Após aplicar as soluções, verificar:

- [ ] `docker ps` mostra 3 containers rodando
- [ ] `docker logs quant-ranker-backend` sem erros
- [ ] `docker logs quant-ranker-frontend` sem erros
- [ ] `curl http://localhost:8000/health` retorna `{"status":"healthy"}`
- [ ] `curl http://localhost:8000/api/v1/ranking` retorna dados ou 404 (se não houver dados)
- [ ] Frontend acessível em `http://<EC2-IP>:8501`
- [ ] Frontend consegue carregar ranking

## Próximos Passos

Se tudo estiver funcionando mas não houver dados:

```bash
# 1. Executar pipeline completo
docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py

# 2. Verificar dados gerados
docker exec -it quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
db = SessionLocal()
print(f'Total scores: {db.query(ScoreDaily).count()}')
db.close()
"

# 3. Acessar frontend e verificar ranking
```

## Contato

Se o problema persistir, forneça:
1. Output de `docker ps`
2. Output de `docker logs quant-ranker-backend --tail 100`
3. Output de `docker logs quant-ranker-frontend --tail 100`
4. Output de `curl http://localhost:8000/health`

---

**Versão**: 2.7.0  
**Data**: Março 2026
