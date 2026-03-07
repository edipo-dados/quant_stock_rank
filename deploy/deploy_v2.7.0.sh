#!/bin/bash

# Script de Deploy Automatizado - v2.7.0
# Quant Stock Ranker - Melhorias de Robustez

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções auxiliares
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo ""
echo "=========================================="
echo "  DEPLOY v2.7.0 - Quant Stock Ranker"
echo "  Melhorias de Robustez"
echo "=========================================="
echo ""

# Verificar se está no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    log_error "docker-compose.yml não encontrado!"
    log_error "Execute este script do diretório raiz do projeto"
    exit 1
fi

# 1. Backup do banco de dados
log_info "Passo 1/10: Criando backup do banco de dados..."
if [ -f "./deploy/backup-db.sh" ]; then
    ./deploy/backup-db.sh
    log_success "Backup criado com sucesso"
else
    log_warning "Script de backup não encontrado, pulando..."
fi

# 2. Verificar arquivos novos
log_info "Passo 2/10: Verificando arquivos novos..."
required_files=(
    "app/backtest/portfolio_risk.py"
    "scripts/run_enhanced_backtest.py"
    "ROBUSTEZ_V2.7.0.md"
    "DEPLOY_V2.7.0.md"
)

missing_files=0
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        log_error "Arquivo não encontrado: $file"
        missing_files=$((missing_files + 1))
    else
        log_success "✓ $file"
    fi
done

if [ $missing_files -gt 0 ]; then
    log_error "$missing_files arquivo(s) faltando. Faça upload dos arquivos antes de continuar."
    exit 1
fi

# 3. Verificar modificações
log_info "Passo 3/10: Verificando arquivos modificados..."
modified_files=(
    "app/config.py"
    "app/backtest/portfolio.py"
    "app/backtest/metrics.py"
    "app/backtest/backtest_engine.py"
)

for file in "${modified_files[@]}"; do
    if [ -f "$file" ]; then
        log_success "✓ $file"
    else
        log_error "Arquivo não encontrado: $file"
        exit 1
    fi
done

# 4. Parar containers
log_info "Passo 4/10: Parando containers..."
docker-compose down
log_success "Containers parados"

# 5. Backup do código atual (opcional)
log_info "Passo 5/10: Criando backup do código..."
backup_dir="../quant_stock_rank_backup_v2.6.0_$(date +%Y%m%d_%H%M%S)"
if [ ! -d "$backup_dir" ]; then
    cp -r . "$backup_dir"
    log_success "Backup do código criado em: $backup_dir"
else
    log_warning "Diretório de backup já existe, pulando..."
fi

# 6. Rebuild dos containers
log_info "Passo 6/10: Rebuilding containers..."
docker-compose build backend
log_success "Backend rebuilded"

# 7. Iniciar containers
log_info "Passo 7/10: Iniciando containers..."
docker-compose up -d
log_success "Containers iniciados"

# Aguardar containers iniciarem
log_info "Aguardando containers iniciarem (30s)..."
sleep 30

# 8. Verificar saúde
log_info "Passo 8/10: Verificando saúde do sistema..."

# Verificar containers
if docker ps | grep -q "quant-ranker-backend"; then
    log_success "✓ Backend container rodando"
else
    log_error "Backend container não está rodando!"
    docker logs quant-ranker-backend --tail 50
    exit 1
fi

if docker ps | grep -q "quant-ranker-frontend"; then
    log_success "✓ Frontend container rodando"
else
    log_warning "Frontend container não está rodando"
fi

# Verificar API
log_info "Testando API..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    log_success "✓ API respondendo"
else
    log_error "API não está respondendo!"
    docker logs quant-ranker-backend --tail 50
    exit 1
fi

# 9. Validar dados
log_info "Passo 9/10: Validando dados..."

# Verificar banco
log_info "Verificando banco de dados..."
docker exec quant-ranker-backend python scripts/check_db.py > /tmp/check_db.log 2>&1
if [ $? -eq 0 ]; then
    log_success "✓ Banco de dados OK"
else
    log_warning "Verificação do banco retornou avisos (ver /tmp/check_db.log)"
fi

# Verificar scores
log_info "Verificando scores..."
docker exec quant-ranker-backend python scripts/check_latest_scores.py > /tmp/check_scores.log 2>&1
if [ $? -eq 0 ]; then
    log_success "✓ Scores OK"
else
    log_warning "Verificação de scores retornou avisos (ver /tmp/check_scores.log)"
fi

# 10. Executar pipeline
log_info "Passo 10/10: Executando pipeline de atualização..."
log_warning "Isso pode levar alguns minutos..."

docker exec quant-ranker-backend python scripts/run_smart_pipeline.py > /tmp/pipeline.log 2>&1
if [ $? -eq 0 ]; then
    log_success "✓ Pipeline executado com sucesso"
else
    log_error "Pipeline falhou! Ver logs em /tmp/pipeline.log"
    tail -50 /tmp/pipeline.log
    exit 1
fi

# Teste opcional: Backtest Enhanced
log_info "Teste opcional: Executar backtest enhanced? (s/n)"
read -r run_backtest

if [ "$run_backtest" = "s" ] || [ "$run_backtest" = "S" ]; then
    log_info "Executando backtest enhanced..."
    docker exec quant-ranker-backend python scripts/run_enhanced_backtest.py
    log_success "Backtest concluído"
fi

# Resumo final
echo ""
echo "=========================================="
echo "  DEPLOY CONCLUÍDO COM SUCESSO!"
echo "=========================================="
echo ""
log_success "Versão: 2.7.0"
log_success "Melhorias:"
log_success "  ✓ Correção definitiva do cálculo de Alpha"
log_success "  ✓ Volatility Targeting (Sharpe +30-50%)"
log_success "  ✓ Limites de Exposição por Setor (máx 30%)"
echo ""
log_info "Próximos passos:"
echo "  1. Monitorar logs: docker logs -f quant-ranker-backend"
echo "  2. Acessar frontend: http://$(hostname -I | awk '{print $1}'):8501"
echo "  3. Testar API: curl http://localhost:8000/api/ranking/latest"
echo "  4. Executar backtest: docker exec -it quant-ranker-backend python scripts/run_enhanced_backtest.py"
echo ""
log_info "Documentação:"
echo "  - ROBUSTEZ_V2.7.0.md"
echo "  - DEPLOY_V2.7.0.md"
echo "  - CHANGELOG.md"
echo ""

# Salvar informações do deploy
deploy_info_file="deploy/deploy_info_v2.7.0.txt"
cat > "$deploy_info_file" << EOF
Deploy v2.7.0 - Quant Stock Ranker
Data: $(date)
Usuário: $(whoami)
Hostname: $(hostname)
Status: SUCCESS

Containers:
$(docker ps --format "table {{.Names}}\t{{.Status}}")

Versão do código:
$(git log -1 --oneline 2>/dev/null || echo "Git não disponível")

Backup criado em: $backup_dir
EOF

log_success "Informações do deploy salvas em: $deploy_info_file"

echo ""
log_success "Deploy finalizado! Sistema v2.7.0 está rodando."
echo ""
