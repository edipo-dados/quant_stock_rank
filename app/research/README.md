## 📊 Quant Research – Backtest Engine

Aplicação Streamlit para rodar backtests utilizando a engine já implementada no projeto.

### Características

- ✅ Interface gráfica para configuração de parâmetros
- ✅ Integração com BacktestService e tabelas de persistência
- ✅ Visualização de equity curve interativa (Plotly)
- ✅ Métricas de performance em cards
- ✅ Histórico de execuções
- ✅ Isolada da aplicação principal (NÃO altera dados de produção)

### Instalação

Certifique-se de ter as dependências instaladas:

```bash
pip install streamlit plotly
```

### Uso

#### Local

```bash
# Opção 1: Via script
bash scripts/run_research_app.sh

# Opção 2: Direto
streamlit run app/research/streamlit_backtest_app.py

# Opção 3: Porta customizada
streamlit run app/research/streamlit_backtest_app.py --server.port 8502
```

#### Docker

```bash
# Executar dentro do container
docker exec -it quant-ranker-backend streamlit run app/research/streamlit_backtest_app.py --server.port 8502 --server.address 0.0.0.0

# Ou adicionar ao docker-compose.yml (opcional)
```

### Interface

#### Sidebar - Parâmetros

- **Período**: Data início e fim
- **Top N**: Número de ativos no portfólio (1-50)
- **Capital Inicial**: Valor em R$ (padrão: 100.000)
- **Custo de Transação**: Percentual (0-1%, padrão: 0.2%)
- **Usar Smoothing**: Checkbox para ativar suavização
- **Alpha Smoothing**: Peso do score atual (0.1-0.9, padrão: 0.7)
- **Nome do Teste**: Identificador opcional

#### Validações

- ✅ Data início < Data fim
- ✅ Período mínimo de 3 meses
- ✅ Verificação de dados disponíveis no período

#### Resultados

**Métricas em Cards**:
- Total Return
- CAGR
- Volatilidade
- Max Drawdown
- Sharpe Ratio
- Sortino Ratio
- Turnover Médio
- Alpha, Beta, Information Ratio (se disponíveis)

**Equity Curve**:
- Gráfico interativo Plotly
- Linha do portfólio (NAV)
- Linha do benchmark (se disponível)
- Hover com detalhes

**Posições**:
- Tabela do último rebalance
- Ticker, Peso, Score
- Ordenado por peso (desc)

**Histórico**:
- Lista de todas as execuções
- Run ID, Nome, Período, Top N, Sharpe, CAGR, Data
- Botão "Ver" para visualizar cada run

### Arquitetura

```
streamlit_backtest_app.py
├── validate_inputs()      # Validação de parâmetros
├── run_backtest_ui()      # Execução do backtest
├── display_metrics()      # Exibição de métricas
├── display_equity_curve() # Gráfico Plotly
├── display_positions()    # Tabela de posições
├── display_history()      # Histórico de runs
└── main()                 # Interface principal
```

### Integração

A aplicação utiliza:

- `BacktestService`: Orquestração de backtest
- `BacktestEngine`: Motor de simulação
- `BacktestRepository`: Operações de banco
- Tabelas: `backtest_runs`, `backtest_nav`, `backtest_positions`, `backtest_metrics`

**NÃO modifica**:
- `scores_daily`
- `features_monthly`
- `features_daily`
- Qualquer tabela de produção

### Fluxo de Execução

1. **Usuário configura parâmetros** na sidebar
2. **Clica em "Rodar Backtest"**
3. **Sistema valida inputs**
4. **Cria registro em `backtest_runs`**
5. **Executa BacktestEngine**
6. **Persiste resultados** (NAV, posições, métricas)
7. **Exibe resultados** na interface
8. **Adiciona ao histórico**

### Casos de Uso

#### 1. Testar Diferentes Períodos

```
Período 1: 2023-01-01 a 2023-12-31
Período 2: 2024-01-01 a 2024-12-31
Comparar: Sharpe, CAGR, Max Drawdown
```

#### 2. Avaliar Impacto do Smoothing

```
Run 1: Smoothing OFF
Run 2: Smoothing ON (alpha=0.7)
Run 3: Smoothing ON (alpha=0.9)
Comparar: Turnover, Sharpe
```

#### 3. Otimizar Top N

```
Run 1: Top 5
Run 2: Top 10
Run 3: Top 20
Comparar: Diversificação vs Performance
```

#### 4. Medir Robustez Temporal

```
Run 1: 2022-01-01 a 2022-12-31
Run 2: 2023-01-01 a 2023-12-31
Run 3: 2024-01-01 a 2024-12-31
Verificar: Consistência de métricas
```

### Segurança

- ✅ Validação de inputs
- ✅ Try/except com logging
- ✅ Rollback automático em caso de erro
- ✅ Isolamento de dados de produção
- ✅ Cada execução gera novo run_id único

### Evolução Futura

A estrutura permite:

- [ ] Comparar múltiplos runs lado a lado
- [ ] Exportar resultados em CSV
- [ ] Grid search de parâmetros
- [ ] Walk-forward analysis
- [ ] Integração com ML
- [ ] Otimização de pesos
- [ ] Análise de atribuição

### Troubleshooting

#### Erro: "Sem dados de scores disponíveis"

```bash
# Verificar se há scores no período
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date

db = SessionLocal()
count = db.query(ScoreDaily).filter(
    ScoreDaily.date >= date(2024, 1, 1),
    ScoreDaily.date <= date(2024, 12, 31)
).count()
print(f'Scores disponíveis: {count}')
db.close()
"

# Se zero, rodar pipeline
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50
```

#### Erro: "Tabelas de backtest não existem"

```bash
# Executar migration
docker exec quant-ranker-backend python scripts/migrate_add_backtest_tables.py
```

#### Aplicação não inicia

```bash
# Verificar dependências
pip install streamlit plotly

# Verificar porta
lsof -i :8502  # Se ocupada, usar outra porta
streamlit run app/research/streamlit_backtest_app.py --server.port 8503
```

### Logs

A aplicação gera logs em:
- Console do Streamlit
- Logger Python (nível INFO)

Para debug detalhado:

```python
# Modificar no início do arquivo
logging.basicConfig(level=logging.DEBUG)
```

### Referências

- Código: `app/research/streamlit_backtest_app.py`
- Service: `app/backtest/service.py`
- Engine: `app/backtest/backtest_engine.py`
- Models: `app/backtest/models.py`
- Documentação: `app/backtest/README_PERSISTENCE.md`
