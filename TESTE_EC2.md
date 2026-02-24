# Guia de Teste - Correção de Scores no EC2

## Problema Identificado
Os fundamentos não estavam sendo calculados devido a dois problemas:

1. **Campos faltantes** no dicionário `fundamentals_data`:
   - Campo `cash` estava faltando (necessário para `calculate_financial_strength`)
   - Campo `total_assets` estava faltando (necessário para ROA em instituições financeiras)

2. **Colunas não-numéricas** sendo passadas para normalização:
   - Campo `net_income_history` é uma lista, não um valor numérico
   - O normalizador tentava processar listas, causando erro `TypeError: unhashable type: 'list'`

## Correção Aplicada

### Correção 1: Campos Faltantes
Adicionados os campos faltantes com valores fallback:
- `cash`: 0.0 (fallback até implementarmos a coleta deste dado)
- `total_assets`: valor do banco de dados
- Melhorado logging de erros com traceback completo

### Correção 2: Filtro de Colunas Numéricas
Implementado filtro para excluir colunas não-numéricas antes da normalização:
- Verifica tipo de cada coluna
- Inclui apenas valores numéricos (int, float)
- Exclui listas, dicts e outros tipos não-numéricos
- Log das colunas selecionadas para debug

## Passos para Testar no EC2

### 1. Conectar ao EC2
```bash
ssh -i sua-chave.pem ubuntu@SEU_IP_EC2
```

### 2. Atualizar o Código
```bash
cd ~/quant_stock_rank
git pull
```

### 3. Rebuild do Backend (com cache limpo)
```bash
docker compose build --no-cache backend
```

### 4. Restart dos Containers
```bash
docker compose down
docker compose up -d
```

### 5. Verificar que Containers Estão Rodando
```bash
docker compose ps
```

Deve mostrar todos os 3 containers como "Up":
- quant-ranker-backend
- quant-ranker-frontend  
- quant-ranker-db

### 6. Limpar Scores Antigos (Opcional mas Recomendado)
```bash
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "DELETE FROM scores_daily;"
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "DELETE FROM features_monthly;"
```

### 7. Executar Pipeline em Modo Teste
```bash
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode test"
```

### 8. Verificar Logs do Pipeline
Procure por:
- ✅ "Colunas numéricas para normalização: [...]" (deve listar as colunas)
- ✅ "Fundamentos: X/5 calculados" (deve ser > 0, idealmente 5/5)
- ✅ "Features mensais salvas: X tickers" (deve ser > 0)
- ✅ "Scores: X/5 calculados" (deve ser 5/5)
- ❌ "Erro ao calcular fundamentos" (não deve aparecer mais)
- ❌ "unhashable type: 'list'" (não deve aparecer mais)

### 9. Verificar Dados no Banco
```bash
# Verificar features mensais
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "SELECT COUNT(*) FROM features_monthly;"

# Verificar scores
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "SELECT COUNT(*) FROM scores_daily;"

# Ver os scores calculados
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "SELECT ticker, final_score, rank FROM scores_daily ORDER BY rank LIMIT 10;"
```

### 10. Testar API
```bash
curl http://localhost:8000/api/v1/ranking
```

Deve retornar JSON com os scores, não mais erro 404.

### 11. Testar Frontend
Abra no navegador:
```
http://SEU_IP_EC2:8501
```

A página de Ranking deve mostrar os ativos com scores.

## Resultados Esperados

### Antes da Correção
```
Fundamentos: 0/5 calculados
Features mensais salvas: 0 tickers
Scores: 5/5 calculados (mas sem fundamentos, apenas momentum)
```

### Depois da Correção
```
Fundamentos: 5/5 calculados
Features mensais salvas: 5 tickers
Scores: 5/5 calculados (com fundamentos completos)
```

## Troubleshooting

### Se houver erro "unhashable type: 'list'"
Este erro foi corrigido. Se ainda aparecer:
1. Verifique se o código foi atualizado: `git log --oneline -1`
2. Rebuild do backend: `docker compose build --no-cache backend`
3. Verifique os logs: `docker logs quant-ranker-backend --tail 100`

### Se ainda houver erro "object of type 'float' has no len()"
Verifique os logs detalhados:
```bash
docker logs quant-ranker-backend --tail 100
```

O traceback completo agora será exibido.

### Se scores ainda estiverem vazios
1. Verifique se o pipeline completou com sucesso
2. Verifique se há dados de preços:
   ```bash
   docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "SELECT COUNT(*) FROM raw_prices_daily;"
   ```
3. Verifique se há dados fundamentais:
   ```bash
   docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "SELECT COUNT(*) FROM raw_fundamentals;"
   ```

### Se o backend não iniciar
```bash
docker logs quant-ranker-backend
```

Procure por erros de importação ou sintaxe.

## Próximos Passos (Após Teste Bem-Sucedido)

1. Implementar coleta do campo `cash` do yfinance
2. Adicionar coluna `cash` na tabela `raw_fundamentals`
3. Implementar cálculo de fundamentos com histórico (3 anos)
4. Executar pipeline em modo FULL para todos os ativos líquidos

## Informações do Banco de Dados

- Host: postgres (dentro do Docker)
- Porta: 5432
- Usuário: quant_user
- Senha: quant_password
- Database: quant_ranker

## Comandos Úteis

```bash
# Ver logs em tempo real
docker logs -f quant-ranker-backend

# Entrar no container do backend
docker exec -it quant-ranker-backend bash

# Entrar no PostgreSQL
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker

# Restart apenas do backend
docker compose restart backend

# Ver uso de recursos
docker stats
```
