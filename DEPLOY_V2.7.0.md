# Guia de Deploy - v2.7.0

Deploy da versão 2.7.0 com melhorias de robustez (Volatility Targeting, Sector Limits, Alpha Corrigido).

## 📋 Pré-requisitos

- Acesso SSH ao servidor EC2
- Docker e Docker Compose instalados
- Backup do banco de dados atual
- Variáveis de ambiente configuradas (.env)

## 🔄 Processo de Deploy

### 1. Backup do Sistema Atual

```bash
# Conectar ao EC2
ssh ubuntu@<seu-ec2-ip>

# Navegar para o diretório
cd ~/quant_stock_rank

# Fazer backup do banco de dados
./deploy/backup-db.sh

# Verificar backup criado
ls -lh backups/
```

### 2. Atualizar Código

```bash
# Parar containers
docker-compose down

# Fazer backup do código atual (opcional)
cp -r ~/quant_stock_rank ~/quant_stock_rank_backup_v2.6.0

# Atualizar do repositório
git pull origin main

# Ou fazer upload manual dos arquivos modificados
# scp -r app/ ubuntu@<ec2-ip>:~/quant_stock_rank/
# scp -r scripts/ ubuntu@<ec2-ip>:~/quant_stock_rank/
```

### 3. Verificar Arquivos Novos

```bash
# Verificar que os novos arquivos foram copiados
ls -la app/backtest/portfolio_risk.py
ls -la scripts/run_enhanced_backtest.py
ls -la ROBUSTEZ_V2.7.0.md

# Verificar modificações
git diff HEAD~1 app/config.py
git diff HEAD~1 app/backtest/portfolio.py
git diff HEAD~1 app/backtest/metrics.py
```

### 4. Atualizar Configurações

```bash
# Editar .env se necessário
nano .env

# Verificar configurações em app/config.py
# Valores padrão já estão corretos:
# use_volatility_targeting = True
# target_portfolio_volatility = 0.15
# use_sector_limits = True
# max_sector_exposure = 0.30
```

### 5. Rebuild dos Containers

```bash
# Rebuild da imagem backend
docker-compose build backend

# Verificar imagem criada
docker images | grep quant

# Iniciar containers
docker-compose up -d

# Verificar logs
docker-compose logs -f backend
```

### 6. Verificar Saúde do Sistema

```bash
# Verificar containers rodando
docker ps

# Testar API
curl http://localhost:8000/health

# Verificar logs
docker logs quant-ranker-backend --tail 50

# Verificar frontend
curl http://localhost:8501
```

### 7. Validar Dados

```bash
# Verificar banco de dados
docker exec -it quant-ranker-backend python scripts/check_db.py

# Verificar cobertura de dados
docker exec -it quant-ranker-backend python scripts/check_historical_coverage.py

# Verificar scores mais recentes
docker exec -it quant-ranker-backend python scripts/check_latest_scores.py
```

### 8. Executar Pipeline de Atualização

```bash
# Executar pipeline completo
docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py

# Verificar execução
docker logs quant-ranker-backend --tail 100
```

### 9. Testar Backtest Enhanced

```bash
# Executar backtest com melhorias v2.7.0
docker exec -it quant-ranker-backend python scripts/run_enhanced_backtest.py

# Comparar com versão anterior
docker exec -it quant-ranker-backend python scripts/run_optimized_backtest.py
```

### 10. Atualizar Cron (se necessário)

```bash
# Editar crontab
crontab -e

# Adicionar/atualizar linha (se ainda não existe)
0 19 * * 1-5 cd /home/ubuntu/quant_stock_rank && docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py >> /var/log/quant_ranker.log 2>&1

# Verificar cron configurado
crontab -l
```

## 🧪 Testes Pós-Deploy

### Teste 1: API Endpoints

```bash
# Ranking atual
curl http://localhost:8000/api/ranking/latest

# Ranking por data
curl http://localhost:8000/api/ranking/date/2026-03-01

# Health check
curl http://localhost:8000/health
```

### Teste 2: Frontend

```bash
# Acessar no navegador
http://<seu-ec2-ip>:8501

# Verificar:
# - Ranking atual carrega
# - Gráficos aparecem
# - Filtros funcionam
```

### Teste 3: Backtest

```bash
# Executar backtest enhanced
docker exec -it quant-ranker-backend python scripts/run_enhanced_backtest.py

# Verificar métricas:
# - Sharpe Ratio > 0.5 (esperado)
# - Volatilidade ~15%
# - Alpha validado (-50% a +50%)
# - Exposição setorial < 30%
```

