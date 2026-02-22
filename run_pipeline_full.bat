@echo off
echo Executando Pipeline Completo com Dados B3...
set DATABASE_URL=sqlite:///./quant_ranker.db
set PYTHONPATH=.
python -m scripts.run_pipeline --mode liquid
pause
