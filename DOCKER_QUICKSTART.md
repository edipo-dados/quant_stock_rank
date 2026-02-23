# 🐳 Guia Rápido - Docker

## Pré-requisitos

- Docker Desktop instalado e rodando
- 4GB de RAM disponível
- 10GB de espaço em disco

## Iniciar o Sistema

```cmd
docker-start.bat
```

Isso irá:
1. Parar containers existentes
2. Construir as imagens Docker
3. Iniciar PostgreSQL, Backend e Frontend
4. Inicializar o banco de dados

Aguarde cerca de 30 segundos para tudo iniciar.

## Acessar o Sistema

- **Frontend**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
  - Usuário: `quant_user`
  - Senha: `quant_password`
  - Database: `quant_ranker`

## Rodar o Pipeline de Dados

```cmd
docker-pipeline.bat
```

Escolha uma das opções:
1. **Teste** - 5 ativos para teste rápido
2. **Líquidos** - Top 100 ativos mais líquidos da B3
3. **Manual** - Especificar tickers customizados

## Comandos Úteis

### Ver logs em tempo real
```cmd
docker-compose logs -f
```

### Ver logs de um serviço específico
```cmd
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Parar tudo
```cmd
docker-compose down
```

### Parar e remover volumes (limpa banco de dados)
```cmd
docker-compose down -v
```

### Reiniciar um serviço
```cmd
docker-compose restart backend
docker-compose restart frontend
```

### Acessar o shell do backend
```cmd
docker-compose exec backend bash
```

### Executar comandos no backend
```cmd
REM Rodar pipeline
docker-compose exec backend python scripts/run_pipeline.py --mode test

REM Verificar banco de dados
docker-compose exec backend python scripts/check_db.py

REM Inicializar banco (recriar tabelas)
docker-compose exec backend python scripts/init_db.py --drop
```

### Conectar ao PostgreSQL
```cmd
docker-compose exec postgres psql -U quant_user -d quant_ranker
```

Comandos SQL úteis:
```sql
-- Ver tabelas
\dt

-- Ver dados de uma tabela
SELECT * FROM scores_daily ORDER BY rank LIMIT 10;

-- Contar registros
SELECT COUNT(*) FROM raw_prices_daily;

-- Sair
\q
```

## Estrutura dos Containers

```
┌─────────────────────────────────────┐
│  Frontend (Streamlit)               │
│  Port: 8501                         │
│  Container: quant-ranker-frontend   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Backend (FastAPI)                  │
│  Port: 8000                         │
│  Container: quant-ranker-backend    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  PostgreSQL                         │
│  Port: 5432                         │
│  Container: quant-ranker-db         │
│  Volume: postgres_data              │
└─────────────────────────────────────┘
```

## Volumes Persistentes

Os dados são salvos em volumes Docker:
- `postgres_data` - Dados do PostgreSQL
- `backend_logs` - Logs do backend

Para limpar tudo:
```cmd
docker-compose down -v
```

## Troubleshooting

### Porta já em uso
```cmd
REM Verificar o que está usando a porta
netstat -ano | findstr :8000
netstat -ano | findstr :8501
netstat -ano | findstr :5432

REM Matar o processo
taskkill /PID [numero] /F
```

### Container não inicia
```cmd
REM Ver logs detalhados
docker-compose logs backend

REM Reconstruir imagem
docker-compose build --no-cache backend
docker-compose up -d
```

### Banco de dados corrompido
```cmd
REM Parar tudo e limpar volumes
docker-compose down -v

REM Iniciar novamente
docker-start.bat
```

### Erro de memória
```cmd
REM Limpar imagens não usadas
docker system prune -a

REM Aumentar memória no Docker Desktop
REM Settings > Resources > Memory > 4GB+
```

## Desenvolvimento

Para desenvolvimento com hot-reload:

```cmd
REM Os volumes já estão mapeados para hot-reload
REM Edite os arquivos em ./app ou ./frontend
REM As mudanças serão refletidas automaticamente
```

## Produção

Para deploy em produção, veja:
- `GUIA_DEPLOY.md` - Guia completo de deploy
- `deploy/` - Scripts e configurações para diferentes plataformas

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# PostgreSQL
POSTGRES_USER=quant_user
POSTGRES_PASSWORD=quant_password
POSTGRES_DB=quant_ranker
POSTGRES_PORT=5432

# API
API_PORT=8000
LOG_LEVEL=INFO

# Frontend
FRONTEND_PORT=8501

# Scoring Weights
MOMENTUM_WEIGHT=0.4
QUALITY_WEIGHT=0.3
VALUE_WEIGHT=0.3
```

## Próximos Passos

1. Execute `docker-start.bat`
2. Aguarde os serviços iniciarem
3. Execute `docker-pipeline.bat` para popular dados
4. Acesse http://localhost:8501
5. Explore o ranking de ações!
