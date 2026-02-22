# ✅ Render Deploy - Checklist Completo

## 📋 Pré-Deploy

- [ ] Código está no GitHub
- [ ] Conta criada no Render (https://render.com)
- [ ] Cartão de crédito adicionado (se usar planos pagos)
- [ ] Arquivos de configuração commitados:
  - [ ] `render.yaml`
  - [ ] `docker/Dockerfile.backend.render`
  - [ ] `docker/Dockerfile.frontend.render`
  - [ ] `scripts/render_init.sh`

---

## 🗄️ Passo 1: Database

- [ ] Acessar Dashboard do Render
- [ ] Clicar em "New +" → "PostgreSQL"
- [ ] Configurar:
  - [ ] Name: `quant-ranker-db`
  - [ ] Database: `quant_ranker`
  - [ ] User: `quant_user`
  - [ ] Region: Oregon (US West) ou Frankfurt
  - [ ] Plan: Starter ($7/mês) ou Free
- [ ] Clicar em "Create Database"
- [ ] Aguardar status "Available" (2-3 min)
- [ ] **COPIAR Internal Database URL** ⭐ IMPORTANTE

```
Internal Database URL copiada: ___________________________
```

---

## 🔧 Passo 2: Backend

- [ ] Dashboard → "New +" → "Web Service"
- [ ] Conectar repositório GitHub
- [ ] Selecionar: `Recomendacoes_financeiras`
- [ ] Configurar:
  - [ ] Name: `quant-ranker-backend`
  - [ ] Region: Oregon (mesmo do DB)
  - [ ] Branch: `main`
  - [ ] Environment: `Docker`
  - [ ] Dockerfile Path: `./docker/Dockerfile.backend.render`
  - [ ] Plan: Starter ($7/mês) ou Free
- [ ] Adicionar variáveis de ambiente:
  - [ ] `DATABASE_URL` = (Internal URL do Passo 1)
  - [ ] `MOMENTUM_WEIGHT` = `0.4`
  - [ ] `QUALITY_WEIGHT` = `0.3`
  - [ ] `VALUE_WEIGHT` = `0.3`
  - [ ] `API_HOST` = `0.0.0.0`
  - [ ] `API_PORT` = `8000`
  - [ ] `LOG_LEVEL` = `INFO`
- [ ] Health Check Path: `/health`
- [ ] Clicar em "Create Web Service"
- [ ] Aguardar build e deploy (5-10 min)
- [ ] Verificar status "Live"
- [ ] **COPIAR URL do Backend** ⭐ IMPORTANTE

```
Backend URL: ___________________________
```

- [ ] Testar no navegador: `https://[backend-url]/health`
- [ ] Deve retornar: `{"status":"healthy","version":"1.0.0"}`

---

## 🎨 Passo 3: Frontend

- [ ] Dashboard → "New +" → "Web Service"
- [ ] Conectar mesmo repositório
- [ ] Configurar:
  - [ ] Name: `quant-ranker-frontend`
  - [ ] Region: Oregon (mesmo do backend)
  - [ ] Branch: `main`
  - [ ] Environment: `Docker`
  - [ ] Dockerfile Path: `./docker/Dockerfile.frontend.render`
  - [ ] Plan: Starter ($7/mês) ou Free
- [ ] Adicionar variáveis de ambiente:
  - [ ] `BACKEND_URL` = (URL do Backend do Passo 2)
  - [ ] `FRONTEND_PORT` = `8501`
- [ ] Clicar em "Create Web Service"
- [ ] Aguardar build e deploy (5-10 min)
- [ ] Verificar status "Live"
- [ ] **COPIAR URL do Frontend** ⭐ IMPORTANTE

```
Frontend URL: ___________________________
```

- [ ] Testar no navegador: `https://[frontend-url]`
- [ ] Deve carregar a página inicial

---

## 📊 Passo 4: Inicializar Banco

- [ ] Ir para serviço `quant-ranker-backend`
- [ ] Clicar na aba "Shell"
- [ ] Executar comando:
```bash
python scripts/init_db.py
```
- [ ] Verificar mensagem de sucesso
- [ ] Tabelas criadas no banco

---

## ⏰ Passo 5: Pipeline (Cron Job)

- [ ] Dashboard → "New +" → "Cron Job"
- [ ] Conectar mesmo repositório
- [ ] Configurar:
  - [ ] Name: `quant-ranker-pipeline`
  - [ ] Region: Oregon
  - [ ] Branch: `main`
  - [ ] Environment: `Docker`
  - [ ] Dockerfile Path: `./docker/Dockerfile.backend.render`
  - [ ] Command: `python -m scripts.run_pipeline --mode liquid`
  - [ ] Schedule: `0 21 * * *` (21h UTC = 18h BRT)
- [ ] Adicionar MESMAS variáveis do backend:
  - [ ] `DATABASE_URL`
  - [ ] `MOMENTUM_WEIGHT`
  - [ ] `QUALITY_WEIGHT`
  - [ ] `VALUE_WEIGHT`
  - [ ] `LOG_LEVEL`
- [ ] Clicar em "Create Cron Job"
- [ ] Clicar em "Trigger Run" (executar manualmente)
- [ ] Aguardar execução (5-10 min)
- [ ] Verificar logs para confirmar sucesso

---

## ✅ Passo 6: Testes Finais

### Backend API

- [ ] Testar health: `https://[backend-url]/health`
- [ ] Testar docs: `https://[backend-url]/docs`
- [ ] Testar ranking: `https://[backend-url]/api/v1/ranking`
- [ ] Testar top 5: `https://[backend-url]/api/v1/top?limit=5`
- [ ] Verificar se retorna dados (não vazio)

### Frontend

- [ ] Abrir: `https://[frontend-url]`
- [ ] Página inicial carrega
- [ ] Menu lateral funciona
- [ ] Navegar para "🏆 Ranking"
- [ ] Ver lista de ativos
- [ ] Clicar em um ativo
- [ ] Ver detalhes do ativo

### Pipeline

- [ ] Verificar logs do Cron Job
- [ ] Confirmar que dados foram inseridos
- [ ] Verificar quantidade de registros no banco

---

## 📝 Pós-Deploy

### Documentar URLs

```
Frontend: https://___________________________
Backend: https://___________________________
API Docs: https://___________________________/docs
Database: (Internal URL - não expor)
```

### Configurações Opcionais

- [ ] Configurar domínio customizado
- [ ] Configurar monitoramento (UptimeRobot)
- [ ] Configurar alertas de erro (Sentry)
- [ ] Configurar backup adicional
- [ ] Adicionar README com URLs

### Segurança

- [ ] Verificar que DATABASE_URL não está exposta
- [ ] Verificar que secrets estão seguros
- [ ] Testar HTTPS (deve ser automático)
- [ ] Verificar CORS se necessário

---

## 💰 Custos Confirmados

```
PostgreSQL: $___/mês
Backend: $___/mês
Frontend: $___/mês
Cron Job: Grátis
─────────────────────
Total: $___/mês
```

---

## 🎉 Deploy Completo!

- [ ] Aplicação está no ar
- [ ] Todos os testes passaram
- [ ] URLs documentadas
- [ ] Custos confirmados
- [ ] Equipe notificada

---

## 📞 Suporte

Se algo não funcionou:

1. ✅ Verificar logs no Render
2. ✅ Consultar `deploy/RENDER_COMPLETO.md`
3. ✅ Consultar `deploy/RENDER_COMANDOS.md`
4. ✅ Pedir ajuda no chat

---

## 🔄 Próximas Atualizações

Para atualizar a aplicação:

1. Fazer commit e push no GitHub
2. Render detecta automaticamente
3. Faz redeploy automático
4. Verificar logs para confirmar

Ou:

1. Dashboard → Service
2. Botão "Manual Deploy"
3. Selecionar branch
4. Deploy

---

**Data do Deploy:** ___/___/______  
**Responsável:** ___________________________  
**Status:** ⬜ Em Progresso | ⬜ Completo | ⬜ Com Problemas

