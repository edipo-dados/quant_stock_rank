# Melhorias Acadêmicas - Versão 2.2.0

Este documento descreve as melhorias acadêmicas implementadas no sistema de ranking quantitativo.

## 📚 Visão Geral

As melhorias implementadas seguem metodologias acadêmicas amplamente documentadas na literatura de finanças quantitativas, com foco em:

1. **Momentum Acadêmico**: Excluir último mês para evitar reversão de curto prazo
2. **Normalização Setorial**: Z-score intra-setor para comparação justa

## 1. Momentum Acadêmico (IMPLEMENTADO ✅)

### Problema Identificado
A metodologia anterior usava retornos brutos de 6 e 12 meses, que incluem o último mês. Estudos acadêmicos mostram que:
- **Short-term reversal effect**: Ações com alto retorno no último mês tendem a reverter no curto prazo
- **Momentum effect**: Ações com alto retorno nos últimos 12 meses (excluindo último mês) tendem a continuar performando bem

### Solução Implementada
Calcular momentum excluindo o último mês:

```python
# Novos fatores
return_1m = (price_today - price_1m_ago) / price_1m_ago
momentum_6m_ex_1m = return_6m - return_1m
momentum_12m_ex_1m = return_12m - return_1m
```

### Score de Momentum Atualizado
```python
momentum_score = mean([
    momentum_6m_ex_1m_normalized,   # Novo
    momentum_12m_ex_1m_normalized,  # Novo
    -volatility_90d_normalized,
    -recent_drawdown_normalized
])
```

### Mudanças
- ✅ RSI removido do score (mantido para compatibilidade)
- ✅ return_6m e return_12m não usados diretamente no score
- ✅ Novos fatores momentum_6m_ex_1m e momentum_12m_ex_1m

### Referências Acadêmicas
- **Jegadeesh, N. (1990)**. "Evidence of Predictable Behavior of Security Returns". *Journal of Finance*, 45(3), 881-898.
- **Lehmann, B. N. (1990)**. "Fads, Martingales, and Market Efficiency". *Quarterly Journal of Economics*, 105(1), 1-28.
- **Jegadeesh, N., & Titman, S. (1993)**. "Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency". *Journal of Finance*, 48(1), 65-91.

## 2. Normalização Setorial (IMPLEMENTADO, NÃO ATIVADO ⚠️)

### Problema Identificado
A normalização cross-sectional atual compara todos os ativos juntos, o que pode ser injusto:
- Setores diferentes têm características fundamentalmente diferentes
- Exemplo: Bancos têm ROE naturalmente mais alto que utilities
- Comparar P/L de banco com P/L de tech não faz sentido

### Solução Implementada
Z-score intra-setor (sector-neutral):

```python
def sector_neutral_zscore(df, feature, sector_col="sector"):
    """
    Calcula z-score dentro de cada setor.
    
    Para cada setor:
    - Se setor >= 5 ativos: z-score intra-setor
    - Se setor < 5 ativos: z-score global (fallback)
    """
    normalized = pd.Series(index=df.index, dtype=float)
    
    for sector in df[sector_col].unique():
        sector_mask = df[sector_col] == sector
        sector_data = df.loc[sector_mask, feature]
        
        if sector_data.count() >= 5:
            # Z-score intra-setor
            mean = sector_data.mean()
            std = sector_data.std()
            if std > 0:
                normalized[sector_mask] = (sector_data - mean) / std
        else:
            # Fallback para z-score global
            mean = df[feature].mean()
            std = df[feature].std()
            if std > 0:
                normalized[sector_mask] = (sector_data - mean) / std
    
    return normalized
```

### Status
- ✅ Código implementado em `app/factor_engine/normalizer.py`
- ✅ Método `normalize_factors_sector_neutral()` disponível
- ⚠️ **NÃO ATIVADO** no pipeline (requer dados de setor)

### Para Ativar
1. Adicionar ingestão de dados de setor (tabela `asset_info`)
2. Adicionar coluna `sector` ao DataFrame de fatores
3. Usar `normalize_factors_sector_neutral()` no pipeline

### Referências Acadêmicas
- **Fama, E. F., & French, K. R. (1997)**. "Industry costs of equity". *Journal of Financial Economics*, 43(2), 153-193.
- **Moskowitz, T. J., & Grinblatt, M. (1999)**. "Do Industries Explain Momentum?". *Journal of Finance*, 54(4), 1249-1290.

## 3. Mudanças no Banco de Dados

### Novas Colunas em `features_daily`
```sql
ALTER TABLE features_daily ADD COLUMN return_1m FLOAT;
ALTER TABLE features_daily ADD COLUMN momentum_6m_ex_1m FLOAT;
ALTER TABLE features_daily ADD COLUMN momentum_12m_ex_1m FLOAT;
```

### Migração
Execute o script de migração:
```bash
docker exec -it quant_backend python scripts/migrate_add_momentum_columns.py
```

