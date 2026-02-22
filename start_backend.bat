@echo off
set PYTHONPATH=.
set DATABASE_URL=sqlite:///./quant_ranker.db
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
