# Deploy Quickstart v2.7.0

Guia rápido para fazer deploy da versão 2.7.0 com melhorias de robustez.

## 🚀 Deploy Rápido (5 minutos)

### Opção 1: Script Automatizado (Recomendado)

```bash
# 1. Conectar ao EC2
ssh ubuntu@<seu-ec2-ip>

# 2. Navegar para o diretório
cd ~/quant_stock_rank

# 3. Fazer backup
./deploy/backup-db.sh

# 4. Atualizar código (git ou upload manual)
git pull origin main
# OU fazer upload dos arquivos via scp

# 5. Executar deploy automatizado
chmod +x deploy/deploy_v2.7.0.sh
./deploy/deploy_v2.7.0.sh

# 6. Validar deploy
chmod +x deploy/validate_v2.7.0.sh
./deploy/validate_v2.7.0.sh
```

### Opção 2: Deploy Manual (10 minutos)

```bash
# 1. Conectar e navegar
ssh ubuntu@<seu-ec2-ip>
cd ~/quant_stock_rank

# 2. Backup
./deploy/backup-db.sh

# 3. Parar containers
docker-compose down

# 4. Atualizar código
git pull origin main

# 5. Rebuild e iniciar
docker-compose build backend
docker-compose up -d

# 6. Aguardar inicialização
sleep 30

# 7. Verificar saúde
curl http://localhost:8000/health
docker ps

# 8. Executar pipeline
docker exec -it quant-ranker-backend python scripts/run_smart_pipeline.py

# 9. Testar backtest
docker exec -it quant-ranker-backend python scripts/run_enhanced_backtest.py
```

## 📋 Checklist Mínimo

Antes de fazer deploy:

- [ ] ✅ Backup do banco criado
- [ ] ✅ Código atualizado no servidor
- [ ] ✅ Arquivos novos verificados:
  - `app/backtest/portfolio_risk.py`
  - `scripts/run_enhanced_backtest.py`
- [ ] ✅ `.env` configurado com `FMP_API_KEY`

Após deploy:

- [ ] ✅ Containers rodando (`docker ps`)
- [ ] ✅ API respondendo (`curl localhost:8000/health`)
- [ ] ✅ Pipeline executado com sucesso
- [ ] ✅ Backtest enhanced testado

## 🔍 Verificações Rápidas

### Verificar Containers
```bash
docker ps
# Deve mostrar: quant-ranker-backend e quant-ranker-frontend
```

### Verificar API
```bash
curl http://localhost:8000/health
# Deve retornar: {"status":"ok"} ou similar
```

### Verificar Logs
```bash
docker logs quant-ranker-backend --tail 50
# Não deve ter erros críticos
```

### Verificar Configurações
```bash
docker exec quant-ranker-backend python -c "
from app.config import settings
print(f'Volatility Targeting: {settings.use_volatility_targeting}')
print(f'Sector Limits: {settings.use_sector_limits}')
print(f'Target Vol: {settings.target_portfolio_volatility*100}%')
print(f'Max Sector: {settings.max_sector_exposure*100}%')
"
```

### Testar Backtest Enhanced
```bash
docker exec -it quant-ranker-backend python scripts/run_enhanced_backtest.py
```

Deve mostrar:
- Sharpe Ratio: 0.53-0.62 (esperado)
- Volatilidade: ~15%
- Exposição setorial: < 30%

## ⚠️ Troubleshooting Rápido

### Container não inicia
```bash
docker logs quant-ranker-backend
docker-compose restart
```

### API não responde
```bash
docker exec quant-ranker-backend curl http://localhost:8000/health
docker-compose restart backend
```

### Erro de importação
```bash
docker exec quant-ranker-backend python -c "from app.backtest.portfolio_risk import PortfolioRiskManager"
# Se falhar, verificar se arquivo foi copiado
docker exec quant-ranker-backend ls -la app/backtest/portfolio_risk.py
```

### Backtest falha
```bash
# Verificar dados
docker exec quant-ranker-backend python scripts/check_backtest_data.py

# Verificar benchmark
docker exec quant-ranker-backend python scripts/ingest_benchmark.py
```

## 🔄 Rollback Rápido

Se algo der errado:

```bash
# Parar containers
docker-compose down

# Restaurar backup do banco
./deploy/restore-db.sh backups/quant_ranker_backup_YYYYMMDD.db

# Reverter código (se fez backup)
cd ..
rm -rf quant_stock_rank
mv quant_stock_rank_backup_v2.6.0 quant_stock_rank
cd quant_stock_rank

# Reiniciar
docker-compose up -d
```

## 📊 Métricas de Sucesso

Após deploy, verificar:

✅ **Sharpe Ratio**: 0.53-0.62 (melhoria de 30-50%)  
✅ **Volatilidade**: ~15% (controlada)  
✅ **Max Drawdown**: -15% a -16% (melhoria)  
✅ **Alpha**: -50% a +50% (validado)  
✅ **Exposição Setorial**: < 30% por setor  

## 📞 Suporte

- **Documentação Completa**: `DEPLOY_V2.7.0.md`
- **Checklist Detalhado**: `deploy/PRE_DEPLOY_CHECKLIST_V2.7.0.md`
- **Melhorias Técnicas**: `ROBUSTEZ_V2.7.0.md`
- **Changelog**: `CHANGELOG.md`

## ⏱️ Tempo Estimado

- **Deploy Automatizado**: 5-10 minutos
- **Deploy Manual**: 10-15 minutos
- **Validação**: 5 minutos
- **Total**: 15-30 minutos

---

**Versão**: 2.7.0  
**Data**: Março 2026  
**Complexidade**: Baixa  
**Risco**: Baixo (rollback disponível)
