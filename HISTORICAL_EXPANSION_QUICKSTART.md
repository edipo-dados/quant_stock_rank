# Guia Rápido: Expansão Histórica

Guia prático para expandir dados históricos de todos os tickers da B3.

## 🚀 Início Rápido

### 1. Executar Expansão Completa

```bash
# Dentro do Docker (recomendado)
docker exec quant-ranker-backend python scripts/ingest_full_history.py --start 2018-01-01

# Ou localmente
python scripts/ingest_full_history.py --start 2018-01-01
```

**Tempo estimado**: ~1 hora para 100 tickers

### 2. Verificar Cobertura

```bash
# Verificar estatísticas de cobertura
docker exec quant-ranker-backend python scripts/check_historical_coverage.py
```

### 3. Ver Relatório de Qualidade

```bash
# Ver relatório JSON gerado
docker exec quant-ranker-backend cat data_quality_report.json
```

## 📊 O Que Será Feito

1. ✅ Buscar todos os tickers já cadastrados no banco
2. ✅ Ingerir preços históricos desde 2018-01-01
3. ✅ Ingerir fundamentos históricos (últimos 5 anos)
4. ✅ Validar qualidade técnica dos dados
5. ✅ Gerar relatório completo

## 🎯 Resultados Esperados

Após execução:

- **5 anos de preços** por ticker (2018-2024)
- **3-5 anos de fundamentos** por ticker
- **Taxa de validação ≥ 80%** para tickers líquidos
- **Relatório JSON** com detalhes de qualidade
- **Base pronta** para backtests de 5 anos

## 🔧 Opções Úteis

### Modo Incremental (Atualização)

```bash
# Buscar apenas dados novos desde última execução
docker exec quant-ranker-backend python scripts/ingest_full_history.py --mode incremental
```

### Processar Tickers Específicos

```bash
# Processar apenas alguns tickers
docker exec quant-ranker-backend python scripts/ingest_full_history.py \
  --start 2018-01-01 \
  --tickers "PETR4.SA,VALE3.SA,ITUB4.SA"
```

### Apenas Preços ou Fundamentos

```bash
# Apenas preços
docker exec quant-ranker-backend python scripts/ingest_full_history.py \
  --start 2018-01-01 \
  --skip-fundamentals

# Apenas fundamentos
docker exec quant-ranker-backend python scripts/ingest_full_history.py \
  --skip-prices
```

### Pular Validação (Mais Rápido)

```bash
# Pular validação para execução mais rápida
docker exec quant-ranker-backend python scripts/ingest_full_history.py \
  --start 2018-01-01 \
  --skip-validation
```

## 📝 Logs

### Ver Logs em Tempo Real

```bash
# Acompanhar execução
docker exec quant-ranker-backend tail -f ingest_full_history.log
```

### Ver Logs Completos

```bash
# Ver todo o log
docker exec quant-ranker-backend cat ingest_full_history.log
```

## ⚠️ Troubleshooting

### Erro: "Too Many Requests (429)"

**Solução**: Aguardar alguns minutos e tentar novamente

```bash
# Reduzir paralelização
docker exec quant-ranker-backend python scripts/ingest_full_history.py \
  --start 2018-01-01 \
  --max-workers 3
```

### Taxa de Validação Baixa (<80%)

**Solução**: Verificar se tickers são válidos

```bash
# Ver cobertura atual
docker exec quant-ranker-backend python scripts/check_historical_coverage.py
```

### Execução Interrompida

**Solução**: Executar novamente em modo incremental

```bash
# Continuar de onde parou
docker exec quant-ranker-backend python scripts/ingest_full_history.py --mode incremental
```

## 🔄 Compatibilidade

### Pipeline Diário

✅ **Não interfere** com o pipeline diário
✅ **Pode rodar em paralelo** (com cuidado no rate limiting)
✅ **Usa mesmas tabelas** (upsert automático)

### Backtest

✅ **Compatível** com backtest de 5 anos
✅ **Suporta** histórico adaptativo (1-3 anos)
✅ **Garante** dados suficientes para Quality 3Y

## 📚 Documentação Completa

Para mais detalhes, consulte:

- [docs/HISTORICAL_EXPANSION.md](docs/HISTORICAL_EXPANSION.md) - Documentação completa
- [docs/PIPELINE_ARCHITECTURE.md](docs/PIPELINE_ARCHITECTURE.md) - Arquitetura do pipeline
- [README.md](README.md) - Visão geral do sistema

## 💡 Dicas

1. **Execute fora de horário de pico** para evitar rate limiting
2. **Use modo incremental** para atualizações diárias
3. **Monitore os logs** para identificar problemas
4. **Verifique o relatório** após execução
5. **Mantenha max-workers em 5** para estabilidade

## 🎉 Pronto!

Após a execução, sua base estará pronta para:

- ✅ Backtests de 5 anos (2018-2024)
- ✅ Análises de longo prazo
- ✅ Validação estatística robusta
- ✅ Cálculo de fatores com histórico completo
