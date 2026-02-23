@echo off
echo ========================================
echo Iniciando Sistema com Docker + PostgreSQL
echo ========================================
echo.

REM Parar containers existentes
echo Parando containers existentes...
docker-compose down

echo.
echo Construindo imagens Docker...
docker-compose build

echo.
echo Iniciando containers...
docker-compose up -d

echo.
echo Aguardando servicos iniciarem...
echo - PostgreSQL...
timeout /t 5 /nobreak >nul
echo - Backend...
timeout /t 10 /nobreak >nul
echo - Frontend...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Sistema iniciado com sucesso!
echo ========================================
echo.
echo Servicos disponiveis:
echo - PostgreSQL: localhost:5432
echo   Usuario: quant_user
echo   Senha: quant_password
echo   Database: quant_ranker
echo.
echo - API Backend: http://localhost:8000
echo - API Docs: http://localhost:8000/docs
echo - Frontend: http://localhost:8501
echo.
echo Comandos uteis:
echo   Ver logs: docker-compose logs -f
echo   Ver logs do backend: docker-compose logs -f backend
echo   Ver logs do frontend: docker-compose logs -f frontend
echo   Parar tudo: docker-compose down
echo   Reiniciar: docker-compose restart
echo.
echo Para rodar o pipeline de dados:
echo   docker-compose exec backend python scripts/run_pipeline.py --mode test
echo.
pause
