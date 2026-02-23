# 🚀 Como Usar o Sistema com Docker

## Instalação Completa ✅

Tudo já está configurado! Você tem:

### Arquivos Docker
- ✅ `docker-compose.yml` - Configuração com PostgreSQL, Backend e Frontend
- ✅ `docker/Dockerfile.backend` - Imagem do backend com FastAPI
- ✅ `docker/Dockerfile.frontend` - Imagem do frontend com Streamlit

### Scripts Prontos
- ✅ `docker-start.bat` - Inicia todo o sistema
- ✅ `docker-stop.bat` - Para todo o sistema
- ✅ `docker-pipeline.bat` - Executa o pipeline de dados

## Uso Rápido (3 Passos)

### 1️⃣ Iniciar o Sistema
```cmd
docker-start.bat
```
Aguarde ~30 segundos

### 2️⃣ Rodar o Pipeline
```cmd
docker-pipeline.bat
```
Escolha opção 1 (Teste) para começar

### 3️⃣ Acessar
Abra no navegador: http://localhost:8501

## O que Acontece ao Iniciar?

```
1. PostgreSQL inicia (porta 5432)
   ↓
2. Backend inicia e cria tabelas (porta 8000)
   ↓
3. Frontend inicia (porta 8501)
   ↓
4. Sistema pronto! 🎉
```

## Arquitetura

```
┌──────────────────┐
│   Seu Browser    │
│  localhost:8501  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│    Streamlit     │  Container: quant-ranker-frontend
│   (Frontend)     │  Porta: 8501
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│     FastAPI      │  Container: quant-ranker-backend
│    (Backend)     │  Porta: 8000
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   PostgreSQL     │  Container: quant-ranker-db
│   (Database)     │  Porta: 5432
│                  │  Volume: postgres_data (persistente)
└──────────────────┘
```

## Comandos Essenciais

### Iniciar
```cmd
docker-start.bat
```

### Parar
```cmd
docker-stop.bat
```

### Ver Logs
```cmd
docker-compose logs -f
```

### Rodar Pipeline
```cmd
docker-pipeline.bat
```

### Reiniciar Tudo
```cmd
docker-compose restart
```

### Limpar Tudo (incluindo dados)
```cmd
docker-compose down -v
docker-start.bat
```

## URLs Importantes

| Serviço | URL | Descrição |
|---------|-----|-----------|
| Frontend | http://localhost:8501 | Interface web |
| API Docs | http://localhost:8000/docs | Documentação da API |
| API Health | http://localhost:8000/health | Status da API |
| PostgreSQL | localhost:5432 | Banco de dados |

## Credenciais PostgreSQL

```
Host: localhost
Port: 5432
User: quant_user
Password: quant_password
Database: quant_ranker
```

## Opções do Pipeline

### Modo Teste (Recomendado para começar)
```cmd
docker-pipeline.bat
# Escolha opção 1
```
Processa 5 ativos: ITUB4, BBDC4, PETR4, MGLU3, AMER3

### Modo Líquidos (Produção)
```cmd
docker-pipeline.bat
# Escolha opção 2
# Digite: 100 (ou outro número)
```
Processa os 100 ativos mais líquidos da B3

### Modo Manual (Customizado)
```cmd
docker-pipeline.bat
# Escolha opção 3
# Digite: PETR4.SA VALE3.SA ITUB4.SA
```

## Verificar se Está Funcionando

### 1. Verificar containers
```cmd
docker-compose ps
```
Todos devem estar "Up"

### 2. Testar API
Abra no navegador: http://localhost:8000/docs

### 3. Testar Frontend
Abra no navegador: http://localhost:8501

### 4. Ver dados no banco
```cmd
docker-compose exec postgres psql -U quant_user -d quant_ranker -c "SELECT COUNT(*) FROM scores_daily;"
```

## Problemas Comuns

### "Porta já em uso"
```cmd
# Parar tudo
docker-compose down

# Verificar portas
netstat -ano | findstr :8000
netstat -ano | findstr :8501
netstat -ano | findstr :5432

# Matar processo se necessário
taskkill /PID [numero] /F
```

### "Container não inicia"
```cmd
# Ver logs
docker-compose logs backend

# Reconstruir
docker-compose build --no-cache
docker-compose up -d
```

### "Sem dados no frontend"
```cmd
# Rodar pipeline
docker-pipeline.bat
# Escolha opção 1
```

### "Erro de memória"
```cmd
# Limpar Docker
docker system prune -a

# Aumentar memória no Docker Desktop
# Settings > Resources > Memory > 4GB+
```

## Desenvolvimento

Os arquivos estão mapeados para hot-reload:
- Edite `./app/*` → Backend recarrega automaticamente
- Edite `./frontend/*` → Frontend recarrega automaticamente

## Dados Persistentes

Os dados do PostgreSQL são salvos em um volume Docker persistente.

Para limpar tudo:
```cmd
docker-compose down -v
```

Para backup:
```cmd
docker-compose exec postgres pg_dump -U quant_user quant_ranker > backup.sql
```

Para restaurar:
```cmd
docker-compose exec -T postgres psql -U quant_user quant_ranker < backup.sql
```

## Próximos Passos

1. ✅ Execute `docker-start.bat`
2. ✅ Execute `docker-pipeline.bat` (opção 1)
3. ✅ Acesse http://localhost:8501
4. ✅ Explore o ranking!
5. 🎯 Customize os pesos em `.env`
6. 🎯 Rode com mais ativos (opção 2)
7. 🎯 Agende execução diária

## Suporte

- Documentação completa: `DOCKER_QUICKSTART.md`
- Guia de deploy: `GUIA_DEPLOY.md`
- README principal: `README.md`

---

**Dica**: Mantenha o Docker Desktop aberto enquanto usa o sistema!
