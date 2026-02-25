#!/bin/bash
# Fix imediato para docker-compose.yml corrompido

echo "🔧 Corrigindo docker-compose.yml..."

# Resetar do Git (descarta mudanças locais)
git checkout docker-compose.yml

echo "✅ docker-compose.yml resetado do Git"

# Mostrar estado
echo ""
echo "📋 Dockerfiles configurados:"
grep "dockerfile:" docker-compose.yml | grep -v "#"

echo ""
echo "✅ PRONTO! Agora execute:"
echo "   docker-compose down"
echo "   docker-compose up -d --build"
