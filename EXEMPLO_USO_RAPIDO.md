# Exemplo de Uso Rápido - Ativos Líquidos

## Resultados dos Testes

✅ **Todos os testes passaram!**

### Top 10 Ativos Mais Líquidos da B3

| Posição | Ticker | Volume Médio | Volume Financeiro | Preço Médio |
|---------|--------|--------------|-------------------|-------------|
| 1 | VALE3.SA | 36.9M ações | R$ 3.16 bilhões | R$ 85.59 |
| 2 | ITUB4.SA | 36.7M ações | R$ 1.68 bilhões | R$ 45.30 |
| 3 | PETR4.SA | 44.1M ações | R$ 1.59 bilhões | R$ 36.18 |
| 4 | BBAS3.SA | 40.0M ações | R$ 988 milhões | R$ 24.45 |
| 5 | B3SA3.SA | 54.1M ações | R$ 877 milhões | R$ 16.35 |
| 6 | BBDC4.SA | 40.4M ações | R$ 842 milhões | R$ 20.85 |
| 7 | BPAC11.SA | 11.8M ações | R$ 706 milhões | R$ 59.32 |
| 8 | PRIO3.SA | 11.8M ações | R$ 589 milhões | R$ 49.79 |
| 9 | PETR3.SA | 14.6M ações | R$ 563 milhões | R$ 38.69 |
| 10 | SBSP3.SA | 3.3M ações | R$ 472 milhões | R$ 141.89 |

## Como Usar

### 1. Teste Rápido (5 ativos)
```bash
python scripts/run_pipeline.py --mode test
```

### 2. Top 10 Mais Líquidos
```bash
python scripts/run_pipeline.py --mode liquid --limit 10
```

### 3. Top 50 Mais Líquidos (Recomendado)
```bash
python scripts/run_pipeline.py --mode liquid --limit 50
```

### 4. Top 100 Mais Líquidos (Produção)
```bash
python scripts/run_pipeline.py --mode liquid --limit 100
```

### 5. Lista Manual
```bash
python scripts/run_pipeline.py --mode manual --tickers VALE3.SA PETR4.SA ITUB4.SA
```

## Estatísticas

- **Universo analisado**: 82 ativos da B3
- **Ativos com liquidez > R$ 1M/dia**: 63 ativos
- **Ativos com liquidez > R$ 10M/dia**: 61 ativos
- **Período de análise**: Últimos 30 dias
- **Métrica principal**: Volume financeiro médio (volume × preço)

## Próximos Passos

1. ✅ Funcionalidade implementada e testada
2. 🔄 Rodar pipeline com top 50 mais líquidos
3. 🔄 Validar resultados do ranking
4. 🔄 Comparar com lista hardcoded anterior
