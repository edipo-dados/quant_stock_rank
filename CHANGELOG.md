# Changelog

## [2.1.0] - 2026-02-23

### ✨ Adicionado
- Chat com IA usando Gemini 2.5 Flash para análise conversacional de ações
- Busca web integrada (DuckDuckGo) para notícias e informações externas
- Funções de contexto de mercado (Ibovespa, USD/BRL, Selic)
- Informações detalhadas de empresas via yfinance
- Chat Assistente como primeira página do aplicativo

### 🐛 Corrigido
- Serialização de valores NaN/Infinity em respostas JSON para Gemini API
- Migração completa para biblioteca google-genai (nova API)
- Imports circulares entre gemini_adapter e routes
- Conexão entre containers Docker (frontend → backend)

### 🔄 Alterado
- Reorganizada estrutura de documentação (tudo em docs/)
- README.md mais conciso e direto
- Removidos 5 arquivos de documentação duplicada
- Documentação consolidada e organizada

### 📚 Documentação
- Movido CHAT_GEMINI.md para docs/
- Movido MCP_SERVER.md para docs/
- Renomeado APLICACAO_DOCKER_COMPLETA.md para docs/DOCKER.md
- Removidos: LEIA-ME-PRIMEIRO.md, DOCKER_QUICKSTART.md, DOCKER_PIPELINE_RATE_LIMITING.md, COMO_USAR_DOCKER.md, ESTRUTURA_DADOS_E_CALCULOS_RANKING.md

## [2.0.0] - 2026-02-22

### ✨ Adicionado
- Endpoint `/api/v1/prices/{ticker}` para buscar histórico de preços do banco de dados
- Função `safe_format()` no frontend para tratamento seguro de None/NaN
- Conversão automática de tipos NumPy para Python nativo antes de salvar no banco
- Rastreamento de execuções do pipeline na tabela `pipeline_executions`
- Suporte completo para todos os ativos líquidos da B3 (63 tickers)
- Campos `enterprise_value` e `book_value_per_share` agora são populados corretamente
- Cálculo de P/B ratio (Price to Book) e EV/EBITDA funcionando

### 🐛 Corrigido
- Erro "schema 'np' does not exist" ao salvar features com tipos NumPy
- Erro "unsupported format string passed to NoneType.__format__" no frontend
- Scores com valores NaN agora são calculados corretamente (tratamento de None/NaN)
- Histórico de preços agora carrega do banco via API em vez de yfinance direto
- Caracteres Unicode (✓, ✗, ⚠, ℹ) substituídos por ASCII para compatibilidade Windows
- Frontend não quebra mais com valores None em scores e métricas

### 🔄 Alterado
- Pipeline agora detecta automaticamente se precisa executar modo FULL ou INCREMENTAL
- Modo FULL busca 400 dias de preços (vs 365 anteriormente)
- Modo INCREMENTAL busca apenas 7 dias de preços
- Frontend busca preços da API do backend em vez de yfinance diretamente
- Melhor tratamento de erros e logging em todo o sistema

### 🗑️ Removido
- Arquivo `quant_ranker.db` (SQLite não é mais usado)
- Scripts antigos: `pipeline-auto.bat`, `pipeline-full.bat`, `pipeline-incremental.bat`
- Scripts de migração já executados: `migrate_asset_info_table.py`, `migrate_score_schema.py`
- Scripts não utilizados: `run_pipeline.py`, `run_pipeline_smart.py`, `fix_pipeline_status.py`
- Configuração do Render: `render.yaml`, `render_init.sh`
- Logs antigos: `pipeline.log`, `pipeline_smart.log`

## [1.0.0] - 2026-02-20

### ✨ Implementado
- Sistema completo de ranking quantitativo multi-fator
- Backend FastAPI com API REST
- Frontend Streamlit interativo
- Pipeline de ingestão com rate limiting
- Suporte a Docker com PostgreSQL
- Modo FULL e INCREMENTAL para pipeline
- Filtros de elegibilidade
- Normalização cross-sectional
- Cálculo de scores por fator (Momentum, Quality, Value)
- Tratamento específico para setores (Financeiro vs Industrial)