## 4. Impacto Esperado

### Momentum Acadêmico
- ✅ Redução de ruído de curto prazo
- ✅ Melhor captura de tendências persistentes
- ✅ Alinhamento com literatura acadêmica
- ✅ Potencial melhoria de performance out-of-sample

### Normalização Setorial (quando ativada)
- ✅ Comparação mais justa entre ativos
- ✅ Redução de viés setorial
- ✅ Melhor diversificação setorial no ranking
- ⚠️ Requer dados de setor de qualidade

## 5. Tratamento de Valores Ausentes (IMPLEMENTADO ✅)

### Problema Identificado
A metodologia anterior não tratava adequadamente valores ausentes (missing values):
- Valores ausentes eram tratados como zero, distorcendo análise
- Não havia distinção entre fatores críticos e secundários
- Ativos com dados insuficientes não eram filtrados adequadamente

### Solução Implementada

#### Classificação de Fatores
**Fatores Críticos** (ausência = exclusão):
- Momentum: `momentum_6m_ex_1m`, `momentum_12m_ex_1m`
- Quality: `roe_mean_3y`, `net_margin`
- Value: `pe_ratio`, `price_to_book`

**Fatores Secundários** (ausência = imputação setorial):
- Momentum: `volatility_90d`, `recent_drawdown`
- Quality: `roe_volatility`, `revenue_growth_3y`, `debt_to_ebitda`
- Value: `ev_ebitda`, `fcf_yield`

#### Filtro de Elegibilidade Atualizado
```python
# Verificar fatores críticos
critical_momentum = ['momentum_6m_ex_1m', 'momentum_12m_ex_1m']
critical_quality = ['roe_mean_3y', 'net_margin']
critical_value = ['pe_ratio', 'price_to_book']

for factor in critical_momentum + critical_quality + critical_value:
    if fundamentals.get(factor) is None:
        exclusion_reasons.append(f"missing_critical_factor_{factor}")
```

#### Imputação Setorial
```python
# Imputar fatores secundários com média setorial
imputed_df = normalizer.impute_missing_with_sector_mean(
    factors_df,
    factor_columns=['volatility_90d', 'recent_drawdown'],
    sector_col='sector'
)
```

#### Scoring Engine Atualizado
```python
# Se fatores críticos ausentes, retorna score muito baixo
if missing_critical:
    logger.warning(f"Critical factors missing: {missing_critical}")
    return -999.0

# Se fatores secundários ausentes, usa apenas disponíveis
for factor_name in secondary_factors:
    value = factors.get(factor_name)
    if value is not None and not math.isnan(value):
        factors_list.append(value)

# Calcular média dos fatores disponíveis
score = sum(factors_list) / len(factors_list)
```

### Mudanças
- ✅ Classificação de fatores em críticos e secundários
- ✅ Filtro de elegibilidade verifica fatores críticos
- ✅ Imputação setorial para fatores secundários
- ✅ Scoring engine trata missing values adequadamente
- ✅ Documentação completa em `docs/MISSING_VALUE_TREATMENT.md`

### Referências Acadêmicas
- **Little, R. J., & Rubin, D. B. (2019)**. "Statistical Analysis with Missing Data" (3rd ed.). Wiley.
- **Enders, C. K. (2010)**. "Applied Missing Data Analysis". Guilford Press.

## 6. Remoção de Penalidades Fixas (IMPLEMENTADO ✅)

### Problema Identificado
A metodologia anterior usava thresholds arbitrários:
- `debt_to_ebitda > 5` → penalidade de 50%
- `net_income < 0` → penalidade de 60%

Problemas:
- Thresholds arbitrários sem justificativa acadêmica
- Penalidades fixas não capturam gradação de risco
- Dupla penalização (threshold + fator normalizado)

### Solução Implementada

#### Remoção de Penalidades Fixas
```python
# ANTES (REMOVIDO):
if debt_to_ebitda_raw > 5:
    quality_score *= 0.5  # Penalidade fixa

if net_income_last_year < 0:
    quality_score *= 0.4  # Penalidade fixa

# DEPOIS:
# Risco capturado diretamente nos fatores normalizados
# debt_to_ebitda alto → score baixo naturalmente (invertido)
# net_income negativo → score baixo naturalmente
```

#### Penalização Contínua
O risco agora é capturado de forma contínua através dos fatores normalizados:
- `debt_to_ebitda` normalizado e invertido (-1 a +1)
- Valores altos de dívida resultam em scores baixos naturalmente
- Sem thresholds arbitrários

#### Filtro de Elegibilidade
Critérios extremos movidos para filtro de elegibilidade:
- `debt_to_ebitda > 8` → exclusão (não penalidade)
- `net_income < 0` no último ano → exclusão
- `net_income < 0` em 2 dos últimos 3 anos → exclusão

