#!/bin/bash
# Script para limpar espaço em disco no EC2

set -e

echo "=========================================="
echo "EC2 DISK CLEANUP"
echo "=========================================="

echo ""
echo "📊 Espaço em disco ANTES da limpeza:"
df -h /

echo ""
echo "🧹 Limpando Docker..."

# Parar containers
echo "1. Parando containers..."
docker-compose down 2>/dev/null || true

# Remover containers parados
echo "2. Removendo containers parados..."
docker container prune -f

# Remover imagens não usadas
echo "3. Removendo imagens não usadas..."
docker image prune -a -f

# Remover volumes não usados
echo "4. Removendo volumes não usados..."
docker volume prune -f

# Remover networks não usadas
echo "5. Removendo networks não usadas..."
docker network prune -f

# Remover build cache
echo "6. Removendo build cache..."
docker builder prune -a -f

echo ""
echo "🧹 Limpando sistema..."

# Limpar apt cache
echo "7. Limpando apt cache..."
sudo apt-get clean
sudo apt-get autoclean
sudo apt-get autoremove -y

# Limpar logs antigos
echo "8. Limpando logs antigos..."
sudo journalctl --vacuum-time=3d

# Limpar tmp
echo "9. Limpando /tmp..."
sudo rm -rf /tmp/*

echo ""
echo "=========================================="
echo "✅ LIMPEZA CONCLUÍDA"
echo "=========================================="

echo ""
echo "📊 Espaço em disco APÓS a limpeza:"
df -h /

echo ""
echo "💡 Espaço liberado:"
echo "   Antes: $(df -h / | awk 'NR==2 {print $3}')"
echo "   Depois: $(df -h / | awk 'NR==2 {print $3}')"
echo "   Disponível: $(df -h / | awk 'NR==2 {print $4}')"