### 📚 Documentação
- README.md completo e atualizado
- Guia de Uso detalhado (docs/GUIA_USO.md)
- Documentação de Cálculos de Ranking (docs/CALCULOS_RANKING.md)
- Índice de Documentação (docs/INDEX.md)
- Guias Docker (APLICACAO_DOCKER_COMPLETA.md, DOCKER_QUICKSTART.md, etc)

### 🧹 Limpeza
- Removidos 30+ arquivos de documentação duplicada/obsoleta
- Removidos arquivos de teste temporários
- Removidos scripts batch obsoletos
- Removidos logs e arquivos de banco local
- Organizada estrutura de documentação em pasta docs/

### 🔧 Configuração
- docker-compose.yml configurado com PostgreSQL
- Rate limiting implementado (2s entre tickers, 5s entre batches)
- Variáveis de ambiente configuráveis
- Pesos de fatores ajustáveis

### 📊 Features
- Ingestão de preços diários (Yahoo Finance)
- Ingestão de fundamentos (Yahoo Finance)
- Cálculo de 12+ features quantitativas
- Normalização z-score cross-sectional
- Penalidades de risco
- Ranking automático
- API REST com 3 endpoints principais
- Interface web com 2 páginas

### 🐛 Problemas Conhecidos
- Issue com tipos numpy no PostgreSQL (features não são salvas)
- Workaround: Usar SQLite localmente ou aguardar correção

### 🚀 Próximos Passos
- Corrigir conversão de tipos numpy para PostgreSQL
- Adicionar mais fatores (ESG, Liquidez, etc)
- Implementar backtesting
- Adicionar alertas por email
- Criar dashboard de performance

---

## Arquivos Removidos

### Documentação Duplicada/Obsoleta (30+ arquivos)
- AMBIENTE_INICIADO.md
- ARQUITETURA_HIBRIDA_DOCKER.md
- CHECKLIST_TESTE_DOCKER.md
- COMO_INICIAR.md
- COMO_RODAR_PIPELINE_COM_ROBUSTEZ.md
- COMO_USAR_ATIVOS_LIQUIDOS.md
- DEPLOY_COMPLETO.md
- DEPLOY_RENDER_PRONTO.md
- DEPLOY_RENDER_RESUMO.md
- DEPLOY_RESUMO.md
- DEPLOYMENT_DOCKER_SUCESSO.md
- DOCKER_DEPLOYMENT_SUCCESS.md
- EXEMPLO_USO_RAPIDO.md
- GUIA_CONEXAO_BANCO.md
- GUIA_DEPLOY.md
- GUIA_EXECUCAO_LOCAL.md
- GUIA_RAPIDO.md
- IMPLEMENTACAO_COMPLETA_STATUS.md
- IMPLEMENTACAO_FATORES_SETOR_ESPECIFICO.md
- INICIO_RAPIDO.md
- INSTALACAO_RAPIDA.md
- INSTRUCOES_TESTE_APLICACAO.md
- INSTRUCOES_TESTE_DOCKER.md
- MELHORIAS_APIS_EXTERNAS.md
- MIGRACAO_YAHOO_FINANCE.md
- MIGRATION_GUIDE_SCORING_IMPROVEMENTS.md
- PIPELINE_COMPLETO_SUCESSO.md
- PROBLEMA_FMP_API_FINANCIALS.md
- RESUMO_IMPLEMENTACAO_ROBUSTEZ.md
- ROBUSTNESS_IMPROVEMENTS_SUMMARY.md
- SETUP_LOCAL_RAPIDO.md
- SETUP_LOCAL.md
- SOLUCAO_YAHOO_FINANCE.md
- SUCESSO_SETUP_LOCAL.md
- TESTE_DOCKER.md
- VALIDACAO_FINAL_DOCKER.md
- VALIDATION_SUMMARY.md

### Scripts Batch Obsoletos
- iniciar_local.bat
- iniciar_sistema.bat
- run_all_tests.bat
- run_pipeline_full.bat
- setup_local.bat
- start_all.bat
- start_all_test.bat
- start_api.bat
- start_backend.bat
- start_backend_local.bat
- start_db.bat
- start_dev.bat
- start_frontend.bat
- start_frontend_local.bat
- start_local.bat
- start_sistema_completo.bat
- stop_all.bat
- test_sistema_completo.bat
- test_start_all.bat

