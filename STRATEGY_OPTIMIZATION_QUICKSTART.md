## Otimização da Estratégia Quantitativa - Guia Rápido

### Melhorias Implementadas

1. **Score-Weighted Portfolio** (em vez de equal weight)
   - Peso proporcional ao score
   - Limite máximo de 25% por ativo

2. **Market Regime Filter** (IBOV MA200)
   - 100% exposição quando IBOV > MA200
   - 50% exposição quando IBOV < MA200

3. **Temporal Smoothing**
   - Score suavizado = 0.7 × atual + 0.3 × anterior
   - Reduz ruído e turnover

4. **Pesos Multifator Otimizados**
   - Momentum: 0.5 (antes 0.4)
   - Value: 0.25 (antes 0.3)
   - Quality: 0.15 (antes 0.2)
   - Risk: 0.10 (mantido)

5. **Filtro de Liquidez Aumentado**
   - Volume mínimo: 5M (antes 100k)
   - Market cap mínimo: 1B (mantido)

### Executar Backtest Otimizado

```bash
# Local (Windows)
python scripts/run_optimized_backtest.py

# EC2 (Docker)
docker exec -it quant-ranker-backend python scripts/run_optimized_backtest.py
```

### Comparar Baseline vs Otimizada

```bash
# Local
python scripts/compare_strategies.py

# EC2
docker exec -it quant-ranker-backend python scripts/compare_strategies.py
```

### Resultados Esperados

| Métrica | Baseline | Otimizada | Melhoria |
|---------|----------|-----------|----------|
| Sharpe Ratio | 0.8 | 1.2+ | +50% |
| CAGR | 15% | 18%+ | +20% |
| Max Drawdown | -35% | -25% | +29% |

### Configurações

Arquivo: `app/config.py`

```python
# Pesos multifator
momentum_weight = 0.5
value_weight = 0.25
quality_weight = 0.15
risk_weight = 0.10

# Filtros
minimum_volume = 5_000_000
minimum_market_cap = 1_000_000_000

# Regime filter
regime_ma_period = 200
regime_bullish_exposure = 1.0
regime_bearish_exposure = 0.5
```

### Documentação Completa

Ver: `docs/STRATEGY_OPTIMIZATION_PLAN.md`

### Próximos Passos

1. Executar backtest otimizado
2. Comparar com baseline
3. Validar métricas
4. Implementar em produção (se resultados positivos)
