# Expansão Histórica de Dados

Documentação completa do módulo de expansão histórica de preços e fundamentos para todos os tickers da B3.

## 📋 Visão Geral

O módulo de expansão histórica busca dados completos (5 anos) para todos os tickers já cadastrados no sistema, garantindo base robusta para backtests e análises de longo prazo.

## 🎯 Objetivos

1. **Expandir preços históricos** desde 2018-01-01 até hoje
2. **Expandir fundamentos históricos** (últimos 5 anos disponíveis)
3. **Validar qualidade técnica** dos dados ingeridos
4. **Gerar relatório de qualidade** completo
5. **Garantir compatibilidade** com backtests de 5 anos

## 🏗️ Arquitetura

### Módulos Criados

```
app/ingestion/
├── historical_expansion.py    # Expansão de preços e fundamentos
└── data_validation.py         # Validação técnica de dados

scripts/
└── ingest_full_history.py     # Script principal de execução
```

### Fluxo de Execução

```
1. Carregar tickers da base
   ↓
2. Ingerir preços históricos (paralelo)
   ↓
3. Ingerir fundamentos históricos (paralelo)
   ↓
4. Validar qualidade dos dados
   ↓
5. Gerar relatório final
```

## 🚀 Uso

### Comando Básico

```bash
# Ingestão completa (preços + fundamentos + validação)
python scripts/ingest_full_history.py --start 2018-01-01

# Dentro do Docker
docker exec quant-ranker-backend python scripts/ingest_full_history.py --start 2018-01-01
```

### Opções Disponíveis

```bash
# Modo incremental (apenas novos dados)
python scripts/ingest_full_history.py --start 2018-01-01 --mode incremental

# Aumentar paralelização (cuidado com rate limiting)
python scripts/ingest_full_history.py --start 2018-01-01 --max-workers 10

# Processar apenas preços
python scripts/ingest_full_history.py --start 2018-01-01 --skip-fundamentals

# Processar apenas fundamentos
python scripts/ingest_full_history.py --start 2018-01-01 --skip-prices

# Pular validação (mais rápido)
python scripts/ingest_full_history.py --start 2018-01-01 --skip-validation

# Processar tickers específicos
python scripts/ingest_full_history.py --start 2018-01-01 --tickers "PETR4.SA,VALE3.SA,ITUB4.SA"
```

## 📊 Validações Técnicas

### Validação de Preços

O sistema verifica:

1. **Mínimo 3 anos contínuos** de dados
2. **Buracos > 5 dias úteis** (gaps de dados)
3. **Variação diária > 40%** (outliers)
4. **Volume zero recorrente** (>10% dos dias)
5. **Datas fora de ordem** ou duplicadas
6. **Preços negativos ou zero**

### Validação de Fundamentos

O sistema verifica:

1. **Mínimo 3 anos disponíveis**
2. **Revenue negativa** (problema estrutural)
3. **Equity negativa** (patrimônio líquido negativo)
4. **EBITDA extremamente volátil** (>300% variação)
5. **Net income ausente** (>50% dos períodos)

## 📈 Relatório de Qualidade

O script gera `data_quality_report.json` com:

```json
{
  "summary": {
    "total_tickers_processed": 100,
    "valid_prices": 85,
    "valid_fundamentals": 78,
    "valid_for_backtest": 75,
    "insufficient_for_backtest": 25,
    "price_validation_rate": 85.0,
    "fundamental_validation_rate": 78.0,
    "backtest_ready_rate": 75.0,
    "years_stats": {
      "min": 3.2,
      "max": 6.5,
      "avg": 5.1,
      "median": 5.3
    }
  },
  "valid_for_backtest": ["PETR4.SA", "VALE3.SA", ...],
  "insufficient_for_backtest": [
    {
      "ticker": "TICKER.SA",
      "price_valid": false,
      "fundamental_valid": true,
      "price_issues": ["Insufficient history: 2.1 years < 3 years"],
      "fundamental_issues": []
    }
  ]
}
```

## 🔧 Características Técnicas

### Expansão de Preços

- **Fonte**: Yahoo Finance (yfinance)
- **Período**: 2018-01-01 até hoje (configurável)
- **Campos**: date, open, high, low, close, volume, adj_close
- **Upsert**: Não duplica registros existentes
- **Validação**: Remove datas futuras e duplicadas
- **Índice**: Composto (ticker, date) para performance

### Expansão de Fundamentos

- **Fonte**: Yahoo Finance (yfinance)
- **Período**: Últimos 5 anos disponíveis
- **Demonstrações**:
  - Income Statement (revenue, net_income, ebitda)
  - Balance Sheet (total_assets, total_debt, shareholders_equity)
  - Cash Flow (operating_cashflow, free_cashflow)
- **Upsert**: Por (ticker, fiscal_year)
- **Metadados**: data_coleta, source="yahoo"

### Paralelização

- **Max workers**: 5 (padrão, configurável)
- **Delay entre requisições**: 1s (preços), 2s (fundamentos)
- **Retry automático**: Até 3 tentativas por ticker
- **Thread-safe**: Usa ThreadPoolExecutor

