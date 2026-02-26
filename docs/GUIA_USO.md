# Guia de Uso - Sistema de Ranking Quantitativo v2.5.2

## Índice
1. [Início Rápido](#1-início-rápido)
2. [Executar com Docker](#2-executar-com-docker)
3. [Executar Localmente](#3-executar-localmente)
4. [Usar a API](#4-usar-a-api)
5. [Usar o Frontend](#5-usar-o-frontend)
6. [Executar Pipeline](#6-executar-pipeline)
7. [Configurações Avançadas](#7-configurações-avançadas)
8. [Troubleshooting](#8-troubleshooting)

## Versão Atual: 2.5.2

Sistema com arquitetura de 3 camadas e tratamento estatístico correto de missing values:
- Elegibilidade estrutural (dados brutos apenas)
- Feature engineering com imputação estatística
- Scoring com normalização cross-sectional
- Scores distribuídos entre -3 e +3, média ~0
- Taxa de elegibilidade >= 80%

---

## 1. Início Rápido

### Pré-requisitos
- Docker e Docker Compose instalados
- OU Python 3.11+ instalado

### Opção A: Docker (Recomendado)
```bash
# 1. Clone o repositório
git clone https://github.com/edipo-dados/quant_stock_rank.git
cd quant_stock_rank

# 2. Inicie os containers
docker-compose up -d

# 3. Inicialize o banco de dados
docker-compose exec backend python scripts/init_db.py

# 4. Execute o pipeline
docker-compose exec backend python scripts/run_pipeline_docker.py --mode test

# 5. Acesse a aplicação
# Frontend: http://localhost:8501
# API: http://localhost:8000/docs
```

### Opção B: Local
```bash
# 1. Clone o repositório
git clone https://github.com/edipo-dados/quant_stock_rank.git
cd quant_stock_rank

# 2. Instale dependências
pip install -r requirements.txt

# 3. Configure variáveis de ambiente
cp .env.example .env
# Edite .env e configure DATABASE_URL para SQLite:
# DATABASE_URL=sqlite:///./quant_ranker.db

# 4. Inicialize o banco
python scripts/init_db.py

# 5. Execute o pipeline
python scripts/run_pipeline.py --mode test

# 6. Inicie a API (terminal 1)
python app/main.py

# 7. Inicie o frontend (terminal 2)
streamlit run frontend/streamlit_app.py
```

---

## 2. Executar com Docker

### 2.1 Gerenciar Containers

#### Iniciar todos os serviços
```bash
docker-compose up -d
```

#### Ver status
```bash
docker-compose ps
```

#### Ver logs
```bash
# Todos os serviços
docker-compose logs -f

# Apenas backend
docker-compose logs -f backend

# Apenas frontend
docker-compose logs -f frontend
```

#### Parar serviços
```bash
docker-compose down
```

#### Rebuild (após mudanças no código)
```bash
docker-compose up -d --build
```

### 2.2 Acessar Containers

```bash
# Backend
docker-compose exec backend bash

# Frontend
docker-compose exec frontend bash

# PostgreSQL
docker-compose exec postgres psql -U quant_user -d quant_ranker
```

### 2.3 Executar Comandos

```bash
# Inicializar banco
docker-compose exec backend python scripts/init_db.py

# Verificar banco
docker-compose exec backend python scripts/check_db.py

# Executar pipeline
docker-compose exec backend python scripts/run_pipeline_docker.py --mode test

# Executar testes
docker-compose exec backend pytest tests/
```

---

## 3. Executar Localmente

### 3.1 Configuração Inicial

#### Instalar Dependências
```bash
pip install -r requirements.txt
```

#### Configurar Banco de Dados

**SQLite (Desenvolvimento)**
```bash
# .env
DATABASE_URL=sqlite:///./quant_ranker.db
```

**PostgreSQL (Produção)**
```bash
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/quant_ranker
```

#### Inicializar Banco
```bash
python scripts/init_db.py
```

### 3.2 Executar Serviços

#### Backend (API)
```bash
# Desenvolvimento (com reload)
python app/main.py

# Produção
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Frontend (Streamlit)
```bash
streamlit run frontend/streamlit_app.py
```

#### Pipeline
```bash
# Modo teste (5 ativos)
python scripts/run_pipeline.py --mode test

# Ativos líquidos (top 50)
python scripts/run_pipeline.py --mode liquid --limit 50

# Ativos customizados
python scripts/run_pipeline.py --mode manual --tickers PETR4.SA VALE3.SA ITUB4.SA
```

---

## 4. Usar a API

### 4.1 Endpoints Disponíveis

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Documentação Interativa
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### Ranking Completo
```bash
curl http://localhost:8000/api/v1/ranking
```

Resposta:
```json
{
  "date": "2026-02-22",
  "rankings": [
    {
      "ticker": "ITUB4.SA",
      "date": "2026-02-22",
      "final_score": 1.28,
      "base_score": 1.28,
      "momentum_score": 0.96,
      "quality_score": 1.83,
      "value_score": 1.15,
      "confidence": 0.85,
      "passed_eligibility": true,
      "rank": 1
    }
  ],
  "total_assets": 50
}
```

#### Top N Ativos
```bash
# Top 10
curl http://localhost:8000/api/v1/top?limit=10

# Top 20
curl http://localhost:8000/api/v1/top?limit=20
```

#### Detalhes de um Ativo
```bash
curl http://localhost:8000/api/v1/asset/ITUB4.SA
```

Resposta:
```json
{
  "ticker": "ITUB4.SA",
  "date": "2026-02-22",
  "score": {
    "final_score": 1.28,
    "momentum_score": 0.96,
    "quality_score": 1.83,
    "value_score": 1.15,
    "rank": 1
  },
  "factors": {
    "momentum": {
      "return_6m": 0.48,
      "return_12m": 0.82,
      "rsi_14": 64.56,
      "volatility_90d": 0.22,
      "recent_drawdown": -0.003
    },
    "quality": {
      "roe": 0.19,
      "net_margin": 0.27,
      "revenue_growth_3y": 0.07
    },
    "value": {
      "pe_ratio": 12.5,
      "debt_to_ebitda": null
    }
  }
}
```

### 4.2 Filtros e Parâmetros

#### Ranking por Data
```bash
curl "http://localhost:8000/api/v1/ranking?date=2026-02-20"
```

#### Apenas Elegíveis
```bash
curl "http://localhost:8000/api/v1/ranking?eligible_only=true"
```

#### Limite de Resultados
```bash
curl "http://localhost:8000/api/v1/top?limit=20"
```

### 4.3 Usar com Python

```python
import requests

# Obter ranking
response = requests.get("http://localhost:8000/api/v1/ranking")
data = response.json()

# Top 10
top10 = requests.get("http://localhost:8000/api/v1/top?limit=10").json()

# Detalhes de um ativo
asset = requests.get("http://localhost:8000/api/v1/asset/ITUB4.SA").json()

print(f"Top ativo: {top10['rankings'][0]['ticker']}")
print(f"Score: {top10['rankings'][0]['final_score']}")
```

---

## 5. Usar o Frontend

### 5.1 Acessar Interface

Abra o navegador em: http://localhost:8501

### 5.2 Páginas Disponíveis

#### Página Principal (Home)
- Visão geral do sistema
- Estatísticas gerais
- Links rápidos

#### Ranking 🏆
- Lista completa de ativos ranqueados
- Filtros por score, setor, elegibilidade
- Exportação para CSV
- Visualizações:
  - Tabela interativa
  - Gráfico de distribuição de scores
  - Top 10 ativos

#### Detalhes do Ativo 📊
- Busca por ticker
- Score detalhado por fator
- Breakdown de features
- Gráficos:
  - Evolução de preço
  - Comparação com benchmark
  - Radar chart de fatores

### 5.3 Funcionalidades

#### Filtros
- **Score mínimo**: Mostrar apenas ativos acima de um score
- **Elegibilidade**: Apenas elegíveis ou todos
- **Setor**: Filtrar por setor específico
- **Top N**: Limitar número de resultados

#### Exportação
- **CSV**: Download da tabela completa
- **JSON**: Download dos dados brutos

#### Visualizações
- **Tabela**: Ordenável e filtrável
- **Gráficos**: Interativos (Plotly)
- **Métricas**: Cards com KPIs

---

## 6. Executar Pipeline

### 6.1 Modos de Execução

#### Modo Teste (5 ativos)
```bash
# Docker
docker-compose exec backend python scripts/run_pipeline_docker.py --mode test

# Local
python scripts/run_pipeline.py --mode test
```

Ativos: ITUB4.SA, BBDC4.SA, PETR4.SA, VALE3.SA, MGLU3.SA

#### Modo Líquidos (Top N da B3)
```bash
# Top 50
docker-compose exec backend python scripts/run_pipeline_docker.py --mode liquid --limit 50

# Top 100
docker-compose exec backend python scripts/run_pipeline_docker.py --mode liquid --limit 100
```

#### Modo Manual (Ativos Customizados)
```bash
docker-compose exec backend python scripts/run_pipeline_docker.py --mode manual --tickers PETR4.SA VALE3.SA ITUB4.SA BBDC4.SA
```

### 6.2 Opções Avançadas

#### Forçar Modo FULL
```bash
# Busca 400 dias de histórico mesmo com dados recentes
docker-compose exec backend python scripts/run_pipeline_docker.py --mode test --force-full
```

#### Ver Logs Detalhados
```bash
# Logs são salvos em pipeline_docker.log
docker-compose exec backend tail -f pipeline_docker.log
```

### 6.3 Etapas do Pipeline

1. **Verificação de Modo**: FULL ou INCREMENTAL
2. **Ingestão de Preços**: Yahoo Finance com rate limiting
3. **Ingestão de Fundamentos**: Yahoo Finance com rate limiting
4. **Filtro de Elegibilidade**: Aplicar critérios
5. **Cálculo de Features**: Momentum e Fundamentalistas
6. **Normalização**: Cross-sectional z-score
7. **Cálculo de Scores**: Por fator e final
8. **Geração de Ranking**: Ordenação por score

### 6.4 Rate Limiting

O pipeline Docker implementa rate limiting para evitar bloqueio:
- **2 segundos** entre cada ticker
- **5 segundos** entre batches de 5 tickers
- **3 tentativas** automáticas em caso de falha

Tempo estimado:
- 5 ativos: ~2 minutos (FULL) / ~30 segundos (INCREMENTAL)
- 50 ativos: ~20 minutos (FULL) / ~5 minutos (INCREMENTAL)
- 100 ativos: ~40 minutos (FULL) / ~10 minutos (INCREMENTAL)

---

## 7. Configurações Avançadas

### 7.1 Variáveis de Ambiente

Edite o arquivo `.env`:

```env
# Banco de Dados
DATABASE_URL=postgresql://quant_user:quant_password@postgres:5432/quant_ranker

# Pesos dos Fatores (v2.5.2)
MOMENTUM_WEIGHT=0.35  # 35%
QUALITY_WEIGHT=0.25   # 25%
VALUE_WEIGHT=0.30     # 30%
SIZE_WEIGHT=0.10      # 10%

# API
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
```

### 7.2 Ajustar Pesos dos Fatores (v2.5.2)

Pesos padrão:
```env
MOMENTUM_WEIGHT=0.35  # 35%
QUALITY_WEIGHT=0.25   # 25%
VALUE_WEIGHT=0.30     # 30%
SIZE_WEIGHT=0.10      # 10%
```

#### Perfil Agressivo (Momentum)
```env
MOMENTUM_WEIGHT=0.50
QUALITY_WEIGHT=0.20
VALUE_WEIGHT=0.20
SIZE_WEIGHT=0.10
```

#### Perfil Conservador (Quality)
```env
MOMENTUM_WEIGHT=0.20
QUALITY_WEIGHT=0.45
VALUE_WEIGHT=0.25
SIZE_WEIGHT=0.10
```

#### Perfil Value
```env
MOMENTUM_WEIGHT=0.20
QUALITY_WEIGHT=0.20
VALUE_WEIGHT=0.50
SIZE_WEIGHT=0.10
```

### 7.3 Ajustar Rate Limiting

Edite `scripts/run_pipeline_docker.py`:

```python
SLEEP_BETWEEN_TICKERS = 2  # Aumentar se houver bloqueio
SLEEP_BETWEEN_BATCHES = 5  # Aumentar para mais segurança
BATCH_SIZE = 5             # Reduzir para menos chamadas
MAX_RETRIES = 3            # Aumentar para mais tentativas
```

### 7.4 Backup e Restore

#### Backup do Banco
```bash
# Docker
docker-compose exec postgres pg_dump -U quant_user quant_ranker > backup.sql

# Local (PostgreSQL)
pg_dump -U quant_user quant_ranker > backup.sql
```

#### Restore do Banco
```bash
# Docker
cat backup.sql | docker-compose exec -T postgres psql -U quant_user quant_ranker

# Local (PostgreSQL)
psql -U quant_user quant_ranker < backup.sql
```

---

## 8. Troubleshooting

### 8.1 Problemas Comuns

#### Container não inicia
```bash
# Ver logs
docker-compose logs backend

# Rebuild
docker-compose down
docker-compose up -d --build
```

#### Banco de dados vazio
```bash
# Reinicializar
docker-compose exec backend python scripts/init_db.py
docker-compose exec backend python scripts/run_pipeline_docker.py --mode test
```

#### API não responde
```bash
# Verificar health
curl http://localhost:8000/health

# Restart
docker-compose restart backend
```

#### Frontend não carrega
```bash
# Ver logs
docker-compose logs frontend

# Restart
docker-compose restart frontend
```

#### Pipeline falha com erro de API
```bash
# Aumentar rate limiting em scripts/run_pipeline_docker.py
SLEEP_BETWEEN_TICKERS = 5  # Aumentar de 2 para 5
SLEEP_BETWEEN_BATCHES = 10 # Aumentar de 5 para 10
```

### 8.2 Erros Conhecidos

#### "Scores muito baixos ou negativos"
- **Causa**: Sistema v2.5.1 e anteriores usavam valores sentinela (-999)
- **Solução**: Atualizar para v2.5.2 com tratamento estatístico correto
- **Resultado esperado**: Scores entre -3 e +3, média ~0

#### "Taxa de elegibilidade baixa"
- **Causa**: Filtro verificando features derivadas em vez de dados brutos
- **Solução**: v2.5.2 usa arquitetura de 3 camadas
- **Resultado esperado**: >= 80% dos ativos elegíveis

#### "No data found for ticker"
- **Causa**: Ticker não existe ou sem dados no Yahoo Finance
- **Solução**: Verificar ticker correto (ex: PETR4.SA, não PETR4)

#### "Rate limit exceeded"
- **Causa**: Muitas chamadas à API Yahoo Finance
- **Solução**: Aumentar delays em `run_pipeline_docker.py`

### 8.3 Logs e Debug

#### Ver logs em tempo real
```bash
# Todos
docker-compose logs -f

# Apenas erros
docker-compose logs -f | grep ERROR

# Últimas 100 linhas
docker-compose logs --tail=100 backend
```

#### Ativar debug mode
```env
# .env
LOG_LEVEL=DEBUG
```

#### Verificar dados no banco
```bash
# Docker
docker-compose exec postgres psql -U quant_user -d quant_ranker

# Queries úteis
SELECT COUNT(*) FROM raw_prices_daily;
SELECT COUNT(*) FROM raw_fundamentals;
SELECT COUNT(*) FROM scores_daily;
SELECT ticker, final_score, rank FROM scores_daily ORDER BY rank LIMIT 10;
```

---

## 9. Próximos Passos

### 9.1 Produção
- Configure PostgreSQL externo
- Use Nginx como reverse proxy
- Configure SSL/TLS
- Implemente autenticação
- Configure backup automático

### 9.2 Melhorias
- Adicione mais fatores
- Implemente backtesting
- Adicione alertas por email
- Crie dashboard de performance
- Integre com broker para execução

### 9.3 Recursos Adicionais
- [Documentação de Cálculos](CALCULOS_RANKING.md)
- [Documentação da API](http://localhost:8000/docs)
- [Código no GitHub](https://github.com/edipo-dados/quant_stock_rank)
