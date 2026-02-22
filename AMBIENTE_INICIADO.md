# ✅ Ambiente Local Iniciado com Sucesso!

## Status dos Serviços

### ✅ API Backend - RODANDO
- **URL**: http://localhost:8000
- **Status**: Healthy
- **Versão**: 1.0.0
- **Documentação**: http://localhost:8000/docs

### ✅ Frontend Streamlit - RODANDO
- **URL**: http://localhost:8501
- **Status**: Ativo e funcionando
- **Local URL**: http://localhost:8501
- **Network URL**: http://192.168.15.16:8501

## Ranking Atual (Top 5)

```
1. ITUB4.SA  - Score:  0.466 ⭐
2. ABEV3.SA  - Score:  0.360
3. BBDC4.SA  - Score:  0.231
4. RENT3.SA  - Score:  0.091
5. WEGE3.SA  - Score:  0.029
```

## Como Acessar

### 1. API REST
Abra seu navegador em: **http://localhost:8000/docs**

Endpoints disponíveis:
- `GET /health` - Status da API
- `GET /api/v1/ranking` - Ranking completo
- `GET /api/v1/top?limit=5` - Top N ativos
- `GET /api/v1/asset/{ticker}` - Detalhes de um ativo

### 2. Frontend Web
Abra seu navegador em: **http://localhost:8501**

Se ainda não carregar, aguarde mais 30 segundos e recarregue a página.

Páginas disponíveis:
- **Home**: Visão geral do sistema
- **🏆 Ranking**: Lista completa de ativos ranqueados
- **📊 Detalhes do Ativo**: Análise detalhada

## Testar API via Terminal

### Health Check:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

### Top 5 Ativos:
```powershell
(Invoke-RestMethod -Uri "http://localhost:8000/api/v1/top?limit=5").top_assets | Select-Object rank, ticker, final_score
```

### Ranking Completo:
```powershell
(Invoke-RestMethod -Uri "http://localhost:8000/api/v1/ranking").rankings | Select-Object rank, ticker, final_score
```

### Detalhes de um Ativo:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/asset/ITUB4.SA"
```

## Processos em Execução

Você deve ter 2 janelas abertas:
1. **Python (API)** - Executando uvicorn
2. **Python (Frontend)** - Executando streamlit

**Não feche essas janelas!** Elas mantêm os serviços rodando.

## Parar os Serviços

Para parar, feche as janelas ou pressione `Ctrl+C` em cada uma.

## Atualizar Dados

Para buscar novos dados e recalcular o ranking:

```powershell
$env:DATABASE_URL="sqlite:///./quant_ranker.db"
$env:PYTHONPATH="."
python scripts/run_pipeline.py
```

Isso levará cerca de 1 minuto e atualizará:
- Preços (últimos 400 dias)
- Dados fundamentalistas
- Fatores calculados
- Scores e ranking

## Verificar Dados no Banco

```powershell
python -c "from app.models.database import SessionLocal; from app.models.schemas import ScoreDaily; db = SessionLocal(); scores = db.query(ScoreDaily).order_by(ScoreDaily.rank).all(); print(f'\n{len(scores)} ativos ranqueados:\n'); [print(f'{s.rank}. {s.ticker}: {s.final_score:.3f}') for s in scores]; db.close()"
```

## Troubleshooting

### Frontend não carrega
1. Aguarde 60 segundos
2. Recarregue a página (F5)
3. Verifique se a janela do Streamlit não mostra erros
4. Se necessário, feche e reinicie:
   ```powershell
   Start-Process python -ArgumentList "-m", "streamlit", "run", "frontend/streamlit_app.py"
   ```

### API não responde
1. Verifique se a janela da API está aberta
2. Procure por erros na janela
3. Se necessário, reinicie:
   ```powershell
   $env:DATABASE_URL="sqlite:///./quant_ranker.db"
   $env:PYTHONPATH="."
   Start-Process python -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"
   ```

### Porta já em uso
Se receber erro "Address already in use":

```powershell
# Encontrar processo na porta 8000
netstat -ano | findstr :8000

# Matar processo (substitua PID pelo número encontrado)
taskkill /PID [PID] /F
```

## Próximos Passos

1. ✅ Acesse o Frontend: http://localhost:8501
2. ✅ Navegue para "🏆 Ranking"
3. ✅ Explore os dados dos ativos
4. ✅ Teste a API: http://localhost:8000/docs
5. 🔄 Execute a pipeline para atualizar dados

## Dados Disponíveis

- **Ativos**: 10 ações brasileiras
- **Período**: Últimos 400 dias de preços
- **Fundamentos**: 4-5 anos de dados anuais
- **Última atualização**: 2026-02-18

## Composição dos Scores

- **Momentum (40%)**: Retornos, RSI, Volatilidade, Drawdown
- **Quality (30%)**: ROE, Margem Líquida, Crescimento, Dívida/EBITDA
- **Value (30%)**: P/L, EV/EBITDA, P/VP

## Suporte

Consulte:
- `COMO_INICIAR.md` - Instruções detalhadas
- `SUCESSO_SETUP_LOCAL.md` - Detalhes técnicos
- `GUIA_RAPIDO.md` - Comandos úteis
