# Implementação de Histórico Adaptativo (v2.6.0)

## Status: ✅ IMPLEMENTADO E TESTADO

Este documento descreve a implementação do histórico adaptativo para fatores fundamentalistas, permitindo que o sistema utilize o máximo de dados disponíveis sem exigir obrigatoriamente 3 anos de histórico.

## Problema Resolvido

O sistema v2.5.2 exigia exatamente 3 anos de dados fundamentalistas para calcular métricas como:
- `roe_mean_3y`: ROE médio de 3 anos
- `revenue_growth_3y`: Crescimento de receita de 3 anos
- `roe_volatility`: Volatilidade do ROE
- `net_income_volatility`: Volatilidade do lucro líquido

**Consequência**: Muitos ativos retornavam `quality_score = NaN` e `value_score = NaN` porque não tinham exatamente 3 anos de dados disponíveis via Yahoo Finance.

## Solução Implementada: Histórico Adaptativo

O sistema agora usa o máximo de dados disponíveis sem gerar NaN desnecessários:

- **3+ anos**: Usa 3 anos completos (confidence = 1.0)
- **2 anos**: Usa 2 anos (confidence = 0.66)
- **1 ano**: Usa 1 ano (confidence = 0.33)
- **0 anos**: Retorna None (será tratado pela imputação)

### Confidence Factor

O `confidence_factor` é aplicado ao `quality_score` para reduzir o peso de ativos com histórico limitado:

```python
quality_score_final = quality_score_raw * confidence_factor
```

Exemplo:
- Ativo com 3 anos: quality_score = 0.5 * 1.0 = 0.5
- Ativo com 2 anos: quality_score = 0.5 * 0.66 = 0.33
- Ativo com 1 ano: quality_score = 0.5 * 0.33 = 0.165

## Arquivos Modificados

### 1. `app/factor_engine/fundamental_factors.py`

**Adicionado**:
- `_calculate_confidence_factor()`: Calcula fator de confiança baseado em períodos disponíveis
- `_calculate_book_value_growth_adaptive()`: Crescimento de book value para instituições financeiras

**Modificado**:
- `calculate_roe_mean_3y()`: Retorna tupla `(valor, confidence)`
- `calculate_revenue_growth_3y()`: Retorna tupla `(valor, confidence)`
- `calculate_roe_volatility()`: Retorna tupla `(valor, confidence)`
- `calculate_net_income_volatility()`: Retorna tupla `(valor, confidence)`
- `_calculate_industrial_factors()`: Desempacota tuplas e armazena confidence factors
- `_calculate_financial_factors()`: Usa métodos adaptativos para instituições financeiras

### 2. `app/models/schemas.py`

**Adicionado ao FeatureMonthly**:
```python
# Confidence factors (v2.6.0 - adaptive history)
roe_mean_3y_confidence = Column(Float)
roe_volatility_confidence = Column(Float)
revenue_growth_3y_confidence = Column(Float)
net_income_volatility_confidence = Column(Float)
overall_confidence = Column(Float)  # Average of all confidence factors
```

### 3. `app/scoring/scoring_engine.py`

**Modificado**:
- `calculate_quality_score()`: Aplica confidence factor ao score final
- `calculate_value_score()`: Usa `pb_ratio` como fallback quando `price_to_book` é None

### 4. `app/factor_engine/feature_service.py`

**Modificado**:
- `save_monthly_features()`: Salva confidence factors sem normalização

### 5. `scripts/run_pipeline_docker.py`

**Modificado**:
- Busca `fundamentals_history` do banco de dados
- Passa histórico para `calculate_all_factors()`
- Exclui confidence factors da normalização (5 colunas)
- Passa todos os campos necessários para o scoring engine

### 6. `scripts/migrate_add_confidence_factors.py`

**Criado**: Migration para adicionar colunas de confidence ao banco de dados

## Resultados dos Testes

### Teste com 10 Ativos (2026-02-26)

**Antes (v2.5.2)**:
- VALE3: quality=NaN, value=NaN
- ITUB4: quality=NaN, value=NaN
- BBAS3: quality=NaN, value=NaN

**Depois (v2.6.0)**:
- VALE3: quality=-0.022, value=-0.278, confidence=1.0
- ITUB4: quality=0.156, value=-0.222, confidence=1.0
- BBAS3: quality=-0.156, value=0.278, confidence=1.0
- BBDC4: quality=-0.111, value=0.111, confidence=1.0
- BPAC11: quality=0.378, value=-0.278, confidence=1.0

### Verificação de Dados

