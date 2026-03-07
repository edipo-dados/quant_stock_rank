# Documentação do Quant Stock Ranker

Sistema quantitativo de ranking de ações da B3 com modelo multifator otimizado.

## 📚 Índice Geral

### 🚀 Quick Start
- **[../README.md](../README.md)** - Visão geral e instalação
- **[../STRATEGY_OPTIMIZATION_QUICKSTART.md](../STRATEGY_OPTIMIZATION_QUICKSTART.md)** - Guia da estratégia otimizada
- **[../BACKTEST_QUICKSTART.md](../BACKTEST_QUICKSTART.md)** - Guia de backtesting
- **[../CRON_QUICKSTART.md](../CRON_QUICKSTART.md)** - Automação com cron

### 📖 Guias de Uso
- **[GUIA_USO.md](GUIA_USO.md)** - Como usar o sistema
- **[DOCKER.md](DOCKER.md)** - Configuração Docker

### ⚙️ Configurações e Regras
- **[REGRAS_E_CONFIGURACOES.md](REGRAS_E_CONFIGURACOES.md)** - ⭐ Regras de negócio completas
- **[CALCULOS_RANKING.md](CALCULOS_RANKING.md)** - Detalhes dos cálculos
- **[MISSING_VALUE_TREATMENT.md](MISSING_VALUE_TREATMENT.md)** - Tratamento de missing data

### 🏗️ Arquitetura
- **[PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md)** - Arquitetura do pipeline
- **[STRATEGY_OPTIMIZATION_PLAN.md](STRATEGY_OPTIMIZATION_PLAN.md)** - Plano técnico completo

### 📊 Modelos Quantitativos
- **[ACADEMIC_MOMENTUM_IMPLEMENTATION.md](ACADEMIC_MOMENTUM_IMPLEMENTATION.md)** - Momentum acadêmico
- **[VALUE_SIZE_IMPLEMENTATION.md](VALUE_SIZE_IMPLEMENTATION.md)** - Fatores value e size
- **[BACKTEST_SMOOTHING.md](BACKTEST_SMOOTHING.md)** - Temporal smoothing
- **[HISTORICAL_EXPANSION.md](HISTORICAL_EXPANSION.md)** - Expansão histórica

### 🔌 Integrações
- **[CHAT_GEMINI.md](CHAT_GEMINI.md)** - Integração Gemini AI
- **[MCP_SERVER.md](MCP_SERVER.md)** - Model Context Protocol

### 🚀 Deploy
- **[../deploy/INDEX.md](../deploy/INDEX.md)** - Índice de deployment
- **[../deploy/README.md](../deploy/README.md)** - Guia de deployment
- **[../deploy/SETUP_NOVO_EC2.md](../deploy/SETUP_NOVO_EC2.md)** - Setup EC2

## 📊 Performance Atual

| Métrica | Valor |
|---------|-------|
| CAGR | 5.31% |
| Alpha Anual | 23.07% |
| Sharpe Ratio | 0.41 |
| Sortino Ratio | 0.83 |
| Max Drawdown | -18.01% |
| Turnover | 19.43% |

## 🎯 Modelo Multifator

| Fator | Peso |
|-------|------|
| Momentum | 50% |
| Value | 25% |
| Quality | 15% |
| Risk | 10% |

## 🔗 Links Rápidos

- **Configurações**: `app/config.py`
- **Métricas**: `app/backtest/metrics.py`
- **Fatores**: `app/factor_engine/`
- **Scripts**: `scripts/`

---

**Última atualização**: Março 2026  
**Versão**: 2.6.0
