# Setup Novo EC2 - Passo a Passo

## 1. CONECTAR AO SERVIDOR

```bash
ssh -i sua-chave.pem ubuntu@IP_DO_SERVIDOR
```

---

## 2. ATUALIZAR SISTEMA

```bash
sudo apt update
sudo apt upgrade -y
```

---

## 3. INSTALAR DOCKER

Copie e cole tudo de uma vez:

```bash
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io
sudo usermod -aG docker ubuntu
newgrp docker
```

Verificar:
```bash
docker --version
```

---

## 4. INSTALAR DOCKER COMPOSE

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

Verificar:
```bash
docker-compose --version
```

---

## 5. INSTALAR GIT

```bash
sudo apt install -y git
```

---

## 6. CLONAR REPOSITÓRIO

```bash
cd ~
git clone https://github.com/edipo-dados/quant_stock_rank.git
cd quant_stock_rank
```

---

## 7. CONFIGURAR AMBIENTE

```bash
nano .env.production
```

Cole este conteúdo (ajuste suas chaves):

```
DATABASE_URL=postgresql://quant_user:quant_password@postgres:5432/quant_ranker
POSTGRES_USER=quant_user
POSTGRES_PASSWORD=quant_password
POSTGRES_DB=quant_ranker
FMP_API_KEY=SUA_CHAVE_AQUI
GEMINI_API_KEY=SUA_CHAVE_AQUI
MOMENTUM_WEIGHT=0.4
QUALITY_WEIGHT=0.3
VALUE_WEIGHT=0.3
ENVIRONMENT=production
```

Salvar: `Ctrl+O`, Enter, `Ctrl+X`

---

## 8. SUBIR APLICAÇÃO

```bash
docker-compose build --no-cache
docker-compose up -d
```

---

## 9. VERIFICAR

```bash
docker-compose ps
```

Deve mostrar 3 containers rodando.

Ver logs:
```bash
docker logs quant-ranker-backend --tail 50
```

---

## 10. TESTAR

```bash
curl http://localhost:8000/health
```

Abrir no navegador:
```
http://IP_DO_SERVIDOR:8501
```

---

## PRONTO! 🎉

Sua aplicação está rodando.

---

## COMANDOS ÚTEIS

### Ver logs
```bash
docker logs -f quant-ranker-backend
docker logs -f quant-ranker-frontend
```

### Restart
```bash
docker-compose restart
```

### Stop/Start
```bash
docker-compose down
docker-compose up -d
```

### Atualizar código
```bash
cd ~/quant_stock_rank
git pull
docker-compose build --no-cache
docker-compose down
docker-compose up -d
```

### Executar pipeline
```bash
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode test"
```

---

## SE TIVER BACKUP DO BANCO ANTIGO

### Copiar backup para novo servidor
```bash
# No seu computador
scp -i sua-chave.pem ~/Downloads/backup.sql ubuntu@IP_NOVO:~/
```

### Restaurar
```bash
# No servidor novo
cat ~/backup.sql | docker exec -i quant-ranker-db psql -U quant_user -d quant_ranker
```

### Verificar
```bash
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "SELECT COUNT(*) FROM scores_daily;"
```

---

## PROBLEMAS?

### Containers não sobem
```bash
docker-compose logs
docker-compose down -v
docker system prune -a
docker-compose up -d
```

### Porta em uso
```bash
sudo netstat -tulpn | grep -E '8000|8501|5432'
```

### Banco não conecta
```bash
docker logs quant-ranker-db
docker exec quant-ranker-db pg_isready -U quant_user
```
