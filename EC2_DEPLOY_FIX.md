# 🚀 EC2 Deploy - Solução Rápida para Erro de Build

**Problema**: Build falha no EC2 com `exit code: 1` no `pip install`

---

## ✅ Solução Rápida (5 minutos)

### Passo 1: Conectar ao EC2
```bash
ssh -i sua-chave.pem ubuntu@seu-ec2-ip
cd /home/ubuntu/quant_stock_rank
```

### Passo 2: Atualizar Código
```bash
git pull origin main
```

### Passo 3: Executar Script de Fix
```bash
# Tornar script executável
chmod +x scripts/fix_ec2_build.sh

# Executar
bash scripts/fix_ec2_build.sh
```

O script irá:
- ✅ Verificar recursos do sistema
- ✅ Adicionar swap (2GB) se necessário
- ✅ Instalar dependências (gcc, g++, etc.)
- ✅ Configurar Dockerfile otimizado
- ✅ Limpar cache do Docker

### Passo 4: Rebuild
```bash
docker-compose down
docker-compose up -d --build
```

### Passo 5: Verificar
```bash
# Aguardar 60 segundos
sleep 60

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs backend | tail -50
```

---

## 🎯 Solução Alternativa (se ainda falhar)

### Opção A: Build Manual com Dockerfile Otimizado

```bash
cd /home/ubuntu/quant_stock_rank

# Editar docker-compose.yml
nano docker-compose.yml
```

Alterar linha 28:
```yaml
# De:
dockerfile: docker/Dockerfile.backend

# Para:
dockerfile: docker/Dockerfile.backend.ec2
```

Salvar (Ctrl+O, Enter, Ctrl+X) e rebuild:
```bash
docker-compose down
docker-compose up -d --build
```

---

### Opção B: Usar Imagens Pré-construídas

Se você tem Docker Hub:

**No seu computador local:**
```bash
cd quant_stock_rank

# Login
docker login

# Build e push
docker build -f docker/Dockerfile.backend -t seu-usuario/quant-backend:2.5.0 .
docker push seu-usuario/quant-backend:2.5.0

docker build -f docker/Dockerfile.frontend -t seu-usuario/quant-frontend:2.5.0 .
docker push seu-usuario/quant-frontend:2.5.0
```

**No EC2:**
```bash
nano docker-compose.yml
```

Alterar backend e frontend:
```yaml
backend:
  image: seu-usuario/quant-backend:2.5.0
  # Comentar ou remover seção build

frontend:
  image: seu-usuario/quant-frontend:2.5.0
  # Comentar ou remover seção build
```

```bash
docker-compose down
docker-compose pull
docker-compose up -d
```

---

### Opção C: Upgrade da Instância EC2

Se nada funcionar, considere upgrade:
- t2.micro (1GB RAM) → t2.small (2GB RAM)
- t2.small (2GB RAM) → t2.medium (4GB RAM)

No AWS Console:
1. Parar instância
2. Actions → Instance Settings → Change Instance Type
3. Selecionar t2.small ou t2.medium
4. Iniciar instância
5. Tentar build novamente

---

## 📊 Verificar Recursos

```bash
# Memória
free -h

# Disco
df -h

# Swap
swapon --show

# Processos
top
```

---

## 🔍 Debug

### Ver logs detalhados do build:
```bash
docker-compose build backend 2>&1 | tee build.log
tail -100 build.log
```

### Ver logs do container:
```bash
docker-compose logs backend
docker-compose logs frontend
```

### Verificar conectividade:
```bash
curl -I https://pypi.org/
ping -c 3 8.8.8.8
```

---

## ✅ Após Build Bem-Sucedido

```bash
# 1. Executar migrações
docker exec quant-ranker-backend python scripts/migrate_add_academic_momentum.py
docker exec quant-ranker-backend python scripts/migrate_add_value_size_factors.py
docker exec quant-ranker-backend python scripts/migrate_add_backtest_smoothing.py

# 2. Aplicar suavização
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all

# 3. Executar pipeline
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50

# 4. Verificar
docker exec quant-ranker-backend python scripts/pre_deploy_check.py
curl http://localhost:8000/health
```

---

## 📞 Suporte

Se ainda tiver problemas:
1. Ver `EC2_BUILD_TROUBLESHOOTING.md` para diagnóstico completo
2. Verificar logs: `docker-compose logs backend`
3. Verificar recursos: `free -h` e `df -h`

---

**Última Atualização**: 2026-02-25  
**Versão**: 2.5.0
