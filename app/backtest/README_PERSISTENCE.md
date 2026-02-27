# Estrutura Persistente de Backtesting

## Visão Geral

Sistema de persistência para armazenar e auditar execuções de backtest no PostgreSQL existente, sem criar novo banco e sem alterar tabelas de produção.

**Versão**: 2.7.0  
**Data**: 2026-02-26

## Arquitetura

### Separação de Concerns

```
┌─────────────────────────────────────────────────────────┐
│                   Backtest Engine                        │
│              (Lógica de Simulação)                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 Backtest Service                         │
│            (Orquestração de Negócio)                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│               Backtest Repository                        │
│              (Operações de Banco)                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 Backtest Models                          │
│            (Definições SQLAlchemy)                       │
└─────────────────────────────────────────────────────────┘
```

## Estrutura de Tabelas

### 1. `backtest_runs`

Armazena metadados de cada execução.

```sql
CREATE TABLE backtest_runs (
    id VARCHAR(36) PRIMARY KEY,  -- UUID
    name VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    rebalance_frequency VARCHAR(20) NOT NULL DEFAULT 'monthly',
    top_n INTEGER NOT NULL,
    transaction_cost FLOAT NOT NULL DEFAULT 0.001,
    initial_capital FLOAT NOT NULL DEFAULT 100000.0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    notes TEXT
);

CREATE INDEX idx_backtest_runs_dates ON backtest_runs(start_date, end_date);
CREATE INDEX idx_backtest_runs_created ON backtest_runs(created_at);
```

### 2. `backtest_nav`

Armazena equity curve diária.

```sql
CREATE TABLE backtest_nav (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL REFERENCES backtest_runs(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    nav FLOAT NOT NULL,
    benchmark_nav FLOAT,
    daily_return FLOAT NOT NULL,
    benchmark_return FLOAT,
    UNIQUE(run_id, date)
);

CREATE INDEX idx_backtest_nav_run_date ON backtest_nav(run_id, date);
```

### 3. `backtest_positions`

Armazena carteira em cada rebalance.

```sql
CREATE TABLE backtest_positions (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL REFERENCES backtest_runs(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    weight FLOAT NOT NULL,
    score_at_selection FLOAT,
    UNIQUE(run_id, date, ticker)
);

CREATE INDEX idx_backtest_positions_run_date ON backtest_positions(run_id, date);
CREATE INDEX idx_backtest_positions_ticker ON backtest_positions(ticker);
```

### 4. `backtest_metrics`

Armazena métricas finais.

```sql
CREATE TABLE backtest_metrics (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL UNIQUE REFERENCES backtest_runs(id) ON DELETE CASCADE,
    total_return FLOAT NOT NULL,
    cagr FLOAT NOT NULL,
    volatility FLOAT NOT NULL,
    sharpe_ratio FLOAT NOT NULL,
    sortino_ratio FLOAT NOT NULL,
    max_drawdown FLOAT NOT NULL,
    turnover_avg FLOAT NOT NULL,
    alpha FLOAT,
    beta FLOAT,
    information_ratio FLOAT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_backtest_metrics_run ON backtest_metrics(run_id);
```

## Uso

### 1. Executar Migration

```bash
# Docker
docker exec quant-ranker-backend python scripts/migrate_add_backtest_tables.py

# Local
python scripts/migrate_add_backtest_tables.py
```

### 2. Testar Estrutura

```bash
# Docker
docker exec quant-ranker-backend python scripts/test_backtest_persistence.py

# Local
python scripts/test_backtest_persistence.py
```

### 3. Usar no Código

```python
from app.models.database import SessionLocal
from app.backtest.service import BacktestService
from datetime import date

# Inicializar
db = SessionLocal()
service = BacktestService(db)

# Criar backtest run
run = service.create_backtest_run(
    name="momentum_v1",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    rebalance_frequency="monthly",
    top_n=10,
    transaction_cost=0.001,
    initial_capital=100000.0,
    notes="Teste de estratégia momentum"
)

# Salvar resultados
service.save_backtest_results(
    run_id=run.id,
    nav_records=[...],  # Lista de dicts com date, nav, daily_return
    positions=[...],     # Lista de dicts com date, ticker, weight
    metrics={...}        # Dict com métricas finais
)

# Consultar resultados
summary = service.get_backtest_summary(run.id)
equity_curve = service.get_equity_curve(run.id)
portfolio = service.get_portfolio_composition(run.id, date(2024, 1, 1))

# Comparar versões
comparison = service.compare_runs(['run_id_1', 'run_id_2'])
```

## Garantias

