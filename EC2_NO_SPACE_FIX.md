# 🚨 ERRO: No Space Left on Device

**Erro**: `[Errno 28] No space left on device`

**Causa**: EC2 sem espaço em disco suficiente para build do Docker

---

## ✅ Solução Imediata (Copy & Paste)

### 1️⃣ Conectar ao EC2
```bash
ssh -i sua-chave.pem ubuntu@seu-ec2-ip
cd /home/ubuntu/quant_stock_rank
```

### 2️⃣ Verificar Espaço
```bash
df -h /
```

Se mostrar 100% ou próximo disso, continue:

### 3️⃣ Limpar Espaço
```bash
# Atualizar código
git pull origin main

# Tornar script executável
chmod +x scripts/cleanup_ec2_disk.sh

# Executar limpeza
bash scripts/cleanup_ec2_disk.sh
```

**O script irá:**
- ✅ Parar containers
- ✅ Remover containers parados
- ✅ Remover imagens Docker não usadas
- ✅ Remover volumes não usados
- ✅ Remover build cache
- ✅ Limpar apt cache
- ✅ Limpar logs antigos
- ✅ Limpar /tmp

### 4️⃣ Verificar Espaço Liberado
```bash
df -h /
```

Deve ter pelo menos 5GB livres para o build.

### 5️⃣ Rebuild
```bash
docker-compose up -d --build
```

---

## 🔄 Limpeza Manual (se script falhar)

### Limpar Docker
```bash
# Parar tudo
docker-compose down

# Limpar TUDO do Docker (CUIDADO!)
docker system prune -a -f --volumes

# Verificar espaço
df -h /
```

### Limpar Sistema
```bash
# Limpar apt
sudo apt-get clean
sudo apt-get autoclean
sudo apt-get autoremove -y

# Limpar logs
sudo journalctl --vacuum-time=3d

# Limpar tmp
sudo rm -rf /tmp/*

# Verificar espaço
df -h /
```

### Encontrar Arquivos Grandes
```bash
# Top 10 maiores diretórios
sudo du -h / 2>/dev/null | sort -rh | head -10

# Arquivos maiores que 100MB
sudo find / -type f -size +100M 2>/dev/null | head -20
```

---

## 💾 Aumentar Espaço em Disco

Se a limpeza não resolver, você precisa aumentar o volume EBS:

### No AWS Console:

1. **EC2 Dashboard** → **Volumes**
2. Selecionar volume da instância
3. **Actions** → **Modify Volume**
4. Aumentar tamanho (ex: 8GB → 20GB)
5. **Modify**

### No EC2 (após modificar):

```bash
# Verificar novo tamanho
lsblk

# Expandir partição (para Ubuntu/Debian)
sudo growpart /dev/xvda 1

# Expandir filesystem
sudo resize2fs /dev/xvda1

# Verificar
df -h /
```

---

## 📊 Espaço Recomendado

| Instância | Disco Padrão | Recomendado | Motivo |
|-----------|--------------|-------------|--------|
| t2.micro | 8GB | 15-20GB | Build Docker + dados |
| t2.small | 8GB | 15-20GB | Build Docker + dados |
| t2.medium | 8GB | 20-30GB | Build Docker + dados + logs |

---

## 🎯 Prevenção

### 1. Limpar Regularmente
```bash
# Adicionar ao cron (diário às 3am)
crontab -e

# Adicionar linha:
0 3 * * * cd /home/ubuntu/quant_stock_rank && bash scripts/cleanup_ec2_disk.sh >> /var/log/cleanup.log 2>&1
```

### 2. Monitorar Espaço
```bash
# Criar script de monitoramento
cat > ~/check_disk.sh << 'EOF'
#!/bin/bash
USED=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $USED -gt 80 ]; then
    echo "⚠️  ALERTA: Disco em ${USED}% de uso!"
    df -h /
fi
EOF

chmod +x ~/check_disk.sh

# Adicionar ao cron (a cada hora)
crontab -e

# Adicionar linha:
0 * * * * ~/check_disk.sh
```

### 3. Limitar Logs
```bash
# Limitar tamanho dos logs do Docker
sudo nano /etc/docker/daemon.json
```

Adicionar:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

```bash
# Reiniciar Docker
sudo systemctl restart docker
```

---

## 🆘 Se Nada Funcionar

### Opção 1: Criar Nova Instância com Mais Disco
- Criar nova EC2 com 20GB de disco
- Migrar dados
- Terminar instância antiga

### Opção 2: Usar Docker Hub (Build Local)
```bash
# No seu PC (com mais espaço)
docker login
docker build -f docker/Dockerfile.backend.ec2 -t seu-usuario/quant-backend:2.5.0 .
docker build -f docker/Dockerfile.frontend.ec2 -t seu-usuario/quant-frontend:2.5.0 .
docker push seu-usuario/quant-backend:2.5.0
docker push seu-usuario/quant-frontend:2.5.0

# No EC2 (apenas pull, sem build)
# Editar docker-compose.yml para usar images
```

### Opção 3: Usar Render/Railway/Fly.io
Plataformas com mais recursos e gerenciamento automático.

---

## 📝 Checklist

- [ ] Verificar espaço em disco (`df -h /`)
- [ ] Executar cleanup_ec2_disk.sh
- [ ] Verificar espaço liberado (mínimo 5GB)
- [ ] Rebuild Docker
- [ ] Se não resolver, aumentar volume EBS
- [ ] Configurar limpeza automática (cron)
- [ ] Configurar monitoramento de disco

---

**Commit**: fc9a7f2  
**Versão**: 2.5.0  
**Data**: 2026-02-25  
**Status**: ⚠️  SEM ESPAÇO EM DISCO
