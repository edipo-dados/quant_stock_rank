#!/bin/bash

# Script de Restauração do Banco de Dados
# Sistema de Ranking Quantitativo

set -e

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

echo "=================================================="
echo "Restauração do Banco de Dados - Quant Ranker"
echo "=================================================="
echo ""

# Verificar se arquivo de backup foi fornecido
if [ -z "$1" ]; then
    print_error "Uso: $0 <arquivo_backup.sql.gz>"
    echo ""
    echo "Backups disponíveis:"
    ls -lh /home/deploy/backups/ | grep "quant_ranker_backup_"
    exit 1
fi

BACKUP_FILE="$1"

# Verificar se arquivo existe
if [ ! -f "$BACKUP_FILE" ]; then
    print_error "Arquivo não encontrado: $BACKUP_FILE"
    exit 1
fi

# Confirmar restauração
echo ""
print_info "ATENÇÃO: Esta operação irá SUBSTITUIR todos os dados atuais!"
echo ""
read -p "Tem certeza que deseja continuar? (digite 'sim' para confirmar): " CONFIRM

if [ "$CONFIRM" != "sim" ]; then
    print_info "Operação cancelada"
    exit 0
fi

echo ""
print_info "Iniciando restauração..."

# Descomprimir se necessário
if [[ "$BACKUP_FILE" == *.gz ]]; then
    print_info "Descomprimindo backup..."
    gunzip -c "$BACKUP_FILE" > /tmp/restore_temp.sql
    SQL_FILE="/tmp/restore_temp.sql"
else
    SQL_FILE="$BACKUP_FILE"
fi

# Parar aplicação
print_info "Parando aplicação..."
docker compose stop backend frontend

# Restaurar banco
print_info "Restaurando banco de dados..."
if docker compose exec -T postgres psql -U quant_user quant_ranker < "$SQL_FILE"; then
    print_success "Banco de dados restaurado com sucesso"
else
    print_error "Falha ao restaurar banco de dados"
    docker compose start backend frontend
    exit 1
fi

# Limpar arquivo temporário
if [ -f "/tmp/restore_temp.sql" ]; then
    rm /tmp/restore_temp.sql
fi

# Reiniciar aplicação
print_info "Reiniciando aplicação..."
docker compose start backend frontend

# Aguardar serviços
print_info "Aguardando serviços iniciarem..."
sleep 10

# Verificar saúde
print_info "Verificando saúde dos serviços..."
if curl -s http://localhost:8000/health > /dev/null; then
    print_success "Backend está saudável"
else
    print_error "Backend não está respondendo"
fi

echo ""
print_success "Restauração concluída!"
echo ""
