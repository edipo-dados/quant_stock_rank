# Pipeline Architecture v2.5.1

## Problema Resolvido

O pipeline anterior tinha um **deadlock lógico**:
- Filtro de elegibilidade verificava fatores derivados (ev_ebitda, momentum_ex_1m, etc.)
- Mas esses fatores só eram calculados DEPOIS do filtro passar
- Resultado: 100% dos ativos eram excluídos

## Nova Arquitetura: 3 Camadas

### LAYER 1: Structural Eligibility 🔍

**Responsabilidade**: Validar dados brutos e saúde financeira estrutural

**Usa APENAS**:
- Dados fundamentais brutos (equity, ebitda, revenue)
- Histórico de preços (volume, disponibilidade)
- Métricas de distress estrutural (leverage, lucros persistentes)

**NÃO usa**:
- Fatores derivados (ev_ebitda, fcf_yield)
- Fatores calculados (momentum_ex_1m, roe_mean_3y)
- Scores normalizados

**Critérios de Exclusão**:
```python
# ❌ Excluir se:
- shareholders_equity <= 0  # Patrimônio negativo
- ebitda <= 0  # Sem geração operacional (exceto bancos)
- revenue <= 0  # Sem atividade
- volume < minimum_volume  # Ilíquido
- net_income < 0 (último ano)  # Prejuízo atual
- net_income < 0 em 2 dos últimos 3 anos  # Prejuízo persistente
- net_debt_to_ebitda > 8  # Alavancagem excessiva
```

**Arquivo**: `app/filters/eligibility_filter.py`

**Meta**: >= 80% dos ativos devem passar

---

### LAYER 2: Feature Engineering 🔧

**Responsabilidade**: Calcular TODAS as features para TODOS os elegíveis

**Processo**:
1. Calcular features de momentum (momentum_6m_ex_1m, volatility, etc.)
2. Calcular features fundamentalistas (roe, pe_ratio, ev_ebitda, etc.)
3. **NUNCA excluir ativo por feature faltante**
4. Impute missing values usando:
   - Mediana setorial (se setor >= 5 ativos)
   - Mediana universal (fallback)

**Arquivos**:
- `app/factor_engine/momentum_factors.py`
- `app/factor_engine/fundamental_factors.py`
- `app/factor_engine/missing_handler.py` (novo)

**Garantia**: Nenhum ativo é excluído nesta camada

---

### LAYER 3: Scoring & Normalization 🎯

**Responsabilidade**: Normalizar, aplicar pesos e ranquear

**Processo**:
1. Normalização cross-sectional (z-score)
2. Winsorização ±3σ
3. Aplicar pesos configuráveis:
   - Momentum: 35%
   - Quality: 25%
   - Value: 30%
   - Size: 10%
4. Aplicar penalidades de risco
5. Calcular ranking final

**Arquivos**:
- `app/factor_engine/normalizer.py`
- `app/scoring/scoring_engine.py`
- `app/scoring/score_service.py`

---

## Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────┐
│ INPUT: Tickers (ex: 50 ativos)                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: STRUCTURAL ELIGIBILITY                             │
│ • Valida dados brutos                                       │
│ • Exclui ativos estruturalmente inviáveis                   │
│ • Meta: >= 80% passam                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    40-45 elegíveis
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: FEATURE ENGINEERING                                │
│ • Calcula TODAS as features                                 │
│ • Imputa missing values (mediana setorial/universal)        │
│ • NUNCA exclui ativos                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    40-45 com features
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: SCORING & NORMALIZATION                            │
│ • Normaliza cross-sectional                                 │
│ • Aplica pesos e penalidades                                │
│ • Gera ranking final                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    OUTPUT: Ranking
```

---

## Logs Detalhados

O pipeline agora gera logs estruturados em cada camada:

### LAYER 1 Logs
```
🔍 LAYER 1: STRUCTURAL ELIGIBILITY (raw data only)
Total ativos iniciais: 50
✅ Ativos elegíveis (estrutural): 42
❌ Ativos excluídos (estrutural): 8
📊 Taxa de elegibilidade: 84.0%

