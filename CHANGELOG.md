# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [2.7.0] - 2026-03-07

### ✨ Novas Funcionalidades - Robustez da Estratégia

#### 1. Correção Definitiva do Cálculo de Alpha
- **Alinhamento de Retornos**: Garante que retornos da estratégia e benchmark estão na mesma frequência (diária)
- **Remoção de NaN**: Remove valores ausentes antes do cálculo
- **Conversão de Risk-Free Rate**: Converte taxa livre de risco anual para diária (rf_daily = rf_annual / 252)
- **Validações Robustas**: Limita alpha entre -50% e +50%, logs detalhados
- **Documentação**: Comentários passo-a-passo no código

#### 2. Volatility Targeting
- **Risk-Adjusted Weighting**: Pesos ajustados pelo inverso da volatilidade (weight_i = score_i / vol_i)
- **Portfolio Volatility Control**: Ajusta exposição total para atingir volatilidade alvo (15%)
- **Lookback Period**: Usa 90 dias de histórico para cálculo de volatilidade
- **Melhoria Esperada**: Sharpe Ratio +30-50% segundo literatura
- **Configurável**: Pode ser ativado/desativado via `use_volatility_targeting`

#### 3. Limites de Exposição por Setor
- **Máximo por Setor**: Limita exposição a 30% por setor
- **Redistribuição Automática**: Excesso redistribuído proporcionalmente
- **Prevenção de Concentração**: Evita concentração em bancos, commodities, etc
- **Configurável**: Pode ser ativado/desativado via `use_sector_limits`

### 🔧 Melhorias Técnicas

#### Novos Módulos
- `app/backtest/portfolio_risk.py` - Gerenciamento de risco de portfólio
  - `get_asset_volatilities()` - Calcula volatilidades anualizadas
  - `get_asset_sectors()` - Obtém setores dos ativos
  - `get_returns_history()` - Histórico de retornos diários

#### Atualizações em Módulos Existentes
- `app/backtest/portfolio.py`:
  - `apply_volatility_targeting()` - Aplica volatility targeting
  - `apply_sector_limits()` - Aplica limites setoriais
  - `sector_exposures` - Tracking de exposição por setor

- `app/backtest/metrics.py`:
  - `calculate_alpha_beta()` - Versão corrigida com validações
  - Logs detalhados de cálculos intermediários

- `app/backtest/backtest_engine.py`:
  - Novos parâmetros: `use_volatility_targeting`, `use_sector_limits`
  - Integração com `PortfolioRiskManager`

- `app/config.py`:
  - `use_volatility_targeting: bool = True`
  - `target_portfolio_volatility: float = 0.15`
  - `volatility_lookback_days: int = 90`
  - `use_sector_limits: bool = True`
  - `max_sector_exposure: float = 0.30`

### 📊 Scripts Novos
- `scripts/run_enhanced_backtest.py` - Backtest com todas as melhorias v2.7.0

### 📚 Documentação Atualizada
- README.md - Adicionadas novas funcionalidades
- CHANGELOG.md - Documentação completa das mudanças
- docs/REGRAS_E_CONFIGURACOES.md - Novas regras de risco

### 🎯 Resultados Esperados
- **Sharpe Ratio**: Melhoria de 30-50% com volatility targeting
- **Max Drawdown**: Redução com limites setoriais
- **Estabilidade**: Menor volatilidade do portfólio
- **Diversificação**: Melhor distribuição setorial

## [2.6.0] - 2026-03-07

### ✅ Implementado e Validado

#### Otimizações da Estratégia
- **Score-Weighted Portfolio**: Pesos proporcionais aos scores (máx 25% por ativo)
- **Market Regime Filter**: Filtro baseado em MA200 do IBOVESPA (100% bull / 50% bear)
- **Temporal Smoothing**: Suavização 0.7 atual + 0.3 anterior
- **Pesos Multifator Otimizados**: Momentum 50%, Value 25%, Quality 15%, Risk 10%
- **Filtro de Liquidez Aumentado**: Volume mínimo R$ 5M (antes R$ 100k)
- **Rebalanceamento Mensal**: Reduz custos de transação

