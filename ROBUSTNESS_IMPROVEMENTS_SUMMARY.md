# Melhorias de Robustez no Modelo de Scoring

## Resumo das Implementações

Este documento descreve as melhorias de robustez estrutural implementadas no modelo de scoring do Quant Stock Ranker.

## 1. Filtro de Elegibilidade Aprimorado

### Novos Critérios de Exclusão

Além dos critérios existentes (patrimônio líquido, EBITDA, receita e volume), foram adicionados:

#### 1.1 Lucro Líquido Negativo no Último Ano
- **Critério**: Excluir empresas com `net_income_last_year < 0`
- **Razão de exclusão**: `negative_net_income_last_year`
- **Impacto**: Elimina empresas com prejuízo recente

#### 1.2 Lucro Negativo em 2 dos Últimos 3 Anos
- **Critério**: Excluir empresas com lucro negativo em 2 ou mais dos últimos 3 anos
- **Razão de exclusão**: `negative_net_income_2_of_3_years`
- **Impacto**: Elimina empresas com histórico de prejuízos recorrentes

#### 1.3 Endividamento Excessivo
- **Critério**: Excluir empresas com `net_debt_to_ebitda > 8`
- **Razão de exclusão**: `excessive_leverage_debt_to_ebitda_gt_8`
- **Impacto**: Elimina empresas com alavancagem extrema
- **Exceção**: Instituições financeiras são isentas desta verificação

### Arquivo Modificado
- `app/filters/eligibility_filter.py`

## 2. Ajustes no Fator Qualidade

### 2.1 ROE Médio de 3 Anos
- **Mudança**: Usar `roe_mean_3y` ao invés de ROE de um único período
- **Benefício**: Reduz impacto de volatilidade de curto prazo

### 2.2 Penalização por Volatilidade do ROE
- **Fórmula**: `ROE_ajustado = ROE_mean - (0.5 * ROE_std)`
- **Implementação**: Novo fator `roe_volatility` (invertido no cálculo)
- **Benefício**: Favorece empresas com rentabilidade consistente

### 2.3 Penalização por Prejuízo Recente
- **Critério**: Se `net_income_last_year < 0`
- **Penalidade**: `quality_score *= 0.4` (redução de 60%)
- **Benefício**: Penaliza fortemente empresas com prejuízo recente

### 2.4 Penalização Progressiva de Endividamento
- **Níveis de penalização**:
  - `debt_to_ebitda > 3`: Penalização leve (0.9x)
  - `debt_to_ebitda > 5`: Penalização forte (0.7x)
  - `debt_to_ebitda > 8`: Exclusão (filtro de elegibilidade)
- **Benefício**: Penalização gradual baseada no nível de risco

### Arquivo Modificado
- `app/scoring/scoring_engine.py` - método `calculate_quality_score()`

## 3. Distress Flag

### 3.1 Implementação
- **Localização**: `score_asset_enhanced()` no `ScoringEngine`
- **Penalidade**: Reduz score final em 50% (multiplica por 0.5)

### 3.2 Condições de Ativação
O distress flag é ativado se **qualquer** das seguintes condições for verdadeira:

1. **Lucro líquido negativo no último ano**
   - `net_income_last_year < 0`
   - Razão: `negative_net_income_last_year`

2. **Lucro negativo em 2 dos últimos 3 anos**
   - Contagem de anos com lucro negativo >= 2
   - Razão: `negative_net_income_2_of_3_years`

3. **Endividamento elevado**
   - `debt_to_ebitda > 5`
   - Razão: `high_leverage_debt_to_ebitda_gt_5`

### 3.3 Registro no Breakdown
- Campo `risk_penalties['distress']`: 0.5 se ativado, 1.0 caso contrário
- Campo `risk_penalties['distress_reasons']`: Lista de razões que ativaram o flag

### Arquivo Modificado
- `app/scoring/scoring_engine.py` - método `score_asset_enhanced()`

## 4. Integração com Feature Service

### 4.1 Novos Campos Coletados
O `FeatureService` agora coleta dados adicionais para o filtro de elegibilidade:

- `net_income_last_year`: Lucro líquido do último ano
- `net_income_history`: Lista com lucro líquido dos últimos 3 anos
- `net_debt_to_ebitda`: Razão dívida líquida / EBITDA

