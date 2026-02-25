# EC2 Deploy - Quick Reference

**Versão**: 2.5.0  
**Status**: ✅ PRONTO

---

## 🚀 Deploy Rápido (Copy & Paste)

### 1. Conectar e Atualizar
```bash
ssh -i sua-chave.pem ubuntu@seu-ec2-ip
cd /home/ubuntu/quant_stock_rank
docker-compose down
git pull origin main
docker-compose up -d --build
sleep 60
docker-compose ps
```

### 2. Executar Migrações (ORDEM IMPORTANTE!)
```bash
docker exec quant-ranker-backend python scripts/migrate_add_academic_momentum.py
docker exec quant-ranker-backend python scripts/migrate_add_value_size_factors.py
docker exec quant-ranker-backend python scripts/migrate_add_backtest_smoothing.py
```

### 3. Aplicar Suavização
```bash
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all
```

### 4. Executar Pipeline
```bash
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50
```

### 5. Verificar
```bash
docker exec quant-ranker-backend python scripts/pre_deploy_check.py
docker exec quant-ranker-backend python scripts/check_db.py
curl http://localhost:8000/health
curl http://localhost:8501
```

---

## 🔄 Configurar Cron (Opcional)

```bash
crontab -e
```

Adicionar:
```cron
# Pipeline diário às 13:30 (segunda a sexta)
30 13 * * 1-5 cd /home/ubuntu/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> /var/log/quant_pipeline.log 2>&1

# Suavização após pipeline
45 13 * * 1-5 cd /home/ubuntu/quant_stock_rank && docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py >> /var/log/quant_smoothing.log 2>&1
```

---

## 🆘 Troubleshooting

### Containers não iniciam
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
docker-compose restart
```

### Migração falha
```bash
docker exec quant-ranker-backend python scripts/check_db.py
# Tentar migração novamente
```

### Pipeline falha
```bash
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode test
```

### Frontend não carrega
```bash
curl http://localhost:8000/health
docker-compose restart frontend
```

---

## 📊 Verificar Ranking

```bash
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
    smoothed = f'{s.final_score_smoothed:.3f}' if s.final_score_smoothed else 'N/A'
    print(f'Rank {s.rank:2d}: {s.ticker:10s} | Score: {s.final_score:.3f} | Smoothed: {smoothed}')
db.close()
"
```

---

## 💾 Backup

```bash
# Antes do deploy
docker exec quant-ranker-db pg_dump -U quant_user quant_ranker > backup_$(date +%Y%m%d).sql

# Restaurar se necessário
cat backup_20260225.sql | docker exec -i quant-ranker-db psql -U quant_user quant_ranker
```

---

## ✅ Checklist

- [ ] Conectar ao EC2
- [ ] Parar containers
- [ ] Pull código
- [ ] Rebuild containers
- [ ] Executar 3 migrações (ordem!)
- [ ] Aplicar suavização
- [ ] Executar pipeline
- [ ] Verificar health
- [ ] Verificar ranking
- [ ] Configurar cron (opcional)
- [ ] Fazer backup

---

**Última Atualização**: 2026-02-25
