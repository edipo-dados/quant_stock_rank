# 🚨 SOLUÇÃO IMEDIATA PARA ERRO NO EC2

**Erro**: Build falha com `exit code: 1` no `pip install`

---

## 🎯 Execute Estes Comandos no EC2 (Copy & Paste)

### 1️⃣ Conectar e Atualizar
```bash
ssh -i sua-chave.pem ubuntu@seu-ec2-ip
cd /home/ubuntu/quant_stock_rank
git pull origin main
```

### 2️⃣ Executar Fix Automático
```bash
chmod +x scripts/fix_ec2_build.sh scripts/setup_ec2_swap.sh
bash scripts/fix_ec2_build.sh
```

**O que o script faz:**
- ✅ Adiciona 2GB de swap (resolve problema de memória)
- ✅ Instala gcc, g++, build-essential
- ✅ Configura Dockerfile otimizado
- ✅ Limpa cache do Docker

### 3️⃣ Rebuild
```bash
docker-compose down
docker-compose up -d --build
```

**Aguarde 2-5 minutos** para o build completar.

### 4️⃣ Verificar
```bash
# Aguardar containers iniciarem
sleep 60

# Ver status
docker-compose ps

# Ver logs
docker-compose logs backend | tail -30
```

Se ver "Uvicorn running" nos logs, está funcionando! ✅

---

## 🔄 Se Ainda Falhar

### Opção 1: Usar Dockerfile Otimizado Manualmente
```bash
nano docker-compose.yml
```

Linha 28 (backend), mudar de:
```yaml
dockerfile: docker/Dockerfile.backend
```

Para:
```yaml
dockerfile: docker/Dockerfile.backend.ec2
```

Linha 82 (frontend), mudar de:
```yaml
dockerfile: docker/Dockerfile.frontend
```

Para:
```yaml
dockerfile: docker/Dockerfile.frontend.ec2
```

Salvar (Ctrl+O, Enter, Ctrl+X) e rebuild:
```bash
docker-compose down
docker-compose up -d --build
```

---

### Opção 2: Verificar Memória e Swap
```bash
free -h
```

Se não tiver swap, adicionar manualmente:
```bash
bash scripts/setup_ec2_swap.sh
```

---

### Opção 3: Ver Logs Detalhados
```bash
docker-compose build backend 2>&1 | tee build.log
tail -100 build.log
```

Procure por:
- "MemoryError" → Precisa de mais swap
- "Timeout" → Problema de rede
- "gcc: command not found" → Precisa instalar dependências

---

## ✅ Após Build Bem-Sucedido

```bash
# Migrações (ORDEM IMPORTANTE!)
docker exec quant-ranker-backend python scripts/migrate_add_academic_momentum.py
docker exec quant-ranker-backend python scripts/migrate_add_value_size_factors.py
docker exec quant-ranker-backend python scripts/migrate_add_backtest_smoothing.py

# Suavização
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all

# Pipeline
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50

# Verificar
docker exec quant-ranker-backend python scripts/pre_deploy_check.py
curl http://localhost:8000/health
```

---

## 📊 Comandos de Diagnóstico

```bash
# Memória
free -h

# Disco
df -h

# Swap
swapon --show

# Containers
docker-compose ps

# Logs
docker-compose logs backend
docker-compose logs frontend
```

---

## 🆘 Última Opção

Se nada funcionar, considere:

1. **Upgrade da instância**: t2.micro → t2.small (2GB RAM)
2. **Build local + Docker Hub**: Build no seu PC e push para registry
3. **Ver documentação completa**: `EC2_BUILD_TROUBLESHOOTING.md`

---

## 💡 Dica

O problema mais comum é **falta de memória** em instâncias t2.micro (1GB RAM).

A solução mais rápida é adicionar swap:
```bash
bash scripts/setup_ec2_swap.sh
```

---

**Commit**: 55ee691  
**Versão**: 2.5.0  
**Data**: 2026-02-25
