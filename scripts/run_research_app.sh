#!/bin/bash

# Script para executar aplicação Streamlit de research

echo "=========================================="
echo "Quant Research – Backtest Engine"
echo "=========================================="
echo ""
echo "Iniciando aplicação Streamlit..."
echo ""

# Executar Streamlit
streamlit run app/research/streamlit_backtest_app.py --server.port 8502

echo ""
echo "=========================================="
echo "Aplicação encerrada"
echo "=========================================="
