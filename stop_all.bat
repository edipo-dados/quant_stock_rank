@echo off
echo ========================================
echo   Parando Quant Stock Ranker
echo ========================================
echo.

echo [1/2] Parando backend (FastAPI)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    echo Matando processo %%a na porta 8000
    taskkill /F /PID %%a >nul 2>&1
)

echo [2/2] Parando frontend (Streamlit)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8501" ^| find "LISTENING"') do (
    echo Matando processo %%a na porta 8501
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ========================================
echo   Aplicacao parada!
echo ========================================
echo.
