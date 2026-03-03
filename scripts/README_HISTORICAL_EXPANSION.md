# Scripts de Expansão Histórica

Guia de uso dos scripts de expansão histórica de dados.

## 📁 Scripts Disponíveis

### 1. ingest_full_history.py

Script principal para ingestão completa de histórico.

**Uso básico:**
```bash
python scripts/ingest_full_history.py --start 2018-01-01
```

**Opções:**
- `--start`: Data inicial (YYYY-MM-DD), padrão: 2018-01-01
- `--mode`: full ou incremental, padrão: full
- `--max-workers`: Número de threads, padrão: 5
- `--skip-prices`: Pular ingestão de preços
- `--skip-fundamentals`: Pular ingestão de fundamentos
- `--skip-validation`: Pular validação
- `--tickers`: Lista de tickers específicos (separados por vírgula)

**Exemplos:**

```bash
# Ingestão completa (recomendado para primeira execução)
python scripts/ingest_full_history.py --start 2018-01-01

# Modo incremental (atualização)
python scripts/ingest_full_history.py --mode incremental

# Processar tickers específicos
python scripts/ingest_full_history.py --tickers "PETR4.SA,VALE3.SA,ITUB4.SA"

# Apenas preços
python scripts/ingest_full_history.py --skip-fundamentals

# Apenas fundamentos
python scripts/ingest_full_history.py --skip-prices

# Sem validação (mais rápido)
python scripts/ingest_full_history.py --skip-validation

# Mais threads (cuidado com rate limiting)
python scripts/ingest_full_history.py --max-workers 10
```

### 2. check_historical_coverage.py

Script para verificar cobertura histórica de dados.

**Uso:**
```bash
python scripts/check_historical_coverage.py
```

**Saída:**
- Total de tickers com preços
- Total de tickers com fundamentos
- Estatísticas de cobertura
- Top 10 e Bottom 10 tickers
- Tickers prontos para backtest

**Exemplo de saída:**
```
📊 PREÇOS:
  Total de tickers: 100
  Total de registros: 125,000
  Período: 2018-01-01 a 2024-02-26 (6.2 anos)

  Top 10 tickers (mais registros):
    PETR4.SA  : 1,523 registros, 6.2 anos (2018-01-01 a 2024-02-26)
    VALE3.SA  : 1,520 registros, 6.2 anos (2018-01-01 a 2024-02-26)
    ...

💼 FUNDAMENTOS:
  Total de tickers: 95
  Total de registros: 475

  Estatísticas de cobertura:
    Média de anos por ticker: 5.0
    Mediana de anos por ticker: 5.0

🔗 COBERTURA COMBINADA:
  Tickers com preços E fundamentos: 95
  ✅ Tickers prontos para backtest (≥3 anos ambos): 85
     Taxa: 89.5%
```

## 🐳 Uso no Docker

### Executar dentro do container

```bash
# Ingestão completa
docker exec quant-ranker-backend python scripts/ingest_full_history.py --start 2018-01-01

# Verificar cobertura
docker exec quant-ranker-backend python scripts/check_historical_coverage.py

# Ver relatório
docker exec quant-ranker-backend cat data_quality_report.json

# Ver logs
docker exec quant-ranker-backend tail -f ingest_full_history.log
```

### Copiar relatório para host

```bash
# Copiar relatório JSON
docker cp quant-ranker-backend:/app/data_quality_report.json .

# Copiar logs
docker cp quant-ranker-backend:/app/ingest_full_history.log .
```

## 📊 Relatório de Qualidade

O script `ingest_full_history.py` gera `data_quality_report.json` com:

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
  "valid_for_backtest": [
    "PETR4.SA",
    "VALE3.SA",
    ...
  ],
  "insufficient_for_backtest": [
    {
      "ticker": "TICKER.SA",
      "price_valid": false,
      "fundamental_valid": true,
      "price_issues": ["Insufficient history: 2.1 years < 3 years"],
      "fundamental_issues": []
    }
  ],
  "price_results": [...],
  "fundamental_results": [...]
}
```

## 🔍 Validações Realizadas

### Preços

- ✅ Mínimo 3 anos contínuos
- ✅ Buracos > 5 dias úteis
- ✅ Variação diária > 40% (outliers)
- ✅ Volume zero recorrente (>10%)
- ✅ Datas fora de ordem
- ✅ Preços negativos ou zero

### Fundamentos

- ✅ Mínimo 3 anos disponíveis
- ✅ Revenue negativa
- ✅ Equity negativa
- ✅ EBITDA volátil (>300%)
- ✅ Net income ausente (>50%)

## ⏱️ Tempo de Execução

Estimativas para 100 tickers:

| Etapa | Tempo |
|-------|-------|
| Preços | 20-30 min |
| Fundamentos | 30-40 min |
| Validação | 2-5 min |
| **Total** | **~1 hora** |

## 💾 Espaço em Disco

Estimativas para 100 tickers (5 anos):

| Tipo | Registros | Espaço |
|------|-----------|--------|
| Preços | ~1.2M | ~200 MB |
| Fundamentos | ~500 | ~5 MB |
| **Total** | | **~205 MB** |

## 🔄 Fluxo Recomendado

### Primeira Execução (Full)

```bash
# 1. Executar ingestão completa
docker exec quant-ranker-backend python scripts/ingest_full_history.py --start 2018-01-01

