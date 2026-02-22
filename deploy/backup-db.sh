#!/bin/bash

# Script de Backup Automático do Banco de Dados
# Sistema de Ranking Quantitativo

set -e

# Configurações
BACKUP_DIR="/home/deploy/backups"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="quant_ranker_backup_${DATE}.sql"

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
echo "Backup do Banco de Dados - Quant Ranker"
echo "=================================================="
echo ""

# Criar diretório de backup se não existir
mkdir -p "$BACKUP_DIR"

# Fazer backup
print_info "Iniciando backup..."

if docker compose exec -T postgres pg_dump -U quant_user quant_ranker > "${BACKUP_DIR}/${BACKUP_FILE}"; then
    print_success "Backup criado: ${BACKUP_FILE}"
    
    # Comprimir backup
    print_info "Comprimindo backup..."
    gzip "${BACKUP_DIR}/${BACKUP_FILE}"
    print_success "Backup comprimido: ${BACKUP_FILE}.gz"
    
    # Calcular tamanho
    SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}.gz" | cut -f1)
    print_info "Tamanho: ${SIZE}"
    
else
    print_error "Falha ao criar backup"
    exit 1
fi

# Remover backups antigos
print_info "Removendo backups com mais de ${RETENTION_DAYS} dias..."
find "$BACKUP_DIR" -name "quant_ranker_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
print_success "Backups antigos removidos"

# Listar backups existentes
echo ""
print_info "Backups disponíveis:"
ls -lh "$BACKUP_DIR" | grep "quant_ranker_backup_"

echo ""
print_success "Backup concluído com sucesso!"
echo ""

# Opcional: Upload para S3 ou outro storage
# Descomente e configure se necessário
# print_info "Fazendo upload para S3..."
# aws s3 cp "${BACKUP_DIR}/${BACKUP_FILE}.gz" s3://seu-bucket/backups/
# print_success "Upload concluído"