### Arquivos de Teste Temporários
- check_americanas.py
- check_eligibility_all.py
- check_pssa3.py
- test_americanas_robustness.py
- test_api_direct.py
- test_api_final.py
- test_api_local.py
- test_api_route.py
- test_docker.bat
- test_docker.sh
- test_docker_complete.py
- test_feature_calc.py
- test_fmp_correct.py
- test_fmp_discovery.py
- test_fmp_endpoints.py
- test_fmp_simple.py
- test_fmp_stable_endpoints.py
- test_fmp_v3_working.py
- test_liquid_stocks.py
- test_list_symbols.py
- test_sector_specific_factors.py
- test_yahoo_docker.py
- test_yahoo_fundamentals.py
- test_yahoo_local.py

### Arquivos de Dados Temporários
- pipeline.log
- quant_ranker.db (SQLite local)

---

## Arquivos Mantidos

### Documentação Principal
- README.md (atualizado)
- APLICACAO_DOCKER_COMPLETA.md
- COMO_USAR_DOCKER.md
- DOCKER_PIPELINE_RATE_LIMITING.md
- DOCKER_QUICKSTART.md
- ESTRUTURA_DADOS_E_CALCULOS_RANKING.md

### Documentação Nova (pasta docs/)
- docs/GUIA_USO.md (novo)
- docs/CALCULOS_RANKING.md (novo)
- docs/INDEX.md (novo)

### Scripts Essenciais
- docker-start.bat
- docker-stop.bat
- docker-pipeline.bat

### Configuração
- .env.example
- .gitignore
- docker-compose.yml
- requirements.txt
- render.yaml

### Código Fonte
- app/ (todo o backend)
- frontend/ (todo o frontend)
- scripts/ (scripts de pipeline)
- tests/ (testes unitários e integração)
- docker/ (Dockerfiles)

---

## Estrutura Final

```
quant_stock_rank/
├── app/                              # Backend FastAPI
├── frontend/                         # Frontend Streamlit
├── scripts/                          # Scripts de pipeline
├── tests/                            # Testes
├── docker/                           # Dockerfiles
├── docs/                             # Documentação organizada
│   ├── GUIA_USO.md                  # Guia completo de uso
│   ├── CALCULOS_RANKING.md          # Metodologia detalhada
│   └── INDEX.md                     # Índice da documentação
├── deploy/                           # Configurações de deploy
├── .streamlit/                       # Configuração Streamlit
├── README.md                         # Documentação principal
├── APLICACAO_DOCKER_COMPLETA.md     # Guia Docker completo
├── COMO_USAR_DOCKER.md              # Comandos Docker
├── DOCKER_PIPELINE_RATE_LIMITING.md # Pipeline otimizado
├── DOCKER_QUICKSTART.md             # Referência rápida
├── ESTRUTURA_DADOS_E_CALCULOS_RANKING.md  # Schema do banco
├── CHANGELOG.md                      # Este arquivo
├── docker-compose.yml                # Configuração Docker
├── requirements.txt                  # Dependências Python
├── .env.example                      # Exemplo de configuração
├── docker-start.bat                  # Iniciar Docker
├── docker-stop.bat                   # Parar Docker
└── docker-pipeline.bat               # Executar pipeline
```

---

## Navegação da Documentação

### Para Começar
1. [README.md](README.md) - Visão geral
2. [docs/GUIA_USO.md](docs/GUIA_USO.md) - Tutorial completo
3. [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) - Referência rápida

### Para Entender
1. [docs/CALCULOS_RANKING.md](docs/CALCULOS_RANKING.md) - Metodologia
2. [ESTRUTURA_DADOS_E_CALCULOS_RANKING.md](ESTRUTURA_DADOS_E_CALCULOS_RANKING.md) - Schema

### Para Usar
1. [docs/GUIA_USO.md](docs/GUIA_USO.md) - Como usar
2. [APLICACAO_DOCKER_COMPLETA.md](APLICACAO_DOCKER_COMPLETA.md) - Docker completo
3. [API Swagger](http://localhost:8000/docs) - API interativa

### Índice Completo
- [docs/INDEX.md](docs/INDEX.md) - Índice de toda documentação

---

## Contribuidores

- Sistema desenvolvido e documentado por equipe de desenvolvimento

---

## Licença

MIT License - Veja LICENSE para detalhes
