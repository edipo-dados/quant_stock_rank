# Quant Stock Ranker v2.8

Sistema de ranking quantitativo de ações da B3 baseado em modelo multifator.

**URL:** `http://eas-bot.duckdns.org:8501` (Frontend) | `http://eas-bot.duckdns.org:8000` (API)

## Arquitetura

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐
│  Yahoo Fin  │───▶│   Backend   │───▶│  PostgreSQL  │
│  (Dados)    │    │  (FastAPI)  │    │   (Banco)    │
└─────────────┘    └──────┬──────┘    └──────────────┘
                          │
                   ┌──────┴──────┐
                   │  Frontend   │
                   │ (Streamlit) │
                   └─────────────┘
```

## Stack

- Backend: FastAPI + SQLAlchemy
- Frontend: Streamlit
- Banco: PostgreSQL
- Deploy: Docker Compose no EC2

## Modelo Multifator (v2.8 - Anti-Defensive Bias)

| Fator | Peso | Descrição |
|-------|------|-----------|
| Momentum | 60% | 12m ex-1m (50%), 6m ex-1m (30%), vol/drawdown (20%) |
| Value | 20% | P/E, P/B, EV/EBITDA, FCF Yield, Earnings Yield |
| Quality | 15% | ROE 3Y, margem líquida, crescimento receita |
| Risk | 5% | Volatilidade 90d/1y, drawdown (reduzido para evitar viés defensivo) |

**Novidades v2.8:**
- Momentum dominante com peso 60% (12m_ex_1m como fator principal)
- Risk weight reduzido de 10% para 5% (evita viés em utilities/Ambev)
- Earnings Yield adicionado ao fator Value (Net Income / Market Cap)
- Penalização para volatilidade muito baixa (percentil 20 → -10% no score)

## Melhorias v2.7.0

- Correção definitiva do cálculo de Alpha (CAPM)
- Volatility Targeting (alvo 15% anual)
- Limites de exposição por setor (máx 30%)
- Validações robustas de métricas

---

## Pipelines - Ordem de Execução

### 1. Pipeline de Dados (obrigatório, rodar primeiro)

Baixa preços do Yahoo Finance, calcula features e gera scores.

```bash
# Pipeline FULL (primeira execução ou reset)
docker exec -it quant-ranker-backend python scripts/clear_and_run_full.py --mode liquid --limit 50

# Pipeline INCREMENTAL (atualizações diárias)
docker exec -it quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50

# Pipeline SMART (decide automaticamente entre FULL e INCREMENTAL)
docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py
```

| Script | Quando usar | Tempo estimado |
|--------|-------------|----------------|
| `clear_and_run_full.py` | Primeira execução, reset de dados | 30-60 min |
| `run_pipeline_docker.py` | Atualização diária | 10-20 min |
| `run_smart_pipeline.py` | Automático (CRON) | 10-60 min |

### 2. Pipeline de Backtest (opcional, após pipeline de dados)

Simula a estratégia historicamente e calcula métricas de performance.

```bash
# Gerar scores históricos (necessário antes do backtest)
docker exec -it quant-ranker-backend python scripts/generate_historical_scores.py

# Executar backtest
docker exec -it quant-ranker-backend python scripts/run_backtest_pipeline.py

# Backtest com melhorias v2.7.0 (volatility targeting + sector limits)
docker exec -it quant-ranker-backend python scripts/run_enhanced_backtest.py
```

| Script | Quando usar | Tempo estimado |
|--------|-------------|----------------|
| `generate_historical_scores.py` | Antes do primeiro backtest | 20-40 min |
| `run_backtest_pipeline.py` | Backtest padrão | 5-15 min |
| `run_enhanced_backtest.py` | Backtest com melhorias v2.7.0 | 5-15 min |

### 3. Scripts Auxiliares

```bash
# Verificar scores mais recentes
docker exec -it quant-ranker-backend python scripts/check_latest_scores.py

# Verificar cobertura histórica
docker exec -it quant-ranker-backend python scripts/check_historical_coverage.py

# Atualizar lista de ações líquidas da B3
docker exec -it quant-ranker-backend python scripts/update_liquid_stocks.py

# Limpar dados de backtest
docker exec -it quant-ranker-backend python scripts/clear_backtest_data.py

# Aplicar suavização temporal nos scores
docker exec -it quant-ranker-backend python scripts/apply_temporal_smoothing.py --all

# Comparar estratégias
docker exec -it quant-ranker-backend python scripts/compare_strategies.py
```

---

## Deploy no EC2

### Primeiro Deploy

```bash
# 1. Clonar repositório
git clone https://github.com/edipo-dados/quant_stock_rank.git
cd quant_stock_rank

# 2. Configurar .env
cp .env.example .env
# Editar .env com suas configurações

# 3. Subir containers
docker-compose up -d

# 4. Criar tabelas do banco
docker exec -it quant-ranker-backend python scripts/init_db.py

