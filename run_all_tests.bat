@echo off
echo ========================================
echo Executando Todos os Testes do Sistema
echo ========================================
echo.

REM Define a variável de ambiente para o banco de dados
set DATABASE_URL=postgresql://quant_user:quant_password@localhost:5432/quant_ranker

echo [1/1] Executando testes...
python -m pytest tests/ -v --tb=short

if errorlevel 1 (
    echo.
    echo ========================================
    echo ALGUNS TESTES FALHARAM
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo TODOS OS TESTES PASSARAM!
echo ========================================
pause
