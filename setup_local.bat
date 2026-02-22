@echo off
echo ========================================
echo Setup Local - Quant Stock Ranker
echo ========================================
echo.

REM Define variável de ambiente para SQLite
set DATABASE_URL=sqlite:///./quant_ranker.db

echo [1/3] Inicializando banco de dados SQLite...
python scripts/init_db.py
if %errorlevel% neq 0 (
    echo ERRO: Falha ao inicializar banco de dados
    exit /b 1
)

echo.
echo [2/3] Testando conexão com Yahoo Finance...
python -c "from app.ingestion.yahoo_client import YahooFinanceClient; from datetime import date, timedelta; client = YahooFinanceClient(); end = date.today(); start = end - timedelta(days=30); df = client.fetch_daily_prices('PETR4.SA', start, end); print(f'✓ Yahoo Finance OK - {len(df)} registros obtidos')"
if %errorlevel% neq 0 (
    echo ERRO: Falha ao conectar com Yahoo Finance
    exit /b 1
)

echo.
echo [3/3] Executando pipeline de teste...
python scripts/run_pipeline.py
if %errorlevel% neq 0 (
    echo ERRO: Falha ao executar pipeline
    exit /b 1
)

echo.
echo ========================================
echo ✓ Setup concluído com sucesso!
echo ========================================
echo.
echo Para iniciar a API:
echo   set DATABASE_URL=sqlite:///./quant_ranker.db
echo   uvicorn app.main:app --reload
echo.
echo Para iniciar o frontend:
echo   cd frontend
echo   streamlit run streamlit_app.py
echo.
