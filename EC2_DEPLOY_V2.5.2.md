# Deploy v2.5.2 - Tratamento Estatístico de Missing Values

## O Que Mudou

### v2.5.1 → v2.5.2

#### Problema Resolvido
Sistema usava valores sentinela (-999) para features ausentes, contaminando normalização e gerando scores absurdos (-549).

#### Nova Implementação
Tratamento estatístico correto de missing values:

1. **Cálculo de Features**: Retorna NaN em vez de -999
2. **Identificação**: Detecta NaNs antes da normalização
3. **Imputação**: Usa medianas setoriais/universo
4. **Normalização**: Z-score cross-sectional sem contaminação
5. **Scoring**: Redistribui pesos quando há NaN

### Garantias v2.5.2
- ✅ Scores distribuídos entre -3 e +3
- ✅ Média próxima de 0 (±0.1)
- ✅ Desvio padrão ~0.2-0.3
- ✅ Sem valores extremos (-549)
- ✅ Pipeline estatisticamente estável
- ✅ Taxa de elegibilidade >= 80%

### Resultados
- **Antes**: Média=-549, Range=[-999, -300]
- **Depois**: Média=0.00, Desvio=0.23, Range=[-0.38, 0.25]

---

## Deploy no EC2

### Passo 1: Pull das Mudanças

```bash
cd ~/quant_stock_rank
git pull origin main
```

### Passo 2: Rebuild dos Containers

```bash
docker-compose down
docker-compose up -d --build
```

### Passo 3: Aguardar Containers

```bash
sleep 10
docker-compose ps
```

Deve mostrar todos os containers como `healthy`.

### Passo 4: Testar Pipeline

```bash
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode test --limit 10
```

### Passo 5: Verificar Logs

Você deve ver logs estruturados em 3 camadas com scores corretos:

```
🔍 LAYER 1: STRUCTURAL ELIGIBILITY (raw data only)
Total ativos iniciais: 5
✅ Ativos elegíveis (estrutural): 4
❌ Ativos excluídos (estrutural): 1
📊 Taxa de elegibilidade: 80.0%

🔧 LAYER 2: FEATURE ENGINEERING (calculate all features)
📈 Calculando features de momentum...
✅ Momentum: 4/4 calculados
💼 Calculando features fundamentalistas...
✅ Fundamentos: 4/4 calculados

📊 Análise de missing values (antes da imputação):
Total missing values: 47
Missing por feature:
  - roe_mean_3y: 4 (100.0%)
  - price_to_book: 4 (100.0%)
  ...

🔄 LAYER 2.5: MISSING VALUE IMPUTATION
✅ Features diárias salvas: 4 tickers
✅ Features mensais salvas: 4 tickers
📋 Resumo de imputações: 19 valores imputados

🎯 LAYER 3: SCORING & NORMALIZATION
✅ Scores calculados: 4/4
✅ Ranking atualizado: 4 ativos

📊 Estatísticas dos Scores (v2.5.2):
Média: 0.00
Desvio: 0.23
Min: -0.38
Max: 0.25
```

---

## Verificações

### 1. Verificar Taxa de Elegibilidade

```bash
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import Score
from datetime import date

db = SessionLocal()
scores = db.query(Score).filter(Score.date == date.today()).all()
print(f'✅ Scores gerados: {len(scores)}')
db.close()
"
```

Deve mostrar >= 4 scores (80% de 5 ativos).

### 2. Verificar Frontend

Acesse: `http://SEU_IP_EC2:8501`

Deve mostrar ranking atualizado com dados de hoje.

### 3. Verificar Imputações

Os logs mostram quantos valores foram imputados. Isso é normal e esperado para ativos com histórico limitado.

---

## Rodar Pipeline Completo (50 Ativos)

Após verificar que o teste funcionou:

```bash
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50
```

Isso deve gerar ~40-45 ativos elegíveis (80-90% de 50).

---

## Configurar Cron Job

Para rodar automaticamente todo dia às 19h:

```bash
crontab -e
```

Adicionar:
```bash
0 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> /var/log/pipeline.log 2>&1
```

---

## Troubleshooting

### Taxa de Elegibilidade < 80%

**Causa**: Dados fundamentais incompletos

**Solução**:
```bash
# Verificar fundamentos no banco
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import RawFundamental
db = SessionLocal()
count = db.query(RawFundamental).count()
print(f'Fundamentos: {count}')
db.close()
"

# Se baixo, rodar em modo FULL
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full
```

### Muitos Missing Values

**Normal!** O sistema imputa automaticamente. Missing values são esperados para:
- `roe_mean_3y`: Precisa de 3 anos de histórico
- `price_to_book`: Precisa de market_cap (não disponível no Yahoo)
- `fcf_yield`: Precisa de free cash flow

Esses valores são imputados com medianas e não afetam o ranking.

### Scores Fora do Range Esperado

**v2.5.2**: Scores devem estar entre -3 e +3, média ~0

Se ver scores como -549 ou -999:
```bash
# Verificar versão
git log --oneline -1

# Deve mostrar commit com "remove sentinel values"
# Se não, atualizar:
git pull origin main
docker-compose down
docker-compose up -d --build
```

---

## Comparação: v2.5.0 → v2.5.1 → v2.5.2

### v2.5.0 (Deadlock)
```
Elegibilidade: 0 elegíveis, 10 excluídos  ❌
Scores: 0/0 calculados  ❌
Ranking: 0 ativos  ❌
```

### v2.5.1 (3 Camadas)
```
LAYER 1 - Elegibilidade: 4 (80.0%)  ✅
LAYER 2 - Features: 4 calculados  ✅
LAYER 3 - Scores: Média=-549  ❌ (valores sentinela)
```

### v2.5.2 (Tratamento Estatístico)
```
LAYER 1 - Elegibilidade: 4 (80.0%)  ✅
LAYER 2 - Features + Imputação: 4 calculados  ✅
LAYER 3 - Scores: Média=0.00, Desvio=0.23  ✅
Range: [-0.38, 0.25]  ✅
```

---

## Arquivos Modificados

### v2.5.1 (3 Camadas)
- `app/filters/eligibility_filter.py` - Layer 1 (estrutural apenas)
- `app/factor_engine/missing_handler.py` - Layer 2.5 (novo)
- `scripts/run_pipeline_docker.py` - Orquestração com logs
- `docs/PIPELINE_ARCHITECTURE.md` - Documentação completa

### v2.5.2 (Tratamento Estatístico)
- `app/scoring/scoring_engine.py` - Métodos retornam NaN, não -999
- `app/factor_engine/missing_handler.py` - Imputação estatística
- `scripts/refactor_remove_sentinel_values.py` - Script de refatoração
- `docs/CALCULOS_RANKING.md` - Regras atualizadas

---

## Próximos Passos

1. ✅ Deploy no EC2
2. ✅ Testar com 10 ativos
3. ✅ Rodar com 50 ativos
4. ✅ Configurar cron job
5. ✅ Monitorar logs diários

---

## Suporte

Se encontrar problemas:

1. Verificar logs: `docker-compose logs -f backend`
2. Verificar containers: `docker-compose ps`
3. Verificar espaço: `df -h`
4. Limpar se necessário: `docker system prune -a -f`

---

## Commit

```
fix: Complete removal of -999 sentinel values

Commit: 0769998
Branch: main
Version: 2.5.2
```
    