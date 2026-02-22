# Melhorias - APIs Externas e Inicialização Automática

## 🎯 Objetivo

Configurar o sistema para:
1. Consumir dados de APIs externas (Yahoo Finance e FMP) automaticamente
2. Executar o pipeline de extração na inicialização do Docker
3. Usar dados de fallback se as APIs falharem

## 🔧 Implementações Realizadas

### 1. Script de Teste de APIs (`scripts/test_apis.py`)

Novo script que testa a conectividade com as APIs externas antes de executar o pipeline:

- **Yahoo Finance**: Testa buscando dados de AAPL (ticker americano confiável)
- **FMP API**: Testa buscando income statement de AAPL
- **Retorna códigos de status**:
  - `0`: Todas as APIs funcionando
  - `1`: Algumas APIs funcionando
  - `2`: Nenhuma API funcionando

### 2. Script de Entrypoint Docker (`scripts/docker_entrypoint.sh`)

Novo script que é executado automaticamente quando o container backend inicia:

**Fluxo de execução:**
1. Aguarda PostgreSQL estar pronto
2. Inicializa o banco de dados (cria tabelas)
3. Testa conectividade com APIs externas
4. Executa pipeline de extração de dados:
   - Se APIs funcionando: executa pipeline completo
   - Se APIs parcialmente funcionando: tenta pipeline
   - Se APIs não funcionando: usa dados de teste
5. Inicia a API FastAPI

### 3. Dockerfile Atualizado

O Dockerfile do backend foi atualizado para:
- Copiar o script de entrypoint
- Tornar o script executável
- Usar o script como CMD ao invés de uvicorn direto

### 4. Script de Inicialização Melhorado

O `start_sistema_completo.bat` foi atualizado para:
- Reconstruir a imagem do backend (para incluir o novo entrypoint)
- Aguardar 60 segundos para o sistema inicializar completamente
- Mostrar logs do backend para acompanhar o processo

## 📋 Como Usar

### Iniciar Sistema com Extração Automática

```bash
start_sistema_completo.bat
```

Este comando irá:
1. Parar containers existentes
2. Definir variáveis de ambiente
3. Reconstruir imagem do backend
4. Iniciar todos os containers
5. Aguardar inicialização (60s)

Durante a inicialização, o backend automaticamente:
- Inicializa o banco
- Testa APIs externas
- Executa pipeline de dados
- Insere dados de teste se necessário

### Verificar Logs da Inicialização

```bash
docker-compose logs backend
```

Você verá o processo completo:
```
[1/5] Aguardando PostgreSQL...
✓ PostgreSQL pronto!

[2/5] Inicializando banco de dados...
✓ Tabelas criadas

[3/5] Testando conectividade com APIs externas...
✓ Yahoo Finance OK
✗ FMP API FALHOU

[4/5] Executando pipeline de extração de dados...
⚠ Algumas APIs funcionando - tentando pipeline...
...

[5/5] Iniciando API FastAPI...
```

## 🔍 Diagnóstico de Problemas

### Yahoo Finance Falhando

**Sintomas:**
```
✗ Yahoo Finance FALHOU: No data returned for ticker PETR4.SA
```

**Possíveis Causas:**
1. Problema de rede/firewall
2. Rate limiting do Yahoo Finance
3. Ticker brasileiro não disponível

**Soluções:**
1. Testar com ticker americano: `AAPL`, `MSFT`, `GOOGL`
2. Aguardar alguns minutos e tentar novamente
3. Verificar conectividade de rede do container

### FMP API Falhando

**Sintomas:**
```
✗ FMP API FALHOU: HTTP error: 403 Client Error: Forbidden
```

**Possíveis Causas:**
1. Chave de API inválida ou expirada
2. Chave sem permissão para o endpoint
3. Limite de requisições excedido

**Soluções:**
1. Verificar chave da API no `.env`:
   ```
   FMP_API_KEY=sua_chave_aqui
   ```
