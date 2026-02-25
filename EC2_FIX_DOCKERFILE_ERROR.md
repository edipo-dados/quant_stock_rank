# 🚨 ERRO: Dockerfile.backend.ec2.ec2.ec2

**Erro**: `open Dockerfile.backend.ec2.ec2.ec2: no such file or directory`

**Causa**: Script `fix_ec2_build.sh` foi executado múltiplas vezes, aplicando `sed` repetidamente

---

## ✅ Solução Imediata (Copy & Paste)

### No EC2:

```bash
# 1. Conectar
ssh -i sua-chave.pem ubuntu@seu-ec2-ip
cd /home/ubuntu/quant_stock_rank

# 2. Atualizar código (tem o fix)
git pull origin main

# 3. Resetar docker-compose.yml
chmod +x scripts/reset_docker_compose.sh
bash scripts/reset_docker_compose.sh

# 4. Verificar estado
grep "dockerfile:" docker-compose.yml | head -2

# Deve mostrar:
# dockerfile: docker/Dockerfile.backend
# dockerfile: docker/Dockerfile.frontend

# 5. Aplicar fix corretamente (agora com proteção)
chmod +x scripts/fix_ec2_build.sh
bash scripts/fix_ec2_build.sh

# 6. Verificar novamente
grep "dockerfile:" docker-compose.yml | head -2

# Deve mostrar:
# dockerfile: docker/Dockerfile.backend.ec2
# dockerfile: docker/Dockerfile.frontend.ec2

# 7. Rebuild
docker-compose down
docker-compose up -d --build
```

---

## 🔧 Correção Manual (se script falhar)

### Opção 1: Editar Manualmente

```bash
nano docker-compose.yml
```

Procurar e corrigir as linhas:

**Backend (linha ~28):**
```yaml
# De:
dockerfile: docker/Dockerfile.backend.ec2.ec2.ec2

# Para:
dockerfile: docker/Dockerfile.backend.ec2
```

**Frontend (linha ~82):**
```yaml
# De:
dockerfile: docker/Dockerfile.frontend.ec2.ec2.ec2

# Para:
dockerfile: docker/Dockerfile.frontend.ec2
```

Salvar (Ctrl+O, Enter, Ctrl+X)

### Opção 2: Usar Backup

```bash
# Se tiver backup
cp docker-compose.yml.backup docker-compose.yml

# Aplicar fix novamente
bash scripts/fix_ec2_build.sh
```

### Opção 3: Resetar do Git

```bash
# Descartar mudanças locais
git checkout docker-compose.yml

# Aplicar fix
bash scripts/fix_ec2_build.sh
```

---

## 🎯 O Que Foi Corrigido

O script `fix_ec2_build.sh` agora:

1. ✅ Verifica se já foi aplicado antes de aplicar novamente
2. ✅ Não aplica `sed` múltiplas vezes
3. ✅ Mostra mensagem se já estiver configurado

**Antes:**
```bash
sed -i 's|Dockerfile.backend|Dockerfile.backend.ec2|g'
# Executar 3x = Dockerfile.backend.ec2.ec2.ec2
```

**Depois:**
```bash
if grep -q "Dockerfile.backend.ec2"; then
    echo "Já configurado"
else
    sed -i 's|Dockerfile.backend|Dockerfile.backend.ec2|g'
fi
```

---

## 📝 Prevenção

Para evitar este problema no futuro:

1. **Sempre verificar estado antes:**
   ```bash
   grep "dockerfile:" docker-compose.yml
   ```

2. **Usar script de reset se necessário:**
   ```bash
   bash scripts/reset_docker_compose.sh
   ```

3. **Não executar fix_ec2_build.sh múltiplas vezes**
   - Execute apenas uma vez
   - Se precisar executar novamente, reset primeiro

---

## ✅ Após Correção

```bash
# Verificar
docker-compose ps

# Ver logs
docker-compose logs backend | tail -30
docker-compose logs frontend | tail -30

# Testar
curl http://localhost:8000/health
```

---

**Commit**: ffedd39 (com fix)  
**Versão**: 2.5.0  
**Data**: 2026-02-25  
**Status**: ✅ CORRIGIDO
