# 🐳 Deploy via Docker Hub (Solução Definitiva)

**Quando usar**: Quando o EC2 não consegue fazer build (falta de recursos, espaço, etc.)

**Vantagem**: Build no seu PC (com mais recursos) e apenas pull no EC2

---

## 📋 Pré-requisitos

1. Conta no Docker Hub (gratuita): https://hub.docker.com/signup
2. Docker Desktop instalado no seu PC Windows
3. Git Bash ou PowerShell

---

## 🚀 Passo 1: Build Local (no seu PC Windows)

### 1.1 Abrir Terminal
```bash
# Git Bash ou PowerShell
cd C:\Users\edipo\quanty_quality_rank\quant_stock_rank
```

### 1.2 Login no Docker Hub
```bash
docker login
# Digite seu username e password do Docker Hub
```

### 1.3 Build das Imagens
```bash
# Backend (vai demorar 3-5 minutos)
docker build -f docker/Dockerfile.backend -t SEU-USUARIO/quant-backend:2.5.0 .

# Frontend (vai demorar 2-3 minutos)
docker build -f docker/Dockerfile.frontend -t SEU-USUARIO/quant-frontend:2.5.0 .
```

**IMPORTANTE**: Substitua `SEU-USUARIO` pelo seu username do Docker Hub!

Exemplo: Se seu username é `joaosilva`, use:
```bash
docker build -f docker/Dockerfile.backend -t joaosilva/quant-backend:2.5.0 .
docker build -f docker/Dockerfile.frontend -t joaosilva/quant-frontend:2.5.0 .
```

### 1.4 Push para Docker Hub
```bash
# Push backend
docker push SEU-USUARIO/quant-backend:2.5.0

# Push frontend
docker push SEU-USUARIO/quant-frontend:2.5.0
```

Aguarde o upload completar (pode demorar 5-10 minutos dependendo da sua internet).

---

## 🔧 Passo 2: Configurar EC2

### 2.1 Criar docker-compose.hub.yml

No EC2, criar novo arquivo:

```bash
cd /home/ubuntu/quant_stock_rank
nano docker-compose.hub.yml
```

Colar este conteúdo (SUBSTITUIR `SEU-USUARIO`):

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: quant-ranker-db
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-quant_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-quant_password}
      POSTGRES_DB: ${POSTGRES_DB:-quant_ranker}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - quant-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-quant_user} -d ${POSTGRES_DB:-quant_ranker}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  backend:
    image: SEU-USUARIO/quant-backend:2.5.0
    container_name: quant-ranker-backend
    dns:
      - 8.8.8.8
      - 8.8.4.4
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-quant_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-quant_password}
      POSTGRES_DB: ${POSTGRES_DB:-quant_ranker}
      DATABASE_URL: postgresql://${POSTGRES_USER:-quant_user}:${POSTGRES_PASSWORD:-quant_password}@postgres:5432/${POSTGRES_DB:-quant_ranker}
      MOMENTUM_WEIGHT: ${MOMENTUM_WEIGHT:-0.35}
      QUALITY_WEIGHT: ${QUALITY_WEIGHT:-0.25}
      VALUE_WEIGHT: ${VALUE_WEIGHT:-0.30}
      SIZE_WEIGHT: ${SIZE_WEIGHT:-0.10}
      API_HOST: ${API_HOST:-0.0.0.0}
      API_PORT: ${API_PORT:-8000}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    ports:
      - "${API_PORT:-8000}:8000"
    volumes:
      - ./app:/app/app
      - ./scripts:/app/scripts
      - backend_logs:/app/logs
    networks:
      - quant-network
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

  frontend:
    image: SEU-USUARIO/quant-frontend:2.5.0
    container_name: quant-ranker-frontend
    environment:
      BACKEND_URL: http://backend:8000
      FRONTEND_PORT: ${FRONTEND_PORT:-8501}
    ports:
      - "${FRONTEND_PORT:-8501}:8501"
    volumes:
      - ./frontend:/app/frontend
      - ./app:/app/app
    networks:
      - quant-network
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  backend_logs:
    driver: local

networks:
  quant-network:
    driver: bridge
```

Salvar (Ctrl+O, Enter, Ctrl+X)

### 2.2 Iniciar Containers

```bash
# Parar containers antigos
docker-compose down

# Iniciar com novo arquivo
docker-compose -f docker-compose.hub.yml up -d

# Verificar
docker-compose -f docker-compose.hub.yml ps
```

---

## ✅ Passo 3: Verificar e Configurar

### 3.1 Verificar Status
```bash
# Aguardar 60 segundos
sleep 60

# Ver status
docker-compose -f docker-compose.hub.yml ps

# Ver logs
docker-compose -f docker-compose.hub.yml logs backend | tail -30
docker-compose -f docker-compose.hub.yml logs frontend | tail -30
```

### 3.2 Executar Migrações
```bash
docker exec quant-ranker-backend python scripts/migrate_add_academic_momentum.py
docker exec quant-ranker-backend python scripts/migrate_add_value_size_factors.py
docker exec quant-ranker-backend python scripts/migrate_add_backtest_smoothing.py
```

### 3.3 Aplicar Suavização
```bash
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all
```

### 3.4 Executar Pipeline
```bash
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50
```

### 3.5 Verificar Sistema
```bash
docker exec quant-ranker-backend python scripts/pre_deploy_check.py
curl http://localhost:8000/health
```

---

## 🔄 Atualizações Futuras

Quando precisar atualizar o código:

**No seu PC:**
```bash
cd quant_stock_rank
git pull origin main

# Rebuild e push
docker build -f docker/Dockerfile.backend -t SEU-USUARIO/quant-backend:2.5.1 .
docker push SEU-USUARIO/quant-backend:2.5.1

docker build -f docker/Dockerfile.frontend -t SEU-USUARIO/quant-frontend:2.5.1 .
docker push SEU-USUARIO/quant-frontend:2.5.1
```

**No EC2:**
```bash
cd /home/ubuntu/quant_stock_rank
git pull origin main

# Atualizar versão no docker-compose.hub.yml
nano docker-compose.hub.yml
# Mudar 2.5.0 para 2.5.1

# Restart
docker-compose -f docker-compose.hub.yml down
docker-compose -f docker-compose.hub.yml pull
docker-compose -f docker-compose.hub.yml up -d
```

---

## 📊 Vantagens desta Abordagem

✅ Build no PC (mais recursos)  
✅ Sem problemas de memória/disco no EC2  
✅ Deploy rápido (apenas pull)  
✅ Fácil rollback (trocar versão)  
✅ Funciona em qualquer EC2 (até t2.micro)  

---

## 🆘 Troubleshooting

### Erro: "denied: requested access to the resource is denied"
```bash
# Fazer login novamente
docker login
```

### Erro: "manifest unknown"
```bash
# Verificar se fez push
docker images | grep quant

# Se não tiver, fazer push novamente
docker push SEU-USUARIO/quant-backend:2.5.0
```

### Containers não iniciam
```bash
# Ver logs
docker-compose -f docker-compose.hub.yml logs

# Restart
docker-compose -f docker-compose.hub.yml restart
```

---

**Versão**: 2.5.0  
**Data**: 2026-02-25  
**Status**: ✅ SOLUÇÃO DEFINITIVA
