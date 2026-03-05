# Plano de Correções e Melhorias - Backtest Quantitativo

## Análise do Estado Atual

### ✅ O que já está implementado corretamente:

1. **Momentum 12-1 (Acadêmico)**: ✅ JÁ IMPLEMENTADO
   - `momentum_12m_ex_1m` e `momentum_6m_ex_1m` já calculados
   - Exclui último mês para evitar reversão de curto prazo
   - Localização: `app/factor_engine/momentum_factors.py`

2. **Filtro de Liquidez**: ✅ JÁ IMPLEMENTADO
   - Volume mínimo configurável
   - Localização: `app/filters/eligibility_filter.py`
   - Critério: `minimum_volume` (configurável em `app/config.py`)

3. **Normalização de Fatores**: ✅ JÁ IMPLEMENTADO
   - Z-score cross-sectional
   - Localização: `app/factor_engine/normalizer.py`

4. **Benchmark IBOVESPA**: ✅ JÁ IMPLEMENTADO
   - Tabela `benchmark_prices` criada
   - Dados ingeridos desde 2021
   - Integrado no BacktestEngine

5. **Lookahead Bias**: ✅ PARCIALMENTE IMPLEMENTADO
   - Snapshots mensais em `ranking_history`
   - Precisa validar timing de execução

### ❌ O que precisa ser corrigido:

1. **Alpha incorreto** (199%)
2. **Information Ratio** incorreto
3. **Falta market cap mínimo** no filtro
4. **Walk Forward Validation** não implementado
5. **Métricas incompletas** (Sortino, Calmar)
6. **Visualizações** precisam melhorar
7. **Logs de backtest** não estruturados

---

## Plano de Implementação

### FASE 1: Correções Críticas de Métricas (PRIORIDADE MÁXIMA)

#### 1.1 Corrigir Cálculo de Alpha

**Problema atual**:
```python
# Código atual em app/backtest/metrics.py (linha ~180)
metrics['alpha'] = (portfolio_return_annual - (risk_free_rate + metrics['beta'] * (benchmark_return_annual - risk_free_rate))) * 100
```

**Problemas**:
- Não está anualizando corretamente
- Pode estar usando retornos mensais sem conversão

**Solução**:
```python
@staticmethod
def calculate_alpha_beta(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 12
) -> Tuple[float, float]:
    """
    Calcula Alpha e Beta usando CAPM.
    
    Beta = Cov(Rs, Rb) / Var(Rb)
    Alpha = E[Rs] - (Rf + Beta * (E[Rb] - Rf))
    
    Onde:
    - Rs = retornos da estratégia
    - Rb = retornos do benchmark
    - Rf = taxa livre de risco
    - E[] = valor esperado (média)
    
    Returns:
        Tuple de (alpha_anualizado, beta)
    """
    # Alinhar séries
    min_len = min(len(strategy_returns), len(benchmark_returns))
    strategy = strategy_returns.iloc[:min_len]
    benchmark = benchmark_returns.iloc[:min_len]
    
    # Calcular Beta
    covariance = strategy.cov(benchmark)
    benchmark_variance = benchmark.var()
    beta = covariance / benchmark_variance if benchmark_variance != 0 else 0.0
    
    # Calcular retornos médios anualizados
    strategy_mean_annual = strategy.mean() * periods_per_year
    benchmark_mean_annual = benchmark.mean() * periods_per_year
    
    # Calcular Alpha anualizado
    alpha = strategy_mean_annual - (risk_free_rate + beta * (benchmark_mean_annual - risk_free_rate))
    
    return alpha * 100, beta  # Alpha em %
```

**Arquivos a modificar**:
- `app/backtest/metrics.py` - Substituir cálculo de alpha/beta

#### 1.2 Corrigir Information Ratio

**Problema atual**:
```python
# Código atual (linha ~185)
excess_returns = returns_aligned - benchmark_aligned
tracking_error = excess_returns.std() * np.sqrt(periods_per_year)
metrics['information_ratio'] = (excess_returns.mean() * periods_per_year) / tracking_error
```

**Problema**: Está correto, mas precisa validar se está sendo chamado corretamente

**Solução**: Adicionar validação e documentação
```python
@staticmethod
def calculate_information_ratio(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    periods_per_year: int = 12
) -> float:
    """
    Calcula Information Ratio.
    
    IR = E[Rs - Rb] / σ[Rs - Rb]
    
    Anualizado:
    IR = (mean(excess_returns) * periods_per_year) / (std(excess_returns) * sqrt(periods_per_year))
    
    Simplifica para:
    IR = mean(excess_returns) / std(excess_returns) * sqrt(periods_per_year)
    """
    # Alinhar séries
    min_len = min(len(strategy_returns), len(benchmark_returns))
    strategy = strategy_returns.iloc[:min_len]
    benchmark = benchmark_returns.iloc[:min_len]
    
    # Calcular excess returns
    excess_returns = strategy - benchmark
    
    # Calcular IR
    mean_excess = excess_returns.mean()
    std_excess = excess_returns.std()
    
    if std_excess == 0:
        return 0.0
    
    # Anualizar
    ir = (mean_excess / std_excess) * np.sqrt(periods_per_year)
    
    return ir
```

