# Deploy no Railway - Guia Passo a Passo

## 🚂 Railway - Deploy Mais Fácil

Railway é a opção mais simples para fazer deploy da sua aplicação. Este guia detalha cada passo.

---

## 📋 Pré-requisitos

- [ ] Conta no GitHub
- [ ] Repositório Git do projeto
- [ ] Chave da API do Yahoo Finance (se necessário)

---

## 🚀 Passo a Passo

### 1. Criar Conta no Railway

1. Acesse: https://railway.app
2. Clique em "Login"
3. Escolha "Login with GitHub"
4. Autorize o Railway a acessar seus repositórios

**Créditos grátis:** Railway oferece $5 de crédito mensal no plano gratuito.

---

### 2. Criar Novo Projeto

1. No dashboard do Railway, clique em **"New Project"**
2. Selecione **"Deploy from GitHub repo"**
3. Escolha o repositório do seu projeto
4. Railway detectará automaticamente o `docker-compose.yml`

---

### 3. Adicionar PostgreSQL

1. No projeto criado, clique no botão **"+ New"**
2. Selecione **"Database"**
3. Escolha **"Add PostgreSQL"**
4. Railway criará automaticamente um banco PostgreSQL

**Importante:** Railway gera automaticamente a variável `DATABASE_URL` e a injeta nos seus serviços.

---

### 4. Configurar Variáveis de Ambiente

#### 4.1. Acessar Configurações

1. Clique no serviço **backend** (ou o nome do seu serviço principal)
2. Vá para a aba **"Variables"**

#### 4.2. Adicionar Variáveis

Adicione as seguintes variáveis:

```bash
# API Keys
FMP_API_KEY=sua_chave_aqui

# Scoring Weights (opcional, já tem defaults)
MOMENTUM_WEIGHT=0.4
QUALITY_WEIGHT=0.3
VALUE_WEIGHT=0.3

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Frontend Configuration
FRONTEND_PORT=8501
```

**Nota:** A variável `DATABASE_URL` é criada automaticamente pelo Railway quando você adiciona o PostgreSQL.

#### 4.3. Configurar Backend URL no Frontend

1. Clique no serviço **frontend**
2. Vá para **"Variables"**
3. Adicione:

```bash
BACKEND_URL=https://seu-backend.railway.app
```

**Importante:** Você precisa pegar a URL pública do backend primeiro (veja próximo passo).

---

### 5. Obter URLs Públicas

#### 5.1. Gerar URL Pública para Backend

1. Clique no serviço **backend**
2. Vá para a aba **"Settings"**
3. Role até **"Networking"**
4. Clique em **"Generate Domain"**
5. Railway gerará uma URL como: `seu-backend.railway.app`

#### 5.2. Gerar URL Pública para Frontend

1. Repita o processo para o serviço **frontend**
2. URL será algo como: `seu-frontend.railway.app`

#### 5.3. Atualizar BACKEND_URL

1. Volte nas variáveis do **frontend**
2. Atualize `BACKEND_URL` com a URL real do backend
3. Exemplo: `BACKEND_URL=https://quant-ranker-backend.railway.app`

---

### 6. Deploy Automático

Railway faz deploy automaticamente quando você:
- Faz push para o branch principal (main/master)
- Altera variáveis de ambiente
- Clica em "Redeploy"

**Acompanhar deploy:**
1. Clique no serviço
2. Vá para a aba **"Deployments"**
3. Veja os logs em tempo real

---

### 7. Verificar Aplicação

#### 7.1. Testar Backend

```bash
# Substitua pela sua URL
curl https://seu-backend.railway.app/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

#### 7.2. Testar Frontend

Acesse no navegador:
```
https://seu-frontend.railway.app
```

Você deve ver a interface do Streamlit.

---

### 8. Executar Pipeline Inicial

#### 8.1. Via Railway CLI (Recomendado)

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Conectar ao projeto
railway link

# Executar pipeline
railway run python scripts/run_pipeline.py --mode liquid
```

#### 8.2. Via Interface Web

1. No serviço backend, vá para **"Settings"**
2. Role até **"Deploy"**
3. Em **"Custom Start Command"**, adicione:

```bash
sh -c "python scripts/init_db.py && python scripts/run_pipeline.py --mode liquid && uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

Isso executará o pipeline na inicialização.

---

### 9. Configurar Domínio Customizado (Opcional)

#### 9.1. Adicionar Domínio

1. No serviço, vá para **"Settings"**
2. Role até **"Networking"**
3. Em **"Custom Domain"**, clique em **"Add Domain"**
4. Digite seu domínio: `app.seudominio.com`

#### 9.2. Configurar DNS

No seu provedor de domínio (GoDaddy, Namecheap, etc.):

```
Tipo: CNAME
Nome: app
Valor: seu-projeto.railway.app
TTL: 3600
```

Railway configurará SSL automaticamente.

---

### 10. Configurar Cron Job para Pipeline

Railway não tem cron jobs nativos, mas você pode usar:

#### Opção A: GitHub Actions (Recomendado)

Crie `.github/workflows/daily-pipeline.yml`:

```yaml
name: Daily Pipeline

