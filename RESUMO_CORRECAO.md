# Resumo da Correção - Pipeline de Scores

## Problema
Os scores não estavam sendo salvos no banco de dados. O pipeline executava, mas a tabela `scores_daily` permanecia vazia.

## Causa Raiz
O cálculo de fundamentos falhava com erro: `object of type 'float' has no len()`

Análise detalhada:
1. Pipeline buscava dados fundamentais do banco
2. Criava dicionário `fundamentals_data` com os campos
3. Chamava `calculate_all_factors()` para calcular fatores
4. O método detectava se era instituição financeira ou industrial
5. Para ambos os casos, alguns cálculos precisavam de campos que não estavam no dicionário:
   - `cash`: necessário para `calculate_financial_strength` (cálculo de dívida líquida)
   - `total_assets`: necessário para ROA em instituições financeiras

## Solução Implementada

### Arquivo: `scripts/run_pipeline_docker.py`

Adicionados campos faltantes no dicionário `fundamentals_data`:

```python
fundamentals_data = {
    'net_income': fundamental.net_income,
    'shareholders_equity': fundamental.shareholders_equity,
    'revenue': fundamental.revenue,
    'ebitda': fundamental.ebitda,
    'total_debt': fundamental.total_debt,
    'cash': 0.0,  # ✅ NOVO: Fallback até implementarmos coleta
    'eps': fundamental.eps,
    'enterprise_value': fundamental.enterprise_value,
    'book_value_per_share': fundamental.book_value_per_share,
    'total_assets': fundamental.total_assets  # ✅ NOVO: Para ROA
}
```

Melhorado logging de erros:
```python
except Exception as e:
    logger.warning(f"Erro ao calcular fundamentos para {ticker}: {e}")
    import traceback
    logger.debug(f"Traceback: {traceback.format_exc()}")  # ✅ NOVO
```

## Impacto da Correção

### Antes
```
Fundamentos: 0/5 calculados ❌
Features mensais: 0 tickers ❌
Scores: 5/5 calculados (apenas momentum, sem fundamentos) ⚠️
Tabela scores_daily: 0 registros ❌
```

### Depois (Esperado)
```
Fundamentos: 5/5 calculados ✅
Features mensais: 5 tickers ✅
Scores: 5/5 calculados (com momentum + fundamentos) ✅
Tabela scores_daily: 5 registros ✅
```

## Limitações Conhecidas

### 1. Campo `cash` com Valor Fallback
- **Situação**: Usando `cash = 0.0` como fallback
- **Impacto**: Cálculo de `financial_strength` pode não ser preciso
- **Solução Futura**: 
  - Adicionar coluna `cash` na tabela `raw_fundamentals`
  - Coletar valor real do yfinance: `info['totalCash']`
  - Atualizar ingestion_service para buscar este campo

### 2. Sem Histórico de Fundamentos
- **Situação**: Passando `fundamentals_history=None`
- **Impacto**: Não calcula métricas de 3 anos:
  - ROE robusto (média de 3 anos)
  - Crescimento de receita 3Y
  - Volatilidade do lucro líquido
- **Solução Futura**:
  - Buscar múltiplos períodos do banco: `ORDER BY period_end_date DESC LIMIT 3`
  - Converter para lista de dicts
  - Passar como `fundamentals_history`

## Próximos Passos

### Curto Prazo (Urgente)
1. ✅ Testar correção no EC2 (seguir `TESTE_EC2.md`)
2. ✅ Verificar que scores são salvos no banco
3. ✅ Confirmar que API retorna dados
4. ✅ Validar que frontend exibe ranking

### Médio Prazo (Melhorias)
1. Implementar coleta do campo `cash`
2. Implementar histórico de fundamentos (3 anos)
3. Adicionar mais campos ao schema se necessário:
   - `cash` ou `cash_and_equivalents`
   - `current_assets`
   - `current_liabilities`

### Longo Prazo (Otimizações)
1. Implementar cache de cálculos
2. Paralelizar cálculo de fatores
3. Adicionar validação de dados antes do cálculo
4. Implementar retry automático para falhas temporárias

## Arquivos Modificados

1. `scripts/run_pipeline_docker.py`
   - Adicionados campos `cash` e `total_assets`
   - Melhorado logging de erros

2. `TESTE_EC2.md` (NOVO)
   - Guia completo de teste no EC2

3. `RESUMO_CORRECAO.md` (NOVO)
   - Este documento

## Comandos para Deploy

```bash
# No EC2
cd ~/quant_stock_rank
git pull
docker compose build --no-cache backend
docker compose down
docker compose up -d

# Limpar dados antigos (opcional)
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "DELETE FROM scores_daily;"
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "DELETE FROM features_monthly;"

# Executar pipeline
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode test"

# Verificar resultados
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "SELECT COUNT(*) FROM scores_daily;"
curl http://localhost:8000/api/v1/ranking
```

## Referências

- Issue original: Scores não sendo salvos no banco
- Erro: `object of type 'float' has no len()`
- Logs: Pipeline executava mas `scores_daily` vazio
- Causa: Campos faltantes em `fundamentals_data`
- Solução: Adicionar `cash` e `total_assets`

## Contato

Para dúvidas ou problemas:
1. Verificar logs: `docker logs quant-ranker-backend`
2. Verificar banco: `docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker`
3. Consultar `TESTE_EC2.md` para troubleshooting