### 4.2 Cálculo de net_debt_to_ebitda
```python
net_debt_to_ebitda = net_debt / ebitda if (
    net_debt is not None and 
    ebitda is not None and 
    ebitda != 0
) else None
```

### Arquivo Modificado
- `app/factor_engine/feature_service.py` - método `filter_eligible_assets()`

## 5. Testes Implementados

### 5.1 Novos Testes Unitários
Arquivo: `tests/unit/test_eligibility_filter.py`

Classe: `TestRobustnessImprovements`

Testes:
1. `test_negative_net_income_last_year_excludes`
2. `test_negative_net_income_2_of_3_years_excludes`
3. `test_excessive_leverage_excludes`
4. `test_financial_institution_exempt_from_leverage_check`
5. `test_all_robustness_criteria_pass`

### 5.2 Resultado dos Testes
```
5 passed in 1.04s
```

## 6. Impacto Esperado

### 6.1 Filtro de Elegibilidade
- **Antes**: ~94.6% de aprovação (70 de 74 ativos)
- **Depois**: Espera-se redução para ~85-90% devido aos novos critérios
- **Benefício**: Universo mais saudável financeiramente

### 6.2 Scoring
- **Qualidade**: Empresas com prejuízos ou alta volatilidade terão scores menores
- **Distress Flag**: Empresas em dificuldade terão score reduzido em 50%
- **Benefício**: Rankings mais conservadores e robustos

## 7. Próximos Passos

### 7.1 Atualização do Pipeline
Os seguintes componentes precisam ser atualizados para fornecer os novos campos:

1. **Fundamental Factors Calculator**
   - Calcular `roe_mean_3y` e `roe_volatility`
   - Fornecer `net_income_last_year` e `net_income_history`
   - Fornecer `debt_to_ebitda_raw` (valor não normalizado)

2. **Normalizer**
   - Adicionar normalização para `roe_mean_3y` e `roe_volatility`

3. **Score Service**
   - Passar novos campos para `score_asset_enhanced()`

### 7.2 Validação
- Executar pipeline completo com novos critérios
- Comparar rankings antes/depois
- Validar que empresas problemáticas (AZUL4, OIBR3, etc.) são corretamente penalizadas

## 8. Arquivos Modificados

1. `app/filters/eligibility_filter.py` - Novos critérios de exclusão
2. `app/scoring/scoring_engine.py` - Ajustes no quality score e distress flag
3. `app/factor_engine/feature_service.py` - Coleta de novos campos
4. `tests/unit/test_eligibility_filter.py` - Novos testes

## 9. Compatibilidade

### 9.1 Backward Compatibility
- Os novos campos são opcionais (verificação de `None`)
- Se não fornecidos, os critérios correspondentes são ignorados
- Código existente continua funcionando sem modificações

### 9.2 Migração
- Não é necessária migração de banco de dados
- Novos campos serão populados na próxima execução do pipeline
- Dados históricos podem não ter os novos campos (comportamento gracioso)

## 10. Documentação Técnica

### 10.1 Novos Parâmetros em `is_eligible()`

```python
fundamentals = {
    # Campos existentes
    'shareholders_equity': float,
    'ebitda': float,
    'revenue': float,
    
    # Novos campos
    'net_income_last_year': float,           # Lucro líquido do último ano
    'net_income_history': List[float],       # Lucro dos últimos 3 anos
    'net_debt_to_ebitda': float             # Razão dívida líquida / EBITDA
}
```

### 10.2 Novos Parâmetros em `calculate_quality_score()`

```python
factors = {
    # Campos existentes
    'net_margin': float,
    'revenue_growth_3y': float,
    'debt_to_ebitda': float,  # Normalizado
    
    # Novos campos
    'roe_mean_3y': float,           # ROE médio de 3 anos (normalizado)
    'roe_volatility': float,        # Volatilidade do ROE (normalizado)
    'net_income_last_year': float,  # Para penalização
    'debt_to_ebitda_raw': float     # Valor não normalizado para penalização
}
```

### 10.3 Novos Campos em `ScoreResult`

```python
risk_penalties = {
    'volatility': float,           # Existente
    'drawdown': float,             # Existente
    'distress': float,             # NOVO: 0.5 se ativado, 1.0 caso contrário
    'distress_reasons': List[str]  # NOVO: Razões que ativaram o distress flag
}
```

---

**Data de Implementação**: 2026-02-18
**Versão**: 1.0
**Status**: ✅ Implementado e Testado