Razões de exclusão estrutural:
  MGLU3.SA: negative_net_income_2_of_3_years
  COGN3.SA: low_volume
  ...
```

### LAYER 2 Logs
```
🔧 LAYER 2: FEATURE ENGINEERING (calculate all features)
Calculando features para 42 ativos elegíveis...

📈 Calculando features de momentum...
✅ Momentum: 42/42 calculados

💼 Calculando features fundamentalistas...
✅ Fundamentos: 42/42 calculados

📊 Análise de missing values (antes da imputação):
Total missing values: 87
Missing por feature:
  - roe_mean_3y: 15 (35.7%)
  - price_to_book: 8 (19.0%)
  - fcf_yield: 12 (28.6%)

🔄 LAYER 2.5: MISSING VALUE IMPUTATION
Imputando valores faltantes usando medianas setoriais/universais...
✅ Features diárias salvas: 42 tickers
✅ Features mensais salvas: 42 tickers

📋 Resumo de imputações: 87 valores imputados
  - sector_median: 52 imputações
  - universe_median: 35 imputações
```

### LAYER 3 Logs
```
🎯 LAYER 3: SCORING & NORMALIZATION
Calculando scores finais...
✅ Scores calculados: 42/42

📊 Atualizando ranking...
✅ Ranking atualizado: 42 ativos
```

### Pipeline Summary
```
📊 RESUMO DO PIPELINE
================================================================================
LAYER 1 - Elegibilidade Estrutural:
  • Ativos iniciais: 50
  • Ativos elegíveis: 42 (84.0%)
  • Ativos excluídos: 8

LAYER 2 - Feature Engineering:
  • Momentum calculado: 42
  • Fundamentos calculados: 42
  • Valores imputados: 87

LAYER 3 - Scoring:
  • Scores calculados: 42
  • Ranking final: 42 ativos
================================================================================
```

---

## Garantias

### ✅ Determinismo
- Pipeline sempre produz mesmo resultado para mesmos inputs
- Sem exclusões aleatórias por missing values

### ✅ Sem Deadlock
- Filtro estrutural não depende de features calculadas
- Features são calculadas para todos os elegíveis
- Missing values são imputados, não excluídos

### ✅ Transparência
- Logs detalhados em cada camada
- Rastreamento de todas as imputações
- Métricas de qualidade (taxa de elegibilidade, missing values)

### ✅ Robustez Institucional
- >= 80% dos ativos devem passar Layer 1
- Nenhum ativo excluído por missing features
- Imputação baseada em medianas (robusta a outliers)

---

## Uso

### Rodar Pipeline Completo
```bash
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50
```

### Rodar Pipeline de Teste
```bash
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode test --limit 10
```

### Verificar Logs
```bash
docker-compose logs -f backend
```

---

## Troubleshooting

### Taxa de Elegibilidade < 80%

**Causa**: Dados fundamentais incompletos ou de baixa qualidade

**Solução**:
```bash
# Verificar quantos ativos têm fundamentos
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import RawFundamental
db = SessionLocal()
count = db.query(RawFundamental).count()
print(f'Fundamentos: {count}')
db.close()
"

# Se baixo, rodar pipeline em modo FULL
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 --force-full
```

### Muitos Missing Values (> 50%)

**Causa**: Histórico de dados insuficiente

**Solução**: Normal para ativos novos. O sistema imputa automaticamente.

### Scores Muito Baixos

**Causa**: Fatores críticos faltando (roe_mean_3y, price_to_book)

**Solução**: Aguardar acúmulo de histórico. Scores melhoram com o tempo.

---

## Migração de Versões Anteriores

Se você está vindo de uma versão anterior:

1. **Pull das mudanças**:
   ```bash
   git pull origin main
   ```

2. **Rebuild dos containers**:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

3. **Rodar pipeline de teste**:
   ```bash
   docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode test --limit 10
   ```

4. **Verificar logs** para confirmar 3 camadas funcionando

---

## Referências

- `app/filters/eligibility_filter.py` - Layer 1
- `app/factor_engine/missing_handler.py` - Layer 2.5
- `app/scoring/scoring_engine.py` - Layer 3
- `scripts/run_pipeline_docker.py` - Orquestração
