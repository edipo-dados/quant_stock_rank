# Checklist de Deploy - v2.5.0

## ✅ Pré-Deploy (Concluído)

### Migrações de Banco de Dados
- [x] `migrate_add_academic_momentum.py` - Momentum acadêmico
- [x] `migrate_add_value_size_factors.py` - VALUE e SIZE
- [x] `migrate_add_backtest_smoothing.py` - Backtest e suavização

### Testes
- [x] Testes de missing values - PASSOU
- [x] Verificação de banco de dados - OK
- [x] Ranking funcionando - OK
- [x] Suavização temporal aplicada - OK
- [x] Backend health check - OK

### Funcionalidades Implementadas
- [x] Momentum acadêmico (exclui último mês)
- [x] Expansão VALUE (Price-to-Book, FCF Yield, EV/EBITDA)
- [x] Fator SIZE (size premium)
- [x] Tratamento de missing values (críticos vs secundários)
- [x] Remoção de penalidades fixas
- [x] Suavização temporal (alpha=0.7)
- [x] Backtest mensal completo
- [x] Métricas de performance (CAGR, Sharpe, Max DD, etc.)

## 📋 Deploy no EC2

### 1. Preparar Repositório Git

```bash
# No diretório local
cd quant_stock_rank

# Verificar status
git status

# Adicionar todos os arquivos
git add .

# Commit
git commit -m "v2.5.0: Backtest, Suavização Temporal e Melhorias Acadêmicas

- Momentum acadêmico (exclui último mês)
- Expansão VALUE (Price-to-Book, FCF Yield, EV/EBITDA)
- Fator SIZE (size premium)
- Tratamento de missing values
- Remoção de penalidades fixas
- Suavização temporal (alpha=0.7)
- Backtest mensal completo
- Métricas de performance"

# Push para repositório
git push origin main
```

### 2. Deploy no EC2

```bash
# Conectar ao EC2
ssh -i sua-chave.pem ubuntu@seu-ec2-ip

# Navegar para o diretório do projeto
cd /home/ubuntu/quant_stock_rank

# Parar containers
docker-compose down

# Atualizar código
git pull origin main

# Rebuild e restart
docker-compose up -d --build

# Aguardar containers iniciarem (30-60 segundos)
sleep 60

# Verificar status
docker-compose ps
```

### 3. Executar Migrações no EC2

```bash
# Migração 1: Academic Momentum
docker exec quant-ranker-backend python scripts/migrate_add_academic_momentum.py

# Migração 2: VALUE e SIZE
docker exec quant-ranker-backend python scripts/migrate_add_value_size_factors.py

# Migração 3: Backtest e Suavização
docker exec quant-ranker-backend python scripts/migrate_add_backtest_smoothing.py
```

### 4. Aplicar Suavização Temporal

```bash
# Aplicar suavização a todos os scores históricos
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all
```

### 5. Executar Pipeline

```bash
# Pipeline completo (50 ativos mais líquidos)
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50
```

### 6. Verificações Pós-Deploy

```bash
# 1. Verificar banco de dados
docker exec quant-ranker-backend python scripts/check_db.py

# 2. Verificar ranking
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date

db = SessionLocal()
scores = db.query(ScoreDaily).filter(
    ScoreDaily.date == date.today(),
    ScoreDaily.passed_eligibility == True
).order_by(ScoreDaily.rank).limit(10).all()

print('Top 10 Ranking:')
for s in scores:
    print(f'Rank {s.rank}: {s.ticker} - Score: {s.final_score:.3f}')
db.close()
"

# 3. Verificar health do backend
curl http://localhost:8000/health

# 4. Verificar frontend
curl http://localhost:8501
```

### 7. Configurar Cron (Opcional)

```bash
# Editar crontab
crontab -e

# Adicionar linha para executar pipeline diariamente às 13:30 (após fechamento do mercado)
30 13 * * 1-5 cd /home/ubuntu/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> /var/log/quant_pipeline.log 2>&1

# Adicionar linha para aplicar suavização após pipeline
45 13 * * 1-5 cd /home/ubuntu/quant_stock_rank && docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py >> /var/log/quant_smoothing.log 2>&1
```

