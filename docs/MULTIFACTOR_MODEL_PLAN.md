# Plano de Implementação - Modelo Multifator Robusto

## Análise do Estado Atual

### ✅ O que já está implementado:

1. **Filtros de Liquidez**: ✅ IMPLEMENTADO
   - `minimum_volume` configurável (padrão: 100.000)
   - Localização: `app/filters/eligibility_filter.py`
   - ❌ FALTA: `minimum_market_cap` (1 bilhão)

2. **Fatores de Momentum**: ✅ PARCIALMENTE IMPLEMENTADO
   - ✅ `momentum_12m_ex_1m` (12 meses excluindo último mês)
   - ✅ `momentum_6m_ex_1m` (6 meses excluindo último mês)
   - ✅ `return_6m`, `return_12m`, `return_1m`
   - ❌ FALTA: `return_3m`
   - Localização: `app/factor_engine/momentum_factors.py`

3. **Fatores de Value**: ✅ PARCIALMENTE IMPLEMENTADO
   - ✅ `pe_ratio`, `pb_ratio` (price_to_book)
   - ✅ `ev_ebitda`
   - ✅ `fcf_yield` (Free Cash Flow Yield)
   - Localização: `app/factor_engine/fundamental_factors.py`

4. **Fatores de Quality**: ✅ PARCIALMENTE IMPLEMENTADO
   - ✅ `roe`, `net_margin`
   - ✅ `debt_to_ebitda`
   - ❌ FALTA: `roic` (Return on Invested Capital)
   - Localização: `app/factor_engine/fundamental_factors.py`

5. **Fatores de Risk**: ✅ PARCIALMENTE IMPLEMENTADO
   - ✅ `volatility_90d`, `volatility_180d`
   - ✅ `max_drawdown_3y`
   - ❌ FALTA: `volatility_1y`, `max_drawdown_1y`
   - Localização: `app/factor_engine/momentum_factors.py`

6. **Normalização**: ✅ IMPLEMENTADO
   - Z-score cross-sectional
   - Winsorização
   - Localização: `app/factor_engine/normalizer.py`

7. **Scoring Engine**: ✅ IMPLEMENTADO
   - Combina fatores com pesos configuráveis
   - Localização: `app/scoring/scoring_engine.py`

8. **Backtest Engine**: ✅ IMPLEMENTADO
   - Rebalanceamento mensal
   - Métricas completas (CAGR, Sharpe, Sortino, Calmar, Alpha, Beta, IR)
   - Benchmark IBOVESPA
   - Localização: `app/backtest/backtest_engine.py`

### ❌ O que precisa ser implementado/corrigido:

1. **Market Cap Mínimo** no filtro (1 bilhão)
2. **Return 3 meses** no momentum
3. **ROIC** no quality
4. **Volatilidade 1 ano** e **Max Drawdown 1 ano** no risk
5. **Pesos do modelo** ajustados (0.4 momentum, 0.3 value, 0.2 quality, 0.1 risk)
6. **Análises adicionais** no relatório
7. **Visualizações** melhoradas no dashboard

---

## Plano de Implementação

### FASE 1: Completar Fatores Faltantes (PRIORIDADE ALTA)

#### 1.1 Adicionar Market Cap Mínimo

**Modificar**: `app/config.py`
```python
class Settings(BaseSettings):
    # ... existente ...
    minimum_volume: float = 100000  # Já existe
    minimum_market_cap: float = 1_000_000_000  # NOVO: 1 bilhão
```

**Modificar**: `app/filters/eligibility_filter.py`
```python
def __init__(self, config: Settings):
    self.minimum_volume = config.minimum_volume
    self.minimum_market_cap = config.minimum_market_cap  # NOVO

def is_eligible(self, ticker, fundamentals, volume_data):
    # ... código existente ...
    
    # NOVO: Check market cap >= minimum
    market_cap = fundamentals.get('market_cap')
    if market_cap is None or market_cap < self.minimum_market_cap:
        exclusion_reasons.append("low_market_cap")
```

#### 1.2 Adicionar Return 3 Meses

