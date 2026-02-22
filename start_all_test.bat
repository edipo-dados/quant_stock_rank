@echo off
echo ========================================
echo   Quant Stock Ranker - Teste Completo
echo ========================================
echo.

REM Verificar se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale Python 3.9+ primeiro.
    timeout /t 5
    exit /b 1
)

echo [1/5] Verificando ambiente virtual...
if not exist "venv" (
    echo [AVISO] Ambiente virtual nao encontrado. Criando...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [INFO] Instalando dependencias...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo.
echo [2/5] Inicializando banco de dados...
python scripts/init_db.py
if errorlevel 1 (
    echo [ERRO] Falha ao inicializar banco de dados.
    timeout /t 5
    exit /b 1
)

echo.
echo [3/5] Executando pipeline (MODO TESTE - 10 ativos)...
echo [INFO] Processando 10 ativos liquidos para teste...
python scripts/run_pipeline.py --mode test --limit 10
if errorlevel 1 (
    echo [AVISO] Pipeline falhou, mas continuando...
    timeout /t 3
)

echo.
echo [4/5] Iniciando backend (FastAPI)...
start "Backend - FastAPI" cmd /k "call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo [INFO] Aguardando backend iniciar...
timeout /t 5 /nobreak >nul

echo.
echo [5/5] Iniciando frontend (Streamlit)...
start "Frontend - Streamlit" cmd /k "call venv\Scripts\activate.bat && streamlit run frontend/streamlit_app.py"
echo [INFO] Aguardando frontend iniciar...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   Aplicacao iniciada com sucesso!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:8501
echo Docs API: http://localhost:8000/docs
echo.
echo Abrindo frontend no navegador em 3 segundos...
timeout /t 3 /nobreak >nul

start http://localhost:8501

echo.
echo Para parar a aplicacao, use: stop_all.bat
echo Ou feche as janelas do Backend e Frontend manualmente.
echo.
