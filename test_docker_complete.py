"""
Teste completo do deployment Docker.
"""

import requests
import time

print("=" * 70)
print("TESTE COMPLETO DO DEPLOYMENT DOCKER")
print("=" * 70)
print()

# URLs
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:8501"

# 1. Testar Backend Health
print("[1/5] Testando Backend Health...")
try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=5)
    if response.status_code == 200:
        print(f"✓ Backend Health OK: {response.json()}")
    else:
        print(f"✗ Backend Health FALHOU: Status {response.status_code}")
except Exception as e:
    print(f"✗ Backend Health ERRO: {e}")

print()

# 2. Testar API de Ranking
print("[2/5] Testando API de Ranking...")
try:
    response = requests.get(f"{BACKEND_URL}/api/v1/ranking", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ API Ranking OK")
        print(f"  Data: {data['date']}")
        print(f"  Total de ativos: {data['total_assets']}")
        print(f"  Primeiro ativo: {data['rankings'][0]['ticker']} (score: {data['rankings'][0]['final_score']})")
    else:
        print(f"✗ API Ranking FALHOU: Status {response.status_code}")
except Exception as e:
    print(f"✗ API Ranking ERRO: {e}")

print()

# 3. Testar API de Top Assets
print("[3/5] Testando API de Top Assets...")
try:
    response = requests.get(f"{BACKEND_URL}/api/v1/top?n=3", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ API Top Assets OK")
        print(f"  Top 3 ativos: {[a['ticker'] for a in data['top_assets']]}")
    else:
        print(f"✗ API Top Assets FALHOU: Status {response.status_code}")
except Exception as e:
    print(f"✗ API Top Assets ERRO: {e}")

print()

# 4. Testar API de Asset Details
print("[4/5] Testando API de Asset Details...")
try:
    response = requests.get(f"{BACKEND_URL}/api/v1/asset/PETR4.SA", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ API Asset Details OK")
        print(f"  Ticker: {data['ticker']}")
        print(f"  Score: {data['score']['final_score']}")
        print(f"  Rank: {data['score']['rank']}")
    else:
        print(f"✗ API Asset Details FALHOU: Status {response.status_code}")
except Exception as e:
    print(f"✗ API Asset Details ERRO: {e}")

print()

# 5. Testar Frontend
print("[5/5] Testando Frontend...")
try:
    response = requests.get(f"{FRONTEND_URL}/_stcore/health", timeout=10)
    if response.status_code == 200:
        print(f"✓ Frontend Health OK")
    else:
        print(f"✗ Frontend Health FALHOU: Status {response.status_code}")
except Exception as e:
    print(f"✗ Frontend Health ERRO: {e}")

print()
print("=" * 70)
print("TESTE CONCLUÍDO")
print("=" * 70)
print()
print("Acesse a aplicação em:")
print(f"  Frontend: {FRONTEND_URL}")
print(f"  Backend API: {BACKEND_URL}/docs")
