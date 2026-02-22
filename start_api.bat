@echo off
echo ========================================
echo Iniciando API - Quant Stock Ranker
echo ========================================
echo.

set DATABASE_URL=sqlite:///./quant_ranker.db
set PYTHONPATH=.

echo Configuracao:
echo   DATABASE_URL: %DATABASE_URL%
echo   API: http://localhost:8000
echo   Docs: http://localhost:8000/docs
echo.

echo Iniciando servidor...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