# 2. Verificar cobertura
docker exec quant-ranker-backend python scripts/check_historical_coverage.py

# 3. Ver relatório
docker exec quant-ranker-backend cat data_quality_report.json

# 4. Se taxa de validação < 80%, investigar
docker exec quant-ranker-backend python scripts/check_historical_coverage.py | grep "insufficient"
```

### Atualizações (Incremental)

```bash
# Executar semanalmente ou mensalmente
docker exec quant-ranker-backend python scripts/ingest_full_history.py --mode incremental
```

### Processar Novos Tickers

```bash
# Adicionar novos tickers ao banco primeiro (via pipeline diário)
# Depois executar expansão para eles
docker exec quant-ranker-backend python scripts/ingest_full_history.py \
  --tickers "NOVO1.SA,NOVO2.SA" \
  --start 2018-01-01
```

## 🐛 Troubleshooting

### Erro: "Too Many Requests (429)"

**Causa**: Rate limiting do Yahoo Finance

**Solução**:
```bash
# Reduzir workers
docker exec quant-ranker-backend python scripts/ingest_full_history.py \
  --start 2018-01-01 \
  --max-workers 3

# Ou aguardar alguns minutos e tentar novamente
```

### Taxa de Validação Baixa (<80%)

**Causa**: Muitos tickers com dados insuficientes

**Solução**:
```bash
# Verificar quais tickers têm problemas
docker exec quant-ranker-backend cat data_quality_report.json | grep "insufficient_for_backtest"

# Executar novamente em modo full
docker exec quant-ranker-backend python scripts/ingest_full_history.py \
  --start 2018-01-01 \
  --mode full
```

### Execução Interrompida

**Causa**: Timeout, erro de rede, etc.

**Solução**:
```bash
# Continuar de onde parou (modo incremental)
docker exec quant-ranker-backend python scripts/ingest_full_history.py --mode incremental
```

### Ticker Específico Falhando

**Causa**: Ticker deslistado, sem dados, etc.

**Solução**:
```bash
# Verificar logs
docker exec quant-ranker-backend grep "TICKER.SA" ingest_full_history.log

# Tentar processar individualmente
docker exec quant-ranker-backend python scripts/ingest_full_history.py \
  --tickers "TICKER.SA" \
  --start 2018-01-01
```

## 📝 Logs

### Localização

- **Container**: `/app/ingest_full_history.log`
- **Host**: Copiar com `docker cp`

### Ver logs em tempo real

```bash
docker exec quant-ranker-backend tail -f ingest_full_history.log
```

### Buscar erros

```bash
docker exec quant-ranker-backend grep "ERROR" ingest_full_history.log
docker exec quant-ranker-backend grep "✗" ingest_full_history.log
```

### Buscar ticker específico

```bash
docker exec quant-ranker-backend grep "PETR4.SA" ingest_full_history.log
```

## 🎯 Casos de Uso

### Caso 1: Setup Inicial

```bash
# Primeira vez configurando o sistema
docker exec quant-ranker-backend python scripts/ingest_full_history.py --start 2018-01-01
```

### Caso 2: Atualização Mensal

```bash
# Atualizar dados mensalmente
docker exec quant-ranker-backend python scripts/ingest_full_history.py --mode incremental
```

### Caso 3: Adicionar Novos Tickers

```bash
# Novos tickers foram adicionados ao universo
docker exec quant-ranker-backend python scripts/ingest_full_history.py \
  --tickers "NOVO1.SA,NOVO2.SA,NOVO3.SA" \
  --start 2018-01-01
```

### Caso 4: Reprocessar Ticker com Problema

```bash
# Um ticker específico teve problema
docker exec quant-ranker-backend python scripts/ingest_full_history.py \
  --tickers "TICKER.SA" \
  --start 2018-01-01 \
  --mode full
```

### Caso 5: Validação Rápida

```bash
# Apenas validar dados existentes
docker exec quant-ranker-backend python scripts/ingest_full_history.py \
  --skip-prices \
  --skip-fundamentals
```

## 📚 Referências

- [HISTORICAL_EXPANSION.md](../docs/HISTORICAL_EXPANSION.md) - Documentação completa
- [HISTORICAL_EXPANSION_QUICKSTART.md](../HISTORICAL_EXPANSION_QUICKSTART.md) - Guia rápido
- [HISTORICAL_EXPANSION_SUMMARY.md](../HISTORICAL_EXPANSION_SUMMARY.md) - Resumo executivo