## 🔧 Configuração de Ambiente

### Arquivo .env (Verificar)

```env
# Database
POSTGRES_USER=quant_user
POSTGRES_PASSWORD=quant_password
POSTGRES_DB=quant_ranker
POSTGRES_PORT=5432
DATABASE_URL=postgresql://quant_user:quant_password@postgres:5432/quant_ranker

# API Keys
GEMINI_API_KEY=sua_chave_aqui

# Scoring Weights
MOMENTUM_WEIGHT=0.35
QUALITY_WEIGHT=0.25
VALUE_WEIGHT=0.30
SIZE_WEIGHT=0.10

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
FRONTEND_PORT=8501
BACKEND_URL=http://localhost:8000
```

## 📊 Testes Opcionais no EC2

### Teste de Backtest

```bash
# Executar backtest de 1 ano
docker exec quant-ranker-backend python scripts/run_backtest.py \
    --top-n 10 \
    --weight-method equal \
    --use-smoothing \
    --save

# Verificar resultados
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import BacktestResult

db = SessionLocal()
results = db.query(BacktestResult).order_by(BacktestResult.created_at.desc()).limit(5).all()

print('Últimos Backtests:')
for r in results:
    print(f'{r.backtest_name}: CAGR={r.cagr:.2f}%, Sharpe={r.sharpe_ratio:.2f}, MaxDD={r.max_drawdown:.2f}%')
db.close()
"
```

## 🚨 Troubleshooting

### Problema: Containers não iniciam
```bash
# Ver logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Restart
docker-compose restart
```

### Problema: Migração falha
```bash
# Verificar conexão com banco
docker exec quant-ranker-backend python scripts/check_db.py

# Tentar migração novamente
docker exec quant-ranker-backend python scripts/migrate_add_backtest_smoothing.py
```

### Problema: Pipeline falha
```bash
# Ver logs detalhados
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode test

# Verificar APIs
docker exec quant-ranker-backend python scripts/test_apis.py
```

### Problema: Frontend não carrega
```bash
# Verificar se backend está respondendo
curl http://localhost:8000/health

# Restart frontend
docker-compose restart frontend
```

## 📝 Notas Importantes

1. **Backup do Banco**: Fazer backup antes do deploy
   ```bash
   docker exec quant-ranker-db pg_dump -U quant_user quant_ranker > backup_$(date +%Y%m%d).sql
   ```

2. **Pesos dos Fatores**: Verificar se somam 1.0
   - MOMENTUM_WEIGHT=0.35
   - QUALITY_WEIGHT=0.25
   - VALUE_WEIGHT=0.30
   - SIZE_WEIGHT=0.10
   - Total = 1.00 ✓

3. **Suavização Temporal**: Alpha padrão = 0.7
   - Pode ser ajustado conforme necessidade
   - Valores maiores = mais reativo
   - Valores menores = mais suave

4. **Backtest**: Requer dados históricos
   - Mínimo 1 ano de dados recomendado
   - Snapshots mensais criados automaticamente

## ✅ Checklist Final

- [ ] Código commitado no Git
- [ ] Push para repositório remoto
- [ ] Deploy no EC2 executado
- [ ] Migrações executadas
- [ ] Suavização aplicada
- [ ] Pipeline executado com sucesso
- [ ] Verificações pós-deploy OK
- [ ] Cron configurado (opcional)
- [ ] Backup do banco realizado
- [ ] Documentação atualizada

## 📚 Documentação

- `docs/CALCULOS_RANKING.md` - Cálculos detalhados
- `docs/BACKTEST_SMOOTHING.md` - Backtest e suavização
- `docs/MELHORIAS_ACADEMICAS.md` - Melhorias implementadas
- `docs/MISSING_VALUE_TREATMENT.md` - Tratamento de missing
- `CHANGELOG.md` - Histórico de mudanças

---

**Versão**: 2.5.0  
**Data**: 2026-02-25  
**Status**: ✅ Pronto para Deploy
