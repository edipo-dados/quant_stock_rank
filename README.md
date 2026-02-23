# Sistema de Ranking Quantitativo de Ações

Sistema automatizado para análise e ranking de ações brasileiras usando fatores quantitativos de momentum, qualidade e valor.

## 🎯 Visão Geral

Este sistema avalia ações da B3 através de uma abordagem multi-fator que combina:
- **Momentum** (40%): Tendências de preço e força relativa
- **Qualidade** (30%): Fundamentos e consistência financeira
- **Valor** (30%): Atratividade de valuation

O resultado é um ranking objetivo que identifica as ações mais atrativas segundo critérios quantitativos.

## ✨ Características

- ✅ **Análise Multi-Fator**: Combina momentum, qualidade e valor
- ✅ **Dados em Tempo Real**: Integração com Yahoo Finance
- ✅ **API REST**: Endpoints para integração
- ✅ **Interface Web**: Dashboard interativo com Streamlit
- ✅ **Docker**: Deploy simplificado com containers
- ✅ **Rate Limiting**: Proteção contra bloqueio de APIs
- ✅ **Modo Incremental**: Atualizações eficientes
- ✅ **Filtros de Elegibilidade**: Critérios de qualidade mínima
- ✅ **Normalização Cross-Sectional**: Comparação justa entre ativos

## 🚀 Início Rápido

### Pré-requisitos
- Docker e Docker Compose instalados
- Git

### Instalação e Execução

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/quant_stock_rank.git
cd quant_stock_rank

# 2. Configure as variáveis de ambiente (opcional)
cp .env.example .env
# Edite .env se necessário

# 3. Inicie os containers
docker-compose up -d

# 4. Aguarde os containers iniciarem (30-60 segundos)
docker-compose ps

# 5. Execute o pipeline inicial (todos os ativos B3)
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 200"

# 6. Acesse a aplicação
# Frontend: http://localhost:8501
# API: http://localhost:8000/docs
```

### Atualizações Diárias (Modo Incremental)

```bash
# Executa atualização incremental (muito mais rápido)
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 200"
```

## 📊 Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network                            │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐  │
│  │  PostgreSQL  │◄─────┤   Backend    │◄─────┤ Frontend │  │
│  │   (5432)     │      │   FastAPI    │      │Streamlit │  │
│  │              │      │   (8000)     │      │  (8501)  │  │
│  └──────────────┘      └──────────────┘      └──────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Componentes

- **Backend (FastAPI)**: API REST para acesso aos dados e rankings
- **Frontend (Streamlit)**: Interface web interativa
- **PostgreSQL**: Banco de dados relacional
- **Pipeline**: Script de ingestão e processamento com modo FULL e INCREMENTAL

## 📚 Documentação

### Documentação Principal
- **[Guia de Uso](docs/GUIA_USO.md)**: Como usar o sistema (início rápido, API, frontend, pipeline)
- **[Cálculos de Ranking](docs/CALCULOS_RANKING.md)**: Metodologia detalhada dos cálculos
- **[Docker - Aplicação Completa](APLICACAO_DOCKER_COMPLETA.md)**: Guia completo do Docker
- **[Docker - Pipeline Rate Limiting](DOCKER_PIPELINE_RATE_LIMITING.md)**: Pipeline otimizado

### Documentação Técnica
- **[API Swagger](http://localhost:8000/docs)**: Documentação interativa da API
- **[API ReDoc](http://localhost:8000/redoc)**: Documentação alternativa da API
- **[Estrutura de Dados](ESTRUTURA_DADOS_E_CALCULOS_RANKING.md)**: Schema do banco de dados

### Guias Específicos
- **[Como Usar Docker](COMO_USAR_DOCKER.md)**: Comandos e configurações Docker
- **[Docker Quickstart](DOCKER_QUICKSTART.md)**: Referência rápida Docker

## 🔧 Uso

### Executar Pipeline

```bash
# Modo automático (detecta se precisa FULL ou INCREMENTAL)
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 200"

# Forçar modo FULL (primeira execução ou dados antigos)
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 200 --force-full"

# Modo teste (5 ativos apenas)
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode test"
```

### Modos de Execução

**FULL** (primeira execução ou dados >7 dias):
- Busca 400 dias de preços históricos
- Busca todos os fundamentos
- Tempo: ~30-40 minutos para 63 ativos

**INCREMENTAL** (atualizações diárias):
- Busca apenas últimos 7 dias de preços
- Pula fundamentos se já existem
- Tempo: ~5-10 minutos para 63 ativos

### Usar API

```bash
# Health check
curl http://localhost:8000/health

