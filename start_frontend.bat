@echo off
cd frontend
set BACKEND_URL=http://localhost:8000
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
python -m streamlit run streamlit_app.py --server.headless=true
