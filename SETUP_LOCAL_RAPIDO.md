# Setup Local Rápido - Quant Stock Ranker

## Status Atual

✅ Banco de dados SQLite configurado  
✅ Yahoo Finance funcionando (preços)  
⚠️ Dados fundamentalistas com problemas de mapeamento  
⚠️ Cálculo de scores falhando devido a dados None  

## Como Rodar Localmente

### 1. Configurar Ambiente

```bash
# Definir variável de ambiente para SQLite
set DATABASE_URL=sqlite:///./quant_ranker.db
set PYTHONPATH=.
```

### 2. Inicializar Banco de Dados

```bash
python scripts/init_db.py
```

### 3. Testar API (sem dados)

```bash
# Terminal 1: Iniciar API
uvicorn app.main:app --reload

# Terminal 2: Testar endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/ranking
```

### 4. Testar Frontend (sem dados)

```bash
cd frontend
streamlit run streamlit_app.py
```

## Problemas Conhecidos

### 1. Dados Fundamentalistas Retornam None

**Causa**: O mapeamento entre os campos do Yahoo Finance e o banco de dados está incorreto.

**Campos afetados**:
- revenue → None
- net_income → None  
- ebitda → None
- eps → None
- total_assets → None
- total_debt → None
- shareholders_equity → None
- operating_cash_flow → None
- free_cash_flow → None

**Impacto**: 
- Fatores fundamentalistas não são calculados
- Scores não são gerados
- Ranking fica vazio

**Solução necessária**: 
Corrigir o mapeamento em `app/ingestion/ingestion_service.py` método `_create_fundamental_record()` para usar os nomes corretos dos campos retornados pelo Yahoo Finance.

### 2. Return 12m Não Calculado

**Causa**: Precisamos de 252 dias de dados (1 ano útil), mas só temos 248 dias.

**Solução**: Aumentar o lookback_days em `scripts/run_pipeline.py` para 400 dias.

## Próximos Passos

1. **Corrigir mapeamento de dados fundamentalistas**
   - Investigar estrutura real retornada pelo Yahoo Finance
   - Atualizar `_create_fundamental_record()` com campos corretos
   
2. **Testar pipeline completo**
   - Executar `python scripts/run_pipeline.py`
   - Verificar se scores são gerados
   
3. **Validar API com dados**
   - Testar endpoints `/api/v1/ranking` e `/api/v1/top`
   - Verificar se retornam dados corretos

## Comandos Úteis

```bash
# Ver dados no banco
python -c "from app.models.database import SessionLocal; from app.models.schemas import RawPriceDaily; db = SessionLocal(); print(db.query(RawPriceDaily).count(), 'preços'); db.close()"

# Ver fundamentos
python -c "from app.models.database import SessionLocal; from app.models.schemas import RawFundamental; db = SessionLocal(); print(db.query(RawFundamental).count(), 'fundamentos'); db.close()"

# Ver scores
python -c "from app.models.database import SessionLocal; from app.models.schemas import ScoreDaily; db = SessionLocal(); print(db.query(ScoreDaily).count(), 'scores'); db.close()"

# Limpar banco e recomeçar
python scripts/init_db.py --drop
```

## Arquivos de Configuração

- `.env` - Variáveis de ambiente (DATABASE_URL, etc)
- `app/config.py` - Configurações da aplicação
- `docker-compose.yml` - Para rodar com Docker (PostgreSQL)

## Modo Docker vs Local

### Local (SQLite)
- Mais rápido para desenvolvimento
- Não precisa de PostgreSQL instalado
- Dados em arquivo `quant_ranker.db`

### Docker (PostgreSQL)
- Mais próximo de produção
- Requer Docker instalado
- Dados persistentes em volume Docker
