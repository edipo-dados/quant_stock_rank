# Plano de Melhorias - Backtest Engine

## Status Atual

### ✅ Já Implementado
1. **Estrutura de tabelas de backtest** - `backtest_runs`, `backtest_nav`, `backtest_positions`, `backtest_metrics`
2. **BacktestEngine básico** - Seleção Top N, rebalanceamento mensal, cálculo de métricas
3. **Interface Streamlit** - Página de Research com configuração e visualização
4. **Scores históricos** - Sistema de snapshots mensais em `ranking_history`
5. **Métricas básicas** - CAGR, Sharpe, Volatilidade, Max Drawdown, Turnover
6. **Fatores implementados** - Momentum (6m/12m ex-1m), Quality (ROE, margins), Value (P/E, EV/EBITDA)

### ❌ Problemas Identificados
1. **Scores N/A nas posições** - ✅ CORRIGIDO (commit 66bbd98)
2. **Sem benchmark (IBOVESPA)** - Não implementado
3. **Custos de transação ignorados** - Não implementado
4. **Fatores incompletos** - Faltam EV/EBIT, FCF Yield, ROIC
5. **Sem validação de dados** - Backtest pode falhar silenciosamente
6. **Métricas incompletas** - Faltam Alpha, Beta, Information Ratio, Calmar Ratio

---

## Plano de Implementação

### FASE 1: Benchmark e Custos (PRIORIDADE ALTA)

#### 1.1 Adicionar Benchmark IBOVESPA
**Objetivo**: Comparar estratégia com mercado

**Implementação**:
```python
# Nova tabela
class BenchmarkPrice(Base):
    __tablename__ = "benchmark_prices"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)  # ^BVSP
    date = Column(Date, nullable=False, index=True)
    close = Column(Float, nullable=False)
    daily_return = Column(Float)
    
    __table_args__ = (
        UniqueConstraint('symbol', 'date', name='uix_benchmark_symbol_date'),
    )
```

**Script de ingestão**:
- `scripts/ingest_benchmark.py` - Buscar ^BVSP do Yahoo Finance
- Rodar diariamente junto com pipeline principal
- Calcular retornos diários automaticamente

**Modificações no BacktestEngine**:
- Adicionar parâmetro `benchmark_symbol='IBOV'`
- Calcular `benchmark_return` para cada período
- Salvar em `backtest_nav.benchmark_nav` e `benchmark_return`

**Métricas adicionais**:
- Alpha = Strategy Return - (Beta × Benchmark Return)
- Beta = Cov(Strategy, Benchmark) / Var(Benchmark)
- Information Ratio = (Strategy Return - Benchmark Return) / Tracking Error

**Arquivos a modificar**:
- `app/backtest/backtest_engine.py` - Adicionar cálculo de benchmark
- `app/backtest/metrics.py` - Adicionar métricas vs benchmark
- `app/models/schemas.py` - Adicionar tabela BenchmarkPrice
- `frontend/pages/4_🔬_Research_Backtest.py` - Exibir benchmark no gráfico

#### 1.2 Implementar Custos de Transação
**Objetivo**: Backtest mais realista

**Implementação**:
```python
# No BacktestEngine
def calculate_transaction_costs(
    old_weights: Dict[str, float],
    new_weights: Dict[str, float],
    transaction_cost_bps: float = 10  # 0.1% = 10 bps
) -> float:
    """
    Calcula custo de transação baseado em turnover.
    
    Args:
        old_weights: Pesos anteriores
        new_weights: Novos pesos
        transaction_cost_bps: Custo em basis points (10 = 0.1%)
    
    Returns:
        Custo total como % do portfólio
    """
    turnover = calculate_turnover(old_weights, new_weights)
    cost = turnover * (transaction_cost_bps / 10000)
    return cost
```

**Aplicação**:
- Subtrair custo do retorno do portfólio em cada rebalanceamento
- `portfolio_return_net = portfolio_return_gross - transaction_cost`
- Salvar custo acumulado em `backtest_metrics`

**Arquivos a modificar**:
- `app/backtest/backtest_engine.py` - Adicionar cálculo de custos
- `app/backtest/models.py` - Adicionar campo `total_transaction_costs`
- `frontend/pages/4_🔬_Research_Backtest.py` - Exibir custos totais

---

### FASE 2: Melhorias nos Fatores (PRIORIDADE MÉDIA)

#### 2.1 Expandir Fatores de Value
**Objetivo**: Adicionar métricas fundamentalistas robustas

**Novos fatores**:
```python
# Em features_monthly
ev_ebit = Column(Float)  # Enterprise Value / EBIT
fcf_yield = Column(Float)  # Free Cash Flow / Market Cap
```

**Cálculo**:
```python
# EV/EBIT
ev_ebit = enterprise_value / ebitda if ebitda > 0 else None

# FCF Yield
fcf_yield = free_cash_flow / market_cap if market_cap > 0 else None
```

