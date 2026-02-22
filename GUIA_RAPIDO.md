# 🚀 Guia Rápido - Quant Stock Ranker

## Iniciar Ambiente Local

### Opção 1: Tudo de uma vez (Recomendado)
```bash
start_all.bat
```
Isso abrirá 2 janelas:
- **API** rodando em http://localhost:8000
- **Frontend** rodando em http://localhost:8501

### Opção 2: Componentes separados

**Apenas API:**
```bash
start_api.bat
```

**Apenas Frontend:**
```bash
start_frontend.bat
```

## Acessar Aplicação

### Frontend (Interface Web)
🌐 http://localhost:8501

Páginas disponíveis:
- **Home**: Visão geral do sistema
- **🏆 Ranking**: Lista completa de ativos ranqueados
- **📊 Detalhes do Ativo**: Análise detalhada de cada ativo

### API REST
🔗 http://localhost:8000

Endpoints principais:
- `GET /health` - Status da API
- `GET /api/v1/ranking` - Ranking completo
- `GET /api/v1/top?limit=5` - Top N ativos
- `GET /api/v1/asset/{ticker}` - Detalhes de um ativo

### Documentação da API
📚 http://localhost:8000/docs

Interface Swagger interativa para testar todos os endpoints.

## Executar Pipeline

Para atualizar os dados e recalcular o ranking:

```bash
set DATABASE_URL=sqlite:///./quant_ranker.db
set PYTHONPATH=.
python scripts/run_pipeline.py
```

Isso irá:
1. Buscar preços do Yahoo Finance (últimos 400 dias)
2. Buscar dados fundamentalistas
3. Calcular fatores de momentum
4. Calcular fatores fundamentalistas
5. Normalizar features
6. Calcular scores
7. Gerar ranking

Tempo estimado: ~1 minuto para 10 ativos

## Verificar Dados

### Ver scores no banco:
```bash
python -c "from app.models.database import SessionLocal; from app.models.schemas import ScoreDaily; db = SessionLocal(); scores = db.query(ScoreDaily).order_by(ScoreDaily.rank).all(); print(f'\n{len(scores)} ativos ranqueados:\n'); [print(f'{s.rank}. {s.ticker}: {s.final_score:.3f}') for s in scores]; db.close()"
```

### Ver estatísticas:
```bash
python scripts/check_db.py
```

## Testar API

### Via Python:
```bash
python test_api_local.py
```

### Via curl:
```bash
# Health check
curl http://localhost:8000/health

# Ranking completo
curl http://localhost:8000/api/v1/ranking

# Top 5
curl http://localhost:8000/api/v1/top?limit=5

# Detalhes de um ativo
curl http://localhost:8000/api/v1/asset/ITUB4.SA
```

## Limpar e Reiniciar

Para limpar o banco e recomeçar:

```bash
set DATABASE_URL=sqlite:///./quant_ranker.db
echo sim | python scripts/init_db.py --drop
python scripts/run_pipeline.py
```

## Estrutura de Dados

### Ranking Atual (exemplo):
```
1. ITUB4.SA: 0.466 (Momentum: 0.44, Quality: 0.97, Value: 0.00)
2. ABEV3.SA: 0.360 (Momentum: 0.46, Quality: 0.00, Value: 0.58)
3. BBDC4.SA: 0.231 (Momentum: 0.08, Quality: -0.11, Value: 0.78)
4. RENT3.SA: 0.091 (Momentum: 0.35, Quality: -0.13, Value: -0.04)
5. WEGE3.SA: 0.029 (Momentum: -0.39, Quality: 1.02, Value: -0.40)
```

### Pesos dos Fatores:
- **Momentum**: 40% (return_6m, return_12m, rsi_14, volatility, drawdown)
- **Quality**: 30% (roe, net_margin, revenue_growth, debt_to_ebitda)
- **Value**: 30% (pe_ratio, ev_ebitda, pb_ratio)

## Troubleshooting

### API não inicia
- Verifique se a porta 8000 está livre
- Confirme que uvicorn está instalado: `pip install uvicorn`

### Frontend não inicia
- Verifique se a porta 8501 está livre
- Confirme que streamlit está instalado: `pip install streamlit`

### Erro "No module named 'app'"
```bash
set PYTHONPATH=.
```

### Banco de dados vazio
Execute a pipeline:
```bash
python scripts/run_pipeline.py
```

### Erro de conexão Frontend → API
Verifique se a API está rodando:
```bash
curl http://localhost:8000/health
```

## Parar Ambiente

Feche as janelas do terminal ou pressione `Ctrl+C` em cada uma.

## Próximos Passos

1. ✅ Ambiente local funcionando
2. 🔄 Adicionar mais tickers em `scripts/run_pipeline.py`
3. 🔄 Ajustar pesos em `.env` (MOMENTUM_WEIGHT, QUALITY_WEIGHT, VALUE_WEIGHT)
4. 🔄 Agendar execução diária da pipeline
5. 🔄 Deploy em produção com Docker

## Suporte

Consulte os arquivos:
- `SUCESSO_SETUP_LOCAL.md` - Detalhes técnicos das correções
- `README.md` - Documentação completa do projeto
- `SETUP_LOCAL_RAPIDO.md` - Problemas conhecidos e soluções
