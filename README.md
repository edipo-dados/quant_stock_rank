# 📊 Sistema de Ranking Quantitativo de Ações

Sistema automatizado para análise e ranking de ações brasileiras usando fatores quantitativos de momentum, qualidade e valor.

## 🎯 Visão Geral

Avalia ações da B3 através de uma abordagem multi-fator:
- **Momentum** (40%): Tendências de preço e força relativa
- **Qualidade** (30%): Fundamentos e consistência financeira
- **Valor** (30%): Atratividade de valuation

## ✨ Características

- ✅ Análise Multi-Fator com 3 fatores principais
- ✅ Dados em Tempo Real via Yahoo Finance
- ✅ API REST com FastAPI
- ✅ Interface Web com Streamlit
- ✅ Chat com IA (Gemini 2.5 Flash) para análise conversacional
- ✅ MCP Server para integração com agentes de IA
- ✅ Docker com PostgreSQL
- ✅ Pipeline Inteligente (FULL/INCREMENTAL)
- ✅ Rate Limiting para proteção de APIs

## 🚀 Início Rápido

### Pré-requisitos
- Docker e Docker Compose
- Git

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/quant_stock_rank.git
cd quant_stock_rank

# 2. Inicie os containers
docker-compose up -d

# 3. Execute o pipeline inicial
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 200"

# 4. Acesse a aplicação
# Frontend: http://localhost:8501
# API: http://localhost:8000/docs
```


## 📚 Documentação

- **[Guia de Uso](docs/GUIA_USO.md)**: Tutorial completo de uso
- **[Cálculos de Ranking](docs/CALCULOS_RANKING.md)**: Metodologia detalhada
- **[Docker](docs/DOCKER.md)**: Guia completo do Docker
- **[Chat com IA](docs/CHAT_GEMINI.md)**: Como usar o assistente conversacional
- **[MCP Server](docs/MCP_SERVER.md)**: Integração com agentes de IA
- **[API](http://localhost:8000/docs)**: Documentação interativa (Swagger)

## 🔧 Uso Básico

### Executar Pipeline

```bash
# Modo automático (detecta FULL ou INCREMENTAL)
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 200"

# Modo teste (5 ativos)
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode test"
```

### Usar API

```bash
# Health check
curl http://localhost:8000/health

# Ranking completo
curl http://localhost:8000/api/v1/ranking

# Top 10 ativos
curl http://localhost:8000/api/v1/top?n=10
```

### Chat com IA

1. Obtenha API key gratuita: https://makersuite.google.com/app/apikey
2. Acesse http://localhost:8501
3. Navegue para "💬 Chat Assistente"
4. Cole sua API key
5. Converse naturalmente sobre ações!

## 📈 Metodologia

### Fatores Avaliados

**Momentum (40%)**
- Retorno 6 e 12 meses
- RSI 14 dias
- Volatilidade e Drawdown

**Qualidade (30%)**
- ROE e Margem líquida
- Crescimento de receita
- Consistência financeira

**Valor (30%)**
- P/E, P/B, EV/EBITDA
- Debt to EBITDA

Veja detalhes em [Cálculos de Ranking](docs/CALCULOS_RANKING.md).

## ⚙️ Configuração

Edite `.env` para ajustar pesos dos fatores:

```env
MOMENTUM_WEIGHT=0.4  # 40%
QUALITY_WEIGHT=0.3   # 30%
VALUE_WEIGHT=0.3     # 30%
```

## 🛠️ Desenvolvimento

### Estrutura do Projeto

```
quant_stock_rank/
├── app/              # Backend FastAPI
├── frontend/         # Frontend Streamlit
├── scripts/          # Scripts de pipeline
├── tests/            # Testes
├── docker/           # Dockerfiles
└── docs/             # Documentação
```

### Executar Testes

```bash
docker exec quant-ranker-backend bash -c "cd /app && pytest tests/"
```

## 🐛 Troubleshooting

```bash
# Ver logs
docker logs quant-ranker-backend --tail 50

# Reiniciar containers
docker-compose restart

# Reconstruir
docker-compose down
docker-compose build
docker-compose up -d
```

Veja mais em [Guia de Uso - Troubleshooting](docs/GUIA_USO.md).

## 📝 Licença

MIT License - Código aberto

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## ⚠️ Aviso Legal

Este sistema é apenas para fins educacionais e de pesquisa. Não constitui recomendação de investimento. Sempre consulte um profissional qualificado antes de tomar decisões de investimento.

---

**Desenvolvido com ❤️ para a comunidade de investidores quantitativos**
