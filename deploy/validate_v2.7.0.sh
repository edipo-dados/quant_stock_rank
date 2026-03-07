#!/bin/bash

# Script de Validação Pós-Deploy - v2.7.0
# Valida que todas as melhorias foram implementadas corretamente

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Contadores
PASSED=0
FAILED=0
WARNINGS=0

# Funções
log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    PASSED=$((PASSED + 1))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    FAILED=$((FAILED + 1))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

# Banner
echo ""
echo "=========================================="
echo "  VALIDAÇÃO PÓS-DEPLOY v2.7.0"
echo "=========================================="
echo ""

# 1. Verificar arquivos novos
log_test "1. Verificando arquivos novos..."

if docker exec quant-ranker-backend test -f app/backtest/portfolio_risk.py; then
    log_pass "portfolio_risk.py existe"
else
    log_fail "portfolio_risk.py não encontrado"
fi

if docker exec quant-ranker-backend test -f scripts/run_enhanced_backtest.py; then
    log_pass "run_enhanced_backtest.py existe"
else
    log_fail "run_enhanced_backtest.py não encontrado"
fi

# 2. Verificar imports
log_test "2. Verificando imports Python..."

if docker exec quant-ranker-backend python -c "from app.backtest.portfolio_risk import PortfolioRiskManager" 2>/dev/null; then
    log_pass "PortfolioRiskManager importa corretamente"
else
    log_fail "Erro ao importar PortfolioRiskManager"
fi

if docker exec quant-ranker-backend python -c "from app.backtest.portfolio import Portfolio" 2>/dev/null; then
    log_pass "Portfolio importa corretamente"
else
    log_fail "Erro ao importar Portfolio"
fi

# 3. Verificar configurações
log_test "3. Verificando configurações..."

