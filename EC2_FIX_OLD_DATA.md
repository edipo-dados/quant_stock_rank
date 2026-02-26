# Fix: Dados Antigos Após Pipeline Full no EC2

## Problema

Após executar o pipeline full no EC2, o frontend ainda mostra dados antigos.

## Causa

O pipeline pode estar rodando em modo INCREMENTAL em vez de FULL, ou os scores antigos não estão sendo substituídos.

## Diagnóstico

### 1. Verificar Datas dos Dados

```bash
docker exec quant-ranker-backend python scripts/check_data_dates.py
```

Isso mostrará:
- Data mais recente de preços
- Data mais recente de fundamentos
- Data mais recente de scores
- Quantos scores existem para hoje

### 2. Verificar Logs do Pipeline

```bash
docker logs quant-ranker-backend --tail 100 | grep -E "MODO|FULL|INCREMENTAL"
```

Procure por:
- `Modo detectado: FULL` ou `Modo detectado: INCREMENTAL`
- `Buscando 400 dias de histórico` (FULL)
- `Buscando 5 dias de histórico` (INCREMENTAL)

## Solução

### Opção 1: Limpar Scores Antigos e Reexecutar

```bash
# 1. Limpar scores antigos (mantém últimos 7 dias)
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date, timedelta

db = SessionLocal()
cutoff = date.today() - timedelta(days=7)
deleted = db.query(ScoreDaily).filter(ScoreDaily.date < cutoff).delete()
db.commit()
print(f'✅ Scores antigos removidos: {deleted}')
db.close()
"

# 2. Executar pipeline FULL
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full

# 3. Verificar dados
docker exec quant-ranker-backend python scripts/check_data_dates.py

# 4. Reiniciar containers
docker-compose restart backend frontend
```

### Opção 2: Usar Script Automatizado

```bash
# Tornar executável
chmod +x scripts/ec2_fix_old_data.sh

# Executar
./scripts/ec2_fix_old_data.sh
```

### Opção 3: Limpar Tudo e Recomeçar

```bash
# 1. Parar containers
docker-compose down

# 2. Remover volume do banco (CUIDADO: apaga tudo!)
docker volume rm quant_stock_rank_postgres_data

# 3. Subir containers
docker-compose up -d

# 4. Aguardar inicialização
sleep 10

# 5. Inicializar banco
docker exec quant-ranker-backend python scripts/init_db.py

# 6. Executar pipeline FULL
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full
```

## Verificação

### 1. Verificar Data dos Scores

```bash
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date

db = SessionLocal()
today = date.today()
scores = db.query(ScoreDaily).filter(ScoreDaily.date == today).count()
print(f'Scores de hoje ({today}): {scores}')
db.close()
"
```

Deve mostrar > 0 scores para hoje.

### 2. Testar API

```bash
curl http://localhost:8000/api/v1/ranking | jq '.date'
```

Deve mostrar a data de hoje.

### 3. Verificar Frontend

Acesse `http://SEU_IP:8501` e verifique:
- Data do ranking deve ser hoje
- Scores devem estar atualizados

## Prevenção

### 1. Sempre Usar --force-full

Quando quiser garantir dados frescos:

```bash
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full
```

### 2. Configurar Cron Job Corretamente

```bash
crontab -e
```

Adicionar:
```bash
# Executar pipeline FULL todo dia às 19h
0 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full >> /var/log/pipeline.log 2>&1
```

### 3. Monitorar Logs

```bash
# Ver últimas execuções
tail -f /var/log/pipeline.log

# Verificar modo usado
grep "Modo detectado" /var/log/pipeline.log | tail -5
```

## Entendendo FULL vs INCREMENTAL

### Modo INCREMENTAL (Padrão)
- Busca apenas últimos 5 dias de preços
- Mais rápido (~5 minutos)
- Usado quando já há dados recentes no banco
- **Problema**: Pode não atualizar se dados estão desatualizados

### Modo FULL (--force-full)
- Busca 400 dias de histórico
- Mais lento (~20 minutos)
- Sempre busca dados frescos
- **Recomendado**: Para primeira execução ou quando dados estão antigos

### Como o Pipeline Decide

```python
# Verifica última data de preços no banco
latest_price_date = db.query(max(RawPriceDaily.date)).scalar()

# Se última data é recente (< 5 dias), usa INCREMENTAL
if latest_price_date and (today - latest_price_date).days < 5:
    mode = "INCREMENTAL"
else:
    mode = "FULL"

# --force-full sempre força FULL
if args.force_full:
    mode = "FULL"
```

## Troubleshooting Adicional

### Pipeline Roda Mas Não Gera Scores

**Sintomas:**
- Pipeline completa sem erros
- Preços e fundamentos são atualizados
- Mas scores não são gerados

**Causa:** Erro no cálculo de scores (NaN, divisão por zero, etc.)

**Solução:**
```bash
# Ver logs de erro
docker logs quant-ranker-backend | grep -A 10 "ERROR"

# Verificar elegibilidade
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date

db = SessionLocal()
scores = db.query(ScoreDaily).filter(
    ScoreDaily.date == date.today(),
    ScoreDaily.passed_eligibility == True
).count()
print(f'Ativos elegíveis hoje: {scores}')
db.close()
"
```

### Frontend Mostra Data Antiga

**Sintomas:**
- API retorna data correta
- Frontend mostra data antiga

**Causa:** Cache do Streamlit

**Solução:**
```bash
# Limpar cache e reiniciar
docker-compose restart frontend

# Ou forçar rebuild
docker-compose up -d --build frontend
```

### API Retorna 404

**Sintomas:**
- `curl http://localhost:8000/api/v1/ranking` retorna 404

**Causa:** Nenhum score no banco

**Solução:**
```bash
# Verificar se há scores
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily

db = SessionLocal()
count = db.query(ScoreDaily).count()
print(f'Total de scores no banco: {count}')
db.close()
"

# Se 0, executar pipeline
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full
```

## Comandos Úteis

```bash
# Verificar última execução do pipeline
docker logs quant-ranker-backend --tail 200 | grep "RESUMO DO PIPELINE" -A 20

# Verificar scores de hoje
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date

db = SessionLocal()
scores = db.query(ScoreDaily).filter(ScoreDaily.date == date.today()).all()
for s in scores[:5]:
    print(f'{s.ticker}: {s.final_score:.3f}')
db.close()
"

# Limpar cache do Docker
docker system prune -f

# Reiniciar tudo
docker-compose restart
```

## Resumo

1. **Sempre use --force-full** quando quiser dados frescos
2. **Verifique as datas** com `check_data_dates.py`
3. **Limpe scores antigos** se necessário
4. **Monitore os logs** para ver se pipeline está em FULL ou INCREMENTAL
5. **Reinicie containers** após atualizar dados

---

**Última atualização:** 26/02/2026 - v2.5.2
