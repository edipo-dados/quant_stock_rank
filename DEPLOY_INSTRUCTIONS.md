# 🚀 Instruções de Deploy - v2.7.1

## ✅ Correções Implementadas

### 1. Erro SQLite na Página de Research
**Problema**: Research Backtest page estava usando SQLite em vez de PostgreSQL
**Solução**: Adicionado comentário explícito no `docker-compose.yml` para garantir que DATABASE_URL seja configurado corretamente

### 2. Configuração de Cron Jobs
**Problema**: Suavização temporal não estava configurada para rodar automaticamente
**Solução**: Criado guia completo de configuração de cron jobs

## 📋 Próximos Passos no EC2

### 1. Atualizar Código

```bash
# Conectar ao EC2
ssh -i sua-chave.pem ubuntu@seu-ec2-ip

# Navegar para o diretório
cd ~/quant_stock_rank

# Pull das mudanças
git pull origin main
```

### 2. Rebuild do Frontend (Corrigir SQLite)

```bash
# Rebuild apenas o frontend
docker-compose build frontend

# Restart dos containers
docker-compose down
docker-compose up -d

# Aguardar containers iniciarem
sleep 30

# Verificar status
docker ps
```

### 3. Configurar Cron Jobs

```bash
# Editar crontab
crontab -e

# Adicionar as seguintes linhas:
# Pipeline diário às 19:00 (após fechamento do mercado)
0 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> /var/log/pipeline.log 2>&1

# Suavização temporal às 19:30 (30 min após pipeline)
30 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all >> /var/log/smoothing.log 2>&1

# Salvar e sair (ESC + :wq no vim, ou CTRL+X no nano)
```

### 4. Verificar Configuração

```bash
# Listar cron jobs configurados
crontab -l

# Criar diretório de logs se não existir
sudo mkdir -p /var/log
sudo touch /var/log/pipeline.log /var/log/smoothing.log
sudo chown ubuntu:ubuntu /var/log/pipeline.log /var/log/smoothing.log
```

### 5. Testar Execução Manual

```bash
# Testar pipeline
cd ~/quant_stock_rank
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50

# Aguardar pipeline terminar (2-3 minutos)

# Testar suavização
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all

# Verificar logs
tail -50 /var/log/pipeline.log
tail -50 /var/log/smoothing.log
```

### 6. Verificar Research Page

```bash
# Acessar frontend
http://seu-ec2-ip:8501

# Navegar para página "🔬 Research Backtest"
# Tentar executar um backtest
# Não deve mais aparecer erro de SQLite
```

## 📚 Documentação Criada

### 1. CRON_SETUP.md
Guia completo de configuração de cron jobs:
- Formato do cron explicado
- Exemplos de configuração
- Monitoramento de logs
- Troubleshooting
- Rotação de logs
- Alertas por email (opcional)

**Localização**: `deploy/CRON_SETUP.md`

### 2. Atualizações em Documentos Existentes

- **README.md**: Adicionado cron job de suavização
- **EC2_DEPLOY_V2.6.0.md**: Nova seção "Configurar Cron Jobs"
- **deploy/INDEX.md**: Referência ao CRON_SETUP.md
- **QUICK_REFERENCE.md**: Comandos de cron e suavização

## 🔍 Verificações Pós-Deploy

### Verificar Frontend Usando PostgreSQL

```bash
# Verificar variável de ambiente do frontend
docker exec quant-ranker-frontend env | grep DATABASE_URL

# Deve mostrar:
# DATABASE_URL=postgresql://quant_user:quant_password@postgres:5432/quant_ranker
```

### Verificar Cron Jobs

```bash
# Listar cron jobs
crontab -l

# Deve mostrar:
# 0 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50 >> /var/log/pipeline.log 2>&1
# 30 19 * * * cd ~/quant_stock_rank && docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all >> /var/log/smoothing.log 2>&1
```

### Verificar Logs

```bash
# Ver logs do pipeline (após primeira execução às 19:00)
tail -100 /var/log/pipeline.log

# Ver logs da suavização (após primeira execução às 19:30)
tail -100 /var/log/smoothing.log

# Monitorar em tempo real
tail -f /var/log/pipeline.log
```