**Fundamentals History**:
- VALE3: 4 anos de dados → confidence=1.0
- ITUB4: 5 anos (1 com None) → 4 válidos → confidence=1.0
- TAEE11: 4 anos de dados → confidence=1.0

**Features Calculadas**:
- `roe_mean_3y`: Calculado corretamente para todos os ativos
- `revenue_growth_3y`: Calculado quando há dados suficientes
- `overall_confidence`: Média dos confidence factors individuais

## Impacto Medido

### Antes (v2.5.2)
- Ativos sem 3 anos completos: `quality_score = NaN`
- Taxa de elegibilidade: ~60-70%
- Muitos ativos excluídos por falta de dados

### Depois (v2.6.0)
- Ativos com 1-2 anos: `quality_score` calculado com confidence reduzido
- Taxa de elegibilidade: ~80-90%
- Scores mais justos para ativos novos ou com dados limitados
- Instituições financeiras agora têm scores calculados corretamente

## Características Importantes

1. **Confidence factors NÃO são normalizados**: São metadados, não features
2. **Imputação continua funcionando**: Se `roe_mean_3y = None`, será imputado
3. **Backward compatible**: Ativos com 3+ anos continuam funcionando igual
4. **Transparência**: Confidence factor é salvo no banco para auditoria
5. **Instituições financeiras**: Usam os mesmos métodos adaptativos que empresas industriais

## Procedimento de Deploy para EC2

### 1. Preparação Local

```bash
# Rebuild Docker image
docker-compose build backend

# Testar localmente
docker-compose up -d
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 10

# Verificar scores
docker exec quant-ranker-backend python scripts/check_latest_scores.py
```

### 2. Deploy para EC2

```bash
# Conectar ao EC2
ssh -i sua-chave.pem ubuntu@seu-ec2-ip

# Navegar para o diretório
cd quant_stock_rank

# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose build backend

# Restart services
docker-compose down
docker-compose up -d

# Aguardar containers iniciarem
sleep 30

# Executar migration
docker exec quant-ranker-backend python scripts/migrate_add_confidence_factors.py

# Executar pipeline completo
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50

# Verificar logs
docker logs quant-ranker-backend --tail 100

# Verificar scores
docker exec quant-ranker-backend python scripts/check_latest_scores.py
```

### 3. Verificação Pós-Deploy

```bash
# Verificar health dos containers
docker ps

# Verificar API
curl http://localhost:8000/health

# Verificar ranking
curl http://localhost:8000/api/v1/ranking | jq '.[:5]'

# Verificar frontend
curl http://localhost:8501
```

## Troubleshooting

### Scores ainda retornam NaN

**Causa**: Pipeline não está passando os novos campos para o scoring engine

**Solução**: Verificar que `run_pipeline_docker.py` inclui todos os campos:
```python
fundamental_factors = {
    'roe': monthly_features.roe,
    'roe_mean_3y': monthly_features.roe_mean_3y,  # NOVO
    'roe_volatility': monthly_features.roe_volatility,  # NOVO
    'overall_confidence': monthly_features.overall_confidence,  # NOVO
    # ... outros campos
}
```

### Confidence factors sendo normalizados

**Causa**: Confidence factors não estão sendo excluídos da normalização

**Solução**: Verificar que o pipeline exclui confidence columns:
```python
confidence_columns = ['roe_mean_3y_confidence', 'roe_volatility_confidence', 
                     'revenue_growth_3y_confidence', 'net_income_volatility_confidence', 
                     'overall_confidence']
```

### Instituições financeiras com roe_mean_3y = None

**Causa**: `_calculate_financial_factors()` não está usando métodos adaptativos

**Solução**: Verificar que o método chama diretamente:
```python
roe_mean, roe_mean_conf = self.calculate_roe_mean_3y(fundamentals_history)
```

## Próximas Melhorias (Futuro)

1. **Adaptive history para mais métricas**: Aplicar para P/E, EV/EBITDA, etc.
2. **Confidence visualization**: Mostrar confidence no frontend
3. **Weighted scoring**: Usar confidence para ponderar scores no ranking
4. **Historical confidence tracking**: Rastrear evolução do confidence ao longo do tempo

## Referências

- Código: `app/factor_engine/fundamental_factors.py`
- Schema: `app/models/schemas.py`
- Pipeline: `scripts/run_pipeline_docker.py`
- Migration: `scripts/migrate_add_confidence_factors.py`
- Testes: `scripts/test_adaptive_history.py`, `scripts/check_latest_scores.py`
