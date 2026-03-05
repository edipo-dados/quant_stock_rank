# Modelo Multifator Robusto v2.0 - Documentação

## 📖 Índice de Documentação

Este diretório contém toda a documentação relacionada à implementação do Modelo Multifator Robusto v2.0.

---

## 📄 Documentos Principais

### 1. MULTIFACTOR_IMPLEMENTATION_SUMMARY.md
**Para:** Desenvolvedores e equipe técnica
**Conteúdo:**
- Resumo técnico de todas as mudanças
- Arquivos modificados e criados
- Detalhes de implementação por sprint
- Estrutura do modelo multifator
- Instruções de deploy

**Quando usar:** Para entender o que foi implementado tecnicamente.

---

### 2. MULTIFACTOR_USER_GUIDE.md
**Para:** Usuários finais e analistas
**Conteúdo:**
- Visão geral do modelo
- Como usar o sistema
- Interpretação de resultados
- Troubleshooting
- Configurações avançadas
- Exemplos práticos

**Quando usar:** Para aprender a usar o sistema e interpretar resultados.

---

### 3. DEPLOY_CHECKLIST_V2.md
**Para:** DevOps e responsáveis pelo deploy
**Conteúdo:**
- Checklist completo de deploy
- Comandos passo a passo
- Testes pós-deploy
- Procedimentos de rollback
- Monitoramento

**Quando usar:** Durante o processo de deploy no EC2.

---

### 4. docs/MULTIFACTOR_MODEL_PLAN.md
**Para:** Arquitetos e planejadores
**Conteúdo:**
- Plano detalhado de implementação
- Análise do estado atual
- Roadmap de 4 fases
- Referências acadêmicas
- Estrutura de código

**Quando usar:** Para entender o planejamento e arquitetura do modelo.

---

## 🚀 Quick Start

### Para Desenvolvedores

1. Ler: `MULTIFACTOR_IMPLEMENTATION_SUMMARY.md`
2. Revisar código modificado
3. Seguir: `DEPLOY_CHECKLIST_V2.md`

### Para Usuários

1. Ler: `MULTIFACTOR_USER_GUIDE.md`
2. Acessar frontend: `http://seu-ec2-ip:8501`
3. Executar backtest de teste

### Para Deploy

1. Fazer backup: `./deploy/backup-db.sh`
2. Seguir: `DEPLOY_CHECKLIST_V2.md` passo a passo
3. Validar: `scripts/validate_backtest_data.py`

---

## 📊 Resumo das Mudanças

### Novos Fatores
- ✅ return_3m (momentum)
- ✅ ROIC (quality)
- ✅ volatility_1y (risk)
- ✅ max_drawdown_1y (risk)

### Novos Filtros
- ✅ minimum_market_cap (1 bilhão BRL)

### Novos Pesos
- Momentum: 0.4 (↑ de 0.35)
- Quality: 0.2 (↓ de 0.25)
- Value: 0.3 (mantido)
- Risk: 0.1 (novo)

### Novas Visualizações
- ✅ Gráfico de drawdown
- ✅ Tabela de retornos anuais
- ✅ Gráfico de turnover

### Novas Validações
- ✅ BacktestDataValidator
- ✅ Script de validação standalone
- ✅ Validação automática no backtest

---

## 🎯 Objetivos do Modelo

O modelo multifator robusto visa:

1. **Maior Alpha:** Retorno excedente vs IBOVESPA
2. **Sharpe > 1.0:** Boa relação risco/retorno
3. **Drawdown < 20%:** Proteção em quedas
4. **IR > 0.5:** Alpha consistente
5. **Turnover < 50%:** Custos controlados

---

## 📈 Métricas de Sucesso

### Cenário Ideal
```
Total Return: +150%
CAGR: +25%
Sharpe Ratio: 1.5
Max Drawdown: -15%
Alpha: +10%
Information Ratio: 0.8
Turnover Médio: 35%
```

---

## 🔧 Comandos Úteis

### Validar Dados
```bash
docker exec quant-ranker-backend python scripts/validate_backtest_data.py \
  --start-date 2021-01-01 --end-date 2026-03-05 --top-n 10
```

### Rodar Pipeline
```bash
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py
```

### Verificar Logs
```bash
docker logs quant-ranker-backend --tail 100 --follow
```

### Backup
```bash
./deploy/backup-db.sh
```

---

## 📚 Referências Acadêmicas

- **Fama & French (1993):** Common risk factors
- **Jegadeesh & Titman (1993):** Momentum
- **Ang et al. (2006):** Low Volatility Anomaly
- **Asness et al. (2014):** Quality Minus Junk

---

## 🆘 Suporte

### Problemas Comuns

**Erro: "Validação falhou"**
→ Rodar pipeline: `scripts/run_pipeline_docker.py`

**Scores N/A**
→ Normal para alguns ativos (ex: bancos sem EBITDA)

**Backtest lento**
→ Reduzir período ou top_n

### Logs
```bash
# Backend
docker logs quant-ranker-backend --tail 100

# Frontend
docker logs quant-ranker-frontend --tail 100
```

### Rollback
Ver seção de rollback em `DEPLOY_CHECKLIST_V2.md`

---

## 📝 Changelog

### v2.0 (2026-03-05)
- ✅ Modelo multifator robusto implementado
- ✅ 4 novos fatores adicionados
- ✅ Pesos otimizados
- ✅ 3 novas visualizações
- ✅ Sistema de validação automática

### v1.0 (anterior)
- Modelo básico com momentum e value
- Backtest simples
- Métricas básicas

---

## 🎓 Aprendizado

### Para Entender o Modelo
1. Ler: `MULTIFACTOR_USER_GUIDE.md` - Seção "Visão Geral"
2. Ler: `docs/MULTIFACTOR_MODEL_PLAN.md` - Seção "Estrutura"
3. Executar backtest de teste
4. Analisar resultados

### Para Modificar o Modelo
1. Ler: `MULTIFACTOR_IMPLEMENTATION_SUMMARY.md`
2. Revisar: `app/scoring/scoring_engine.py`
3. Ajustar pesos em: `app/config.py`
4. Rebuild e testar

---

## ✅ Status

**Implementação:** ✅ Completa (Sprint 1-4)
**Testes:** ✅ Validados
**Documentação:** ✅ Completa
**Deploy:** 🟡 Pendente

---

## 📞 Contato

Para dúvidas sobre:
- **Implementação técnica:** Ver `MULTIFACTOR_IMPLEMENTATION_SUMMARY.md`
- **Uso do sistema:** Ver `MULTIFACTOR_USER_GUIDE.md`
- **Deploy:** Ver `DEPLOY_CHECKLIST_V2.md`
- **Planejamento:** Ver `docs/MULTIFACTOR_MODEL_PLAN.md`

---

**Última atualização:** 2026-03-05
**Versão:** 2.0 (Modelo Multifator Robusto)
**Status:** ✅ Pronto para Deploy
