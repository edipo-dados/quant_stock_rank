# Quant Stock Ranker - Sistema de Ranking Quantitativo de Ações

Sistema quantitativo para ranking e seleção de ações da B3 usando modelo multifator otimizado.

## 🎯 Visão Geral

Sistema completo de análise quantitativa que:
- Ingere dados de preços e fundamentalistas de ações brasileiras
- Calcula fatores quantitativos (momentum, value, quality, risk)
- Gera ranking ponderado por scores
- Executa backtests com filtros de regime de mercado
- **Volatility targeting para controle de risco (v2.7.0)**
- **Limites de exposição por setor (v2.7.0)**
- Fornece API REST e interface Streamlit

## 📊 Modelo Quantitativo

### Fatores e Pesos (Otimizados)

| Fator | Peso | Descrição |
|-------|------|-----------|
| **Momentum** | 50% | Retornos 12M, 6M, 3M com skip de 1 mês |
| **Value** | 25% | P/E, P/B, EV/EBITDA, Dividend Yield |
| **Quality** | 15% | ROE, ROA, Debt/EBITDA, Margem Líquida |
| **Risk** | 10% | Volatilidade e Max Drawdown (penalização) |

### Filtros de Elegibilidade

- **Liquidez**: Volume médio diário > R$ 5.000.000
- **Market Cap**: Capitalização > R$ 1.000.000.000
- **Universo**: Componentes do Ibovespa + ações líquidas da B3

### Otimizações Implementadas

1. **Score-Weighted Portfolio**: Pesos proporcionais aos scores (máx 25% por ativo)
2. **Market Regime Filter**: Filtro baseado em MA200 do IBOVESPA
3. **Temporal Smoothing**: 70% score atual + 30% score anterior
4. **Rebalanceamento Mensal**: Reduz custos de transação
5. **Normalização Min-Max**: Scores entre 0-1 para cada fator
6. **Volatility Targeting (v2.7.0)**: Ajusta exposição para volatilidade alvo de 15%
7. **Sector Limits (v2.7.0)**: Máximo 30% de exposição por setor

## 🚀 Quick Start

### Pré-requisitos

- Docker e Docker Compose
- Chaves de API: FMP (Financial Modeling Prep)

### Configuração

1. Clone o repositório:
```bash
git clone <repo-url>
cd quant_stock_rank
```

2. Configure variáveis de ambiente:
```bash
cp .env.example .env
# Edite .env e adicione sua FMP_API_KEY
```

3. Inicie os containers:
```bash
docker-compose up -d
```

4. Execute o pipeline completo:
```bash
docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py
```

### Acessar Aplicação

- **Frontend (Streamlit)**: http://localhost:8501
- **API (FastAPI)**: http://localhost:8000
- **Documentação API**: http://localhost:8000/docs

## 📁 Estrutura do Projeto

```
quant_stock_rank/
├── app/
│   ├── api/              # Endpoints REST
│   ├── backtest/         # Engine de backtesting
│   ├── confidence/       # Cálculo de confiança
│   ├── factor_engine/    # Cálculo de fatores
│   ├── filters/          # Filtros de elegibilidade
│   ├── ingestion/        # Ingestão de dados
│   ├── models/           # Schemas do banco
│   ├── scoring/          # Sistema de scoring
│   └── config.py         # Configurações centralizadas
├── frontend/             # Interface Streamlit
├── scripts/              # Scripts utilitários
├── docs/                 # Documentação técnica
└── docker/               # Dockerfiles
```

## 🔧 Scripts Principais

### Pipeline Completo
```bash
# Executa ingestão + cálculo de scores + ranking
docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py
```

### Backtest Otimizado
```bash
# Versão v2.6.0 (baseline otimizado)
docker exec -it quant-ranker-backend python scripts/run_optimized_backtest.py

# Versão v2.7.0 (com volatility targeting e sector limits)
docker exec -it quant-ranker-backend python scripts/run_enhanced_backtest.py
```

### Ingestão de Benchmark
```bash
# Ingere dados do IBOVESPA para comparação
docker exec -it quant-ranker-backend python scripts/ingest_benchmark.py
```

