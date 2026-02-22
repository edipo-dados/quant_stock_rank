@echo off
echo ========================================
echo Iniciando Banco de Dados PostgreSQL
echo ========================================
echo.

REM Verifica se Docker está instalado
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Docker nao esta instalado ou nao esta no PATH
    echo.
    echo Instale o Docker Desktop em: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [1/3] Iniciando container PostgreSQL...
docker-compose up -d postgres

if errorlevel 1 (
    echo.
    echo ERRO: Falha ao iniciar o container
    pause
    exit /b 1
)

echo.
echo [2/3] Aguardando banco de dados ficar pronto...
timeout /t 5 /nobreak >nul

echo.
echo [3/3] Verificando conexao...
python scripts/check_db.py

if errorlevel 1 (
    echo.
    echo AVISO: Banco iniciado mas ainda nao esta pronto
    echo Aguarde alguns segundos e execute: python scripts/check_db.py
)

echo.
echo ========================================
echo Banco de dados iniciado com sucesso!
echo ========================================
echo.
echo Para conectar:
echo   Host: localhost
echo   Porta: 5432
echo   Database: quant_ranker
echo   Usuario: user
echo   Senha: password
echo.
echo Para inicializar as tabelas:
echo   python scripts/init_db.py
echo.
echo Para parar o banco:
echo   docker-compose down
echo.
pause
