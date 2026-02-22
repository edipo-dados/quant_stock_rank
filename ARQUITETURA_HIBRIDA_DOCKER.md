# 🏗️ Arquitetura Híbrida - Docker + Pipeline Local

## Problema Identificado

O Yahoo Finance bloqueia requisições vindas de containers Docker, causando erro:
```
yfinance - ERROR - No timezone found, symbol may be delisted
```

## ✅ Solução: Arquitetura Híbrida

**Pipeline Local + Aplicação Docker**

- **Pipeline**: Roda localmente (acesso direto ao Yahoo Finance)
- **Aplicação**: Roda no Docker (backend API + frontend + banco)
- **Banco de Dados**: Compartilhado entre ambos

---

## 🎯 Como Funciona

```
┌─────────────────────────────────────────────────────────┐
│                    SEU COMPUTADOR                        │
│                                                          │
│  ┌──────────────────┐         ┌──────────────────────┐ │
│  │  Pipeline Local  │────────▶│   Docker Compose     │ │
│  │                  │         │                      │ │
│  │ • Ingestão       │         │ ┌────────────────┐  │ │
│  │ • Cálculos       │         │ │   PostgreSQL   │  │ │
│  │ • Normalização   │◀────────│ │   (Banco)      │  │ │
│  │ • Scoring        │         │ └────────────────┘  │ │
│  └──────────────────┘         │                      │ │
│         │                     │ ┌────────────────┐  │ │
│         │                     │ │   Backend API  │  │ │
│         └─────────────────────│ │   (FastAPI)    │  │ │
│                               │ └────────────────┘  │ │
│                               │                      │ │
│                               │ ┌────────────────┐  │ │
│                               │ │   Frontend     │  │ │
│                               │ │   (Streamlit)  │  │ │
│                               │ └────────────────┘  │ │
│                               └──────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Configuração

### 1. Manter Docker Rodando

O Docker serve a aplicação (API + Frontend + Banco):

```bash
# Iniciar containers
docker compose up -d

# Verificar status
docker compose ps
```

**Containers ativos**:
- `quant-ranker-db` - PostgreSQL (porta 5432)
- `quant-ranker-backend` - FastAPI (porta 8000)
- `quant-ranker-frontend` - Streamlit (porta 8501)

### 2. Executar Pipeline Localmente

O pipeline roda fora do Docker, mas conecta no banco Docker:

```bash
# Pipeline completo (63 ativos líquidos B3)
python scripts/run_pipeline.py --mode liquid

# Pipeline de teste (5 ativos)
python scripts/run_pipeline.py --mode test

# Pipeline manual (tickers específicos)
python scripts/run_pipeline.py --mode manual --tickers PETR4.SA VALE3.SA
```

### 3. Configuração do Banco

O arquivo `.env` já está configurado para conectar no banco Docker:

```env
# Banco de dados (Docker)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/quant_ranker
```

**Importante**: O pipeline local usa `localhost:5432` que é o banco exposto pelo Docker.

---

## 🔄 Workflow Diário

### Opção 1: Manual

```bash
# 1. Garantir que Docker está rodando
docker compose ps

# 2. Executar pipeline
python scripts/run_pipeline.py --mode liquid

# 3. Acessar aplicação
# Frontend: http://localhost:8501
# API: http://localhost:8000/docs
```

### Opção 2: Automatizado (Agendamento)

#### Windows (Task Scheduler)

Criar arquivo `run_daily_pipeline.bat`:

```batch
@echo off
cd C:\Users\Edipo\Recomendacoes_financeiras
call venv\Scripts\activate
python scripts/run_pipeline.py --mode liquid
```

Agendar no Task Scheduler:
- Horário: 18:00 (após fechamento do mercado)
- Ação: Executar `run_daily_pipeline.bat`

#### Linux/Mac (Cron)

```bash
# Editar crontab
crontab -e

# Adicionar linha (executa às 18:00 todo dia)
0 18 * * * cd /path/to/projeto && source venv/bin/activate && python scripts/run_pipeline.py --mode liquid
```

---

## 🚀 Deploy em Produção

### Opção 1: Railway/Render (Recomendado)

**Arquitetura**:
- Deploy do Docker (API + Frontend + Banco) na plataforma
- Pipeline roda localmente no seu computador
- Conecta no banco remoto via URL pública

**Configuração**:

1. Deploy no Railway seguindo `deploy/railway.md`
2. Obter URL do banco PostgreSQL (Railway fornece)
3. Configurar `.env` local:

```env
# Banco de dados remoto (Railway)
DATABASE_URL=postgresql://user:pass@railway.app:5432/railway
```

4. Executar pipeline local:

```bash
python scripts/run_pipeline.py --mode liquid
```

Os dados vão direto para o banco na nuvem!

### Opção 2: VPS com Agendamento

**Arquitetura**:
- Deploy completo no VPS (Docker + Pipeline)
- Cron job executa pipeline diariamente
- Tudo na mesma máquina

**Configuração**:

```bash
# 1. Deploy no VPS
ssh user@seu-vps.com
git clone seu-repo
cd projeto

