# Como Usar a Busca Automática de Ativos Líquidos

## Visão Geral

O sistema agora pode buscar automaticamente os ativos mais líquidos da B3 baseado no volume médio de negociação. Isso elimina a necessidade de manter uma lista hardcoded de tickers.

## Modos de Execução do Pipeline

O pipeline agora suporta 3 modos de seleção de ativos:

### 1. Modo TEST (Padrão)
Processa apenas 5 ativos para testes rápidos.

```bash
python scripts/run_pipeline.py --mode test
```

Ativos processados:
- ITUB4.SA (Itaú)
- BBDC4.SA (Bradesco)
- PETR4.SA (Petrobras)
- MGLU3.SA (Magazine Luiza)
- AMER3.SA (Americanas - para testar exclusão)

### 2. Modo LIQUID (Recomendado para Produção)
Busca automaticamente os ativos mais líquidos da B3.

```bash
# Top 100 mais líquidos (padrão)
python scripts/run_pipeline.py --mode liquid

# Top 50 mais líquidos
python scripts/run_pipeline.py --mode liquid --limit 50

# Top 200 mais líquidos
python scripts/run_pipeline.py --mode liquid --limit 200
```

**Vantagens:**
- ✅ Sempre atualizado com os ativos mais negociados
- ✅ Elimina viés de seleção manual
- ✅ Maximiza a cobertura do mercado
- ✅ Foca em ativos com liquidez real

**Como funciona:**
1. Analisa o universo de ~90 ativos da B3
2. Calcula volume médio dos últimos 30 dias
3. Calcula volume financeiro (volume × preço)
4. Filtra ativos com volume mínimo de R$ 1 milhão/dia
5. Ordena por liquidez (mais líquido primeiro)
6. Retorna os top N ativos

### 3. Modo MANUAL
Permite especificar manualmente quais ativos processar.

```bash
python scripts/run_pipeline.py --mode manual --tickers VALE3.SA PETR4.SA ITUB4.SA
```

## Critérios de Liquidez

### Volume Financeiro Médio
- **Mínimo padrão**: R$ 1.000.000 por dia
- **Cálculo**: Volume de ações × Preço médio
- **Período**: Últimos 30 dias

### Universo de Ativos
O sistema analisa ~90 ativos incluindo:
- Componentes do Ibovespa
- Principais ações de cada setor
- Ativos com histórico de alta liquidez

Setores cobertos:
- Bancos (ITUB4, BBDC4, BBAS3, etc.)
- Petróleo e Energia (PETR4, PETR3, PRIO3, etc.)
- Mineração (VALE3, CSNA3, GGBR4, etc.)
- Varejo (MGLU3, LREN3, ARZZ3, etc.)
- Alimentos (ABEV3, JBSS3, BRFS3, etc.)
- Telecomunicações (VIVT3, TIMS3)
- Utilities (ELET3, CMIG4, CPFE3, etc.)
- E mais...

## Testando a Funcionalidade

### Teste Rápido
```bash
python test_liquid_stocks.py
```

Este script executa 4 testes:
1. **Top 10 mais líquidos**: Valida busca básica
2. **Top 50 mais líquidos**: Valida limite maior
3. **Busca com detalhes**: Valida DataFrame completo
4. **Filtro de volume**: Valida filtro de volume mínimo

### Saída Esperada
```
Top 10 Ativos Mais Líquidos:
--------------------------------------------------------------------------------
VALE3.SA   - Avg Volume:   45,234,567 shares, Avg Financial Volume: R$  2,345,678,901.23, Avg Price: R$    51.85
PETR4.SA   - Avg Volume:   38,123,456 shares, Avg Financial Volume: R$  1,987,654,321.45, Avg Price: R$    52.10
ITUB4.SA   - Avg Volume:   32,456,789 shares, Avg Financial Volume: R$  1,234,567,890.12, Avg Price: R$    38.05
...
```

## Exemplos de Uso

### Desenvolvimento Local
```bash
# Teste rápido com 5 ativos
python scripts/run_pipeline.py --mode test

# Teste com top 20 mais líquidos
python scripts/run_pipeline.py --mode liquid --limit 20
```

### Produção
```bash
# Pipeline completo com top 100 mais líquidos
python scripts/run_pipeline.py --mode liquid --limit 100

# Pipeline com top 50 (mais rápido)
python scripts/run_pipeline.py --mode liquid --limit 50
```

### Análise Específica
```bash
# Analisar apenas bancos
python scripts/run_pipeline.py --mode manual --tickers ITUB4.SA BBDC4.SA BBAS3.SA SANB11.SA

# Analisar apenas petróleo
python scripts/run_pipeline.py --mode manual --tickers PETR4.SA PETR3.SA PRIO3.SA
```

## Configuração Avançada

### Ajustar Volume Mínimo
Edite `app/ingestion/b3_liquid_stocks.py`:

```python
# Aumentar volume mínimo para R$ 5 milhões/dia
tickers = fetcher.fetch_most_liquid_stocks(
    limit=100,
    min_volume=5_000_000  # R$ 5M
)
```

### Ajustar Período de Análise
```python
# Usar últimos 60 dias ao invés de 30
tickers = fetcher.fetch_most_liquid_stocks(
    limit=100,
    lookback_days=60
)
```

### Adicionar Novos Ativos ao Universo
Edite a lista `B3_UNIVERSE` em `app/ingestion/b3_liquid_stocks.py`:

```python
B3_UNIVERSE = [
    # ... ativos existentes ...
    "NOVO1.SA",  # Adicionar novo ativo
    "NOVO2.SA",
]
```

## Vantagens vs Lista Hardcoded

| Aspecto | Lista Hardcoded | Busca Automática |
|---------|----------------|------------------|
| Atualização | Manual | Automática |
| Viés de seleção | Alto | Baixo |
| Cobertura | Fixa | Dinâmica |
| Manutenção | Alta | Baixa |
| Liquidez garantida | Não | Sim |

## Troubleshooting

### Erro: "Nenhum ativo líquido encontrado"
**Causa**: Problemas de conexão com Yahoo Finance ou volume mínimo muito alto

**Solução**:
```bash
# Verificar conexão
python test_liquid_stocks.py

# Reduzir volume mínimo
# Editar b3_liquid_stocks.py e reduzir min_volume
```

### Erro: "No data for ticker"
**Causa**: Ticker não tem dados no Yahoo Finance

**Solução**: O sistema automaticamente pula esses tickers

### Pipeline muito lento
**Causa**: Muitos ativos sendo processados

**Solução**:
```bash
# Reduzir limite
python scripts/run_pipeline.py --mode liquid --limit 30
```

## Próximos Passos

1. ✅ Implementado: Busca automática de ativos líquidos
2. 🔄 Sugerido: Cache de liquidez (evitar buscar todo dia)
3. 🔄 Sugerido: Integração com API da B3 oficial
4. 🔄 Sugerido: Filtro por setor/segmento
5. 🔄 Sugerido: Alertas de mudança de liquidez

## Referências

- **Yahoo Finance**: Fonte de dados de volume e preços
- **B3 Universe**: Lista curada de ~90 ativos principais
- **Volume Financeiro**: Métrica principal de liquidez