### Mudanças
- ✅ Removidas penalidades fixas de `calculate_quality_score()`
- ✅ Risco capturado diretamente em fatores normalizados
- ✅ Critérios extremos movidos para filtro de elegibilidade
- ✅ Penalização contínua baseada em z-score

### Referências Acadêmicas
- **Piotroski, J. D. (2000)**. "Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers". *Journal of Accounting Research*, 38, 1-41.
- **Altman, E. I. (1968)**. "Financial Ratios, Discriminant Analysis and the Prediction of Corporate Bankruptcy". *Journal of Finance*, 23(4), 589-609.

## 7. Testes e Validação

### Testes Necessários
1. ✅ Verificar cálculo de momentum_6m_ex_1m e momentum_12m_ex_1m
2. ✅ Verificar salvamento no banco de dados
3. ✅ Verificar score de momentum atualizado
4. ✅ Verificar tratamento de missing values
5. ✅ Verificar remoção de penalidades fixas
6. ⏳ Comparar ranking antes/depois (backtest)
7. ⏳ Validar normalização setorial (quando ativada)

### Comandos de Teste
```bash
# 1. Executar migração
docker exec -it quant_backend python scripts/migrate_add_momentum_columns.py

# 2. Executar pipeline
docker exec -it quant_backend python scripts/run_pipeline_docker.py

# 3. Verificar features calculadas
docker exec -it quant_backend python scripts/validate_features.py

# 4. Verificar scores
docker exec -it quant_backend python scripts/check_db.py

# 5. Verificar tratamento de missing values
docker exec -it quant_backend python -c "
from app.scoring.scoring_engine import ScoringEngine
from app.config import settings

engine = ScoringEngine(settings)

# Testar com fatores críticos ausentes
factors = {'momentum_6m_ex_1m': None, 'momentum_12m_ex_1m': 0.15}
score = engine.calculate_momentum_score(factors)
print(f'Score com fator crítico ausente: {score}')  # Deve ser -999.0

# Testar com fatores secundários ausentes
factors = {'momentum_6m_ex_1m': 0.10, 'momentum_12m_ex_1m': 0.15}
score = engine.calculate_momentum_score(factors)
print(f'Score sem fatores secundários: {score}')  # Deve calcular normalmente
"
```

## 8. Próximos Passos

### Curto Prazo
- [x] Executar migração de banco de dados (momentum)
- [x] Executar migração de banco de dados (value/size)
- [x] Implementar tratamento de missing values
- [x] Remover penalidades fixas
- [ ] Executar pipeline com novos fatores
- [ ] Validar cálculos
- [ ] Comparar ranking antes/depois

### Médio Prazo
- [ ] Adicionar ingestão de dados de setor
- [ ] Ativar normalização setorial
- [ ] Testar impacto de normalização setorial
- [ ] Backtest comparativo

### Longo Prazo
- [ ] Implementar outros fatores acadêmicos (low volatility, quality minus junk)
- [ ] Implementar rebalanceamento dinâmico
- [ ] Implementar risk parity

## 9. Referências Completas

### Momentum
1. Jegadeesh, N. (1990). "Evidence of Predictable Behavior of Security Returns". *Journal of Finance*, 45(3), 881-898.
2. Lehmann, B. N. (1990). "Fads, Martingales, and Market Efficiency". *Quarterly Journal of Economics*, 105(1), 1-28.
3. Jegadeesh, N., & Titman, S. (1993). "Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency". *Journal of Finance*, 48(1), 65-91.

### Setores
4. Fama, E. F., & French, K. R. (1997). "Industry costs of equity". *Journal of Financial Economics*, 43(2), 153-193.
5. Moskowitz, T. J., & Grinblatt, M. (1999). "Do Industries Explain Momentum?". *Journal of Finance*, 54(4), 1249-1290.

### Multi-Factor
6. Fama, E. F., & French, K. R. (1992). "The Cross-Section of Expected Stock Returns". *Journal of Finance*, 47(2), 427-465.
7. Carhart, M. M. (1997). "On Persistence in Mutual Fund Performance". *Journal of Finance*, 52(1), 57-82.

### Missing Data
8. Little, R. J., & Rubin, D. B. (2019). "Statistical Analysis with Missing Data" (3rd ed.). Wiley.
9. Enders, C. K. (2010). "Applied Missing Data Analysis". Guilford Press.

### Quality & Value
10. Piotroski, J. D. (2000). "Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers". *Journal of Accounting Research*, 38, 1-41.
11. Altman, E. I. (1968). "Financial Ratios, Discriminant Analysis and the Prediction of Corporate Bankruptcy". *Journal of Finance*, 23(4), 589-609.

## 10. Contato e Suporte

Para dúvidas sobre as melhorias acadêmicas:
- Consulte `docs/CALCULOS_RANKING.md` para detalhes técnicos
- Consulte `CHANGELOG.md` para histórico de mudanças
- Execute `python scripts/validate_features.py` para validar cálculos
