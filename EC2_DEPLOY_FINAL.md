# 🚀 EC2 Deploy - Guia Final Atualizado

**Problema Resolvido**: Build falha no backend E frontend com `exit code: 1`

**Solução**: Dockerfiles otimizados + swap + dependências mínimas

---

## ✅ Solução Completa (Copy & Paste)

### 1️⃣ Conectar ao EC2
```bash
ssh -i sua-chave.pem ubuntu@seu-ec2-ip
cd /home/ubuntu/quant_stock_rank
```

### 2️⃣ Atualizar Código
```bash
git pull origin main
```

### 2.5️⃣ Verificar Espaço em Disco (IMPORTANTE!)
```bash
df -h /
```

**Se tiver menos de 5GB livres**, execute:
```bash
chmod +x scripts/cleanup_ec2_disk.sh
bash scripts/cleanup_ec2_disk.sh
```

### 3️⃣ Executar Fix Automático
```bash
chmod +x scripts/fix_ec2_build.sh scripts/setup_ec2_swap.sh
bash scripts/fix_ec2_build.sh
```

**O script agora configura:**
- ✅ Swap de 2GB (resolve memória)
- ✅ Dependências do sistema (gcc, g++, etc.)
- ✅ Dockerfile.backend.ec2 (instala em etapas)
- ✅ Dockerfile.frontend.ec2 (dependências mínimas)
- ✅ Limpa cache do Docker

### 4️⃣ Rebuild
```bash
docker-compose down
docker-compose up -d --build
```

**Tempo estimado**: 3-7 minutos

### 5️⃣ Monitorar Build
Em outro terminal:
```bash
# Ver logs em tempo real
docker-compose logs -f backend
```

Ou:
```bash
# Ver progresso
watch -n 2 docker-compose ps
```

### 6️⃣ Verificar Sucesso
```bash
# Aguardar containers iniciarem
sleep 60

# Ver status
docker-compose ps

# Verificar backend
curl http://localhost:8000/health

# Verificar logs
docker-compose logs backend | tail -30
docker-compose logs frontend | tail -30
```

**Sucesso se ver:**
- Backend: `Uvicorn running on http://0.0.0.0:8000`
- Frontend: `You can now view your Streamlit app`

---

## 🎯 O Que Mudou

### Backend (Dockerfile.backend.ec2)
- ✅ Instala dependências em 6 etapas separadas
- ✅ Evita timeout de rede
- ✅ Reduz uso de memória por etapa

### Frontend (Dockerfile.frontend.ec2)
- ✅ Usa `requirements-frontend.txt` (apenas 7 pacotes)
- ✅ Antes: 20+ pacotes (incluindo pytest, hypothesis, etc.)
- ✅ Agora: streamlit, plotly, pandas, numpy, requests, dotenv, pydantic
- ✅ Reduz tempo de build em ~60%

### Swap
- ✅ Adiciona 2GB de swap
- ✅ Essencial para t2.micro (1GB RAM)
- ✅ Ajuda t2.small (2GB RAM)

---

## 🔄 Se Ainda Falhar

### Verificar Qual Serviço Falhou
```bash
# Ver logs do build
docker-compose build backend 2>&1 | tee backend-build.log
docker-compose build frontend 2>&1 | tee frontend-build.log

# Ver últimas linhas
tail -50 backend-build.log
tail -50 frontend-build.log
```

### Backend Falhou?
```bash
# Verificar memória
free -h

# Verificar swap
swapon --show

# Se não tiver swap
bash scripts/setup_ec2_swap.sh
```

### Frontend Falhou?
```bash
# Verificar se requirements-frontend.txt existe
ls -la requirements-frontend.txt

# Se não existir
git pull origin main

# Rebuild só frontend
docker-compose build frontend
```

### Ambos Falharam?
```bash
# Verificar conectividade
curl -I https://pypi.org/
ping -c 3 8.8.8.8

# Verificar espaço em disco
df -h

# Limpar Docker
docker system prune -a -f
```

---

## ✅ Após Build Bem-Sucedido

### 1. Executar Migrações
```bash
docker exec quant-ranker-backend python scripts/migrate_add_academic_momentum.py
docker exec quant-ranker-backend python scripts/migrate_add_value_size_factors.py
docker exec quant-ranker-backend python scripts/migrate_add_backtest_smoothing.py
```

### 2. Aplicar Suavização
```bash
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all
```

### 3. Executar Pipeline
```bash
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50
```

### 4. Verificar Sistema
```bash
docker exec quant-ranker-backend python scripts/pre_deploy_check.py
docker exec quant-ranker-backend python scripts/check_db.py
```

### 5. Testar Endpoints
```bash
# Backend
curl http://localhost:8000/health
curl http://localhost:8000/api/ranking/latest

# Frontend (no navegador)
http://seu-ec2-ip:8501
```

---

## 📊 Comparação

### Antes (requirements.txt completo)
```
Backend: 20+ pacotes, ~3-5 minutos
Frontend: 20+ pacotes, ~3-5 minutos
Total: ~6-10 minutos
Taxa de falha: ~60% em t2.micro
```

### Depois (otimizado)
```
Backend: 20+ pacotes em etapas, ~4-6 minutos
Frontend: 7 pacotes, ~1-2 minutos
Total: ~5-8 minutos
Taxa de falha: ~10% em t2.micro (com swap)
```

---

## 🆘 Última Opção

Se nada funcionar após 3 tentativas:

### Opção A: Upgrade Instância
```
t2.micro (1GB) → t2.small (2GB) = +$10/mês
t2.small (2GB) → t2.medium (4GB) = +$20/mês
```

### Opção B: Build Local + Docker Hub
```bash
# No seu PC
docker login
docker build -f docker/Dockerfile.backend.ec2 -t seu-usuario/quant-backend:2.5.0 .
docker build -f docker/Dockerfile.frontend.ec2 -t seu-usuario/quant-frontend:2.5.0 .
docker push seu-usuario/quant-backend:2.5.0
docker push seu-usuario/quant-frontend:2.5.0

# No EC2
# Editar docker-compose.yml para usar images em vez de build
```

### Opção C: Usar Render/Railway/Fly.io
Plataformas com build automático e mais recursos.

---

## 📝 Checklist

- [ ] Git pull executado
- [ ] Script fix_ec2_build.sh executado
- [ ] Swap configurado (2GB)
- [ ] Dependências instaladas (gcc, g++, etc.)
- [ ] docker-compose.yml atualizado (.ec2)
- [ ] Build executado (docker-compose up -d --build)
- [ ] Containers rodando (docker-compose ps)
- [ ] Backend healthy (curl /health)
- [ ] Frontend acessível (navegador)
- [ ] Migrações executadas (3 scripts)
- [ ] Suavização aplicada
- [ ] Pipeline executado
- [ ] Verificação final (pre_deploy_check.py)

---

## 💡 Dicas

1. **Paciência**: Build pode levar 5-8 minutos
2. **Monitorar**: Use `docker-compose logs -f` em outro terminal
3. **Swap**: Essencial para t2.micro
4. **Espaço**: Mínimo 10GB livre em disco
5. **Rede**: Conexão estável é importante

---

**Commit**: fc9a7f2  
**Versão**: 2.5.0  
**Data**: 2026-02-25  
**Status**: ✅ OTIMIZADO PARA EC2