**Modificar**: `app/factor_engine/momentum_factors.py`
```python
def calculate_return_3m(self, prices: pd.DataFrame) -> float:
    """
    Calcula retorno acumulado dos últimos 3 meses.
    
    Retorno = (Preço_final / Preço_inicial) - 1
    
    Args:
        prices: DataFrame com coluna 'adj_close'
        
    Returns:
        Retorno de 3 meses como float
    """
    try:
        if len(prices) < 63:  # ~3 meses de dias úteis
            raise InsufficientDataError(
                f"Need at least 63 days for 3m return, got {len(prices)}"
            )
        
        recent_prices = prices.tail(63)
        initial_price = recent_prices['adj_close'].iloc[0]
        final_price = recent_prices['adj_close'].iloc[-1]
        
        if pd.isna(initial_price) or pd.isna(final_price):
            raise InsufficientDataError("Missing price data for 3m return")
        
        if initial_price <= 0:
            raise CalculationError(f"Invalid initial price: {initial_price}")
        
        return (final_price / initial_price) - 1
        
    except (TypeError, ValueError, KeyError) as e:
        raise CalculationError(f"Error calculating 3m return: {e}")

def calculate_all_factors(self, ticker, prices):
    # ... código existente ...
    
    # NOVO: Return 3m
    try:
        factors['return_3m'] = self.calculate_return_3m(prices)
    except (InsufficientDataError, CalculationError) as e:
        logger.warning(f"Could not calculate 3m return for {ticker}: {e}")
        factors['return_3m'] = None
```

#### 1.3 Adicionar ROIC (Return on Invested Capital)

**Modificar**: `app/factor_engine/fundamental_factors.py`
```python
def calculate_roic(self, fundamentals: Dict[str, float]) -> float:
    """
    Calcula ROIC (Return on Invested Capital).
    
    ROIC = NOPAT / Invested Capital
    
    Onde:
    - NOPAT = Net Operating Profit After Tax ≈ EBITDA * (1 - tax_rate)
    - Invested Capital = Total Assets - Current Liabilities
    
    Simplificação:
    ROIC ≈ Net Income / (Total Assets - Current Liabilities)
    
    Args:
        fundamentals: Dict com net_income, total_assets, current_liabilities
        
    Returns:
        ROIC como float (ex: 0.15 para 15%)
    """
    net_income = fundamentals.get('net_income')
    total_assets = fundamentals.get('total_assets')
    current_liabilities = fundamentals.get('current_liabilities')
    
    if net_income is None or total_assets is None:
        return None
    
    # Se current_liabilities não disponível, usar total_assets como proxy
    if current_liabilities is None:
        invested_capital = total_assets
    else:
        invested_capital = total_assets - current_liabilities
    
    if invested_capital <= 0:
        return None
    
    roic = net_income / invested_capital
    
    return roic
```

#### 1.4 Adicionar Volatilidade 1 Ano e Max Drawdown 1 Ano

**Modificar**: `app/factor_engine/momentum_factors.py`
```python
def calculate_volatility_1y(self, prices: pd.DataFrame) -> float:
    """
    Calcula volatilidade de 1 ano (252 dias úteis).
    
    Volatilidade = std(retornos diários) * sqrt(252) (anualizada)
    """
    try:
        if len(prices) < 253:
            raise InsufficientDataError(
                f"Need at least 253 days for 1y volatility, got {len(prices)}"
            )
        
        recent_prices = prices.tail(253)
        returns = recent_prices['adj_close'].pct_change().dropna()
        
        if len(returns) < 252:
            raise InsufficientDataError("Insufficient returns for volatility")
        
        daily_std = returns.std()
        
        if pd.isna(daily_std):
            raise InsufficientDataError("Could not calculate standard deviation")
        
        annualized_vol = daily_std * np.sqrt(252)
        
        return annualized_vol
        
    except (TypeError, ValueError, KeyError) as e:
        raise CalculationError(f"Error calculating 1y volatility: {e}")

def calculate_max_drawdown_1y(self, prices: pd.DataFrame) -> float:
    """
    Calcula drawdown máximo de 1 ano (252 dias úteis).
    
    Drawdown máximo = min((Preço - Pico_anterior) / Pico_anterior)
    """
    try:
        if len(prices) < 252:
            raise InsufficientDataError(
                f"Need at least 252 days for 1y max drawdown, got {len(prices)}"
            )
        
        recent_prices = prices.tail(252)
        close_prices = recent_prices['adj_close']
        running_max = close_prices.expanding().max()
        drawdowns = (close_prices - running_max) / running_max
        max_drawdown = drawdowns.min()
        
        if pd.isna(max_drawdown):
            raise InsufficientDataError("Could not calculate max drawdown")
        
        return max_drawdown
        
    except (TypeError, ValueError, KeyError) as e:
        raise CalculationError(f"Error calculating 1y max drawdown: {e}")
```

