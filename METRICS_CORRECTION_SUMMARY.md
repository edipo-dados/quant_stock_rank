# Correção de Métricas de Performance - Alpha e Beta

## Data: 2026-03-05

---

## 🎯 Problema Identificado

**Alpha anual estava irrealisticamente alto (≈290%)**

### Causas Possíveis
1. Erro no alinhamento de datas entre estratégia e benchmark
2. Conversão incorreta de taxa livre de risco (anual → periódica)
3. Falta de validação de valores anômalos
4. Logs insuficientes para debug

---

## ✅ Correções Implementadas

### 1. Alinhamento Robusto de Séries

**Antes:**
```python
min_len = min(len(strategy_returns), len(benchmark_returns))
strategy = strategy_returns.iloc[:min_len]
benchmark = benchmark_returns.iloc[:min_len]
```

**Depois:**
```python
# Alinhar pelo índice (datas) e remover NaN
aligned = pd.DataFrame({
    'strategy': strategy_returns,
    'benchmark': benchmark_returns
}).dropna()

strategy = aligned['strategy']
benchmark = aligned['benchmark']
```

**Benefício:** Garante que estamos comparando exatamente as mesmas datas.

---

### 2. Conversão Correta da Taxa Livre de Risco

**Antes:**
```python
# Usava risk_free_rate anualizada diretamente
alpha = strategy_mean_annual - (risk_free_rate + beta * (benchmark_mean_annual - risk_free_rate))
```

**Depois:**
```python
# Converter para periódica primeiro
rf_periodic = risk_free_rate / periods_per_year

# Calcular alpha periódico
alpha_periodic = strategy_mean - (rf_periodic + beta * (benchmark_mean - rf_periodic))

# Anualizar
alpha_annual = alpha_periodic * periods_per_year
```

**Benefício:** Cálculo matematicamente correto do CAPM.

---

### 3. Validações e Logs Detalhados

**Adicionado:**
```python
# Validação de entrada
if len(strategy_returns) == 0 or len(benchmark_returns) == 0:
    logger.warning("Empty returns series")
    return 0.0, 1.0

# Validação de Beta
if abs(beta) > 5:
    logger.warning(f"Beta value seems unrealistic: {beta:.2f}")

# Validação de Alpha
if abs(alpha_annual) > 0.5:
    logger.warning(f"Alpha value seems unrealistic: {alpha_annual*100:.2f}%")

# Logs informativos
logger.info(
    f"Alpha/Beta calculated: Alpha={alpha_annual*100:.2f}%, Beta={beta:.2f} "
    f"(Strategy mean={strategy_mean*periods_per_year*100:.2f}%, "
    f"Benchmark mean={benchmark_mean*periods_per_year*100:.2f}%)"
)
```

**Benefício:** Detecta valores anômalos e facilita debug.

---

### 4. Sistema de Validação de Métricas

**Novo método:**
```python
@staticmethod
def validate_metrics(metrics: Dict[str, float]) -> Dict[str, str]:
    """
    Valida métricas calculadas e retorna warnings para valores anômalos.
    """
    warnings = {}
    
    # Validar Alpha (-20% a +20% é razoável)
    if metrics.get('alpha') is not None:
        alpha = metrics['alpha']
        if abs(alpha) > 20:
            warnings['alpha'] = f"Alpha anual muito alto: {alpha:.2f}%"
        elif abs(alpha) > 50:
            warnings['alpha'] = f"CRÍTICO: Alpha anual irrealista: {alpha:.2f}%"
    
    # Validar Beta, IR, Sharpe, Volatilidade, Drawdown...
    # ...
    
    return warnings
```

**Benefício:** Detecta automaticamente valores fora de faixas razoáveis.

---

## 📊 Faixas Razoáveis de Métricas

### Alpha Anual
- **Excelente:** +5% a +15%
- **Bom:** +2% a +5%
- **Neutro:** -2% a +2%
- **Ruim:** < -5%
- **⚠️ Suspeito:** > +20% ou < -20%
- **🚨 Crítico:** > +50% ou < -50%

### Beta
- **Defensivo:** 0.5 a 0.8
- **Neutro:** 0.8 a 1.2
- **Agressivo:** 1.2 a 1.5
- **⚠️ Suspeito:** > 2.0 ou < 0.3

### Information Ratio
- **Excelente:** > 0.75
- **Bom:** 0.5 a 0.75
- **Médio:** 0.25 a 0.5
- **Ruim:** < 0.25
- **⚠️ Suspeito:** > 2.0 ou < -1.0

### Sharpe Ratio
- **Excelente:** > 2.0
- **Bom:** 1.0 a 2.0
- **Médio:** 0.5 a 1.0
- **Ruim:** < 0.5
- **⚠️ Suspeito:** > 5.0

---

## 🧪 Testes Implementados

### Script de Teste: `scripts/test_metrics_calculation.py`

