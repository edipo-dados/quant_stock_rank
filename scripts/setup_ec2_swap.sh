#!/bin/bash
# Script para configurar swap no EC2 (t2.micro/t2.small)

set -e

echo "=========================================="
echo "EC2 SWAP SETUP"
echo "=========================================="

# Verificar se já existe swap
if swapon --show | grep -q '/swapfile'; then
    echo "✅ Swap já configurado"
    free -h
    exit 0
fi

echo "📊 Memória atual:"
free -h

echo ""
echo "🔧 Criando arquivo de swap de 2GB..."
sudo fallocate -l 2G /swapfile

echo "🔒 Configurando permissões..."
sudo chmod 600 /swapfile

echo "💾 Criando swap..."
sudo mkswap /swapfile

echo "✅ Ativando swap..."
sudo swapon /swapfile

echo "📝 Tornando permanente..."
if ! grep -q '/swapfile' /etc/fstab; then
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

echo ""
echo "=========================================="
echo "✅ SWAP CONFIGURADO COM SUCESSO"
echo "=========================================="
echo ""
echo "📊 Memória após configuração:"
free -h

echo ""
echo "💡 Dica: Agora você pode fazer o build do Docker:"
echo "   docker-compose down"
echo "   docker-compose up -d --build"