### ✅ Isolamento

- Tabelas isoladas no namespace `backtest_*`
- NÃO altera tabelas de produção
- NÃO altera `scores_daily`
- Cascade delete automático

### ✅ Reproduzibilidade

- Cada execução tem ID único (UUID)
- Todos os parâmetros são armazenados
- Posições e NAV são auditáveis
- Timestamps de criação

### ✅ Escalabilidade

- Múltiplos backtests simultâneos
- Índices otimizados para consultas
- Batch inserts para performance
- Relacionamentos via foreign keys

### ✅ Auditabilidade

- Histórico completo de execuções
- Composição de portfólio por data
- Métricas comparáveis
- Notas e metadados

## Casos de Uso

### 1. Comparar Versões de Modelo

```python
# Rodar backtest com modelo v1
run_v1 = service.create_backtest_run(name="model_v1", ...)
# ... executar backtest ...
service.save_backtest_results(run_v1.id, ...)

# Rodar backtest com modelo v2
run_v2 = service.create_backtest_run(name="model_v2", ...)
# ... executar backtest ...
service.save_backtest_results(run_v2.id, ...)

# Comparar
comparison = service.compare_runs([run_v1.id, run_v2.id])
```

### 2. Armazenar Histórico de Experimentos

```python
# Experimento 1: Top 5 ativos
run1 = service.create_backtest_run(
    name="exp_top5",
    top_n=5,
    notes="Teste com 5 ativos"
)

# Experimento 2: Top 10 ativos
run2 = service.create_backtest_run(
    name="exp_top10",
    top_n=10,
    notes="Teste com 10 ativos"
)

# Listar todos os experimentos
runs = service.list_backtests(limit=50)
```

### 3. Auditar Composição de Portfólio

```python
# Ver portfólio em data específica
portfolio = service.get_portfolio_composition(
    run_id="abc-123",
    rebalance_date=date(2024, 6, 1)
)

# Ver todas as datas de rebalance
from app.backtest.repository import BacktestRepository
repo = BacktestRepository(db)
rebalance_dates = repo.get_rebalance_dates("abc-123")
```

### 4. Visualizar Equity Curve

```python
# Obter equity curve completa
equity_curve = service.get_equity_curve(run_id="abc-123")

# Plotar
import matplotlib.pyplot as plt
dates = [point['date'] for point in equity_curve]
navs = [point['nav'] for point in equity_curve]
plt.plot(dates, navs)
plt.show()
```

## Integração com Backtest Engine Existente

O `backtest_engine.py` existente pode ser integrado facilmente:

```python
from app.backtest.backtest_engine import BacktestEngine
from app.backtest.service import BacktestService
from app.models.database import SessionLocal

# Executar backtest
engine = BacktestEngine(...)
results = engine.run()

# Persistir resultados
db = SessionLocal()
service = BacktestService(db)

run = service.create_backtest_run(
    name="production_backtest",
    start_date=results['start_date'],
    end_date=results['end_date'],
    ...
)

service.save_backtest_results(
    run_id=run.id,
    nav_records=results['nav_records'],
    positions=results['positions'],
    metrics=results['metrics']
)
```

## Próximos Passos

### Fase 1: Validação ✅
- [x] Criar models SQLAlchemy
- [x] Criar repository layer
- [x] Criar service layer
- [x] Criar migration
- [x] Criar testes

### Fase 2: Integração
- [ ] Integrar com `backtest_engine.py`
- [ ] Adicionar persistência automática
- [ ] Criar API endpoints

### Fase 3: Visualização
- [ ] Dashboard de backtests
- [ ] Comparação visual de runs
- [ ] Gráficos de equity curve

### Fase 4: Avançado
- [ ] Suporte a ML models
- [ ] Walk-forward analysis
- [ ] Otimização de parâmetros

## Troubleshooting

### Tabelas não criadas

```bash
# Verificar se migration foi executada
docker exec quant-ranker-backend python -c "
from sqlalchemy import inspect
from app.models.database import engine
inspector = inspect(engine)
tables = inspector.get_table_names()
print('Tabelas backtest:', [t for t in tables if t.startswith('backtest_')])
"
```

### Erro de foreign key

Certifique-se de que o `run_id` existe antes de inserir NAV/positions/metrics.

### Performance lenta

Use batch inserts via `bulk_save_objects()` para grandes volumes de dados.

## Referências

- Código: `app/backtest/models.py`, `repository.py`, `service.py`
- Migration: `scripts/migrate_add_backtest_tables.py`
- Testes: `scripts/test_backtest_persistence.py`
- Documentação: Este arquivo