2. Obter nova chave em: https://financialmodelingprep.com/developer/docs/
3. Verificar plano da API (free tier tem limitações)

### Testar APIs Manualmente

```bash
# Dentro do container
docker exec quant-ranker-backend python scripts/test_apis.py

# Ou localmente
python scripts/test_apis.py
```

## 📊 Comportamento com APIs Falhando

### Cenário 1: Todas as APIs Funcionando
- ✅ Pipeline executa normalmente
- ✅ Dados reais são extraídos
- ✅ Ranking gerado com dados atualizados

### Cenário 2: Algumas APIs Funcionando
- ⚠️ Pipeline tenta executar
- ⚠️ Usa dados disponíveis
- ⚠️ Pode ter dados incompletos

### Cenário 3: Nenhuma API Funcionando
- ✗ Pipeline não executa
- ✅ Dados de teste são inseridos
- ✅ Sistema funciona para demonstração

## 🔄 Executar Pipeline Manualmente

Se quiser executar o pipeline manualmente após o sistema iniciar:

```bash
# Executar pipeline completo
docker exec quant-ranker-backend python -m scripts.run_pipeline

# Ou inserir dados de teste
docker exec quant-ranker-backend python scripts/insert_test_data.py
```

## 📝 Configuração de Tickers

Os tickers são configurados no `scripts/run_pipeline.py`:

```python
TICKERS = [
    "PETR4.SA",  # Petrobras
    "VALE3.SA",  # Vale
    "ITUB4.SA",  # Itaú
    "BBDC4.SA",  # Bradesco
    "ABEV3.SA",  # Ambev
    "BBAS3.SA",  # Banco do Brasil
    "WEGE3.SA",  # WEG
    "RENT3.SA",  # Localiza
    "LREN3.SA",  # Lojas Renner
    "MGLU3.SA",  # Magazine Luiza
]
```

Para adicionar mais tickers, edite esta lista e reconstrua a imagem.

## 🚀 Próximos Passos

### Para Produção

1. **Obter Chaves de API Válidas**:
   - FMP API: https://financialmodelingprep.com/
   - Considerar plano pago para mais requisições

2. **Implementar Cache**:
   - Cachear dados de APIs para reduzir requisições
   - Usar Redis para cache distribuído

3. **Implementar Retry Logic**:
   - Retry automático com backoff exponencial
   - Fallback para dados cached

4. **Monitoramento**:
   - Alertas quando APIs falham
   - Métricas de sucesso/falha de extração
   - Dashboard de saúde do sistema

5. **Agendamento**:
   - Cron job para executar pipeline diariamente
   - Horário configurável (ex: após fechamento do mercado)

### Para Desenvolvimento

1. **Testes de Integração**:
   - Testes com mock das APIs
   - Testes de fallback

2. **Documentação**:
   - Documentar formato de dados das APIs
   - Documentar transformações aplicadas

3. **Validação de Dados**:
   - Validar qualidade dos dados extraídos
   - Alertar sobre dados inconsistentes

## 📞 Suporte

Se as APIs continuarem falhando:

1. Verifique os logs: `docker-compose logs backend`
2. Teste APIs manualmente: `docker exec quant-ranker-backend python scripts/test_apis.py`
3. Verifique conectividade: `docker exec quant-ranker-backend ping google.com`
4. Verifique variáveis de ambiente: `docker exec quant-ranker-backend printenv | grep FMP`

## ✅ Checklist de Validação

- [ ] Script de teste de APIs criado
- [ ] Script de entrypoint criado e executável
- [ ] Dockerfile atualizado para usar entrypoint
- [ ] Script de inicialização atualizado
- [ ] Documentação criada
- [ ] Sistema testado com APIs funcionando
- [ ] Sistema testado com APIs falhando
- [ ] Logs verificados
- [ ] Frontend acessível
- [ ] API respondendo
