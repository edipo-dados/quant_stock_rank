#!/bin/bash
# Script para testar deployment Docker local
# Valida: Requisitos 13.6, 13.9

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "Sistema de Ranking Quantitativo"
echo "Teste de Deployment Docker"
echo "========================================"
echo ""

# Verificar se Docker está rodando
echo "[1/5] Verificando Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}[ERRO] Docker não está rodando!${NC}"
    echo ""
    echo "Por favor, inicie o Docker e tente novamente."
    echo ""
    exit 1
fi
echo -e "${GREEN}[OK] Docker está rodando${NC}"
echo ""

# Parar containers existentes (se houver)
echo "[2/5] Parando containers existentes..."
docker-compose down > /dev/null 2>&1
echo -e "${GREEN}[OK] Containers parados${NC}"
echo ""

# Iniciar serviços
echo "[3/5] Iniciando serviços com docker-compose..."
echo "Isso pode levar alguns minutos na primeira vez..."
echo ""
docker-compose up -d --build

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERRO] Falha ao iniciar serviços!${NC}"
    echo ""
    echo "Para ver os logs:"
    echo "  docker-compose logs"
    echo ""
    exit 1
fi
echo ""
echo -e "${GREEN}[OK] Serviços iniciados${NC}"
echo ""

# Aguardar serviços ficarem prontos
echo "[4/5] Aguardando serviços ficarem prontos..."
echo "Isso pode levar 1-2 minutos..."
echo ""
sleep 60
echo -e "${GREEN}[OK] Aguardando concluído${NC}"
echo ""

# Executar testes
echo "[5/5] Executando testes de deployment..."
echo ""
python3 scripts/test_docker_deployment.py

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${YELLOW}[AVISO] Alguns testes falharam${NC}"
    echo ""
    echo "Para ver logs dos serviços:"
    echo "  docker-compose logs postgres"
    echo "  docker-compose logs backend"
    echo "  docker-compose logs frontend"
    echo ""
    echo "Para parar os serviços:"
    echo "  docker-compose down"
    echo ""
    exit 1
fi

echo ""
echo "========================================"
echo "Deployment testado com sucesso!"
echo "========================================"
echo ""
echo "Serviços disponíveis:"
echo "  - Backend API: http://localhost:8000"
echo "  - Frontend: http://localhost:8501"
echo "  - PostgreSQL: localhost:5432"
echo ""
echo "Para parar os serviços:"
echo "  docker-compose down"
echo ""
echo "Para ver logs:"
echo "  docker-compose logs -f"
echo ""
