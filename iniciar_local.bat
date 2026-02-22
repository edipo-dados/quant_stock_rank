@echo off
cls
echo ========================================
echo Quant Stock Ranker - Ambiente Local
echo ========================================
echo.
echo Escolha uma opcao:
echo.
echo 1. Iniciar API (Backend)
echo 2. Iniciar Frontend (Streamlit)
echo 3. Iniciar AMBOS (em janelas separadas)
echo 4. Executar Pipeline (atualizar dados)
echo 5. Testar API
echo 6. Sair
echo.
set /p opcao="Digite o numero da opcao: "

if "%opcao%"=="1" goto api
if "%opcao%"=="2" goto frontend
if "%opcao%"=="3" goto ambos
if "%opcao%"=="4" goto pipeline
if "%opcao%"=="5" goto testar
if "%opcao%"=="6" goto sair

echo Opcao invalida!
pause
goto :eof

:api
echo.
echo Iniciando API...
echo Acesse: http://localhost:8000
echo Docs: http://localhost:8000/docs
echo.
set DATABASE_URL=sqlite:///./quant_ranker.db
set PYTHONPATH=.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
goto :eof

:frontend
echo.
echo Iniciando Frontend...
echo Acesse: http://localhost:8501
echo.
set BACKEND_URL=http://localhost:8000
cd frontend
streamlit run streamlit_app.py
goto :eof

:ambos
echo.
echo Iniciando API e Frontend em janelas separadas...
echo.
start "API - Quant Ranker" cmd /c "set DATABASE_URL=sqlite:///./quant_ranker.db && set PYTHONPATH=. && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak > nul
start "Frontend - Quant Ranker" cmd /c "set BACKEND_URL=http://localhost:8000 && cd frontend && streamlit run streamlit_app.py"
echo.
echo ========================================
echo Ambiente iniciado!
echo ========================================
echo.
echo API: http://localhost:8000
echo Frontend: http://localhost:8501
echo.
echo Pressione qualquer tecla para fechar...
pause > nul
goto :eof

:pipeline
echo.
echo Executando pipeline...
set DATABASE_URL=sqlite:///./quant_ranker.db
set PYTHONPATH=.
python scripts/run_pipeline.py
echo.
pause
goto :eof

:testar
echo.
echo Testando API...
python test_api_local.py
echo.
pause
goto :eof

:sair
exit
