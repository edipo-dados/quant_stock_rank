# 🎓 Melhorias Acadêmicas - Versão 2.2.0

## ✅ O Que Foi Implementado

### 1. Momentum Acadêmico (Excluindo Último Mês)
O sistema agora usa a metodologia acadêmica de momentum que **exclui o último mês** dos retornos.

**Por quê?**
- Estudos mostram que ações com alto retorno no último mês tendem a reverter no curto prazo
- Momentum de 6-12 meses (excluindo último mês) é mais persistente e confiável

**Novos Fatores:**
- `momentum_6m_ex_1m` = return_6m - return_1m
- `momentum_12m_ex_1m` = return_12m - return_1m

**Score de Momentum Atualizado:**
```
momentum_score = média([
    momentum_6m_ex_1m,      # Novo
    momentum_12m_ex_1m,     # Novo
    -volatility_90d,
    -recent_drawdown
])
```

**Mudanças:**
- ✅ RSI removido do score (mantido para compatibilidade)
- ✅ return_6m e return_12m não usados diretamente no score

### 2. Normalização Setorial (Implementada, Não Ativada)
Código pronto para normalização intra-setor, mas não ativado (requer dados de setor).

**Quando ativar:**
- Adicionar ingestão de dados de setor
- Usar `normalize_factors_sector_neutral()` no pipeline

## 🚀 Como Aplicar as Mudanças

### Passo 1: Migração do Banco de Dados
```bash
# Adicionar novas colunas à tabela features_daily
docker exec -it quant_backend python scripts/migrate_add_momentum_columns.py
```

### Passo 2: Executar Pipeline
```bash
# Calcular novos fatores para todos os ativos
docker exec -it quant_backend python scripts/run_pipeline_docker.py
```

### Passo 3: Validar
```bash
# Verificar se os novos fatores foram calculados
docker exec -it quant_backend python scripts/validate_features.py

# Verificar scores atualizados
docker exec -it quant_backend python scripts/check_db.py
```

## 📊 Impacto Esperado

### Melhorias
- ✅ Redução de ruído de curto prazo
- ✅ Melhor captura de tendências persistentes
- ✅ Alinhamento com literatura acadêmica
- ✅ Potencial melhoria de performance

### Compatibilidade
- ✅ Código anterior continua funcionando
- ✅ RSI mantido no banco (não usado no score)
- ✅ Migração não destrutiva

## 📚 Referências Acadêmicas

1. **Jegadeesh, N. (1990)**. "Evidence of Predictable Behavior of Security Returns"
2. **Lehmann, B. N. (1990)**. "Fads, Martingales, and Market Efficiency"
3. **Jegadeesh, N., & Titman, S. (1993)**. "Returns to Buying Winners and Selling Losers"

## 📖 Documentação Completa

- [MELHORIAS_ACADEMICAS.md](docs/MELHORIAS_ACADEMICAS.md) - Detalhes técnicos completos
- [CALCULOS_RANKING.md](docs/CALCULOS_RANKING.md) - Metodologia atualizada
- [CHANGELOG.md](CHANGELOG.md) - Histórico de mudanças

## ❓ FAQ

### O ranking vai mudar?
Sim, o ranking será recalculado com a nova metodologia de momentum.

### Preciso reprocessar dados históricos?
Sim, execute o pipeline após a migração para calcular os novos fatores.

### O que acontece com o RSI?
RSI continua sendo calculado e salvo, mas não é mais usado no score final.

### Posso reverter as mudanças?
Sim, o código anterior está preservado. Basta usar os campos antigos.

### Quando ativar normalização setorial?
Quando tiver dados de setor de qualidade. Por enquanto, use normalização cross-sectional global.

## 🎯 Próximos Passos

1. ✅ Execute a migração
2. ✅ Execute o pipeline
3. ✅ Valide os resultados
4. ⏳ Compare ranking antes/depois
5. ⏳ Considere ativar normalização setorial

---

**Versão:** 2.2.0  
**Data:** 24 de Fevereiro de 2026  
**Status:** Pronto para produção ✅