## ⚠️ Considerações Importantes

### Rate Limiting

O Yahoo Finance tem limites de requisições. Recomendações:

- Usar `--max-workers 5` (padrão)
- Não reduzir delays entre requisições
- Executar fora de horário de pico
- Monitorar logs para erros 429 (Too Many Requests)

### Tempo de Execução

Estimativas para 100 tickers:

- **Preços**: ~20-30 minutos (5 workers)
- **Fundamentos**: ~30-40 minutos (5 workers)
- **Validação**: ~2-5 minutos
- **Total**: ~1 hora

### Espaço em Disco

Estimativas para 100 tickers (5 anos):

- **Preços**: ~1.2 milhões de registros (~200 MB)
- **Fundamentos**: ~500 registros (~5 MB)
- **Total**: ~205 MB

## 🔄 Compatibilidade

### Pipeline Diário

O módulo de expansão histórica **NÃO interfere** com o pipeline diário:

- Usa mesmas tabelas (RawPriceDaily, RawFundamental)
- Upsert garante não duplicação
- Pipeline diário continua funcionando normalmente
- Pode rodar em paralelo (com cuidado no rate limiting)

### Backtest Engine

Após expansão, o backtest pode:

- Rodar períodos de 2018-2024 (6 anos)
- Calcular Quality 3Y sem NaN excessivo
- Calcular Momentum 12M corretamente
- Usar histórico adaptativo (1-3 anos)

### Docker

Totalmente compatível:

```bash
# Executar dentro do container
docker exec quant-ranker-backend python scripts/ingest_full_history.py --start 2018-01-01

# Ver logs
docker exec quant-ranker-backend tail -f ingest_full_history.log
```

## 📝 Logs

O script gera dois arquivos de log:

1. **ingest_full_history.log**: Log completo da execução
2. **Console output**: Resumo em tempo real

Exemplo de log:

```
2024-02-26 10:00:00 - INFO - Buscando preços históricos para PETR4.SA desde 2018-01-01
2024-02-26 10:00:05 - INFO - ✓ PETR4.SA: 1523 registros inseridos/atualizados
2024-02-26 10:00:10 - INFO - Buscando fundamentos históricos para PETR4.SA
2024-02-26 10:00:15 - INFO - ✓ PETR4.SA: 5 registros, 5 anos
```

## 🐛 Troubleshooting

### Erro: "No data available"

**Causa**: Ticker não existe ou foi deslistado

**Solução**: Normal, o script continua com próximo ticker

### Erro: "Too Many Requests (429)"

**Causa**: Rate limiting do Yahoo Finance

**Solução**:
- Reduzir `--max-workers` para 3
- Aguardar alguns minutos e tentar novamente
- Executar em horário de menor tráfego

### Erro: "Insufficient history"

**Causa**: Ticker tem menos de 3 anos de dados

**Solução**: Normal para tickers recentes, será marcado no relatório

### Validação baixa (<80%)

**Causa**: Muitos tickers com dados insuficientes

**Solução**:
- Verificar se tickers são válidos (não deslistados)
- Executar novamente em modo `full`
- Revisar lista de tickers no banco

## 📚 Exemplos de Uso

### Cenário 1: Primeira Execução (Full)

```bash
# Buscar 5 anos completos para todos os tickers
docker exec quant-ranker-backend python scripts/ingest_full_history.py --start 2018-01-01

# Verificar relatório
docker exec quant-ranker-backend cat data_quality_report.json
```

### Cenário 2: Atualização Incremental

```bash
# Buscar apenas dados novos desde última execução
docker exec quant-ranker-backend python scripts/ingest_full_history.py --mode incremental
```

### Cenário 3: Processar Tickers Específicos

```bash
# Processar apenas alguns tickers
docker exec quant-ranker-backend python scripts/ingest_full_history.py \
  --start 2018-01-01 \
  --tickers "PETR4.SA,VALE3.SA,ITUB4.SA,BBDC4.SA"
```

### Cenário 4: Apenas Validação

```bash
# Validar dados existentes sem ingerir novos
docker exec quant-ranker-backend python scripts/ingest_full_history.py \
  --skip-prices \
  --skip-fundamentals
```

## 🎯 Resultados Esperados

Após execução bem-sucedida:

✅ **5 anos de preços diários** por ticker (2018-2024)
✅ **3-5 anos de fundamentos** por ticker
✅ **Relatório de qualidade completo** (JSON)
✅ **Taxa de validação ≥ 80%** para tickers líquidos
✅ **Base pronta para backtests** de 5 anos
✅ **Compatibilidade total** com pipeline diário

## 🔗 Referências

- [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md) - Arquitetura do pipeline
- [CALCULOS_RANKING.md](CALCULOS_RANKING.md) - Cálculos de fatores
- [MISSING_VALUE_TREATMENT.md](MISSING_VALUE_TREATMENT.md) - Tratamento de missing values
- [ADAPTIVE_HISTORY_IMPLEMENTATION.md](../ADAPTIVE_HISTORY_IMPLEMENTATION.md) - Histórico adaptativo