**Normalização**:
- Z-score cross-sectional (por data)
- Winsorização em [-3, 3]

**Arquivos a modificar**:
- `app/factor_engine/fundamental_factors.py` - Adicionar cálculos
- `app/scoring/scoring_engine.py` - Incluir no value_score

#### 2.2 Expandir Fatores de Quality
**Objetivo**: Adicionar métricas de qualidade operacional

**Novos fatores**:
```python
# Em features_monthly
roic = Column(Float)  # Return on Invested Capital
debt_to_ebitda = Column(Float)  # Já existe, garantir uso correto
revenue_growth_yoy = Column(Float)  # Growth year-over-year
```

**Cálculo**:
```python
# ROIC
invested_capital = total_assets - current_liabilities
roic = net_income / invested_capital if invested_capital > 0 else None

# Revenue Growth YoY
revenue_growth_yoy = (revenue_current - revenue_previous) / revenue_previous
```

**Arquivos a modificar**:
- `app/factor_engine/fundamental_factors.py` - Adicionar ROIC
- `app/scoring/scoring_engine.py` - Incluir no quality_score

#### 2.3 Refinar Momentum
**Objetivo**: Evitar reversão de curto prazo

**Implementação atual**: ✅ Já usa momentum ex-1m
- `momentum_12m_ex_1m` = return_12m - return_1m
- `momentum_6m_ex_1m` = return_6m - return_1m

**Validação**: Confirmar que está sendo usado corretamente no scoring

---

### FASE 3: Validação e Robustez (PRIORIDADE ALTA)

#### 3.1 Validação Pré-Backtest
**Objetivo**: Evitar backtests com dados incompletos

**Implementação**:
```python
class BacktestValidator:
    """Valida dados antes de executar backtest."""
    
    @staticmethod
    def validate_data_availability(
        db: Session,
        start_date: date,
        end_date: date,
        min_tickers: int = 20
    ) -> Dict[str, Any]:
        """
        Valida disponibilidade de dados.
        
        Returns:
            Dict com status e mensagens de erro
        """
        issues = []
        
        # 1. Verificar scores históricos
        score_count = db.query(ScoreDaily).filter(
            ScoreDaily.date >= start_date,
            ScoreDaily.date <= end_date
        ).count()
        
        if score_count == 0:
            issues.append("Sem scores disponíveis para o período")
        
        # 2. Verificar preços
        price_dates = db.query(distinct(RawPriceDaily.date)).filter(
            RawPriceDaily.date >= start_date,
            RawPriceDaily.date <= end_date
        ).count()
        
        expected_days = (end_date - start_date).days
        if price_dates < expected_days * 0.7:  # 70% dos dias
            issues.append(f"Dados de preços incompletos: {price_dates}/{expected_days} dias")
        
        # 3. Verificar número de tickers
        ticker_count = db.query(distinct(ScoreDaily.ticker)).filter(
            ScoreDaily.date >= start_date,
            ScoreDaily.date <= end_date
        ).count()
        
        if ticker_count < min_tickers:
            issues.append(f"Poucos tickers disponíveis: {ticker_count} < {min_tickers}")
        
        # 4. Verificar benchmark
        benchmark_count = db.query(BenchmarkPrice).filter(
            BenchmarkPrice.date >= start_date,
            BenchmarkPrice.date <= end_date
        ).count()
        
        if benchmark_count == 0:
            issues.append("Benchmark não disponível para o período")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'score_count': score_count,
            'price_dates': price_dates,
            'ticker_count': ticker_count,
            'benchmark_count': benchmark_count
        }
```

**Integração**:
- Chamar antes de `engine.run_backtest()`
- Exibir warnings na interface se houver problemas
- Permitir override com flag `--force`

**Arquivos a criar**:
- `app/backtest/validator.py` - Classe BacktestValidator

#### 3.2 Tratamento de Erros
**Objetivo**: Logs claros e recuperação de falhas

**Implementação**:
- Try-catch em cada etapa do backtest
- Log detalhado de erros
- Salvar status parcial se falhar no meio
- Exibir traceback na interface

**Arquivos a modificar**:
- `app/backtest/backtest_engine.py` - Adicionar try-catch
- `frontend/pages/4_🔬_Research_Backtest.py` - Exibir erros detalhados

---

### FASE 4: Métricas Avançadas (PRIORIDADE MÉDIA)

#### 4.1 Adicionar Métricas Faltantes

**Sortino Ratio**:
```python
def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 12
) -> float:
    """
    Calcula Sortino Ratio (penaliza apenas downside).
    """
    mean_return = returns.mean() * periods_per_year
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std() * np.sqrt(periods_per_year)
    
    if downside_std == 0:
        return 0.0
    
    return (mean_return - risk_free_rate) / downside_std
```