---

### FASE 2: Ajustar Pesos do Modelo

#### 2.1 Atualizar Configuração de Pesos

**Modificar**: `app/config.py`
```python
class Settings(BaseSettings):
    # ... existente ...
    
    # Scoring Weights (Modelo Multifator Robusto)
    momentum_weight: float = 0.4  # Aumentar de 0.35 para 0.4
    value_weight: float = 0.3     # Manter
    quality_weight: float = 0.2   # Reduzir de 0.25 para 0.2
    size_weight: float = 0.0      # Remover (ou manter 0)
    risk_weight: float = 0.1      # NOVO: Low Volatility Premium
```

#### 2.2 Atualizar Scoring Engine

**Modificar**: `app/scoring/scoring_engine.py`
```python
def __init__(self, config: Optional[Settings] = None):
    # ... código existente ...
    
    self.momentum_weight = config.momentum_weight  # 0.4
    self.quality_weight = config.quality_weight    # 0.2
    self.value_weight = config.value_weight        # 0.3
    self.risk_weight = config.risk_weight          # 0.1 (NOVO)
    
    # Validar que pesos somam 1.0
    total_weight = (self.momentum_weight + self.quality_weight + 
                   self.value_weight + self.risk_weight)
    
    if abs(total_weight - 1.0) > 0.01:
        logger.warning(f"Weights do not sum to 1.0: total={total_weight}")

def calculate_risk_score(self, factors: Dict[str, float]) -> float:
    """
    Calcula score de risco (Low Volatility).
    
    Menor risco é melhor, então invertemos os sinais:
    - volatility_90d: INVERTIDO (menor é melhor)
    - volatility_1y: INVERTIDO (menor é melhor)
    - max_drawdown_1y: INVERTIDO (menor drawdown é melhor)
    
    Args:
        factors: Dicionário com fatores normalizados
        
    Returns:
        Score de risco (média dos fatores invertidos)
    """
    import math
    
    risk_factors = []
    
    # Volatilidade 90 dias (invertido)
    vol_90d = factors.get('volatility_90d')
    if vol_90d is not None and not (isinstance(vol_90d, float) and math.isnan(vol_90d)):
        risk_factors.append(-vol_90d)  # Invertido
    
    # Volatilidade 1 ano (invertido)
    vol_1y = factors.get('volatility_1y')
    if vol_1y is not None and not (isinstance(vol_1y, float) and math.isnan(vol_1y)):
        risk_factors.append(-vol_1y)  # Invertido
    
    # Max Drawdown 1 ano (invertido)
    max_dd_1y = factors.get('max_drawdown_1y')
    if max_dd_1y is not None and not (isinstance(max_dd_1y, float) and math.isnan(max_dd_1y)):
        risk_factors.append(-max_dd_1y)  # Invertido (drawdown é negativo)
    
    # Se nenhum fator disponível, retorna NaN
    if not risk_factors:
        import numpy as np
        return np.nan
    
    # Calcular média
    risk_score = sum(risk_factors) / len(risk_factors)
    
    return risk_score

def calculate_final_score(
    self,
    momentum_score: float,
    quality_score: float,
    value_score: float,
    risk_score: float = 0.0
) -> float:
    """
    Calcula score final como média ponderada.
    
    final_score = 0.4 * momentum + 0.3 * value + 0.2 * quality + 0.1 * risk
    """
    import numpy as np
    
    scores_and_weights = []
    
    if not np.isnan(momentum_score):
        scores_and_weights.append((momentum_score, self.momentum_weight))
    
    if not np.isnan(quality_score):
        scores_and_weights.append((quality_score, self.quality_weight))
    
    if not np.isnan(value_score):
        scores_and_weights.append((value_score, self.value_weight))
    
    if not np.isnan(risk_score):
        scores_and_weights.append((risk_score, self.risk_weight))
    
    if not scores_and_weights:
        return 0.0
    
    total_weight = sum(weight for _, weight in scores_and_weights)
    final_score = sum(score * (weight / total_weight) 
                     for score, weight in scores_and_weights)
    
    return final_score
```

