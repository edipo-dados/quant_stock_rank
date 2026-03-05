# Checklist de Deploy - Modelo Multifator v2.0

## Data: 2026-03-05

---

## ✅ Pré-Deploy (Local)

- [ ] Todos os arquivos commitados
- [ ] Testes locais passaram (se aplicável)
- [ ] Documentação atualizada
- [ ] Changelog atualizado

```bash
# Verificar status
git status

# Commit
git add .
git commit -m "feat: implement multifactor model v2.0 (Sprint 1-4)

- Add return_3m, volatility_1y, max_drawdown_1y factors
- Add ROIC quality factor
- Add minimum_market_cap filter (1B BRL)
- Implement risk_score (low volatility premium)
- Update weights: momentum 0.4, quality 0.2, value 0.3, risk 0.1
- Add drawdown chart, annual returns table, turnover chart
- Add BacktestDataValidator with automatic validation
- Add validate_backtest_data.py script"

# Push
git push origin main
```

---

## ✅ Deploy no EC2

### 1. Conectar ao EC2

```bash
ssh seu-usuario@seu-ec2-ip
cd /path/to/quant-ranker
```

### 2. Backup do Banco de Dados

```bash
# IMPORTANTE: Sempre fazer backup antes de deploy
./deploy/backup-db.sh

# Verificar backup criado
ls -lh backups/
```

### 3. Pull das Mudanças

```bash
git pull origin main

# Verificar se pull foi bem sucedido
git log --oneline -5
```

### 4. Rebuild dos Containers

```bash
# Parar containers
docker-compose down

# Rebuild (pode demorar alguns minutos)
docker-compose build backend frontend

# Subir containers
docker-compose up -d

# Verificar se subiram
docker ps
```

### 5. Verificar Logs

```bash
# Backend
docker logs quant-ranker-backend --tail 50

# Deve mostrar:
# "ScoringEngine initialized with weights: momentum=0.4, quality=0.2, value=0.3, risk=0.1, size=0.0"

# Frontend
docker logs quant-ranker-frontend --tail 50
```

---

## ✅ Testes Pós-Deploy

### 1. Verificar Configuração

```bash
# Verificar pesos do modelo
docker exec quant-ranker-backend python -c "
from app.config import settings
print(f'Momentum: {settings.momentum_weight}')
print(f'Quality: {settings.quality_weight}')
print(f'Value: {settings.value_weight}')
print(f'Risk: {settings.risk_weight}')
print(f'Market Cap Min: {settings.minimum_market_cap}')
"

# Saída esperada:
# Momentum: 0.4
# Quality: 0.2
# Value: 0.3
# Risk: 0.1
# Market Cap Min: 1000000000.0
```

### 2. Validar Dados

```bash
docker exec quant-ranker-backend python scripts/validate_backtest_data.py \
  --start-date 2021-01-01 \
  --end-date 2026-03-05 \
  --top-n 10

# Deve mostrar: Status: ✅ VÁLIDO
```

### 3. Rodar Pipeline

```bash
# Rodar pipeline para recalcular scores com novo modelo
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py

# Verificar logs
docker logs quant-ranker-backend --tail 100
```

### 4. Verificar Novos Fatores

```bash
# Verificar se novos fatores estão sendo calculados
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date, timedelta

db = SessionLocal()
recent_date = date.today() - timedelta(days=1)

score = db.query(ScoreDaily).filter(
    ScoreDaily.date == recent_date
).first()

if score:
    print(f'Ticker: {score.ticker}')
    print(f'Date: {score.date}')
    print(f'Final Score: {score.final_score}')
    print(f'Momentum Score: {score.momentum_score}')
    print(f'Quality Score: {score.quality_score}')
    print(f'Value Score: {score.value_score}')
else:
    print('Sem scores recentes')

db.close()
"
```

### 5. Testar Frontend

```bash
# Verificar se frontend está acessível
curl -I http://localhost:8501

# Deve retornar: HTTP/1.1 200 OK
```

Acessar no navegador: `http://seu-ec2-ip:8501`

- [ ] Página inicial carrega
- [ ] Página "Ranking" carrega
- [ ] Página "Research Backtest" carrega
- [ ] Consegue configurar backtest
- [ ] Consegue executar backtest
- [ ] Gráficos aparecem corretamente
- [ ] Novos gráficos (drawdown, retornos anuais, turnover) aparecem

### 6. Executar Backtest de Teste

Via frontend:
1. Ir para "🔬 Research Backtest"
2. Configurar:
   - Nome: "Teste Deploy v2.0"
   - Data Inicial: 2024-01-01
   - Data Final: 2026-03-05
   - Top N: 10