# Ranking completo
curl http://localhost:8000/api/v1/ranking

# Top 10 ativos
curl http://localhost:8000/api/v1/top?n=10

# Detalhes de um ativo
curl http://localhost:8000/api/v1/asset/ITUB4.SA

# Histórico de preços
curl http://localhost:8000/api/v1/prices/PETR4.SA?days=365
```

### Usar Frontend

Acesse http://localhost:8501 e navegue pelas páginas:
- **🏆 Ranking**: Lista completa de ativos ranqueados
- **📊 Detalhes do Ativo**: Análise detalhada por ticker

## 📈 Metodologia

### Fatores Avaliados

#### Momentum (40%)
- Retorno 6 meses
- Retorno 12 meses
- RSI 14 dias
- Volatilidade 90 dias
- Drawdown recente

#### Qualidade (30%)
- ROE (Return on Equity)
- Margem líquida
- Crescimento de receita 3 anos
- ROE médio 3 anos
- Volatilidade do ROE

#### Valor (30%)
- P/E Ratio
- P/B Ratio (Price to Book)
- EV/EBITDA
- Debt to EBITDA

### Processo de Cálculo

1. **Ingestão de Dados**: Yahoo Finance (preços e fundamentos)
2. **Filtro de Elegibilidade**: Critérios de qualidade mínima
3. **Cálculo de Features**: Indicadores por fator
4. **Normalização**: Z-score cross-sectional
5. **Scores por Fator**: Média ponderada das features
6. **Score Final**: Combinação dos 3 fatores
7. **Ranking**: Ordenação por score final

Veja detalhes completos em [Cálculos de Ranking](docs/CALCULOS_RANKING.md).

## ⚙️ Configuração

### Variáveis de Ambiente

Edite `.env` para configurar:

```env
# Banco de Dados
DATABASE_URL=postgresql://quant_user:quant_password@postgres:5432/quant_ranker

# Pesos dos Fatores
MOMENTUM_WEIGHT=0.4  # 40%
QUALITY_WEIGHT=0.3   # 30%
VALUE_WEIGHT=0.3     # 30%

# API
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
```

### Perfis de Investimento

#### Agressivo (Momentum)
```env
MOMENTUM_WEIGHT=0.6
QUALITY_WEIGHT=0.2
VALUE_WEIGHT=0.2
```

#### Conservador (Quality)
```env
MOMENTUM_WEIGHT=0.2
QUALITY_WEIGHT=0.5
VALUE_WEIGHT=0.3
```

#### Value Investing
```env
MOMENTUM_WEIGHT=0.2
QUALITY_WEIGHT=0.3
VALUE_WEIGHT=0.5
```

## 🛠️ Desenvolvimento

### Estrutura do Projeto

```
quant_stock_rank/
├── app/                      # Backend FastAPI
│   ├── api/                  # Rotas e schemas da API
│   ├── confidence/           # Engine de confiança
│   ├── core/                 # Exceções e utilitários
│   ├── factor_engine/        # Cálculo de features
│   ├── filters/              # Filtros de elegibilidade
│   ├── ingestion/            # Ingestão de dados
│   ├── models/               # Schemas do banco
│   ├── report/               # Geração de relatórios
│   └── scoring/              # Cálculo de scores
├── frontend/                 # Frontend Streamlit
│   └── pages/                # Páginas da interface
├── scripts/                  # Scripts de pipeline e utilitários
├── tests/                    # Testes unitários e integração
├── docker/                   # Dockerfiles
├── docs/                     # Documentação
├── docker-compose.yml        # Configuração Docker
├── docker-pipeline.bat       # Script Windows para pipeline
├── docker-start.bat          # Script Windows para iniciar
├── docker-stop.bat           # Script Windows para parar
└── requirements.txt          # Dependências Python
```

### Scripts Disponíveis

**Utilitários:**
- `init_db.py` - Inicializa o banco de dados
- `check_db.py` - Verifica estado do banco
- `check_pipeline_history.py` - Histórico de execuções
- `validate_features.py` - Valida features calculadas
- `recalculate_scores.py` - Recalcula scores existentes
- `test_apis.py` - Testa APIs externas
- `test_docker_deployment.py` - Testa deployment Docker
- `insert_test_data.py` - Insere dados de teste

**Pipeline:**
- `run_pipeline_docker.py` - Pipeline principal (FULL/INCREMENTAL)

### Executar Testes

```bash
# Todos os testes
docker exec quant-ranker-backend bash -c "cd /app && pytest tests/"

