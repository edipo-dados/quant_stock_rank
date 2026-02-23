# Índice da Documentação

## 📖 Documentação Completa do Sistema de Ranking Quantitativo

Este índice organiza toda a documentação do sistema para facilitar a navegação.

---

## 🚀 Início Rápido

### Para Iniciantes
1. **[README Principal](../README.md)** - Visão geral e início rápido
2. **[Guia de Uso](GUIA_USO.md)** - Tutorial completo passo a passo
3. **[Docker Quickstart](../DOCKER_QUICKSTART.md)** - Referência rápida Docker

### Para Desenvolvedores
1. **[Estrutura de Dados](../ESTRUTURA_DADOS_E_CALCULOS_RANKING.md)** - Schema do banco
2. **[Cálculos de Ranking](CALCULOS_RANKING.md)** - Metodologia detalhada
3. **[API Swagger](http://localhost:8000/docs)** - Documentação interativa

---

## 📚 Documentação por Categoria

### 1. Guias de Uso

| Documento | Descrição | Público |
|-----------|-----------|---------|
| [Guia de Uso](GUIA_USO.md) | Tutorial completo do sistema | Todos |
| [Como Usar Docker](../COMO_USAR_DOCKER.md) | Comandos e configurações Docker | Usuários Docker |
| [Docker Quickstart](../DOCKER_QUICKSTART.md) | Referência rápida Docker | Usuários Docker |

### 2. Documentação Técnica

| Documento | Descrição | Público |
|-----------|-----------|---------|
| [Cálculos de Ranking](CALCULOS_RANKING.md) | Metodologia e fórmulas detalhadas | Desenvolvedores/Analistas |
| [Estrutura de Dados](../ESTRUTURA_DADOS_E_CALCULOS_RANKING.md) | Schema do banco e relacionamentos | Desenvolvedores |
| [Aplicação Docker Completa](../APLICACAO_DOCKER_COMPLETA.md) | Arquitetura e configuração Docker | DevOps |
| [Pipeline Rate Limiting](../DOCKER_PIPELINE_RATE_LIMITING.md) | Pipeline otimizado com rate limiting | Desenvolvedores |

### 3. Documentação da API

| Recurso | URL | Descrição |
|---------|-----|-----------|
| Swagger UI | http://localhost:8000/docs | Documentação interativa |
| ReDoc | http://localhost:8000/redoc | Documentação alternativa |
| Health Check | http://localhost:8000/health | Status da API |

---

## 🎯 Documentação por Caso de Uso

### Quero começar a usar o sistema
1. Leia o [README Principal](../README.md)
2. Siga o [Guia de Uso - Início Rápido](GUIA_USO.md#1-início-rápido)
3. Consulte o [Docker Quickstart](../DOCKER_QUICKSTART.md) se usar Docker

### Quero entender como funciona o ranking
1. Leia [Cálculos de Ranking - Visão Geral](CALCULOS_RANKING.md#visão-geral)
2. Veja [Cálculos de Ranking - Cálculo de Features](CALCULOS_RANKING.md#3-cálculo-de-features)
3. Entenda [Cálculos de Ranking - Score Final](CALCULOS_RANKING.md#6-score-final)

### Quero usar a API
1. Acesse [Swagger UI](http://localhost:8000/docs)
2. Leia [Guia de Uso - Usar a API](GUIA_USO.md#4-usar-a-api)
3. Veja exemplos em [Cálculos de Ranking - Exemplos](CALCULOS_RANKING.md#10-exemplos-de-cálculo)

### Quero executar o pipeline
1. Leia [Guia de Uso - Executar Pipeline](GUIA_USO.md#6-executar-pipeline)
2. Entenda [Pipeline Rate Limiting](../DOCKER_PIPELINE_RATE_LIMITING.md)
3. Configure [Guia de Uso - Configurações Avançadas](GUIA_USO.md#7-configurações-avançadas)

### Quero desenvolver/modificar o sistema
1. Leia [Estrutura de Dados](../ESTRUTURA_DADOS_E_CALCULOS_RANKING.md)
2. Entenda [Cálculos de Ranking - Arquitetura](CALCULOS_RANKING.md#arquitetura-de-cálculo)
3. Veja [README - Desenvolvimento](../README.md#-desenvolvimento)

### Quero fazer deploy em produção
1. Leia [Aplicação Docker Completa](../APLICACAO_DOCKER_COMPLETA.md)
2. Configure [Guia de Uso - Configurações Avançadas](GUIA_USO.md#7-configurações-avançadas)
3. Implemente [Guia de Uso - Backup e Restore](GUIA_USO.md#74-backup-e-restore)

### Estou com problemas
1. Consulte [Guia de Uso - Troubleshooting](GUIA_USO.md#8-troubleshooting)
2. Veja [Aplicação Docker - Troubleshooting](../APLICACAO_DOCKER_COMPLETA.md#troubleshooting)
3. Verifique logs: `docker-compose logs -f`

---

## 📊 Documentação por Componente

### Backend (FastAPI)
- [Estrutura de Dados](../ESTRUTURA_DADOS_E_CALCULOS_RANKING.md) - Schema e modelos
- [API Swagger](http://localhost:8000/docs) - Endpoints
- [Cálculos de Ranking](CALCULOS_RANKING.md) - Lógica de negócio

### Frontend (Streamlit)
- [Guia de Uso - Usar o Frontend](GUIA_USO.md#5-usar-o-frontend)
- Acesse: http://localhost:8501

### Pipeline
- [Pipeline Rate Limiting](../DOCKER_PIPELINE_RATE_LIMITING.md) - Implementação
- [Guia de Uso - Executar Pipeline](GUIA_USO.md#6-executar-pipeline) - Como usar
- [Cálculos de Ranking - Ingestão](CALCULOS_RANKING.md#1-ingestão-de-dados) - Dados

### Banco de Dados
- [Estrutura de Dados](../ESTRUTURA_DADOS_E_CALCULOS_RANKING.md) - Schema completo
- [Guia de Uso - Backup e Restore](GUIA_USO.md#74-backup-e-restore) - Manutenção

### Docker
- [Aplicação Docker Completa](../APLICACAO_DOCKER_COMPLETA.md) - Guia completo
- [Como Usar Docker](../COMO_USAR_DOCKER.md) - Comandos
- [Docker Quickstart](../DOCKER_QUICKSTART.md) - Referência rápida

---

## 🔍 Busca Rápida

### Comandos Mais Usados

```bash
# Iniciar aplicação
docker-compose up -d

# Executar pipeline
docker-compose exec backend python scripts/run_pipeline_docker.py --mode test

# Ver logs
docker-compose logs -f backend

# Parar aplicação
docker-compose down
```

Veja mais em [Docker Quickstart](../DOCKER_QUICKSTART.md).

### Endpoints Mais Usados

```bash
# Ranking completo
curl http://localhost:8000/api/v1/ranking

# Top 10
curl http://localhost:8000/api/v1/top?limit=10

# Detalhes de ativo
curl http://localhost:8000/api/v1/asset/ITUB4.SA
```

Veja mais em [Guia de Uso - API](GUIA_USO.md#4-usar-a-api).

### Configurações Mais Usadas

```env
# Pesos dos fatores
MOMENTUM_WEIGHT=0.4
QUALITY_WEIGHT=0.3
VALUE_WEIGHT=0.3

# Banco de dados
DATABASE_URL=postgresql://user:pass@host:5432/db
```

Veja mais em [Guia de Uso - Configurações](GUIA_USO.md#7-configurações-avançadas).

---

## 📖 Glossário

### Termos Técnicos

- **Momentum**: Tendência de continuação de movimento de preços
- **Quality**: Qualidade dos fundamentos financeiros
- **Value**: Atratividade do valuation (preço vs valor intrínseco)
- **Z-Score**: Normalização estatística (desvios padrão da média)
- **Cross-Sectional**: Comparação entre ativos no mesmo momento
- **Rate Limiting**: Controle de frequência de chamadas à API
- **Elegibilidade**: Critérios mínimos para inclusão no ranking

### Siglas

- **ROE**: Return on Equity (Retorno sobre Patrimônio Líquido)
- **P/E**: Price to Earnings (Preço sobre Lucro)
- **RSI**: Relative Strength Index (Índice de Força Relativa)
- **EBITDA**: Earnings Before Interest, Taxes, Depreciation and Amortization
- **API**: Application Programming Interface
- **REST**: Representational State Transfer

---

## 🔗 Links Úteis

### Aplicação
- Frontend: http://localhost:8501
- API Swagger: http://localhost:8000/docs
- API ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

### Repositório
- GitHub: https://github.com/edipo-dados/quant_stock_rank
- Issues: https://github.com/edipo-dados/quant_stock_rank/issues

### Fontes de Dados
- Yahoo Finance: https://finance.yahoo.com
- B3: https://www.b3.com.br

---

## 📝 Contribuindo com a Documentação

Encontrou um erro ou quer melhorar a documentação?

1. Abra uma issue no GitHub
2. Ou faça um Pull Request com suas sugestões
3. Siga o padrão de formatação Markdown

---

## 📅 Última Atualização

**Data**: 22 de Fevereiro de 2026

**Versão do Sistema**: 1.0.0

**Documentos Atualizados**:
- README.md
- docs/GUIA_USO.md
- docs/CALCULOS_RANKING.md
- docs/INDEX.md

---

## 💡 Dicas

- Use Ctrl+F para buscar termos específicos
- Marque esta página nos favoritos para acesso rápido
- Consulte o [Guia de Uso](GUIA_USO.md) para tutoriais passo a passo
- Veja [Cálculos de Ranking](CALCULOS_RANKING.md) para entender a metodologia
- Use [Docker Quickstart](../DOCKER_QUICKSTART.md) como referência rápida

---

**Precisa de ajuda?** Consulte a seção [Troubleshooting](GUIA_USO.md#8-troubleshooting) ou abra uma issue no GitHub.
