@echo off
echo Iniciando Frontend (Streamlit)...
set BACKEND_URL=http://localhost:8000
cd frontend
python -m streamlit run streamlit_app.py --server.headless=true
