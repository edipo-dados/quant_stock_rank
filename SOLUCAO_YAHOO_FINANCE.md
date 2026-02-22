# 🔧 Solução para Yahoo Finance no Docker

## 🎯 Problema Identificado

O Yahoo Finance funciona perfeitamente na sua máquina local, mas falha dentro do Docker com erro **HTTP 429 (Too Many Requests)**.

### Por que isso acontece?

- **Localmente**: Sua máquina tem IP residencial, User-Agent normal, histórico de navegação
- **No Docker**: Container tem IP diferente, sem cookies, detectado como "bot" pelo Yahoo Finance
- **Resultado**: Yahoo Finance bloqueia requisições do Docker (rate limiting agressivo)

## ✅ Solução Recomendada: Pipeline Local + Docker para Servir

Execute o pipeline de dados **localmente** (onde Yahoo Finance funciona) e use o Docker apenas para servir a aplicação.

### Passo a Passo

#### 1. Executar Pipeline Localmente

```bash
# Certifique-se que o PostgreSQL está rodando no Docker
docker-compose up -d postgres

# Execute o pipeline na sua máquina local
python -m scripts.run_pipeline
```

O pipeline vai:
- ✅ Buscar dados do Yahoo Finance (funciona local!)
- ✅ Salvar no PostgreSQL (que está no Docker)
- ✅ Calcular features e scores
- ✅ Gerar rankings

#### 2. Iniciar Backend e Frontend no Docker

```bash
# Iniciar apenas backend e frontend (postgres já está rodando)
docker-compose up -d backend frontend
```

Agora o Docker vai:
- ✅ Ler dados do PostgreSQL (já populado pelo pipeline local)
- ✅ Servir a API
- ✅ Exibir o frontend

### Vantagens desta Abordagem

1. **Yahoo Finance funciona** - Pipeline roda localmente onde não há bloqueio
2. **Docker serve a aplicação** - Backend e Frontend em containers
3. **Dados persistentes** - PostgreSQL mantém os dados entre execuções
4. **Flexibilidade** - Você controla quando atualizar os dados

---

## 🔄 Workflow Recomendado

### Primeira Execução (Setup Inicial)

```bash
# 1. Subir PostgreSQL
docker-compose up -d postgres

# 2. Aguardar PostgreSQL ficar pronto (10-15 segundos)
timeout /t 15

# 3. Executar pipeline localmente
python -m scripts.run_pipeline

# 4. Subir backend e frontend
docker-compose up -d backend frontend

# 5. Acessar aplicação
start http://localhost:8501
```

### Atualizações Diárias de Dados

```bash
# Executar pipeline para atualizar dados
python -m scripts.run_pipeline

# Reiniciar backend para garantir cache limpo (opcional)
docker-compose restart backend
```

### Parar Tudo

```bash
docker-compose down
```

---

## 📝 Script Automatizado

Criei um script `run_local_pipeline.bat` para facilitar:

```batch
@echo off
echo ========================================
echo PIPELINE LOCAL + DOCKER
echo ========================================
echo.

echo [1/4] Verificando PostgreSQL...
docker-compose up -d postgres
timeout /t 15 /nobreak

echo.
echo [2/4] Executando pipeline local...
python -m scripts.run_pipeline

echo.
echo [3/4] Iniciando backend e frontend...
docker-compose up -d backend frontend

echo.
echo [4/4] Aguardando containers ficarem prontos...
timeout /t 20 /nobreak

echo.
echo ========================================
echo PRONTO!
echo ========================================
echo.
echo Acesse: http://localhost:8501
echo API Docs: http://localhost:8000/docs
echo.
pause
```

---

## 🎯 Alternativas (Caso queira tudo no Docker)

### Opção 1: Usar API Alternativa

Substituir Yahoo Finance por outra API que não tenha rate limiting tão agressivo:

- **Alpha Vantage** - 5 requisições/minuto (grátis)
- **IEX Cloud** - 50k requisições/mês (grátis)
- **Twelve Data** - 800 requisições/dia (grátis)

### Opção 2: Proxy/VPN no Docker

Configurar um proxy ou VPN dentro do container para mascarar o IP:

```yaml
backend:
  environment:
    HTTP_PROXY: http://seu-proxy:porta
    HTTPS_PROXY: http://seu-proxy:porta
```

### Opção 3: Cache de Dados

Implementar cache local dos dados do Yahoo Finance:

- Buscar dados 1x por dia
- Armazenar em arquivo local
- Reutilizar durante o dia

---

## ✅ Conclusão

A solução **Pipeline Local + Docker para Servir** é a mais simples e eficaz:

- ✅ Yahoo Finance funciona (local)
- ✅ Aplicação em Docker (fácil deploy)
- ✅ Dados persistentes (PostgreSQL)
- ✅ Sem custos adicionais
- ✅ Sem complexidade extra

**Recomendação**: Use esta abordagem e execute o pipeline localmente 1x por dia (ou quando quiser atualizar os dados).