#### 1.3 Adicionar Sortino Ratio

**Implementação**:
```python
@staticmethod
def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 12
) -> float:
    """
    Calcula Sortino Ratio (penaliza apenas downside).
    
    Sortino = (E[R] - Rf) / σ_downside
    
    Onde σ_downside = std(retornos negativos)
    """
    mean_return = returns.mean() * periods_per_year
    
    # Calcular downside deviation (apenas retornos negativos)
    downside_returns = returns[returns < 0]
    
    if len(downside_returns) == 0:
        return np.inf  # Sem downside
    
    downside_std = downside_returns.std() * np.sqrt(periods_per_year)
    
    if downside_std == 0:
        return 0.0
    
    sortino = (mean_return - risk_free_rate) / downside_std
    
    return sortino
```

#### 1.4 Adicionar Calmar Ratio

**Implementação**:
```python
@staticmethod
def calculate_calmar_ratio(
    returns: pd.Series,
    periods_per_year: int = 12
) -> float:
    """
    Calcula Calmar Ratio.
    
    Calmar = CAGR / |Max Drawdown|
    """
    cagr = PerformanceMetrics.calculate_cagr(returns, periods_per_year)
    
    cumulative_returns = (1 + returns).cumprod()
    max_dd = PerformanceMetrics.calculate_max_drawdown(cumulative_returns)
    
    if max_dd == 0:
        return np.inf
    
    calmar = (cagr / 100) / abs(max_dd / 100)
    
    return calmar
```

---

### FASE 2: Melhorias no Filtro de Liquidez

#### 2.1 Adicionar Market Cap Mínimo

**Modificar**: `app/filters/eligibility_filter.py`

```python
def __init__(self, config: Settings):
    self.minimum_volume = config.minimum_volume
    self.minimum_market_cap = config.minimum_market_cap  # Novo: 1 bilhão

def is_eligible(self, ticker, fundamentals, volume_data):
    # ... código existente ...
    
    # Novo: Check market cap >= minimum
    market_cap = fundamentals.get('market_cap')
    if market_cap is None or market_cap < self.minimum_market_cap:
        exclusion_reasons.append("low_market_cap")
```

**Adicionar em** `app/config.py`:
```python
class Settings(BaseSettings):
    # ... existente ...
    minimum_market_cap: float = 1_000_000_000  # 1 bilhão
```

---

### FASE 3: Walk Forward Validation

#### 3.1 Implementar Walk Forward Backtest

**Criar**: `app/backtest/walk_forward.py`

```python
class WalkForwardBacktest:
    """
    Implementa Walk Forward Validation para reduzir overfitting.
    
    Divide período em janelas:
    - Treino: 2 anos
    - Teste: 6 meses
    - Desloca janela e repete
    """
    
    def __init__(
        self,
        train_period_months: int = 24,
        test_period_months: int = 6
    ):
        self.train_period_months = train_period_months
        self.test_period_months = test_period_months
    
    def generate_windows(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """
        Gera janelas de treino/teste.
        
        Returns:
            Lista de dicts com:
            {
                'train_start': date,
                'train_end': date,
                'test_start': date,
                'test_end': date
            }
        """
        windows = []
        current_start = start_date
        
        while True:
            # Calcular datas
            train_end = current_start + relativedelta(months=self.train_period_months)
            test_start = train_end + relativedelta(days=1)
            test_end = test_start + relativedelta(months=self.test_period_months)
            
            if test_end > end_date:
                break
            
            windows.append({
                'train_start': current_start,
                'train_end': train_end,
                'test_start': test_start,
                'test_end': test_end
            })
            
            # Deslocar janela
            current_start = test_start
        
        return windows
    
    def run_walk_forward(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        **backtest_params
    ) -> Dict:
        """
        Executa walk forward validation.
        
        Returns:
            Dict com resultados agregados de todas as janelas
        """
        windows = self.generate_windows(start_date, end_date)
        
        results = []
        
        for i, window in enumerate(windows):
            logger.info(f"Window {i+1}/{len(windows)}: "
                       f"Train {window['train_start']} to {window['train_end']}, "
                       f"Test {window['test_start']} to {window['test_end']}")
            
            # Rodar backtest na janela de teste
            engine = BacktestEngine(
                start_date=window['test_start'],
                end_date=window['test_end'],
                **backtest_params
            )
            
            result = engine.run_backtest(db)
            results.append(result)
        
        # Agregar resultados
        aggregated = self.aggregate_results(results)
        
        return aggregated
```

---

### FASE 4: Melhorias na Interface

#### 4.1 Adicionar Tabela de Comparação

**Modificar**: `frontend/pages/4_🔬_Research_Backtest.py`

