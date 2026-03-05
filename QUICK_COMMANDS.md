# Comandos Rápidos - Modelo Multifator v2.0

## 🚀 Deploy

```bash
# Backup
./deploy/backup-db.sh

# Pull e rebuild
git pull origin main
docker-compose down
docker-compose build backend frontend
docker-compose up -d

# Verificar
docker ps
docker logs quant-ranker-backend --tail 50
```

---

## ✅ Validação

```bash
# Validar dados
docker exec quant-ranker-backend python scripts/validate_backtest_data.py \
  --start-date 2021-01-01 \
  --end-date 2026-03-05 \
  --top-n 10

# Verificar configuração
docker exec quant-ranker-backend python -c "
from app.config import settings
print(f'Momentum: {settings.momentum_weight}')
print(f'Quality: {settings.quality_weight}')
print(f'Value: {settings.value_weight}')
print(f'Risk: {settings.risk_weight}')
print(f'Market Cap Min: {settings.minimum_market_cap}')
"
```

---

## 🔄 Pipeline

```bash
# Rodar pipeline completo
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py

# Verificar scores recentes
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date, timedelta

db = SessionLocal()
recent_date = date.today() - timedelta(days=1)

count = db.query(ScoreDaily).filter(
    ScoreDaily.date == recent_date
).count()

print(f'Scores em {recent_date}: {count}')
db.close()
"
```

---

## 📊 Backtest

```bash
# Via script
docker exec quant-ranker-backend python scripts/run_backtest_pipeline.py \
  --start-date 2021-01-01 \
  --end-date 2026-03-05 \
  --top-n 10

# Via frontend
# Acessar: http://seu-ec2-ip:8501
# Ir para: 🔬 Research Backtest
```

---

## 🔍 Monitoramento

```bash
# Logs em tempo real
docker logs quant-ranker-backend --tail 100 --follow

# Status dos containers
docker ps

# Uso de recursos
docker stats

# Espaço em disco
df -h

# Verificar processos
docker exec quant-ranker-backend ps aux
```

---

## 🗄️ Banco de Dados

```bash
# Backup
./deploy/backup-db.sh

# Listar backups
ls -lh backups/

# Restaurar
./deploy/restore-db.sh backups/quant_ranker_YYYY-MM-DD_HH-MM-SS.sql

# Conectar ao banco
docker exec -it quant-ranker-db psql -U postgres -d quant_ranker

# Queries úteis
docker exec quant-ranker-db psql -U postgres -d quant_ranker -c "
SELECT date, COUNT(*) as count 
FROM scores_daily 
WHERE date >= '2026-01-01' 
GROUP BY date 
ORDER BY date DESC 
LIMIT 10;
"
```

---

## 🧹 Limpeza

```bash
# Limpar dados de backtest antigos
docker exec quant-ranker-backend python scripts/clear_backtest_data.py

# Limpar logs antigos
docker exec quant-ranker-backend find /app/logs -name "*.log" -mtime +30 -delete

# Limpar imagens Docker não usadas
docker image prune -a

# Limpar volumes não usados
docker volume prune
```

---

## 🔧 Troubleshooting

```bash
# Container não inicia
docker logs quant-ranker-backend --tail 100
docker-compose down
docker-compose up -d

# Erro de conexão com banco
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
db = SessionLocal()
print('Conexão OK')
db.close()
"

# Verificar variáveis de ambiente
docker exec quant-ranker-backend env | grep -E 'DATABASE|FMP|GEMINI'

# Reiniciar serviço específico
docker-compose restart backend
docker-compose restart frontend
```

---

## 📝 Verificações Rápidas

```bash
# Verificar versão do código
git log --oneline -5

# Verificar última execução do pipeline
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from sqlalchemy import func

db = SessionLocal()
last_date = db.query(func.max(ScoreDaily.date)).scalar()
print(f'Última data com scores: {last_date}')
db.close()
"

# Verificar tickers disponíveis
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date, timedelta

db = SessionLocal()
recent_date = date.today() - timedelta(days=1)

tickers = db.query(ScoreDaily.ticker).filter(
    ScoreDaily.date == recent_date
).distinct().all()

print(f'Tickers em {recent_date}: {len(tickers)}')
print('Exemplos:', [t[0] for t in tickers[:5]])
db.close()
"

# Verificar benchmark
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.backtest.benchmark import BenchmarkManager
from datetime import date

db = SessionLocal()
bm = BenchmarkManager(db)
data = bm.get_benchmark_data(
    start_date=date(2026, 1, 1),
    end_date=date(2026, 3, 5)
)
print(f'Registros de benchmark: {len(data) if data else 0}')
db.close()
"
```

---

## 🔄 Rollback

```bash
# Reverter código
git log --oneline -10
git reset --hard <commit-hash-anterior>

# Restaurar banco
./deploy/restore-db.sh backups/quant_ranker_YYYY-MM-DD_HH-MM-SS.sql

# Rebuild
docker-compose down
docker-compose build
docker-compose up -d
```

---

## 📊 Análises Rápidas

```bash
# Distribuição de scores
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date, timedelta
import numpy as np

db = SessionLocal()
recent_date = date.today() - timedelta(days=1)

scores = db.query(ScoreDaily.final_score).filter(
    ScoreDaily.date == recent_date,
    ScoreDaily.final_score.isnot(None)
).all()

scores = [s[0] for s in scores]
if scores:
    print(f'Scores em {recent_date}:')
    print(f'  Count: {len(scores)}')
    print(f'  Mean: {np.mean(scores):.3f}')
    print(f'  Std: {np.std(scores):.3f}')
    print(f'  Min: {np.min(scores):.3f}')
    print(f'  Max: {np.max(scores):.3f}')
else:
    print('Sem scores disponíveis')

db.close()
"

# Top 10 ativos
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date, timedelta

db = SessionLocal()
recent_date = date.today() - timedelta(days=1)

top = db.query(ScoreDaily).filter(
    ScoreDaily.date == recent_date,
    ScoreDaily.final_score.isnot(None)
).order_by(ScoreDaily.final_score.desc()).limit(10).all()

print(f'Top 10 em {recent_date}:')
for i, s in enumerate(top, 1):
    print(f'{i}. {s.ticker}: {s.final_score:.3f}')

db.close()
"
```

---

## 🎯 Testes Rápidos

```bash
# Teste de validação
docker exec quant-ranker-backend python scripts/validate_backtest_data.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --top-n 10

# Teste de pipeline (dry run)
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.ingestion.ingestion_service import IngestionService

db = SessionLocal()
service = IngestionService(db)
print('IngestionService OK')
db.close()
"

# Teste de scoring
docker exec quant-ranker-backend python -c "
from app.scoring.scoring_engine import ScoringEngine
from app.config import settings

engine = ScoringEngine(settings)
print(f'Pesos: M={engine.momentum_weight}, Q={engine.quality_weight}, V={engine.value_weight}, R={engine.risk_weight}')
"
```

---

## 📱 Acesso Rápido

```bash
# Frontend
http://seu-ec2-ip:8501

# Páginas
http://seu-ec2-ip:8501/Ranking
http://seu-ec2-ip:8501/Research_Backtest
http://seu-ec2-ip:8501/Chat_Assistente
http://seu-ec2-ip:8501/Detalhes_do_Ativo

# SSH
ssh seu-usuario@seu-ec2-ip
cd /path/to/quant-ranker
```

---

**Última atualização:** 2026-03-05
**Versão:** 2.0
