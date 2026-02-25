# 🚀 Guia Completo de Deploy no EC2

**Versão**: 2.5.0  
**Data**: 2026-02-25  
**Status**: Guia Completo com Todas as Soluções

---

## 📋 Problemas Comuns e Soluções

### Problema 1: Build Falha com `exit code: 1`
**Causa**: Falta de memória (RAM)  
**Solução**: Ver `EC2_BUILD_TROUBLESHOOTING.md`

### Problema 2: `No space left on device`
**Causa**: Disco cheio  
**Solução**: Ver `EC2_NO_SPACE_FIX.md`

### Problema 3: Frontend usa `requirements.txt` completo
**Causa**: Dockerfile.frontend não atualizado  
**Solução**: Usar Dockerfile.frontend.ec2

---

## ✅ Deploy Completo (Passo a Passo)

### Pré-requisitos
- EC2 Ubuntu 20.04/22.04
- Mínimo: t2.small (2GB RAM, 15GB disco)
- Docker e Docker Compose instalados
- Git configurado

### Passo 1: Conectar ao EC2
```bash
ssh -i sua-chave.pem ubuntu@seu-ec2-ip
cd /home/ubuntu/quant_stock_rank
```

### Passo 2: Atualizar Código
```bash
git pull origin main
```

### Passo 3: Verificar Recursos

#### 3.1 Verificar Espaço em Disco
```bash
df -h /
```

**Se < 5GB livres:**
```bash
chmod +x scripts/cleanup_ec2_disk.sh
bash scripts/cleanup_ec2_disk.sh
```

#### 3.2 Verificar Memória
```bash
free -h
```

**Se < 2GB RAM total:**
```bash
chmod +x scripts/setup_ec2_swap.sh
bash scripts/setup_ec2_swap.sh
```

### Passo 4: Configurar Sistema
```bash
# Executar fix automático
chmod +x scripts/fix_ec2_build.sh
bash scripts/fix_ec2_build.sh
```

**O script configura:**
- ✅ Swap (2GB)
- ✅ Dependências (gcc, g++, etc.)
- ✅ Dockerfiles otimizados (.ec2)
- ✅ Limpeza de cache

### Passo 5: Build
```bash
docker-compose down
docker-compose up -d --build
```

**Tempo estimado**: 5-10 minutos

### Passo 6: Monitorar Build

Em outro terminal:
```bash
# Logs em tempo real
docker-compose logs -f backend

# Ou
docker-compose logs -f frontend
```

Ou:
```bash
# Ver progresso
watch -n 2 docker-compose ps
```

### Passo 7: Verificar Sucesso
```bash
# Aguardar containers iniciarem
sleep 60

# Ver status
docker-compose ps

# Verificar backend
curl http://localhost:8000/health

# Ver logs
docker-compose logs backend | tail -30
docker-compose logs frontend | tail -30
```

**Sucesso se ver:**
- Backend: `Uvicorn running on http://0.0.0.0:8000`
- Frontend: `You can now view your Streamlit app`
- Status: `healthy`

### Passo 8: Executar Migrações
```bash
docker exec quant-ranker-backend python scripts/migrate_add_academic_momentum.py
docker exec quant-ranker-backend python scripts/migrate_add_value_size_factors.py
docker exec quant-ranker-backend python scripts/migrate_add_backtest_smoothing.py
```

### Passo 9: Aplicar Suavização
```bash
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all
```

### Passo 10: Executar Pipeline
```bash
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50
```

### Passo 11: Verificar Sistema
```bash
docker exec quant-ranker-backend python scripts/pre_deploy_check.py
docker exec quant-ranker-backend python scripts/check_db.py
```

### Passo 12: Testar Endpoints
```bash
# Backend
curl http://localhost:8000/health
curl http://localhost:8000/api/ranking/latest

# Frontend (no navegador)
http://seu-ec2-ip:8501
```

---

## 🔧 Troubleshooting

### Build Falha no Backend
```bash
# Ver logs detalhados
docker-compose build backend 2>&1 | tee backend-build.log
tail -100 backend-build.log

# Verificar memória
free -h

# Verificar swap
swapon --show

# Se não tiver swap
bash scripts/setup_ec2_swap.sh

# Tentar novamente
docker-compose down
docker-compose up -d --build
```