```python
def display_comparison_table(metrics):
    """Exibe tabela comparativa Estratégia vs Benchmark."""
    
    st.subheader("📊 Comparação Detalhada")
    
    comparison_data = {
        'Métrica': [
            'Total Return',
            'CAGR',
            'Volatilidade',
            'Sharpe Ratio',
            'Max Drawdown'
        ],
        'Estratégia': [
            f"{metrics.total_return:.2%}",
            f"{metrics.cagr:.2%}",
            f"{metrics.volatility:.2%}",
            f"{metrics.sharpe_ratio:.2f}",
            f"{metrics.max_drawdown:.2%}"
        ],
        'IBOVESPA': [
            f"{metrics.benchmark_total_return:.2%}" if metrics.benchmark_total_return else "N/A",
            f"{metrics.benchmark_cagr:.2%}" if metrics.benchmark_cagr else "N/A",
            f"{metrics.benchmark_volatility:.2%}" if metrics.benchmark_volatility else "N/A",
            f"{metrics.benchmark_sharpe:.2f}" if metrics.benchmark_sharpe else "N/A",
            f"{metrics.benchmark_max_drawdown:.2%}" if metrics.benchmark_max_drawdown else "N/A"
        ]
    }
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
```

#### 4.2 Adicionar Gráfico de Drawdown

```python
def display_drawdown_chart(run_id):
    """Exibe gráfico de drawdown ao longo do tempo."""
    
    db = SessionLocal()
    try:
        service = BacktestService(db)
        equity_curve = service.get_equity_curve(run_id)
        
        df = pd.DataFrame(equity_curve)
        
        # Calcular drawdown
        df['cummax'] = df['nav'].cummax()
        df['drawdown'] = (df['nav'] - df['cummax']) / df['cummax']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['drawdown'] * 100,
            mode='lines',
            name='Drawdown',
            fill='tozeroy',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title="Drawdown ao Longo do Tempo",
            xaxis_title="Data",
            yaxis_title="Drawdown (%)",
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    finally:
        db.close()
```

---

### FASE 5: Logs Estruturados

#### 5.1 Adicionar Logging de Rebalanceamentos

**Modificar**: `app/backtest/backtest_engine.py`

```python
def run_backtest(self, db: Session = None) -> Dict:
    # ... código existente ...
    
    # Adicionar após cada rebalanceamento:
    rebalance_log = {
        'date': rebalance_date,
        'selected_tickers': selected_tickers,
        'weights': weights,
        'scores': {ticker: scores_dict.get(ticker) for ticker in selected_tickers},
        'portfolio_value': nav,
        'period_return': portfolio_return,
        'benchmark_return': benchmark_return
    }
    
    logger.info(f"Rebalance log: {rebalance_log}")
```

---

## Cronograma de Implementação

### Sprint 1 (1-2 dias) - CRÍTICO
- ✅ Corrigir Alpha (método separado)
- ✅ Validar Information Ratio
- ✅ Adicionar Sortino Ratio
- ✅ Adicionar Calmar Ratio
- ✅ Testar métricas com dados reais

### Sprint 2 (1 dia)
- ✅ Adicionar market_cap mínimo no filtro
- ✅ Atualizar config.py
- ✅ Testar filtro

### Sprint 3 (2 dias)
- ✅ Implementar Walk Forward Validation
- ✅ Criar interface para WF
- ✅ Documentar uso

### Sprint 4 (1-2 dias)
- ✅ Melhorar visualizações
- ✅ Adicionar tabela comparativa
- ✅ Adicionar gráfico de drawdown
- ✅ Melhorar logs

---

## Validação Final

### Checklist de Qualidade:

- [ ] Alpha entre -10% e +10% (valores razoáveis)
- [ ] Beta entre 0.5 e 1.5 (sensibilidade ao mercado)
- [ ] Information Ratio entre -1 e 2 (consistência)
- [ ] Sortino > Sharpe (penaliza apenas downside)
- [ ] Calmar > 0.5 (retorno vs drawdown)
- [ ] Filtro exclui small caps (<1bi)
- [ ] Walk Forward mostra consistência
- [ ] Gráficos claros e informativos
- [ ] Logs estruturados e úteis

---

## Arquivos a Modificar

```
app/backtest/
├── metrics.py              # Corrigir alpha, adicionar sortino/calmar
├── backtest_engine.py      # Adicionar logs estruturados
└── walk_forward.py         # NOVO - Walk forward validation

app/filters/
└── eligibility_filter.py   # Adicionar market cap mínimo

app/
└── config.py               # Adicionar minimum_market_cap

frontend/pages/
└── 4_🔬_Research_Backtest.py  # Melhorar visualizações

docs/
└── BACKTEST_CORRECTIONS_PLAN.md  # Este arquivo
```

---

## Referências

- Fama-French: "Common risk factors in the returns on stocks and bonds" (1993)
- Jegadeesh & Titman: "Returns to Buying Winners and Selling Losers" (1993)
- CAPM: Sharpe (1964), Lintner (1965)
- Information Ratio: Grinold & Kahn "Active Portfolio Management" (1999)
