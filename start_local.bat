@echo off
echo ========================================
echo QUANT STOCK RANKER - AMBIENTE LOCAL
echo ========================================
echo.

echo [1/5] Verificando PostgreSQL no Docker...
docker ps | findstr quant-ranker-db >nul 2>&1
if %errorlevel% neq 0 (
    echo PostgreSQL nao esta rodando. Iniciando...
    docker-compose up -d postgres
    echo Aguardando PostgreSQL ficar pronto...
    timeout /t 15 /nobreak >nul
) else (
    echo PostgreSQL ja esta rodando!
)
echo.

echo [2/5] Inicializando banco de dados...
python scripts/init_db.py
echo.

echo [3/5] Testando Yahoo Finance...
python scripts/test_apis.py
echo.

echo [4/5] Executando pipeline de dados...
python -m scripts.run_pipeline
echo.

echo [5/5] Ambiente pronto!
echo ========================================
echo.
echo Para iniciar a aplicacao:
echo.
echo   Backend:  python -m uvicorn app.main:app --reload
echo   Frontend: streamlit run frontend/streamlit_app.py
echo.
echo Ou execute os scripts separados:
echo   start_backend.bat
echo   start_frontend.bat
echo.
pause