config_check=$(docker exec quant-ranker-backend python -c "
from app.config import settings
print(f'{settings.use_volatility_targeting},{settings.use_sector_limits},{settings.target_portfolio_volatility},{settings.max_sector_exposure}')
" 2>/dev/null)

if echo "$config_check" | grep -q "True,True,0.15,0.3"; then
    log_pass "Configurações de risco corretas"
else
    log_warn "Configurações de risco diferentes do esperado: $config_check"
fi

# 4. Verificar métodos novos
log_test "4. Verificando métodos novos..."

if docker exec quant-ranker-backend python -c "
from app.backtest.portfolio import Portfolio
p = Portfolio(['TEST'])
assert hasattr(p, 'apply_volatility_targeting'), 'Método apply_volatility_targeting não encontrado'
assert hasattr(p, 'apply_sector_limits'), 'Método apply_sector_limits não encontrado'
print('OK')
" 2>/dev/null | grep -q "OK"; then
    log_pass "Métodos de Portfolio implementados"
else
    log_fail "Métodos de Portfolio não encontrados"
fi

# 5. Verificar containers
log_test "5. Verificando containers..."

if docker ps | grep -q "quant-ranker-backend"; then
    log_pass "Backend container rodando"
else
    log_fail "Backend container não está rodando"
fi

if docker ps | grep -q "quant-ranker-frontend"; then
    log_pass "Frontend container rodando"
else
    log_warn "Frontend container não está rodando"
fi

# 6. Verificar API
log_test "6. Verificando API..."

if curl -s http://localhost:8000/health | grep -q "ok\|healthy"; then
    log_pass "API respondendo"
else
    log_fail "API não está respondendo"
fi

# 7. Verificar banco de dados
log_test "7. Verificando banco de dados..."

db_check=$(docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import AssetInfo, RawPriceDaily, RankingHistory
db = SessionLocal()
assets = db.query(AssetInfo).count()
prices = db.query(RawPriceDaily).count()
rankings = db.query(RankingHistory).count()
db.close()
print(f'{assets},{prices},{rankings}')
" 2>/dev/null)

IFS=',' read -r assets prices rankings <<< "$db_check"

if [ "$assets" -gt 0 ]; then
    log_pass "AssetInfo: $assets registros"
else
    log_fail "AssetInfo vazio"
fi

if [ "$prices" -gt 0 ]; then
    log_pass "RawPriceDaily: $prices registros"
else
    log_warn "RawPriceDaily vazio"
fi

if [ "$rankings" -gt 0 ]; then
    log_pass "RankingHistory: $rankings registros"
else
    log_warn "RankingHistory vazio (necessário para backtest)"
fi

# 8. Verificar setores
log_test "8. Verificando informações de setores..."

sectors_check=$(docker exec quant-ranker-backend python -c "
from app.models.database import SessionLocal
from app.models.schemas import AssetInfo
db = SessionLocal()
with_sector = db.query(AssetInfo).filter(AssetInfo.sector.isnot(None)).count()
total = db.query(AssetInfo).count()
db.close()
print(f'{with_sector},{total}')
" 2>/dev/null)

IFS=',' read -r with_sector total <<< "$sectors_check"

if [ "$with_sector" -gt 0 ]; then
    coverage=$((with_sector * 100 / total))
    log_pass "Setores: $with_sector/$total ativos ($coverage%)"
    if [ "$coverage" -lt 50 ]; then
        log_warn "Cobertura de setores baixa (<50%)"
    fi
else
    log_warn "Nenhum ativo com informação de setor"
fi

# 9. Testar cálculo de volatilidade
log_test "9. Testando cálculo de volatilidade..."

if docker exec quant-ranker-backend python -c "
from app.backtest.portfolio_risk import PortfolioRiskManager
from datetime import date
manager = PortfolioRiskManager()
vols = manager.get_asset_volatilities(['ITUB3', 'PETR4'], date(2026, 3, 1), 90)
assert len(vols) > 0, 'Nenhuma volatilidade calculada'
print('OK')
" 2>/dev/null | grep -q "OK"; then
    log_pass "Cálculo de volatilidade funciona"
else
    log_warn "Erro ao calcular volatilidades (pode ser falta de dados)"
fi

# 10. Testar script de backtest enhanced
log_test "10. Testando script de backtest enhanced..."

if docker exec quant-ranker-backend python -c "
import sys
sys.path.insert(0, '/app')
with open('scripts/run_enhanced_backtest.py', 'r') as f:
    code = f.read()
    compile(code, 'run_enhanced_backtest.py', 'exec')
print('OK')
" 2>/dev/null | grep -q "OK"; then
    log_pass "Script de backtest enhanced válido"
else
    log_fail "Erro de sintaxe no script de backtest enhanced"
fi

# 11. Verificar logs
log_test "11. Verificando logs recentes..."

error_count=$(docker logs quant-ranker-backend --tail 100 2>&1 | grep -i "error" | grep -v "ERROR_LEVEL\|errors='coerce'" | wc -l)

if [ "$error_count" -eq 0 ]; then
    log_pass "Nenhum erro nos logs recentes"
elif [ "$error_count" -lt 5 ]; then
    log_warn "$error_count erro(s) nos logs recentes"
else
    log_fail "$error_count erros nos logs recentes"
fi

# 12. Verificar performance
log_test "12. Verificando performance..."

# Testar tempo de resposta da API
response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8000/health)
response_ms=$(echo "$response_time * 1000" | bc)

if (( $(echo "$response_time < 1.0" | bc -l) )); then
    log_pass "API response time: ${response_ms}ms"
else
    log_warn "API response time alto: ${response_ms}ms"
fi

# Verificar uso de memória
mem_usage=$(docker stats --no-stream --format "{{.MemPerc}}" quant-ranker-backend | sed 's/%//')

if (( $(echo "$mem_usage < 80" | bc -l) )); then
    log_pass "Uso de memória: ${mem_usage}%"
else
    log_warn "Uso de memória alto: ${mem_usage}%"
fi

# Resumo
echo ""
echo "=========================================="
echo "  RESUMO DA VALIDAÇÃO"
echo "=========================================="
echo ""
echo -e "${GREEN}Testes Passados:${NC} $PASSED"
echo -e "${YELLOW}Avisos:${NC} $WARNINGS"
echo -e "${RED}Testes Falhados:${NC} $FAILED"
echo ""

# Resultado final
if [ "$FAILED" -eq 0 ]; then
    if [ "$WARNINGS" -eq 0 ]; then
        echo -e "${GREEN}✓ VALIDAÇÃO COMPLETA - SISTEMA OK${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ VALIDAÇÃO COMPLETA - SISTEMA OK COM AVISOS${NC}"
        echo ""
        echo "Revisar avisos acima. Sistema está funcional mas pode precisar de ajustes."
        exit 0
    fi
else
    echo -e "${RED}✗ VALIDAÇÃO FALHOU - REVISAR ERROS${NC}"
    echo ""
    echo "Erros críticos encontrados. Considere rollback ou correções."
    exit 1
fi
