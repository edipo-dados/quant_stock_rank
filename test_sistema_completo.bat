@echo off
echo ================================================================================
echo TESTE COMPLETO DO SISTEMA - QUANT STOCK RANKER
echo ================================================================================
echo.

echo [1/5] Verificando status dos containers...
docker-compose ps
echo.

echo [2/5] Testando health check da API...
curl -s http://localhost:8000/health
echo.
echo.

echo [3/5] Testando endpoint de ranking...
curl -s http://localhost:8000/api/v1/ranking | python -m json.tool
echo.

echo [4/5] Testando endpoint de top 3 ativos...
curl -s "http://localhost:8000/api/v1/top?n=3" | python -m json.tool
echo.

echo [5/5] Testando endpoint de detalhes de ativo...
curl -s http://localhost:8000/api/v1/asset/PETR4.SA | python -m json.tool
echo.

echo ================================================================================
echo TESTE COMPLETO!
echo ================================================================================
echo.
echo Acesse a aplicacao em:
echo - Frontend: http://localhost:8501
echo - API Docs: http://localhost:8000/docs
echo.
pause
