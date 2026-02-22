"""Test if FMP v3 API still works with our API key."""

import requests

API_KEY = "fNVVAjv4Jlkl7Js2VbCRm7bBivEEQDc3"
TICKER = "AAPL"
BASE_URL = "https://financialmodelingprep.com/api/v3"

print("Testing FMP v3 API (Legacy but still functional)")
print("=" * 80)

endpoints = {
    "Income Statement": f"/income-statement/{TICKER}",
    "Balance Sheet": f"/balance-sheet-statement/{TICKER}",
    "Cash Flow": f"/cash-flow-statement/{TICKER}",
    "Key Metrics": f"/key-metrics/{TICKER}",
}

for name, endpoint in endpoints.items():
    url = f"{BASE_URL}{endpoint}"
    params = {"apikey": API_KEY, "limit": 1}
    
    print(f"\n{name}:")
    print(f"  URL: {url}")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict) and "Error Message" in data:
                print(f"  ❌ API Error: {data['Error Message']}")
            elif isinstance(data, list):
                if len(data) > 0:
                    print(f"  ✅ SUCCESS! Got {len(data)} records")
                    print(f"  Sample keys: {list(data[0].keys())[:10]}")
                else:
                    print(f"  ⚠️  Empty list returned")
            else:
                print(f"  ⚠️  Unexpected response type: {type(data)}")
        else:
            try:
                error_data = response.json()
                print(f"  ❌ Error: {error_data}")
            except:
                print(f"  ❌ Error: {response.text[:200]}")
                
    except Exception as e:
        print(f"  ❌ Exception: {str(e)}")

print("\n" + "=" * 80)
print("\nConclusion:")
print("If endpoints work, your API key has access to legacy v3 endpoints.")
print("This means you subscribed BEFORE August 31, 2025.")
