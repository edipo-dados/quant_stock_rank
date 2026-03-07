# Checklist Pré-Deploy v2.7.0

Verificações necessárias antes de fazer o deploy da versão 2.7.0.

## ✅ Checklist de Preparação

### 1. Ambiente

- [ ] Acesso SSH ao servidor EC2 funcionando
- [ ] Docker e Docker Compose instalados e funcionando
- [ ] Espaço em disco suficiente (mínimo 5GB livres)
- [ ] Memória RAM disponível (mínimo 2GB livres)
- [ ] Portas 8000 e 8501 disponíveis

**Verificar**:
```bash
ssh ubuntu@<ec2-ip> "docker --version && docker-compose --version"
ssh ubuntu@<ec2-ip> "df -h | grep -E 'Filesystem|/$'"
ssh ubuntu@<ec2-ip> "free -h"
ssh ubuntu@<ec2-ip> "netstat -tulpn | grep -E '8000|8501'"
```

### 2. Backup

- [ ] Backup do banco de dados criado
- [ ] Backup do código atual criado
- [ ] Backups testados (podem ser restaurados)
- [ ] Espaço suficiente para backups

**Executar**:
```bash
ssh ubuntu@<ec2-ip>
cd ~/quant_stock_rank
./deploy/backup-db.sh
ls -lh backups/
```

### 3. Código

- [ ] Todos os arquivos novos foram copiados para o servidor
- [ ] Todos os arquivos modificados foram atualizados
- [ ] Permissões dos arquivos estão corretas
- [ ] Scripts têm permissão de execução

**Arquivos Novos (3)**:
- [ ] `app/backtest/portfolio_risk.py`
- [ ] `scripts/run_enhanced_backtest.py`
- [ ] `ROBUSTEZ_V2.7.0.md`

**Arquivos Modificados (6)**:
- [ ] `app/config.py`
- [ ] `app/backtest/portfolio.py`
- [ ] `app/backtest/metrics.py`
- [ ] `app/backtest/backtest_engine.py`
- [ ] `README.md`
- [ ] `CHANGELOG.md`

**Verificar**:
```bash
ssh ubuntu@<ec2-ip> "cd ~/quant_stock_rank && ls -la app/backtest/portfolio_risk.py"
ssh ubuntu@<ec2-ip> "cd ~/quant_stock_rank && ls -la scripts/run_enhanced_backtest.py"
```

### 4. Configurações

- [ ] Arquivo `.env` existe e está configurado
- [ ] `FMP_API_KEY` está definida
- [ ] Configurações de risco revisadas em `app/config.py`
- [ ] Parâmetros de volatility targeting corretos
- [ ] Parâmetros de sector limits corretos

**Verificar**:
```bash
ssh ubuntu@<ec2-ip> "cd ~/quant_stock_rank && cat .env | grep FMP_API_KEY"
ssh ubuntu@<ec2-ip> "cd ~/quant_stock_rank && grep -A5 'use_volatility_targeting' app/config.py"
```

**Configurações Esperadas**:
```python
use_volatility_targeting: bool = True
target_portfolio_volatility: float = 0.15
volatility_lookback_days: int = 90
use_sector_limits: bool = True
max_sector_exposure: float = 0.30
```

### 5. Dados

- [ ] Banco de dados existe e está acessível
- [ ] Dados de preços estão atualizados
- [ ] Dados de fundamentalistas estão disponíveis
- [ ] Ranking snapshots existem (para backtest)
- [ ] Benchmark (IBOVESPA) está ingerido

**Verificar**:
```bash
ssh ubuntu@<ec2-ip> "cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/check_db.py"
ssh ubuntu@<ec2-ip> "cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/check_historical_coverage.py"
```

### 6. Sistema Atual

- [ ] Sistema atual está funcionando corretamente
- [ ] API está respondendo
- [ ] Frontend está acessível
- [ ] Pipeline está executando sem erros
- [ ] Logs não mostram erros críticos

**Verificar**:
```bash
ssh ubuntu@<ec2-ip> "curl -s http://localhost:8000/health"
ssh ubuntu@<ec2-ip> "curl -s http://localhost:8501"
ssh ubuntu@<ec2-ip> "docker logs quant-ranker-backend --tail 50"
```

### 7. Testes Locais