### Atualizar Universo de Ações
```bash
# Atualiza lista de ações líquidas dinamicamente
docker exec -it quant-ranker-backend python scripts/update_liquid_stocks.py
```

### Gerar Snapshots Históricos
```bash
# Gera rankings históricos para backtest
docker exec -it quant-ranker-backend python scripts/generate_historical_scores.py \
  --start 2022-01-01 --end 2026-03-01 --frequency monthly
```

## 📈 Performance do Backtest

Resultados do backtest otimizado (2022-2026):

| Métrica | Valor |
|---------|-------|
| **Total Return** | 16.78% |
| **CAGR** | 5.31% |
| **Volatilidade** | 15.62% |
| **Max Drawdown** | -18.01% |
| **Sharpe Ratio** | 0.41 |
| **Sortino Ratio** | 0.83 |
| **Calmar Ratio** | 0.29 |
| **Alpha Anual** | 23.07% |
| **Beta** | 0.62 |
| **Information Ratio** | -0.28 |

## 🔄 Automação (Cron)

Para atualização automática diária:

```bash
# Adicionar ao crontab
0 19 * * 1-5 cd /home/ubuntu/quant_stock_rank && docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py >> /var/log/quant_ranker.log 2>&1
```

Ver `CRON_QUICKSTART.md` para detalhes.

## 📚 Documentação

- **[ROBUSTEZ_V2.7.0.md](ROBUSTEZ_V2.7.0.md)**: Melhorias de robustez v2.7.0
- **[STRATEGY_OPTIMIZATION_QUICKSTART.md](STRATEGY_OPTIMIZATION_QUICKSTART.md)**: Guia de otimização da estratégia
- **[BACKTEST_QUICKSTART.md](BACKTEST_QUICKSTART.md)**: Guia de backtesting
- **[HISTORICAL_EXPANSION_QUICKSTART.md](HISTORICAL_EXPANSION_QUICKSTART.md)**: Expansão histórica de dados
- **[CRON_QUICKSTART.md](CRON_QUICKSTART.md)**: Automação com cron
- **[docs/STRATEGY_OPTIMIZATION_PLAN.md](docs/STRATEGY_OPTIMIZATION_PLAN.md)**: Plano técnico completo
- **[docs/REGRAS_E_CONFIGURACOES.md](docs/REGRAS_E_CONFIGURACOES.md)**: Regras de negócio completas
- **[deploy/](deploy/)**: Guias de deployment

## 🛠️ Tecnologias

- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Frontend**: Streamlit
- **Dados**: yfinance, FMP API
- **Banco**: SQLite (produção: PostgreSQL)
- **Deploy**: Docker, Docker Compose, Nginx

## 📊 API Endpoints

### Ranking Atual
```bash
GET /api/ranking/latest
```

### Ranking por Data
```bash
GET /api/ranking/date/{date}
```

### Histórico de Ativo
```bash
GET /api/asset/{ticker}/history
```

### Executar Pipeline
```bash
POST /api/pipeline/run
```

Ver documentação completa em `/docs` após iniciar a API.

## 🧪 Validação de Dados

```bash
# Verificar cobertura de dados
docker exec -it quant-ranker-backend python scripts/check_historical_coverage.py

# Validar dados de backtest
docker exec -it quant-ranker-backend python scripts/check_backtest_data.py

# Verificar scores mais recentes
docker exec -it quant-ranker-backend python scripts/check_latest_scores.py
```

## 🔐 Segurança

- Nunca commite `.env` com chaves reais
- Use `.env.example` como template
- Em produção, use secrets management (AWS Secrets Manager, etc)

## 📝 Licença

Proprietary - Todos os direitos reservados

## 👥 Contribuindo

Este é um projeto privado. Para contribuir, entre em contato com os mantenedores.

## 📞 Suporte

Para questões técnicas, consulte a documentação em `docs/` ou abra uma issue.

---

**Última atualização**: Março 2026  
**Versão**: 2.7.0  
**Novidades**: Volatility Targeting, Sector Limits, Alpha Corrigido
