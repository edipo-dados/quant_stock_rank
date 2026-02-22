# 🚀 Setup Ambiente Local - Guia Completo

## 📋 Pré-requisitos

Antes de começar, certifique-se que você tem instalado:

- ✅ **Python 3.11+** - [Download](https://www.python.org/downloads/)
- ✅ **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/) (apenas para PostgreSQL)
- ✅ **Git** - [Download](https://git-scm.com/downloads)

---

## 🔧 Setup Inicial (Executar 1x)

### 1. Instalar Dependências Python

```bash
pip install -r requirements.txt
```

### 2. Iniciar PostgreSQL no Docker

```bash
docker-compose up -d postgres
```

Aguarde 10-15 segundos para o PostgreSQL ficar pronto.

### 3. Inicializar Banco de Dados

```bash
python scripts/init_db.py
```

### 4. Executar Pipeline de Dados

```bash
python -m scripts.run_pipeline
```

Isso vai:
- Buscar dados do Yahoo Finance (preços + fundamentals)
- Calcular features (momentum, qualidade, valor)
- Calcular scores e rankings
- Salvar tudo no PostgreSQL

---

## ▶️ Iniciar Aplicação

Você precisa de **2 terminais** (ou use os scripts .bat):

### Terminal 1: Backend (FastAPI)

```bash
python -m uvicorn app.main:app --reload
```

Ou use o script:
```bash
start_backend.bat
```

**Acesse**: http://localhost:8000/docs

### Terminal 2: Frontend (Streamlit)

```bash
streamlit run frontend/streamlit_app.py
```

Ou use o script:
```bash
start_frontend.bat
```

**Acesse**: http://localhost:8501

---

## 🎯 Script Automatizado (Recomendado)

Execute tudo de uma vez:

```bash
start_local.bat
```

Este script vai:
1. ✅ Verificar/iniciar PostgreSQL
2. ✅ Inicializar banco de dados
3. ✅ Testar Yahoo Finance
4. ✅ Executar pipeline de dados
5. ✅ Preparar ambiente

Depois, execute em terminais separados:
- `start_backend.bat`
- `start_frontend.bat`

---

## 📊 Estrutura do Ambiente Local

```
┌─────────────────────────────────────────┐
│  Frontend (Streamlit)                   │
│  http://localhost:8501                  │
│  ↓ Consome API                          │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  Backend (FastAPI)                      │
│  http://localhost:8000                  │
│  ↓ Lê dados                             │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  PostgreSQL (Docker)                    │
│  localhost:5432                         │
│  User: quant_user                       │
│  Pass: quant_password                   │
│  DB: quant_ranker                       │
└─────────────────────────────────────────┘
```

---

## 🔄 Atualizar Dados

Para atualizar os dados com informações mais recentes:

```bash
python -m scripts.run_pipeline
```

Recomendação: Execute 1x por dia (após o fechamento do mercado).

---

## 🧪 Testar Componentes

### Testar Yahoo Finance

```bash
python test_yahoo_local.py
```

### Testar APIs Externas

```bash
python scripts/test_apis.py
```

### Testar Banco de Dados

```bash
python scripts/check_db.py
```

### Validar Features

```bash
python scripts/validate_features.py
```

---

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError"

**Solução**: Instale as dependências
```bash
pip install -r requirements.txt
```

### Erro: "Connection refused" (PostgreSQL)

**Solução**: Inicie o PostgreSQL
```bash
docker-compose up -d postgres
```

Aguarde 15 segundos e tente novamente.

### Erro: "No module named 'app'"

**Solução**: Execute comandos da raiz do projeto
```bash
cd C:\Users\Edipo\Recomendacoes_financeiras
python -m scripts.run_pipeline
```

### Erro: Yahoo Finance retorna dados vazios

**Solução**: Verifique sua conexão com internet e tente novamente. O Yahoo Finance pode ter rate limiting temporário.

### Frontend não conecta ao Backend

**Solução**: Verifique se o `.env` tem:
```
BACKEND_URL=http://localhost:8000
```

---

## 📁 Arquivos de Configuração

### `.env` (Configurações)

```env
DATABASE_URL=postgresql://quant_user:quant_password@localhost:5432/quant_ranker
BACKEND_URL=http://localhost:8000
MOMENTUM_WEIGHT=0.4
QUALITY_WEIGHT=0.3
VALUE_WEIGHT=0.3
```

### `requirements.txt` (Dependências)

Todas as bibliotecas Python necessárias.

---

## 🎯 Workflow Diário

### Manhã (Antes do Mercado)

```bash
# Atualizar dados
python -m scripts.run_pipeline

# Iniciar aplicação
start_backend.bat  # Terminal 1
start_frontend.bat # Terminal 2
```

### Durante o Dia

- Acesse http://localhost:8501
- Visualize rankings
- Analise ativos
- Gere relatórios

### Noite (Após Fechamento)

```bash
# Atualizar dados do dia
python -m scripts.run_pipeline
```

---

## 📊 Dados Disponíveis

Após executar o pipeline, você terá:

- **Preços Diários**: Últimos 365 dias
- **Fundamentals**: Dados anuais (últimos 5 anos)
- **Features**: Momentum, Qualidade, Valor
- **Scores**: Score final ponderado
- **Rankings**: Posição de cada ativo

---

## 🔒 Segurança

### Credenciais do Banco

- **User**: quant_user
- **Password**: quant_password
- **Database**: quant_ranker
- **Port**: 5432

⚠️ **Importante**: Estas são credenciais de desenvolvimento. Para produção, use credenciais seguras!

---

## 📝 Comandos Úteis

### Parar PostgreSQL

```bash
docker-compose down
```

### Ver Logs do PostgreSQL

```bash
docker logs quant-ranker-db
```

### Conectar ao PostgreSQL

```bash
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker
```

### Limpar Banco de Dados

```bash
python scripts/init_db.py --reset
```

---

## ✅ Checklist de Verificação

Antes de usar a aplicação, verifique:

- [ ] Python 3.11+ instalado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Docker Desktop rodando
- [ ] PostgreSQL iniciado (`docker-compose up -d postgres`)
- [ ] Banco inicializado (`python scripts/init_db.py`)
- [ ] Pipeline executado (`python -m scripts.run_pipeline`)
- [ ] Backend rodando (`start_backend.bat`)
- [ ] Frontend rodando (`start_frontend.bat`)
- [ ] Acesso ao frontend (http://localhost:8501)

---

## 🎉 Pronto!

Seu ambiente local está configurado e funcionando!

**Acesse**: http://localhost:8501

**Documentação da API**: http://localhost:8000/docs

---

## 📞 Suporte

Se encontrar problemas:

1. Verifique o checklist acima
2. Consulte a seção Troubleshooting
3. Verifique os logs dos componentes
4. Execute os scripts de teste

---

**Última atualização**: 2026-02-18
