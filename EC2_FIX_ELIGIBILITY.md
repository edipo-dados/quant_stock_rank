# Fix: Correção do Filtro de Elegibilidade

## Problema Identificado

O pipeline estava gerando **0 ativos elegíveis** devido a um deadlock no filtro de elegibilidade:

1. O filtro verificava se fatores críticos (momentum_6m_ex_1m, roe_mean_3y, etc.) já existiam
2. Mas esses fatores são calculados DEPOIS do filtro passar
3. Resultado: Todos os ativos eram excluídos por "missing_critical_factor"

## Solução Implementada

### 1. Filtro de Elegibilidade (`app/filters/eligibility_filter.py`)

Removidas as verificações de fatores calculados. O filtro agora verifica apenas:
- ✅ shareholders_equity > 0
- ✅ ebitda > 0 (exceto instituições financeiras)
- ✅ revenue > 0
- ✅ net_income >= 0 (último ano)
- ✅ net_income positivo em 2+ dos últimos 3 anos
- ✅ net_debt_to_ebitda <= 8
- ✅ volume médio >= minimum_volume

### 2. Pipeline (`scripts/run_pipeline_docker.py`)

Atualizado para usar fatores acadêmicos de momentum:
```python
# ANTES (errado)
momentum_factors = {
    'return_6m': daily_features.return_6m,
    'return_12m': daily_features.return_12m,
    'rsi_14': daily_features.rsi_14,
    ...
}

# DEPOIS (correto)
momentum_factors = {
    'momentum_6m_ex_1m': daily_features.momentum_6m_ex_1m,
    'momentum_12m_ex_1m': daily_features.momentum_12m_ex_1m,
    'volatility_90d': daily_features.volatility_90d,
    'recent_drawdown': daily_features.recent_drawdown
}
```

## Deploy no EC2

### Opção 1: Script Automatizado

```bash
# No EC2
cd ~/quant_stock_rank
bash scripts/deploy_ec2_fix.sh
```

### Opção 2: Manual

```bash
# 1. Pull das mudanças
cd ~/quant_stock_rank
git pull origin main

# 2. Rebuild dos containers
docker-compose down
docker-compose up -d --build

# 3. Aguardar containers ficarem healthy
sleep 10
docker-compose ps

# 4. Testar pipeline
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode test --limit 10
```

## Verificação

### 1. Verificar Logs do Pipeline

```bash
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode test --limit 10
```

Deve mostrar:
```
Elegibilidade: 4 elegíveis, 1 excluídos  # ✅ Não mais 0 elegíveis!
Momentum: 4/4 calculados
Fundamentos: 4/4 calculados
Scores: 4/4 calculados
Ranking: 4 ativos
```

### 2. Verificar Scores no Banco

```bash
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import Score
from datetime import date

db = SessionLocal()
scores = db.query(Score).filter(Score.date == date.today()).all()
print(f'Scores gerados: {len(scores)}')
for s in scores[:5]:
    print(f'{s.ticker}: final={s.final_score:.2f}, momentum={s.momentum_score:.2f}')
db.close()
"
```

### 3. Verificar Frontend

Acesse: `http://SEU_IP_EC2:8501`

Deve mostrar ranking com dados de hoje.

## Resultados Esperados

### Antes da Correção
- ❌ Elegíveis: 0
- ❌ Scores: 0
- ❌ Ranking vazio
- ❌ Frontend mostra apenas dados antigos

### Depois da Correção
- ✅ Elegíveis: 4-5 (dependendo dos dados)
- ✅ Scores: 4-5 ativos
- ✅ Ranking atualizado
- ✅ Frontend mostra dados de hoje

## Próximos Passos

### 1. Rodar Pipeline Completo (50 ativos)

```bash
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50
```

### 2. Configurar Cron Job

```bash
# Editar crontab
crontab -e

# Adicionar (rodar todo dia às 19h)
0 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> /var/log/pipeline.log 2>&1
```

### 3. Monitorar Logs

```bash
# Logs do backend
docker-compose logs -f backend

# Logs do pipeline
tail -f /var/log/pipeline.log
```

## Troubleshooting

### Problema: Ainda mostra 0 elegíveis

```bash
# Verificar se fundamentos existem
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import RawFundamental

db = SessionLocal()
count = db.query(RawFundamental).count()
print(f'Fundamentos no banco: {count}')
db.close()
"

# Se 0, rodar pipeline em modo FULL
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode test --limit 10 --force-full
```

### Problema: Scores muito baixos (-549)

Isso é normal! Significa que alguns fatores ainda estão faltando:
- roe_mean_3y: Precisa de 3 anos de histórico
- price_to_book: Precisa de market_cap (não disponível no Yahoo Finance)

Esses fatores serão preenchidos conforme mais dados forem coletados.

### Problema: Containers não sobem

```bash
# Verificar espaço em disco
df -h

# Se pouco espaço, limpar
docker system prune -a -f
```

## Commit

```
fix: Remove critical factor checks from eligibility filter and use academic momentum factors in scoring

- Remove deadlock where eligibility filter checked for calculated factors before they were computed
- Update pipeline to use momentum_6m_ex_1m and momentum_12m_ex_1m instead of return_6m/return_12m
- Eligibility filter now only checks raw fundamental data (equity, ebitda, revenue, volume, leverage)
- Calculated factors (momentum, quality, value) are computed AFTER eligibility filtering
- Fixes issue where 0 assets were passing eligibility due to missing factors

Commit: 352408e
```
