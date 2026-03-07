#!/bin/bash
# Script para encontrar e entrar no container correto

echo "=== Containers em execução ==="
docker ps

echo ""
echo "=== Procurando container do backend ==="
BACKEND_CONTAINER=$(docker ps --filter "name=backend" --format "{{.Names}}" | head -n 1)

if [ -z "$BACKEND_CONTAINER" ]; then
    echo "❌ Nenhum container com 'backend' no nome encontrado"
    echo ""
    echo "Tentando encontrar por imagem..."
    BACKEND_CONTAINER=$(docker ps --filter "ancestor=quant" --format "{{.Names}}" | head -n 1)
fi

if [ -z "$BACKEND_CONTAINER" ]; then
    echo "❌ Nenhum container encontrado"
    echo ""
    echo "Containers disponíveis:"
    docker ps --format "{{.Names}}"
else
    echo "✓ Container encontrado: $BACKEND_CONTAINER"
    echo ""
    echo "Para entrar no container, execute:"
    echo "docker exec -it $BACKEND_CONTAINER bash"
    echo ""
    echo "Ou execute diretamente o diagnóstico:"
    echo "docker exec -it $BACKEND_CONTAINER python scripts/diagnose_itub3.py"
fi