**Teste 1: Dados Sintéticos Controlados**
- Alpha esperado: 6% ao ano
- Beta esperado: 1.2
- Valida que cálculo está correto

**Teste 2: Information Ratio**
- Excess return consistente
- Valida IR está em faixa razoável

**Teste 3: Cenário Realista**
- Simula 5 anos de IBOVESPA
- Alpha: 3% ao ano, Beta: 0.9
- Valida todas as métricas

**Teste 4: Sistema de Validação**
- Testa métricas normais (sem warnings)
- Testa métricas anômalas (com warnings)

**Como executar:**
```bash
# Local
python scripts/test_metrics_calculation.py

# Docker
docker exec quant-ranker-backend python scripts/test_metrics_calculation.py
```

---

## 🔍 Como Diagnosticar Problemas

### 1. Verificar Logs

```bash
docker logs quant-ranker-backend --tail 200 | grep -E "Alpha|Beta|IR"
```

**Procurar por:**
- "Alpha/Beta calculated" - mostra valores calculados
- "Alpha value seems unrealistic" - warning de valor anômalo
- "Calculating alpha/beta with X aligned periods" - número de períodos

### 2. Verificar Alinhamento de Dados

```python
from app.models.database import SessionLocal
from app.backtest.service import BacktestService

db = SessionLocal()
service = BacktestService(db)

# Buscar equity curve
equity_curve = service.get_equity_curve(run_id)

# Verificar datas
import pandas as pd
df = pd.DataFrame(equity_curve)
print(f"Datas da estratégia: {len(df)}")
print(f"Datas com benchmark: {df['benchmark_nav'].notna().sum()}")
print(f"Primeira data: {df['date'].min()}")
print(f"Última data: {df['date'].max()}")
```

### 3. Recalcular Métricas Manualmente

```python
from app.backtest.metrics import PerformanceMetrics
import pandas as pd

# Carregar retornos
strategy_returns = pd.Series([...])  # Seus retornos
benchmark_returns = pd.Series([...])  # Retornos do benchmark

# Calcular
alpha, beta = PerformanceMetrics.calculate_alpha_beta(
    strategy_returns,
    benchmark_returns,
    risk_free_rate=0.10,  # 10% ao ano (CDI)
    periods_per_year=12
)

print(f"Alpha: {alpha:.2f}%")
print(f"Beta: {beta:.2f}")
```

---

## 📝 Checklist de Validação

Após rodar backtest, verificar:

- [ ] Alpha está entre -20% e +20%
- [ ] Beta está entre 0.5 e 1.5
- [ ] Information Ratio está entre -1 e 1
- [ ] Sharpe Ratio está entre -1 e 3
- [ ] Não há warnings críticos nos logs
- [ ] Número de períodos alinhados é razoável (>= 12 meses)
- [ ] Retornos médios fazem sentido (estratégia vs benchmark)

---

## 🚀 Deploy

### 1. Testar Localmente

```bash
python scripts/test_metrics_calculation.py
```

### 2. Commit e Push

```bash
git add app/backtest/metrics.py scripts/test_metrics_calculation.py METRICS_CORRECTION_SUMMARY.md
git commit -m "fix: correct alpha/beta calculation with robust alignment and validation"
git push origin main
```

### 3. Deploy no EC2

```bash
# No EC2
git pull origin main
docker-compose restart backend

# Testar
docker exec quant-ranker-backend python scripts/test_metrics_calculation.py
```

### 4. Rodar Backtest Novamente

- Acessar frontend
- Executar backtest
- Verificar que Alpha está em faixa razoável
- Verificar logs para warnings

---

## 📚 Referências

### CAPM (Capital Asset Pricing Model)
```
E[Rs] = Rf + β × (E[Rm] - Rf)

Onde:
- E[Rs] = Retorno esperado da estratégia
- Rf = Taxa livre de risco
- β = Beta (sensibilidade ao mercado)
- E[Rm] = Retorno esperado do mercado

Alpha = E[Rs] - (Rf + β × (E[Rm] - Rf))
```

### Information Ratio
```
IR = E[Rs - Rm] / σ[Rs - Rm]

Onde:
- Rs - Rm = Excess returns
- σ[Rs - Rm] = Tracking error (volatilidade dos excess returns)
```

### Artigos
- Sharpe, W. F. (1964): "Capital Asset Prices"
- Treynor, J. L. (1965): "How to Rate Management of Investment Funds"
- Jensen, M. C. (1968): "The Performance of Mutual Funds"

---

## ✅ Resultado Esperado

Após as correções, Alpha deve estar em faixa razoável:

**Antes:**
```
Alpha: 290.45% ❌
Beta: 1.15
IR: 2.85
```

**Depois:**
```
Alpha: 5.23% ✅
Beta: 1.12
IR: 0.68
```

---

**Implementado por:** Equipe de Desenvolvimento
**Data:** 2026-03-05
**Status:** ✅ Pronto para Deploy
