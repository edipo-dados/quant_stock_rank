@echo off
echo ========================================
echo Executando Pipeline de Dados no Docker
echo ========================================
echo.

REM Verificar se os containers estão rodando
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo ERRO: Containers nao estao rodando!
    echo Execute docker-start.bat primeiro.
    pause
    exit /b 1
)

echo Escolha o modo de execucao:
echo.
echo 1. Teste (5 ativos)
echo 2. Liquidos (top 100 ativos mais liquidos)
echo 3. Manual (especificar tickers)
echo.
set /p modo="Digite o numero: "

if "%modo%"=="1" (
    echo.
    echo Executando pipeline em modo TESTE...
    docker-compose exec backend python scripts/run_pipeline_docker.py --mode test
) else if "%modo%"=="2" (
    echo.
    set /p limit="Quantos ativos liquidos? (padrao 100): "
    if "%limit%"=="" set limit=100
    echo Executando pipeline com %limit% ativos liquidos...
    docker-compose exec backend python scripts/run_pipeline_docker.py --mode liquid --limit %limit%
) else if "%modo%"=="3" (
    echo.
    echo Digite os tickers separados por espaco (ex: PETR4.SA VALE3.SA ITUB4.SA):
    set /p tickers="Tickers: "
    echo Executando pipeline com tickers customizados...
    docker-compose exec backend python scripts/run_pipeline_docker.py --mode manual --tickers %tickers%
) else (
    echo Opcao invalida!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Pipeline concluido!
echo ========================================
echo.
echo Acesse o frontend para ver os resultados:
echo http://localhost:8501
echo.
pause
