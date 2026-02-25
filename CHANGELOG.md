# Changelog

## [2.5.0] - 2026-02-25

### ✨ Backtest e Suavização Temporal

#### Suavização Temporal
- ✅ **Suavização Exponencial**: `final_score_smoothed = 0.7 * current + 0.3 * previous`
- ✅ Reduz turnover do portfólio (mudanças bruscas no ranking)
- ✅ Nova coluna `final_score_smoothed` em `scores_daily`
- ✅ Módulo `app/scoring/temporal_smoothing.py`
- ✅ Script `scripts/apply_temporal_smoothing.py`
- ✅ Parâmetro `alpha` configurável (default 0.7)

#### Backtest Mensal
- ✅ **Engine de Backtest**: Módulo completo `app/backtest/`
- ✅ **Snapshots Mensais**: Tabela `ranking_history` para histórico
- ✅ **Seleção Top N**: Seleciona N melhores ativos por score
- ✅ **Ponderação**: Equal weight ou score weighted
- ✅ **Rebalanceamento**: Mensal (último dia útil)
- ✅ **Métricas**:
  - CAGR (Compound Annual Growth Rate)
  - Sharpe Ratio
  - Maximum Drawdown
  - Volatilidade anualizada
  - Turnover médio
- ✅ **Persistência**: Tabela `backtest_results` para resultados
- ✅ Script `scripts/run_backtest.py`

#### Banco de Dados
- ✅ Nova coluna: `scores_daily.final_score_smoothed`
- ✅ Nova tabela: `ranking_history` (snapshots mensais)
- ✅ Nova tabela: `backtest_results` (resultados de backtests)
- ✅ Script de migração: `scripts/migrate_add_backtest_smoothing.py`

#### Documentação
- ✅ `docs/BACKTEST_SMOOTHING.md`: Guia completo
- ✅ Exemplos de uso e estratégias
- ✅ Workflow completo

### 📝 Arquivos Criados
- `app/backtest/__init__.py`
- `app/backtest/backtest_engine.py`
- `app/backtest/portfolio.py`
- `app/backtest/metrics.py`
- `app/scoring/temporal_smoothing.py`
- `scripts/migrate_add_backtest_smoothing.py`
- `scripts/apply_temporal_smoothing.py`
- `scripts/run_backtest.py`
- `docs/BACKTEST_SMOOTHING.md`

### 🎯 Benefícios
- ✅ Avaliação objetiva de estratégias
- ✅ Redução de turnover (menores custos)
- ✅ Métricas padronizadas (CAGR, Sharpe, etc.)
- ✅ Comparação de estratégias
- ✅ Otimização de parâmetros

### 📚 Referências
- Hyndman & Athanasopoulos (2018): Exponential Smoothing
- Bacon (2008): Portfolio Performance Measurement
- Sharpe (1966): Sharpe Ratio
- Frazzini et al. (2018): Transaction Costs

## [2.4.0] - 2026-02-25

### ✨ Tratamento de Valores Ausentes e Remoção de Penalidades Fixas

#### Tratamento de Missing Values
- ✅ **Classificação de Fatores**: Fatores divididos em críticos (exclusão) e secundários (imputação)
- ✅ **Fatores Críticos** (ausência = exclusão do ranking):
  - Momentum: `momentum_6m_ex_1m`, `momentum_12m_ex_1m`
  - Quality: `roe_mean_3y`, `net_margin`
  - Value: `pe_ratio`, `price_to_book`
- ✅ **Fatores Secundários** (ausência = imputação setorial):
  - Momentum: `volatility_90d`, `recent_drawdown`
  - Quality: `roe_volatility`, `revenue_growth_3y`, `debt_to_ebitda`
  - Value: `ev_ebitda`, `fcf_yield`
- ✅ **Imputação Setorial**: Valores ausentes de fatores secundários imputados com média do setor
- ✅ **Filtro de Elegibilidade**: Verifica presença de fatores críticos antes do scoring

#### Remoção de Penalidades Fixas
- ✅ **Removidas penalidades arbitrárias**:
  - `debt_to_ebitda > 5` → penalidade de 50% (REMOVIDO)
  - `net_income < 0` → penalidade de 60% (REMOVIDO)
- ✅ **Penalização Contínua**: Risco capturado diretamente em fatores normalizados
- ✅ **Critérios Extremos**: Movidos para filtro de elegibilidade:
  - `debt_to_ebitda > 8` → exclusão
  - `net_income < 0` no último ano → exclusão
  - `net_income < 0` em 2 dos últimos 3 anos → exclusão

