"""Test final da API."""
import requests

# Test ranking endpoint
r = requests.get('http://localhost:8000/api/v1/ranking')
print(f'Status: {r.status_code}')

if r.status_code == 200:
    data = r.json()
    print(f'Data: {data["date"]}')
    print(f'Total de ativos: {data["total_assets"]}')
    print(f'\nTop 3:')
    for i, asset in enumerate(data["rankings"][:3], 1):
        print(f'  {i}. {asset["ticker"]} - Score: {asset["final_score"]:.3f}')
        print(f'     Elegível: {asset["passed_eligibility"]}')
        if asset["exclusion_reasons"]:
            print(f'     Razões: {asset["exclusion_reasons"]}')
else:
    print(f'Erro: {r.text}')
