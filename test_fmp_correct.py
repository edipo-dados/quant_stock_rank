"""Test FMP API with correct endpoint structure."""

import requests

API_KEY = "fNVVAjv4Jlkl7Js2VbCRm7bBivEEQDc3"
TICKER = "AAPL"

# Based on the working search-symbol endpoint pattern
# https://financialmodelingprep.com/stable/search-symbol?query=AAPL&apikey=KEY

print("Testing FMP API endpoints")
print("=" * 80)

# Test 1: Search symbol (we know this works)
print("\n1. Testing search-symbol (known working):")
url = "https://financialmodelingprep.com/stable/search-symbol"
params = {"query": TICKER, "apikey": API_KEY}
try:
    response = requests.get(url, params=params, timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ SUCCESS! Got {len(data)} results")
        if data:
            print(f"   Sample: {data[0]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Try financial statements with stable base
print("\n2. Testing income-statement with /stable:")
url = f"https://financialmodelingprep.com/stable/income-statement/{TICKER}"
params = {"apikey": API_KEY, "limit": 1}
try:
    response = requests.get(url, params=params, timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and data:
            print(f"   ✅ SUCCESS! Got {len(data)} records")
            print(f"   Keys: {list(data[0].keys())[:10]}")
        else:
            print(f"   Response: {data}")
    else:
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Try with api/v3 (even though it's legacy, let's see the error)
print("\n3. Testing with /api/v3 (legacy):")
url = f"https://financialmodelingprep.com/api/v3/income-statement/{TICKER}"
params = {"apikey": API_KEY, "limit": 1}
try:
    response = requests.get(url, params=params, timeout=10)
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response: {data}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Try with api/v4
print("\n4. Testing with /api/v4:")
url = f"https://financialmodelingprep.com/api/v4/income-statement/{TICKER}"
params = {"apikey": API_KEY, "limit": 1}
try:
    response = requests.get(url, params=params, timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and data:
            print(f"   ✅ SUCCESS! Got {len(data)} records")
            print(f"   Keys: {list(data[0].keys())[:10]}")
        else:
            print(f"   Response: {data}")
    else:
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Try different endpoint names
print("\n5. Testing alternative endpoint names:")
endpoints = [
    "https://financialmodelingprep.com/stable/financial-statement/income/{TICKER}",
    "https://financialmodelingprep.com/stable/financials/income-statement/{TICKER}",
    "https://financialmodelingprep.com/stable/company/{TICKER}/income-statement",
]

for url_template in endpoints:
    url = url_template.format(TICKER=TICKER)
    params = {"apikey": API_KEY, "limit": 1}
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"   {url}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and data:
                print(f"   ✅ SUCCESS! Got {len(data)} records")
            else:
                print(f"   Response type: {type(data)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("\nNOTE: Check FMP documentation at:")
print("https://site.financialmodelingprep.com/developer/docs")
