# Guia de Teste de Deployment Docker

Este documento descreve como testar o deployment local com Docker Compose.

**Valida: Requisitos 13.6, 13.9**

## Pré-requisitos

1. Docker Desktop instalado e rodando
2. Arquivo `.env` configurado com as variáveis necessárias (especialmente `FMP_API_KEY`)

## Opção 1: Teste Automatizado (Recomendado)

Execute o script de teste automatizado:

```bash
# Windows
test_docker.bat

# Linux/Mac
chmod +x test_docker.sh
./test_docker.sh
```

O script irá:
1. Verificar se Docker está rodando
2. Parar containers existentes
3. Iniciar todos os serviços (postgres, backend, frontend)
4. Aguardar serviços ficarem prontos
5. Executar testes automatizados

## Opção 2: Teste Manual

### 1. Iniciar Serviços

```bash
docker-compose up -d --build
```

Aguarde 1-2 minutos para os serviços iniciarem completamente.

### 2. Verificar Status dos Serviços

```bash
docker-compose ps
```

Você deve ver 3 serviços rodando:
- `quant-ranker-db` (postgres)
- `quant-ranker-backend` (backend)
- `quant-ranker-frontend` (frontend)

### 3. Verificar Logs

```bash
# Ver logs de todos os serviços
docker-compose logs

# Ver logs de um serviço específico
docker-compose logs postgres
docker-compose logs backend
docker-compose logs frontend

# Seguir logs em tempo real
docker-compose logs -f backend
```

### 4. Testar Backend API

#### Health Check
```bash
curl http://localhost:8000/health
```

Resposta esperada:
```json
{"status": "healthy", "version": "1.0.0"}
```

#### Endpoint /ranking
```bash
curl http://localhost:8000/api/v1/ranking
```

Se o banco estiver vazio, retornará 404. Isso é esperado.

#### Endpoint /top
```bash
curl http://localhost:8000/api/v1/top?n=5
```

#### Documentação da API
Abra no navegador: http://localhost:8000/docs

### 5. Testar Frontend

Abra no navegador: http://localhost:8501

Você deve ver a interface Streamlit com:
- Página de Ranking
- Página de Detalhes do Ativo

### 6. Testar Conectividade do Banco de Dados

```bash
# Conectar ao PostgreSQL
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker

# Dentro do psql, listar tabelas
\dt

# Sair
\q
```

### 7. Executar Script de Teste Python

```bash
python scripts/test_docker_deployment.py
```

Este script executa testes automatizados de todos os componentes.

## Testes Esperados

O script de teste verifica:

1. **Docker está rodando** ✓
2. **Serviços do docker-compose**:
   - postgres está rodando ✓
   - backend está rodando ✓
   - frontend está rodando ✓
3. **Serviços ficam prontos**:
   - Backend responde em /health ✓
   - Frontend responde em /_stcore/health ✓
4. **Endpoints da API**:
   - GET /health retorna 200 ✓
   - GET /ranking retorna 200 ou 404 (se vazio) ✓
   - GET /top retorna 200 ou 404 (se vazio) ✓
   - GET /asset/INVALID retorna 404 ✓
5. **Frontend**:
   - Health check retorna 200 ✓
   - Página principal carrega ✓

## Populando o Banco com Dados de Teste

Para testar com dados reais:

```bash
# Entrar no container do backend
docker exec -it quant-ranker-backend bash

# Executar pipeline de ingestão
python scripts/run_pipeline.py --tickers PETR4.SA VALE3.SA ITUB4.SA --days 365

# Sair do container
exit
```

Após popular o banco, os endpoints /ranking e /top retornarão dados.

## Parar Serviços

```bash
# Parar serviços mantendo volumes
docker-compose down

# Parar serviços e remover volumes (limpa banco de dados)
docker-compose down -v
```

## Troubleshooting

### Serviço não inicia

```bash
# Ver logs detalhados
docker-compose logs backend

# Verificar health check
docker inspect quant-ranker-backend | grep -A 10 Health
```

### Erro de conexão com banco de dados

```bash
# Verificar se postgres está rodando
docker-compose ps postgres

# Ver logs do postgres
docker-compose logs postgres

# Testar conexão
docker exec -it quant-ranker-db pg_isready -U quant_user
```

### Frontend não carrega

```bash
# Ver logs do frontend
docker-compose logs frontend

# Verificar se backend está acessível do frontend
docker exec -it quant-ranker-frontend curl http://backend:8000/health
```

### Porta já em uso

Se alguma porta (5432, 8000, 8501) já estiver em uso, edite o arquivo `.env`:

```env
POSTGRES_PORT=5433
API_PORT=8001
FRONTEND_PORT=8502
```

E reinicie os serviços:

```bash
docker-compose down
docker-compose up -d
```

## Estrutura de Rede

Os serviços se comunicam através da rede `quant-network`:

```
┌─────────────────────────────────────────┐
│         quant-network (bridge)          │
│                                         │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │ postgres │  │ backend  │  │frontend││
│  │  :5432   │◄─┤  :8000   │◄─┤ :8501  ││
│  └──────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────┘
         │              │            │
         └──────────────┴────────────┘
              Portas expostas no host
```

## Volumes Persistentes

- `postgres_data`: Dados do PostgreSQL
- `backend_logs`: Logs do backend

Para limpar volumes:

```bash
docker-compose down -v
```

## Próximos Passos

Após validar o deployment local:

1. Configure CI/CD para build automático das imagens
2. Faça push das imagens para um registry (Docker Hub, AWS ECR, etc)
3. Configure deployment em ambiente de produção (AWS ECS, Kubernetes, etc)
4. Configure monitoramento e alertas
5. Configure backups automáticos do banco de dados

## Referências

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Streamlit Deployment](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app)
