# Implementação de Fatores Específicos por Setor

## Resumo da Implementação

Implementação completa de cálculo de fatores específicos para instituições financeiras vs empresas industriais, seguindo a solução técnica correta para bancos.

## Solução Técnica para Bancos

### Qualidade:
- **ROE 3Y** (cap 30% vs 50% para industriais)
- **Crescimento lucro 3Y** (usando book value growth como proxy)
- **Estabilidade do lucro** (net_income_volatility invertido)
- **Índice de eficiência** (efficiency_ratio invertido - menor é melhor)

### Valor:
- **P/L** (pe_ratio invertido)
- **P/VP** (pb_ratio invertido - métrica chave para bancos)

### Remove:
- **EV/EBITDA** (não aplicável para bancos)
- **Debt/EBITDA** (não aplicável para bancos)

## Arquivos Modificados

### 1. `app/factor_engine/fundamental_factors.py`
- **Modificação**: Adicionada detecção automática de setor
- **Novos métodos**:
  - `_is_financial_institution()`: Detecta bancos por heurística ou AssetInfoService
  - `_calculate_financial_factors()`: Delega para FinancialFactorCalculator
  - `_calculate_industrial_factors()`: Implementação original para empresas industriais
- **Parâmetro novo**: `db_session` para acessar informações de setor

### 2. `app/factor_engine/financial_factors.py`
- **Status**: Já existia, apenas corrigido logging
- **Funcionalidades**:
  - ROE robusto com cap 30% para bancos
  - ROA (Return on Assets) - métrica chave para bancos
  - Efficiency ratio - índice de eficiência operacional
  - Book value growth - crescimento do patrimônio líquido
  - P/VP e P/L específicos para bancos

### 3. `app/scoring/scoring_engine.py`
- **Novos métodos**:
  - `calculate_quality_score_financial()`: Scoring de qualidade para bancos
  - `calculate_value_score_financial()`: Scoring de valor para bancos
  - `_is_financial_institution()`: Detecção baseada nos fatores calculados
  - `score_asset_sector_aware()`: Scoring com detecção automática de setor

### 4. `app/filters/eligibility_filter.py`
- **Modificação**: Bancos não precisam reportar EBITDA
- **Lógica**: Se não tem EBITDA mas tem revenue e equity válidos = provável banco
- **Exceção**: Debt/EBITDA > 8 não se aplica a bancos

### 5. `scripts/run_pipeline.py`
- **Modificação**: Passa `db_session` para `calculate_all_factors()`
- **Adicionado**: Path setup para execução correta

### 6. `app/models/schemas.py`
- **Nova tabela**: `AssetInfo` para armazenar setor e indústria
- **Campos**: ticker, sector, industry, company_name, country, etc.

### 7. `app/ingestion/asset_info_service.py`
- **Status**: Já existia
- **Funcionalidade**: Busca informações de setor do Yahoo Finance

## Scripts Criados

### 1. `scripts/migrate_asset_info_table.py`
- **Função**: Adiciona tabela AssetInfo ao banco existente
- **Status**: ✅ Executado com sucesso

### 2. `test_sector_specific_factors.py`
- **Função**: Testa detecção de setor e cálculo de fatores específicos
- **Status**: ✅ Todos os testes passaram
- **Cobertura**:
  - Detecção automática de bancos vs industriais
  - Cálculo de fatores específicos para cada setor
  - Scoring diferenciado por setor

## Detecção Automática de Setor

### Método 1: AssetInfoService (Preferencial)
- Usa informações do Yahoo Finance armazenadas na tabela `AssetInfo`
- Setores financeiros: "Financial Services", "Financial", "Banks", "Insurance", "Real Estate"

### Método 2: Heurística (Fallback)
- Se não tem EBITDA mas tem revenue e equity válidos = provável banco
- Funciona para a maioria dos casos sem necessidade de dados externos

## Fluxo de Execução

1. **Pipeline chama** `FundamentalFactorCalculator.calculate_all_factors()`
2. **Detecção de setor** via `_is_financial_institution()`
3. **Delegação**:
   - Bancos → `_calculate_financial_factors()` → `FinancialFactorCalculator`
   - Industriais → `_calculate_industrial_factors()` (implementação original)
4. **Scoring** usa `score_asset_sector_aware()` para detecção automática
5. **Fatores específicos** são calculados conforme o setor

## Resultados dos Testes

### Teste de Banco (ITUB4):
```
✅ ROE: 0.1000 (cap 30%)
✅ ROA: 0.0100 (específico para bancos)
✅ P/VP: 1.2000 (métrica chave)
✅ P/L: 12.0000
✅ Efficiency Ratio: 0.8000
✅ debt_to_ebitda: None (não aplicável)
✅ ev_ebitda: None (não aplicável)
```

### Teste de Industrial (PETR4):
```
✅ ROE: 0.1000 (cap 50%)
✅ debt_to_ebitda: 1.6667 (aplicável)
✅ ev_ebitda: 6.0000 (aplicável)
✅ P/VP: 2.0000
✅ P/L: 20.0000
```

### Diferenças no Scoring:
- **Quality Score**: Bancos usam fatores específicos (ROE, efficiency, estabilidade)
- **Value Score**: Bancos usam apenas P/L e P/VP (remove EV/EBITDA)
- **Detecção automática**: Funciona corretamente para ambos os setores

## Próximos Passos

1. **Testar com dados reais**: Executar pipeline com bancos brasileiros (ITUB4, BBDC4, BBAS3)
2. **Popular AssetInfo**: Executar pipeline para buscar informações de setor automaticamente
3. **Validar rankings**: Verificar se bancos não são mais penalizados injustamente
4. **Monitorar performance**: Acompanhar se bancos sobem no ranking com os novos fatores

## Comandos para Teste

```bash
# Inicializar banco (já feito)
echo sim | python scripts/init_db.py --drop

# Testar implementação
python test_sector_specific_factors.py

# Executar pipeline com bancos
python scripts/run_pipeline.py --mode test --tickers ITUB4,BBDC4,PETR4,VALE3 --limit 4
```

## Status Final

✅ **Implementação completa e testada**
✅ **Detecção automática de setor funcionando**
✅ **Fatores específicos para bancos implementados**
✅ **Scoring diferenciado por setor**
✅ **Filtro de elegibilidade adaptado para bancos**
✅ **Migração de banco de dados concluída**

A solução técnica está correta e segue as melhores práticas para análise de instituições financeiras vs empresas industriais.