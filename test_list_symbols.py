"""Test listing all available stock symbols from FMP and Yahoo Finance."""

import requests
import yfinance as yf

print("=" * 80)
print("TESTE 1: FMP - Listar Símbolos de Ações")
print("=" * 80)

API_KEY = "fNVVAjv4Jlkl7Js2VbCRm7bBivEEQDc3"

# Test FMP endpoints for listing stocks
fmp_endpoints = {
    "Stock List (v3)": "https://financialmodelingprep.com/api/v3/stock/list",
    "Stock List (stable)": "https://financialmodelingprep.com/stable/stock/list",
    "Available Traded List (v3)": "https://financialmodelingprep.com/api/v3/available-traded/list",
    "Available Traded (stable)": "https://financialmodelingprep.com/stable/available-traded/list",
    "Symbol List (v3)": "https://financialmodelingprep.com/api/v3/symbol/available-indexes",
    "Search (stable)": "https://financialmodelingprep.com/stable/search",
}

for name, url in fmp_endpoints.items():
    print(f"\n{name}:")
    print(f"  URL: {url}")
    
    try:
        response = requests.get(url, params={"apikey": API_KEY}, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict) and "Error Message" in data:
                print(f"  ❌ Error: {data['Error Message'][:100]}")
            elif isinstance(data, list):
                print(f"  ✅ SUCCESS! Got {len(data)} symbols")
                if len(data) > 0:
                    print(f"  Sample: {data[0]}")
            elif isinstance(data, dict):
                print(f"  ✅ Got dict response")
                print(f"  Keys: {list(data.keys())}")
            else:
                print(f"  ⚠️  Unexpected type: {type(data)}")
        else:
            try:
                error = response.json()
                print(f"  ❌ Error: {error}")
            except:
                print(f"  ❌ Error: {response.text[:100]}")
    except Exception as e:
        print(f"  ❌ Exception: {str(e)[:100]}")

print("\n" + "=" * 80)
print("TESTE 2: Yahoo Finance - Listar Símbolos")
print("=" * 80)

# Yahoo Finance doesn't have a direct "list all stocks" API
# But we can use common indices to get lists of stocks

print("\nYahoo Finance não tem API direta para listar TODAS as ações.")
print("Mas podemos usar índices conhecidos:")

indices = {
    "S&P 500": "^GSPC",
    "Dow Jones": "^DJI",
    "NASDAQ": "^IXIC",
    "Russell 2000": "^RUT",
}

print("\nÍndices disponíveis:")
for name, symbol in indices.items():
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        print(f"  ✅ {name} ({symbol}): {info.get('longName', 'N/A')}")
    except Exception as e:
        print(f"  ❌ {name} ({symbol}): {str(e)[:50]}")

print("\n" + "=" * 80)
print("TESTE 3: Buscar Componentes de Índices")
print("=" * 80)

# Try to get S&P 500 components from Wikipedia (common approach)
print("\nBuscando componentes do S&P 500 via Wikipedia...")
try:
    import pandas as pd
    
    # Wikipedia has a table with S&P 500 components
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    sp500_table = tables[0]
    
    print(f"  ✅ SUCCESS! Got {len(sp500_table)} S&P 500 companies")
    print(f"\n  Primeiras 5 empresas:")
    print(sp500_table[['Symbol', 'Security', 'GICS Sector']].head())
    
    # Test if we can get data for these symbols
    print(f"\n  Testando dados para primeiras 3 empresas:")
    for idx, row in sp500_table.head(3).iterrows():
        symbol = row['Symbol']
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            print(f"    ✅ {symbol}: {info.get('longName', 'N/A')}")
        except Exception as e:
            print(f"    ❌ {symbol}: {str(e)[:50]}")
            
except Exception as e:
    print(f"  ❌ Error: {str(e)}")

print("\n" + "=" * 80)
print("TESTE 4: Ações Brasileiras (B3)")
print("=" * 80)

# Test Brazilian stocks
br_stocks = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "WEGE3.SA"]

print("\nTestando ações brasileiras no Yahoo Finance:")
for symbol in br_stocks:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        print(f"  ✅ {symbol}: {info.get('longName', 'N/A')}")
    except Exception as e:
        print(f"  ❌ {symbol}: {str(e)[:50]}")

print("\n" + "=" * 80)
print("\nCONCLUSÕES:")
print("=" * 80)
print("""
1. FMP: Verificar se endpoints de listagem funcionam com sua chave
2. Yahoo Finance: 
   - Não tem API para listar TODAS as ações
   - Pode buscar componentes de índices (S&P 500, etc) via Wikipedia
   - Funciona bem para ações específicas quando você sabe o símbolo
3. Para B3 (Brasil): Adicionar sufixo .SA aos símbolos
4. Alternativa: Manter lista manual de símbolos que você quer acompanhar
""")