### Build Falha no Frontend
```bash
# Ver logs detalhados
docker-compose build frontend 2>&1 | tee frontend-build.log
tail -100 frontend-build.log

# Verificar se está usando requirements-frontend.txt
grep "requirements-frontend.txt" docker/Dockerfile.frontend

# Se não estiver, usar Dockerfile otimizado
nano docker-compose.yml
# Mudar linha 82: dockerfile: docker/Dockerfile.frontend.ec2

# Tentar novamente
docker-compose down
docker-compose up -d --build
```

### Erro: No Space Left on Device
```bash
# Ver espaço
df -h /

# Limpar
bash scripts/cleanup_ec2_disk.sh

# Verificar espaço liberado
df -h /

# Se ainda não tiver 5GB, aumentar volume EBS
# Ver EC2_NO_SPACE_FIX.md
```

### Containers Não Iniciam
```bash
# Ver logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Restart
docker-compose restart

# Se não resolver, rebuild
docker-compose down
docker-compose up -d --build
```

### Backend Unhealthy
```bash
# Ver logs
docker-compose logs backend | tail -50

# Verificar banco
docker exec quant-ranker-backend python scripts/check_db.py

# Restart
docker-compose restart backend
```

### Frontend Unhealthy
```bash
# Ver logs
docker-compose logs frontend | tail -50

# Verificar se backend está OK
curl http://localhost:8000/health

# Restart
docker-compose restart frontend
```

---

## 📊 Requisitos Mínimos

| Recurso | Mínimo | Recomendado | Ideal |
|---------|--------|-------------|-------|
| RAM | 1GB + 2GB swap | 2GB + 2GB swap | 4GB |
| Disco | 15GB | 20GB | 30GB |
| CPU | 1 vCPU | 2 vCPUs | 4 vCPUs |
| Instância | t2.micro* | t2.small | t2.medium |

*t2.micro requer swap obrigatório

---

## 🎯 Checklist Completo

### Pré-Deploy
- [ ] EC2 criada e acessível
- [ ] Docker instalado
- [ ] Docker Compose instalado
- [ ] Git configurado
- [ ] Repositório clonado

### Preparação
- [ ] Git pull executado
- [ ] Espaço em disco verificado (>5GB)
- [ ] Memória verificada (>2GB total)
- [ ] Swap configurado (se necessário)
- [ ] Script fix_ec2_build.sh executado
- [ ] Dependências instaladas

### Build
- [ ] docker-compose down executado
- [ ] docker-compose up -d --build executado
- [ ] Build completado sem erros
- [ ] Containers iniciados

### Verificação
- [ ] docker-compose ps mostra 3 containers
- [ ] Backend status: healthy
- [ ] Frontend status: healthy (ou starting)
- [ ] Postgres status: healthy
- [ ] curl /health retorna 200

### Configuração
- [ ] 3 migrações executadas
- [ ] Suavização aplicada
- [ ] Pipeline executado
- [ ] pre_deploy_check.py passou
- [ ] check_db.py passou

### Testes
- [ ] Backend acessível (curl)
- [ ] Frontend acessível (navegador)
- [ ] Ranking funcionando
- [ ] API respondendo

### Produção
- [ ] Cron configurado (opcional)
- [ ] Monitoramento configurado (opcional)
- [ ] Backup configurado (opcional)
- [ ] Logs configurados

---

## 📚 Documentação

- `EC2_COMPLETE_GUIDE.md` - Este guia (completo)
- `EC2_DEPLOY_FINAL.md` - Guia rápido de deploy
- `EC2_FIX_NOW.md` - Solução rápida para erros
- `EC2_BUILD_TROUBLESHOOTING.md` - Troubleshooting de build
- `EC2_NO_SPACE_FIX.md` - Solução para disco cheio
- `DEPLOY_CHECKLIST.md` - Checklist detalhado
- `DEPLOY_SUMMARY.md` - Resumo executivo

---

## 🆘 Suporte

Se após seguir este guia ainda tiver problemas:

1. **Verificar logs**: `docker-compose logs`
2. **Verificar recursos**: `free -h` e `df -h`
3. **Limpar e tentar novamente**: `bash scripts/cleanup_ec2_disk.sh`
4. **Considerar upgrade**: t2.micro → t2.small
5. **Build local + Docker Hub**: Ver EC2_BUILD_TROUBLESHOOTING.md

---

**Commit**: 3192780  
**Versão**: 2.5.0  
**Data**: 2026-02-25  
**Status**: ✅ GUIA COMPLETO