# Testes unitários apenas
docker exec quant-ranker-backend bash -c "cd /app && pytest tests/unit/"

# Testes de integração apenas
docker exec quant-ranker-backend bash -c "cd /app && pytest tests/integration/"
```

### Adicionar Novos Fatores

1. Adicione o cálculo em `app/factor_engine/`
2. Atualize o schema em `app/models/schemas.py`
3. Atualize a normalização em `app/factor_engine/normalizer.py`
4. Atualize o scoring em `app/scoring/scoring_engine.py`

## 📊 Dados

### Fontes
- **Yahoo Finance**: Preços diários e fundamentos
- **B3**: Lista de ativos líquidos

### Frequência de Atualização
- **Preços**: Diária (após fechamento do mercado)
- **Fundamentos**: Trimestral/Anual (após divulgação)

### Período Histórico
- **Modo FULL**: 400 dias de preços + 4-5 anos de fundamentos
- **Modo INCREMENTAL**: 7 dias de preços + fundamentos faltantes

## 🔒 Rate Limiting e Performance

O pipeline implementa rate limiting para evitar bloqueio do Yahoo Finance:
- **2 segundos** entre cada ticker
- **5 segundos** entre batches de 5 tickers
- **3 tentativas** automáticas em caso de falha

### Tempo Estimado de Execução

**Modo FULL** (primeira execução):
- 5 ativos: ~2 minutos
- 50 ativos: ~20 minutos
- 63 ativos (B3): ~30-40 minutos

**Modo INCREMENTAL** (atualizações):
- 5 ativos: ~30 segundos
- 50 ativos: ~5 minutos
- 63 ativos (B3): ~5-10 minutos

### Otimizações Implementadas

1. **Modo Incremental**: Busca apenas dados novos
2. **Batch Processing**: Processa em lotes de 5 tickers
3. **Rate Limiting**: Evita bloqueio de API
4. **Retry Logic**: Tenta novamente em caso de falha
5. **Conversão de Tipos**: NumPy → Python nativo antes do banco
6. **Safe Formatting**: Tratamento de None/NaN no frontend

## 🐛 Troubleshooting

### Container não inicia
```bash
# Ver logs
docker logs quant-ranker-backend
docker logs quant-ranker-frontend
docker logs quant-ranker-db

# Reconstruir e reiniciar
docker-compose down
docker-compose build
docker-compose up -d
```

### Banco de dados vazio
```bash
# Verificar estado do banco
docker exec quant-ranker-backend bash -c "cd /app && python scripts/check_db.py"

# Executar pipeline
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode test"
```

### API não responde
```bash
# Testar health check
curl http://localhost:8000/health

# Reiniciar backend
docker restart quant-ranker-backend

# Ver logs
docker logs quant-ranker-backend --tail 50
```

### Frontend com erros
```bash
# Reiniciar frontend
docker restart quant-ranker-frontend

# Ver logs
docker logs quant-ranker-frontend --tail 50

# Reconstruir se necessário
docker-compose build frontend
docker restart quant-ranker-frontend
```

### Erros de formatação (None/NaN)
Os erros de formatação foram corrigidos com:
- Função `safe_format()` no frontend
- Conversão NumPy → Python no backend
- Tratamento de None/NaN em todos os displays

### Histórico de preços não carrega
O sistema agora busca preços da API do backend (banco de dados) em vez do yfinance diretamente.
Se não carregar, verifique se o pipeline foi executado com sucesso.

Veja mais em [Guia de Uso - Troubleshooting](docs/GUIA_USO.md).

## 📝 Licença

Este projeto é de código aberto e está disponível sob a licença MIT.

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:
1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no GitHub.

## 🙏 Agradecimentos

- Yahoo Finance pela API de dados
- B3 pela lista de ativos líquidos
- Comunidade open source pelas bibliotecas utilizadas

---

**Nota**: Este sistema é apenas para fins educacionais e de pesquisa. Não constitui recomendação de investimento. Sempre consulte um profissional qualificado antes de tomar decisões de investimento.
