"""Teste rápido da API local."""

import os
os.environ['DATABASE_URL'] = 'sqlite:///./quant_ranker.db'

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("Testando API local...")
print("=" * 50)

# Teste 1: Health check
print("\n[1] GET /health")
response = client.get("/health")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Teste 2: Ranking
print("\n[2] GET /api/v1/ranking")
response = client.get("/api/v1/ranking")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    if isinstance(data, list):
        print(f"Ativos retornados: {len(data)}")
        if data:
            print(f"Primeiro ativo: {data[0]}")
    elif isinstance(data, dict):
        print(f"Resposta: {data}")
else:
    print(f"Erro: {response.text}")

# Teste 3: Top ativos
print("\n[3] GET /api/v1/top?limit=5")
response = client.get("/api/v1/top?limit=5")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    if isinstance(data, dict) and 'rankings' in data:
        rankings = data['rankings']
        print(f"Top ativos: {len(rankings)}")
        for i, asset in enumerate(rankings[:5], 1):
            print(f"  {i}. {asset.get('ticker')} - Score: {asset.get('final_score'):.3f}")
    else:
        print(f"Resposta: {data}")
else:
    print(f"Erro: {response.text}")

print("\n" + "=" * 50)
print("✓ Testes concluídos!")
