@echo off
echo Iniciando Backend API (FastAPI)...
set DATABASE_URL=sqlite:///./quant_ranker.db
set PYTHONPATH=.
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
