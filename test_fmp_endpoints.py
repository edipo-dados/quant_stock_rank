"""Test script to discover correct FMP API endpoints."""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = "fNVVAjv4Jlkl7Js2VbCRm7bBivEEQDc3"
BASE_URL = "https://financialmodelingprep.com/stable"

# Test ticker
TICKER = "AAPL"

# Possible endpoint patterns based on FMP documentation
endpoints_to_test = [
    # Income Statement
    f"/income-statement/{TICKER}",
    f"/financials/income-statement/{TICKER}",
    f"/api/v4/income-statement/{TICKER}",
    
    # Balance Sheet
    f"/balance-sheet-statement/{TICKER}",
    f"/financials/balance-sheet-statement/{TICKER}",
    f"/api/v4/balance-sheet-statement/{TICKER}",
    
    # Cash Flow
    f"/cash-flow-statement/{TICKER}",
    f"/financials/cash-flow-statement/{TICKER}",
    f"/api/v4/cash-flow-statement/{TICKER}",
    
    # Key Metrics
    f"/key-metrics/{TICKER}",
    f"/financials/key-metrics/{TICKER}",
    f"/api/v4/key-metrics/{TICKER}",
    f"/key-metrics-ttm/{TICKER}",
]

print(f"Testing FMP API endpoints with ticker: {TICKER}")
print(f"Base URL: {BASE_URL}")
print(f"API Key: {API_KEY[:10]}...")
print("=" * 80)

working_endpoints = []

for endpoint in endpoints_to_test:
    url = f"{BASE_URL}{endpoint}"
    params = {"apikey": API_KEY, "limit": 1}
    
    try:
        print(f"\nTesting: {endpoint}")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if it's an error response
            if isinstance(data, dict) and "Error Message" in data:
                print(f"  ❌ Error: {data['Error Message'][:100]}")
            elif isinstance(data, list) and len(data) > 0:
                print(f"  ✅ SUCCESS! Got {len(data)} records")
                print(f"     Sample keys: {list(data[0].keys())[:5]}")
                working_endpoints.append(endpoint)
            elif isinstance(data, dict) and len(data) > 0:
                print(f"  ✅ SUCCESS! Got dict response")
                print(f"     Keys: {list(data.keys())[:5]}")
                working_endpoints.append(endpoint)
            else:
                print(f"  ⚠️  Empty response")
        else:
            print(f"  ❌ HTTP {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Exception: {str(e)[:100]}")

print("\n" + "=" * 80)
print("\nWORKING ENDPOINTS:")
for endpoint in working_endpoints:
    print(f"  ✅ {endpoint}")

if not working_endpoints:
    print("  ❌ No working endpoints found!")
    print("\nTrying alternative base URLs...")
    
    # Try v4 API directly
    alt_base = "https://financialmodelingprep.com/api/v4"
    test_endpoint = f"/income-statement/{TICKER}"
    url = f"{alt_base}{test_endpoint}"
    params = {"apikey": API_KEY, "limit": 1}
    
    print(f"\nTesting v4 API: {url}")
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response type: {type(data)}")
            if isinstance(data, list) and len(data) > 0:
                print(f"✅ V4 API WORKS! Keys: {list(data[0].keys())[:5]}")
            elif isinstance(data, dict):
                print(f"Response: {data}")
    except Exception as e:
        print(f"Error: {e}")