3. Executar
4. Verificar:
   - [ ] Backtest completa sem erros
   - [ ] Métricas aparecem
   - [ ] Equity curve aparece
   - [ ] Gráfico de drawdown aparece
   - [ ] Tabela de retornos anuais aparece
   - [ ] Gráfico de turnover aparece
   - [ ] Tabela de posições aparece

---

## ✅ Monitoramento Pós-Deploy

### Primeiras 24 horas

```bash
# Verificar logs a cada 2-4 horas
docker logs quant-ranker-backend --tail 100 --follow

# Verificar uso de recursos
docker stats

# Verificar espaço em disco
df -h
```

### Primeira semana

- [ ] Pipeline diário rodando sem erros
- [ ] Scores sendo calculados corretamente
- [ ] Frontend acessível e responsivo
- [ ] Sem erros críticos nos logs
- [ ] Backups automáticos funcionando

---

## ✅ Rollback (Se Necessário)

Se algo der errado:

### 1. Restaurar Banco de Dados

```bash
# Listar backups
ls -lh backups/

# Restaurar último backup
./deploy/restore-db.sh backups/quant_ranker_YYYY-MM-DD_HH-MM-SS.sql
```

### 2. Reverter Código

```bash
# Ver commits recentes
git log --oneline -10

# Reverter para commit anterior
git revert HEAD
# ou
git reset --hard <commit-hash-anterior>

# Rebuild
docker-compose down
docker-compose build
docker-compose up -d
```

---

## ✅ Comunicação

### Notificar Stakeholders

- [ ] Deploy concluído com sucesso
- [ ] Novas funcionalidades disponíveis:
  - Modelo multifator robusto (4 categorias)
  - Novos fatores (return_3m, ROIC, volatility_1y, max_drawdown_1y)
  - Filtro de market cap mínimo (1 bilhão)
  - Gráfico de drawdown
  - Tabela de retornos anuais
  - Gráfico de turnover
  - Validação automática de dados
- [ ] Documentação atualizada:
  - `MULTIFACTOR_IMPLEMENTATION_SUMMARY.md`
  - `MULTIFACTOR_USER_GUIDE.md`
  - `docs/MULTIFACTOR_MODEL_PLAN.md`

---

## ✅ Próximos Passos

### Curto Prazo (1-2 semanas)
- [ ] Monitorar performance do novo modelo
- [ ] Coletar feedback dos usuários
- [ ] Ajustar pesos se necessário
- [ ] Documentar casos de uso

### Médio Prazo (1 mês)
- [ ] Analisar backtests de longo prazo (3-5 anos)
- [ ] Comparar com modelo anterior
- [ ] Otimizar performance se necessário
- [ ] Adicionar mais visualizações se solicitado

### Longo Prazo (3+ meses)
- [ ] Implementar walk-forward validation
- [ ] Adicionar mais fatores (se necessário)
- [ ] Implementar machine learning (opcional)
- [ ] Expandir para outros mercados (opcional)

---

## 📝 Notas

### Mudanças Principais

1. **Fatores Novos:**
   - return_3m (momentum)
   - ROIC (quality)
   - volatility_1y (risk)
   - max_drawdown_1y (risk)

2. **Pesos Atualizados:**
   - Momentum: 0.35 → 0.4
   - Quality: 0.25 → 0.2
   - Value: 0.3 (mantido)
   - Risk: 0.0 → 0.1 (novo)

3. **Filtros:**
   - Market cap mínimo: 1 bilhão BRL (novo)

4. **Visualizações:**
   - Gráfico de drawdown
   - Tabela de retornos anuais
   - Gráfico de turnover

5. **Validações:**
   - Validação automática antes de backtest
   - Script standalone de validação
   - Logs estruturados

### Arquivos Modificados

- `app/config.py`
- `app/filters/eligibility_filter.py`
- `app/factor_engine/momentum_factors.py`
- `app/factor_engine/fundamental_factors.py`
- `app/scoring/scoring_engine.py`
- `frontend/pages/4_🔬_Research_Backtest.py`
- `app/backtest/backtest_engine.py`

### Arquivos Criados

- `app/backtest/validator.py`
- `scripts/validate_backtest_data.py`
- `MULTIFACTOR_IMPLEMENTATION_SUMMARY.md`
- `MULTIFACTOR_USER_GUIDE.md`
- `DEPLOY_CHECKLIST_V2.md`

---

## ✅ Assinaturas

- [ ] Deploy executado por: _______________
- [ ] Data/Hora: _______________
- [ ] Testes validados por: _______________
- [ ] Aprovado por: _______________

---

**Versão:** 2.0 (Modelo Multifator Robusto)
**Data:** 2026-03-05
