# ⚡ Render - Quick Start Guide

## 🎯 Deploy em 10 Minutos

### Pré-requisitos
- ✅ Código no GitHub
- ✅ Conta no Render (https://render.com)

---

## 📝 Checklist Rápido

### 1️⃣ Criar Database (2 min)
```
Dashboard → New + → PostgreSQL
Name: quant-ranker-db
Plan: Starter ($7/mês)
```
**Copie a Internal Database URL!**

### 2️⃣ Deploy Backend (5 min)
```
Dashboard → New + → Web Service
Repository: Recomendacoes_financeiras
Name: quant-ranker-backend
Environment: Docker
Dockerfile: ./docker/Dockerfile.backend.render
Plan: Starter ($7/mês)
```

**Variáveis de Ambiente:**
```bash
DATABASE_URL = <Internal Database URL do passo 1>
MOMENTUM_WEIGHT = 0.4
QUALITY_WEIGHT = 0.3
VALUE_WEIGHT = 0.3
API_HOST = 0.0.0.0
API_PORT = 8000
LOG_LEVEL = INFO
```

**Health Check Path:** `/health`

### 3️⃣ Deploy Frontend (3 min)
```
Dashboard → New + → Web Service
Repository: Recomendacoes_financeiras
Name: quant-ranker-frontend
Environment: Docker
Dockerfile: ./docker/Dockerfile.frontend.render
Plan: Starter ($7/mês)
```

**Variáveis de Ambiente:**
```bash
BACKEND_URL = https://quant-ranker-backend.onrender.com
FRONTEND_PORT = 8501
```

### 4️⃣ Inicializar Banco (1 min)
```
Backend → Shell → Executar:
python scripts/init_db.py
```

### 5️⃣ Executar Pipeline (1 min)
```
Dashboard → New + → Cron Job
Name: quant-ranker-pipeline
Dockerfile: ./docker/Dockerfile.backend.render
Command: python -m scripts.run_pipeline --mode liquid
Schedule: 0 21 * * *
```

**Mesmas variáveis do Backend!**

Depois: **Trigger Run** manualmente para popular dados.

---

## ✅ Testar

### Backend
```
https://quant-ranker-backend.onrender.com/health
https://quant-ranker-backend.onrender.com/docs
https://quant-ranker-backend.onrender.com/api/v1/ranking
```

### Frontend
```
https://quant-ranker-frontend.onrender.com
```

---

## 💰 Custo Total

```
PostgreSQL Starter: $7/mês
Backend Starter: $7/mês
Frontend Starter: $7/mês
Cron Job: Grátis
─────────────────────────
Total: $21/mês
```

---

## 🐛 Problemas Comuns

### Backend não inicia
- ✅ Verifique DATABASE_URL (use Internal, não External)
- ✅ Aguarde 5-10 min no primeiro deploy

### Frontend não mostra dados
- ✅ Verifique BACKEND_URL no frontend
- ✅ Execute init_db.py no backend
- ✅ Execute pipeline manualmente

### Build falha
- ✅ Verifique caminho do Dockerfile
- ✅ Veja logs de build para erro específico

---

## 📞 Ajuda

Documentação completa: `deploy/RENDER_COMPLETO.md`

