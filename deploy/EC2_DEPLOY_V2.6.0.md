# Deploy EC2 - v2.6.0 (Adaptive History)

## Pré-requisitos

- EC2 instance com Docker e Docker Compose instalados
- Acesso SSH configurado
- Git configurado com acesso ao repositório
- Portas 8000 (API) e 8501 (Frontend) abertas no Security Group

## Procedimento de Deploy

### 1. Conectar ao EC2

```bash
ssh -i sua-chave.pem ubuntu@seu-ec2-ip
```

### 2. Navegar para o Diretório

```bash
cd quant_stock_rank
```

### 3. Backup do Banco de Dados (Recomendado)

```bash
# Criar backup
./deploy/backup-db.sh

# Verificar backup criado
ls -lh backups/
```

### 4. Pull das Mudanças

```bash
# Pull latest changes
git pull origin main

# Verificar versão
git log --oneline -5
```

### 5. Rebuild dos Containers

```bash
# Stop containers
docker-compose down

# Rebuild backend com novas mudanças
docker-compose build backend

# Start containers
docker-compose up -d

# Aguardar containers iniciarem
sleep 30
```

### 6. Verificar Health dos Containers

```bash
# Verificar status
docker ps

# Verificar logs do backend
docker logs quant-ranker-backend --tail 50

# Verificar logs do frontend
docker logs quant-ranker-frontend --tail 50
```

### 7. Executar Migration (v2.6.0)

```bash
# Executar migration para adicionar confidence factors
docker exec quant-ranker-backend python scripts/migrate_add_confidence_factors.py

# Verificar se migration foi bem-sucedida
docker exec quant-ranker-backend python -c "
from app.models.database import get_db
from sqlalchemy import text
db = next(get_db())
result = db.execute(text('SELECT column_name FROM information_schema.columns WHERE table_name = \\'features_monthly\\' AND column_name LIKE \\'%confidence%\\''))
print('Confidence columns:', [row[0] for row in result])
"
```

### 8. Executar Pipeline Completo

```bash
# Executar pipeline com 50 ativos mais líquidos
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50

# Monitorar logs em tempo real
docker logs -f quant-ranker-backend
```

### 8.1. (OPCIONAL) Limpar Dados e Rodar Pipeline FULL do Zero

Se você quiser começar do zero (deletar todos os dados e reprocessar):

```bash
# ATENÇÃO: Isto DELETA todos os dados! Faça backup antes!

# Opção 1: Usando script Python (recomendado)
docker exec -it quant-ranker-backend python scripts/clear_and_run_full.py --mode liquid --limit 50

# Opção 2: Usando script bash
docker exec -it quant-ranker-backend bash scripts/clear_and_run_full.sh liquid 50

# Opção 3: Apenas limpar dados (sem rodar pipeline)
docker exec -it quant-ranker-backend python scripts/clear_and_run_full.py --clear-only --no-confirm
```

### 9. Verificação Pós-Deploy

```bash
# Verificar API health
curl http://localhost:8000/health

# Verificar ranking (primeiros 5)
curl http://localhost:8000/api/v1/ranking | jq '.[:5]'

# Verificar scores específicos
docker exec quant-ranker-backend python scripts/check_latest_scores.py

# Verificar frontend
curl http://localhost:8501
```

### 10. (OPCIONAL) Aplicar Suavização Temporal

A suavização temporal reduz turnover do portfólio ao suavizar mudanças bruscas nos scores:

```bash
# Aplicar suavização a todas as datas com scores
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all

# Ou apenas à data de hoje
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py

# Verificar scores suavizados
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date

db = SessionLocal()
scores = db.query(ScoreDaily).filter(ScoreDaily.date == date.today()).limit(5).all()
print('Ticker | Raw Score | Smoothed Score')
print('-' * 40)
for s in scores:
    smoothed = s.final_score_smoothed if s.final_score_smoothed else s.final_score
    print(f'{s.ticker:8} | {s.final_score:9.3f} | {smoothed:14.3f}')
db.close()
"
```

**Parâmetros de suavização**:
- `--alpha 0.7`: 70% peso no score atual, 30% no anterior (padrão)
- `--alpha 0.8`: Mais reativo (80% atual, 20% anterior)
- `--alpha 0.5`: Peso igual (50% atual, 50% anterior)

### 11. Configurar Cron Jobs para Execução Automática

Configure o cron para executar o pipeline e suavização automaticamente:

```bash
# Editar crontab
crontab -e

# Adicionar as seguintes linhas:
# Pipeline diário às 19:00 (após fechamento do mercado)
0 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> /var/log/pipeline.log 2>&1

# Suavização temporal às 19:30 (30 min após pipeline)
30 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all >> /var/log/smoothing.log 2>&1
```

**Verificar cron jobs configurados**:
```bash
# Listar cron jobs
crontab -l

# Verificar logs
tail -f /var/log/pipeline.log
tail -f /var/log/smoothing.log
```

**Testar execução manual**:
```bash
# Testar pipeline
cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50

# Testar suavização (aguardar pipeline terminar)
cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all
```

### 12. Verificar Scores e Confidence Factors