- [ ] Código foi testado localmente
- [ ] Backtest enhanced foi executado com sucesso
- [ ] Métricas estão dentro do esperado
- [ ] Não há erros de sintaxe Python
- [ ] Imports estão corretos

**Executar Localmente**:
```bash
# Testar sintaxe
python -m py_compile app/backtest/portfolio_risk.py
python -m py_compile scripts/run_enhanced_backtest.py

# Testar imports
python -c "from app.backtest.portfolio_risk import PortfolioRiskManager"
python -c "from app.backtest.portfolio import Portfolio"
```

### 8. Documentação

- [ ] CHANGELOG.md atualizado
- [ ] README.md atualizado
- [ ] ROBUSTEZ_V2.7.0.md criado
- [ ] DEPLOY_V2.7.0.md criado
- [ ] Documentação técnica revisada

### 9. Comunicação

- [ ] Equipe notificada sobre o deploy
- [ ] Janela de manutenção agendada (se necessário)
- [ ] Plano de rollback comunicado
- [ ] Contatos de emergência disponíveis

### 10. Plano de Rollback

- [ ] Procedimento de rollback documentado
- [ ] Backups testados e funcionando
- [ ] Tempo estimado de rollback conhecido (~10 min)
- [ ] Critérios de rollback definidos

**Critérios de Rollback**:
- API não responde após 5 minutos
- Erros críticos nos logs
- Pipeline falha completamente
- Backtest retorna métricas absurdas
- Performance degradada significativamente

## 📋 Checklist de Execução

### Durante o Deploy

- [ ] Notificar início do deploy
- [ ] Executar script de deploy: `./deploy/deploy_v2.7.0.sh`
- [ ] Monitorar logs em tempo real
- [ ] Verificar cada passo do script
- [ ] Anotar qualquer erro ou warning

### Pós-Deploy

- [ ] Verificar containers rodando
- [ ] Testar API endpoints
- [ ] Testar frontend
- [ ] Executar pipeline manualmente
- [ ] Executar backtest enhanced
- [ ] Validar métricas
- [ ] Verificar exposição setorial
- [ ] Monitorar logs por 30 minutos
- [ ] Notificar conclusão do deploy

## 🎯 Métricas de Sucesso

### Métricas Técnicas
- [ ] API response time < 500ms
- [ ] Pipeline execution time < 30 min
- [ ] Containers memory usage < 80%
- [ ] No critical errors in logs

### Métricas de Negócio
- [ ] Sharpe Ratio: 0.53-0.62 (esperado +30-50%)
- [ ] Volatilidade: ~15% (controlada)
- [ ] Max Drawdown: -15% a -16% (melhoria)
- [ ] Alpha: -50% a +50% (validado)
- [ ] Exposição setorial: < 30% por setor

## ⚠️ Sinais de Alerta

### Rollback Imediato Se:
- ❌ API não responde após 5 minutos
- ❌ Containers crasham repetidamente
- ❌ Erros de importação Python
- ❌ Banco de dados corrompido
- ❌ Pipeline falha completamente

### Investigar Se:
- ⚠️ Warnings nos logs
- ⚠️ Performance degradada (>20%)
- ⚠️ Métricas fora do esperado
- ⚠️ Exposição setorial > 35%
- ⚠️ Volatilidade > 18%

## 📞 Contatos de Emergência

- **Desenvolvedor**: [seu-contato]
- **DevOps**: [contato-devops]
- **Suporte AWS**: [suporte-aws]

## 📝 Notas Adicionais

### Tempo Estimado
- Preparação: 15 minutos
- Execução: 30 minutos
- Validação: 15 minutos
- **Total**: ~60 minutos

### Melhor Horário
- Fora do horário de mercado (após 18h)
- Evitar sextas-feiras
- Preferir terça ou quarta-feira

### Recursos Necessários
- Acesso SSH ao EC2
- Acesso ao repositório Git
- Permissões de admin no Docker
- Acesso aos logs

---

## ✅ Aprovação Final

- [ ] Todos os itens do checklist verificados
- [ ] Backups criados e testados
- [ ] Equipe notificada
- [ ] Plano de rollback pronto
- [ ] Janela de manutenção confirmada

**Aprovado por**: _______________  
**Data**: _______________  
**Horário**: _______________

---

**Versão**: 2.7.0  
**Data de Criação**: Março 2026  
**Última Atualização**: Março 2026
