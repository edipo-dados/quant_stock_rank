# Próximos Passos - Deploy v2.7.0

## ✅ Git Commit Concluído

**Commit**: `81fcd98`  
**Tag**: `v2.7.0`  
**Branch**: `main`  
**Status**: ✅ Pushed para GitHub

### Estatísticas
- 53 arquivos alterados
- 4,143 inserções (+)
- 7,786 deleções (-)

### Mudanças
- ✅ 10 arquivos novos
- ✅ 9 arquivos modificados
- ✅ 34 arquivos removidos (limpeza)

---

## 🚀 Como Fazer o Deploy no EC2

### Passo 1: Conectar ao EC2

```bash
ssh ubuntu@<seu-ec2-ip>
```

### Passo 2: Atualizar Código

```bash
cd ~/quant_stock_rank
git pull origin main
```

Você deve ver:
```
From https://github.com/edipo-dados/quant_stock_rank
 * branch            main       -> FETCH_HEAD
Updating de36573..81fcd98
Fast-forward
 53 files changed, 4143 insertions(+), 7786 deletions(-)
 ...
```

### Passo 3: Executar Deploy Automatizado

```bash
# Dar permissão de execução
chmod +x deploy/deploy_v2.7.0.sh
chmod +x deploy/validate_v2.7.0.sh

# Executar deploy
./deploy/deploy_v2.7.0.sh
```

O script irá:
1. ✅ Criar backup do banco
2. ✅ Verificar arquivos novos
3. ✅ Parar containers
4. ✅ Rebuild backend
5. ✅ Iniciar containers
6. ✅ Validar saúde do sistema
7. ✅ Executar pipeline
8. ✅ (Opcional) Executar backtest

### Passo 4: Validar Deploy

```bash
./deploy/validate_v2.7.0.sh
```

Deve mostrar:
```
✓ VALIDAÇÃO COMPLETA - SISTEMA OK
Testes Passados: 12
Avisos: 0
Testes Falhados: 0
```

### Passo 5: Testar Backtest Enhanced

```bash
docker exec -it quant-ranker-backend python scripts/run_enhanced_backtest.py
```

Verificar métricas:
- ✅ Sharpe Ratio: 0.53-0.62 (esperado)
- ✅ Volatilidade: ~15%
- ✅ Exposição setorial: < 30%

---

## 📋 Checklist de Deploy

### Antes do Deploy
- [ ] Conectado ao EC2
- [ ] Código atualizado (`git pull`)
- [ ] Backup criado
- [ ] Sistema atual funcionando

### Durante o Deploy
- [ ] Script executado sem erros
- [ ] Containers iniciados
- [ ] API respondendo
- [ ] Pipeline executado

### Após o Deploy
- [ ] Validação passou
- [ ] Backtest enhanced testado
- [ ] Métricas validadas
- [ ] Logs sem erros críticos

---

## 🎯 Resultados Esperados

### Métricas de Performance

| Métrica | v2.6.0 | v2.7.0 Esperado | Melhoria |
|---------|--------|-----------------|----------|
| **Sharpe Ratio** | 0.41 | 0.53-0.62 | +30-50% |
| **Volatilidade** | 15.62% | ~15.00% | Controlada |
| **Max Drawdown** | -18.01% | -15% a -16% | -10-15% |
| **Alpha** | 23.07% | Mais preciso | Validado |
| **Concentração** | Sem limite | Máx 30% | Diversificado |

### Melhorias Implementadas

1. **Correção Definitiva do Cálculo de Alpha**
   - Retornos diários alinhados
   - Risk-free rate convertida corretamente
   - Validações robustas

2. **Volatility Targeting**
   - Pesos ajustados pela volatilidade
   - Controle de volatilidade do portfólio
   - Melhoria esperada: +30-50% no Sharpe

3. **Limites de Exposição por Setor**
   - Máximo 30% por setor
   - Redistribuição automática
   - Melhor diversificação

---

## 📚 Documentação

### Guias de Deploy
- **Quick Start**: `DEPLOY_QUICKSTART_V2.7.0.md` (5 min)
- **Guia Completo**: `DEPLOY_V2.7.0.md` (30 min)
- **Checklist**: `deploy/PRE_DEPLOY_CHECKLIST_V2.7.0.md`

### Documentação Técnica
- **Melhorias**: `ROBUSTEZ_V2.7.0.md`
- **Changelog**: `CHANGELOG.md`
- **Regras**: `docs/REGRAS_E_CONFIGURACOES.md`
- **README**: `README.md`

### Scripts
- **Deploy**: `deploy/deploy_v2.7.0.sh`
- **Validação**: `deploy/validate_v2.7.0.sh`
- **Backtest**: `scripts/run_enhanced_backtest.py`

---

## 🔄 Rollback (se necessário)

Se algo der errado durante o deploy:

```bash
# Parar containers
docker-compose down

# Restaurar backup do banco
./deploy/restore-db.sh backups/quant_ranker_backup_YYYYMMDD.db

# Reverter código
git checkout v2.6.0
# OU
cd ..
rm -rf quant_stock_rank
mv quant_stock_rank_backup_v2.6.0 quant_stock_rank
cd quant_stock_rank

# Reiniciar
docker-compose up -d
```

**Tempo de rollback**: ~10 minutos

---

## ⏱️ Tempo Estimado

- **Atualização do código**: 2 minutos
- **Deploy automatizado**: 5-10 minutos
- **Validação**: 5 minutos
- **Testes**: 5 minutos
- **Total**: 15-30 minutos

---

## 📞 Suporte

### Em Caso de Problemas

1. **Verificar logs**:
   ```bash
   docker logs quant-ranker-backend --tail 100
   ```

2. **Verificar containers**:
   ```bash
   docker ps
   docker-compose ps
   ```

3. **Consultar troubleshooting**:
   - `DEPLOY_V2.7.0.md` - Seção Troubleshooting
   - `deploy/PRE_DEPLOY_CHECKLIST_V2.7.0.md`

4. **Rollback se necessário**:
   - Ver seção "Rollback" acima

### Contatos
- **Desenvolvedor**: [seu-contato]
- **Repositório**: https://github.com/edipo-dados/quant_stock_rank
- **Tag**: v2.7.0

---

## ✅ Conclusão

O código v2.7.0 foi commitado e enviado para o GitHub com sucesso. 

**Próximo passo**: Fazer deploy no EC2 seguindo as instruções acima.

**Tempo estimado total**: 15-30 minutos

**Risco**: Baixo (rollback disponível)

**Impacto esperado**: Alto (Sharpe +30-50%, melhor controle de risco)

---

**Data**: Março 2026  
**Versão**: 2.7.0  
**Status**: ✅ Pronto para Deploy  
**Commit**: 81fcd98  
**Tag**: v2.7.0