#### Scoring Engine
- ✅ Atualizado `calculate_momentum_score()` com tratamento de missing
- ✅ Atualizado `calculate_quality_score()` com tratamento de missing e remoção de penalidades
- ✅ Atualizado `calculate_value_score()` com tratamento de missing
- ✅ Score = -999.0 quando fatores críticos ausentes
- ✅ Score calculado com fatores disponíveis quando secundários ausentes

#### Normalizer
- ✅ Novo método `impute_missing_with_sector_mean()` para imputação setorial
- ✅ Atualizado `normalize_factors_sector_neutral()` com parâmetro `impute_missing`
- ✅ Fallback para média global quando setor não tem valores suficientes

#### Eligibility Filter
- ✅ Verificação de fatores críticos adicionada
- ✅ Razões de exclusão incluem fatores críticos ausentes
- ✅ Critérios extremos de risco movidos do scoring para filtro

#### Documentação
- ✅ Criado `docs/MISSING_VALUE_TREATMENT.md` com metodologia completa
- ✅ Atualizado `docs/MELHORIAS_ACADEMICAS.md` com seções 5 e 6
- ✅ Criado `docs/SUMMARY_V2.2.0.md` com resumo de todas as melhorias

### 📝 Arquivos Modificados
- `app/scoring/scoring_engine.py`: Tratamento de missing e remoção de penalidades
- `app/factor_engine/normalizer.py`: Imputação setorial
- `app/filters/eligibility_filter.py`: Verificação de fatores críticos

### 🎯 Benefícios
- ✅ Maior precisão: valores ausentes não confundidos com valores ruins
- ✅ Robustez: imputação setorial preserva características setoriais
- ✅ Transparência: razões de exclusão registradas no banco
- ✅ Penalização contínua: sem thresholds arbitrários
- ✅ Alinhamento acadêmico: metodologia baseada em literatura

### 📚 Referências Acadêmicas
- Little, R. J., & Rubin, D. B. (2019). "Statistical Analysis with Missing Data" (3rd ed.). Wiley.
- Enders, C. K. (2010). "Applied Missing Data Analysis". Guilford Press.
- Piotroski, J. D. (2000). "Value Investing". *Journal of Accounting Research*, 38, 1-41.
- Altman, E. I. (1968). "Financial Ratios and Corporate Bankruptcy". *Journal of Finance*, 23(4), 589-609.

## [2.3.0] - 2026-02-25

### ✨ Expansão do Fator VALUE e Implementação do Fator SIZE

#### Novos Fatores VALUE
- ✅ **Price-to-Book**: `Market Cap / Shareholders Equity` (invertido - menor é melhor)
- ✅ **FCF Yield**: `Free Cash Flow / Market Cap` (maior é melhor)
- ✅ **EV/EBITDA**: Calculado a partir de componentes `(Market Cap + Debt - Cash) / EBITDA`
- ✅ Value Score agora usa 5 indicadores: `pe_ratio`, `ev_ebitda`, `price_to_book`, `fcf_yield`, `debt_to_ebitda`

#### Fator SIZE (Size Premium)
- ✅ **Size Factor**: `-log(market_cap)` para capturar size premium
- ✅ Empresas menores têm valores maiores (size premium documentado por Fama-French)
- ✅ **SIZE_WEIGHT** configurável (default 0.0 = desabilitado, recomendado 0.1)
- ✅ Score final agora inclui: `momentum + quality + value + size`

#### Banco de Dados
- ✅ Adicionadas colunas à tabela `features_monthly`:
  - `price_to_book`: Price-to-Book usando market cap
  - `fcf_yield`: Free Cash Flow Yield
  - `size_factor`: -log(market_cap) para size premium
- ✅ Script de migração: `scripts/migrate_add_value_size_factors.py`

#### Configuração
- ✅ Novo parâmetro `SIZE_WEIGHT` em config (default 0.0)
- ✅ Pesos recomendados com SIZE: momentum=0.35, quality=0.25, value=0.30, size=0.10

#### Documentação
- ✅ Criado `docs/VALUE_SIZE_IMPLEMENTATION.md` com detalhes completos
- ✅ Justificativa acadêmica: Fama-French (1992, 1993), Banz (1981)
- ✅ Configurações recomendadas para diferentes perfis de investimento

