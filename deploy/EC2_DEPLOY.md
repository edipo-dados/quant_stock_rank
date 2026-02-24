# Deploy no AWS EC2

## Pré-requisitos

1. Instância EC2 com Ubuntu 22.04 ou superior
2. Docker e Docker Compose instalados
3. Portas abertas no Security Group:
   - 8000 (Backend API)
   - 8501 (Frontend Streamlit)
   - 5432 (PostgreSQL - opcional, apenas se quiser acesso externo)

## Passo 1: Instalar Docker e Docker Compose

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo apt install docker-compose-plugin -y

# Verificar instalação
docker --version
docker compose version
```

## Passo 2: Clonar o Repositório

```bash
# Clonar repositório
git clone https://github.com/edipo-dados/quant_stock_rank.git
cd quant_stock_rank
```

## Passo 3: Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de produção
cp .env.production .env

# Editar variáveis (IMPORTANTE: mudar senha do banco!)
nano .env
```

Configurações importantes no `.env`:

```bash
# Database - USE SENHA FORTE!
POSTGRES_USER=quant_user
POSTGRES_PASSWORD=SUA_SENHA_FORTE_AQUI
POSTGRES_DB=quant_ranker
DATABASE_URL=postgresql://quant_user:SUA_SENHA_FORTE_AQUI@postgres:5432/quant_ranker

# API Key do Gemini
GEMINI_API_KEY=sua_chave_aqui

# URLs
BACKEND_URL=http://backend:8000
```

## Passo 4: Subir a Aplicação

```bash
# Construir imagens
docker compose build

# Subir containers
docker compose up -d

# Verificar status
docker compose ps

# Ver logs
docker compose logs -f
```

## Passo 5: Inicializar Banco de Dados

```bash
# Executar script de inicialização
docker exec quant-ranker-backend python scripts/init_db.py

# Verificar tabelas criadas
docker exec quant-ranker-backend python scripts/check_db.py
```

## Passo 6: Executar Pipeline Inicial

```bash
# Executar pipeline com ativos líquidos (modo full)
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full"

# Verificar execução
docker exec quant-ranker-backend python scripts/check_pipeline_history.py
```

## Passo 7: Configurar Nginx (Opcional - Recomendado)

```bash
# Instalar Nginx
sudo apt install nginx -y

# Criar configuração
sudo nano /etc/nginx/sites-available/quant-ranker
```

Conteúdo do arquivo:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;  # ou IP público

    # Frontend Streamlit
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Ativar site
sudo ln -s /etc/nginx/sites-available/quant-ranker /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

## Passo 8: Configurar SSL com Let's Encrypt (Opcional)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter certificado
sudo certbot --nginx -d seu-dominio.com

# Renovação automática já está configurada
```

## Comandos Úteis

### Gerenciar Containers

```bash
# Ver logs
docker compose logs -f backend
docker compose logs -f frontend

# Reiniciar serviços
docker compose restart backend
docker compose restart frontend

# Parar tudo
docker compose down

# Parar e remover volumes (CUIDADO: apaga dados!)
docker compose down -v
```

### Backup do Banco de Dados

```bash
# Criar backup
docker exec quant-ranker-db pg_dump -U quant_user quant_ranker > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
cat backup_20260224_120000.sql | docker exec -i quant-ranker-db psql -U quant_user quant_ranker
```

### Atualizar Aplicação

```bash
# Puxar últimas mudanças
git pull

# Reconstruir e reiniciar
docker compose build
docker compose up -d

# Verificar
docker compose ps
```

### Executar Pipeline Manualmente

```bash
# Modo incremental (atualização diária)
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 50"

# Modo full (recalcular tudo)
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full"
```

### Monitoramento

```bash
# Ver uso de recursos
docker stats

# Ver logs em tempo real
docker compose logs -f --tail 100

# Verificar saúde dos containers
docker compose ps
```

## Troubleshooting

### Erro: "database does not exist"

```bash
# Verificar variáveis de ambiente
docker compose config

# Recriar banco
docker compose down
docker volume rm quant_stock_rank_postgres_data
docker compose up -d
docker exec quant-ranker-backend python scripts/init_db.py
```

### Erro: "Connection refused" no frontend

```bash
# Verificar se backend está rodando
docker compose ps

# Ver logs do backend
docker compose logs backend

# Reiniciar backend
docker compose restart backend
```

### Frontend não carrega

```bash
# Ver logs
docker compose logs frontend

# Verificar se porta 8501 está aberta
sudo netstat -tlnp | grep 8501

# Reiniciar frontend
docker compose restart frontend
```

### Pipeline falha com rate limiting

```bash
# Ajustar configurações no script
# Editar scripts/run_pipeline_docker.py
# Aumentar SLEEP_BETWEEN_TICKERS e SLEEP_BETWEEN_BATCHES
```

## Segurança

1. **Mudar senhas padrão** no `.env`
2. **Configurar firewall** (UFW):
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```
3. **Não expor porta 5432** (PostgreSQL) publicamente
4. **Usar SSL/HTTPS** em produção
5. **Manter sistema atualizado**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

## Automação com Cron

Para executar o pipeline automaticamente todos os dias:

```bash
# Editar crontab
crontab -e

# Adicionar linha (executa às 6h da manhã)
0 6 * * * cd /home/ubuntu/quant_stock_rank && docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 50" >> /home/ubuntu/pipeline.log 2>&1
```

## Monitoramento de Logs

```bash
# Configurar logrotate
sudo nano /etc/logrotate.d/quant-ranker
```

Conteúdo:

```
/home/ubuntu/pipeline.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## Recursos da Instância EC2

Recomendações mínimas:
- **Tipo**: t3.medium ou superior
- **vCPUs**: 2
- **RAM**: 4 GB
- **Storage**: 20 GB SSD
- **Sistema**: Ubuntu 22.04 LTS

Para produção com muitos ativos:
- **Tipo**: t3.large ou superior
- **vCPUs**: 4
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