---

### FASE 3: Melhorar Relatórios e Visualizações

#### 3.1 Adicionar Tabela de Breakdown de Fatores

**Criar**: `frontend/components/factor_breakdown.py`
```python
import streamlit as st
import pandas as pd

def display_factor_breakdown(run_id, db):
    """
    Exibe breakdown de fatores para cada ativo selecionado.
    """
    st.subheader("📊 Breakdown de Fatores por Ativo")
    
    # Buscar posições do último rebalance
    from app.backtest.repository import BacktestRepository
    repo = BacktestRepository(db)
    
    rebalance_dates = repo.get_rebalance_dates(run_id)
    if not rebalance_dates:
        st.warning("Sem dados de rebalanceamento")
        return
    
    last_date = rebalance_dates[-1]
    positions = repo.get_positions(run_id, last_date)
    
    # Montar DataFrame
    data = []
    for pos in positions:
        data.append({
            'Ticker': pos.ticker,
            'Peso': f"{pos.weight:.1%}",
            'Score Final': f"{pos.score_at_selection:.3f}" if pos.score_at_selection else "N/A",
            # TODO: Buscar scores individuais de momentum, value, quality, risk
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
```

#### 3.2 Adicionar Gráfico de Drawdown

**Modificar**: `frontend/pages/4_🔬_Research_Backtest.py`
```python
def display_drawdown_chart(run_id):
    """Exibe gráfico de drawdown ao longo do tempo."""
    
    db = SessionLocal()
    try:
        service = BacktestService(db)
        equity_curve = service.get_equity_curve(run_id)
        
        if not equity_curve:
            st.warning("Sem dados de equity curve")
            return
        
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
        ))
        
        st.plotly_chart(fig, use_container_width=True)
        
    finally:
        db.close()
```

#### 3.3 Adicionar Tabela de Retornos Anuais

```python
def display_annual_returns(run_id):
    """Exibe tabela de retornos anuais."""
    
    db = SessionLocal()
    try:
        service = BacktestService(db)
        equity_curve = service.get_equity_curve(run_id)
        
        df = pd.DataFrame(equity_curve)
        df['year'] = pd.to_datetime(df['date']).dt.year
        
        # Calcular retorno por ano
        annual_returns = []
        for year in df['year'].unique():
            year_data = df[df['year'] == year]
            if len(year_data) > 1:
                start_nav = year_data['nav'].iloc[0]
                end_nav = year_data['nav'].iloc[-1]
                annual_return = (end_nav - start_nav) / start_nav
                
                annual_returns.append({
                    'Ano': year,
                    'Retorno': f"{annual_return:.2%}"
                })
        
        if annual_returns:
            st.subheader("📅 Retornos Anuais")
            df_annual = pd.DataFrame(annual_returns)
            st.dataframe(df_annual, use_container_width=True, hide_index=True)
        
    finally:
        db.close()
```

---

### FASE 4: Validações e Logging

#### 4.1 Adicionar Validação de Dados