### 📝 Arquivos Modificados
- `app/factor_engine/fundamental_factors.py`: Novos métodos de cálculo VALUE e SIZE
- `app/models/schemas.py`: Novas colunas em FeatureMonthly
- `app/factor_engine/feature_service.py`: Salvamento de novos campos
- `app/config.py`: Adicionado SIZE_WEIGHT
- `app/scoring/scoring_engine.py`: Value score expandido e size score implementado

### 🔮 Próximos Passos (Opcional)
- [ ] Ativar SIZE factor ajustando SIZE_WEIGHT=0.1 no .env
- [ ] Melhorar disponibilidade de market_cap para mais ativos
- [ ] Backtesting com diferentes configurações de pesos

## [2.2.0] - 2026-02-25

### ✨ Melhorias Acadêmicas Implementadas

#### Momentum Acadêmico (Excluindo Último Mês)
- ✅ Implementado `momentum_6m_ex_1m` = return_6m - return_1m
- ✅ Implementado `momentum_12m_ex_1m` = return_12m - return_1m
- ✅ Adicionado `return_1m` para cálculo de momentum ex-1m
- ✅ RSI removido do score final (mantido para compatibilidade)
- ✅ Score de momentum agora usa apenas: momentum_6m_ex_1m, momentum_12m_ex_1m, -volatility_90d, -recent_drawdown
- 📚 Justificativa: Evita efeito de reversão de curto prazo (Jegadeesh 1990, Lehmann 1990)

#### Normalização Setorial (Implementada, Não Ativada)
- ✅ Implementado `sector_neutral_zscore()` no CrossSectionalNormalizer
- ✅ Z-score calculado dentro de cada setor (intra-sector comparison)
- ✅ Fallback para z-score global quando setor < 5 ativos
- ✅ Método `normalize_factors_sector_neutral()` disponível
- ⚠️ Não ativado no pipeline (requer dados de setor)
- 📝 Para ativar: Adicionar coluna 'sector' ao DataFrame e usar normalize_factors_sector_neutral()

#### Banco de Dados
- ✅ Adicionadas colunas à tabela `features_daily`:
  - `return_1m`: Retorno de 1 mês
  - `momentum_6m_ex_1m`: Momentum 6m excluindo último mês
  - `momentum_12m_ex_1m`: Momentum 12m excluindo último mês
- ✅ `rsi_14` mantido para compatibilidade mas não usado no score

#### Documentação
- ✅ Atualizado `docs/CALCULOS_RANKING.md` com metodologia acadêmica
- ✅ Adicionadas referências: Jegadeesh (1990), Lehmann (1990)
- ✅ Documentado status de RSI como descontinuado
- ✅ Explicada justificativa de momentum ex-1m

### 📝 Arquivos Modificados
- `app/factor_engine/momentum_factors.py`: Novos métodos de momentum
- `app/factor_engine/normalizer.py`: Normalização setorial
- `app/scoring/scoring_engine.py`: Score de momentum atualizado
- `app/factor_engine/feature_service.py`: Salvamento de novos campos
- `app/models/schemas.py`: Novas colunas em FeatureDaily
- `docs/CALCULOS_RANKING.md`: Documentação atualizada

### 🔮 Próximos Passos (Opcional)
- [ ] Adicionar ingestão de dados de setor (AssetInfo)
- [ ] Ativar normalização setorial no pipeline
- [ ] Testar impacto de normalização setorial vs percentile ranking

## [2.1.1] - 2026-02-24

### 🐛 Corrigido
- Pipeline: Adicionados campos `cash` e `total_assets` ao dicionário fundamentals_data
- Pipeline: Implementado filtro de colunas numéricas antes da normalização
- Pipeline: Corrigido erro "unhashable type: 'list'" ao normalizar net_income_history
- Pipeline: Melhorado logging com traceback completo para debug

### ✨ Adicionado
- Documentação: SETUP_NOVO_EC2.md - Guia simples de setup para novo servidor
- Documentação: Guia de configuração de cron job para pipeline automático
- Documentação: Comandos úteis para execução manual do pipeline

### 🗑️ Removido
- Arquivos temporários: QUICK_FIX.md, RESUMO_CORRECAO.md, TESTE_EC2.md
- Documentação obsoleta: RENDER_*.md, railway.md, DECISION_TREE.md

### 📚 Documentação
- README.md: Atualizado com informações completas e atuais
- deploy/INDEX.md: Reorganizado com fluxo claro de deploy
- Estrutura de documentação consolidada e limpa

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
