"""
Teste de diagnóstico do Yahoo Finance para rodar dentro do Docker.
"""

import yfinance as yf
import requests
import socket
from datetime import datetime

print("=" * 60)
print("DIAGNÓSTICO YAHOO FINANCE - DOCKER")
print("=" * 60)
print()

# 1. Testar resolução DNS
print("[1/5] Testando resolução DNS...")
try:
    ip = socket.gethostbyname("query1.finance.yahoo.com")
    print(f"✓ DNS OK: query1.finance.yahoo.com -> {ip}")
except Exception as e:
    print(f"✗ DNS FALHOU: {e}")

print()

# 2. Testar conectividade HTTP direta
print("[2/5] Testando conectividade HTTP...")
try:
    response = requests.get("https://query1.finance.yahoo.com", timeout=10)
    print(f"✓ HTTP OK: Status {response.status_code}")
except Exception as e:
    print(f"✗ HTTP FALHOU: {e}")

print()

# 3. Testar yfinance com ticker simples
print("[3/5] Testando yfinance com AAPL...")
try:
    stock = yf.Ticker("AAPL")
    hist = stock.history(period="1d")
    if not hist.empty:
        print(f"✓ AAPL OK: Preço = {hist['Close'].iloc[-1]:.2f}")
    else:
        print("✗ AAPL: Sem dados")
except Exception as e:
    print(f"✗ AAPL FALHOU: {e}")

print()

# 4. Testar yfinance com ticker brasileiro
print("[4/5] Testando yfinance com PETR4.SA...")
try:
    stock = yf.Ticker("PETR4.SA")
    hist = stock.history(period="1d")
    if not hist.empty:
        print(f"✓ PETR4.SA OK: Preço = {hist['Close'].iloc[-1]:.2f}")
    else:
        print("✗ PETR4.SA: Sem dados")
except Exception as e:
    print(f"✗ PETR4.SA FALHOU: {e}")

print()

# 5. Verificar configurações de rede
print("[5/5] Verificando configurações de rede...")
try:
    import os
    print(f"  HTTP_PROXY: {os.environ.get('HTTP_PROXY', 'não definido')}")
    print(f"  HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', 'não definido')}")
    print(f"  NO_PROXY: {os.environ.get('NO_PROXY', 'não definido')}")
except Exception as e:
    print(f"✗ Erro ao verificar variáveis: {e}")

print()
print("=" * 60)
print("DIAGNÓSTICO CONCLUÍDO")
print("=" * 60)
