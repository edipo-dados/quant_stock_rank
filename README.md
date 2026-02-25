# Quant Stock Ranker 📊

Sistema quantitativo de ranking de ações brasileiras usando análise multifatorial com metodologia acadêmica.

**Versão**: 2.5.0 | **Última Atualização**: 2026-02-25

## 🎯 Visão Geral

Sistema completo de análise quantitativa que combina:
- **Momentum** (35%): Momentum acadêmico (exclui último mês), volatilidade, drawdown
- **Qualidade** (25%): ROE, margens, crescimento, estabilidade
- **Valor** (30%): P/L, P/VP, EV/EBITDA, FCF Yield
- **Size** (10%): Size premium (empresas menores)

### ✨ Novidades v2.5.0

- ✅ **Backtest Mensal**: CAGR, Sharpe Ratio, Max Drawdown, Turnover
- ✅ **Suavização Temporal**: Reduz turnover (alpha=0.7)
- ✅ **Momentum Acadêmico**: Exclui último mês (Jegadeesh 1990)
- ✅ **VALUE Expandido**: 5 indicadores (P/L, P/VP, EV/EBITDA, FCF Yield, Debt/EBITDA)
- ✅ **Fator SIZE**: Size premium (Fama-French)
- ✅ **Missing Values**: Tratamento acadêmico (críticos vs secundários)
- ✅ **Sem Penalidades Fixas**: Penalização contínua baseada em fatores

## 🚀 Quick Start

### Opção 1: Docker (Recomendado)

```bash
# Clonar repositório
git clone https://github.com/edipo-dados/quant_stock_rank.git
cd quant_stock_rank

# Configurar ambiente
cp .env.example .env.production
nano .env.production  # Adicionar suas API keys

# Subir aplicação
docker-compose up -d

# Executar pipeline
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode test"
```

Acessar:
- Frontend: http://localhost:8501
- API: http://localhost:8000

### Opção 2: Deploy em EC2

Ver guia completo: [`deploy/SETUP_NOVO_EC2.md`](deploy/SETUP_NOVO_EC2.md)

## 📚 Documentação

### Guias de Deploy
- [Setup Novo EC2](deploy/SETUP_NOVO_EC2.md) - Guia passo a passo para novo servidor
- [EC2 Deploy Completo](deploy/EC2_DEPLOY.md) - Documentação detalhada de deploy
- [Quick Reference](deploy/QUICK_REFERENCE.md) - Comandos úteis

### Documentação Técnica
- [Cálculos de Ranking](docs/CALCULOS_RANKING.md) - Metodologia de scoring completa
- [Backtest e Suavização](docs/BACKTEST_SMOOTHING.md) - Backtest e suavização temporal
- [Melhorias Acadêmicas](docs/MELHORIAS_ACADEMICAS.md) - Todas as melhorias v2.2.0-2.5.0
- [Missing Values](docs/MISSING_VALUE_TREATMENT.md) - Tratamento de valores ausentes
- [Pipeline Inteligente](docs/PIPELINE_INTELIGENTE.md) - Funcionamento do pipeline
- [Chat Gemini](docs/CHAT_GEMINI.md) - Assistente de IA
- [Resumo v2.2.0-2.4.0](docs/SUMMARY_V2.2.0.md) - Resumo das melhorias

### Guias de Uso
- [Guia de Uso](docs/GUIA_USO.md) - Como usar o sistema
- [Docker](docs/DOCKER.md) - Guia Docker
- [Índice de Documentação](docs/INDEX.md) - Índice completo

## 📊 Métricas e Performance

### Backtest
Execute backtests para avaliar estratégias:
```bash
# Backtest básico (último ano, Top 10, equal weight)
docker exec quant-ranker-backend python scripts/run_backtest.py --save

# Backtest customizado
docker exec quant-ranker-backend python scripts/run_backtest.py \
    --start-date 2024-01-01 \
    --top-n 20 \
    --weight-method score_weighted \
    --use-smoothing \
    --save
```

Métricas calculadas:
- **CAGR**: Retorno anualizado composto
- **Sharpe Ratio**: Retorno ajustado ao risco
- **Maximum Drawdown**: Maior queda desde o pico
- **Volatilidade**: Desvio padrão anualizado
- **Turnover**: Mudança média do portfólio

### Suavização Temporal
Reduza turnover com suavização exponencial:
```bash
# Aplicar suavização a todos os scores
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all

# Customizar alpha (0.7 = 70% atual, 30% anterior)
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --alpha 0.8
```

## 🔧 Configuração

### Pesos dos Fatores (.env)
```env
MOMENTUM_WEIGHT=0.35  # 35%
QUALITY_WEIGHT=0.25   # 25%
VALUE_WEIGHT=0.30     # 30%
SIZE_WEIGHT=0.10      # 10%
# Total = 1.00 (100%)
```

### Perfis de Investimento

**Balanceado (Padrão)**:
```env
MOMENTUM_WEIGHT=0.35
QUALITY_WEIGHT=0.25
VALUE_WEIGHT=0.30
SIZE_WEIGHT=0.10
```

**Conservador (Quality)**:
```env
MOMENTUM_WEIGHT=0.20
QUALITY_WEIGHT=0.50
VALUE_WEIGHT=0.30
SIZE_WEIGHT=0.00
```

**Agressivo (Momentum + Size)**:
```env
MOMENTUM_WEIGHT=0.50
QUALITY_WEIGHT=0.15
VALUE_WEIGHT=0.20
SIZE_WEIGHT=0.15
```

