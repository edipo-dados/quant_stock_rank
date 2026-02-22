@echo off
echo ========================================
echo   Quant Stock Ranker - Modo DEV
echo ========================================
echo.

REM Ativar ambiente virtual
if not exist "venv" (
    echo [ERRO] Ambiente virtual nao encontrado. Execute start_all.bat primeiro.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo [1/2] Iniciando backend (FastAPI)...
start "Backend - FastAPI" cmd /k "call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 5 /nobreak >nul

echo [2/2] Iniciando frontend (Streamlit)...
start "Frontend - Streamlit" cmd /k "call venv\Scripts\activate.bat && streamlit run frontend/streamlit_app.py"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   Aplicacao iniciada!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:8501
echo.
echo Abrindo frontend no navegador...
timeout /t 2 /nobreak >nul
start http://localhost:8501
