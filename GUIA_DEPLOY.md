# Guia Completo de Deploy - Sistema de Ranking Quantitativo

## 📋 Índice

1. [Visão Geral da Arquitetura](#visão-geral-da-arquitetura)
2. [Opções de Deploy](#opções-de-deploy)
3. [Deploy em Cloud (Recomendado)](#deploy-em-cloud)
4. [Deploy Local/VPS](#deploy-localvps)
5. [Configuração de Produção](#configuração-de-produção)
6. [Monitoramento e Manutenção](#monitoramento-e-manutenção)
7. [Custos Estimados](#custos-estimados)

---

## 🏗️ Visão Geral da Arquitetura

Sua aplicação possui 3 componentes principais:

```
┌─────────────────┐
│   Frontend      │  Streamlit (porta 8501)
│   (Streamlit)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Backend       │  FastAPI (porta 8000)
│   (FastAPI)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Database      │  PostgreSQL (porta 5432)
│  (PostgreSQL)   │
└─────────────────┘
```

**Características importantes:**
- Backend consome APIs externas (Yahoo Finance)
- Pipeline de dados executado periodicamente
- Banco de dados com histórico de preços e scores
- Interface web para visualização

---

## 🚀 Opções de Deploy

### Comparação Rápida

| Opção | Custo/mês | Complexidade | Escalabilidade | Recomendado para |
|-------|-----------|--------------|----------------|------------------|
| **Railway** | $5-20 | ⭐ Baixa | ⭐⭐ Média | Protótipos, MVP |
| **Render** | $7-25 | ⭐ Baixa | ⭐⭐ Média | Startups, pequenos projetos |
| **Fly.io** | $0-30 | ⭐⭐ Média | ⭐⭐⭐ Alta | Projetos sérios |
| **AWS (ECS)** | $30-100 | ⭐⭐⭐ Alta | ⭐⭐⭐⭐ Muito Alta | Produção enterprise |
| **DigitalOcean** | $12-50 | ⭐⭐ Média | ⭐⭐⭐ Alta | Projetos médios |
| **VPS Manual** | $5-20 | ⭐⭐⭐ Alta | ⭐⭐ Média | Controle total |

---

## ☁️ Deploy em Cloud

### Opção 1: Railway (Mais Fácil) ⭐ RECOMENDADO PARA COMEÇAR

**Vantagens:**
- Deploy automático via Git
- Interface super simples
- PostgreSQL incluído
- SSL/HTTPS automático
- $5 de crédito grátis

**Passo a passo:**

1. **Criar conta no Railway**
   ```bash
   # Acesse: https://railway.app
   # Faça login com GitHub
   ```

2. **Criar novo projeto**
   - Clique em "New Project"
   - Selecione "Deploy from GitHub repo"
   - Conecte seu repositório

3. **Adicionar PostgreSQL**
   - No projeto, clique em "+ New"
   - Selecione "Database" → "PostgreSQL"
   - Railway criará automaticamente

4. **Configurar variáveis de ambiente**
   ```bash
   # No painel do Railway, adicione:
   DATABASE_URL=<gerado automaticamente pelo Railway>
   FMP_API_KEY=sua_chave_aqui
   MOMENTUM_WEIGHT=0.4
   QUALITY_WEIGHT=0.3
   VALUE_WEIGHT=0.3
   ```

5. **Deploy automático**
   - Railway detecta o `docker-compose.yml`
   - Deploy acontece automaticamente a cada push

**Custo estimado:** $5-15/mês

---

### Opção 2: Render (Alternativa Simples)

**Vantagens:**
- Free tier generoso
- PostgreSQL gerenciado
- Deploy automático
- SSL incluído

**Passo a passo:**

1. **Criar conta no Render**
   ```bash
   # Acesse: https://render.com
   ```

2. **Criar PostgreSQL Database**
   - Dashboard → New → PostgreSQL
   - Escolha o plano (Free ou Starter $7/mês)
   - Copie a `Internal Database URL`

3. **Criar Web Service para Backend**
   - New → Web Service
   - Conecte seu repositório
   - Configurações:
     ```
     Name: quant-ranker-backend
     Environment: Docker
     Docker Command: (deixe vazio, usa docker-compose)
     ```

4. **Criar Web Service para Frontend**
   - Repita o processo
   - Nome: quant-ranker-frontend

5. **Configurar variáveis de ambiente**
   - Em cada serviço, adicione as variáveis necessárias

**Custo estimado:** $7-25/mês

---

### Opção 3: Fly.io (Melhor Custo-Benefício)

**Vantagens:**
- Free tier com 3 VMs
- Deploy global (edge computing)
- Excelente performance
- PostgreSQL incluído

**Passo a passo:**

1. **Instalar Fly CLI**
   ```bash
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   
   # Ou baixe de: https://fly.io/docs/hands-on/install-flyctl/
   ```

2. **Login e criar app**
   ```bash
   fly auth login
   fly launch
   ```

3. **Configurar PostgreSQL**
   ```bash
   fly postgres create
   fly postgres attach <postgres-app-name>
   ```

4. **Deploy**
   ```bash
   fly deploy
   ```

**Custo estimado:** $0-30/mês (free tier disponível)

---

### Opção 4: AWS ECS (Produção Enterprise)

**Vantagens:**
- Máxima escalabilidade
- Integração com outros serviços AWS
- Alta disponibilidade
- Controle total

**Arquitetura recomendada:**
```
Internet → ALB → ECS Fargate (Backend + Frontend) → RDS PostgreSQL
                                                   → CloudWatch (logs)
                                                   → S3 (backups)
```

**Passo a passo resumido:**

1. **Criar RDS PostgreSQL**
2. **Criar ECR repositories** (para imagens Docker)
3. **Criar ECS Cluster** (Fargate)
4. **Criar Task Definitions**
5. **Criar Services**
6. **Configurar ALB** (Application Load Balancer)
7. **Configurar Route53** (DNS)

**Custo estimado:** $30-100/mês

---

### Opção 5: DigitalOcean App Platform

**Vantagens:**
- Interface simples
- PostgreSQL gerenciado
- Preço previsível
- Boa documentação

**Passo a passo:**

1. **Criar conta no DigitalOcean**
   ```bash
   # Acesse: https://www.digitalocean.com
   ```

2. **Criar App**
   - Apps → Create App
   - Conecte GitHub
   - Selecione repositório

3. **Adicionar Database**
   - Add Resource → Database
   - PostgreSQL

4. **Configurar componentes**
   - Backend: Web Service (porta 8000)
   - Frontend: Web Service (porta 8501)

**Custo estimado:** $12-50/mês

---

## 🖥️ Deploy Local/VPS

### Opção 6: VPS Manual (Controle Total)

**Recomendado para:** Quem quer controle total e custos baixos

**Provedores sugeridos:**
- **Contabo:** €4-8/mês (melhor custo-benefício)
- **Hetzner:** €4-10/mês (excelente na Europa)
- **DigitalOcean Droplet:** $6-12/mês
- **Vultr:** $6-12/mês
- **Linode:** $5-10/mês

**Passo a passo completo:**

#### 1. Provisionar VPS

```bash
# Especificações mínimas recomendadas:
# - 2 vCPUs
# - 4 GB RAM
# - 50 GB SSD
# - Ubuntu 22.04 LTS
```

#### 2. Configurar servidor

```bash
# Conectar via SSH
ssh root@seu-ip

# Atualizar sistema
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose
apt install docker-compose-plugin -y

# Criar usuário não-root
adduser deploy
usermod -aG docker deploy
usermod -aG sudo deploy

# Configurar firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

#### 3. Clonar repositório

```bash
# Trocar para usuário deploy
su - deploy

# Clonar projeto
git clone https://github.com/seu-usuario/seu-repo.git
cd seu-repo

# Criar arquivo .env
cp .env.example .env
nano .env  # Editar com suas configurações
```

#### 4. Deploy com Docker Compose

```bash
# Build e iniciar
docker compose up -d --build

# Verificar logs
docker compose logs -f

# Verificar status
docker compose ps
```

#### 5. Configurar Nginx como Reverse Proxy

```bash
# Instalar Nginx
sudo apt install nginx -y

# Criar configuração
sudo nano /etc/nginx/sites-available/quant-ranker
```

Adicione:

```nginx
# Frontend
server {
    listen 80;
    server_name seu-dominio.com;

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
}

# Backend API
server {
    listen 80;
    server_name api.seu-dominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Ativar configuração
sudo ln -s /etc/nginx/sites-available/quant-ranker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. Configurar SSL com Let's Encrypt

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter certificados
sudo certbot --nginx -d seu-dominio.com -d api.seu-dominio.com

# Renovação automática já está configurada
```

#### 7. Configurar Cron para Pipeline

```bash
# Editar crontab
crontab -e

# Adicionar linha para executar pipeline diariamente às 18h
0 18 * * * cd /home/deploy/seu-repo && docker compose exec -T backend python scripts/run_pipeline.py --mode liquid >> /home/deploy/logs/pipeline.log 2>&1
```

**Custo estimado:** $5-20/mês

---

## ⚙️ Configuração de Produção

### Arquivo .env para Produção

```bash
# Database (use PostgreSQL em produção)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# API Keys
FMP_API_KEY=sua_chave_real_aqui

# Scoring Weights
MOMENTUM_WEIGHT=0.4
QUALITY_WEIGHT=0.3
VALUE_WEIGHT=0.3

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Frontend
FRONTEND_PORT=8501
BACKEND_URL=http://backend:8000  # Ou URL pública da API

# PostgreSQL
POSTGRES_USER=quant_user
POSTGRES_PASSWORD=senha_forte_aqui
POSTGRES_DB=quant_ranker
POSTGRES_PORT=5432

# Security (adicione em produção)
SECRET_KEY=gere_uma_chave_secreta_forte
ALLOWED_HOSTS=seu-dominio.com,api.seu-dominio.com
CORS_ORIGINS=https://seu-dominio.com
```

### Melhorias de Segurança

1. **Usar secrets management**
   ```bash
   # AWS Secrets Manager, HashiCorp Vault, etc.
   ```

2. **Configurar rate limiting**
   ```python
   # No FastAPI, adicionar middleware
   from slowapi import Limiter
   ```

3. **Habilitar HTTPS apenas**
   ```nginx
   # Redirecionar HTTP para HTTPS
   ```

4. **Configurar backup automático do banco**
   ```bash
   # Cron job para pg_dump
   ```

---

## 📊 Monitoramento e Manutenção

### Logs

```bash
# Docker Compose
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres

# Logs do pipeline
tail -f logs/pipeline.log
```

### Health Checks

```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:8501/_stcore/health

# Database
docker compose exec postgres pg_isready
```

### Backup do Banco de Dados

```bash
# Backup manual
docker compose exec postgres pg_dump -U quant_user quant_ranker > backup_$(date +%Y%m%d).sql

# Restaurar backup
docker compose exec -T postgres psql -U quant_user quant_ranker < backup_20260220.sql
```

### Monitoramento Recomendado

1. **Uptime monitoring:** UptimeRobot (grátis)
2. **Application monitoring:** Sentry (grátis até 5k eventos/mês)
3. **Logs:** Papertrail ou Logtail
4. **Métricas:** Prometheus + Grafana (se VPS próprio)

---

## 💰 Custos Estimados

### Comparação Detalhada

| Provedor | Setup | Mensal | Anual | Inclui |
|----------|-------|--------|-------|--------|
| **Railway** | Grátis | $5-15 | $60-180 | DB, SSL, Deploy auto |
| **Render** | Grátis | $7-25 | $84-300 | DB, SSL, Deploy auto |
| **Fly.io** | Grátis | $0-30 | $0-360 | DB, SSL, Edge |
| **DigitalOcean** | Grátis | $12-50 | $144-600 | DB gerenciado |
| **AWS ECS** | Grátis | $30-100 | $360-1200 | Tudo AWS |
| **VPS (Contabo)** | Grátis | €4-8 | €48-96 | Servidor apenas |
| **VPS (Hetzner)** | Grátis | €4-10 | €48-120 | Servidor apenas |

### Custos Adicionais

- **Domínio:** $10-15/ano
- **Monitoramento:** $0-20/mês (muitos têm free tier)
- **Backups:** $0-5/mês
- **CDN (opcional):** $0-10/mês

---

## 🎯 Recomendação Final

### Para Começar (MVP/Teste)
**→ Railway ou Fly.io**
- Mais fácil de configurar
- Deploy em minutos
- Custo baixo inicial

### Para Produção (Pequeno/Médio)
**→ DigitalOcean App Platform ou Render**
- Bom equilíbrio preço/facilidade
- Escalável
- Suporte decente

### Para Produção (Grande Escala)
**→ AWS ECS ou Kubernetes**
- Máxima escalabilidade
- Controle total
- Integração com outros serviços

### Para Máximo Controle e Custo Mínimo
**→ VPS (Contabo/Hetzner) + Docker**
- Custo muito baixo
- Controle total
- Requer conhecimento técnico

---

## 📝 Próximos Passos

1. **Escolher provedor** baseado em suas necessidades
2. **Configurar domínio** (opcional mas recomendado)
3. **Fazer deploy inicial** seguindo o guia do provedor escolhido
4. **Configurar monitoramento** (UptimeRobot mínimo)
5. **Configurar backups automáticos** do banco
6. **Testar pipeline** em produção
7. **Documentar** URLs e credenciais

---

## 🆘 Suporte

Se precisar de ajuda com alguma opção específica, me avise qual provedor você escolheu e posso criar um guia detalhado passo a passo!