## 📊 Cronograma de Execução

```
19:00 - Pipeline diário
        ├─ Atualiza dados do Yahoo Finance
        ├─ Calcula features (momentum, quality, value, size)
        ├─ Calcula scores
        └─ Salva no banco de dados

19:30 - Suavização temporal (30 min após pipeline)
        ├─ Lê scores do dia
        ├─ Aplica smoothing exponencial (alpha=0.7)
        ├─ Atualiza final_score_smoothed
        └─ Reduz turnover do portfólio
```

## 🎯 Benefícios da Suavização Temporal

1. **Reduz Turnover**: Menos mudanças bruscas no ranking
2. **Reduz Custos**: Menos transações = menos custos
3. **Melhora Sharpe**: Portfólio mais estável
4. **Mantém Performance**: Não sacrifica retorno

**Fórmula**:
```
final_score_smoothed = 0.7 * score_atual + 0.3 * score_anterior
```

## 🔧 Comandos Úteis

### Executar Pipeline Manualmente

```bash
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50
```

### Executar Suavização Manualmente

```bash
docker exec quant-ranker-backend python scripts/apply_temporal_smoothing.py --all
```

### Ver Scores Suavizados

```bash
docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily
from datetime import date

db = SessionLocal()
scores = db.query(ScoreDaily).filter(ScoreDaily.date == date.today()).limit(10).all()
print('Ticker | Raw Score | Smoothed Score')
print('-' * 40)
for s in scores:
    smoothed = s.final_score_smoothed if s.final_score_smoothed else s.final_score
    print(f'{s.ticker:8} | {s.final_score:9.3f} | {smoothed:14.3f}')
db.close()
"
```

### Verificar Última Execução do Cron

```bash
# Ver última linha do log
tail -1 /var/log/pipeline.log

# Ver última execução bem-sucedida
grep "COMPLETED" /var/log/pipeline.log | tail -1

# Ver erros
grep "ERROR" /var/log/pipeline.log | tail -10
```

## 🆘 Troubleshooting

### Cron não está executando

```bash
# Verificar se cron está rodando
sudo systemctl status cron

# Iniciar cron
sudo systemctl start cron
sudo systemctl enable cron
```

### Logs não são criados

```bash
# Criar logs manualmente
sudo touch /var/log/pipeline.log /var/log/smoothing.log
sudo chown ubuntu:ubuntu /var/log/pipeline.log /var/log/smoothing.log
sudo chmod 644 /var/log/pipeline.log /var/log/smoothing.log
```

### Research page ainda mostra erro SQLite

```bash
# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose down
docker-compose up -d

# Verificar variável de ambiente
docker exec quant-ranker-frontend env | grep DATABASE_URL
```

## 📝 Checklist Final

- [ ] Código atualizado (`git pull`)
- [ ] Frontend rebuilded
- [ ] Containers rodando (`docker ps`)
- [ ] Cron jobs configurados (`crontab -l`)
- [ ] Logs criados e com permissões corretas
- [ ] Pipeline testado manualmente
- [ ] Suavização testada manualmente
- [ ] Research page testada (sem erro SQLite)
- [ ] Primeira execução automática verificada (após 19:00)

## 🎉 Resultado Esperado

Após seguir todos os passos:

1. ✅ Research Backtest page funcionando sem erros
2. ✅ Pipeline executando automaticamente às 19:00
3. ✅ Suavização executando automaticamente às 19:30
4. ✅ Logs sendo gerados em `/var/log/`
5. ✅ Sistema totalmente automatizado

## 📞 Suporte

Para mais detalhes, consulte:
- **Cron Jobs**: `deploy/CRON_SETUP.md`
- **Deploy Completo**: `deploy/EC2_DEPLOY_V2.6.0.md`
- **Comandos Rápidos**: `deploy/QUICK_REFERENCE.md`
- **Índice de Deploy**: `deploy/INDEX.md`

---

**Versão**: v2.7.1  
**Data**: 27/02/2026  
**Commit**: 5b81326