#### Correções Críticas
- **Cálculo de Alpha/Beta**: Implementado CAPM correto com validações
- **Information Ratio**: Cálculo corrigido com tracking error
- **Ingestão de Benchmark**: Corrigido para lidar com DataFrames do pandas
- **Normalização de Scores**: Min-Max (0-1) em vez de z-score
- **Tickers**: Padronizado sem sufixo .SA no banco

#### Performance Validada (Backtest 2022-2026)
- Total Return: 16.78%
- CAGR: 5.31%
- Alpha Anual: 23.07% ✅
- Beta: 0.62 ✅
- Sharpe: 0.41
- Sortino: 0.83
- Max Drawdown: -18.01%
- Turnover: 19.43%

#### Documentação
- ✅ README.md atualizado com visão geral completa
- ✅ STRATEGY_OPTIMIZATION_QUICKSTART.md com resultados validados
- ✅ docs/REGRAS_E_CONFIGURACOES.md com todas as regras
- ✅ docs/INDEX.md reorganizado
- ✅ Removidos 34 arquivos de teste/debug obsoletos

#### Scripts Principais
- `run_optimized_backtest.py` - Backtest com configurações otimizadas
- `run_smart_pipeline.py` - Pipeline completo de produção
- `update_liquid_stocks.py` - Atualização dinâmica do universo
- `ingest_benchmark.py` - Ingestão do IBOVESPA
- `generate_historical_scores.py` - Geração de snapshots históricos

### 🗑️ Removido

#### Arquivos de Teste/Debug (34 arquivos)
- `scripts/test_*.py` (11 arquivos)
- `scripts/debug_*.py` (4 arquivos)
- `scripts/fix_*.py` (3 arquivos)
- `scripts/diagnose_*.py` (1 arquivo)
- `scripts/investigate_*.py` (1 arquivo)
- `scripts/renormalize_scores.py`
- `scripts/check_itub3.py`

#### Documentação Obsoleta
- `docs/MULTIFACTOR_MODEL_PLAN.md`
- `docs/MELHORIAS_ACADEMICAS.md`
- `docs/BACKTEST_NEXT_STEPS.md`
- `docs/BACKTEST_CORRECTIONS_PLAN.md`
- `docs/BACKTEST_IMPROVEMENTS_PLAN.md`
- `docs/PIPELINE_INTELIGENTE.md`
- `IMPLEMENTATION_SUMMARY.md`
- `ADDITIONAL_IMPROVEMENTS_SUMMARY.md`
- `ADAPTIVE_HISTORY_IMPLEMENTATION.md`
- `HISTORICAL_EXPANSION_SUMMARY.md`
- `scripts/README_DIAGNOSE_ITUB3.md`

## [2.5.0] - 2026-03-06

### Adicionado
- Seleção dinâmica de ações por liquidez (componentes Ibovespa)
- Scripts de diagnóstico de dados
- Validações de métricas de backtest

### Corrigido
- Conversão de dtype em select_top_n()
- Conversão de dtype em get_ranking_snapshot()
- Tratamento de None em métricas de benchmark

## [2.4.0] - 2026-03-05

### Adicionado
- Temporal smoothing dos scores
- Market regime filter (MA200)
- Calmar Ratio
- Sortino Ratio

### Modificado
- Pesos multifator ajustados
- Filtros de elegibilidade aumentados

## [2.3.0] - 2026-03-01

### Adicionado
- Sistema de backtest completo
- Persistência de resultados
- Comparação com benchmark
- Métricas de performance

## [2.2.0] - 2026-02-25

### Adicionado
- Fatores de momentum acadêmico (12M, 6M, 3M)
- Fatores de value (P/E, P/B, EV/EBITDA, DY)
- Fatores de quality (ROE, ROA, Debt/EBITDA, Margem)
- Fatores de risk (Volatilidade, Max Drawdown)

## [2.1.0] - 2026-02-20

### Adicionado
- Pipeline inteligente de ingestão
- Tratamento de missing values
- Sistema de confiança

## [2.0.0] - 2026-02-15

### Adicionado
- Refatoração completa da arquitetura
- Modelo multifator
- API REST com FastAPI
- Interface Streamlit

## [1.0.0] - 2026-02-01

### Adicionado
- Versão inicial
- Ingestão básica de dados
- Cálculo simples de scores
- Ranking básico

---

**Formato**: Baseado em [Keep a Changelog](https://keepachangelog.com/)  
**Versionamento**: [Semantic Versioning](https://semver.org/)