on:
  schedule:
    - cron: '0 18 * * *'  # 18h UTC diariamente
  workflow_dispatch:  # Permite execução manual

jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Railway Pipeline
        run: |
          curl -X POST https://seu-backend.railway.app/api/v1/pipeline/run \
            -H "Authorization: Bearer ${{ secrets.API_TOKEN }}"
```

#### Opção B: Serviço Externo (EasyCron, cron-job.org)

1. Acesse: https://cron-job.org
2. Crie conta gratuita
3. Adicione novo cron job:
   - URL: `https://seu-backend.railway.app/api/v1/pipeline/run`
   - Schedule: `0 18 * * *` (diariamente às 18h)

---

### 11. Monitoramento

#### 11.1. Logs no Railway

1. Clique no serviço
2. Vá para **"Deployments"**
3. Clique no deployment ativo
4. Veja logs em tempo real

#### 11.2. Configurar Alertas

1. No projeto, clique em **"Settings"**
2. Vá para **"Notifications"**
3. Configure alertas para:
   - Deploy failures
   - Service crashes
   - High resource usage

---

### 12. Backup do Banco de Dados

#### 12.1. Backup Manual

```bash
# Via Railway CLI
railway run pg_dump > backup_$(date +%Y%m%d).sql
```

#### 12.2. Backup Automático

Railway faz backups automáticos do PostgreSQL, mas você pode configurar backups adicionais:

1. Use GitHub Actions para backup diário
2. Armazene no GitHub ou S3

Exemplo de workflow:

```yaml
name: Database Backup

on:
  schedule:
    - cron: '0 2 * * *'  # 2h UTC diariamente

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - name: Backup Database
        run: |
          railway run pg_dump > backup.sql
          # Upload para S3 ou outro storage
```

---

## 📊 Custos no Railway

### Plano Gratuito (Hobby)
- **Crédito mensal:** $5
- **Recursos:** 512 MB RAM, 1 GB storage
- **Limitações:** Serviços dormem após inatividade

### Plano Developer ($5/mês)
- **Crédito mensal:** $5 + $5 de uso
- **Recursos:** Sem limites de sleep
- **Ideal para:** Projetos pessoais

### Plano Team ($20/mês)
- **Crédito mensal:** $20 de uso
- **Recursos:** Múltiplos projetos, colaboração
- **Ideal para:** Pequenas equipes

**Estimativa para sua aplicação:**
- Backend + Frontend + PostgreSQL: ~$8-15/mês
- Com uso moderado: ~$10/mês

---

## 🔧 Troubleshooting

### Problema: Serviço não inicia

**Solução:**
1. Verifique logs no Railway
2. Confirme que todas as variáveis estão configuradas
3. Verifique se o `DATABASE_URL` está correto

### Problema: Frontend não conecta ao Backend

**Solução:**
1. Verifique se `BACKEND_URL` no frontend está correto
2. Use a URL pública do backend (não localhost)
3. Confirme que backend está rodando

### Problema: Pipeline falha

**Solução:**
1. Verifique se `FMP_API_KEY` está configurada
2. Confirme que banco de dados está acessível
3. Execute `init_db.py` primeiro

### Problema: Banco de dados não conecta

**Solução:**
1. Verifique se PostgreSQL está rodando no Railway
2. Confirme que `DATABASE_URL` foi gerada automaticamente
3. Teste conexão via Railway CLI: `railway run python scripts/check_db.py`

---

## ✅ Checklist Final

- [ ] Projeto criado no Railway
- [ ] PostgreSQL adicionado
- [ ] Variáveis de ambiente configuradas
- [ ] URLs públicas geradas
- [ ] Backend acessível via URL
- [ ] Frontend acessível via URL
- [ ] Pipeline executado com sucesso
- [ ] Dados visíveis no frontend
- [ ] Monitoramento configurado
- [ ] Backup configurado (opcional)
- [ ] Domínio customizado (opcional)

---

## 🎉 Pronto!

Sua aplicação está no ar! Acesse:
- **Frontend:** https://seu-frontend.railway.app
- **API:** https://seu-backend.railway.app/docs

---

## 📞 Suporte

Se tiver problemas:
1. Verifique logs no Railway
2. Consulte documentação: https://docs.railway.app
3. Discord do Railway: https://discord.gg/railway
