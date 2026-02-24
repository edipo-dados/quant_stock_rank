# Quick Fix - Comandos Rápidos para EC2

## Atualizar e Testar (Copie e Cole)

```bash
# 1. Atualizar código
cd ~/quant_stock_rank && git pull

# 2. Rebuild backend
docker compose build --no-cache backend

# 3. Restart containers
docker compose down && docker compose up -d

# 4. Aguardar containers iniciarem (30 segundos)
sleep 30

# 5. Limpar dados antigos (opcional)
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "DELETE FROM scores_daily; DELETE FROM features_monthly;"

# 6. Executar pipeline
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode test"

# 7. Verificar scores no banco
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "SELECT COUNT(*) FROM scores_daily;"

# 8. Ver ranking
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "SELECT ticker, final_score, rank FROM scores_daily ORDER BY rank LIMIT 10;"

# 9. Testar API
curl http://localhost:8000/api/v1/ranking | jq
```

## O Que Esperar

### Logs do Pipeline (Sucesso)
```
✅ Colunas numéricas para normalização: ['roe', 'net_margin', 'pe_ratio', 'pb_ratio', ...]
✅ Fundamentos: 5/5 calculados
✅ Features mensais salvas: 5 tickers
✅ Scores: 5/5 calculados
✅ PIPELINE CONCLUÍDO COM SUCESSO
```

### Resultado no Banco
```
 count 
-------
     5
(1 row)
```

### API Response
```json
{
  "date": "2026-02-24",
  "ranking": [
    {
      "ticker": "ITUB4.SA",
      "rank": 1,
      "final_score": 0.089,
      ...
    }
  ]
}
```

## Se Algo Der Errado

### Ver logs completos
```bash
docker logs quant-ranker-backend --tail 200
```

### Verificar status dos containers
```bash
docker compose ps
```

### Restart completo
```bash
docker compose down
docker compose up -d
docker logs -f quant-ranker-backend
```

### Verificar dados no banco
```bash
# Entrar no PostgreSQL
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker

# Comandos úteis dentro do psql:
\dt                                    # Listar tabelas
SELECT COUNT(*) FROM raw_prices_daily;  # Ver preços
SELECT COUNT(*) FROM raw_fundamentals;  # Ver fundamentos
SELECT COUNT(*) FROM features_daily;    # Ver features diárias
SELECT COUNT(*) FROM features_monthly;  # Ver features mensais
SELECT COUNT(*) FROM scores_daily;      # Ver scores
\q                                      # Sair
```

## Erros Conhecidos (Corrigidos)

### ❌ "object of type 'float' has no len()"
**Status**: CORRIGIDO
**Causa**: Campos `cash` e `total_assets` faltando
**Solução**: Adicionados com valores fallback

### ❌ "unhashable type: 'list'"
**Status**: CORRIGIDO
**Causa**: Campo `net_income_history` (lista) sendo normalizado
**Solução**: Filtro de colunas numéricas implementado

## Acesso ao Frontend

Após pipeline executar com sucesso:
```
http://SEU_IP_EC2:8501
```

Páginas disponíveis:
1. 💬 Chat Assistente
2. 🏆 Ranking
3. 📊 Detalhes do Ativo

## Informações do Sistema

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:8501
- **Database**: postgres:5432
- **User**: quant_user
- **Password**: quant_password
- **Database**: quant_ranker

## Próximos Passos

Após confirmar que está funcionando:

1. Executar pipeline FULL:
```bash
docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full"
```

2. Configurar cron job para execução diária:
```bash
# Editar crontab
crontab -e

# Adicionar linha (executa todo dia às 18h):
0 18 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend bash -c "cd /app && PYTHONPATH=/app python scripts/run_pipeline_docker.py --mode liquid --limit 50" >> ~/pipeline.log 2>&1
```

3. Configurar backup automático do banco:
```bash
# Executar script de backup
cd ~/quant_stock_rank/deploy
chmod +x backup-db.sh
./backup-db.sh
```

## Suporte

Para mais detalhes:
- `TESTE_EC2.md` - Guia completo de teste
- `RESUMO_CORRECAO.md` - Análise técnica das correções
- `deploy/EC2_DEPLOY.md` - Guia completo de deploy
