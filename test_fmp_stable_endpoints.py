"""Test FMP stable API with correct endpoint paths."""

import requests

API_KEY = "fNVVAjv4Jlkl7Js2VbCRm7bBivEEQDc3"
TICKER = "AAPL"

print("Testing FMP Stable API Endpoints")
print("=" * 80)

# Test with /stable base URL but v3-style endpoint paths
base_url = "https://financialmodelingprep.com/stable"

endpoints = {
    "Income Statement": f"/income-statement/{TICKER}",
    "Balance Sheet": f"/balance-sheet-statement/{TICKER}",
    "Cash Flow": f"/cash-flow-statement/{TICKER}",
    "Key Metrics": f"/key-metrics/{TICKER}",
    "Key Metrics TTM": f"/key-metrics-ttm/{TICKER}",
}

for name, endpoint in endpoints.items():
    url = f"{base_url}{endpoint}"
    params = {"apikey": API_KEY, "limit": 1}
    
    print(f"\n{name}:")
    print(f"  URL: {url}")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict) and "Error Message" in data:
                print(f"  ❌ API Error: {data['Error Message'][:100]}")
            elif isinstance(data, list):
                if len(data) > 0:
                    print(f"  ✅ SUCCESS! Got {len(data)} records")
                    print(f"  Sample keys: {list(data[0].keys())[:10]}")
                else:
                    print(f"  ⚠️  Empty list returned")
            elif isinstance(data, dict):
                print(f"  ✅ SUCCESS! Got dict response")
                print(f"  Keys: {list(data.keys())[:10]}")
            else:
                print(f"  ⚠️  Unexpected response type: {type(data)}")
        else:
            try:
                error_data = response.json()
                print(f"  ❌ Error: {error_data}")
            except:
                print(f"  ❌ Error: {response.text[:200]}")
                
    except Exception as e:
        print(f"  ❌ Exception: {str(e)[:100]}")

print("\n" + "=" * 80)
print("\nConclusion:")
print("If all endpoints return 404, the /stable base URL doesn't support these paths yet.")
print("If they return 403 with 'Legacy Endpoint' message, these are also blocked.")
print("If they return 200, we found the correct endpoints!")