```bash
# Verificar que scores não são mais NaN
docker exec quant-ranker-backend python -c "
from app.models.database import get_db
from app.models.schemas import ScoreDaily
from datetime import datetime
db = next(get_db())
scores = db.query(ScoreDaily).filter(ScoreDaily.date == datetime.now().date()).limit(10).all()
for s in scores:
    print(f'{s.ticker}: quality={s.quality_score}, value={s.value_score}, confidence={s.confidence}')
"

# Verificar confidence factors nas features
docker exec quant-ranker-backend python -c "
from app.models.database import get_db
from app.models.schemas import FeatureMonthly
from datetime import datetime
db = next(get_db())
features = db.query(FeatureMonthly).filter(FeatureMonthly.month == datetime(datetime.now().year, datetime.now().month, 1).date()).limit(5).all()
for f in features:
    print(f'{f.ticker}: overall_confidence={f.overall_confidence}, roe_mean_3y={f.roe_mean_3y}')
"
```

## Troubleshooting

### Scores ainda retornam NaN

**Diagnóstico**:
```bash
# Verificar se migration foi executada
docker exec quant-ranker-backend python -c "
from app.models.database import get_db
from sqlalchemy import text
db = next(get_db())
result = db.execute(text('SELECT column_name FROM information_schema.columns WHERE table_name = \\'features_monthly\\' AND column_name = \\'overall_confidence\\''))
print('Has overall_confidence:', result.fetchone() is not None)
"

# Verificar features calculadas
docker exec quant-ranker-backend python scripts/check_latest_scores.py
```

**Solução**:
1. Executar migration novamente
2. Executar pipeline completo
3. Verificar logs para erros

### Containers não iniciam

**Diagnóstico**:
```bash
# Verificar logs
docker logs quant-ranker-backend
docker logs quant-ranker-db

# Verificar espaço em disco
df -h

# Verificar memória
free -h
```

**Solução**:
1. Limpar containers antigos: `docker system prune -a`
2. Verificar configuração do Docker Compose
3. Reiniciar Docker: `sudo systemctl restart docker`

### API retorna 500 errors

**Diagnóstico**:
```bash
# Verificar logs da API
docker logs quant-ranker-backend --tail 100

# Testar endpoint específico
curl -v http://localhost:8000/api/v1/ranking
```

**Solução**:
1. Verificar se banco de dados está acessível
2. Verificar se pipeline foi executado
3. Verificar logs para stack traces

### Pipeline falha

**Diagnóstico**:
```bash
# Executar pipeline com logs detalhados
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 10

# Verificar dados fundamentais
docker exec quant-ranker-backend python scripts/check_data_dates.py
```

**Solução**:
1. Verificar conectividade com Yahoo Finance
2. Verificar espaço em disco
3. Executar pipeline incremental primeiro

## Rollback (Se Necessário)

### 1. Restaurar Backup do Banco

```bash
# Listar backups disponíveis
ls -lh backups/

# Restaurar backup específico
./deploy/restore-db.sh backups/backup_YYYYMMDD_HHMMSS.sql
```

### 2. Reverter para Versão Anterior

```bash
# Checkout versão anterior
git checkout v2.5.2

# Rebuild containers
docker-compose down
docker-compose build backend
docker-compose up -d

# Executar pipeline
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50
```

## Monitoramento Pós-Deploy

### Logs em Tempo Real

```bash
# Backend
docker logs -f quant-ranker-backend

# Frontend
docker logs -f quant-ranker-frontend

# Database
docker logs -f quant-ranker-db
```

### Métricas de Performance

```bash
# Uso de recursos
docker stats

# Espaço em disco
df -h

# Memória
free -h
```

### Verificação Diária

```bash
# Executar pipeline diário
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50

# Verificar scores
curl http://localhost:8000/api/v1/ranking | jq '.[:10]'

# Verificar logs para erros
docker logs quant-ranker-backend --since 24h | grep ERROR
```

## Checklist de Deploy

- [ ] Backup do banco de dados criado
- [ ] Git pull executado com sucesso
- [ ] Containers rebuilded
- [ ] Migration executada
- [ ] Pipeline executado com sucesso
- [ ] API health check passou
- [ ] Ranking retorna dados válidos
- [ ] Scores não são NaN
- [ ] Confidence factors estão sendo calculados
- [ ] Frontend acessível
- [ ] Logs não mostram erros críticos

## Contatos de Suporte

- Documentação: `docs/INDEX.md`
- Troubleshooting: `ADAPTIVE_HISTORY_IMPLEMENTATION.md`
- Issues: GitHub Issues

## Notas da Versão v2.6.0

### Principais Mudanças

1. **Histórico Adaptativo**: Sistema agora usa 1-3 anos de dados em vez de exigir exatamente 3 anos
2. **Confidence Factors**: Novos campos para rastrear qualidade dos dados
3. **Scores Melhorados**: Menos NaN, mais ativos elegíveis
4. **Instituições Financeiras**: Agora calculam scores corretamente

### Impacto Esperado

- Taxa de elegibilidade: 60-70% → 80-90%
- Scores NaN: ~40% → ~5%
- Ativos com dados limitados: Agora têm scores com confidence reduzido

### Breaking Changes

- Schema do banco de dados modificado (migration necessária)
- Confidence factor aplicado ao quality_score
- Pipeline passa novos campos para scoring engine