## 🔄 Pipeline e Manutenção

### Executar Pipeline
```bash
# Modo test (5 ativos)
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode test

# Modo liquid (50 ativos mais líquidos)
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50
```

### Migrações (Primeira Vez)
```bash
# 1. Momentum acadêmico
docker exec quant-ranker-backend python scripts/migrate_add_academic_momentum.py

# 2. VALUE e SIZE
docker exec quant-ranker-backend python scripts/migrate_add_value_size_factors.py

# 3. Backtest e suavização
docker exec quant-ranker-backend python scripts/migrate_add_backtest_smoothing.py

# 4. Aplicar suavização
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all
```

## 📚 Documentação Completa
- [Docker](docs/DOCKER.md) - Configuração Docker
- [MCP Server](docs/MCP_SERVER.md) - Servidor MCP
- [Guia de Uso](docs/GUIA_USO.md) - Como usar o sistema

### Índices
- [Documentação Geral](docs/INDEX.md)
- [Deploy](deploy/INDEX.md)

## 🏗️ Arquitetura

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend    │────▶│ PostgreSQL  │
│ Streamlit   │     │   FastAPI    │     │  Database   │
│  (8501)     │     │   (8000)     │     │   (5432)    │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Pipeline   │
                    │  Diário/Cron │
                    └──────────────┘
```

## 🔧 Tecnologias

- **Backend**: FastAPI, SQLAlchemy, Pandas
- **Frontend**: Streamlit
- **Database**: PostgreSQL
- **Data Sources**: yfinance, FMP API
- **AI**: Google Gemini 2.5 Flash
- **Deploy**: Docker, Docker Compose

## 📊 Funcionalidades

### 1. Ranking Quantitativo
- Análise multifatorial de ações
- Scores normalizados cross-sectionally
- Ranking diário atualizado

### 2. Chat Assistente (IA)
- Análise de ativos com IA
- Busca web integrada
- Consulta a fontes brasileiras (Status Invest, Investidor10, etc)

### 3. Detalhes do Ativo
- Histórico de scores
- Breakdown por fator
- Métricas fundamentalistas

### 4. Pipeline Automatizado
- Ingestão de dados (preços + fundamentos)
- Cálculo de fatores
- Normalização e scoring
- Execução via cron job

## 🔑 Variáveis de Ambiente

```env
# Database
DATABASE_URL=postgresql://quant_user:quant_password@postgres:5432/quant_ranker
POSTGRES_USER=quant_user
POSTGRES_PASSWORD=quant_password
POSTGRES_DB=quant_ranker

# API Keys
FMP_API_KEY=sua_chave_fmp
GEMINI_API_KEY=sua_chave_gemini

# Scoring Weights
MOMENTUM_WEIGHT=0.4
QUALITY_WEIGHT=0.3
VALUE_WEIGHT=0.3
```

## 🚀 Comandos Úteis

### Docker
```bash
# Ver status
docker-compose ps

# Ver logs
docker logs -f quant-ranker-backend

# Restart
docker-compose restart

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Pipeline
```bash
# Modo teste (5 ativos)
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode test"

# Modo produção (50 ativos líquidos)
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 50"

# Forçar recarga completa
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full"
```

### Database
```bash
# Entrar no PostgreSQL
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker

# Backup
docker exec quant-ranker-db pg_dump -U quant_user quant_ranker > backup.sql

# Restaurar
cat backup.sql | docker exec -i quant-ranker-db psql -U quant_user -d quant_ranker

# Ver contagem de registros
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "SELECT COUNT(*) FROM scores_daily;"
```

## 📅 Cron Job (Pipeline Automático)

Para executar o pipeline automaticamente de segunda a sexta às 13:30:

```bash
crontab -e
```

Adicionar:
```cron
30 13 * * 1-5 cd ~/quant_stock_rank && docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 50" >> ~/pipeline.log 2>&1
```

## 🐛 Troubleshooting

### Containers não sobem
```bash
docker-compose logs
docker-compose down -v
docker system prune -a
docker-compose up -d
```

### Backend não conecta ao banco
```bash
docker logs quant-ranker-db
docker exec quant-ranker-backend printenv | grep DATABASE
```

### Frontend não carrega
```bash
docker logs quant-ranker-frontend
docker-compose restart frontend
```

### Pipeline falha
```bash
docker logs quant-ranker-backend --tail 100
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "SELECT * FROM pipeline_executions ORDER BY execution_date DESC LIMIT 5;"
```

## 📈 Roadmap

- [x] Sistema de ranking multifatorial
- [x] Chat assistente com IA
- [x] Pipeline automatizado
- [x] Deploy em Docker
- [x] Integração com fontes brasileiras
- [ ] Backtesting de estratégias
- [ ] Alertas por email/telegram
- [ ] Dashboard de performance
- [ ] API pública

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Add nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 Changelog

Ver [CHANGELOG.md](CHANGELOG.md) para histórico de versões.

## 📄 Licença

Este projeto é privado e proprietário.

## 👤 Autor

Desenvolvido para análise quantitativa de ações brasileiras.

## 🆘 Suporte

Para problemas ou dúvidas:
1. Verificar [Troubleshooting](#-troubleshooting)
2. Consultar documentação em `docs/`
3. Ver logs: `docker logs quant-ranker-backend`

---

**Versão**: 2.1.0  
**Última atualização**: 24/02/2026
