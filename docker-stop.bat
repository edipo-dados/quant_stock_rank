@echo off
echo ========================================
echo Parando Sistema Docker
echo ========================================
echo.

docker-compose down

echo.
echo Sistema parado com sucesso!
echo.
echo Para iniciar novamente: docker-start.bat
echo Para limpar tudo (incluindo dados): docker-compose down -v
echo.
pause