**Calmar Ratio**:
```python
def calculate_calmar_ratio(
    returns: pd.Series,
    periods_per_year: int = 12
) -> float:
    """
    Calcula Calmar Ratio (CAGR / Max Drawdown).
    """
    cagr = calculate_cagr(returns, periods_per_year)
    max_dd = calculate_max_drawdown((1 + returns).cumprod())
    
    if max_dd == 0:
        return 0.0
    
    return cagr / abs(max_dd)
```

**Arquivos a modificar**:
- `app/backtest/metrics.py` - Adicionar funções
- `app/backtest/models.py` - Adicionar campos `calmar_ratio`

---

### FASE 5: Interface e UX (PRIORIDADE BAIXA)

#### 5.1 Melhorar Visualizações

**Gráfico de Equity Curve**:
- Adicionar linha de benchmark
- Adicionar drawdown em subplot
- Adicionar markers nos rebalanceamentos

**Tabela de Métricas**:
- Comparação lado a lado: Strategy vs Benchmark
- Destacar métricas superiores em verde

**Tabela de Posições**:
- Mostrar evolução dos pesos ao longo do tempo
- Heatmap de turnover

#### 5.2 Testes de Robustez

**Configurações múltiplas**:
- Permitir rodar grid search de parâmetros
- Top N: [5, 10, 15, 20]
- Rebalance: [monthly, quarterly]
- Período: [1y, 2y, 3y, 5y]

**Comparação de resultados**:
- Tabela com todas as configurações
- Ordenar por Sharpe Ratio
- Exportar para CSV

---

## Cronograma Sugerido

### Sprint 1 (1-2 dias)
- ✅ Corrigir scores N/A (CONCLUÍDO)
- Implementar benchmark IBOVESPA
- Implementar custos de transação

### Sprint 2 (1-2 dias)
- Adicionar validação pré-backtest
- Melhorar tratamento de erros
- Adicionar métricas vs benchmark (Alpha, Beta, IR)

### Sprint 3 (2-3 dias)
- Expandir fatores de Value (EV/EBIT, FCF Yield)
- Expandir fatores de Quality (ROIC)
- Adicionar métricas avançadas (Sortino, Calmar)

### Sprint 4 (1-2 dias)
- Melhorar visualizações (benchmark no gráfico)
- Implementar testes de robustez
- Documentação final

---

## Arquivos a Criar

```
app/backtest/
├── validator.py          # Validação pré-backtest
└── benchmark.py          # Gerenciamento de benchmark

scripts/
├── ingest_benchmark.py   # Ingestão do IBOVESPA
└── run_robustness_tests.py  # Grid search de parâmetros

docs/
└── BACKTEST_IMPROVEMENTS_PLAN.md  # Este arquivo
```

## Arquivos a Modificar

```
app/backtest/
├── backtest_engine.py    # Benchmark, custos, validação
├── metrics.py            # Novas métricas
├── models.py             # Novos campos
└── repository.py         # Queries de benchmark

app/models/
└── schemas.py            # Tabela BenchmarkPrice

app/factor_engine/
└── fundamental_factors.py  # Novos fatores

app/scoring/
└── scoring_engine.py     # Incluir novos fatores

frontend/pages/
└── 4_🔬_Research_Backtest.py  # Benchmark, validação, UX
```

---

## Priorização

### MUST HAVE (Sprint 1-2)
1. ✅ Scores nas posições
2. Benchmark IBOVESPA
3. Custos de transação
4. Validação de dados
5. Alpha, Beta, Information Ratio

### SHOULD HAVE (Sprint 3)
1. EV/EBIT, FCF Yield
2. ROIC
3. Sortino Ratio, Calmar Ratio
4. Benchmark no gráfico

### NICE TO HAVE (Sprint 4)
1. Testes de robustez
2. Grid search de parâmetros
3. Heatmaps e visualizações avançadas
4. Exportação de resultados

---

## Notas de Implementação

### Benchmark
- Usar símbolo `^BVSP` do Yahoo Finance
- Calcular retornos diários: `(close_t - close_t-1) / close_t-1`
- Sincronizar datas com preços das ações (usar apenas dias com dados)

### Custos de Transação
- Padrão: 0.1% (10 bps) por trade
- Aplicar sobre turnover: `cost = turnover × 0.001`
- Considerar bid-ask spread implícito

### Validação
- Mínimo 70% dos dias com dados de preços
- Mínimo 20 tickers com scores
- Período mínimo: 3 meses
- Alertar mas permitir override

### Performance
- Cachear cálculos de benchmark
- Usar bulk inserts para posições
- Limitar histórico de NAV a 10.000 registros

---

## Referências

- Fama-French Three-Factor Model
- Carhart Four-Factor Model
- Academic papers on momentum (Jegadeesh & Titman)
- Quality factors (Piotroski F-Score)
