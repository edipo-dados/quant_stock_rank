#!/bin/bash

# Script para limpar dados e rodar pipeline FULL
# Uso: ./scripts/clear_and_run_full.sh [mode] [limit]
#
# Exemplos:
#   ./scripts/clear_and_run_full.sh liquid 10    # 10 ativos líquidos
#   ./scripts/clear_and_run_full.sh liquid 50    # 50 ativos (produção)
#   ./scripts/clear_and_run_full.sh test         # 5 ativos teste

MODE=${1:-liquid}
LIMIT=${2:-10}

echo "=========================================="
echo "LIMPAR DADOS E RODAR PIPELINE FULL"
echo "=========================================="
echo "Modo: $MODE"
echo "Limit: $LIMIT"
echo ""
echo "⚠️  ATENÇÃO: Esta operação irá DELETAR todos os dados!"
echo ""
read -p "Digite 'CONFIRMAR' para continuar: " CONFIRM

if [ "$CONFIRM" != "CONFIRMAR" ]; then
    echo "Operação cancelada."
    exit 0
fi

echo ""
echo "Executando..."
python scripts/clear_and_run_full.py --mode $MODE --limit $LIMIT --no-confirm

echo ""
echo "=========================================="
echo "CONCLUÍDO!"
echo "=========================================="
