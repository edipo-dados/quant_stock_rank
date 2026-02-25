# EC2 Build Troubleshooting

**Problema**: Build falha no EC2 com erro no `pip install`

---

## 🔍 Diagnóstico

### Erro Comum:
```
RUN pip install --no-cache-dir -r requirements.txt
exit code: 1
```

### Causas Possíveis:
1. **Falta de memória** - EC2 t2.micro/t2.small tem pouca RAM
2. **Timeout de rede** - Conexão lenta ou instável
3. **Dependências do sistema** - gcc, g++, build-essential faltando
4. **Versões incompatíveis** - Conflitos entre pacotes

---

## ✅ Soluções

### Solução 1: Usar Dockerfile Otimizado (RECOMENDADO)

O `Dockerfile.backend.ec2` instala dependências em etapas menores para evitar timeout e problemas de memória.

```bash
# No EC2, editar docker-compose.yml para usar o Dockerfile otimizado
cd /home/ubuntu/quant_stock_rank

# Backup do docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup

# Editar docker-compose.yml
nano docker-compose.yml
```

Alterar a linha do backend:
```yaml
backend:
  build:
    context: .
    dockerfile: docker/Dockerfile.backend.ec2  # <-- Mudar para .ec2

frontend:
  build:
    context: .
    dockerfile: docker/Dockerfile.frontend.ec2  # <-- Mudar para .ec2
```

Salvar (Ctrl+O, Enter, Ctrl+X) e rebuild:
```bash
docker-compose down
docker-compose up -d --build
```

---

### Solução 2: Aumentar Swap (se t2.micro/t2.small)

EC2 t2.micro tem apenas 1GB RAM. Adicionar swap ajuda:

```bash
# Verificar swap atual
free -h

# Criar arquivo de swap de 2GB
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Tornar permanente
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verificar
free -h
```

Depois rebuild:
```bash
docker-compose down
docker-compose up -d --build
```

---

### Solução 3: Build com Mais Tempo

Aumentar timeout do Docker:

```bash
# Editar daemon.json
sudo nano /etc/docker/daemon.json
```

Adicionar:
```json
{
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 3,
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  }
}
```

Reiniciar Docker:
```bash
sudo systemctl restart docker
docker-compose up -d --build
```

---

### Solução 4: Build Local e Push para Registry

Se o EC2 continuar falhando, build localmente e push para Docker Hub:

**No seu computador local:**
```bash
cd quant_stock_rank

# Login no Docker Hub
docker login

# Build e tag
docker build -f docker/Dockerfile.backend -t seu-usuario/quant-backend:2.5.0 .
docker build -f docker/Dockerfile.frontend -t seu-usuario/quant-frontend:2.5.0 .

# Push
docker push seu-usuario/quant-backend:2.5.0
docker push seu-usuario/quant-frontend:2.5.0
```

**No EC2:**
```bash
# Editar docker-compose.yml
nano docker-compose.yml
```

Alterar para usar imagens do registry:
```yaml
backend:
  image: seu-usuario/quant-backend:2.5.0
  # Remover seção build

frontend:
  image: seu-usuario/quant-frontend:2.5.0
  # Remover seção build
```

```bash
docker-compose down
docker-compose pull
docker-compose up -d
```

---

### Solução 5: Instalar Dependências do Sistema

Garantir que todas as dependências estão instaladas:

```bash
sudo apt-get update
sudo apt-get install -y \
    gcc \
    g++ \
    make \
    build-essential \
    libpq-dev \
    postgresql-client \
    curl \
    git

# Verificar
gcc --version
g++ --version
```

Depois rebuild:
```bash
docker-compose down
docker-compose up -d --build
```

---

### Solução 6: Build Sem Cache

Forçar rebuild completo:

```bash
docker-compose down
docker system prune -a -f  # CUIDADO: Remove todas as imagens não usadas
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔧 Verificações

### 1. Verificar Logs Detalhados
```bash
# Ver logs do build
docker-compose build backend 2>&1 | tee build.log

# Ver últimas 100 linhas
tail -100 build.log
```

### 2. Verificar Recursos do EC2
```bash
# Memória
free -h

# Disco
df -h

# CPU
top
```

### 3. Verificar Conectividade
```bash
# Testar PyPI
curl -I https://pypi.org/

# Testar DNS
nslookup pypi.org
```

---

## 📋 Checklist de Troubleshooting

- [ ] Verificar tipo de instância EC2 (t2.micro? t2.small?)
- [ ] Verificar memória disponível (`free -h`)
- [ ] Verificar espaço em disco (`df -h`)
- [ ] Adicionar swap se necessário
- [ ] Usar Dockerfile.backend.ec2 otimizado
- [ ] Instalar dependências do sistema (gcc, g++, etc.)
- [ ] Verificar conectividade com PyPI
- [ ] Tentar build sem cache
- [ ] Considerar build local + push para registry

---

## 🎯 Solução Rápida (Copy & Paste)

Se você tem t2.micro ou t2.small, execute:

```bash
# 1. Adicionar swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 2. Instalar dependências
sudo apt-get update
sudo apt-get install -y gcc g++ make build-essential libpq-dev

# 3. Usar Dockerfile otimizado
cd /home/ubuntu/quant_stock_rank
cp docker-compose.yml docker-compose.yml.backup
sed -i 's|dockerfile: docker/Dockerfile.backend|dockerfile: docker/Dockerfile.backend.ec2|g' docker-compose.yml

# 4. Rebuild
docker-compose down
docker-compose up -d --build

# 5. Verificar
docker-compose ps
docker-compose logs backend
```

---

## 📞 Se Nada Funcionar

**Opção A: Upgrade da Instância EC2**
- t2.micro → t2.small (2GB RAM)
- t2.small → t2.medium (4GB RAM)

**Opção B: Build Local + Docker Hub**
- Build no seu computador
- Push para Docker Hub
- Pull no EC2

**Opção C: Usar Imagens Pré-construídas**
- Criar imagens otimizadas
- Hospedar no Docker Hub
- Usar no EC2

---

## 📝 Logs Úteis

```bash
# Logs do build
docker-compose build backend 2>&1 | tee build.log

# Logs do container
docker-compose logs backend

# Logs do sistema
dmesg | tail -50

# Uso de memória durante build
watch -n 1 free -h
```

---

**Última Atualização**: 2026-02-25  
**Versão**: 2.5.0
