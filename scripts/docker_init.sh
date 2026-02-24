#!/bin/bash
set -e

echo "=== Iniciando Backend ==="

# Aguardar PostgreSQL estar pronto
echo "Aguardando PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "postgres" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  echo "PostgreSQL não está pronto - aguardando..."
  sleep 2
done

echo "PostgreSQL está pronto!"

# Inicializar banco de dados
echo "Inicializando banco de dados..."
python scripts/init_db.py

echo "Banco de dados inicializado!"

# Iniciar servidor
echo "Iniciando servidor uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --timeout-keep-alive 75