### Teste 4: Pipeline

```bash
# Executar pipeline manualmente
docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py

# Verificar:
# - Ingestão de preços OK
# - Cálculo de scores OK
# - Ranking gerado OK
```

## 🔍 Troubleshooting

### Problema: Container não inicia

```bash
# Ver logs detalhados
docker logs quant-ranker-backend

# Verificar portas
netstat -tulpn | grep -E '8000|8501'

# Reiniciar containers
docker-compose restart
```

### Problema: Erro de importação

```bash
# Verificar arquivo existe
docker exec -it quant-ranker-backend ls -la app/backtest/portfolio_risk.py

# Verificar sintaxe Python
docker exec -it quant-ranker-backend python -m py_compile app/backtest/portfolio_risk.py

# Reinstalar dependências
docker exec -it quant-ranker-backend pip install -r requirements.txt
```

### Problema: Backtest falha

```bash
# Verificar dados disponíveis
docker exec -it quant-ranker-backend python scripts/check_backtest_data.py

# Verificar benchmark
docker exec -it quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.backtest.benchmark import BenchmarkManager
db = SessionLocal()
bm = BenchmarkManager(db)
avail = bm.get_data_availability('2022-01-01', '2026-03-01')
print(avail)
db.close()
"

# Reingerir benchmark se necessário
docker exec -it quant-ranker-backend python scripts/ingest_benchmark.py
```

### Problema: Setores não encontrados

```bash
# Verificar AssetInfo
docker exec -it quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import AssetInfo
db = SessionLocal()
assets = db.query(AssetInfo).filter(AssetInfo.sector.isnot(None)).count()
print(f'Assets with sector: {assets}')
db.close()
"

# Atualizar informações de ativos
docker exec -it quant-ranker-backend python scripts/update_liquid_stocks.py
```

## 📊 Monitoramento Pós-Deploy

### Métricas a Acompanhar

1. **Performance do Sistema**
   - Tempo de execução do pipeline
   - Uso de memória/CPU
   - Tempo de resposta da API

2. **Qualidade dos Dados**
   - Cobertura de preços
   - Scores calculados
   - Ativos no ranking

3. **Métricas de Backtest**
   - Sharpe Ratio (esperado: 0.53-0.62)
   - Volatilidade (esperado: ~15%)
   - Exposição setorial (máx 30%)

### Logs a Monitorar

```bash
# Logs do backend
tail -f /var/log/quant_ranker.log

# Logs do Docker
docker logs -f quant-ranker-backend

# Logs do sistema
journalctl -u docker -f
```

## 🔄 Rollback (se necessário)

### Opção 1: Reverter Código

```bash
# Parar containers
docker-compose down

# Restaurar backup
rm -rf ~/quant_stock_rank
mv ~/quant_stock_rank_backup_v2.6.0 ~/quant_stock_rank
cd ~/quant_stock_rank

# Reiniciar
docker-compose up -d
```

### Opção 2: Reverter Banco

```bash
# Restaurar backup do banco
./deploy/restore-db.sh backups/quant_ranker_backup_YYYYMMDD.db

# Reiniciar containers
docker-compose restart
```

### Opção 3: Desativar Melhorias

```bash
# Editar config.py
docker exec -it quant-ranker-backend nano app/config.py

# Alterar:
# use_volatility_targeting = False
# use_sector_limits = False

# Reiniciar backend
docker-compose restart backend
```

## ✅ Checklist de Deploy

- [ ] Backup do banco de dados criado
- [ ] Código atualizado (git pull ou upload manual)
- [ ] Arquivos novos verificados (portfolio_risk.py, run_enhanced_backtest.py)
- [ ] Configurações revisadas (.env, config.py)
- [ ] Containers rebuilded e iniciados
- [ ] API respondendo (curl /health)
- [ ] Frontend acessível
- [ ] Banco de dados validado
- [ ] Pipeline executado com sucesso
- [ ] Backtest enhanced testado
- [ ] Métricas validadas (Sharpe, Vol, Setores)
- [ ] Cron atualizado (se necessário)
- [ ] Logs monitorados
- [ ] Documentação atualizada

## 📞 Suporte

Em caso de problemas:
1. Verificar logs: `docker logs quant-ranker-backend`
2. Consultar troubleshooting acima
3. Verificar documentação: `ROBUSTEZ_V2.7.0.md`
4. Rollback se necessário

---

**Versão**: 2.7.0  
**Data**: Março 2026  
**Tempo Estimado**: 30-45 minutos  
**Complexidade**: Média  
**Risco**: Baixo (rollback disponível)
