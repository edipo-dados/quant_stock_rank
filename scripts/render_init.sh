#!/bin/bash
# Script de inicialização para Render

set -e

echo "🚀 Iniciando aplicação no Render..."

# Verificar se DATABASE_URL está definida
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL não está definida!"
    exit 1
fi

echo "✅ DATABASE_URL configurada"

# Verificar conexão com o banco
echo "🔍 Verificando conexão com PostgreSQL..."
python -c "
from app.models.database import engine
try:
    with engine.connect() as conn:
        print('✅ Conexão com banco de dados OK')
except Exception as e:
    print(f'❌ Erro ao conectar: {e}')
    exit(1)
"

# Inicializar banco de dados (criar tabelas)
echo "📊 Inicializando banco de dados..."
python scripts/init_db.py

echo "✅ Banco de dados inicializado com sucesso!"

# Iniciar aplicação
echo "🎯 Iniciando servidor FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
