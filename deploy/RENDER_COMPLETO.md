# 🚀 Deploy Completo no Render - Guia Passo a Passo

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Visão Geral do Deploy](#visão-geral-do-deploy)
3. [Passo 1: Preparar o Repositório](#passo-1-preparar-o-repositório)
4. [Passo 2: Criar Conta no Render](#passo-2-criar-conta-no-render)
5. [Passo 3: Criar Banco de Dados PostgreSQL](#passo-3-criar-banco-de-dados-postgresql)
6. [Passo 4: Deploy do Backend (FastAPI)](#passo-4-deploy-do-backend-fastapi)
7. [Passo 5: Deploy do Frontend (Streamlit)](#passo-5-deploy-do-frontend-streamlit)
8. [Passo 6: Configurar Pipeline Automático](#passo-6-configurar-pipeline-automático)
9. [Passo 7: Testar a Aplicação](#passo-7-testar-a-aplicação)
10. [Troubleshooting](#troubleshooting)
11. [Custos e Planos](#custos-e-planos)

---

## ✅ Pré-requisitos

Antes de começar, você precisa ter:

- [ ] Conta no GitHub com seu repositório
- [ ] Código commitado e pushed para o GitHub
- [ ] Cartão de crédito (para planos pagos) ou usar free tier
- [ ] 30-45 minutos de tempo disponível

---

## 🎯 Visão Geral do Deploy

Vamos criar 3 serviços no Render:

```
┌─────────────────────────────────────────────┐
│           RENDER DASHBOARD                  │
├─────────────────────────────────────────────┤
│                                             │
│  1. PostgreSQL Database                     │
│     └─ quant-ranker-db                      │
│                                             │
│  2. Backend Web Service (FastAPI)           │
│     └─ quant-ranker-backend                 │
│     └─ URL: https://quant-ranker-backend... │
│                                             │
│  3. Frontend Web Service (Streamlit)        │
│     └─ quant-ranker-frontend                │
│     └─ URL: https://quant-ranker-frontend...│
│                                             │
└─────────────────────────────────────────────┘
```

**Tempo estimado:** 30-45 minutos  
**Custo estimado:** $7-25/mês (ou free tier com limitações)

---

## 📦 Passo 1: Preparar o Repositório

### 1.1 Criar arquivos de configuração para Render

Vamos criar arquivos específicos para o Render funcionar corretamente.

#### Criar `render.yaml` (Blueprint)

Este arquivo permite deploy automático de todos os serviços de uma vez.

```yaml
# render.yaml
services:
  # Backend API
  - type: web
    name: quant-ranker-backend
    env: docker
    dockerfilePath: ./docker/Dockerfile.backend
    dockerContext: .
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: quant-ranker-db
          property: connectionString
      - key: MOMENTUM_WEIGHT
        value: "0.4"
      - key: QUALITY_WEIGHT
        value: "0.3"
      - key: VALUE_WEIGHT
        value: "0.3"
      - key: LOG_LEVEL
        value: "INFO"
      - key: API_HOST
        value: "0.0.0.0"
      - key: API_PORT
        value: "8000"
    healthCheckPath: /health

  # Frontend Streamlit
  - type: web
    name: quant-ranker-frontend
    env: docker
    dockerfilePath: ./docker/Dockerfile.frontend
    dockerContext: .
    envVars:
      - key: BACKEND_URL
        fromService:
          type: web
          name: quant-ranker-backend
          envVarKey: RENDER_EXTERNAL_URL
      - key: FRONTEND_PORT
        value: "8501"

databases:
  - name: quant-ranker-db
    databaseName: quant_ranker
    user: quant_user
    plan: starter  # ou 'free' para free tier
```

#### Criar `Dockerfile.backend` otimizado para Render

```dockerfile
# docker/Dockerfile.backend
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY app/ ./app/
COPY scripts/ ./scripts/

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Comando de inicialização
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Criar `Dockerfile.frontend` otimizado para Render

```dockerfile
# docker/Dockerfile.frontend
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código do frontend
COPY frontend/ ./frontend/
COPY .streamlit/ ./.streamlit/

# Expor porta
EXPOSE 8501

# Comando de inicialização
CMD ["streamlit", "run", "frontend/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 1.2 Commit e Push

```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

---

## 🌐 Passo 2: Criar Conta no Render

### 2.1 Acessar Render

1. Acesse: https://render.com
2. Clique em **"Get Started"** ou **"Sign Up"**

### 2.2 Fazer Login com GitHub

1. Escolha **"Sign up with GitHub"**
2. Autorize o Render a acessar seus repositórios
3. Você será redirecionado para o Dashboard

### 2.3 Verificar Email (se necessário)

- Verifique seu email e confirme a conta

---

## 🗄️ Passo 3: Criar Banco de Dados PostgreSQL

### 3.1 Criar Database

1. No Dashboard do Render, clique em **"New +"**
2. Selecione **"PostgreSQL"**

### 3.2 Configurar Database

Preencha os campos:

```
Name: quant-ranker-db
Database: quant_ranker
User: quant_user
Region: Oregon (US West) ou Frankfurt (Europe) - escolha o mais próximo
```

### 3.3 Escolher Plano

**Opção 1: Free Tier** (Limitado)
- ✅ Grátis
- ❌ Expira após 90 dias
- ❌ Sem backups automáticos
- ❌ Conexões limitadas

**Opção 2: Starter ($7/mês)** ⭐ RECOMENDADO
- ✅ Sem expiração
- ✅ Backups automáticos diários
- ✅ 1 GB de armazenamento
- ✅ Conexões ilimitadas

**Opção 3: Standard ($20/mês)**
- ✅ Tudo do Starter
- ✅ 10 GB de armazenamento
- ✅ Alta disponibilidade

### 3.4 Criar Database

1. Clique em **"Create Database"**
2. Aguarde 2-3 minutos para provisionar
3. Quando estiver pronto, você verá status **"Available"**

### 3.5 Copiar Credenciais

Na página do database, você verá:

```
Internal Database URL: postgresql://quant_user:xxxxx@dpg-xxxxx/quant_ranker
External Database URL: postgresql://quant_user:xxxxx@dpg-xxxxx-a.oregon-postgres.render.com/quant_ranker
```

**IMPORTANTE:** Copie a **Internal Database URL** - vamos usar ela nos próximos passos.

---

## 🔧 Passo 4: Deploy do Backend (FastAPI)

### 4.1 Criar Web Service

1. No Dashboard, clique em **"New +"**
2. Selecione **"Web Service"**

### 4.2 Conectar Repositório

1. Clique em **"Connect a repository"**
2. Se for a primeira vez, autorize o Render a acessar seus repos
3. Encontre e selecione seu repositório: **"Recomendacoes_financeiras"**
4. Clique em **"Connect"**

### 4.3 Configurar Service

Preencha os campos:

```
Name: quant-ranker-backend
Region: Oregon (US West) - mesmo do database
Branch: main
Root Directory: (deixe vazio)
Environment: Docker
Dockerfile Path: ./docker/Dockerfile.backend
Docker Context: .
```

### 4.4 Escolher Plano

**Opção 1: Free Tier**
- ✅ Grátis
- ❌ Dorme após 15 min de inatividade
- ❌ 750 horas/mês (suficiente para 1 serviço)
- ❌ Lento para acordar (cold start)

**Opção 2: Starter ($7/mês)** ⭐ RECOMENDADO
- ✅ Sempre ativo
- ✅ 512 MB RAM
- ✅ 0.5 CPU
- ✅ Sem cold starts

**Opção 3: Standard ($25/mês)**
- ✅ 2 GB RAM
- ✅ 1 CPU
- ✅ Melhor performance

### 4.5 Configurar Variáveis de Ambiente

Role até **"Environment Variables"** e adicione:

```bash
# Database
DATABASE_URL = <cole a Internal Database URL do Passo 3.5>

# Scoring Weights
MOMENTUM_WEIGHT = 0.4
QUALITY_WEIGHT = 0.3
VALUE_WEIGHT = 0.3

# API Configuration
API_HOST = 0.0.0.0
API_PORT = 8000
LOG_LEVEL = INFO

# PostgreSQL (para referência)
POSTGRES_USER = quant_user
POSTGRES_DB = quant_ranker
```

### 4.6 Configurar Health Check

Em **"Health Check Path"**, adicione:
```
/health
```

### 4.7 Criar Service

1. Clique em **"Create Web Service"**
2. O Render começará a fazer o build
3. Aguarde 5-10 minutos para o primeiro deploy

### 4.8 Verificar Deploy

Você verá logs em tempo real:

```
==> Building...
==> Deploying...
==> Your service is live 🎉
```

Quando terminar, você terá uma URL tipo:
```
https://quant-ranker-backend.onrender.com
```

### 4.9 Testar Backend

Abra no navegador:
```
https://quant-ranker-backend.onrender.com/health
```

Deve retornar:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## 🎨 Passo 5: Deploy do Frontend (Streamlit)

### 5.1 Criar Web Service para Frontend

1. No Dashboard, clique em **"New +"**
2. Selecione **"Web Service"**
3. Conecte o mesmo repositório

### 5.2 Configurar Service

```
Name: quant-ranker-frontend
Region: Oregon (US West) - mesmo do backend
Branch: main
Root Directory: (deixe vazio)
Environment: Docker
Dockerfile Path: ./docker/Dockerfile.frontend
Docker Context: .
```

### 5.3 Escolher Plano

Recomendo o mesmo plano do backend (Starter $7/mês ou Free).

### 5.4 Configurar Variáveis de Ambiente

```bash
# Backend URL - IMPORTANTE: use a URL do seu backend
BACKEND_URL = https://quant-ranker-backend.onrender.com

# Frontend Port
FRONTEND_PORT = 8501
```

**ATENÇÃO:** Substitua `quant-ranker-backend.onrender.com` pela URL real do seu backend (do Passo 4.8).

### 5.5 Criar Service

1. Clique em **"Create Web Service"**
2. Aguarde 5-10 minutos para o build

### 5.6 Verificar Deploy

Quando terminar, você terá uma URL tipo:
```
https://quant-ranker-frontend.onrender.com
```

### 5.7 Testar Frontend

Abra no navegador:
```
https://quant-ranker-frontend.onrender.com
```

Você deve ver a página inicial do sistema!

---

## ⚙️ Passo 6: Configurar Pipeline Automático

### 6.1 Criar Cron Job no Render

O Render permite criar Cron Jobs para executar tarefas agendadas.

1. No Dashboard, clique em **"New +"**
2. Selecione **"Cron Job"**

### 6.2 Configurar Cron Job

```
Name: quant-ranker-pipeline
Region: Oregon (US West)
Branch: main
Environment: Docker
Dockerfile Path: ./docker/Dockerfile.backend
Docker Context: .
Command: python -m scripts.run_pipeline --mode liquid
Schedule: 0 21 * * * (todo dia às 21h UTC = 18h BRT)
```

### 6.3 Adicionar Variáveis de Ambiente

Adicione as mesmas variáveis do backend (especialmente `DATABASE_URL`).

### 6.4 Criar Cron Job

Clique em **"Create Cron Job"**.

O pipeline rodará automaticamente todos os dias no horário configurado!

---

## ✅ Passo 7: Testar a Aplicação

### 7.1 Inicializar Banco de Dados

Primeiro, precisamos criar as tabelas no banco.

**Opção A: Via Render Shell**

1. Vá para o serviço **quant-ranker-backend**
2. Clique na aba **"Shell"**
3. Execute:
```bash
python scripts/init_db.py
```

**Opção B: Via Cron Job Manual**

1. Crie um Cron Job temporário com comando:
```bash
python scripts/init_db.py
```
2. Execute manualmente
3. Delete o Cron Job depois

### 7.2 Executar Pipeline Inicial

Para popular o banco com dados:

1. Vá para o Cron Job **quant-ranker-pipeline**
2. Clique em **"Trigger Run"** (executar manualmente)
3. Aguarde 5-10 minutos
4. Verifique os logs para confirmar sucesso

### 7.3 Testar API

Abra no navegador:

```
# Health check
https://quant-ranker-backend.onrender.com/health

# Ranking
https://quant-ranker-backend.onrender.com/api/v1/ranking

# Top 5
https://quant-ranker-backend.onrender.com/api/v1/top?limit=5
```

### 7.4 Testar Frontend

1. Abra: `https://quant-ranker-frontend.onrender.com`
2. Navegue para **"🏆 Ranking"** no menu lateral
3. Você deve ver a lista de ativos ranqueados!
4. Clique em um ativo para ver detalhes

---

## 🐛 Troubleshooting

### Problema 1: Backend não inicia

**Sintomas:** Logs mostram erro de conexão com banco

**Solução:**
1. Verifique se `DATABASE_URL` está correta
2. Use a **Internal Database URL**, não a External
3. Certifique-se que o database está "Available"

### Problema 2: Frontend não conecta ao Backend

**Sintomas:** Frontend carrega mas não mostra dados

**Solução:**
1. Verifique se `BACKEND_URL` no frontend está correto
2. Teste a URL do backend diretamente no navegador
3. Verifique logs do backend para erros CORS

### Problema 3: Build falha

**Sintomas:** "Build failed" nos logs

**Solução:**
1. Verifique se os Dockerfiles estão no caminho correto
2. Verifique se `requirements.txt` está completo
3. Veja os logs de build para erro específico

### Problema 4: Pipeline falha

**Sintomas:** Cron Job termina com erro

**Solução:**
1. Verifique se Yahoo Finance está acessível
2. Verifique se há dados no banco (tabelas criadas)
3. Execute `init_db.py` primeiro se necessário

### Problema 5: Free Tier dorme

**Sintomas:** Aplicação demora para responder

**Solução:**
- Free tier dorme após 15 min de inatividade
- Upgrade para Starter ($7/mês) para manter sempre ativo
- Ou use um serviço de ping (UptimeRobot) para manter acordado

### Problema 6: Erro de memória

**Sintomas:** "Out of memory" nos logs

**Solução:**
- Free tier tem apenas 512 MB RAM
- Upgrade para Standard ($25/mês) com 2 GB RAM
- Ou otimize o código para usar menos memória

---

## 💰 Custos e Planos

### Cenário 1: Free Tier (Teste/MVP)

```
PostgreSQL: Free (90 dias)
Backend: Free (com sleep)
Frontend: Free (com sleep)
Cron Job: Free (limitado)
────────────────────────
Total: $0/mês

Limitações:
- Services dormem após 15 min
- Database expira em 90 dias
- 750 horas/mês total
- Sem backups automáticos
```

### Cenário 2: Starter (Recomendado) ⭐

```
PostgreSQL Starter: $7/mês
Backend Starter: $7/mês
Frontend Starter: $7/mês
Cron Job: Grátis
────────────────────────
Total: $21/mês

Benefícios:
- Sempre ativo (sem sleep)
- Backups automáticos
- Sem expiração
- Performance decente
```

### Cenário 3: Production

```
PostgreSQL Standard: $20/mês
Backend Standard: $25/mês
Frontend Standard: $25/mês
Cron Job: Grátis
────────────────────────
Total: $70/mês

Benefícios:
- Alta performance
- Mais recursos
- Alta disponibilidade
- Escalável
```

### Dicas para Economizar

1. **Comece com Free Tier** para testar
2. **Upgrade apenas o que precisa** (ex: só o backend)
3. **Use Starter para produção pequena** (melhor custo-benefício)
4. **Monitore uso** no Dashboard do Render

---

## 🎉 Parabéns!

Sua aplicação está no ar! 🚀

### URLs Finais

```
Frontend: https://quant-ranker-frontend.onrender.com
Backend API: https://quant-ranker-backend.onrender.com
API Docs: https://quant-ranker-backend.onrender.com/docs
```

### Próximos Passos

1. ✅ Configurar domínio customizado (opcional)
2. ✅ Configurar monitoramento (UptimeRobot)
3. ✅ Configurar alertas de erro (Sentry)
4. ✅ Documentar URLs e credenciais
5. ✅ Testar pipeline automático

---

## 📞 Precisa de Ajuda?

Se tiver qualquer problema durante o deploy, me avise e eu te ajudo a resolver!

**Documentação Oficial do Render:**
- https://render.com/docs
- https://render.com/docs/docker
- https://render.com/docs/databases

