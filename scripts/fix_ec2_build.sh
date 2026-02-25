#!/bin/bash
# Script para resolver problemas de build no EC2

set -e

echo "=========================================="
echo "EC2 BUILD FIX"
echo "=========================================="

# 1. Verificar tipo de instância
echo ""
echo "1️⃣ Verificando recursos do sistema..."
echo "Memória:"
free -h
echo ""
echo "Disco:"
df -h /
echo ""

# 2. Adicionar swap se necessário
SWAP_SIZE=$(swapon --show | grep -c '/swapfile' || echo "0")
if [ "$SWAP_SIZE" -eq "0" ]; then
    echo "2️⃣ Configurando swap..."
    bash scripts/setup_ec2_swap.sh
else
    echo "2️⃣ Swap já configurado ✅"
fi

# 3. Instalar dependências do sistema
echo ""
echo "3️⃣ Instalando dependências do sistema..."
sudo apt-get update
sudo apt-get install -y \
    gcc \
    g++ \
    make \
    build-essential \
    libpq-dev \
    postgresql-client \
    curl \
    git

echo "✅ Dependências instaladas"

# 4. Verificar se Dockerfile.backend.ec2 existe
echo ""
echo "4️⃣ Verificando Dockerfile otimizado..."
if [ -f "docker/Dockerfile.backend.ec2" ]; then
    echo "✅ Dockerfile.backend.ec2 encontrado"
    
    # Backup do docker-compose.yml
    if [ ! -f "docker-compose.yml.backup" ]; then
        echo "📝 Criando backup do docker-compose.yml..."
        cp docker-compose.yml docker-compose.yml.backup
    fi
    
    # Atualizar docker-compose.yml para usar Dockerfile otimizado
    echo "🔧 Atualizando docker-compose.yml..."
    
    # Verificar se já está usando .ec2
    if grep -q "Dockerfile.backend.ec2" docker-compose.yml; then
        echo "✅ Backend já está usando Dockerfile.backend.ec2"
    else
        sed -i 's|dockerfile: docker/Dockerfile.backend|dockerfile: docker/Dockerfile.backend.ec2|g' docker-compose.yml
        echo "✅ Backend atualizado para Dockerfile.backend.ec2"
    fi
    
    if grep -q "Dockerfile.frontend.ec2" docker-compose.yml; then
        echo "✅ Frontend já está usando Dockerfile.frontend.ec2"
    else
        sed -i 's|dockerfile: docker/Dockerfile.frontend|dockerfile: docker/Dockerfile.frontend.ec2|g' docker-compose.yml
        echo "✅ Frontend atualizado para Dockerfile.frontend.ec2"
    fi
else
    echo "⚠️  Dockerfile.backend.ec2 não encontrado"
    echo "   Usando Dockerfile.backend padrão"
fi

# 5. Limpar Docker
echo ""
echo "5️⃣ Limpando cache do Docker..."
docker system prune -f

echo ""
echo "=========================================="
echo "✅ CONFIGURAÇÃO CONCLUÍDA"
echo "=========================================="
echo ""
echo "📋 Próximos passos:"
echo "   1. docker-compose down"
echo "   2. docker-compose up -d --build"
echo "   3. docker-compose logs -f backend"
echo ""
echo "💡 Se o build ainda falhar, considere:"
echo "   - Upgrade da instância EC2 (t2.small ou t2.medium)"
echo "   - Build local + push para Docker Hub"
echo "   - Ver EC2_BUILD_TROUBLESHOOTING.md para mais opções"
