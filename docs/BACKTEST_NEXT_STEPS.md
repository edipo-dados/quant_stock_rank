# Próximos Passos - Melhorias do Backtest

## ✅ Concluído

1. **Scores nas posições** - Commit 66bbd98
   - BacktestEngine retorna portfolio_scores
   - Scores salvos em backtest_positions
   - Interface exibe scores corretamente

2. **Planejamento completo** - Este commit
   - Documento detalhado em `docs/BACKTEST_IMPROVEMENTS_PLAN.md`
   - Estrutura de benchmark criada
   - Script de ingestão de benchmark

## 🚀 Próximas Ações (em ordem de prioridade)

### 1. Criar tabela de benchmark no banco
```bash
# Adicionar migração para criar tabela benchmark_prices
# A tabela já está definida em app/backtest/benchmark.py
```

### 2. Ingerir dados do IBOVESPA
```bash
# Rodar script de ingestão
docker exec quant-ranker-backend python scripts/ingest_benchmark.py --start-date 2021-01-01 --end-date 2024-12-31
```

### 3. Integrar benchmark no BacktestEngine
- Modificar `app/backtest/backtest_engine.py`
- Adicionar cálculo de benchmark_return para cada período
- Salvar benchmark_nav em backtest_nav

### 4. Implementar custos de transação
- Adicionar método `calculate_transaction_costs()` no BacktestEngine
- Subtrair custos do retorno do portfólio
- Salvar custos totais em backtest_metrics

### 5. Adicionar métricas vs benchmark
- Modificar `app/backtest/metrics.py`
- Implementar cálculo de Alpha, Beta, Information Ratio
- Salvar em backtest_metrics

### 6. Atualizar interface
- Modificar `frontend/pages/4_🔬_Research_Backtest.py`
- Adicionar linha de benchmark no gráfico de equity curve
- Exibir métricas vs benchmark
- Exibir custos de transação totais

### 7. Implementar validação pré-backtest
- Criar `app/backtest/validator.py`
- Validar disponibilidade de dados antes de rodar backtest
- Exibir warnings na interface

## 📋 Checklist de Implementação

### Sprint 1 (Benchmark e Custos)
- [ ] Criar migração para tabela benchmark_prices
- [ ] Rodar migração no banco
- [ ] Ingerir dados históricos do IBOVESPA (2021-2024)
- [ ] Integrar benchmark no BacktestEngine
- [ ] Implementar custos de transação
- [ ] Calcular Alpha, Beta, Information Ratio
- [ ] Atualizar interface com benchmark
- [ ] Testar backtest completo com benchmark

### Sprint 2 (Validação e Robustez)
- [ ] Criar BacktestValidator
- [ ] Integrar validação na interface
- [ ] Melhorar tratamento de erros
- [ ] Adicionar logs detalhados
- [ ] Testar com dados incompletos

### Sprint 3 (Fatores Avançados)
- [ ] Adicionar EV/EBIT
- [ ] Adicionar FCF Yield
- [ ] Adicionar ROIC
- [ ] Atualizar scoring com novos fatores
- [ ] Recalcular scores históricos

### Sprint 4 (Métricas e UX)
- [ ] Implementar Sortino Ratio
- [ ] Implementar Calmar Ratio
- [ ] Melhorar visualizações
- [ ] Adicionar testes de robustez
- [ ] Documentação final

## 🔧 Comandos Úteis

### Ingerir benchmark
```bash
# Período específico
docker exec quant-ranker-backend python scripts/ingest_benchmark.py --start-date 2021-01-01 --end-date 2024-12-31

# Últimos 365 dias
docker exec quant-ranker-backend python scripts/ingest_benchmark.py --days 365
```

### Verificar dados do benchmark
```bash
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.backtest.benchmark import BenchmarkManager
from datetime import date

db = SessionLocal()
bm = BenchmarkManager(db)
avail = bm.get_data_availability(date(2021, 1, 1), date(2024, 12, 31))
print(f'Cobertura: {avail[\"coverage\"]:.1%}')
print(f'Registros: {avail[\"records_found\"]}')
db.close()
"
```

### Rodar backtest com benchmark
```bash
# Após implementar integração
# Usar interface Streamlit ou script
docker exec quant-ranker-backend python scripts/run_backtest_pipeline.py --preset default
```

## 📚 Referências

- **Plano completo**: `docs/BACKTEST_IMPROVEMENTS_PLAN.md`
- **Código de benchmark**: `app/backtest/benchmark.py`
- **Script de ingestão**: `scripts/ingest_benchmark.py`
- **Documentação de backtest**: `BACKTEST_QUICKSTART.md`

## 💡 Notas Importantes

1. **Migração do banco**: Antes de rodar o script de ingestão, criar a tabela benchmark_prices
2. **Dados históricos**: O IBOVESPA (^BVSP) está disponível no Yahoo Finance desde 1993
3. **Sincronização**: Benchmark deve ser ingerido junto com pipeline diário
4. **Performance**: Cachear cálculos de benchmark para evitar queries repetidas
5. **Testes**: Sempre testar com período pequeno primeiro (ex: 1 ano)