**Criar**: `app/backtest/validator.py`
```python
class BacktestDataValidator:
    """Valida dados antes de executar backtest."""
    
    @staticmethod
    def validate_universe(
        db: Session,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Valida disponibilidade e qualidade dos dados.
        
        Returns:
            Dict com status e warnings
        """
        warnings = []
        
        # 1. Verificar scores disponíveis
        score_count = db.query(ScoreDaily).filter(
            ScoreDaily.date >= start_date,
            ScoreDaily.date <= end_date
        ).count()
        
        if score_count == 0:
            warnings.append("CRITICAL: Sem scores disponíveis")
        
        # 2. Verificar tickers com dados incompletos
        tickers_with_missing = db.query(ScoreDaily.ticker).filter(
            ScoreDaily.date >= start_date,
            ScoreDaily.date <= end_date,
            ScoreDaily.final_score.is_(None)
        ).distinct().all()
        
        if tickers_with_missing:
            warnings.append(
                f"WARNING: {len(tickers_with_missing)} tickers com scores faltantes"
            )
        
        # 3. Verificar benchmark
        benchmark_count = db.query(BenchmarkPrice).filter(
            BenchmarkPrice.date >= start_date,
            BenchmarkPrice.date <= end_date
        ).count()
        
        if benchmark_count == 0:
            warnings.append("WARNING: Benchmark não disponível")
        
        return {
            'valid': len([w for w in warnings if 'CRITICAL' in w]) == 0,
            'warnings': warnings,
            'score_count': score_count,
            'benchmark_count': benchmark_count
        }
```

---

## Cronograma de Implementação

### Sprint 1 (1-2 dias) - Completar Fatores
- ✅ Adicionar `minimum_market_cap` (1 bilhão)
- ✅ Adicionar `return_3m`
- ✅ Adicionar `roic`
- ✅ Adicionar `volatility_1y` e `max_drawdown_1y`
- ✅ Testar cálculos

### Sprint 2 (1 dia) - Ajustar Modelo
- ✅ Atualizar pesos (0.4, 0.3, 0.2, 0.1)
- ✅ Implementar `calculate_risk_score()`
- ✅ Atualizar `calculate_final_score()`
- ✅ Testar scoring

### Sprint 3 (1-2 dias) - Melhorar Visualizações
- ✅ Adicionar gráfico de drawdown
- ✅ Adicionar tabela de retornos anuais
- ✅ Adicionar breakdown de fatores
- ✅ Melhorar dashboard

### Sprint 4 (1 dia) - Validações
- ✅ Implementar `BacktestDataValidator`
- ✅ Adicionar logs estruturados
- ✅ Documentar pipeline

---

## Estrutura de Código Atualizada

```
app/
├── ingestion/              # Data Ingestion
│   ├── yahoo_client.py
│   ├── fmp_client.py
│   └── data_validation.py
│
├── factor_engine/          # Feature Engineering
│   ├── momentum_factors.py
│   ├── fundamental_factors.py
│   ├── financial_factors.py
│   └── normalizer.py
│
├── scoring/                # Factor Model
│   ├── scoring_engine.py
│   └── ranker.py
│
├── filters/                # Universe Selection
│   └── eligibility_filter.py
│
├── backtest/               # Backtest Engine
│   ├── backtest_engine.py
│   ├── portfolio.py
│   ├── metrics.py
│   ├── benchmark.py
│   ├── validator.py        # NOVO
│   └── repository.py
│
└── report/                 # Reporting
    └── report_generator.py

frontend/
├── pages/
│   └── 4_🔬_Research_Backtest.py
└── components/             # NOVO
    └── factor_breakdown.py
```

---

## Métricas de Sucesso

### Objetivos:
- ✅ Sharpe Ratio > 1.0 no longo prazo
- ✅ Alpha > 0% vs IBOVESPA
- ✅ Information Ratio > 0.5
- ✅ Max Drawdown < 20%
- ✅ Turnover < 50% mensal

### Validação:
- Backtest de 3+ anos
- Walk Forward Validation
- Out-of-sample testing

---

## Referências

- Fama-French: "Common risk factors" (1993)
- Jegadeesh & Titman: "Momentum" (1993)
- Ang et al.: "Low Volatility Anomaly" (2006)
- Asness et al.: "Quality Minus Junk" (2014)
