#!/bin/bash
# Script para fazer deploy da correção no EC2

set -e

echo "=========================================="
echo "DEPLOY DA CORREÇÃO NO EC2"
echo "=========================================="

# 1. Pull das mudanças
echo ""
echo "1. Fazendo pull das mudanças..."
git pull origin main

# 2. Rebuild dos containers
echo ""
echo "2. Rebuilding containers..."
docker-compose down
docker-compose up -d --build

# 3. Aguardar containers ficarem healthy
echo ""
echo "3. Aguardando containers ficarem healthy..."
sleep 10

# 4. Verificar status
echo ""
echo "4. Verificando status dos containers..."
docker-compose ps

# 5. Rodar pipeline de teste
echo ""
echo "5. Rodando pipeline de teste..."
docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode test --limit 10

echo ""
echo "=========================================="
echo "DEPLOY CONCLUÍDO!"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo "1. Verificar logs: docker-compose logs -f backend"
echo "2. Acessar frontend: http://SEU_IP:8501"
echo "3. Rodar pipeline completo: docker exec quant-ranker-backend python scripts/run_pipeline_docker.py --mode liquid --limit 50"
