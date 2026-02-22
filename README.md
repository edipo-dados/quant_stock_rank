# Sistema de Ranking Quantitativo de Ações

Sistema de recomendação quantitativa de ações que combina análise fundamentalista e técnica para gerar rankings diários. Projetado como base para uma startup de research quantitativo, com arquitetura modular e escalável.

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura](#-arquitetura)
- [Início Rápido](#-início-rápido)
- [Execução Local](#-execução-local)
- [Execução com Docker](#-execução-com-docker)
- [Deploy em Produção](#-deploy-em-produção) ⭐ NOVO
- [API REST](#-api-rest)
- [Variáveis de Ambiente](#-variáveis-de-ambiente)
- [Pipeline de Dados](#-pipeline-de-dados)
- [Testes](#-testes)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Documentação Adicional](#-documentação-adicional)

## 🎯 Visão Geral

O sistema implementa uma estratégia quantitativa híbrida que:

1. **Ingere dados** de preços (Yahoo Finance) e fundamentos (Financial Modeling Prep)
2. **Calcula fatores** fundamentalistas (ROE, margens, P/L, etc) e momentum (retornos, RSI, volatilidade)
3. **Normaliza fatores** usando z-score cross-sectional
4. **Combina fatores** em score final ponderado (40% momentum, 30% qualidade, 30% valor)
5. **Gera rankings** diários ordenados por score
6. **Expõe API REST** para consumo de dados
7. **Apresenta interface web** para visualização

### Características Principais

- ✅ Análise fundamentalista e técnica combinada
- ✅ Normalização cross-sectional para comparabilidade
- ✅ Pesos configuráveis via arquivo de configuração
- ✅ API REST completa com FastAPI
- ✅ Interface web com Streamlit
- ✅ Explicações automáticas em português
- ✅ Testes baseados em propriedades (PBT)
- ✅ Deployment com Docker
- ✅ Arquitetura modular e extensível

## 🏗️ Arquitetura

### Arquitetura em Camadas

O sistema segue uma arquitetura em pipeline com três camadas principais:

```
┌─────────────────┐
│  APIs Externas  │ (Yahoo Finance, FMP)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Ingestão     │ (YahooFinanceClient, FMPClient)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Raw Data      │ (raw_prices_daily, raw_fundamentals)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Factor Engine  │ (FundamentalFactors, MomentumFactors, Normalizer)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Features     │ (features_daily, features_monthly)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Scoring Engine  │ (ScoringEngine, Ranker)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Scores      │ (scores_daily)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    API REST     │ (FastAPI)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Frontend     │ (Streamlit)
└─────────────────┘
```

### Módulos Principais

- **Ingestão**: Coleta dados de APIs externas
- **Factor Engine**: Calcula e normaliza fatores
- **Scoring Engine**: Combina fatores em score final
- **Confidence Engine**: Score de confiança (placeholder)
- **Report Generator**: Explicações automáticas
- **API Layer**: Endpoints REST
- **Frontend**: Interface web

## 🚀 Início Rápido

### Opção 1: Script Automático (Recomendado para Docker)

Execute o script que configura tudo automaticamente:

**Windows:**
```bash
start_sistema_completo.bat
```

Este script irá:
1. Parar containers existentes
2. Definir variáveis de ambiente corretas
3. Iniciar todos os containers (PostgreSQL, Backend, Frontend)
4. Inicializar o banco de dados
5. Inserir dados de teste

Após a execução, acesse:
- **Frontend**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Opção 2: Execução Local (Sem Docker)

#### 1. Iniciar o Banco de Dados

**Windows:**
```bash
start_db.bat
```

**Linux/Mac:**
```bash
docker-compose up -d postgres
```

#### 2. Inicializar as Tabelas

```bash
python scripts/init_db.py
```

#### 3. Verificar Conexão

```bash
python scripts/check_db.py
```

Pronto! O banco de dados está configurado e pronto para uso.

📖 **Para mais detalhes sobre conexão ao banco, veja:** [GUIA_CONEXAO_BANCO.md](GUIA_CONEXAO_BANCO.md)

---

## 💻 Execução Local

### Pré-requisitos

- Python 3.11+
- PostgreSQL 15+ (ou Docker)
- Chave de API do Financial Modeling Prep

### Passo a Passo

#### 1. Clonar o Repositório

```bash
git clone <repository-url>
cd quant-stock-ranker
```

#### 2. Configurar Ambiente Virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

#### 4. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas credenciais
# Obrigatório: FMP_API_KEY
```

#### 5. Iniciar Banco de Dados

**Opção A: Docker (Recomendado)**
```bash
# Windows
start_db.bat

# Linux/Mac
docker-compose up -d postgres
```

**Opção B: PostgreSQL Local**
```bash
# Criar banco de dados
createdb quant_ranker

# Atualizar DATABASE_URL no .env
DATABASE_URL=postgresql://seu_usuario:sua_senha@localhost:5432/quant_ranker
```

#### 6. Inicializar Schema

```bash
python scripts/init_db.py
```

#### 7. Executar Pipeline de Dados (Opcional)

```bash
# Executar pipeline completo
python scripts/run_pipeline.py

# Ou executar etapas individuais via API
```

#### 8. Iniciar Backend

```bash
# Desenvolvimento
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Produção
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Acesse: http://localhost:8000/docs

#### 9. Iniciar Frontend

```bash
# Em outro terminal
streamlit run frontend/streamlit_app.py
```

Acesse: http://localhost:8501

---

## 🐳 Execução com Docker

### Pré-requisitos

- Docker 20.10+
- Docker Compose 2.0+

### Deployment Completo

#### 1. Configurar Variáveis de Ambiente

```bash
cp .env.example .env
# Editar .env com FMP_API_KEY
```

#### 2. Iniciar Todos os Serviços

```bash
docker-compose up -d
```

Isso iniciará:
- PostgreSQL (porta 5432)
- Backend API (porta 8000)
- Frontend Streamlit (porta 8501)

#### 3. Verificar Status

```bash
docker-compose ps
```

#### 4. Acessar Serviços

- **API Backend**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Frontend**: http://localhost:8501
- **PostgreSQL**: localhost:5432

#### 5. Ver Logs

```bash
# Todos os serviços
docker-compose logs -f

# Serviço específico
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

#### 6. Parar Serviços

```bash
# Parar sem remover volumes
docker-compose down

# Parar e remover volumes (limpa banco de dados)
docker-compose down -v
```

### Teste Automatizado do Deployment

**Windows:**
```bash
test_docker.bat
```

**Linux/Mac:**
```bash
chmod +x test_docker.sh
./test_docker.sh
```

O script executa:
1. Verificação do Docker
2. Build das imagens
3. Inicialização dos serviços
4. Testes de health check
5. Validação de endpoints
6. Testes de integração

📖 **Guia completo:** [TESTE_DOCKER.md](TESTE_DOCKER.md)

---

## 🚀 Deploy em Produção

### Opções de Deploy

O sistema pode ser implantado em diversos ambientes. Escolha baseado em suas necessidades:

| Opção | Dificuldade | Custo/mês | Tempo Setup | Recomendado para |
|-------|-------------|-----------|-------------|------------------|
| **Railway** | ⭐ Fácil | $5-15 | 10 min | MVP, Testes |
| **Render** | ⭐ Fácil | $7-25 | 15 min | Startups |
| **Fly.io** | ⭐⭐ Média | $0-30 | 20 min | Projetos sérios |
| **DigitalOcean** | ⭐⭐ Média | $12-50 | 1h | Produção |
| **AWS ECS** | ⭐⭐⭐ Difícil | $30-100 | 2-4h | Enterprise |
| **VPS Manual** | ⭐⭐⭐ Difícil | €4-20 | 1-2h | Controle total |

### Quick Start - Railway (Mais Fácil)

Deploy em 10 minutos:

1. Acesse https://railway.app
2. Login com GitHub
3. New Project → Deploy from GitHub
4. Adicione PostgreSQL
5. Configure variáveis de ambiente
6. Deploy automático!

**Guia completo:** [`deploy/railway.md`](deploy/railway.md)

### Quick Start - VPS (Controle Total)

```bash
# 1. Conectar ao VPS
ssh root@seu-ip

# 2. Executar setup automático
wget https://raw.githubusercontent.com/seu-usuario/seu-repo/main/deploy/vps-setup.sh
sudo bash vps-setup.sh

# 3. Clonar e configurar
su - deploy
git clone https://github.com/seu-usuario/seu-repo.git
cd seu-repo
cp .env.example .env
nano .env

# 4. Deploy
docker compose up -d --build

# 5. Configurar Nginx + SSL
sudo cp deploy/nginx.conf /etc/nginx/sites-available/quant-ranker
sudo ln -s /etc/nginx/sites-available/quant-ranker /etc/nginx/sites-enabled/
sudo certbot --nginx -d seu-dominio.com
```

### Documentação Completa de Deploy

📚 **Guias disponíveis:**

- **[DEPLOY_RESUMO.md](DEPLOY_RESUMO.md)** - Resumo executivo e recomendações
- **[GUIA_DEPLOY.md](GUIA_DEPLOY.md)** - Guia completo com todas as opções
- **[deploy/DECISION_TREE.md](deploy/DECISION_TREE.md)** - Árvore de decisão interativa
- **[deploy/railway.md](deploy/railway.md)** - Guia Railway passo a passo
- **[deploy/QUICK_REFERENCE.md](deploy/QUICK_REFERENCE.md)** - Comandos essenciais
- **[deploy/INDEX.md](deploy/INDEX.md)** - Índice completo da documentação

### Scripts de Automação

```bash
# Setup automático de VPS
./deploy/vps-setup.sh

# Backup do banco de dados
./deploy/backup-db.sh

# Restaurar banco de dados
./deploy/restore-db.sh /path/to/backup.sql.gz
```

### Monitoramento e Manutenção

```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health

# Ver logs
docker compose logs -f

# Backup automático (cron)
crontab -e
# Adicionar: 0 2 * * * /path/to/deploy/backup-db.sh
```

**Referência rápida:** [`deploy/QUICK_REFERENCE.md`](deploy/QUICK_REFERENCE.md)

---

## 🔌 API REST

### Base URL

```
http://localhost:8000
```

### Endpoints

#### 1. GET /ranking

Retorna ranking diário completo ordenado por score.

**Parâmetros:**
- `date` (opcional): Data no formato YYYY-MM-DD. Se omitido, usa data mais recente.

**Exemplo:**
```bash
curl http://localhost:8000/ranking
curl http://localhost:8000/ranking?date=2024-01-15
```

**Resposta:**
```json
{
  "date": "2024-01-15",
  "rankings": [
    {
      "ticker": "PETR4",
      "date": "2024-01-15",
      "final_score": 1.85,
      "breakdown": {
        "momentum_score": 2.1,
        "quality_score": 1.5,
        "value_score": 1.9
      },
      "confidence": 0.5,
      "rank": 1
    },
    ...
  ],
  "total_assets": 50
}
```

#### 2. GET /asset/{ticker}

Retorna detalhes completos de um ativo específico.

**Parâmetros:**
- `ticker` (obrigatório): Símbolo do ativo (ex: PETR4, VALE3)
- `date` (opcional): Data no formato YYYY-MM-DD

**Exemplo:**
```bash
curl http://localhost:8000/asset/PETR4
curl http://localhost:8000/asset/PETR4?date=2024-01-15
```

**Resposta:**
```json
{
  "ticker": "PETR4",
  "score": {
    "ticker": "PETR4",
    "date": "2024-01-15",
    "final_score": 1.85,
    "breakdown": {
      "momentum_score": 2.1,
      "quality_score": 1.5,
      "value_score": 1.9
    },
    "confidence": 0.5,
    "rank": 1
  },
  "explanation": "PETR4 possui score de 1.85, ocupando a 1ª posição no ranking...",
  "raw_factors": {
    "return_6m": 0.25,
    "return_12m": 0.45,
    "rsi_14": 65.0,
    "roe": 0.18,
    "net_margin": 0.15,
    ...
  }
}
```

**Erros:**
- `404`: Ticker não encontrado

#### 3. GET /top

Retorna top N ativos por score.

**Parâmetros:**
- `n` (opcional): Número de ativos a retornar (default: 10)
- `date` (opcional): Data no formato YYYY-MM-DD

**Exemplo:**
```bash
curl http://localhost:8000/top
curl http://localhost:8000/top?n=5
curl http://localhost:8000/top?n=20&date=2024-01-15
```

**Resposta:**
```json
{
  "date": "2024-01-15",
  "top_assets": [
    {
      "ticker": "PETR4",
      "final_score": 1.85,
      ...
    },
    ...
  ],
  "n": 10
}
```

#### 4. GET /health

Health check do serviço.

**Exemplo:**
```bash
curl http://localhost:8000/health
```

**Resposta:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Documentação Interativa

Acesse a documentação Swagger em: http://localhost:8000/docs

---

## ⚙️ Variáveis de Ambiente

### Arquivo .env

Copie `.env.example` para `.env` e configure as seguintes variáveis:

#### Banco de Dados

```bash
# String de conexão PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/quant_ranker

# Para Docker (padrão)
DATABASE_URL=postgresql://user:password@postgres:5432/quant_ranker
```

#### APIs Externas

```bash
# Chave da API Financial Modeling Prep (OBRIGATÓRIO)
# Obtenha em: https://financialmodelingprep.com/developer/docs/
FMP_API_KEY=sua_chave_aqui
```

#### Pesos de Scoring

```bash
# Pesos para combinação de fatores (devem somar 1.0)
MOMENTUM_WEIGHT=0.4    # Peso dos fatores de momentum (default: 0.4)
QUALITY_WEIGHT=0.3     # Peso dos fatores de qualidade (default: 0.3)
VALUE_WEIGHT=0.3       # Peso dos fatores de valor (default: 0.3)
```

#### Filtros de Elegibilidade

```bash
# Volume mínimo diário para inclusão no universo
MINIMUM_VOLUME=100000  # Volume médio diário mínimo (default: 100000)
```

#### Parâmetros de Qualidade Robusta

```bash
# Limite máximo para ROE (Return on Equity)
MAX_ROE_LIMIT=0.50     # Cap de ROE em 50% (default: 0.50)

# Limite de dívida/EBITDA para penalização
DEBT_EBITDA_LIMIT=4.0  # Threshold para penalidade de alavancagem (default: 4.0)
```

#### Penalização de Risco

```bash
# Limite de volatilidade para penalização
VOLATILITY_LIMIT=0.60  # Volatilidade anualizada máxima sem penalidade (default: 0.60)

# Limite de drawdown para penalização
DRAWDOWN_LIMIT=-0.50   # Drawdown máximo sem penalidade em -50% (default: -0.50)
```

#### Winsorização

```bash
# Percentis para winsorização de outliers
WINSORIZE_LOWER_PCT=0.05  # Percentil inferior (default: 0.05 = 5%)
WINSORIZE_UPPER_PCT=0.95  # Percentil superior (default: 0.95 = 95%)
```

#### Configuração da API

```bash
# Host e porta do servidor FastAPI
API_HOST=0.0.0.0       # Host (default: 0.0.0.0)
API_PORT=8000          # Porta (default: 8000)
```

#### Logging

```bash
# Nível de log
LOG_LEVEL=INFO         # Opções: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Variáveis Opcionais

```bash
# Timeout para requisições HTTP (segundos)
HTTP_TIMEOUT=30

# Número de workers para uvicorn
WORKERS=4

# Modo de desenvolvimento
DEBUG=false
```

### Exemplo Completo

Veja `.env.example` para um exemplo completo com todas as variáveis e comentários explicativos.

---

## 🔄 Pipeline de Dados

### Fluxo Completo

O pipeline executa as seguintes etapas:

1. **Ingestão de Preços**: Busca dados diários do Yahoo Finance
2. **Ingestão de Fundamentos**: Busca dados fundamentalistas do FMP
3. **Cálculo de Fatores de Momentum**: Retornos, RSI, volatilidade, drawdown
4. **Cálculo de Fatores Fundamentalistas**: ROE, margens, P/L, P/VP, etc
5. **Normalização Cross-Sectional**: Z-score para comparabilidade
6. **Cálculo de Scores**: Combina fatores com pesos configuráveis
7. **Geração de Ranking**: Ordena ativos por score final

### Executar Pipeline

```bash
# Pipeline completo
python scripts/run_pipeline.py

# Com lista customizada de tickers
python scripts/run_pipeline.py --tickers PETR4 VALE3 ITUB4

# Com período específico
python scripts/run_pipeline.py --start-date 2023-01-01 --end-date 2024-01-01
```

### Validar Features

```bash
# Validar features calculadas
python scripts/validate_features.py

# Validar para ticker específico
python scripts/validate_features.py --ticker PETR4
```

---

## 🧪 Testes

### Executar Todos os Testes

```bash
pytest tests/ -v
```

### Testes por Categoria

```bash
# Testes unitários
pytest tests/unit/ -v

# Testes de integração
pytest tests/integration/ -v

# Testes de propriedade (PBT)
pytest tests/unit/ -v -k "properties"
```

### Testes por Módulo

```bash
# Ingestão
pytest tests/unit/test_ingestion_properties.py -v

# Fatores
pytest tests/unit/test_fundamental_factors.py -v
pytest tests/unit/test_momentum_factors.py -v
pytest tests/unit/test_normalizer_properties.py -v

# Scoring
pytest tests/unit/test_scoring_properties.py -v
pytest tests/unit/test_ranking_properties.py -v

# API
pytest tests/unit/test_api_ranking_properties.py -v
pytest tests/unit/test_api_asset_properties.py -v
pytest tests/unit/test_api_top_properties.py -v

# Pipeline end-to-end
pytest tests/integration/test_pipeline_e2e.py -v
```

### Cobertura de Testes

```bash
# Gerar relatório de cobertura
pytest tests/ --cov=app --cov-report=html

# Ver relatório
# Abrir htmlcov/index.html no navegador
```

### Testes de Deployment Docker

```bash
# Teste automatizado completo
python scripts/test_docker_deployment.py

# Ou usar scripts shell
./test_docker.sh  # Linux/Mac
test_docker.bat   # Windows
```

---

## 📁 Estrutura do Projeto

```
quant-stock-ranker/
├── app/                        # Aplicação backend
│   ├── __init__.py
│   ├── main.py                 # Entry point FastAPI
│   ├── config.py               # Configurações centralizadas
│   │
│   ├── ingestion/              # Módulo de ingestão de dados
│   │   ├── __init__.py
│   │   ├── yahoo_client.py     # Cliente Yahoo Finance
│   │   ├── fmp_client.py       # Cliente FMP API
│   │   └── ingestion_service.py # Orquestração de ingestão
│   │
│   ├── factor_engine/          # Cálculo de fatores
│   │   ├── __init__.py
│   │   ├── fundamental_factors.py  # Fatores fundamentalistas
│   │   ├── momentum_factors.py     # Fatores de momentum
│   │   ├── normalizer.py           # Z-score cross-sectional
│   │   └── feature_service.py      # Orquestração de features
│   │
│   ├── scoring/                # Motor de scoring e ranking
│   │   ├── __init__.py
│   │   ├── scoring_engine.py   # Combina fatores em score
│   │   ├── ranker.py           # Gera rankings
│   │   └── score_service.py    # Orquestração de scoring
│   │
│   ├── confidence/             # Score de confiança
│   │   ├── __init__.py
│   │   └── confidence_engine.py # Placeholder para confiança
│   │
│   ├── report/                 # Geração de relatórios
│   │   ├── __init__.py
│   │   └── report_generator.py # Explicações automáticas
│   │
│   ├── models/                 # Modelos de banco de dados
│   │   ├── __init__.py
│   │   ├── database.py         # Setup SQLAlchemy
│   │   └── schemas.py          # Modelos SQLAlchemy
│   │
│   ├── core/                   # Componentes core
│   │   ├── __init__.py
│   │   ├── exceptions.py       # Exceções customizadas
│   │   └── logging.py          # Setup de logging
│   │
│   └── api/                    # Endpoints REST
│       ├── __init__.py
│       ├── routes.py           # Endpoints REST
│       ├── dependencies.py     # Dependências FastAPI
│       └── schemas.py          # Pydantic schemas
│
├── frontend/                   # Interface Streamlit
│   ├── streamlit_app.py        # App principal
│   └── pages/
│       ├── 1_🏆_Ranking.py     # Página de ranking
│       └── 2_📊_Detalhes_do_Ativo.py  # Detalhes do ativo
│
├── scripts/                    # Scripts utilitários
│   ├── __init__.py
│   ├── init_db.py              # Inicializa schema do banco
│   ├── check_db.py             # Verifica conexão
│   ├── run_pipeline.py         # Pipeline completo
│   ├── validate_features.py    # Valida features calculadas
│   └── test_docker_deployment.py  # Testa deployment Docker
│
├── tests/                      # Testes
│   ├── unit/                   # Testes unitários
│   │   ├── test_database_schemas.py
│   │   ├── test_ingestion_properties.py
│   │   ├── test_fundamental_factors.py
│   │   ├── test_momentum_factors.py
│   │   ├── test_normalizer_properties.py
│   │   ├── test_scoring_properties.py
│   │   ├── test_ranking_properties.py
│   │   ├── test_api_*.py
│   │   └── ...
│   └── integration/            # Testes de integração
│       └── test_pipeline_e2e.py
│
├── docker/                     # Dockerfiles
│   ├── Dockerfile.backend      # Imagem do backend
│   └── Dockerfile.frontend     # Imagem do frontend
│
├── .kiro/                      # Especificações do projeto
│   └── specs/
│       └── quant-stock-ranker/
│           ├── requirements.md # Requisitos
│           ├── design.md       # Design
│           └── tasks.md        # Tarefas
│
├── docker-compose.yml          # Configuração Docker Compose
├── requirements.txt            # Dependências Python
├── .env.example                # Exemplo de variáveis de ambiente
├── .env                        # Variáveis de ambiente (não versionado)
├── README.md                   # Este arquivo
├── GUIA_CONEXAO_BANCO.md      # Guia de conexão ao banco
├── TESTE_DOCKER.md            # Guia de teste Docker
├── start_db.bat               # Script Windows para iniciar DB
├── test_docker.bat            # Script Windows para testar Docker
└── test_docker.sh             # Script Linux/Mac para testar Docker
```

---

## 🛠️ Comandos Úteis

### Banco de Dados

```bash
# Iniciar banco (Docker)
docker-compose up -d postgres

# Parar banco
docker-compose down

# Ver logs do banco
docker-compose logs -f postgres

# Conectar via psql
docker exec -it quant_ranker_db psql -U user -d quant_ranker

# Verificar status e tabelas
python scripts/check_db.py

# Inicializar/recriar tabelas
python scripts/init_db.py

# Recriar tabelas (drop + create)
python scripts/init_db.py --drop
```

### Backend

```bash
# Desenvolvimento (auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Produção
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Com log detalhado
uvicorn app.main:app --reload --log-level debug
```

### Frontend

```bash
# Iniciar Streamlit
streamlit run frontend/streamlit_app.py

# Com porta customizada
streamlit run frontend/streamlit_app.py --server.port 8502
```

### Docker

```bash
# Build das imagens
docker-compose build

# Iniciar todos os serviços
docker-compose up -d

# Ver status
docker-compose ps

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down

# Limpar tudo (incluindo volumes)
docker-compose down -v

# Rebuild e restart
docker-compose up -d --build
```

---

## 📦 Dependências Principais

### Backend

- **FastAPI** (0.104+): Framework web moderno para APIs
- **SQLAlchemy** (2.0+): ORM para banco de dados
- **pandas** (2.1+): Processamento e análise de dados
- **yfinance** (0.2+): Dados de preços do Yahoo Finance
- **requests** (2.31+): Cliente HTTP para APIs externas
- **psycopg2-binary** (2.9+): Driver PostgreSQL
- **pydantic** (2.5+): Validação de dados
- **python-dotenv** (1.0+): Gerenciamento de variáveis de ambiente

### Testes

- **pytest** (7.4+): Framework de testes
- **hypothesis** (6.92+): Testes baseados em propriedades (PBT)
- **pytest-cov** (4.1+): Cobertura de testes

### Frontend

- **streamlit** (1.29+): Framework para interfaces web
- **plotly** (5.18+): Gráficos interativos
- **requests** (2.31+): Cliente HTTP para consumir API

### Infraestrutura

- **uvicorn** (0.24+): Servidor ASGI
- **PostgreSQL** (15+): Banco de dados relacional
- **Docker** (20.10+): Containerização
- **Docker Compose** (2.0+): Orquestração de containers

---

## 🎓 Conceitos Principais

### Fatores Fundamentalistas

Métricas baseadas em demonstrações financeiras:

- **ROE** (Return on Equity): Retorno sobre patrimônio líquido
- **Margem Líquida**: Lucro líquido / Receita
- **Crescimento de Receita 3Y**: CAGR de receita dos últimos 3 anos
- **Dívida/EBITDA**: Alavancagem financeira
- **P/L** (Price/Earnings): Preço / Lucro por ação
- **EV/EBITDA**: Enterprise Value / EBITDA
- **P/VP** (Price/Book): Preço / Valor patrimonial por ação

### Fatores de Momentum

Métricas baseadas em preço e volume:

- **Retorno 6M**: Retorno acumulado dos últimos 6 meses
- **Retorno 12M**: Retorno acumulado dos últimos 12 meses
- **RSI 14**: Relative Strength Index de 14 períodos
- **Volatilidade 90D**: Desvio padrão dos retornos de 90 dias
- **Drawdown Recente**: Queda desde o pico recente (90 dias)

### Normalização Cross-Sectional

Técnica que normaliza fatores comparando todos os ativos no mesmo período:

```
z-score = (valor - média) / desvio_padrão
```

Garante comparabilidade entre fatores de diferentes escalas.

### Score Final

Combinação ponderada de três categorias:

```
Score Final = 0.4 × Momentum + 0.3 × Qualidade + 0.3 × Valor
```

Pesos configuráveis via arquivo `.env`.

---

## 🔍 Troubleshooting

### Erro: "Connection refused" ao conectar ao banco

**Solução:**
```bash
# Verificar se PostgreSQL está rodando
docker-compose ps

# Iniciar se necessário
docker-compose up -d postgres

# Verificar logs
docker-compose logs postgres
```

### Erro: "FMP_API_KEY not found"

**Solução:**
```bash
# Verificar se .env existe
ls -la .env

# Copiar de .env.example se necessário
cp .env.example .env

# Editar e adicionar sua chave
# FMP_API_KEY=sua_chave_aqui
```

### Erro: "Table does not exist"

**Solução:**
```bash
# Inicializar schema do banco
python scripts/init_db.py

# Verificar tabelas criadas
python scripts/check_db.py
```

### Frontend não conecta à API

**Solução:**
```bash
# Verificar se backend está rodando
curl http://localhost:8000/health

# Verificar variável de ambiente no frontend
# API_URL deve apontar para http://localhost:8000
```

### Docker: "Port already in use"

**Solução:**
```bash
# Verificar processos usando a porta
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# Parar processo ou mudar porta no docker-compose.yml
```

---

## 📚 Documentação Adicional

- [Guia de Conexão ao Banco](GUIA_CONEXAO_BANCO.md) - Instruções detalhadas para configurar PostgreSQL
- [Guia de Teste Docker](TESTE_DOCKER.md) - Como testar o deployment completo
- [Requisitos](.kiro/specs/quant-stock-ranker/requirements.md) - Especificação completa de requisitos
- [Design](.kiro/specs/quant-stock-ranker/design.md) - Documento de design da arquitetura
- [Tarefas](.kiro/specs/quant-stock-ranker/tasks.md) - Plano de implementação detalhado

---

## 🚀 Roadmap Futuro

### Fase 2: Backtesting
- [ ] Motor de backtesting histórico
- [ ] Métricas de performance (Sharpe, drawdown, etc)
- [ ] Análise de atribuição de fatores

### Fase 3: Otimização de Portfólio
- [ ] Otimização de Markowitz
- [ ] Rebalanceamento automático
- [ ] Gestão de risco

### Fase 4: Machine Learning
- [ ] Modelos preditivos para fatores
- [ ] Ensemble de estratégias
- [ ] Feature engineering automático

### Fase 5: Produção
- [ ] Deployment em cloud (AWS/GCP/Azure)
- [ ] CI/CD pipeline
- [ ] Monitoramento e alertas
- [ ] Autenticação e autorização

---

## 📄 Licença

Este projeto é proprietário e confidencial.

---

## 👥 Contribuindo

Para contribuir com o projeto:

1. Leia a documentação completa
2. Execute todos os testes antes de submeter mudanças
3. Siga os padrões de código estabelecidos
4. Documente novas funcionalidades

---

## 📞 Suporte

Para dúvidas ou problemas:

1. Consulte a documentação
2. Verifique a seção de Troubleshooting
3. Revise os logs do sistema
4. Entre em contato com a equipe de desenvolvimento

---

**Desenvolvido com ❤️ para análise quantitativa de ações**
