# 🚀 Como Iniciar o Ambiente Local

## Método Simples (Recomendado)

### Passo 1: Abrir Terminal para API

1. Abra um **novo terminal/prompt de comando**
2. Navegue até a pasta do projeto
3. Execute:

```cmd
set DATABASE_URL=sqlite:///./quant_ranker.db
set PYTHONPATH=.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Você verá algo como:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

✅ **API rodando em: http://localhost:8000**

### Passo 2: Abrir Terminal para Frontend

1. Abra um **segundo terminal/prompt de comando**
2. Navegue até a pasta do projeto
3. Execute:

```cmd
cd frontend
streamlit run streamlit_app.py
```

Você verá algo como:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

✅ **Frontend rodando em: http://localhost:8501**

## Método Alternativo (Scripts)

### Opção A: Usar script interativo

```cmd
iniciar_local.bat
```

Escolha a opção 3 para iniciar ambos.

### Opção B: Scripts individuais

**Terminal 1 - API:**
```cmd
start_api.bat
```

**Terminal 2 - Frontend:**
```cmd
start_frontend.bat
```

## Verificar se está funcionando

### Testar API:
Abra o navegador em: http://localhost:8000/docs

Ou no terminal:
```cmd
curl http://localhost:8000/health
```

Resposta esperada:
```json
{"status":"healthy","version":"1.0.0"}
```

### Testar Frontend:
Abra o navegador em: http://localhost:8501

Você deve ver a página inicial do sistema.

## Problemas Comuns

### Erro: "Address already in use" (Porta 8000)

Outra aplicação está usando a porta. Opções:

1. **Encontrar e fechar o processo:**
```cmd
netstat -ano | findstr :8000
taskkill /PID [número_do_pid] /F
```

2. **Usar outra porta:**
```cmd
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Erro: "Address already in use" (Porta 8501)

```cmd
netstat -ano | findstr :8501
taskkill /PID [número_do_pid] /F
```

### Erro: "No module named 'app'"

Certifique-se de estar na pasta raiz do projeto e:
```cmd
set PYTHONPATH=.
```

### Erro: "uvicorn: command not found"

Instale as dependências:
```cmd
pip install -r requirements.txt
```

### Erro: "streamlit: command not found"

```cmd
pip install streamlit
```

### Frontend não conecta na API

1. Verifique se a API está rodando: http://localhost:8000/health
2. Verifique a variável de ambiente:
```cmd
set BACKEND_URL=http://localhost:8000
```

## Parar os Serviços

Em cada terminal, pressione: **Ctrl + C**

## Próximos Passos

Após iniciar:

1. ✅ Acesse o Frontend: http://localhost:8501
2. ✅ Navegue para "🏆 Ranking" no menu lateral
3. ✅ Veja o ranking dos 10 ativos
4. ✅ Clique em um ativo para ver detalhes

## Atualizar Dados

Para buscar novos dados e recalcular o ranking:

```cmd
set DATABASE_URL=sqlite:///./quant_ranker.db
set PYTHONPATH=.
python scripts/run_pipeline.py
```

Isso levará cerca de 1 minuto.

## Comandos Úteis

### Ver dados no banco:
```cmd
python -c "from app.models.database import SessionLocal; from app.models.schemas import ScoreDaily; db = SessionLocal(); scores = db.query(ScoreDaily).order_by(ScoreDaily.rank).all(); [print(f'{s.rank}. {s.ticker}: {s.final_score:.3f}') for s in scores]; db.close()"
```

### Testar API via Python:
```cmd
python test_api_local.py
```

### Limpar banco e reiniciar:
```cmd
echo sim | python scripts/init_db.py --drop
python scripts/run_pipeline.py
```

## Estrutura de URLs

- **API Base**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Ranking**: http://localhost:8000/api/v1/ranking
- **Top 5**: http://localhost:8000/api/v1/top?limit=5
- **Frontend**: http://localhost:8501

## Dicas

1. Mantenha os dois terminais abertos enquanto usa o sistema
2. Use Ctrl+C para parar cada serviço
3. Se algo der errado, reinicie ambos os serviços
4. Consulte os logs nos terminais para debug