# 2. Configurar Docker
docker compose up -d

# 3. Configurar Cron
crontab -e
# Adicionar:
0 18 * * * cd /path/to/projeto && python scripts/run_pipeline.py --mode liquid
```

### Opção 3: Serverless Function (Avançado)

**Arquitetura**:
- API + Frontend no Railway/Render
- Pipeline como Cloud Function (AWS Lambda, Google Cloud Functions)
- Trigger diário via CloudWatch/Cloud Scheduler

**Vantagens**:
- Execução automática
- Sem servidor para manter
- Paga apenas quando executa

**Desvantagens**:
- Mais complexo de configurar
- Pode ter timeout em pipelines longos

---

## 📊 Monitoramento

### Verificar Última Execução

```bash
# Conectar no banco
docker compose exec postgres psql -U postgres -d quant_ranker

# Ver última data com dados
SELECT MAX(date) as ultima_data, COUNT(*) as total_ativos
FROM score_daily
WHERE passed_eligibility = true;

# Ver top 10 mais recente
SELECT ticker, final_score, rank
FROM score_daily
WHERE date = (SELECT MAX(date) FROM score_daily)
  AND passed_eligibility = true
ORDER BY rank
LIMIT 10;
```

### Logs do Pipeline

O pipeline gera logs detalhados:

```bash
# Executar com logs
python scripts/run_pipeline.py --mode liquid 2>&1 | tee pipeline.log

# Ver apenas erros
python scripts/run_pipeline.py --mode liquid 2>&1 | grep ERROR
```

---

## 🔧 Troubleshooting

### Problema: Pipeline não conecta no banco

**Sintoma**: `could not connect to server`

**Solução**:
```bash
# Verificar se Docker está rodando
docker compose ps

# Verificar se porta 5432 está aberta
netstat -an | findstr 5432  # Windows
netstat -an | grep 5432     # Linux/Mac

# Reiniciar banco
docker compose restart postgres
```

### Problema: Dados não aparecem no frontend

**Sintoma**: Frontend mostra "Nenhum dado disponível"

**Solução**:
```bash
# 1. Verificar se pipeline executou com sucesso
# (deve mostrar "PIPELINE COMPLETO COM SUCESSO")

# 2. Verificar dados no banco
docker compose exec postgres psql -U postgres -d quant_ranker
SELECT COUNT(*) FROM score_daily WHERE date = CURRENT_DATE;

# 3. Reiniciar frontend
docker compose restart frontend
```

### Problema: Yahoo Finance retorna erros

**Sintoma**: `No timezone found, symbol may be delisted`

**Solução**:
- Alguns tickers podem estar temporariamente indisponíveis
- O pipeline continua e processa os que funcionam
- Executar novamente mais tarde
- Verificar se ticker está correto na B3

---

## 📈 Melhorias Futuras

### 1. Cache de Dados

Implementar cache para reduzir chamadas à API:

```python
# Salvar dados brutos
# Reusar se já baixou hoje
# Reduz tempo de execução
```

### 2. Retry Logic

Adicionar tentativas automáticas em caso de falha:

```python
# Tentar 3 vezes com backoff exponencial
# Reduz falhas temporárias
```

### 3. Notificações

Enviar email/Telegram quando pipeline completar:

```python
# Notificar sucesso/falha
# Enviar resumo do ranking
# Alertar sobre problemas
```

### 4. Dashboard de Monitoramento

Criar página de status:
- Última execução
- Taxa de sucesso
- Ativos processados
- Tempo de execução

---

## 🎯 Resumo

**Arquitetura Atual**:
✅ Docker: API + Frontend + Banco (sempre rodando)
✅ Pipeline: Local (execução manual/agendada)
✅ Banco: Compartilhado entre ambos

**Vantagens**:
- ✅ Funciona perfeitamente (sem bloqueio do Yahoo Finance)
- ✅ Simples de manter
- ✅ Fácil de debugar
- ✅ Flexível (pode executar quando quiser)

**Próximos Passos**:
1. Agendar execução diária do pipeline
2. Fazer deploy do Docker em produção
3. Configurar pipeline local para conectar no banco remoto
4. Automatizar com cron/Task Scheduler

---

## 📚 Documentação Relacionada

- `PIPELINE_COMPLETO_SUCESSO.md` - Resultados da execução
- `DOCKER_DEPLOYMENT_SUCCESS.md` - Validação do Docker
- `deploy/railway.md` - Deploy em produção
- `README.md` - Documentação geral
