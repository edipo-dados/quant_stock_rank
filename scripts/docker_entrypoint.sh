#!/bin/bash

echo "========================================="
echo "QUANT STOCK RANKER - DOCKER ENTRYPOINT"
echo "========================================="
echo ""

# Aguardar PostgreSQL estar pronto
echo "[1/5] Aguardando PostgreSQL..."
until python -c "from app.models.database import engine; engine.connect()" 2>/dev/null; do
  echo "PostgreSQL não está pronto - aguardando..."
  sleep 2
done
echo "✓ PostgreSQL pronto!"
echo ""

# Inicializar banco de dados
echo "[2/5] Inicializando banco de dados..."
python scripts/init_db.py
echo ""

# Testar APIs externas
echo "[3/5] Testando conectividade com APIs externas..."
python scripts/test_apis.py
API_TEST_RESULT=$?
echo ""

# Executar pipeline de dados
echo "[4/5] Executando pipeline de extração de dados..."
if [ $API_TEST_RESULT -eq 0 ]; then
    echo "✓ APIs funcionando - executando pipeline completo..."
    python -m scripts.run_pipeline || {
        echo "⚠ Pipeline falhou - inserindo dados de teste..."
        python scripts/insert_test_data.py
    }
elif [ $API_TEST_RESULT -eq 1 ]; then
    echo "⚠ Algumas APIs funcionando - tentando pipeline..."
    python -m scripts.run_pipeline || {
        echo "⚠ Pipeline falhou - inserindo dados de teste..."
        python scripts/insert_test_data.py
    }
else
    echo "✗ APIs não funcionando - usando dados de teste..."
    python scripts/insert_test_data.py
fi
echo ""

# Iniciar aplicação
echo "[5/5] Iniciando API FastAPI..."
echo "========================================="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