# 5. Criar tabelas de backtest
docker exec -it quant-ranker-backend python -c 'from app.models.database import engine, Base; from app.backtest.models import *; Base.metadata.create_all(bind=engine); print("OK")'

# 6. Executar pipeline de dados
docker exec -it quant-ranker-backend python scripts/clear_and_run_full.py --mode liquid --limit 50
```

### Atualizar Deploy

```bash
cd ~/quant_stock_rank
docker-compose down
git pull origin main
docker-compose build backend
docker-compose up -d
```

### Verificar Status

```bash
# Containers rodando
docker ps

# Health check da API
curl http://localhost:8000/health

# Logs do backend
docker logs quant-ranker-backend --tail 50
```

### Liberar Portas (Security Group AWS)

| Porta | Serviço |
|-------|---------|
| 8000 | API (FastAPI) |
| 8501 | Frontend (Streamlit) |

---

## API

### Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/health` | GET | Status da API |
| `/api/v1/ranking` | GET | Ranking completo |
| `/api/v1/top?n=10` | GET | Top N ações |
| `/api/v1/asset/{ticker}` | GET | Detalhes de uma ação |
| `/api/v1/ranking?date=YYYY-MM-DD` | GET | Ranking de data específica |
| `/api/v1/prices/{ticker}` | GET | Histórico de preços |

### Exemplo de Uso

```python
import requests

# Top 10 ações
response = requests.get("http://seu-ec2-ip:8000/api/v1/top?n=10")
data = response.json()

for asset in data['top_assets']:
    print(f"{asset['rank']}. {asset['ticker']} - Score: {asset['final_score']:.3f}")
```

### Documentação Interativa

```
http://seu-ec2-ip:8000/docs
```

---

## CRON (Atualização Automática)

```bash
# Editar crontab
crontab -e

# Executar pipeline diariamente às 20h (após fechamento B3)
0 20 * * 1-5 docker exec quant-ranker-backend python scripts/run_smart_pipeline.py >> /var/log/quant-pipeline.log 2>&1
```

---

## Configuração

Parâmetros principais em `app/config.py` ou via variáveis de ambiente:

### Pesos do Modelo
```
MOMENTUM_WEIGHT=0.50
QUALITY_WEIGHT=0.15
VALUE_WEIGHT=0.25
RISK_WEIGHT=0.10
```

### Gerenciamento de Risco (v2.7.0)
```
USE_VOLATILITY_TARGETING=true
TARGET_PORTFOLIO_VOLATILITY=0.15
VOLATILITY_LOOKBACK_DAYS=90
USE_SECTOR_LIMITS=true
MAX_SECTOR_EXPOSURE=0.30
MAX_SINGLE_ASSET_WEIGHT=0.25
```

### Filtros de Elegibilidade
```
MINIMUM_VOLUME=5000000
MINIMUM_MARKET_CAP=1000000000
```

---

## Estrutura do Projeto

```
quant_stock_rank/
├── app/                    # Código principal
│   ├── api/                # API REST (FastAPI)
│   ├── backtest/           # Engine de backtest
│   ├── chat/               # Chat com Gemini
│   ├── confidence/         # Motor de confiança
│   ├── core/               # Exceções e utilitários
│   ├── factor_engine/      # Cálculo de fatores
│   ├── filters/            # Filtros de elegibilidade
│   ├── ingestion/          # Ingestão de dados
│   ├── models/             # Modelos SQLAlchemy
│   ├── report/             # Geração de relatórios
│   ├── research/           # App Streamlit de backtest
│   └── scoring/            # Motor de scoring
├── frontend/               # Frontend Streamlit
├── scripts/                # Scripts de pipeline e utilitários
├── deploy/                 # Scripts e docs de deploy
├── docker/                 # Dockerfiles
├── docs/                   # Documentação técnica
└── tests/                  # Testes automatizados
```

---

## Documentação

| Documento | Descrição |
|-----------|-----------|
| `docs/REGRAS_E_CONFIGURACOES.md` | Regras completas do modelo |
| `docs/CALCULOS_RANKING.md` | Detalhes dos cálculos |
| `docs/API_QUICKSTART.md` | Guia rápido da API |
| `docs/API_AS_AI_TOOL.md` | Integração da API com IA |
| `docs/PIPELINE_ARCHITECTURE.md` | Arquitetura dos pipelines |
| `docs/HISTORICAL_EXPANSION.md` | Expansão de dados históricos |
| `docs/DOCKER.md` | Configuração Docker |
| `docs/MCP_SERVER.md` | Servidor MCP |
| `ROBUSTEZ_V2.7.0.md` | Melhorias de robustez v2.7.0 |
| `CHANGELOG.md` | Histórico de mudanças |
| `deploy/README.md` | Guia de deploy |

---

**Versão**: 2.7.0  
**Licença**: Privado  
**Repositório**: https://github.com/edipo-dados/quant_stock_rank
