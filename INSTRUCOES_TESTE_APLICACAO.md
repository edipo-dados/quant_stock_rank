# Instruções para Testar a Aplicação

## ✅ Status do Sistema

Todos os serviços estão rodando e prontos para teste:

- **PostgreSQL**: ✅ Rodando e saudável (porta 5432)
- **Backend API**: ✅ Rodando e saudável (porta 8000)
- **Frontend Streamlit**: ✅ Rodando (porta 8501)

## 🌐 Como Acessar

### 1. Frontend (Interface Principal)
**URL**: http://localhost:8501

A interface Streamlit oferece:
- **Página Inicial**: Visão geral do sistema e metodologia
- **🏆 Ranking**: Lista completa de ativos rankeados por score
- **📊 Detalhes do Ativo**: Análise detalhada de cada ativo

### 2. Backend API (Documentação Swagger)
**URL**: http://localhost:8000/docs

Documentação interativa da API com todos os endpoints disponíveis.

### 3. Health Check
**URL**: http://localhost:8000/health

Verifica se a API está respondendo corretamente.

## 📊 Dados de Teste

O sistema está populado com dados de teste para 5 ativos:

1. **PETR4.SA** - Rank 1 (Score: 0.85)
2. **VALE3.SA** - Rank 2 (Score: 0.78)
3. **ITUB4.SA** - Rank 3 (Score: 0.72)
4. **BBDC4.SA** - Rank 4 (Score: 0.65)
5. **WEGE3.SA** - Rank 5 (Score: 0.58)

## 🧪 Endpoints da API

Todos os endpoints estão disponíveis em `/api/v1/`:

### GET /api/v1/ranking
Lista completa do ranking de ativos.

**Exemplo**:
```bash
curl http://localhost:8000/api/v1/ranking
```

**Resposta**:
```json
{
  "date": "2026-02-18",
  "rankings": [
    {
      "ticker": "PETR4.SA",
      "final_score": 0.85,
      "breakdown": {
        "momentum_score": 0.90,
        "quality_score": 0.80,
        "value_score": 0.85
      },
      "confidence": 0.95,
      "rank": 1
    },
    ...
  ],
  "total_assets": 5
}
```

### GET /api/v1/asset/{ticker}
Detalhes completos de um ativo específico.

**Exemplo**:
```bash
curl http://localhost:8000/api/v1/asset/PETR4.SA
```

### GET /api/v1/top?n=3
Top N ativos do ranking.

**Exemplo**:
```bash
curl http://localhost:8000/api/v1/top?n=3
```

## 🔧 Comandos Úteis

### Iniciar Sistema Completo (COM VARIÁVEIS CORRETAS)
```bash
# No PowerShell, defina as variáveis antes de iniciar:
$env:FMP_API_KEY="fNVVAjv4Jlkl7Js2VbCRm7bBivEEQDc3"
$env:BACKEND_URL="http://backend:8000"
docker-compose up -d

# Aguarde os containers iniciarem (cerca de 20 segundos)
timeout /t 20 /nobreak

# Inicialize o banco e insira dados de teste
docker exec quant-ranker-backend python scripts/init_db.py
docker exec quant-ranker-backend python scripts/insert_test_data.py
```

### Verificar Status dos Containers
```bash
docker-compose ps
```

### Ver Logs do Backend
```bash
docker-compose logs backend
```

### Ver Logs do Frontend
```bash
docker-compose logs frontend
```

### Reiniciar Serviços
```bash
docker-compose restart backend frontend
```

### Parar Todos os Serviços
```bash
docker-compose down
```

### Iniciar Todos os Serviços
```bash
docker-compose up -d
```

## 📝 Notas Importantes

### Problema com APIs Externas
As APIs externas (Yahoo Finance e Financial Modeling Prep) não estão retornando dados devido a:
- Yahoo Finance: Problemas de rede ou bloqueio
- FMP API: Chave pode estar expirada ou sem permissão para ações brasileiras (erro 403)

Por isso, foram inseridos dados de teste manualmente no banco de dados para demonstração.

### Configuração de Rede Docker
O frontend se conecta ao backend usando o nome do serviço Docker (`backend`) ao invés de `localhost`. Isso é configurado pela variável de ambiente `BACKEND_URL=http://backend:8000` no arquivo `.env`.

### Estrutura da API
Todos os endpoints da API estão sob o prefixo `/api/v1/` conforme definido no `app/main.py`.

## ✨ Funcionalidades para Testar

1. **Visualizar Ranking Completo**
   - Acesse http://localhost:8501
   - Navegue para "🏆 Ranking"
   - Veja a tabela com todos os ativos ordenados por score

2. **Ver Detalhes de um Ativo**
   - Na página de ranking, clique em um ticker
   - Ou navegue para "📊 Detalhes do Ativo"
   - Digite um ticker (ex: PETR4.SA)

3. **Testar API Diretamente**
   - Acesse http://localhost:8000/docs
   - Teste os endpoints interativamente
   - Veja os schemas de request/response

4. **Verificar Health Check**
   - Acesse http://localhost:8000/health
   - Deve retornar: `{"status": "healthy", "version": "1.0.0"}`

## 🎯 Validação Completa

Para validar que o sistema está funcionando corretamente:

1. ✅ Todos os containers estão rodando (postgres, backend, frontend)
2. ✅ Backend responde no health check
3. ✅ API retorna dados de ranking
4. ✅ Frontend carrega e exibe o ranking
5. ✅ Detalhes de ativos são exibidos corretamente

## 🐛 Troubleshooting

### Frontend não carrega dados
- Verifique se o backend está rodando: `docker-compose ps`
- Verifique os logs do frontend: `docker-compose logs frontend`
- Teste a API diretamente: `curl http://localhost:8000/api/v1/ranking`

### API retorna erro 500
- Verifique os logs do backend: `docker-compose logs backend`
- Verifique se o PostgreSQL está rodando: `docker-compose ps postgres`

### Containers não iniciam
- Verifique se as portas 5432, 8000 e 8501 estão disponíveis
- Reinicie o Docker Desktop
- Execute: `docker-compose down && docker-compose up -d`

## 📞 Suporte

Se encontrar problemas, verifique:
1. Logs dos containers: `docker-compose logs [service]`
2. Status dos containers: `docker-compose ps`
3. Conectividade de rede: `docker network ls`
