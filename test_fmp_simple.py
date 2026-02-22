"""
Teste simples para verificar a nova API do FMP.
"""

import requests

# Sua API key
API_KEY = "fNVVAjv4Jlkl7Js2VbCRm7bBivEEQDc3"

print("=" * 80)
print("TESTE SIMPLES DA API FMP")
print("=" * 80)
print()

# Teste 1: Search Symbol (novo endpoint)
print("[1] Testando novo endpoint: /stable/search-symbol")
url = f"https://financialmodelingprep.com/stable/search-symbol?query=AAPL&apikey={API_KEY}"
print(f"URL: {url}")
print()

try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")  # Primeiros 500 caracteres
    print()
    
    if response.status_code == 200:
        data = response.json()
        print("✓ SUCESSO! API está funcionando")
        print(f"Dados recebidos: {len(data)} resultados")
    else:
        print("✗ ERRO! API retornou erro")
        
except Exception as e:
    print(f"✗ ERRO na requisição: {e}")

print()
print("=" * 80)

# Teste 2: Tentar endpoint antigo (para comparação)
print("[2] Testando endpoint antigo (legado): /api/v3/income-statement")
url_old = f"https://financialmodelingprep.com/api/v3/income-statement/AAPL?period=annual&limit=1&apikey={API_KEY}"
print(f"URL: {url_old}")
print()

try:
    response = requests.get(url_old, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    print()
    
    if response.status_code == 200:
        print("✓ Endpoint antigo ainda funciona")
    else:
        print("✗ Endpoint antigo não funciona mais (esperado)")
        
except Exception as e:
    print(f"✗ ERRO na requisição: {e}")

print()
print("=" * 80)
print("TESTE CONCLUÍDO")
print("=" * 80)
