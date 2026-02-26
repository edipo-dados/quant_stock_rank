# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [2.5.2] - 2026-02-26

### 🎯 BREAKING CHANGES
- Remoção completa de valores sentinela (-999)
- Scoring engine agora retorna NaN em vez de -999 para fatores ausentes
- Redistribuição automática de pesos quando categorias têm NaN

### ✨ Added
- Missing value handler com imputação setorial/universal
- Redistribuição automática de pesos no calculate_final_score
- Logs detalhados de imputação
- Tratamento estatístico correto de NaN

### 🔧 Changed
- `calculate_momentum_score`: retorna NaN em vez de -999
- `calculate_quality_score`: retorna NaN em vez de -999
- `calculate_value_score`: retorna NaN em vez de -999
- `calculate_final_score`: redistribui pesos quando há NaN
- Scores agora distribuídos entre -3 e +3 (média ~0)

### 🐛 Fixed
- Scores contaminados por valores sentinela (-549 → 0.00)
- Normalização distorcida por valores extremos
- Sistema instável devido a valores artificiais

### 📊 Results
```
Antes: Média=-549, Desvio=N/A, Range=[-999, -300]
Depois: Média=0.00, Desvio=0.23, Range=[-0.38, 0.25]
```

### 📝 Documentation
- Atualizado README.md com nova arquitetura
- Atualizado PIPELINE_ARCHITECTURE.md
- Removidos arquivos obsoletos de troubleshooting

---

## [2.5.1] - 2026-02-25

### ✨ Added
- Arquitetura de 3 camadas (Eligibility → Feature Engineering → Scoring)
- Missing value handler (`app/factor_engine/missing_handler.py`)
- Logs estruturados por camada
- Análise de missing values antes da imputação
- Resumo de imputações (setor vs universo)

### 🔧 Changed
- Filtro de elegibilidade usa apenas dados brutos
- Features calculadas para TODOS os elegíveis
- Imputação antes da normalização
- Pipeline determinístico

### 🐛 Fixed
- Deadlock lógico (filtro verificava fatores calculados)
- 0 ativos elegíveis → 80% elegíveis
- Exclusão por missing features eliminada

### 📊 Results
```
Taxa de elegibilidade: 0% → 80%
Ativos ranqueados: 0 → 4 (teste)
```

---

## [2.5.0] - 2026-02-24

### ✨ Added
- Fatores acadêmicos de momentum (momentum_6m_ex_1m, momentum_12m_ex_1m)
- Fatores VALUE (pe_ratio, price_to_book, ev_ebitda, fcf_yield)
- Fatores SIZE (size_factor = -log(market_cap))
- Suavização temporal de scores
- Backtest engine completo
- Métricas de performance (Sharpe, Sortino, Max Drawdown)

### 🔧 Changed
- Pesos: Momentum=35%, Quality=25%, Value=30%, Size=10%
- Momentum exclui último mês (evita reversão de curto prazo)
- Normalização cross-sectional com winsorização ±3σ

### 📝 Documentation
- ACADEMIC_MOMENTUM_IMPLEMENTATION.md
- VALUE_SIZE_IMPLEMENTATION.md
- BACKTEST_SMOOTHING.md
- MELHORIAS_ACADEMICAS.md

---

## [2.2.0] - 2026-02-20

### ✨ Added
- Pipeline inteligente (FULL vs INCREMENTAL)
- Rate limiting para APIs externas
- Rastreamento de execuções
- Modo liquid (50 ativos mais líquidos da B3)

### 🔧 Changed
- Ingestão otimizada com batches
- Delay de 2s entre requisições
- Modo incremental busca apenas últimos 7 dias

### 📊 Performance
- FULL: ~15 min (50 ativos)
- INCREMENTAL: ~2 min (50 ativos)

---

## [2.1.0] - 2026-02-15

### ✨ Added
- Chat assistente com Gemini
- Explicações automáticas de scores
- API REST completa
- Frontend Streamlit

### 🔧 Changed
- Arquitetura modular
- Separação backend/frontend
- Docker compose multi-container

---

## [2.0.0] - 2026-02-10

### ✨ Added
- Sistema de scoring multi-fator
- Normalização cross-sectional
- Filtro de elegibilidade
- Banco de dados PostgreSQL
- Docker support

### 🔧 Changed
- Migração de SQLite para PostgreSQL
- Arquitetura em camadas
- Separação de concerns

---

## [1.0.0] - 2026-02-01

### ✨ Added
- Versão inicial
- Ingestão de dados Yahoo Finance
- Cálculo básico de fatores
- Ranking simples

---

## Tipos de Mudanças

- `Added` para novas funcionalidades
- `Changed` para mudanças em funcionalidades existentes
- `Deprecated` para funcionalidades que serão removidas
- `Removed` para funcionalidades removidas
- `Fixed` para correções de bugs
- `Security` para correções de vulnerabilidades

## Versionamento

- **MAJOR**: Mudanças incompatíveis na API
- **MINOR**: Novas funcionalidades compatíveis
- **PATCH**: Correções de bugs compatíveis

Exemplo: v2.5.2
- 2 = MAJOR (arquitetura base)
- 5 = MINOR (features acadêmicas)
- 2 = PATCH (correção de sentinel values)
