# Checklist de Teste de Deployment Docker

**Valida: Requisitos 13.6, 13.9**

Use este checklist para validar manualmente o deployment Docker.

## Pré-requisitos

- [ ] Docker Desktop instalado
- [ ] Docker Desktop está rodando
- [ ] Arquivo `.env` configurado com `FMP_API_KEY`

## 1. Inicialização dos Serviços

### 1.1 Iniciar Docker Compose

```bash
docker-compose up -d --build
```

- [ ] Comando executou sem erros
- [ ] Aguardou 1-2 minutos para serviços iniciarem

### 1.2 Verificar Status dos Serviços

```bash
docker-compose ps
```

Verificar que os seguintes serviços estão com status "Up":
- [ ] `quant-ranker-db` (postgres)
- [ ] `quant-ranker-backend` (backend)
- [ ] `quant-ranker-frontend` (frontend)

### 1.3 Verificar Logs (Opcional)

```bash
docker-compose logs
```

- [ ] Nenhum erro crítico nos logs
- [ ] Backend mostra "Starting Quant Stock Ranker API"
- [ ] Frontend mostra "You can now view your Streamlit app"

## 2. Testes do Backend API

### 2.1 Health Check

```bash
curl http://localhost:8000/health
```

Resposta esperada:
```json
{"status": "healthy", "version": "1.0.0"}
```

- [ ] Retornou status 200
- [ ] JSON contém "status": "healthy"

### 2.2 Documentação da API

Abrir no navegador: http://localhost:8000/docs

- [ ] Página Swagger UI carregou
- [ ] Endpoints visíveis: /ranking, /asset/{ticker}, /top

### 2.3 Endpoint /ranking

```bash
curl http://localhost:8000/api/v1/ranking
```

- [ ] Retornou 200 (com dados) ou 404 (banco vazio) - ambos OK

### 2.4 Endpoint /top

```bash
curl http://localhost:8000/api/v1/top?n=5
```

- [ ] Retornou 200 (com dados) ou 404 (banco vazio) - ambos OK

### 2.5 Endpoint /asset (ticker inválido)

```bash
curl http://localhost:8000/api/v1/asset/INVALID
```

- [ ] Retornou 404
- [ ] Mensagem de erro apropriada

## 3. Testes do Frontend

### 3.1 Página Principal

Abrir no navegador: http://localhost:8501

- [ ] Página carregou
- [ ] Título "Sistema de Ranking Quantitativo" visível
- [ ] Sidebar com navegação visível

### 3.2 Página de Ranking

Clicar em "🏆 Ranking" na sidebar

- [ ] Página carregou
- [ ] Mostra mensagem apropriada (dados ou "sem dados")

### 3.3 Página de Detalhes

Clicar em "📊 Detalhes do Ativo" na sidebar

- [ ] Página carregou
- [ ] Campo de input para ticker visível

## 4. Testes de Conectividade

### 4.1 Conectividade Backend → PostgreSQL

```bash
docker exec -it quant-ranker-backend python -c "from app.models.database import engine; engine.connect(); print('OK')"
```

- [ ] Imprimiu "OK"
- [ ] Sem erros de conexão

### 4.2 Conectividade Frontend → Backend

```bash
docker exec -it quant-ranker-frontend curl http://backend:8000/health
```

- [ ] Retornou JSON com status healthy
- [ ] Sem erros de conexão

### 4.3 Acesso Direto ao PostgreSQL

```bash
docker exec -it quant-ranker-db psql -U quant_user -d quant_ranker -c "\dt"
```

- [ ] Listou tabelas do banco
- [ ] Tabelas esperadas presentes: raw_prices_daily, raw_fundamentals, features_daily, features_monthly, scores_daily

## 5. Testes Automatizados

### 5.1 Executar Script de Teste

```bash
python scripts/test_docker_deployment.py
```

- [ ] Todos os testes passaram
- [ ] Taxa de sucesso: 100%

### 5.2 Executar Testes Unitários (Opcional)

```bash
docker exec -it quant-ranker-backend pytest tests/unit/ -v
```

- [ ] Testes executaram
- [ ] Maioria dos testes passou

## 6. Testes de Health Checks

### 6.1 Health Check do Backend

```bash
docker inspect quant-ranker-backend | grep -A 10 Health
```

- [ ] Health status: healthy

### 6.2 Health Check do Frontend

```bash
docker inspect quant-ranker-frontend | grep -A 10 Health
```

- [ ] Health status: healthy

### 6.3 Health Check do PostgreSQL

```bash
docker inspect quant-ranker-db | grep -A 10 Health
```

- [ ] Health status: healthy

## 7. Testes de Volumes e Persistência

### 7.1 Verificar Volumes

```bash
docker volume ls | grep quant
```

- [ ] Volume `postgres_data` existe
- [ ] Volume `backend_logs` existe

### 7.2 Teste de Persistência (Opcional)

1. Popular banco com dados de teste
2. Parar serviços: `docker-compose down`
3. Iniciar serviços: `docker-compose up -d`
4. Verificar que dados persistiram

- [ ] Dados persistiram após restart

## 8. Limpeza

### 8.1 Parar Serviços

```bash
docker-compose down
```

- [ ] Todos os containers pararam
- [ ] Comando executou sem erros

### 8.2 Limpar Volumes (Opcional)

```bash
docker-compose down -v
```

- [ ] Volumes removidos
- [ ] Banco de dados limpo

## Resumo

Total de verificações: _____ / _____

Status geral:
- [ ] ✅ Todos os testes passaram - Deployment OK
- [ ] ⚠️ Alguns testes falharam - Revisar logs
- [ ] ❌ Muitos testes falharam - Investigar problemas

## Problemas Encontrados

Liste aqui quaisquer problemas encontrados durante os testes:

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

## Notas Adicionais

_______________________________________________
_______________________________________________
_______________________________________________

---

**Data do Teste:** _______________
**Testado por:** _______________
**Versão do Docker:** _______________
**Sistema Operacional:** _______________
