#!/bin/bash
# Script para resetar docker-compose.yml para estado original

set -e

echo "=========================================="
echo "RESET DOCKER-COMPOSE.YML"
echo "=========================================="

if [ -f "docker-compose.yml.backup" ]; then
    echo "📝 Restaurando docker-compose.yml do backup..."
    cp docker-compose.yml.backup docker-compose.yml
    echo "✅ docker-compose.yml restaurado"
else
    echo "⚠️  Backup não encontrado, resetando manualmente..."
    
    # Resetar para Dockerfiles padrão
    sed -i 's|dockerfile: docker/Dockerfile.backend.ec2|dockerfile: docker/Dockerfile.backend|g' docker-compose.yml
    sed -i 's|dockerfile: docker/Dockerfile.frontend.ec2|dockerfile: docker/Dockerfile.frontend|g' docker-compose.yml
    
    # Remover múltiplas extensões .ec2 se existirem
    sed -i 's|Dockerfile.backend.ec2.ec2.*|Dockerfile.backend|g' docker-compose.yml
    sed -i 's|Dockerfile.frontend.ec2.ec2.*|Dockerfile.frontend|g' docker-compose.yml
    
    echo "✅ docker-compose.yml resetado"
fi

echo ""
echo "📋 Estado atual:"
grep "dockerfile:" docker-compose.yml | head -2

echo ""
echo "=========================================="
echo "✅ RESET CONCLUÍDO"
echo "=========================================="
