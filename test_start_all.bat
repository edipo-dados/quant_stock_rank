@echo off
echo ========================================
echo   Teste do Script start_all.bat
echo ========================================
echo.

REM Verificar se Python esta instalado
echo [1/5] Verificando Python...
python --version
if errorlevel 1 (
    echo [ERRO] Python nao encontrado.
    exit /b 1
)
echo [OK] Python encontrado.

echo.
echo [2/5] Verificando ambiente virtual...
if not exist "venv" (
    echo [AVISO] Ambiente virtual nao encontrado.
) else (
    echo [OK] Ambiente virtual existe.
)

echo.
echo [3/5] Testando init_db.py...
python scripts/init_db.py
if errorlevel 1 (
    echo [ERRO] Falha ao inicializar banco.
    exit /b 1
)
echo [OK] Banco inicializado.

echo.
echo [4/5] Testando pipeline (modo test)...
python scripts/run_pipeline.py --mode test --tickers PETR4,VALE3,ITUB4 --limit 3
if errorlevel 1 (
    echo [AVISO] Pipeline falhou.
) else (
    echo [OK] Pipeline executado.
)

echo.
echo [5/5] Verificando banco de dados...
python scripts/check_db.py

echo.
echo ========================================
echo   Teste concluido!
echo ========================================
pause
