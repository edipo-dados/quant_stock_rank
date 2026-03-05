# Migração: Adicionar Benchmark ao Sistema

## Objetivo

Adicionar suporte a benchmark (IBOVESPA) para comparação de performance nos backtests.

## O que a migração faz

1. ✅ Cria a tabela `benchmark_prices` no banco de dados
2. ✅ Ingere dados históricos do IBOVESPA (^BVSP) do Yahoo Finance
3. ✅ Valida a ingestão e cobertura de dados

## Como executar

### Opção 1: Migração completa (recomendado)

```bash
# No EC2 com Docker
docker exec quant-ranker-backend python scripts/migrate_add_benchmark.py
```

Isso vai:
- Criar a tabela `benchmark_prices`
- Ingerir dados desde 2021-01-01 até hoje
- Validar a cobertura de dados

### Opção 2: Período customizado

```bash
# Período específico
docker exec quant-ranker-backend python scripts/migrate_add_benchmark.py \
  --start-date 2020-01-01 \
  --end-date 2024-12-31
```

### Opção 3: Apenas criar tabela (sem ingerir dados)

```bash
docker exec quant-ranker-backend python scripts/migrate_add_benchmark.py --skip-ingestion
```

## Saída esperada

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    MIGRAÇÃO: ADICIONAR BENCHMARK                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

PASSO 1: Verificando se tabela já existe...
✗ Tabela benchmark_prices não existe

PASSO 2: Criando tabela...
================================================================================
CRIANDO TABELA BENCHMARK_PRICES
================================================================================
✓ Tabela benchmark_prices criada com sucesso

PASSO 3: Ingerindo dados históricos...
================================================================================
INGESTÃO DE DADOS DO BENCHMARK
================================================================================
Símbolo: ^BVSP
Período: 2021-01-01 a 2024-12-31

Buscando dados do Yahoo Finance para ^BVSP...
✓ 987 registros obtidos do Yahoo Finance
Salvando no banco de dados...
✓ 987 novos registros inseridos
✓ 0 registros atualizados

PASSO 4: Validando migração...
================================================================================
VALIDAÇÃO DA MIGRAÇÃO
================================================================================
Símbolo: ^BVSP
Período: 2021-01-01 a 2024-12-31
Registros encontrados: 987
Dias esperados: 1461
Cobertura: 67.6%

✓ MIGRAÇÃO BEM-SUCEDIDA
✓ Dados suficientes para backtesting
================================================================================

╔══════════════════════════════════════════════════════════════════════════════╗
║                         MIGRAÇÃO CONCLUÍDA                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Estrutura da tabela criada

```sql
CREATE TABLE benchmark_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    close FLOAT NOT NULL,
    daily_return FLOAT,
    CONSTRAINT uix_benchmark_symbol_date UNIQUE (symbol, date)
);

CREATE INDEX idx_benchmark_date ON benchmark_prices(date);
CREATE INDEX idx_benchmark_symbol ON benchmark_prices(symbol);
```

## Verificar dados após migração

```bash
# Verificar número de registros
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
result = db.execute(text('SELECT COUNT(*) FROM benchmark_prices')).scalar()
print(f'Registros na tabela: {result}')
db.close()
"

# Verificar cobertura de dados
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.backtest.benchmark import BenchmarkManager
from datetime import date

db = SessionLocal()
bm = BenchmarkManager(db)
avail = bm.get_data_availability(date(2021, 1, 1), date(2024, 12, 31))
print(f'Cobertura: {avail[\"coverage\"]:.1%}')
print(f'Registros: {avail[\"records_found\"]}')
print(f'Suficiente: {\"Sim\" if avail[\"sufficient\"] else \"Não\"}')
db.close()
"
```

## Atualização diária do benchmark

Após a migração inicial, adicionar ao cron para atualizar diariamente:

```bash
# Adicionar ao crontab
0 19 * * * cd /home/ubuntu/quant_stock_rank && docker exec quant-ranker-backend python scripts/ingest_benchmark.py --days 7 >> /home/ubuntu/logs/benchmark_update.log 2>&1
```

Ou rodar manualmente:

```bash
# Atualizar últimos 7 dias
docker exec quant-ranker-backend python scripts/ingest_benchmark.py --days 7
```

## Troubleshooting

### Erro: "Tabela já existe"

Se a tabela já existe, o script vai pular a criação e apenas ingerir dados.

### Erro: "Nenhum dado encontrado para ^BVSP"

Possíveis causas:
1. Problema de conexão com Yahoo Finance
2. Símbolo incorreto
3. Período sem dados

Solução:
```bash
# Testar conexão manualmente
docker exec quant-ranker-backend python -c "
from app.ingestion.yahoo_client import YahooFinanceClient
from datetime import date

client = YahooFinanceClient()
df = client.fetch_daily_prices('^BVSP', date(2024, 1, 1), date(2024, 12, 31))
print(f'Registros obtidos: {len(df)}')
print(df.head())
"
```

### Cobertura abaixo de 70%

Isso é normal porque:
- Mercado não opera em finais de semana
- Feriados
- Dias sem negociação

Cobertura de ~67-70% é esperada e suficiente para backtesting.

## Próximos passos

Após executar a migração:

1. ✅ Tabela criada e dados ingeridos
2. ⏳ Integrar benchmark no BacktestEngine
3. ⏳ Adicionar custos de transação
4. ⏳ Calcular Alpha, Beta, Information Ratio
5. ⏳ Atualizar interface para exibir benchmark

Ver `docs/BACKTEST_NEXT_STEPS.md` para detalhes.

## Rollback (se necessário)

Para reverter a migração:

```bash
docker exec quant-ranker-backend python -c "
from app.models.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text('DROP TABLE IF EXISTS benchmark_prices CASCADE'))
    conn.commit()
print('Tabela benchmark_prices removida')
"
```

## Arquivos relacionados

- `scripts/migrate_add_benchmark.py` - Script de migração
- `scripts/ingest_benchmark.py` - Script de atualização diária
- `app/backtest/benchmark.py` - Classe BenchmarkManager
- `docs/BACKTEST_IMPROVEMENTS_PLAN.md` - Plano completo de melhorias
- `docs/BACKTEST_NEXT_STEPS.md` - Próximas ações
