@echo off
REM Script para testar deployment Docker local
REM Valida: Requisitos 13.6, 13.9

echo ========================================
echo Sistema de Ranking Quantitativo
echo Teste de Deployment Docker
echo ========================================
echo.

REM Verificar se Docker está rodando
echo [1/5] Verificando Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Docker nao esta rodando!
    echo.
    echo Por favor, inicie o Docker Desktop e tente novamente.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker esta rodando
echo.

REM Parar containers existentes (se houver)
echo [2/5] Parando containers existentes...
docker-compose down >nul 2>&1
echo [OK] Containers parados
echo.

REM Iniciar serviços
echo [3/5] Iniciando servicos com docker-compose...
echo Isso pode levar alguns minutos na primeira vez...
echo.
docker-compose up -d --build

if %errorlevel% neq 0 (
    echo [ERRO] Falha ao iniciar servicos!
    echo.
    echo Para ver os logs:
    echo   docker-compose logs
    echo.
    pause
    exit /b 1
)
echo.
echo [OK] Servicos iniciados
echo.

REM Aguardar serviços ficarem prontos
echo [4/5] Aguardando servicos ficarem prontos...
echo Isso pode levar 1-2 minutos...
echo.
timeout /t 60 /nobreak >nul
echo [OK] Aguardando concluido
echo.

REM Executar testes
echo [5/5] Executando testes de deployment...
echo.
python scripts\test_docker_deployment.py

if %errorlevel% neq 0 (
    echo.
    echo [AVISO] Alguns testes falharam
    echo.
    echo Para ver logs dos servicos:
    echo   docker-compose logs postgres
    echo   docker-compose logs backend
    echo   docker-compose logs frontend
    echo.
    echo Para parar os servicos:
    echo   docker-compose down
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Deployment testado com sucesso!
echo ========================================
echo.
echo Servicos disponiveis:
echo   - Backend API: http://localhost:8000
echo   - Frontend: http://localhost:8501
echo   - PostgreSQL: localhost:5432
echo.
echo Para parar os servicos:
echo   docker-compose down
echo.
echo Para ver logs:
echo   docker-compose logs -f
echo.
pause
