@echo off
echo ================================================================================
echo INICIANDO SISTEMA COMPLETO - QUANT STOCK RANKER
echo ================================================================================
echo.

echo [1/5] Parando containers existentes...
docker-compose down
echo.

echo [2/5] Definindo variaveis de ambiente...
set FMP_API_KEY=fNVVAjv4Jlkl7Js2VbCRm7bBivEEQDc3
set BACKEND_URL=http://backend:8000
echo Variaveis definidas:
echo - FMP_API_KEY: %FMP_API_KEY%
echo - BACKEND_URL: %BACKEND_URL%
echo.

echo [3/5] Reconstruindo imagens Docker...
docker-compose build backend
echo.

echo [4/5] Iniciando containers...
docker-compose up -d
echo.

echo [5/5] Aguardando sistema inicializar (60 segundos)...
echo O backend ira automaticamente:
echo - Inicializar o banco de dados
echo - Testar conectividade com APIs externas
echo - Executar pipeline de extracao de dados
echo - Inserir dados de teste se APIs falharem
echo.
timeout /t 60 /nobreak
echo.

echo ================================================================================
echo SISTEMA INICIADO COM SUCESSO!
echo ================================================================================
echo.
echo Acesse a aplicacao em:
echo - Frontend: http://localhost:8501
echo - API Docs: http://localhost:8000/docs
echo - Health Check: http://localhost:8000/health
echo.
echo Pressione qualquer tecla para verificar o status dos containers...
pause > nul

docker-compose ps
echo.
echo Pressione qualquer tecla para ver os logs do backend...
pause > nul

docker-compose logs --tail=50 backend
echo.
echo Pressione qualquer tecla para sair...
pause > nul
