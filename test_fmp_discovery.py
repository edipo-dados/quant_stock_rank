"""
Descobrir a estrutura correta da nova API FMP.
"""

import requests

API_KEY = "fNVVAjv4Jlkl7Js2VbCRm7bBivEEQDc3"

print("=" * 80)
print("DESCOBRINDO ESTRUTURA DA NOVA API FMP")
print("=" * 80)
print()

# Testar diferentes bases
bases = [
    "https://financialmodelingprep.com/stable",
    "https://financialmodelingprep.com/api/v4",
    "https://site.financialmodelingprep.com/stable",
    "https://site.financialmodelingprep.com/api/v4",
]

endpoints_to_test = [
    "/income-statement/AAPL",
    "/financial-statements/income-statement/AAPL",
    "/company/income-statement/AAPL",
]

for base in bases:
    print(f"\n{'='*80}")
    print(f"BASE: {base}")
    print(f"{'='*80}")
    
    for endpoint in endpoints_to_test:
        url = f"{base}{endpoint}?period=annual&limit=1&apikey={API_KEY}"
        print(f"\nTestando: {endpoint}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  ✓✓✓ ENCONTRADO! ✓✓✓")
                data = response.json()
                print(f"  Dados: {type(data)}")
                if isinstance(data, list) and len(data) > 0:
                    print(f"  Chaves: {list(data[0].keys())[:10]}")
                break
            elif response.status_code != 404:
                print(f"  Resposta: {response.text[:200]}")
                
        except Exception as e:
            print(f"  Erro: {e}")

print("\n" + "=" * 80)
print("Testando endpoint que funcionou: search-symbol")
url = f"https://financialmodelingprep.com/stable/search-symbol?query=AAPL&apikey={API_KEY}"
response = requests.get(url)
print(f"Status: {response.status_code}")
print(f"Dados: {response.json()[:2]}")  # Primeiros 2 resultados
